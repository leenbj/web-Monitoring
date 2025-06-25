"""
内存管理服务
用于监控和优化应用程序内存使用
"""

import gc
import psutil
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Optional

from ..database import get_db
from ..models import DetectionRecord

logger = logging.getLogger(__name__)


class MemoryManager:
    """内存管理器"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.memory_threshold_mb = 512  # 内存警告阈值（MB）
        self.cleanup_threshold_mb = 256  # 自动清理阈值（MB）
        self.monitoring = False
        self.monitor_thread = None
        self.cleanup_interval = 300  # 5分钟检查一次
        
    def start_monitoring(self):
        """启动内存监控"""
        if self.monitoring:
            return
            
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("内存监控已启动")
    
    def stop_monitoring(self):
        """停止内存监控"""
        self.monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        logger.info("内存监控已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            try:
                self._check_memory_usage()
                time.sleep(self.cleanup_interval)
            except Exception as e:
                logger.error(f"内存监控异常: {e}")
                time.sleep(30)  # 异常后短暂休眠
    
    def _check_memory_usage(self):
        """检查内存使用情况"""
        try:
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            logger.info(f"当前内存使用: {memory_mb:.1f} MB")
            
            if memory_mb > self.memory_threshold_mb:
                logger.warning(f"内存使用过高: {memory_mb:.1f} MB")
                self._perform_cleanup()
            
            if memory_mb > self.cleanup_threshold_mb:
                self._aggressive_cleanup()
                
        except Exception as e:
            logger.error(f"检查内存使用失败: {e}")
    
    def _perform_cleanup(self):
        """执行基础清理"""
        try:
            # 强制垃圾回收
            collected = gc.collect()
            logger.info(f"垃圾回收清理了 {collected} 个对象")
            
            # 清理旧的检测记录（保留最近7天）
            self._cleanup_old_records()
            
        except Exception as e:
            logger.error(f"基础清理失败: {e}")
    
    def _aggressive_cleanup(self):
        """执行激进清理"""
        try:
            logger.warning("执行激进内存清理")
            
            # 多次垃圾回收
            for _ in range(3):
                gc.collect()
            
            # 清理更多旧记录（保留最近3天）
            self._cleanup_old_records(days=3)
            
            # 清理数据库连接池
            self._cleanup_database_connections()
            
        except Exception as e:
            logger.error(f"激进清理失败: {e}")
    
    def _cleanup_old_records(self, days: int = 7):
        """清理旧的检测记录"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with get_db() as db:
                # 计算要删除的记录数
                count = db.query(DetectionRecord).filter(
                    DetectionRecord.detected_at < cutoff_date
                ).count()
                
                if count > 0:
                    # 批量删除
                    db.query(DetectionRecord).filter(
                        DetectionRecord.detected_at < cutoff_date
                    ).delete()
                    db.commit()
                    
                    logger.info(f"清理了 {count} 条旧检测记录（{days}天前）")
                    
        except Exception as e:
            logger.error(f"清理旧记录失败: {e}")
    
    def _cleanup_database_connections(self):
        """清理数据库连接池"""
        try:
            from ..database import engine
            # 清理连接池中的无效连接
            engine.pool._invalidate()
            logger.info("数据库连接池已清理")
        except Exception as e:
            logger.error(f"清理数据库连接失败: {e}")
    
    def get_memory_stats(self) -> Dict:
        """获取内存统计信息"""
        try:
            memory_info = self.process.memory_info()
            memory_percent = self.process.memory_percent()
            
            return {
                'rss_mb': round(memory_info.rss / 1024 / 1024, 2),
                'vms_mb': round(memory_info.vms / 1024 / 1024, 2),
                'percent': round(memory_percent, 2),
                'threshold_mb': self.memory_threshold_mb,
                'cleanup_threshold_mb': self.cleanup_threshold_mb
            }
        except Exception as e:
            logger.error(f"获取内存统计失败: {e}")
            return {}
    
    def force_cleanup(self):
        """手动强制清理"""
        logger.info("手动触发内存清理")
        self._perform_cleanup()
        self._aggressive_cleanup()


# 全局内存管理器实例
memory_manager = MemoryManager()