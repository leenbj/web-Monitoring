"""
网址监控工具 - 网站检测引擎
核心检测逻辑，判断网站的三种访问状态
支持异步高并发检测和智能内存管理
"""

import time
import urllib.parse
import ssl
import socket
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import asyncio

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import logging

logger = logging.getLogger(__name__)

# 北京时区
BEIJING_TZ = timezone(timedelta(hours=8))

def get_beijing_time():
    """获取北京时间"""
    return datetime.now(BEIJING_TZ)

from ..utils.helpers import (
    normalize_url, extract_domain, is_chinese_domain, 
    detect_url_redirect_type
)
from .detection_result import DetectionResult

# 导入高性能组件
try:
    from .async_detector import AsyncWebsiteDetector, AsyncDetectionConfig, AsyncDetectionPool
    from .memory_monitor import get_memory_manager, start_global_memory_monitoring
    ASYNC_SUPPORT = True
except ImportError as e:
    logger.warning(f"异步检测组件导入失败: {e}")
    ASYNC_SUPPORT = False


class WebsiteDetector:
    """网站检测器"""
    
    def __init__(self, config: Dict = None):
        """
        初始化检测器
        
        Args:
            config: 检测配置
        """
        self.config = config or {}
        self.timeout = self.config.get('timeout_seconds', 20)  # 从30降到20
        self.retry_times = self.config.get('retry_times', 2)   # 从3降到2
        self.max_concurrent = self.config.get('max_concurrent', 10)  # 从20降到10
        self.user_agent = self.config.get('user_agent', 
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        self.verify_ssl = self.config.get('verify_ssl', False)
        
        # 会话创建延迟到使用时
        self.session = None
        self._session_lock = threading.Lock()
        
        # 线程锁
        self._lock = threading.Lock()
        
        logger.info(f"网站检测器初始化完成，配置: {self.config}")
    
    def __del__(self):
        """析构函数，确保资源清理"""
        self.close()
    
    def close(self):
        """关闭会话和清理资源"""
        if self.session:
            try:
                self.session.close()
            except Exception as e:
                logger.warning(f"关闭会话时出错: {e}")
            finally:
                self.session = None
    
    def _create_session(self) -> requests.Session:
        """创建请求会话"""
        session = requests.Session()
        
        # 设置重试策略
        retry_strategy = Retry(
            total=self.retry_times,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # 设置请求头
        session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        return session
    
    def _get_session(self) -> requests.Session:
        """获取会话（线程安全的懒加载）"""
        if self.session is None:
            with self._session_lock:
                if self.session is None:
                    self.session = self._create_session()
        return self.session
    
    def _check_ssl_certificate(self, url: str) -> Dict:
        """
        检查SSL证书信息
        
        Args:
            url: 网站URL
            
        Returns:
            SSL证书信息字典
        """
        ssl_info = {
            'valid': False,
            'expired': False,
            'expires_in_days': None,
            'issuer': '',
            'subject': '',
            'error': ''
        }
        
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            if parsed.scheme != 'https':
                return ssl_info
            
            hostname = parsed.hostname
            port = parsed.port or 443
            
            # 创建SSL上下文
            context = ssl.create_default_context()
            
            # 连接并获取证书
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    
                    if cert:
                        # 解析证书信息
                        ssl_info['valid'] = True
                        ssl_info['subject'] = dict(x[0] for x in cert['subject'])['commonName']
                        ssl_info['issuer'] = dict(x[0] for x in cert['issuer'])['commonName']
                        
                        # 检查过期时间
                        not_after = cert['notAfter']
                        expire_date = datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z')
                        expire_date = expire_date.replace(tzinfo=timezone.utc)
                        now = datetime.now(timezone.utc)
                        
                        days_until_expiry = (expire_date - now).days
                        ssl_info['expires_in_days'] = days_until_expiry
                        ssl_info['expired'] = days_until_expiry <= 0
                        
        except ssl.SSLError as e:
            ssl_info['error'] = f"SSL错误: {str(e)}"
        except socket.gaierror as e:
            ssl_info['error'] = f"域名解析失败: {str(e)}"
        except socket.timeout:
            ssl_info['error'] = "SSL连接超时"
        except Exception as e:
            ssl_info['error'] = f"SSL检查异常: {str(e)}"
        
        return ssl_info
    
    def detect_single_website(self, url: str) -> DetectionResult:
        """
        检测单个网站
        
        Args:
            url: 网站URL
            
        Returns:
            检测结果
        """
        start_time = time.time()
        result = DetectionResult()
        result.original_url = url
        result.detected_at = get_beijing_time()
        
        try:
            # 标准化URL
            normalized_url = normalize_url(url)
            if not normalized_url:
                result.error_message = "URL格式不正确"
                return result
            
            logger.info(f"开始检测网站: {normalized_url}")
            
            # 检查SSL证书（如果是HTTPS）
            if normalized_url.startswith('https://'):
                result.ssl_info = self._check_ssl_certificate(normalized_url)
            
            # 执行HTTP请求检测
            response_data = self._make_request(normalized_url)
            
            if response_data['success']:
                # 请求成功，分析结果
                result = self._analyze_response(result, response_data)
            else:
                # 请求失败，设置详细失败原因
                result.status = 'failed'
                result.error_message = response_data.get('error', '未知错误')
                result.failure_reason = response_data.get('failure_reason', 'unknown_error')
                result.retry_count = response_data.get('retry_count', 0)
            
        except Exception as e:
            logger.error(f"检测网站异常: {url}, 错误: {e}")
            result.status = 'failed'
            result.error_message = f"检测异常: {str(e)}"
        
        finally:
            result.detection_duration = time.time() - start_time
            logger.info(f"网站检测完成: {url}, 状态: {result.status}, 耗时: {result.detection_duration:.2f}s")
        
        return result
    
    def _make_request(self, url: str) -> Dict:
        """
        发起HTTP请求
        
        Args:
            url: 请求URL
            
        Returns:
            请求结果字典
        """
        response_data = {
            'success': False,
            'response': None,
            'final_url': '',
            'redirect_chain': [],
            'response_time': 0.0,
            'retry_count': 0,
            'error': '',
            'failure_reason': ''
        }
        
        for attempt in range(self.retry_times + 1):
            try:
                start_time = time.time()
                
                # 发起请求
                session = self._get_session()
                response = session.get(
                    url, 
                    timeout=self.timeout,
                    verify=self.verify_ssl,
                    allow_redirects=True
                )
                
                response_time = time.time() - start_time
                
                # 记录重定向链
                redirect_chain = [url]
                if response.history:
                    for resp in response.history:
                        redirect_chain.append(resp.url)
                redirect_chain.append(response.url)
                
                response_data.update({
                    'success': True,
                    'response': response,
                    'final_url': response.url,
                    'redirect_chain': redirect_chain,
                    'response_time': response_time,
                    'retry_count': attempt
                })
                
                logger.debug(f"请求成功: {url} -> {response.url}, 状态码: {response.status_code}")
                break
                
            except requests.exceptions.Timeout:
                error_msg = f"请求超时 (第{attempt + 1}次尝试)"
                logger.warning(f"{error_msg}: {url}")
                response_data['error'] = error_msg
                response_data['failure_reason'] = 'timeout'
                response_data['retry_count'] = attempt
                
            except requests.exceptions.SSLError as e:
                error_msg = f"SSL证书错误: {str(e)} (第{attempt + 1}次尝试)"
                logger.warning(f"{error_msg}: {url}")
                response_data['error'] = error_msg
                response_data['failure_reason'] = 'ssl_error'
                response_data['retry_count'] = attempt
                
            except requests.exceptions.ConnectionError as e:
                # 进一步分析连接错误原因
                error_str = str(e).lower()
                if 'ssl' in error_str or 'certificate' in error_str:
                    failure_reason = 'ssl_error'
                    error_msg = f"SSL连接错误: {str(e)} (第{attempt + 1}次尝试)"
                elif 'name resolution' in error_str or 'nodename' in error_str:
                    failure_reason = 'dns_error'
                    error_msg = f"域名解析失败: {str(e)} (第{attempt + 1}次尝试)"
                else:
                    failure_reason = 'connection_error'
                    error_msg = f"连接错误: {str(e)} (第{attempt + 1}次尝试)"
                
                logger.warning(f"{error_msg}: {url}")
                response_data['error'] = error_msg
                response_data['failure_reason'] = failure_reason
                response_data['retry_count'] = attempt
                
            except requests.exceptions.RequestException as e:
                error_msg = f"请求异常: {str(e)} (第{attempt + 1}次尝试)"
                logger.warning(f"{error_msg}: {url}")
                response_data['error'] = error_msg
                response_data['failure_reason'] = 'request_error'
                response_data['retry_count'] = attempt
                
            # 如果不是最后一次尝试，等待一段时间再重试
            if attempt < self.retry_times:
                time.sleep(2 ** attempt)  # 指数退避
        
        return response_data
    
    def _analyze_response(self, result: DetectionResult, response_data: Dict) -> DetectionResult:
        """
        分析HTTP响应，判断检测状态
        
        Args:
            result: 检测结果对象
            response_data: 响应数据
            
        Returns:
            更新后的检测结果
        """
        response = response_data['response']
        
        # 基础信息
        result.final_url = response_data['final_url']
        result.response_time = response_data['response_time']
        result.http_status_code = response.status_code
        result.redirect_chain = response_data['redirect_chain']
        result.retry_count = response_data['retry_count']
        
        # 页面内容信息
        try:
            result.page_content_length = len(response.content)
            
            # 尝试提取页面标题
            if 'text/html' in response.headers.get('content-type', '').lower():
                import re
                title_match = re.search(r'<title[^>]*>(.*?)</title>', response.text, re.IGNORECASE | re.DOTALL)
                if title_match:
                    result.page_title = title_match.group(1).strip()[:200]  # 限制长度
        except Exception as e:
            logger.warning(f"解析页面内容失败: {e}")
        
        # 判断检测状态
        if response.status_code >= 400:
            result.status = 'failed'
            result.error_message = f"HTTP错误: {response.status_code}"
        else:
            # 根据URL重定向情况判断状态
            result.status = detect_url_redirect_type(result.original_url, result.final_url)
            
            # 补充状态判断逻辑
            if result.status == 'standard':
                logger.info(f"标准解析: {result.original_url}")
            elif result.status == 'redirect':
                logger.info(f"跳转解析: {result.original_url} -> {result.final_url}")
            else:
                logger.info(f"访问成功但状态未知: {result.original_url}")
        
        return result
    
    def detect_batch_websites(self, urls: List[str], callback=None, 
                            use_async: bool = True) -> List[DetectionResult]:
        """
        批量检测网站（支持异步和同步模式）
        
        Args:
            urls: 网站URL列表
            callback: 进度回调函数
            use_async: 是否使用异步检测（默认True）
            
        Returns:
            检测结果列表
        """
        if not urls:
            return []
        
        # 启动内存监控
        if ASYNC_SUPPORT:
            memory_manager = get_memory_manager()
            if not memory_manager.is_monitoring:
                memory_manager.start_monitoring()
        
        # 根据网站数量和系统资源选择检测模式
        should_use_async = (use_async and ASYNC_SUPPORT and 
                           len(urls) >= 10)  # 10个以上网站使用异步
        
        if should_use_async:
            logger.info(f"使用异步模式检测 {len(urls)} 个网站")
            return self._detect_batch_async(urls, callback)
        else:
            logger.info(f"使用同步模式检测 {len(urls)} 个网站，最大并发数: {self.max_concurrent}")
            return self._detect_batch_sync(urls, callback)
    
    def _detect_batch_sync(self, urls: List[str], callback=None) -> List[DetectionResult]:
        """同步批量检测（原有实现）"""
        start_time = time.time()
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
            # 提交所有检测任务
            future_to_url = {
                executor.submit(self.detect_single_website, url): url 
                for url in urls
            }
            
            # 收集结果
            completed_count = 0
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"检测任务异常: {url}, 错误: {e}")
                    # 创建失败结果
                    error_result = DetectionResult()
                    error_result.original_url = url
                    error_result.status = 'failed'
                    error_result.error_message = f"任务执行异常: {str(e)}"
                    results.append(error_result)
                
                completed_count += 1
                
                # 调用进度回调
                if callback:
                    try:
                        callback(completed_count, len(urls), result)
                    except Exception as e:
                        logger.warning(f"进度回调异常: {e}")
        
        total_time = time.time() - start_time
        logger.info(f"同步批量检测完成，共检测 {len(results)} 个网站，耗时: {total_time:.2f}秒")
        
        # 按原始顺序排序结果 - 修复结果顺序错乱的bug
        url_to_result = {result.original_url: result for result in results}
        ordered_results = []
        for url in urls:
            result = url_to_result.get(url)
            if result is None:
                # 如果没有找到对应结果，创建一个失败结果
                error_result = DetectionResult()
                error_result.original_url = url
                error_result.status = 'failed'
                error_result.error_message = "检测结果丢失"
                ordered_results.append(error_result)
            else:
                ordered_results.append(result)
        
        logger.info(f"结果排序完成，按原始URL顺序返回 {len(ordered_results)} 个结果")
        
        # 统计结果
        self._log_batch_statistics(ordered_results)
        
        return ordered_results
    
    def _detect_batch_async(self, urls: List[str], callback=None) -> List[DetectionResult]:
        """异步批量检测"""
        try:
            # 在事件循环中运行异步检测
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                return loop.run_until_complete(self._async_detect_websites(urls, callback))
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"异步检测失败，回退到同步模式: {e}")
            return self._detect_batch_sync(urls, callback)
    
    async def _async_detect_websites(self, urls: List[str], callback=None) -> List[DetectionResult]:
        """异步检测核心逻辑"""
        start_time = time.time()
        
        # 创建异步检测配置
        config = AsyncDetectionConfig(
            max_concurrent=min(200, len(urls) * 2),  # 根据网站数量动态调整
            max_per_host=30,
            timeout_total=self.timeout,
            verify_ssl=self.verify_ssl
        )
        
        # 使用异步检测器
        async with AsyncWebsiteDetector(config) as detector:
            results = await detector.detect_websites(urls, callback)
        
        total_time = time.time() - start_time
        logger.info(f"异步批量检测完成，共检测 {len(results)} 个网站，耗时: {total_time:.2f}秒")
        
        # 统计结果
        self._log_batch_statistics(results)
        
        return results
    
    def _log_batch_statistics(self, results: List[DetectionResult]):
        """记录批量检测统计信息"""
        total = len(results)
        standard_count = sum(1 for r in results if r.status == 'standard')
        redirect_count = sum(1 for r in results if r.status == 'redirect')
        failed_count = sum(1 for r in results if r.status == 'failed')
        
        avg_response_time = sum(r.response_time for r in results if r.response_time > 0) / max(1, total - failed_count)
        
        logger.info(f"批量检测统计:")
        logger.info(f"  总数: {total}")
        logger.info(f"  标准解析: {standard_count} ({standard_count/total*100:.1f}%)")
        logger.info(f"  跳转解析: {redirect_count} ({redirect_count/total*100:.1f}%)")
        logger.info(f"  无法访问: {failed_count} ({failed_count/total*100:.1f}%)")
        logger.info(f"  平均响应时间: {avg_response_time:.2f}s")
    
    def close(self):
        """关闭检测器，清理资源"""
        if hasattr(self, 'session'):
            self.session.close()
        logger.info("网站检测器已关闭") 