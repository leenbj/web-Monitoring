"""
网址监控工具 - 任务调度服务
负责定时任务的创建、管理和执行
"""

import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from typing import Optional, Callable, Dict, Any
import time

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskScheduler:
    """任务调度器类"""
    
    def __init__(self):
        """初始化调度器"""
        # 配置作业存储和执行器
        jobstores = {
            'default': MemoryJobStore()
        }
        executors = {
            'default': ThreadPoolExecutor(20)
        }
        job_defaults = {
            'coalesce': False,
            'max_instances': 3
        }
        
        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='Asia/Shanghai'
        )
        self.running = False
        
    def start(self):
        """启动调度器"""
        if not self.running:
            try:
                self.scheduler.start()
                self.running = True
                logger.info("任务调度器启动成功")
            except Exception as e:
                logger.error(f"任务调度器启动失败: {e}")
                raise
    
    def stop(self):
        """停止调度器"""
        if self.running:
            try:
                self.scheduler.shutdown()
                self.running = False
                logger.info("任务调度器已停止")
            except Exception as e:
                logger.error(f"任务调度器停止失败: {e}")
    
    def add_interval_job(
        self, 
        func: Callable, 
        job_id: str, 
        minutes: int = 10,
        **kwargs
    ) -> bool:
        """
        添加间隔任务
        
        Args:
            func: 要执行的函数
            job_id: 任务ID
            minutes: 间隔分钟数
            **kwargs: 其他参数
            
        Returns:
            bool: 是否添加成功
        """
        try:
            # 移除同名任务
            self.remove_job(job_id)
            
            # 添加新任务
            self.scheduler.add_job(
                func=func,
                trigger='interval',
                minutes=minutes,
                id=job_id,
                replace_existing=True,
                **kwargs
            )
            
            logger.info(f"已添加间隔任务: {job_id}, 间隔: {minutes}分钟")
            return True
            
        except Exception as e:
            logger.error(f"添加间隔任务失败: {e}")
            return False
    
    def add_cron_job(
        self, 
        func: Callable, 
        job_id: str, 
        cron_expression: str,
        **kwargs
    ) -> bool:
        """
        添加Cron任务
        
        Args:
            func: 要执行的函数
            job_id: 任务ID
            cron_expression: Cron表达式
            **kwargs: 其他参数
            
        Returns:
            bool: 是否添加成功
        """
        try:
            # 解析cron表达式
            cron_parts = cron_expression.split()
            if len(cron_parts) != 5:
                raise ValueError("Cron表达式格式错误")
                
            minute, hour, day, month, day_of_week = cron_parts
            
            # 移除同名任务
            self.remove_job(job_id)
            
            # 添加新任务
            self.scheduler.add_job(
                func=func,
                trigger='cron',
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week,
                id=job_id,
                replace_existing=True,
                **kwargs
            )
            
            logger.info(f"已添加Cron任务: {job_id}, 表达式: {cron_expression}")
            return True
            
        except Exception as e:
            logger.error(f"添加Cron任务失败: {e}")
            return False
    
    def add_one_time_job(
        self, 
        func: Callable, 
        job_id: str, 
        run_date: datetime,
        **kwargs
    ) -> bool:
        """
        添加一次性任务
        
        Args:
            func: 要执行的函数
            job_id: 任务ID
            run_date: 执行时间
            **kwargs: 其他参数
            
        Returns:
            bool: 是否添加成功
        """
        try:
            # 移除同名任务
            self.remove_job(job_id)
            
            # 添加新任务
            self.scheduler.add_job(
                func=func,
                trigger='date',
                run_date=run_date,
                id=job_id,
                replace_existing=True,
                **kwargs
            )
            
            logger.info(f"已添加一次性任务: {job_id}, 执行时间: {run_date}")
            return True
            
        except Exception as e:
            logger.error(f"添加一次性任务失败: {e}")
            return False
    
    def remove_job(self, job_id: str) -> bool:
        """
        移除任务
        
        Args:
            job_id: 任务ID
            
        Returns:
            bool: 是否移除成功
        """
        try:
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
                logger.info(f"已移除任务: {job_id}")
            return True
        except Exception as e:
            logger.error(f"移除任务失败: {e}")
            return False
    
    def pause_job(self, job_id: str) -> bool:
        """
        暂停任务
        
        Args:
            job_id: 任务ID
            
        Returns:
            bool: 是否暂停成功
        """
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"已暂停任务: {job_id}")
            return True
        except Exception as e:
            logger.error(f"暂停任务失败: {e}")
            return False
    
    def resume_job(self, job_id: str) -> bool:
        """
        恢复任务
        
        Args:
            job_id: 任务ID
            
        Returns:
            bool: 是否恢复成功
        """
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"已恢复任务: {job_id}")
            return True
        except Exception as e:
            logger.error(f"恢复任务失败: {e}")
            return False
    
    def get_job_info(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务信息
        
        Args:
            job_id: 任务ID
            
        Returns:
            Dict: 任务信息
        """
        try:
            job = self.scheduler.get_job(job_id)
            if not job:
                return None
                
            return {
                'id': job.id,
                'name': job.name,
                'func': str(job.func),
                'trigger': str(job.trigger),
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'coalesce': job.coalesce,
                'max_instances': job.max_instances
            }
        except Exception as e:
            logger.error(f"获取任务信息失败: {e}")
            return None
    
    def get_all_jobs(self) -> list:
        """
        获取所有任务信息
        
        Returns:
            list: 所有任务信息列表
        """
        try:
            jobs = []
            for job in self.scheduler.get_jobs():
                job_info = {
                    'id': job.id,
                    'name': job.name,
                    'func': str(job.func),
                    'trigger': str(job.trigger),
                    'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                    'coalesce': job.coalesce,
                    'max_instances': job.max_instances
                }
                jobs.append(job_info)
            return jobs
        except Exception as e:
            logger.error(f"获取所有任务信息失败: {e}")
            return []
    
    def is_running(self) -> bool:
        """
        检查调度器是否运行中
        
        Returns:
            bool: 是否运行中
        """
        return self.running and self.scheduler.running
    
    def start_task(self, task_id: int, interval_minutes: int) -> bool:
        """
        启动检测任务的定时调度
        
        Args:
            task_id: 任务ID
            interval_minutes: 检测间隔(分钟)
            
        Returns:
            bool: 是否启动成功
        """
        try:
            # 启动调度器
            if not self.running:
                self.start()
            
            # 任务执行函数
            def run_detection_task():
                """执行检测任务"""
                try:
                    # 导入这里避免循环导入
                    from ..api.tasks import execute_detection_task
                    from ..database import get_db
                    from ..models import DetectionTask
                    
                    with get_db() as db:
                        task = db.query(DetectionTask).filter(DetectionTask.id == task_id).first()
                        if task and task.is_active:
                            logger.info(f"定时执行检测任务: {task_id}")
                            execute_detection_task(task_id)
                        else:
                            logger.info(f"任务 {task_id} 未激活或不存在，跳过执行")
                except Exception as e:
                    logger.error(f"定时执行任务 {task_id} 失败: {e}")
            
            # 添加间隔任务
            job_id = f"detection_task_{task_id}"
            return self.add_interval_job(
                func=run_detection_task,
                job_id=job_id,
                minutes=interval_minutes
            )
            
        except Exception as e:
            logger.error(f"启动任务调度失败: {e}")
            return False
    
    def stop_task(self, task_id: int) -> bool:
        """
        停止检测任务的定时调度
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否停止成功
        """
        try:
            job_id = f"detection_task_{task_id}"
            return self.remove_job(job_id)
        except Exception as e:
            logger.error(f"停止任务调度失败: {e}")
            return False

# 全局调度器实例
scheduler = TaskScheduler() 