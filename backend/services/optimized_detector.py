"""
优化的网站检测服务
解决结果顺序问题，降低资源占用，提高检测精度
"""

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
import threading

from .website_detector import WebsiteDetector
from .async_detector import AsyncWebsiteDetector, AsyncDetectionConfig
from .detection_result import DetectionResult
from .memory_monitor import get_memory_manager

logger = logging.getLogger(__name__)


@dataclass
class OptimizedDetectionConfig:
    """优化检测配置"""
    # 基础配置
    timeout_seconds: int = 15          # 超时时间（从20降到15）
    retry_times: int = 1               # 重试次数（从2降到1）
    max_concurrent: int = 8            # 最大并发数（从10降到8）
    
    # 批处理配置
    batch_size: int = 50               # 批处理大小
    async_threshold: int = 20          # 异步处理阈值
    
    # 资源管理
    memory_check_interval: int = 10    # 内存检查间隔
    enable_memory_monitoring: bool = True
    
    # 结果配置
    preserve_order: bool = True        # 保持结果顺序
    enable_progress_callback: bool = True


class OptimizedWebsiteDetector:
    """优化的网站检测器"""
    
    def __init__(self, config: OptimizedDetectionConfig = None):
        self.config = config or OptimizedDetectionConfig()
        self.stats = {
            'total_urls': 0,
            'successful_detections': 0,
            'failed_detections': 0,
            'avg_response_time': 0.0,
            'start_time': None,
            'end_time': None
        }
        
        # 内存管理
        if self.config.enable_memory_monitoring:
            self.memory_manager = get_memory_manager()
        else:
            self.memory_manager = None
        
        logger.info(f"优化检测器初始化完成，配置: {self.config}")
    
    def detect_websites_batch(self, 
                            urls: List[str], 
                            progress_callback: Optional[Callable] = None) -> List[DetectionResult]:
        """
        批量检测网站（优化版）
        
        Args:
            urls: URL列表
            progress_callback: 进度回调函数
            
        Returns:
            检测结果列表（保持原始顺序）
        """
        if not urls:
            return []
        
        self.stats['total_urls'] = len(urls)
        self.stats['start_time'] = time.time()
        
        logger.info(f"开始批量检测 {len(urls)} 个网站")
        
        try:
            # 根据URL数量选择检测策略
            if len(urls) <= self.config.async_threshold:
                results = self._detect_sync_batch(urls, progress_callback)
            else:
                results = self._detect_async_batch(urls, progress_callback)
            
            # 确保结果顺序正确
            if self.config.preserve_order:
                results = self._ensure_result_order(urls, results)
            
            self._update_stats(results)
            
            logger.info(f"批量检测完成，成功: {self.stats['successful_detections']}, "
                       f"失败: {self.stats['failed_detections']}")
            
            return results
            
        except Exception as e:
            logger.error(f"批量检测异常: {e}")
            return self._create_error_results(urls, str(e))
    
    def _detect_sync_batch(self, 
                          urls: List[str], 
                          progress_callback: Optional[Callable] = None) -> List[DetectionResult]:
        """同步批量检测"""
        logger.info(f"使用同步模式检测 {len(urls)} 个网站")
        
        results = []
        detector = WebsiteDetector({
            'timeout_seconds': self.config.timeout_seconds,
            'retry_times': self.config.retry_times,
            'max_concurrent': self.config.max_concurrent
        })
        
        try:
            # 分批处理以控制内存使用
            for i in range(0, len(urls), self.config.batch_size):
                batch_urls = urls[i:i + self.config.batch_size]
                
                # 检查内存使用
                if self.memory_manager and i % self.config.memory_check_interval == 0:
                    self._check_memory()
                
                # 使用ThreadPoolExecutor确保结果顺序
                with ThreadPoolExecutor(max_workers=self.config.max_concurrent) as executor:
                    # 创建有序的future映射
                    future_to_index = {}
                    for idx, url in enumerate(batch_urls):
                        future = executor.submit(detector.detect_single_website, url)
                        future_to_index[future] = i + idx
                    
                    # 按提交顺序收集结果
                    batch_results = [None] * len(batch_urls)
                    for future in as_completed(future_to_index):
                        try:
                            result = future.result()
                            index = future_to_index[future]
                            batch_results[index - i] = result
                        except Exception as e:
                            logger.error(f"单个检测任务异常: {e}")
                            error_result = DetectionResult()
                            error_result.status = 'failed'
                            error_result.error_message = str(e)
                            index = future_to_index[future]
                            batch_results[index - i] = error_result
                    
                    # 过滤None值并添加到结果
                    valid_results = [r for r in batch_results if r is not None]
                    results.extend(valid_results)
                
                # 进度回调
                if progress_callback and self.config.enable_progress_callback:
                    try:
                        progress_callback(len(results), len(urls))
                    except Exception as e:
                        logger.warning(f"进度回调异常: {e}")
        
        finally:
            detector.close()
        
        return results
    
    def _detect_async_batch(self, 
                           urls: List[str], 
                           progress_callback: Optional[Callable] = None) -> List[DetectionResult]:
        """异步批量检测"""
        logger.info(f"使用异步模式检测 {len(urls)} 个网站")
        
        # 检查异步支持
        try:
            return asyncio.run(self._async_detect_implementation(urls, progress_callback))
        except Exception as e:
            logger.warning(f"异步检测失败，降级到同步模式: {e}")
            return self._detect_sync_batch(urls, progress_callback)
    
    async def _async_detect_implementation(self, 
                                         urls: List[str], 
                                         progress_callback: Optional[Callable] = None) -> List[DetectionResult]:
        """异步检测实现"""
        config = AsyncDetectionConfig(
            max_concurrent=self.config.max_concurrent,
            timeout_total=self.config.timeout_seconds,
            max_content_size=256*1024  # 256KB限制
        )
        
        async with AsyncWebsiteDetector(config) as detector:
            return await detector.detect_batch_websites(
                urls, 
                progress_callback=progress_callback
            )
    
    def _ensure_result_order(self, urls: List[str], results: List[DetectionResult]) -> List[DetectionResult]:
        """确保结果顺序与输入URL顺序一致"""
        if len(results) != len(urls):
            logger.warning(f"结果数量不匹配: 输入{len(urls)}, 输出{len(results)}")
        
        # 创建URL到结果的映射
        url_to_result = {}
        for result in results:
            if result and result.original_url:
                url_to_result[result.original_url] = result
        
        # 按原始URL顺序重新排列结果
        ordered_results = []
        for url in urls:
            if url in url_to_result:
                ordered_results.append(url_to_result[url])
            else:
                # 创建缺失的错误结果
                error_result = DetectionResult()
                error_result.original_url = url
                error_result.status = 'failed'
                error_result.error_message = '未找到检测结果'
                ordered_results.append(error_result)
        
        return ordered_results
    
    def _check_memory(self):
        """检查内存使用情况"""
        if self.memory_manager:
            memory_info = self.memory_manager.get_memory_info()
            if memory_info:
                usage_mb = memory_info.get('rss_mb', 0)
                if usage_mb > 400:  # 400MB警告阈值
                    logger.warning(f"内存使用较高: {usage_mb:.1f}MB")
                    self.memory_manager.force_cleanup()
    
    def _create_error_results(self, urls: List[str], error_message: str) -> List[DetectionResult]:
        """创建错误结果列表"""
        results = []
        for url in urls:
            result = DetectionResult()
            result.original_url = url
            result.status = 'failed'
            result.error_message = error_message
            results.append(result)
        return results
    
    def _update_stats(self, results: List[DetectionResult]):
        """更新统计信息"""
        self.stats['end_time'] = time.time()
        
        successful = sum(1 for r in results if r.status in ['standard', 'redirect'])
        failed = len(results) - successful
        
        self.stats['successful_detections'] = successful
        self.stats['failed_detections'] = failed
        
        # 计算平均响应时间
        response_times = [r.response_time for r in results if r.response_time and r.response_time > 0]
        if response_times:
            self.stats['avg_response_time'] = sum(response_times) / len(response_times)
        
        # 计算总耗时
        if self.stats['start_time'] and self.stats['end_time']:
            total_time = self.stats['end_time'] - self.stats['start_time']
            logger.info(f"检测统计: 总耗时{total_time:.2f}s, "
                       f"平均响应时间{self.stats['avg_response_time']:.3f}s, "
                       f"成功率{successful/len(results)*100:.1f}%")
    
    def get_stats(self) -> Dict:
        """获取检测统计信息"""
        return self.stats.copy()