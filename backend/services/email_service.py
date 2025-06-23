"""
网址监控工具 - 邮件服务
负责发送监控报告和异常通知邮件
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Any
import os
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailService:
    """邮件服务类"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化邮件服务
        
        Args:
            config: 邮件配置字典
        """
        self.config = config or self._get_default_config()
        self.smtp_server = None
        
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.qq.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'username': os.getenv('EMAIL_USERNAME', ''),
            'password': os.getenv('EMAIL_PASSWORD', ''),
            'from_email': os.getenv('FROM_EMAIL', ''),
            'use_tls': os.getenv('USE_TLS', 'true').lower() == 'true'
        }
    
    def connect(self) -> bool:
        """
        连接SMTP服务器
        
        Returns:
            bool: 是否连接成功
        """
        try:
            if self.config['use_tls']:
                self.smtp_server = smtplib.SMTP(
                    self.config['smtp_server'], 
                    self.config['smtp_port']
                )
                self.smtp_server.starttls()
            else:
                self.smtp_server = smtplib.SMTP_SSL(
                    self.config['smtp_server'], 
                    self.config['smtp_port']
                )
            
            if self.config['username'] and self.config['password']:
                self.smtp_server.login(
                    self.config['username'], 
                    self.config['password']
                )
            
            logger.info("SMTP服务器连接成功")
            return True
            
        except Exception as e:
            logger.error(f"SMTP服务器连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开SMTP连接"""
        if self.smtp_server:
            try:
                self.smtp_server.quit()
                logger.info("SMTP连接已断开")
            except Exception as e:
                logger.error(f"断开SMTP连接失败: {e}")
            finally:
                self.smtp_server = None
    
    def send_email(
        self,
        to_emails: List[str],
        subject: str,
        content: str,
        content_type: str = 'html',
        attachments: Optional[List[str]] = None
    ) -> bool:
        """
        发送邮件
        
        Args:
            to_emails: 收件人邮箱列表
            subject: 邮件主题
            content: 邮件内容
            content_type: 内容类型 ('html' 或 'plain')
            attachments: 附件文件路径列表
            
        Returns:
            bool: 是否发送成功
        """
        try:
            # 检查配置
            if not self.config['from_email']:
                logger.error("发件人邮箱未配置")
                return False
            
            if not to_emails:
                logger.error("收件人邮箱为空")
                return False
            
            # 连接服务器
            if not self.connect():
                return False
            
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = self.config['from_email']
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            
            # 添加邮件内容
            msg.attach(MIMEText(content, content_type, 'utf-8'))
            
            # 添加附件
            if attachments:
                for file_path in attachments:
                    if os.path.isfile(file_path):
                        self._add_attachment(msg, file_path)
            
            # 发送邮件
            text = msg.as_string()
            self.smtp_server.sendmail(
                self.config['from_email'], 
                to_emails, 
                text
            )
            
            logger.info(f"邮件发送成功: {subject} -> {to_emails}")
            return True
            
        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return False
        finally:
            self.disconnect()
    
    def _add_attachment(self, msg: MIMEMultipart, file_path: str):
        """
        添加附件
        
        Args:
            msg: 邮件对象
            file_path: 附件文件路径
        """
        try:
            with open(file_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {os.path.basename(file_path)}'
            )
            
            msg.attach(part)
            
        except Exception as e:
            logger.error(f"添加附件失败: {file_path}, 错误: {e}")
    
    def send_detection_report(
        self,
        to_emails: List[str],
        task_name: str,
        statistics: Dict[str, Any],
        failed_websites: List[Dict[str, Any]] = None
    ) -> bool:
        """
        发送检测报告邮件
        
        Args:
            to_emails: 收件人邮箱列表
            task_name: 任务名称
            statistics: 统计数据
            failed_websites: 失败的网站列表
            
        Returns:
            bool: 是否发送成功
        """
        try:
            # 生成邮件内容
            subject = f"网址监控报告 - {task_name} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            content = self._generate_report_content(
                task_name, 
                statistics, 
                failed_websites
            )
            
            return self.send_email(to_emails, subject, content, 'html')
            
        except Exception as e:
            logger.error(f"发送检测报告失败: {e}")
            return False
    
    def send_alert_email(
        self,
        to_emails: List[str],
        alert_type: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        发送告警邮件
        
        Args:
            to_emails: 收件人邮箱列表
            alert_type: 告警类型
            message: 告警消息
            details: 详细信息
            
        Returns:
            bool: 是否发送成功
        """
        try:
            subject = f"网址监控告警 - {alert_type} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            content = self._generate_alert_content(alert_type, message, details)
            
            return self.send_email(to_emails, subject, content, 'html')
            
        except Exception as e:
            logger.error(f"发送告警邮件失败: {e}")
            return False
    
    def _generate_report_content(
        self,
        task_name: str,
        statistics: Dict[str, Any],
        failed_websites: List[Dict[str, Any]] = None
    ) -> str:
        """
        生成检测报告内容
        
        Args:
            task_name: 任务名称
            statistics: 统计数据
            failed_websites: 失败的网站列表
            
        Returns:
            str: HTML格式的报告内容
        """
        failed_websites = failed_websites or []
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>网址监控报告</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #f4f4f4; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .stats {{ background-color: #e8f5e8; padding: 15px; margin: 20px 0; border-radius: 5px; }}
                .failed {{ background-color: #ffe6e6; padding: 15px; margin: 20px 0; border-radius: 5px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .success {{ color: #28a745; }}
                .warning {{ color: #ffc107; }}
                .danger {{ color: #dc3545; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🔍 网址监控报告</h1>
                <p>任务名称: {task_name}</p>
                <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="content">
                <div class="stats">
                    <h2>📊 检测统计</h2>
                    <ul>
                        <li>总网站数: <strong>{statistics.get('total_websites', 0)}</strong></li>
                        <li class="success">正常访问: <strong>{statistics.get('accessible_count', 0)}</strong></li>
                        <li class="warning">跳转访问: <strong>{statistics.get('redirect_count', 0)}</strong></li>
                        <li class="danger">无法访问: <strong>{statistics.get('failed_count', 0)}</strong></li>
                        <li>可访问率: <strong>{statistics.get('accessibility_rate', 0):.1f}%</strong></li>
                    </ul>
                </div>
        """
        
        if failed_websites:
            html += """
                <div class="failed">
                    <h2>❌ 无法访问的网站</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>网站域名</th>
                                <th>错误信息</th>
                                <th>检测时间</th>
                            </tr>
                        </thead>
                        <tbody>
            """
            
            for website in failed_websites:
                html += f"""
                    <tr>
                        <td>{website.get('domain', 'N/A')}</td>
                        <td>{website.get('error_message', 'N/A')}</td>
                        <td>{website.get('check_time', 'N/A')}</td>
                    </tr>
                """
            
            html += """
                        </tbody>
                    </table>
                </div>
            """
        
        html += """
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_alert_content(
        self,
        alert_type: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        生成告警邮件内容
        
        Args:
            alert_type: 告警类型
            message: 告警消息
            details: 详细信息
            
        Returns:
            str: HTML格式的告警内容
        """
        details = details or {}
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>网址监控告警</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #dc3545; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .alert {{ background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; margin: 20px 0; border-radius: 5px; }}
                .details {{ background-color: #f4f4f4; padding: 15px; margin: 20px 0; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>⚠️ 网址监控告警</h1>
                <p>告警类型: {alert_type}</p>
                <p>告警时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="content">
                <div class="alert">
                    <h2>告警信息</h2>
                    <p>{message}</p>
                </div>
        """
        
        if details:
            html += """
                <div class="details">
                    <h2>详细信息</h2>
                    <ul>
            """
            
            for key, value in details.items():
                html += f"<li><strong>{key}:</strong> {value}</li>"
            
            html += """
                    </ul>
                </div>
            """
        
        html += """
            </div>
        </body>
        </html>
        """
        
        return html
    
    def test_connection(self) -> bool:
        """
        测试邮件服务连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            if not self.config['from_email']:
                logger.error("邮件配置不完整")
                return False
            
            success = self.connect()
            if success:
                self.disconnect()
                logger.info("邮件服务连接测试成功")
            else:
                logger.error("邮件服务连接测试失败")
            
            return success
            
        except Exception as e:
            logger.error(f"邮件服务连接测试异常: {e}")
            return False

# 全局邮件服务实例
email_service = EmailService() 