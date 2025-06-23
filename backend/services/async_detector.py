"""
异步网站检测引擎
使用aiohttp替代requests，支持高并发检测
"""

import asyncio
import aiohttp
import time
import ssl
import logging
from typing import List, Dict, Optional, Callable, Set
from datetime import datetime
from urllib.parse import urlparse, urljoin
from dataclasses import dataclass

from ..utils.helpers import get_beijing_time, normalize_url, extract_domain
from .detection_result import DetectionResult

logger = logging.getLogger(__name__)


@dataclass
class AsyncDetectionConfig:
    """异步检测配置 - 进一步优化版本，降低资源占用"""
    max_concurrent: int = 10          # 最大并发连接数（从20降到10）
    max_per_host: int = 3            # 每个主机最大连接数（从5降到3）
    timeout_total: int = 12          # 总超时时间(秒)（从15降到12）
    timeout_connect: int = 6         # 连接超时时间(秒)（从8降到6）
    timeout_read: int = 8            # 读取超时时间(秒)（从12降到8）
    max_redirects: int = 2           # 最大重定向次数（从3降到2）
    max_content_size: int = 256*1024 # 最大内容大小(256KB)（从512KB降到256KB）
    user_agent: str = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    verify_ssl: bool = False         # 是否验证SSL
    dns_cache_ttl: int = 300         # DNS缓存TTL(秒)（从600降到300，减少内存）
    keep_alive: bool = False         # 关闭保持连接，减少资源占用


