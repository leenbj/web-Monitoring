"""
分片检测服务
将大批量检测任务分片处理，避免资源争抢和内存溢出
"""

import logging
import asyncio
import aiohttp
import time
from typing import List, Dict, Optional, Callable, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from .website_detector import WebsiteDetector, DetectionResult
from ..database import get_db
from ..models import DetectionRecord, Website, DetectionTask
from ..utils.helpers import get_beijing_time, batch_process_list

logger = logging.getLogger(__name__)


@dataclass
class BatchDetectionConfig:
    """批处理检测配置"""
    batch_size: int = 50              # 每批次网站数量
    max_concurrent: int = 100         # 最大并发数
    timeout_seconds: int = 30         # 超时时间
    retry_times: int = 3              # 重试次数
    enable_async: bool = True         # 是否启用异步检测
    memory_limit_mb: int = 500        # 内存限制(MB)
    

@dataclass
class BatchDetectionResult:
    """批处理检测结果"""
    total_websites: int = 0
    processed_websites: int = 0
    successful_detections: int = 0
    failed_detections: int = 0
    total_duration: float = 0.0
    batch_results: List[List[DetectionResult]] = None
    error_message: str = ""
    
    def __post_init__(self):
        if self.batch_results is None:
            self.batch_results = []


class BatchDetectionService:
    """分片批量检测服务"""
    
    def __init__(self, config: BatchDetectionConfig = None):
        self.config = config or BatchDetectionConfig()
        self.detector = WebsiteDetector({
            'timeout_seconds': self.config.timeout_seconds,
            'retry_times': self.config.retry_times,
            'max_concurrent': min(self.config.max_concurrent, 200)  # 限制最大并发
        })
        
        # 异步会话（如果启用异步）
        self.async_session = None
        
        logger.info(f"分片检测服务初始化完成，配置: {self.config}")
    
    async def detect_websites_async(self, urls: List[str], 
                                   progress_callback: Optional[Callable] = None) -> BatchDetectionResult:
        """
        异步批量检测网站
        
        Args:
            urls: 网站URL列表
            progress_callback: 进度回调函数
            
        Returns:
            批处理检测结果
        """
        start_time = time.time()
        result = BatchDetectionResult()
        result.total_websites = len(urls)
        
        logger.info(f"开始异步批量检测 {len(urls)} 个网站，分片大小: {self.config.batch_size}")
        
        try:
            # 分片处理
            batches = list(batch_process_list(urls, self.config.batch_size))
            logger.info(f"分为 {len(batches)} 个批次处理")
            
            # 创建异步会话
            connector = aiohttp.TCPConnector(
                limit=self.config.max_concurrent,
                limit_per_host=50,
                ttl_dns_cache=300,
                use_dns_cache=True,
                enable_cleanup_closed=True
            )
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            ) as session:
                self.async_session = session
                
                # 并行处理各个批次
                batch_tasks = []
                for batch_idx, batch_urls in enumerate(batches):
                    task = self._process_batch_async(session, batch_urls, batch_idx)
                    batch_tasks.append(task)
                
                # 等待所有批次完成
                for completed_task in asyncio.as_completed(batch_tasks):
                    try:
                        batch_result = await completed_task
                        result.batch_results.append(batch_result)
                        result.processed_websites += len(batch_result)
                        result.successful_detections += sum(1 for r in batch_result if r.status != 'failed')
                        result.failed_detections += sum(1 for r in batch_result if r.status == 'failed')
                        
                        # 调用进度回调
                        if progress_callback:
                            progress_callback(result.processed_websites, result.total_websites)
                            
                    except Exception as e:
                        logger.error(f"批次处理异常: {e}")
                        result.error_message += f"批次异常: {str(e)}; "
            
            result.total_duration = time.time() - start_time
            
            logger.info(f"异步批量检测完成: 总数 {result.total_websites}, "
                       f"成功 {result.successful_detections}, 失败 {result.failed_detections}, "
                       f"耗时 {result.total_duration:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"异步批量检测失败: {e}")
            result.error_message = str(e)
            result.total_duration = time.time() - start_time
            return result
    
    async def _process_batch_async(self, session: aiohttp.ClientSession, 
                                  urls: List[str], batch_idx: int) -> List[DetectionResult]:
        """
        异步处理单个批次
        
        Args:
            session: aiohttp会话
            urls: 批次URL列表
            batch_idx: 批次索引
            
        Returns:
            检测结果列表
        """
        logger.debug(f"开始处理批次 {batch_idx}，包含 {len(urls)} 个网站")
        
        # 创建检测任务
        detection_tasks = []
        for url in urls:
            task = self._detect_single_website_async(session, url)
            detection_tasks.append(task)
        
        # 并行执行检测
        results = []
        try:
            completed_results = await asyncio.gather(*detection_tasks, return_exceptions=True)
            
            for i, result in enumerate(completed_results):
                if isinstance(result, Exception):
                    # 处理异常
                    error_result = DetectionResult()
                    error_result.original_url = urls[i]
                    error_result.status = 'failed'
                    error_result.error_message = f"检测异常: {str(result)}"
                    results.append(error_result)
                else:
                    results.append(result)
                    
        except Exception as e:
            logger.error(f"批次 {batch_idx} 执行异常: {e}")
            # 创建失败结果
            for url in urls:
                error_result = DetectionResult()
                error_result.original_url = url
                error_result.status = 'failed'
                error_result.error_message = f"批次执行异常: {str(e)}"
                results.append(error_result)
        
        logger.debug(f"批次 {batch_idx} 处理完成，成功 {sum(1 for r in results if r.status != 'failed')} 个")
        return results
    
    async def _detect_single_website_async(self, session: aiohttp.ClientSession, 
                                          url: str) -> DetectionResult:
        """
        异步检测单个网站
        
        Args:
            session: aiohttp会话
            url: 网站URL
            
        Returns:
            检测结果
        """
        result = DetectionResult()
        result.original_url = url
        start_time = time.time()
        
        try:
            # 标准化URL
            from ..utils.helpers import normalize_url
            normalized_url = normalize_url(url)
            
            # 发起HTTP请求
            async with session.get(normalized_url) as response:
                result.http_status_code = response.status
                result.response_time = time.time() - start_time
                result.final_url = str(response.url)
                
                # 判断检测状态
                if response.status == 200:
                    # 检查是否重定向
                    if str(response.url) != normalized_url:
                        result.status = 'redirect'
                    else:
                        result.status = 'standard'
                    
                    # 读取页面内容（限制大小）
                    content = await response.text(encoding='utf-8', errors='ignore')
                    result.page_content_length = len(content)
                    
                    # 提取页面标题
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(content[:10000], 'html.parser')  # 只解析前10KB
                    title_tag = soup.find('title')
                    if title_tag:
                        result.page_title = title_tag.get_text(strip=True)[:200]  # 限制标题长度
                    
                else:
                    result.status = 'failed'
                    result.error_message = f"HTTP状态码: {response.status}"
                    
        except asyncio.TimeoutError:
            result.status = 'failed'
            result.error_message = "请求超时"
            result.failure_reason = 'timeout'
        except Exception as e:
            result.status = 'failed'
            result.error_message = str(e)
            result.failure_reason = 'connection_error'
        
        result.detection_duration = time.time() - start_time
        result.detected_at = get_beijing_time()
        
        return result
    
    def detect_websites_sync(self, urls: List[str], 
                            progress_callback: Optional[Callable] = None) -> BatchDetectionResult:
        """
        同步批量检测网站（兼容模式）
        
        Args:
            urls: 网站URL列表
            progress_callback: 进度回调函数
            
        Returns:
            批处理检测结果
        """
        start_time = time.time()
        result = BatchDetectionResult()
        result.total_websites = len(urls)
        
        logger.info(f"开始同步批量检测 {len(urls)} 个网站，分片大小: {self.config.batch_size}")
        
        try:
            # 分片处理
            batches = list(batch_process_list(urls, self.config.batch_size))
            logger.info(f"分为 {len(batches)} 个批次处理")
            
            # 使用线程池处理各个批次（进一步降低并发）
            with ThreadPoolExecutor(max_workers=min(2, len(batches))) as executor:
                # 提交批次任务
                future_to_batch = {}
                for batch_idx, batch_urls in enumerate(batches):
                    future = executor.submit(self._process_batch_sync, batch_urls, batch_idx)
                    future_to_batch[future] = batch_idx
                
                # 收集结果
                for future in as_completed(future_to_batch):
                    try:
                        batch_result = future.result()
                        result.batch_results.append(batch_result)
                        result.processed_websites += len(batch_result)
                        result.successful_detections += sum(1 for r in batch_result if r.status != 'failed')
                        result.failed_detections += sum(1 for r in batch_result if r.status == 'failed')
                        
                        # 调用进度回调
                        if progress_callback:
                            progress_callback(result.processed_websites, result.total_websites)
                            
                    except Exception as e:
                        logger.error(f"批次处理异常: {e}")
                        result.error_message += f"批次异常: {str(e)}; "
            
            result.total_duration = time.time() - start_time
            
            logger.info(f"同步批量检测完成: 总数 {result.total_websites}, "
                       f"成功 {result.successful_detections}, 失败 {result.failed_detections}, "
                       f"耗时 {result.total_duration:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"同步批量检测失败: {e}")
            result.error_message = str(e)
            result.total_duration = time.time() - start_time
            return result
    
    def _process_batch_sync(self, urls: List[str], batch_idx: int) -> List[DetectionResult]:
        """
        同步处理单个批次
        
        Args:
            urls: 批次URL列表
            batch_idx: 批次索引
            
        Returns:
            检测结果列表
        """
        logger.debug(f"开始同步处理批次 {batch_idx}，包含 {len(urls)} 个网站")
        
        # 使用原有检测器处理
        results = self.detector.detect_batch_websites(urls)
        
        logger.debug(f"批次 {batch_idx} 同步处理完成")
        return results
    
    def save_batch_results(self, task_id: int, websites: List[Website], 
                          batch_result: BatchDetectionResult) -> bool:
        """
        批量保存检测结果到数据库
        
        Args:
            task_id: 任务ID
            websites: 网站列表
            batch_result: 批处理检测结果
            
        Returns:
            是否保存成功
        """
        try:
            # 展平所有批次结果
            all_results = []
            for batch in batch_result.batch_results:
                all_results.extend(batch)
            
            logger.info(f"开始批量保存 {len(all_results)} 条检测记录")
            
            # 分批插入数据库
            batch_size = 100
            for batch_start in range(0, len(all_results), batch_size):
                batch_end = min(batch_start + batch_size, len(all_results))
                batch_records = all_results[batch_start:batch_end]
                
                with get_db() as db:
                    records_to_insert = []
                    
                    for i, result in enumerate(batch_records):
                        website_idx = batch_start + i
                        if website_idx < len(websites):
                            website = websites[website_idx]
                            
                            record = DetectionRecord(
                                task_id=task_id,
                                website_id=website.id,
                                status=result.status,
                                response_time=result.response_time or 0.0,
                                http_status_code=result.http_status_code,
                                final_url=result.final_url or '',
                                error_message=result.error_message or '',
                                failure_reason=getattr(result, 'failure_reason', '') or '',
                                ssl_info=getattr(result, 'ssl_info', {}) or {},
                                page_title=getattr(result, 'page_title', '') or '',
                                page_content_length=getattr(result, 'page_content_length', 0) or 0,
                                retry_count=getattr(result, 'retry_count', 0) or 0,
                                redirect_chain=getattr(result, 'redirect_chain', []) or [],
                                detected_at=result.detected_at,
                                detection_duration=result.detection_duration
                            )
                            records_to_insert.append(record)
                    
                    # 批量插入
                    db.bulk_save_objects(records_to_insert)
                    db.commit()
                    
                    logger.debug(f"批量插入 {len(records_to_insert)} 条记录")
            
            logger.info(f"批量保存完成，共保存 {len(all_results)} 条记录")
            return True
            
        except Exception as e:
            logger.error(f"批量保存检测结果失败: {e}")
            return False
    
    def close(self):
        """关闭服务，清理资源"""
        if self.detector:
            self.detector.close()
        logger.info("分片检测服务已关闭") 