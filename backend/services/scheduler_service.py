"""
调度服务
管理检测任务和定时清理任务
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor

from .detection_service import DetectionService
from .file_cleanup_service import FileCleanupService
from ..database import get_db
from ..models import DetectionTask
from ..utils.helpers import get_beijing_time

logger = logging.getLogger(__name__)


class SchedulerService:
    """调度服务"""
    
    def __init__(self):
        self.detection_service = DetectionService()
        self.cleanup_service = FileCleanupService()
        self.is_running = False
        self.scheduler_thread = None
        self.executor = ThreadPoolExecutor(max_workers=2)  # 从5降到2，减少资源占用
        self.running_tasks = {}
        self._shutdown = False
        self._task_lock = threading.Lock()  # 添加任务锁防止竞态条件
        
        # 文件清理配置
        self.cleanup_interval_hours = 24  # 24小时清理一次
        self.last_cleanup_time = None
        
        logger.info("调度服务初始化完成")
    
    def start(self):
        """启动调度服务"""
        if self.is_running:
            logger.warning("调度服务已在运行")
            return
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("调度服务已启动")
    
    def stop(self):
        """停止调度服务"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # 等待调度线程结束
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        # 关闭线程池
        self.executor.shutdown(wait=True)
        
        logger.info("调度服务已停止")
    
    def _scheduler_loop(self):
        """调度循环"""
        logger.info("调度循环开始")
        
        while self.is_running and not self._shutdown:
            try:
                current_time = get_beijing_time()
                
                # 执行检测任务调度
                self._schedule_detection_tasks(current_time)
                
                # 执行失败网站监控调度
                self._schedule_failed_monitor_tasks(current_time)
                
                # 执行文件清理调度
                self._schedule_file_cleanup(current_time)
                
                # 分段休眠，提高响应性（从60秒分为6次10秒）
                for i in range(6):
                    if self._shutdown:
                        break
                    time.sleep(10)
                
            except Exception as e:
                logger.error(f"调度循环异常: {e}")
                if not self._shutdown:
                    time.sleep(30)  # 异常时休眠30秒
    
    def _schedule_detection_tasks(self, current_time: datetime):
        """调度检测任务"""
        try:
            with get_db() as db:
                # 获取活跃的任务
                active_tasks = db.query(DetectionTask).filter(
                    DetectionTask.is_active == True
                ).all()
                
                for task in active_tasks:
                    # 检查是否需要执行
                    if self._should_run_task(task, current_time):
                        # 使用锁防止竞态条件
                        with self._task_lock:
                            # 检查任务是否已在运行
                            if task.id not in self.running_tasks:
                                # 提交任务到线程池
                                future = self.executor.submit(self._run_detection_task, task.id)
                                self.running_tasks[task.id] = future
                                
                                logger.info(f"提交检测任务: {task.name} (ID: {task.id})")
                            else:
                                logger.debug(f"检测任务 {task.name} 正在运行中，跳过")
                
                # 清理已完成的任务
                with self._task_lock:
                    completed_tasks = []
                    for task_id, future in self.running_tasks.items():
                        if future.done():
                            completed_tasks.append(task_id)
                    
                    for task_id in completed_tasks:
                        del self.running_tasks[task_id]
                
        except Exception as e:
            logger.error(f"调度检测任务失败: {e}")
    
    def _schedule_failed_monitor_tasks(self, current_time: datetime):
        """调度失败网站监控任务"""
        try:
            from ..models import FailedSiteMonitorTask
            
            with get_db() as db:
                # 获取活跃的失败监控任务
                monitor_tasks = db.query(FailedSiteMonitorTask).filter(
                    FailedSiteMonitorTask.is_active == True
                ).all()
                
                for monitor_task in monitor_tasks:
                    # 检查是否需要执行
                    if self._should_run_monitor_task(monitor_task, current_time):
                        # 检查任务是否已在运行
                        monitor_key = f"monitor_{monitor_task.id}"
                        if monitor_key not in self.running_tasks:
                            # 提交监控任务到线程池
                            future = self.executor.submit(self._run_failed_monitor_task, monitor_task.id)
                            self.running_tasks[monitor_key] = future
                            
                            logger.info(f"提交失败监控任务: {monitor_task.name} (ID: {monitor_task.id})")
                        else:
                            logger.debug(f"失败监控任务 {monitor_task.name} 正在运行中，跳过")
                
        except Exception as e:
            logger.error(f"调度失败监控任务失败: {e}")
    
    def _should_run_monitor_task(self, monitor_task, current_time: datetime) -> bool:
        """判断失败监控任务是否应该运行"""
        if not monitor_task.is_active or monitor_task.is_running:
            return False
        
        # 如果从未运行过，立即执行
        if monitor_task.last_run_at is None:
            return True
        
        # 检查时间间隔
        try:
            # 统一使用naive datetime进行比较
            last_run_time = monitor_task.last_run_at
            compare_current_time = current_time
            
            # 如果当前时间有时区信息，转换为naive
            if compare_current_time.tzinfo is not None:
                compare_current_time = compare_current_time.replace(tzinfo=None)
            
            # 如果数据库时间有时区信息，转换为naive  
            if last_run_time.tzinfo is not None:
                last_run_time = last_run_time.replace(tzinfo=None)
            
            time_since_last_run = compare_current_time - last_run_time
            should_run = time_since_last_run.total_seconds() >= monitor_task.interval_hours * 3600
            
            logger.debug(f"失败监控任务 {monitor_task.id} 时间检查: 上次运行={last_run_time}, "
                        f"当前时间={compare_current_time}, 间隔={time_since_last_run.total_seconds()}秒, "
                        f"应该运行={should_run}")
            
            return should_run
            
        except Exception as e:
            logger.error(f"监控任务时间比较异常: {e}")
            return True
    
    def _run_failed_monitor_task(self, monitor_task_id: int):
        """运行失败网站监控任务"""
        try:
            logger.info(f"开始执行失败网站监控任务 ID: {monitor_task_id}")
            
            from ..services.failed_site_monitor_service import FailedSiteMonitorService
            monitor_service = FailedSiteMonitorService()
            
            # 执行监控
            result = monitor_service.run_failed_site_monitor_task(monitor_task_id)
            
            if result:
                logger.info(f"失败网站监控任务 {monitor_task_id} 执行成功")
            else:
                logger.warning(f"失败网站监控任务 {monitor_task_id} 执行失败")
            
        except Exception as e:
            logger.error(f"执行失败网站监控任务 {monitor_task_id} 异常: {e}")
    
    def _schedule_file_cleanup(self, current_time: datetime):
        """调度文件清理任务"""
        try:
            # 检查是否需要执行文件清理
            should_cleanup = False
            
            if self.last_cleanup_time is None:
                # 首次运行，执行清理
                should_cleanup = True
            else:
                # 检查是否达到清理间隔
                time_since_last_cleanup = current_time - self.last_cleanup_time
                if time_since_last_cleanup.total_seconds() >= self.cleanup_interval_hours * 3600:
                    should_cleanup = True
            
            if should_cleanup:
                logger.info("开始执行定期文件清理")
                
                # 在线程池中执行清理
                future = self.executor.submit(self._run_file_cleanup)
                
                # 更新最后清理时间
                self.last_cleanup_time = current_time
                
        except Exception as e:
            logger.error(f"调度文件清理失败: {e}")
    
    def _should_run_task(self, task: DetectionTask, current_time: datetime) -> bool:
        """判断任务是否应该运行"""
        if not task.is_active or task.is_running:
            return False
        
        # 如果从未运行过，立即执行
        if task.last_run_at is None:
            return True
        
        # 检查时间间隔 - 确保时区兼容性（统一使用naive datetime）
        try:
            # 统一使用naive datetime进行比较
            last_run_time = task.last_run_at
            compare_current_time = current_time
            
            # 如果当前时间有时区信息，转换为naive
            if compare_current_time.tzinfo is not None:
                compare_current_time = compare_current_time.replace(tzinfo=None)
            
            # 如果数据库时间有时区信息，转换为naive  
            if last_run_time.tzinfo is not None:
                last_run_time = last_run_time.replace(tzinfo=None)
            
            time_since_last_run = compare_current_time - last_run_time
            should_run = time_since_last_run.total_seconds() >= task.interval_hours * 3600
            
            logger.debug(f"任务 {task.id} 时间检查: 上次运行={last_run_time}, 当前时间={compare_current_time}, "
                        f"间隔={time_since_last_run.total_seconds()}秒, 应该运行={should_run}")
            
            return should_run
            
        except Exception as e:
            logger.error(f"时间比较异常: {e}")
            # 发生异常时，如果超过1小时没运行，则执行任务
            return True
    
    def _run_detection_task(self, task_id: int):
        """运行检测任务"""
        try:
            logger.info(f"开始执行检测任务 ID: {task_id}")
            
            # 执行检测
            result = self.detection_service.run_task(task_id)
            
            if result:
                logger.info(f"检测任务 {task_id} 执行成功")
            else:
                logger.warning(f"检测任务 {task_id} 执行失败")
            
        except Exception as e:
            logger.error(f"执行检测任务 {task_id} 异常: {e}")
    
    def _run_file_cleanup(self):
        """运行文件清理任务"""
        try:
            logger.info("执行定期文件清理")
            result = self.cleanup_service.schedule_cleanup()
            
            if result:
                logger.info("定期文件清理执行成功")
            else:
                logger.warning("定期文件清理执行失败")
            
        except Exception as e:
            logger.error(f"执行文件清理异常: {e}")
    
    def get_status(self) -> Dict:
        """获取调度服务状态"""
        return {
            'is_running': self.is_running,
            'running_tasks_count': len(self.running_tasks),
            'running_task_ids': list(self.running_tasks.keys()),
            'last_cleanup_time': self.last_cleanup_time.isoformat() if self.last_cleanup_time else None,
            'next_cleanup_time': (self.last_cleanup_time + timedelta(hours=self.cleanup_interval_hours)).isoformat() 
                                if self.last_cleanup_time else None
        }
    
    def force_cleanup(self) -> bool:
        """强制执行文件清理"""
        try:
            logger.info("强制执行文件清理")
            result = self.cleanup_service.schedule_cleanup()
            
            if result:
                self.last_cleanup_time = get_beijing_time()
                logger.info("强制文件清理执行成功")
            else:
                logger.warning("强制文件清理执行失败")
            
            return result
            
        except Exception as e:
            logger.error(f"强制文件清理异常: {e}")
            return False
    
    def shutdown(self):
        """关闭调度器，清理资源"""
        try:
            logger.info("正在关闭调度服务...")
            self._shutdown = True
            self.is_running = False
            
            # 等待线程池任务完成
            if self.executor:
                self.executor.shutdown(wait=True, timeout=30)
                logger.info("线程池已关闭")
            
            # 等待调度线程结束
            if self.scheduler_thread and self.scheduler_thread.is_alive():
                self.scheduler_thread.join(timeout=10)
                
            logger.info("调度服务已关闭")
            
        except Exception as e:
            logger.error(f"关闭调度服务时出错: {e}")
    
    def __del__(self):
        """析构函数"""
        self.shutdown() 