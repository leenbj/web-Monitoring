"""
检测服务
负责执行检测任务
"""

import logging
from typing import List, Optional
from datetime import datetime

from .batch_detector import BatchDetectionService, BatchDetectionConfig
from ..database import get_db
from ..models import DetectionTask, Website, DetectionRecord
from ..utils.helpers import get_beijing_time

logger = logging.getLogger(__name__)


class DetectionService:
    """检测服务"""
    
    def __init__(self):
        # 使用优化的配置
        config = BatchDetectionConfig(
            batch_size=20,           # 降低批次大小
            max_concurrent=10,       # 降低并发数
            timeout_seconds=15,      # 降低超时时间
            retry_times=2,           # 降低重试次数
            enable_async=True,
            memory_limit_mb=256      # 降低内存限制
        )
        self.batch_service = BatchDetectionService(config)
        logger.info("检测服务初始化完成")
    
    def run_task(self, task_id: int) -> bool:
        """
        执行检测任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            执行是否成功
        """
        try:
            logger.info(f"开始执行检测任务 {task_id}")
            
            with get_db() as db:
                # 获取任务信息
                task = db.query(DetectionTask).filter(DetectionTask.id == task_id).first()
                if not task:
                    logger.error(f"任务 {task_id} 不存在")
                    return False
                
                if not task.is_active:
                    logger.warning(f"任务 {task_id} 未激活")
                    return False
                
                # 标记任务为运行中
                task.is_running = True
                db.commit()
                
                try:
                    # 获取任务关联的网站
                    websites = task.websites
                    if not websites:
                        logger.warning(f"任务 {task_id} 没有关联的网站")
                        return True
                    
                    # 提取URL列表
                    urls = [website.url for website in websites]
                    logger.info(f"任务 {task_id} 包含 {len(urls)} 个网站")
                    
                    # 执行批量检测
                    result = self.batch_service.detect_websites_sync(urls)
                    
                    # 保存检测结果
                    success = self._save_detection_results(task_id, websites, result)
                    
                    # 更新任务信息
                    from datetime import timedelta
                    current_time = get_beijing_time()
                    # 转换为naive datetime以保持数据库一致性
                    naive_current_time = current_time.replace(tzinfo=None)
                    task.last_run_at = naive_current_time
                    task.next_run_at = naive_current_time + timedelta(minutes=task.interval_minutes)
                    
                    db.commit()
                    
                    logger.info(f"任务 {task_id} 执行完成，成功: {success}")
                    return success
                    
                finally:
                    # 确保清除运行状态
                    task.is_running = False
                    db.commit()
                    
        except Exception as e:
            logger.error(f"执行任务 {task_id} 异常: {e}")
            
            # 清除运行状态
            try:
                with get_db() as db:
                    task = db.query(DetectionTask).filter(DetectionTask.id == task_id).first()
                    if task:
                        task.is_running = False
                        db.commit()
            except Exception as cleanup_error:
                logger.error(f"清理任务状态失败: {cleanup_error}")
            
            return False
    
    def _save_detection_results(self, task_id: int, websites: List[Website], 
                               batch_result) -> bool:
        """
        保存检测结果
        
        Args:
            task_id: 任务ID
            websites: 网站列表
            batch_result: 批量检测结果
            
        Returns:
            保存是否成功
        """
        try:
            # 展平批次结果
            all_results = []
            for batch in batch_result.batch_results:
                all_results.extend(batch)
            
            # 按原始URL顺序排序结果
            url_to_result = {result.original_url: result for result in all_results}
            ordered_results = []
            for website in websites:
                if website.url in url_to_result:
                    ordered_results.append(url_to_result[website.url])
                else:
                    # 创建失败结果
                    from .detection_result import DetectionResult
                    failed_result = DetectionResult()
                    failed_result.original_url = website.url
                    failed_result.status = 'failed'
                    failed_result.error_message = '未找到检测结果'
                    failed_result.detected_at = get_beijing_time()
                    ordered_results.append(failed_result)
            
            # 保存到数据库
            with get_db() as db:
                records = []
                for i, (website, result) in enumerate(zip(websites, ordered_results)):
                    record = DetectionRecord(
                        task_id=task_id,
                        website_id=website.id,
                        status=result.status,
                        http_status_code=result.http_status_code,
                        response_time=result.response_time,
                        final_url=result.final_url,
                        page_title=result.page_title,
                        page_content_length=result.page_content_length,
                        error_message=result.error_message,
                        failure_reason=result.failure_reason,
                        detected_at=result.detected_at.replace(tzinfo=None) if result.detected_at else get_beijing_time().replace(tzinfo=None),
                        detection_duration=result.detection_duration
                    )
                    records.append(record)
                
                db.add_all(records)
                db.commit()
                
                logger.info(f"保存了 {len(records)} 条检测记录")
                return True
                
        except Exception as e:
            logger.error(f"保存检测结果失败: {e}")
            return False
    
    def close(self):
        """关闭检测服务"""
        try:
            if self.batch_service:
                self.batch_service.close()
            logger.info("检测服务已关闭")
        except Exception as e:
            logger.error(f"关闭检测服务失败: {e}") 