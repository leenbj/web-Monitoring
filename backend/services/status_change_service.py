"""
网站状态变化检测服务
负责检测和记录网站状态变化
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    Website, DetectionRecord, WebsiteStatusChange, DetectionTask
)
from ..utils.helpers import get_beijing_time

logger = logging.getLogger(__name__)


class StatusChangeService:
    """网站状态变化检测服务"""
    
    def __init__(self):
        logger.info("状态变化检测服务初始化完成")
    
    def detect_status_changes(self, task_id: int, current_detection_records: List[DetectionRecord]) -> List[WebsiteStatusChange]:
        """
        检测网站状态变化
        
        Args:
            task_id: 任务ID
            current_detection_records: 当前检测记录列表
            
        Returns:
            状态变化记录列表
        """
        try:
            changes = []
            
            with get_db() as db:
                for current_record in current_detection_records:
                    # 获取该网站的上一次检测记录
                    previous_record = self._get_previous_detection_record(
                        db, current_record.website_id, task_id, current_record.detected_at
                    )
                    
                    if previous_record:
                        # 检测状态变化
                        change = self._analyze_status_change(
                            db, current_record, previous_record, task_id
                        )
                        
                        if change:
                            changes.append(change)
                            db.add(change)
                
                # 批量提交变化记录
                if changes:
                    db.commit()
                    logger.info(f"检测到 {len(changes)} 个网站状态变化")
                    
                    # 发送邮件通知
                    self._send_email_notifications(changes, db)
                
                return changes
                
        except Exception as e:
            logger.error(f"检测状态变化失败: {e}")
            return []
    
    def _get_previous_detection_record(
        self, 
        db: Session, 
        website_id: int, 
        task_id: int, 
        current_time: datetime
    ) -> Optional[DetectionRecord]:
        """
        获取网站的上一次检测记录
        
        Args:
            db: 数据库会话
            website_id: 网站ID
            task_id: 任务ID
            current_time: 当前检测时间
            
        Returns:
            上一次检测记录，如果没有则返回None
        """
        try:
            return db.query(DetectionRecord).filter(
                DetectionRecord.website_id == website_id,
                DetectionRecord.task_id == task_id,
                DetectionRecord.detected_at < current_time
            ).order_by(DetectionRecord.detected_at.desc()).first()
            
        except Exception as e:
            logger.error(f"获取上一次检测记录失败: website_id={website_id}, error={e}")
            return None
    
    def _analyze_status_change(
        self, 
        db: Session,
        current_record: DetectionRecord, 
        previous_record: DetectionRecord, 
        task_id: int
    ) -> Optional[WebsiteStatusChange]:
        """
        分析状态变化
        
        Args:
            db: 数据库会话
            current_record: 当前检测记录
            previous_record: 上一次检测记录
            task_id: 任务ID
            
        Returns:
            状态变化记录，如果没有变化则返回None
        """
        try:
            # 将状态归类为可访问/不可访问
            prev_accessible = self._is_accessible_status(previous_record.status)
            curr_accessible = self._is_accessible_status(current_record.status)
            
            # 判断变化类型
            change_type = None
            
            if not prev_accessible and curr_accessible:
                # 从不可访问变为可访问
                change_type = 'became_accessible'
            elif prev_accessible and not curr_accessible:
                # 从可访问变为不可访问
                change_type = 'became_failed'
            elif previous_record.status != current_record.status:
                # 状态发生了变化但可访问性没变
                change_type = 'status_changed'
            
            # 如果没有变化，返回None
            if not change_type:
                return None
            
            # 创建状态变化记录
            change_record = WebsiteStatusChange(
                website_id=current_record.website_id,
                task_id=task_id,
                previous_status=previous_record.status,
                current_status=current_record.status,
                change_type=change_type,
                previous_detection_id=previous_record.id,
                current_detection_id=current_record.id,
                detected_at=current_record.detected_at
            )
            
            logger.info(f"检测到状态变化: 网站{current_record.website_id}, "
                       f"{previous_record.status} -> {current_record.status}, "
                       f"变化类型: {change_type}")
            
            return change_record
            
        except Exception as e:
            logger.error(f"分析状态变化失败: {e}")
            return None
    
    def _is_accessible_status(self, status: str) -> bool:
        """
        判断状态是否为可访问
        
        Args:
            status: 检测状态
            
        Returns:
            是否可访问
        """
        # standard和redirect都视为可访问
        return status in ['standard', 'redirect']
    
    def get_recent_status_changes(
        self, 
        task_id: Optional[int] = None, 
        hours: int = 24,
        limit: int = 100
    ) -> List[Dict]:
        """
        获取最近的状态变化记录
        
        Args:
            task_id: 任务ID，为None时获取所有任务的变化
            hours: 查询最近多少小时的数据
            limit: 返回记录数限制
            
        Returns:
            状态变化记录列表
        """
        try:
            with get_db() as db:
                # 计算时间范围
                since_time = get_beijing_time() - timedelta(hours=hours)
                
                # 构建查询
                query = db.query(WebsiteStatusChange).join(Website)
                
                if task_id:
                    query = query.filter(WebsiteStatusChange.task_id == task_id)
                
                query = query.filter(
                    WebsiteStatusChange.detected_at >= since_time
                ).order_by(
                    WebsiteStatusChange.detected_at.desc()
                ).limit(limit)
                
                changes = query.all()
                
                # 转换为字典格式
                result = []
                for change in changes:
                    change_dict = change.to_dict()
                    # 添加额外信息
                    change_dict['website_name'] = change.website.name if change.website else None
                    change_dict['website_url'] = change.website.url if change.website else None
                    result.append(change_dict)
                
                logger.info(f"获取最近{hours}小时状态变化记录: {len(result)}条")
                return result
                
        except Exception as e:
            logger.error(f"获取状态变化记录失败: {e}")
            return []
    
    def get_accessibility_summary(self, task_id: Optional[int] = None) -> Dict:
        """
        获取网站可访问性摘要
        
        Args:
            task_id: 任务ID，为None时统计所有任务
            
        Returns:
            可访问性摘要字典
        """
        try:
            with get_db() as db:
                # 获取最新的检测记录（每个网站的最新记录）
                from sqlalchemy import func
                
                subquery = db.query(
                    DetectionRecord.website_id,
                    func.max(DetectionRecord.detected_at).label('max_detected_at')
                ).group_by(DetectionRecord.website_id)
                
                if task_id:
                    subquery = subquery.filter(DetectionRecord.task_id == task_id)
                
                subquery = subquery.subquery()
                
                # 获取最新检测记录的状态
                latest_records = db.query(DetectionRecord).join(
                    subquery,
                    (DetectionRecord.website_id == subquery.c.website_id) &
                    (DetectionRecord.detected_at == subquery.c.max_detected_at)
                ).all()
                
                # 统计各种状态
                total_websites = len(latest_records)
                accessible_count = sum(1 for r in latest_records if self._is_accessible_status(r.status))
                failed_count = sum(1 for r in latest_records if r.status == 'failed')
                standard_count = sum(1 for r in latest_records if r.status == 'standard')
                redirect_count = sum(1 for r in latest_records if r.status == 'redirect')
                
                # 计算百分比
                def safe_percentage(count, total):
                    return round(count / total * 100, 1) if total > 0 else 0
                
                summary = {
                    'total_websites': total_websites,
                    'accessible_count': accessible_count,
                    'failed_count': failed_count,
                    'standard_count': standard_count,
                    'redirect_count': redirect_count,
                    'accessibility_rate': safe_percentage(accessible_count, total_websites),
                    'failure_rate': safe_percentage(failed_count, total_websites),
                    'redirect_rate': safe_percentage(redirect_count, total_websites),
                }
                
                logger.info(f"可访问性摘要: 总计{total_websites}个网站, "
                           f"可访问{accessible_count}个({summary['accessibility_rate']}%), "
                           f"不可访问{failed_count}个({summary['failure_rate']}%)")
                
                return summary
                
        except Exception as e:
            logger.error(f"获取可访问性摘要失败: {e}")
            return {
                'total_websites': 0,
                'accessible_count': 0,
                'failed_count': 0,
                'standard_count': 0,
                'redirect_count': 0,
                'accessibility_rate': 0,
                'failure_rate': 0,
                'redirect_rate': 0,
            }
    
    def get_failed_websites(self, task_id: int) -> List[Website]:
        """
        获取当前不可访问的网站列表
        
        Args:
            task_id: 任务ID
            
        Returns:
            不可访问的网站列表
        """
        try:
            with get_db() as db:
                # 获取最新的检测记录（每个网站的最新记录）
                from sqlalchemy import func
                
                subquery = db.query(
                    DetectionRecord.website_id,
                    func.max(DetectionRecord.detected_at).label('max_detected_at')
                ).filter(
                    DetectionRecord.task_id == task_id
                ).group_by(DetectionRecord.website_id).subquery()
                
                # 获取状态为failed的最新检测记录
                failed_records = db.query(DetectionRecord).join(
                    subquery,
                    (DetectionRecord.website_id == subquery.c.website_id) &
                    (DetectionRecord.detected_at == subquery.c.max_detected_at)
                ).filter(
                    DetectionRecord.status == 'failed',
                    DetectionRecord.task_id == task_id
                ).all()
                
                # 获取对应的网站
                failed_website_ids = [record.website_id for record in failed_records]
                failed_websites = db.query(Website).filter(
                    Website.id.in_(failed_website_ids),
                    Website.is_active == True
                ).all()
                
                logger.info(f"任务{task_id}中有{len(failed_websites)}个网站当前不可访问")
                return failed_websites
                
        except Exception as e:
            logger.error(f"获取不可访问网站列表失败: {e}")
            return []
    
    def _send_email_notifications(self, changes: List[WebsiteStatusChange], db: Session):
        """
        发送邮件通知
        
        Args:
            changes: 状态变化记录列表
            db: 数据库会话
        """
        try:
            # 导入邮件服务
            from .email_notification_service import EmailService
            
            email_service = EmailService()
            
            # 检查是否启用邮件通知
            settings = email_service.load_settings(db)
            if not settings.get('enabled'):
                return
            
            # 转换状态变化记录为邮件格式
            website_changes = []
            for change in changes:
                # 检查是否应该发送此类型的通知
                if not email_service.should_send_notification(change.change_type, db):
                    continue
                
                change_dict = {
                    'website_id': change.website_id,
                    'website_name': change.website.name if change.website else '未知网站',
                    'website_url': change.website.url if change.website else '',
                    'previous_status': change.previous_status,
                    'current_status': change.current_status,
                    'change_type': change.change_type,
                    'detected_at': change.detected_at.isoformat() if change.detected_at else None
                }
                website_changes.append(change_dict)
            
            # 如果有需要通知的变化，发送邮件
            if website_changes:
                success = email_service.send_status_change_notification(website_changes, db)
                if success:
                    logger.info(f"邮件通知发送成功，包含 {len(website_changes)} 个状态变化")
                else:
                    logger.warning("邮件通知发送失败")
            else:
                logger.debug("没有需要邮件通知的状态变化")
                
        except Exception as e:
            logger.error(f"发送邮件通知失败: {e}") 