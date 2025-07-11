"""
失败网站专项监控服务
专门监控之前检测失败的网站，以1小时间隔检测
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    Website, DetectionTask, FailedSiteMonitorTask, DetectionRecord, WebsiteStatusChange
)
from ..utils.helpers import get_beijing_time
from .detection_service import DetectionService
from .status_change_service import StatusChangeService

logger = logging.getLogger(__name__)


class FailedSiteMonitorService:
    """失败网站专项监控服务"""
    
    def __init__(self):
        self.detection_service = DetectionService()
        self.status_change_service = StatusChangeService()
        logger.info("失败网站监控服务初始化完成")
    
    def create_or_update_failed_monitor_task(self, parent_task_id: int) -> Optional[FailedSiteMonitorTask]:
        """
        为主任务创建或更新失败网站监控任务
        
        Args:
            parent_task_id: 父任务ID
            
        Returns:
            失败网站监控任务，如果创建失败则返回None
        """
        try:
            with get_db() as db:
                # 检查父任务是否存在
                parent_task = db.query(DetectionTask).filter(DetectionTask.id == parent_task_id).first()
                if not parent_task:
                    logger.error(f"父任务不存在: {parent_task_id}")
                    return None
                
                # 检查是否已存在失败监控任务
                existing_monitor = db.query(FailedSiteMonitorTask).filter(
                    FailedSiteMonitorTask.parent_task_id == parent_task_id
                ).first()
                
                if existing_monitor:
                    # 更新现有任务
                    existing_monitor.name = f"{parent_task.name} - 失败网站监控"
                    existing_monitor.description = f"监控任务 '{parent_task.name}' 中不可访问的网站"
                    existing_monitor.updated_at = get_beijing_time()
                    monitor_task = existing_monitor
                    logger.info(f"更新失败监控任务: {existing_monitor.id}")
                else:
                    # 创建新的失败监控任务
                    monitor_task = FailedSiteMonitorTask(
                        name=f"{parent_task.name} - 失败网站监控",
                        description=f"监控任务 '{parent_task.name}' 中不可访问的网站",
                        parent_task_id=parent_task_id,
                        interval_hours=2,  # 2小时间隔（从30分钟改为2小时，减少资源占用）
                        max_concurrent=5,  # 降低并发数（从10降到5）
                        timeout_seconds=20,  # 降低超时时间（从30降到20）
                        retry_times=2,     # 降低重试次数（从3降到2）
                        is_active=True
                    )
                    db.add(monitor_task)
                    logger.info(f"创建失败监控任务: {monitor_task.name}")
                
                # 获取当前失败的网站并更新监控列表
                failed_websites = self.status_change_service.get_failed_websites(parent_task_id)
                
                # 清除现有关联并添加新的失败网站
                monitor_task.monitored_websites.clear()
                for website in failed_websites:
                    monitor_task.monitored_websites.append(website)
                
                db.commit()
                
                logger.info(f"失败监控任务设置完成: 监控{len(failed_websites)}个失败网站")
                return monitor_task
                
        except Exception as e:
            logger.error(f"创建/更新失败监控任务失败: {e}")
            return None
    
    def update_failed_websites_list(self, monitor_task_id: int) -> bool:
        """
        更新失败网站监控列表
        
        Args:
            monitor_task_id: 监控任务ID
            
        Returns:
            是否更新成功
        """
        try:
            with get_db() as db:
                monitor_task = db.query(FailedSiteMonitorTask).filter(
                    FailedSiteMonitorTask.id == monitor_task_id
                ).first()
                
                if not monitor_task:
                    logger.error(f"失败监控任务不存在: {monitor_task_id}")
                    return False
                
                # 获取父任务中当前失败的网站
                failed_websites = self.status_change_service.get_failed_websites(monitor_task.parent_task_id)
                
                # 记录变化
                old_count = len(monitor_task.monitored_websites)
                
                # 更新监控列表
                monitor_task.monitored_websites.clear()
                for website in failed_websites:
                    monitor_task.monitored_websites.append(website)
                
                monitor_task.updated_at = get_beijing_time()
                db.commit()
                
                new_count = len(failed_websites)
                logger.info(f"失败网站监控列表更新完成: {old_count} -> {new_count}个网站")
                
                return True
                
        except Exception as e:
            logger.error(f"更新失败网站列表失败: {e}")
            return False
    
    def run_failed_site_monitor_task(self, monitor_task_id: int) -> bool:
        """
        执行失败网站监控任务
        
        Args:
            monitor_task_id: 监控任务ID
            
        Returns:
            是否执行成功
        """
        try:
            with get_db() as db:
                monitor_task = db.query(FailedSiteMonitorTask).filter(
                    FailedSiteMonitorTask.id == monitor_task_id
                ).first()
                
                if not monitor_task or not monitor_task.is_active:
                    logger.warning(f"失败监控任务不存在或未激活: {monitor_task_id}")
                    return False
                
                # 检查是否正在运行
                if monitor_task.is_running:
                    logger.warning(f"失败监控任务 {monitor_task_id} 正在运行中，跳过")
                    return False
                
                # 设置运行状态
                monitor_task.is_running = True
                db.commit()
                
                try:
                    # 获取要监控的网站
                    websites = list(monitor_task.monitored_websites)
                    if not websites:
                        logger.info(f"失败监控任务 {monitor_task_id} 没有需要监控的网站")
                        return True
                    
                    logger.info(f"开始执行失败网站监控任务: {monitor_task.name}, 监控{len(websites)}个网站")
                    
                    # 提取URL列表
                    urls = [website.url for website in websites]
                    
                    # 执行检测
                    from .batch_detector import BatchDetectionService
                    batch_service = BatchDetectionService()
                    batch_result = batch_service.detect_websites_sync(urls)
                    
                    # 保存检测结果
                    detection_records = self._save_monitor_results(
                        monitor_task, websites, batch_result
                    )
                    
                    # 检测状态变化（特别关注恢复的网站）
                    recovered_websites = self._check_recovery_status(
                        monitor_task, detection_records
                    )
                    
                    # 更新任务信息
                    current_time = get_beijing_time()
                    naive_current_time = current_time.replace(tzinfo=None)
                    monitor_task.last_run_at = naive_current_time
                    monitor_task.next_run_at = naive_current_time + timedelta(hours=monitor_task.interval_hours)
                    
                    db.commit()
                    
                    logger.info(f"失败网站监控任务 {monitor_task_id} 执行完成, "
                               f"检测{len(websites)}个网站, 恢复{len(recovered_websites)}个网站")
                    
                    return True
                    
                finally:
                    # 确保清除运行状态
                    monitor_task.is_running = False
                    db.commit()
                    
        except Exception as e:
            logger.error(f"执行失败网站监控任务失败: {e}")
            # 清除运行状态
            try:
                with get_db() as db:
                    monitor_task = db.query(FailedSiteMonitorTask).filter(
                        FailedSiteMonitorTask.id == monitor_task_id
                    ).first()
                    if monitor_task:
                        monitor_task.is_running = False
                        db.commit()
            except Exception as cleanup_error:
                logger.error(f"清理监控任务状态失败: {cleanup_error}")
            
            return False
    
    def _save_monitor_results(
        self, 
        monitor_task: FailedSiteMonitorTask, 
        websites: List[Website], 
        batch_result
    ) -> List[DetectionRecord]:
        """
        保存监控检测结果
        
        Args:
            monitor_task: 监控任务
            websites: 网站列表
            batch_result: 批量检测结果
            
        Returns:
            检测记录列表
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
            
            # 保存到数据库，使用父任务ID
            with get_db() as db:
                records = []
                for i, (website, result) in enumerate(zip(websites, ordered_results)):
                    record = DetectionRecord(
                        task_id=monitor_task.parent_task_id,  # 使用父任务ID
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
                
                logger.info(f"保存了 {len(records)} 条失败网站监控记录")
                return records
                
        except Exception as e:
            logger.error(f"保存监控检测结果失败: {e}")
            return []
    
    def _check_recovery_status(
        self, 
        monitor_task: FailedSiteMonitorTask, 
        detection_records: List[DetectionRecord]
    ) -> List[Website]:
        """
        检查网站恢复状态
        
        Args:
            monitor_task: 监控任务
            detection_records: 检测记录列表
            
        Returns:
            恢复的网站列表
        """
        try:
            recovered_websites = []
            
            for record in detection_records:
                # 检查是否从failed状态恢复
                if self.status_change_service._is_accessible_status(record.status):
                    # 获取该网站在主任务中的上一次检测记录
                    with get_db() as db:
                        previous_record = db.query(DetectionRecord).filter(
                            DetectionRecord.website_id == record.website_id,
                            DetectionRecord.task_id == monitor_task.parent_task_id,
                            DetectionRecord.detected_at < record.detected_at
                        ).order_by(DetectionRecord.detected_at.desc()).first()
                        
                        if previous_record and previous_record.status == 'failed':
                            # 网站已恢复
                            website = db.query(Website).filter(Website.id == record.website_id).first()
                            if website:
                                recovered_websites.append(website)
                                
                                # 记录状态变化
                                change_record = WebsiteStatusChange(
                                    website_id=record.website_id,
                                    task_id=monitor_task.parent_task_id,
                                    previous_status=previous_record.status,
                                    current_status=record.status,
                                    change_type='became_accessible',
                                    previous_detection_id=previous_record.id,
                                    current_detection_id=record.id,
                                    detected_at=record.detected_at
                                )
                                db.add(change_record)
                                
                                logger.info(f"网站恢复访问: {website.name} ({website.url})")
                        
                        db.commit()
            
            return recovered_websites
            
        except Exception as e:
            logger.error(f"检查恢复状态失败: {e}")
            return []
    
    def get_monitor_task_status(self, parent_task_id: int) -> Dict:
        """
        获取失败监控任务状态
        
        Args:
            parent_task_id: 父任务ID
            
        Returns:
            监控任务状态字典
        """
        try:
            with get_db() as db:
                monitor_task = db.query(FailedSiteMonitorTask).filter(
                    FailedSiteMonitorTask.parent_task_id == parent_task_id
                ).first()
                
                if not monitor_task:
                    return {
                        'exists': False,
                        'is_active': False,
                        'monitored_websites_count': 0,
                        'last_run_at': None,
                        'next_run_at': None
                    }
                
                return {
                    'exists': True,
                    'id': monitor_task.id,
                    'name': monitor_task.name,
                    'is_active': monitor_task.is_active,
                    'is_running': monitor_task.is_running,
                    'interval_hours': monitor_task.interval_hours,
                    'monitored_websites_count': len(monitor_task.monitored_websites),
                    'last_run_at': monitor_task.last_run_at.isoformat() if monitor_task.last_run_at else None,
                    'next_run_at': monitor_task.next_run_at.isoformat() if monitor_task.next_run_at else None,
                    'created_at': monitor_task.created_at.isoformat() if monitor_task.created_at else None,
                    'updated_at': monitor_task.updated_at.isoformat() if monitor_task.updated_at else None,
                }
                
        except Exception as e:
            logger.error(f"获取监控任务状态失败: {e}")
            return {
                'exists': False,
                'is_active': False,
                'monitored_websites_count': 0,
                'error': str(e)
            }
    
    def get_recovered_websites(
        self, 
        parent_task_id: int, 
        hours: int = 24
    ) -> List[Dict]:
        """
        获取最近恢复的网站列表
        
        Args:
            parent_task_id: 父任务ID
            hours: 查询最近多少小时的恢复记录
            
        Returns:
            恢复的网站列表
        """
        try:
            with get_db() as db:
                # 计算时间范围
                since_time = get_beijing_time() - timedelta(hours=hours)
                
                # 查询恢复记录
                recovery_changes = db.query(WebsiteStatusChange).join(Website).filter(
                    WebsiteStatusChange.task_id == parent_task_id,
                    WebsiteStatusChange.change_type == 'became_accessible',
                    WebsiteStatusChange.detected_at >= since_time
                ).order_by(WebsiteStatusChange.detected_at.desc()).all()
                
                # 转换为字典格式
                result = []
                for change in recovery_changes:
                    result.append({
                        'website_id': change.website_id,
                        'website_name': change.website.name if change.website else None,
                        'website_url': change.website.url if change.website else None,
                        'previous_status': change.previous_status,
                        'current_status': change.current_status,
                        'recovery_time': change.detected_at.isoformat() if change.detected_at else None,
                        'change_id': change.id
                    })
                
                logger.info(f"获取最近{hours}小时恢复的网站: {len(result)}个")
                return result
                
        except Exception as e:
            logger.error(f"获取恢复网站列表失败: {e}")
            return []
    
    def toggle_monitor_task_status(self, monitor_task_id: int) -> bool:
        """
        切换失败监控任务的启动/停止状态
        
        Args:
            monitor_task_id: 监控任务ID
            
        Returns:
            是否操作成功
        """
        try:
            with get_db() as db:
                monitor_task = db.query(FailedSiteMonitorTask).filter(
                    FailedSiteMonitorTask.id == monitor_task_id
                ).first()
                
                if not monitor_task:
                    logger.error(f"失败监控任务不存在: {monitor_task_id}")
                    return False
                
                # 切换状态
                monitor_task.is_active = not monitor_task.is_active
                monitor_task.updated_at = get_beijing_time()
                
                db.commit()
                
                action = "启动" if monitor_task.is_active else "停止"
                logger.info(f"失败监控任务 {monitor_task_id} 已{action}")
                
                return True
                
        except Exception as e:
            logger.error(f"切换失败监控任务状态失败: {e}")
            return False
    
    def update_monitor_task_settings(
        self, 
        monitor_task_id: int, 
        update_params: Dict, 
        website_ids: List[int] = None
    ) -> bool:
        """
        更新失败监控任务设置
        
        Args:
            monitor_task_id: 监控任务ID
            update_params: 更新参数字典
            website_ids: 监控网站ID列表（可选）
            
        Returns:
            是否更新成功
        """
        try:
            with get_db() as db:
                monitor_task = db.query(FailedSiteMonitorTask).filter(
                    FailedSiteMonitorTask.id == monitor_task_id
                ).first()
                
                if not monitor_task:
                    logger.error(f"失败监控任务不存在: {monitor_task_id}")
                    return False
                
                # 更新基本参数
                for key, value in update_params.items():
                    if hasattr(monitor_task, key):
                        setattr(monitor_task, key, value)
                
                # 更新监控网站列表
                if website_ids is not None:
                    from ..models import Website
                    
                    # 清除现有关联
                    monitor_task.monitored_websites.clear()
                    
                    # 添加新的网站
                    for website_id in website_ids:
                        website = db.query(Website).filter(Website.id == website_id).first()
                        if website:
                            monitor_task.monitored_websites.append(website)
                
                monitor_task.updated_at = get_beijing_time()
                db.commit()
                
                logger.info(f"失败监控任务 {monitor_task_id} 设置更新成功")
                return True
                
        except Exception as e:
            logger.error(f"更新失败监控任务设置失败: {e}")
            return False
    
    def delete_monitor_task(self, monitor_task_id: int) -> bool:
        """
        删除失败监控任务
        
        Args:
            monitor_task_id: 监控任务ID
            
        Returns:
            是否删除成功
        """
        try:
            with get_db() as db:
                monitor_task = db.query(FailedSiteMonitorTask).filter(
                    FailedSiteMonitorTask.id == monitor_task_id
                ).first()
                
                if not monitor_task:
                    logger.error(f"失败监控任务不存在: {monitor_task_id}")
                    return False
                
                # 清除网站关联
                monitor_task.monitored_websites.clear()
                
                # 删除任务
                db.delete(monitor_task)
                db.commit()
                
                logger.info(f"失败监控任务 {monitor_task_id} 删除成功")
                return True
                
        except Exception as e:
            logger.error(f"删除失败监控任务失败: {e}")
            return False 