class AsyncWebsiteDetector:
    """异步网站检测器"""
    
    def __init__(self, config: AsyncDetectionConfig = None):
        self.config = config or AsyncDetectionConfig()
        self.session = None
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'timeout_requests': 0,
            'redirect_requests': 0,
            'start_time': None,
            'end_time': None
        }
        
        logger.info(f"异步检测器初始化完成，配置: max_concurrent={self.config.max_concurrent}")
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self._create_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()
    
    async def _create_session(self):
        """创建异步HTTP会话"""
        # SSL上下文配置
        ssl_context = ssl.create_default_context()
        if not self.config.verify_ssl:
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        
        # TCP连接器配置
        connector = aiohttp.TCPConnector(
            limit=self.config.max_concurrent,
            limit_per_host=self.config.max_per_host,
            ttl_dns_cache=self.config.dns_cache_ttl,
            use_dns_cache=True,
            enable_cleanup_closed=True,
            ssl=ssl_context,
            keepalive_timeout=60,
            force_close=not self.config.keep_alive
        )
        
        # 超时配置
        timeout = aiohttp.ClientTimeout(
            total=self.config.timeout_total,
            connect=self.config.timeout_connect,
            sock_read=self.config.timeout_read
        )
        
        # 创建会话
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': self.config.user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        )
        
        logger.info("异步HTTP会话创建完成")
    
    async def detect_websites(self, urls: List[str], 
                             progress_callback: Optional[Callable] = None) -> List['DetectionResult']:
        """
        异步批量检测网站
        
        Args:
            urls: 网站URL列表
            progress_callback: 进度回调函数(completed, total)
            
        Returns:
            检测结果列表
        """
        if not self.session:
            await self._create_session()
        
        self.stats['start_time'] = time.time()
        self.stats['total_requests'] = len(urls)
        
        logger.info(f"开始异步检测 {len(urls)} 个网站")
        
        # 创建信号量控制并发
        semaphore = asyncio.Semaphore(self.config.max_concurrent)
        
        # 创建检测任务
        tasks = []
        for url in urls:
            task = self._detect_with_semaphore(semaphore, url)
            tasks.append(task)
        
        # 执行并发检测
        results = []
        completed = 0
        
        for coro in asyncio.as_completed(tasks):
            try:
                result = await coro
                results.append(result)
                completed += 1
                
                # 更新统计
                if result.status != 'failed':
                    self.stats['successful_requests'] += 1
                    if result.status == 'redirect':
                        self.stats['redirect_requests'] += 1
                else:
                    self.stats['failed_requests'] += 1
                    if 'timeout' in result.error_message.lower():
                        self.stats['timeout_requests'] += 1
                
                # 进度回调
                if progress_callback:
                    try:
                        progress_callback(completed, len(urls))
                    except Exception as e:
                        logger.warning(f"进度回调异常: {e}")
                        
            except Exception as e:
                logger.error(f"检测任务异常: {e}")
                # 创建错误结果
                error_result = DetectionResult()
                error_result.status = 'failed'
                error_result.error_message = f"任务异常: {str(e)}"
                results.append(error_result)
                completed += 1
        
        self.stats['end_time'] = time.time()
        
        # 记录统计信息
        self._log_statistics()
        
        # 按原始顺序排序结果
        url_to_result = {result.original_url: result for result in results}
        ordered_results = [url_to_result.get(url, DetectionResult()) for url in urls]
        
        logger.info(f"异步检测完成，共检测 {len(ordered_results)} 个网站")
        return ordered_results
    
    async def _detect_with_semaphore(self, semaphore: asyncio.Semaphore, url: str) -> 'DetectionResult':
        """
        使用信号量控制并发的检测方法
        
        Args:
            semaphore: 信号量
            url: 网站URL
            
        Returns:
            检测结果
        """
        async with semaphore:
            return await self._detect_single_website(url)
    
    async def _detect_single_website(self, url: str) -> DetectionResult:
        """
        异步检测单个网站
        
        Args:
            url: 网站URL
            
        Returns:
            检测结果
        """
        result = DetectionResult()
        result.original_url = url
        start_time = time.time()
        
        try:
            # 标准化URL
            normalized_url = normalize_url(url)
            result.final_url = normalized_url
            
            # 发起HTTP请求
            async with self.session.get(normalized_url, allow_redirects=True) as response:
                result.response_time = time.time() - start_time
                result.http_status_code = response.status
                result.final_url = str(response.url)
                
                # 记录重定向链
                if hasattr(response, 'history') and response.history:
                    result.redirect_chain = [str(r.url) for r in response.history]
                    result.redirect_chain.append(str(response.url))
                
                # 判断检测状态
                if response.status == 200:
                    # 检查是否发生重定向
                    if str(response.url) != normalized_url:
                        result.status = 'redirect'
                    else:
                        result.status = 'standard'
                    
                    # 读取部分页面内容
                    content = await self._read_content_safely(response)
                    result.page_content_length = len(content)
                    
                    # 提取页面标题
                    result.page_title = self._extract_title(content)
                    
                    # 获取SSL信息
                    if response.url.scheme == 'https':
                        result.ssl_info = await self._get_ssl_info(response)
                
                elif 300 <= response.status < 400:
                    result.status = 'redirect'
                    result.error_message = f"重定向状态码: {response.status}"
                    
                else:
                    result.status = 'failed'
                    result.error_message = f"HTTP状态码: {response.status}"
                    result.failure_reason = 'server_error'
        
        except asyncio.TimeoutError:
            result.status = 'failed'
            result.error_message = "请求超时"
            result.failure_reason = 'timeout'
            
        except aiohttp.ClientConnectorError as e:
            result.status = 'failed'
            result.error_message = f"连接错误: {str(e)}"
            result.failure_reason = 'connection_error'
            
        except aiohttp.ClientSSLError as e:
            result.status = 'failed'
            result.error_message = f"SSL错误: {str(e)}"
            result.failure_reason = 'ssl_error'
            
        except aiohttp.ClientError as e:
            result.status = 'failed'
            result.error_message = f"客户端错误: {str(e)}"
            result.failure_reason = 'client_error'
            
        except Exception as e:
            result.status = 'failed'
            result.error_message = f"未知错误: {str(e)}"
            result.failure_reason = 'unknown_error'
        
        finally:
            result.detection_duration = time.time() - start_time
            result.detected_at = get_beijing_time()
        
        return result
    
    async def _read_content_safely(self, response: aiohttp.ClientResponse) -> str:
        """
        安全读取响应内容，限制大小避免内存溢出
        
        Args:
            response: HTTP响应对象
            
        Returns:
            页面内容（截断）
        """
        try:
            content_length = response.headers.get('Content-Length')
            if content_length and int(content_length) > self.config.max_content_size:
                # 内容过大，只读取部分
                content = await response.content.read(self.config.max_content_size)
                return content.decode('utf-8', errors='ignore')
            else:
                # 正常读取
                return await response.text(encoding='utf-8', errors='ignore')
        except Exception as e:
            logger.warning(f"读取响应内容失败: {e}")
            return ""
    
    def _extract_title(self, content: str) -> str:
        """
        提取页面标题
        
        Args:
            content: 页面内容
            
        Returns:
            页面标题
        """
        try:
            from bs4 import BeautifulSoup
            # 只解析前10KB内容，提高效率
            soup = BeautifulSoup(content[:10240], 'html.parser')
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text(strip=True)
                return title[:200]  # 限制标题长度
        except Exception as e:
            logger.debug(f"提取标题失败: {e}")
        
        return ""
    
    async def _get_ssl_info(self, response: aiohttp.ClientResponse) -> Dict:
        """
        获取SSL证书信息
        
        Args:
            response: HTTP响应对象
            
        Returns:
            SSL信息字典
        """
        ssl_info = {}
        try:
            if response.connection and hasattr(response.connection, 'transport'):
                transport = response.connection.transport
                if hasattr(transport, 'get_extra_info'):
                    ssl_object = transport.get_extra_info('ssl_object')
                    if ssl_object:
                        cert = ssl_object.getpeercert()
                        if cert:
                            ssl_info.update({
                                'subject': dict(x[0] for x in cert.get('subject', [])),
                                'issuer': dict(x[0] for x in cert.get('issuer', [])),
                                'version': cert.get('version'),
                                'serial_number': str(cert.get('serialNumber', '')),
                                'not_before': cert.get('notBefore'),
                                'not_after': cert.get('notAfter'),
                            })
        except Exception as e:
            logger.debug(f"获取SSL信息失败: {e}")
        
        return ssl_info
    
    def _log_statistics(self):
        """记录检测统计信息"""
        if self.stats['end_time'] and self.stats['start_time']:
            duration = self.stats['end_time'] - self.stats['start_time']
            total = self.stats['total_requests']
            successful = self.stats['successful_requests']
            failed = self.stats['failed_requests']
            timeout = self.stats['timeout_requests']
            redirect = self.stats['redirect_requests']
            
            success_rate = (successful / total * 100) if total > 0 else 0
            avg_time = duration / total if total > 0 else 0
            throughput = total / duration if duration > 0 else 0
            
            logger.info(f"异步检测统计:")
            logger.info(f"  总请求数: {total}")
            logger.info(f"  成功请求: {successful} ({success_rate:.1f}%)")
            logger.info(f"  失败请求: {failed}")
            logger.info(f"  超时请求: {timeout}")
            logger.info(f"  重定向请求: {redirect}")
            logger.info(f"  总耗时: {duration:.2f}s")
            logger.info(f"  平均耗时: {avg_time:.3f}s")
            logger.info(f"  吞吐量: {throughput:.1f} req/s")
    
    async def close(self):
        """关闭检测器，清理资源"""
        if self.session:
            try:
                # 确保所有挂起的连接都被关闭
                await self.session.close()
                # 等待一小段时间让连接完全关闭
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.warning(f"关闭session时出错: {e}")
            finally:
                self.session = None
        logger.info("异步检测器已关闭")
    
    def get_stats(self) -> Dict:
        """
        获取检测统计信息
        
        Returns:
            统计信息字典
        """
        return self.stats.copy()


