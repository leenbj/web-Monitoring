"""
内存监控服务
用于监控和优化应用程序的内存使用
"""

import gc
import logging
import threading
import time
import psutil
import os
from typing import Dict, Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class MemoryManager:
    """内存管理器"""
    
    def __init__(self, 
                 max_memory_mb: int = 512,
                 cleanup_threshold: float = 0.8,
                 check_interval: int = 60):
        """
        初始化内存管理器
        
        Args:
            max_memory_mb: 最大内存使用量(MB)
            cleanup_threshold: 清理阈值(比例)
            check_interval: 检查间隔(秒)
        """
        self.max_memory_mb = max_memory_mb
        self.cleanup_threshold = cleanup_threshold
        self.check_interval = check_interval
        self.is_monitoring = False
        self.monitor_thread = None
        self.cleanup_callbacks = []
        
        # 统计信息
        self.stats = {
            'total_checks': 0,
            'cleanup_triggered': 0,
            'max_memory_seen': 0.0,
            'last_cleanup_time': None
        }
        
        logger.info(f"内存管理器初始化: 最大内存={max_memory_mb}MB, "
                   f"清理阈值={cleanup_threshold*100}%, 检查间隔={check_interval}s")
    
    def start_monitoring(self):
        """开始内存监控"""
        if self.is_monitoring:
            logger.warning("内存监控已在运行")
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("内存监控已启动")
    
    def stop_monitoring(self):
        """停止内存监控"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)
        logger.info("内存监控已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.is_monitoring:
            try:
                self._check_memory()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"内存监控异常: {e}")
                time.sleep(self.check_interval)
    
    def _check_memory(self):
        """检查内存使用情况"""
        try:
            # 获取当前进程内存使用
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            # 更新统计
            self.stats['total_checks'] += 1
            if memory_mb > self.stats['max_memory_seen']:
                self.stats['max_memory_seen'] = memory_mb
            
            # 检查是否需要清理
            usage_ratio = memory_mb / self.max_memory_mb
            
            if usage_ratio >= self.cleanup_threshold:
                logger.warning(f"内存使用过高: {memory_mb:.1f}MB ({usage_ratio:.1%}), 触发清理")
                self._trigger_cleanup()
            else:
                logger.debug(f"内存使用正常: {memory_mb:.1f}MB ({usage_ratio:.1%})")
                
        except Exception as e:
            logger.error(f"检查内存时出错: {e}")
    
    def _trigger_cleanup(self):
        """触发内存清理"""
        try:
            # 强制垃圾回收
            collected = gc.collect()
            logger.info(f"垃圾回收完成，回收对象数: {collected}")
            
            # 执行注册的清理回调
            for callback in self.cleanup_callbacks:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"执行清理回调时出错: {e}")
            
            # 更新统计
            self.stats['cleanup_triggered'] += 1
            self.stats['last_cleanup_time'] = datetime.now()
            
        except Exception as e:
            logger.error(f"内存清理时出错: {e}")
    
    def register_cleanup_callback(self, callback: Callable):
        """注册清理回调函数"""
        self.cleanup_callbacks.append(callback)
        logger.info("已注册内存清理回调")
    
    def get_memory_info(self) -> Dict:
        """获取内存信息"""
        try:
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            
            return {
                'rss_mb': memory_info.rss / 1024 / 1024,  # 物理内存
                'vms_mb': memory_info.vms / 1024 / 1024,  # 虚拟内存
                'percent': process.memory_percent(),       # 内存使用百分比
                'max_memory_mb': self.max_memory_mb,
                'threshold': self.cleanup_threshold,
                'stats': self.stats.copy()
            }
        except Exception as e:
            logger.error(f"获取内存信息时出错: {e}")
            return {}
    
    def force_cleanup(self):
        """强制执行内存清理"""
        logger.info("强制执行内存清理")
        self._trigger_cleanup()


# 全局内存管理器实例
_global_memory_manager: Optional[MemoryManager] = None


def get_memory_manager() -> MemoryManager:
    """获取全局内存管理器"""
    global _global_memory_manager
    if _global_memory_manager is None:
        _global_memory_manager = MemoryManager()
    return _global_memory_manager


def start_global_memory_monitoring():
    """启动全局内存监控"""
    manager = get_memory_manager()
    manager.start_monitoring()


def stop_global_memory_monitoring():
    """停止全局内存监控"""
    global _global_memory_manager
    if _global_memory_manager:
        _global_memory_manager.stop_monitoring()


def register_global_cleanup_callback(callback: Callable):
    """注册全局清理回调"""
    manager = get_memory_manager()
    manager.register_cleanup_callback(callback)