"""
邮件通知服务
处理邮件发送和状态变化通知
"""

import smtplib
import json
import logging
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from ..models import SystemSetting
from ..utils.helpers import get_beijing_time

logger = logging.getLogger(__name__)


class EmailService:
    """邮件服务类"""
    
    def __init__(self):
        self.settings = {}
        logger.info("邮件服务初始化完成")
    
    def load_settings(self, db: Session) -> Dict:
        """
        从数据库加载邮件设置
        
        Args:
            db: 数据库会话
            
        Returns:
            邮件设置字典
        """
        try:
            # 默认设置
            default_settings = {
                'enabled': False,
                'smtp_host': '',
                'smtp_port': 465,
                'from_email': '',
                'from_password': '',
                'from_name': '中网网址在线监控',
                'use_ssl': True,
                'recipients': [],
                'notification_types': ['website_failed', 'website_recovered'],
                'frequency_limit': 'immediate'
            }
            
            # 从数据库获取设置
            email_settings = {}
            settings = db.query(SystemSetting).filter(
                SystemSetting.category == 'email',
                SystemSetting.is_active == True
            ).all()
            
            for setting in settings:
                key = setting.key.replace('email_', '')  # 移除前缀
                if setting.data_type == 'json':
                    try:
                        email_settings[key] = json.loads(setting.value)
                    except:
                        email_settings[key] = default_settings.get(key, '')
                elif setting.data_type == 'boolean':
                    email_settings[key] = setting.value.lower() in ('true', '1', 'yes')
                elif setting.data_type == 'integer':
                    email_settings[key] = int(setting.value)
                else:
                    email_settings[key] = setting.value
            
            # 合并默认设置
            self.settings = {**default_settings, **email_settings}
            return self.settings
            
        except Exception as e:
            logger.error(f"加载邮件设置失败: {e}")
            self.settings = default_settings
            return self.settings
    
    def test_connection(
        self, 
        smtp_host: str, 
        smtp_port: int, 
        from_email: str, 
        from_password: str, 
        use_ssl: bool = True
    ) -> bool:
        """
        测试SMTP连接
        
        Args:
            smtp_host: SMTP服务器地址
            smtp_port: SMTP端口
            from_email: 发件邮箱
            from_password: 发件密码
            use_ssl: 是否使用SSL
            
        Returns:
            连接是否成功
        """
        try:
            if use_ssl:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port)
            else:
                server = smtplib.SMTP(smtp_host, smtp_port)
                server.starttls()
            
            server.login(from_email, from_password)
            server.quit()
            
            logger.info(f"SMTP连接测试成功: {smtp_host}:{smtp_port}")
            return True
            
        except Exception as e:
            logger.error(f"SMTP连接测试失败: {e}")
            return False
    
    def send_email(
        self, 
        recipients: List[str], 
        subject: str, 
        content: str, 
        content_type: str = 'html'
    ) -> bool:
        """
        发送邮件
        
        Args:
            recipients: 收件人列表
            subject: 邮件主题
            content: 邮件内容
            content_type: 内容类型 ('html' 或 'plain')
            
        Returns:
            发送是否成功
        """
        try:
            if not self.settings.get('enabled'):
                logger.warning("邮件服务未启用")
                return False
            
            if not recipients:
                logger.warning("收件人列表为空")
                return False
            
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = f"{self.settings.get('from_name', '')} <{self.settings.get('from_email', '')}>"
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = Header(subject, 'utf-8')
            
            # 添加邮件内容
            msg.attach(MIMEText(content, content_type, 'utf-8'))
            
            # 连接SMTP服务器并发送
            if self.settings.get('use_ssl', True):
                server = smtplib.SMTP_SSL(
                    self.settings.get('smtp_host'), 
                    self.settings.get('smtp_port', 465)
                )
            else:
                server = smtplib.SMTP(
                    self.settings.get('smtp_host'), 
                    self.settings.get('smtp_port', 25)
                )
                server.starttls()
            
            server.login(
                self.settings.get('from_email'), 
                self.settings.get('from_password')
            )
            
            text = msg.as_string()
            server.sendmail(self.settings.get('from_email'), recipients, text)
            server.quit()
            
            logger.info(f"邮件发送成功: {len(recipients)} 个收件人")
            return True
            
        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return False
    
    def send_test_email(self, recipients: List[str]) -> bool:
        """
        发送测试邮件
        
        Args:
            recipients: 收件人列表
            
        Returns:
            发送是否成功
        """
        subject = "中网网址在线监控 - 测试邮件"
        
        content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; border-bottom: 2px solid #4CAF50; padding-bottom: 20px; margin-bottom: 30px;">
                    <h1 style="color: #4CAF50; margin: 0;">中网网址在线监控</h1>
                    <p style="color: #666; margin: 10px 0 0 0;">Website Monitoring System</p>
                </div>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h2 style="color: #333; margin-top: 0;">🧪 测试邮件</h2>
                    <p>这是一封测试邮件，用于验证邮件通知功能是否正常工作。</p>
                    <p>如果您收到此邮件，说明邮件配置已经成功！</p>
                </div>
                
                <div style="background: #fff; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
                    <h3 style="color: #333; margin-top: 0;">📧 邮件配置信息</h3>
                    <ul style="list-style: none; padding: 0;">
                        <li style="padding: 5px 0;"><strong>发送时间:</strong> {get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')}</li>
                        <li style="padding: 5px 0;"><strong>收件人:</strong> {', '.join(recipients)}</li>
                        <li style="padding: 5px 0;"><strong>系统状态:</strong> <span style="color: #4CAF50;">正常运行</span></li>
                    </ul>
                </div>
                
                <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0;">
                    <p style="color: #666; font-size: 12px; margin: 0;">
                        此邮件由中网网址在线监控系统自动发送，请勿回复。
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(recipients, subject, content, 'html')
    
    def send_status_change_notification(
        self, 
        website_changes: List[Dict], 
        db: Session
    ) -> bool:
        """
        发送状态变化通知邮件
        
        Args:
            website_changes: 网站状态变化列表
            db: 数据库会话
            
        Returns:
            发送是否成功
        """
        try:
            # 加载邮件设置
            settings = self.load_settings(db)
            
            if not settings.get('enabled'):
                return False
            
            recipients = settings.get('recipients', [])
            if not recipients:
                logger.warning("未配置收件人，跳过邮件通知")
                return False
            
            if not website_changes:
                return True
            
            # 构建邮件内容
            subject = "中网网址在线监控变化通知"
            content = self._build_status_change_email(website_changes)
            
            return self.send_email(recipients, subject, content, 'html')
            
        except Exception as e:
            logger.error(f"发送状态变化通知失败: {e}")
            return False
    
    def _build_status_change_email(self, changes: List[Dict]) -> str:
        """
        构建状态变化邮件内容
        
        Args:
            changes: 状态变化列表
            
        Returns:
            邮件HTML内容
        """
        # 按变化类型分组
        failed_sites = []
        recovered_sites = []
        other_changes = []
        
        for change in changes:
            change_type = change.get('change_type', '')
            if change_type == 'became_failed':
                failed_sites.append(change)
            elif change_type == 'became_accessible':
                recovered_sites.append(change)
            else:
                other_changes.append(change)
        
        # 构建HTML内容
        content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; border-bottom: 2px solid #4CAF50; padding-bottom: 20px; margin-bottom: 30px;">
                    <h1 style="color: #4CAF50; margin: 0;">中网网址在线监控变化通知</h1>
                    <p style="color: #666; margin: 10px 0 0 0;">Website Status Change Notification</p>
                </div>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h2 style="color: #333; margin-top: 0;">📊 变化摘要</h2>
                    <p>检测到 <strong>{len(changes)}</strong> 个网站状态发生变化</p>
                    <ul style="list-style: none; padding: 0;">
                        <li style="padding: 3px 0;">🔴 不可访问: <strong>{len(failed_sites)}</strong> 个</li>
                        <li style="padding: 3px 0;">🟢 已恢复: <strong>{len(recovered_sites)}</strong> 个</li>
                        <li style="padding: 3px 0;">🔄 其他变化: <strong>{len(other_changes)}</strong> 个</li>
                    </ul>
                    <p style="color: #666; font-size: 12px; margin-top: 15px;">
                        检测时间: {get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')}
                    </p>
                </div>
        """
        
        # 添加失败网站信息
        if failed_sites:
            content += """
                <div style="background: #fff; padding: 20px; border-left: 4px solid #f44336; margin-bottom: 20px;">
                    <h3 style="color: #f44336; margin-top: 0;">🔴 网站无法访问</h3>
                    <table style="width: 100%; border-collapse: collapse;">
            """
            for site in failed_sites:
                content += f"""
                        <tr style="border-bottom: 1px solid #eee;">
                            <td style="padding: 10px 0; font-weight: bold;">{site.get('website_name', '未知')}</td>
                            <td style="padding: 10px 0; color: #666;">{site.get('website_url', '')}</td>
                        </tr>
                """
            content += """
                    </table>
                </div>
            """
        
        # 添加恢复网站信息
        if recovered_sites:
            content += """
                <div style="background: #fff; padding: 20px; border-left: 4px solid #4CAF50; margin-bottom: 20px;">
                    <h3 style="color: #4CAF50; margin-top: 0;">🟢 网站已恢复访问</h3>
                    <table style="width: 100%; border-collapse: collapse;">
            """
            for site in recovered_sites:
                content += f"""
                        <tr style="border-bottom: 1px solid #eee;">
                            <td style="padding: 10px 0; font-weight: bold;">{site.get('website_name', '未知')}</td>
                            <td style="padding: 10px 0; color: #666;">{site.get('website_url', '')}</td>
                        </tr>
                """
            content += """
                    </table>
                </div>
            """
        
        # 添加其他变化信息
        if other_changes:
            content += """
                <div style="background: #fff; padding: 20px; border-left: 4px solid #ff9800; margin-bottom: 20px;">
                    <h3 style="color: #ff9800; margin-top: 0;">🔄 其他状态变化</h3>
                    <table style="width: 100%; border-collapse: collapse;">
            """
            for site in other_changes:
                status_map = {
                    'standard': '正常访问',
                    'redirect': '跳转访问', 
                    'failed': '无法访问'
                }
                prev_status = status_map.get(site.get('previous_status', ''), site.get('previous_status', ''))
                curr_status = status_map.get(site.get('current_status', ''), site.get('current_status', ''))
                
                content += f"""
                        <tr style="border-bottom: 1px solid #eee;">
                            <td style="padding: 10px 0; font-weight: bold;">{site.get('website_name', '未知')}</td>
                            <td style="padding: 10px 0; color: #666;">{prev_status} → {curr_status}</td>
                        </tr>
                """
            content += """
                    </table>
                </div>
            """
        
        # 结尾
        content += """
                <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0;">
                    <p style="color: #666; font-size: 12px; margin: 0;">
                        此邮件由中网网址在线监控系统自动发送，请勿回复。<br>
                        如需查看详细信息，请登录监控系统查看。
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return content
    
    def should_send_notification(self, change_type: str, db: Session) -> bool:
        """
        判断是否应该发送通知
        
        Args:
            change_type: 变化类型
            db: 数据库会话
            
        Returns:
            是否应该发送
        """
        try:
            settings = self.load_settings(db)
            
            if not settings.get('enabled'):
                return False
            
            notification_types = settings.get('notification_types', [])
            
            # 映射变化类型
            type_map = {
                'became_failed': 'website_failed',
                'became_accessible': 'website_recovered',
                'status_changed': 'status_changed'
            }
            
            notification_type = type_map.get(change_type)
            return notification_type in notification_types
            
        except Exception as e:
            logger.error(f"判断通知发送条件失败: {e}")
            return False