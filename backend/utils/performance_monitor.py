"""
性能监控工具
用于监控应用性能和资源使用情况
"""

import time
import psutil
import threading
import logging
from datetime import datetime, timedelta
from collections import deque
from functools import wraps
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, max_records: int = 1000):
        self.max_records = max_records
        self.metrics = {
            'cpu_usage': deque(maxlen=max_records),
            'memory_usage': deque(maxlen=max_records),
            'disk_usage': deque(maxlen=max_records),
            'api_response_times': deque(maxlen=max_records),
            'database_query_times': deque(maxlen=max_records),
            'active_connections': deque(maxlen=max_records),
        }
        self.start_time = time.time()
        self.monitoring = False
        self.monitor_thread = None
        
    def start_monitoring(self, interval: int = 30):
        """开始监控"""
        if self.monitoring:
            return
            
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info(f"性能监控已启动，监控间隔: {interval}秒")
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("性能监控已停止")
    
    def _monitor_loop(self, interval: int):
        """监控循环"""
        while self.monitoring:
            try:
                timestamp = datetime.now()
                
                # 收集系统指标
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                # 记录指标
                self.metrics['cpu_usage'].append({
                    'timestamp': timestamp,
                    'value': cpu_percent
                })
                
                self.metrics['memory_usage'].append({
                    'timestamp': timestamp,
                    'value': memory.percent
                })
                
                self.metrics['disk_usage'].append({
                    'timestamp': timestamp,
                    'value': (disk.used / disk.total) * 100
                })
                
                # 检查资源使用情况
                self._check_resource_alerts(cpu_percent, memory.percent)
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"性能监控出错: {e}")
                time.sleep(interval)
    
    def _check_resource_alerts(self, cpu_percent: float, memory_percent: float):
        """检查资源告警"""
        if cpu_percent > 80:
            logger.warning(f"CPU使用率过高: {cpu_percent:.1f}%")
        
        if memory_percent > 80:
            logger.warning(f"内存使用率过高: {memory_percent:.1f}%")
    
    def record_api_response_time(self, endpoint: str, response_time: float):
        """记录API响应时间"""
        self.metrics['api_response_times'].append({
            'timestamp': datetime.now(),
            'endpoint': endpoint,
            'response_time': response_time
        })
    
    def record_database_query_time(self, query_type: str, query_time: float):
        """记录数据库查询时间"""
        self.metrics['database_query_times'].append({
            'timestamp': datetime.now(),
            'query_type': query_type,
            'query_time': query_time
        })
    
    def get_current_stats(self) -> Dict:
        """获取当前统计信息"""
        try:
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # 计算平均响应时间
            recent_api_times = [
                record['response_time'] 
                for record in list(self.metrics['api_response_times'])[-100:]
            ]
            avg_api_time = sum(recent_api_times) / len(recent_api_times) if recent_api_times else 0
            
            # 计算平均查询时间
            recent_db_times = [
                record['query_time'] 
                for record in list(self.metrics['database_query_times'])[-100:]
            ]
            avg_db_time = sum(recent_db_times) / len(recent_db_times) if recent_db_times else 0
            
            return {
                'uptime': time.time() - self.start_time,
                'cpu_usage': cpu_percent,
                'memory_usage': memory.percent,
                'memory_available': memory.available / (1024**3),  # GB
                'disk_usage': (disk.used / disk.total) * 100,
                'disk_free': disk.free / (1024**3),  # GB
                'avg_api_response_time': avg_api_time,
                'avg_database_query_time': avg_db_time,
                'total_api_requests': len(self.metrics['api_response_times']),
                'total_database_queries': len(self.metrics['database_query_times']),
            }
        except Exception as e:
            logger.error(f"获取性能统计失败: {e}")
            return {}
    
    def get_performance_report(self, hours: int = 1) -> Dict:
        """获取性能报告"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        report = {
            'period_hours': hours,
            'cpu_stats': self._calculate_stats('cpu_usage', cutoff_time),
            'memory_stats': self._calculate_stats('memory_usage', cutoff_time),
            'api_stats': self._calculate_api_stats(cutoff_time),
            'database_stats': self._calculate_db_stats(cutoff_time),
        }
        
        return report
    
    def _calculate_stats(self, metric_name: str, cutoff_time: datetime) -> Dict:
        """计算统计数据"""
        records = [
            record for record in self.metrics[metric_name]
            if record['timestamp'] >= cutoff_time
        ]
        
        if not records:
            return {'count': 0}
        
        values = [record['value'] for record in records]
        
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'current': values[-1] if values else 0
        }
    
    def _calculate_api_stats(self, cutoff_time: datetime) -> Dict:
        """计算API统计数据"""
        records = [
            record for record in self.metrics['api_response_times']
            if record['timestamp'] >= cutoff_time
        ]
        
        if not records:
            return {'count': 0}
        
        response_times = [record['response_time'] for record in records]
        endpoints = {}
        
        for record in records:
            endpoint = record['endpoint']
            if endpoint not in endpoints:
                endpoints[endpoint] = []
            endpoints[endpoint].append(record['response_time'])
        
        endpoint_stats = {}
        for endpoint, times in endpoints.items():
            endpoint_stats[endpoint] = {
                'count': len(times),
                'avg_time': sum(times) / len(times),
                'max_time': max(times),
                'min_time': min(times)
            }
        
        return {
            'total_requests': len(records),
            'avg_response_time': sum(response_times) / len(response_times),
            'max_response_time': max(response_times),
            'min_response_time': min(response_times),
            'endpoint_stats': endpoint_stats
        }
    
    def _calculate_db_stats(self, cutoff_time: datetime) -> Dict:
        """计算数据库统计数据"""
        records = [
            record for record in self.metrics['database_query_times']
            if record['timestamp'] >= cutoff_time
        ]
        
        if not records:
            return {'count': 0}
        
        query_times = [record['query_time'] for record in records]
        
        return {
            'total_queries': len(records),
            'avg_query_time': sum(query_times) / len(query_times),
            'max_query_time': max(query_times),
            'min_query_time': min(query_times),
            'slow_queries': len([t for t in query_times if t > 1.0])  # 超过1秒的查询
        }


# 全局性能监控实例
performance_monitor = PerformanceMonitor()


def monitor_api_performance(func):
    """API性能监控装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            end_time = time.time()
            response_time = end_time - start_time
            
            # 获取端点名称
            endpoint = getattr(func, '__name__', 'unknown')
            if hasattr(func, 'view_class'):
                endpoint = f"{func.view_class.__name__}.{endpoint}"
            
            performance_monitor.record_api_response_time(endpoint, response_time)
            
            # 记录慢请求
            if response_time > 2.0:
                logger.warning(f"慢API请求: {endpoint} 耗时 {response_time:.2f}秒")
    
    return wrapper


def monitor_database_performance(query_type: str = 'unknown'):
    """数据库性能监控装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                end_time = time.time()
                query_time = end_time - start_time
                
                performance_monitor.record_database_query_time(query_type, query_time)
                
                # 记录慢查询
                if query_time > 1.0:
                    logger.warning(f"慢数据库查询: {query_type} 耗时 {query_time:.2f}秒")
        
        return wrapper
    return decorator