class AsyncDetectionPool:
    """异步检测池，管理多个检测器实例"""
    
    def __init__(self, pool_size: int = 3, config: AsyncDetectionConfig = None):
        self.pool_size = pool_size
        self.config = config or AsyncDetectionConfig()
        self.detectors = []
        self.current_detector = 0
        
        logger.info(f"异步检测池初始化，池大小: {pool_size}")
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self._create_pool()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close_pool()
    
    async def _create_pool(self):
        """创建检测器池"""
        for i in range(self.pool_size):
            detector = AsyncWebsiteDetector(self.config)
            await detector._create_session()
            self.detectors.append(detector)
        
        logger.info(f"异步检测池创建完成，包含 {len(self.detectors)} 个检测器")
    
    def get_detector(self) -> AsyncWebsiteDetector:
        """
        获取下一个可用的检测器（轮询）
        
        Returns:
            检测器实例
        """
        if not self.detectors:
            raise RuntimeError("检测池未初始化")
        
        detector = self.detectors[self.current_detector]
        self.current_detector = (self.current_detector + 1) % len(self.detectors)
        return detector
    
    async def detect_with_load_balancing(self, urls: List[str], 
                                        progress_callback: Optional[Callable] = None) -> List[DetectionResult]:
        """
        负载均衡的检测方法
        
        Args:
            urls: 网站URL列表
            progress_callback: 进度回调函数
            
        Returns:
            检测结果列表
        """
        if not urls:
            return []
        
        # 将URL分配给不同的检测器
        url_chunks = []
        chunk_size = len(urls) // len(self.detectors)
        remainder = len(urls) % len(self.detectors)
        
        start_idx = 0
        for i in range(len(self.detectors)):
            end_idx = start_idx + chunk_size + (1 if i < remainder else 0)
            url_chunks.append(urls[start_idx:end_idx])
            start_idx = end_idx
        
        # 并行执行检测
        tasks = []
        for i, chunk in enumerate(url_chunks):
            if chunk:  # 确保chunk不为空
                detector = self.detectors[i]
                task = detector.detect_websites(chunk, None)  # 不使用单独的进度回调
                tasks.append(task)
        
        # 等待所有任务完成
        chunk_results = await asyncio.gather(*tasks)
        
        # 合并结果并保持原始顺序
        all_results = []
        for chunk_result in chunk_results:
            all_results.extend(chunk_result)
        
        # 最终进度回调
        if progress_callback:
            progress_callback(len(all_results), len(urls))
        
        return all_results
    
    async def close_pool(self):
        """关闭检测池"""
        for detector in self.detectors:
            await detector.close()
        self.detectors.clear()
        logger.info("异步检测池已关闭") 