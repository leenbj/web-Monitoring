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

# 获取应用的logger
logger = logging.getLogger('backend.services.email_service')

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
            smtp_port = self.config['smtp_port']
            smtp_server = self.config['smtp_server']
            
            # 根据端口选择连接方式
            if smtp_port == 465:
                # 465端口使用SSL连接
                logger.info(f"使用SSL连接: {smtp_server}:{smtp_port}")
                try:
                    self.smtp_server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=30)
                except Exception as ssl_e:
                    logger.warning(f"默认SSL配置失败，尝试自定义SSL配置: {ssl_e}")
                    import ssl
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    self.smtp_server = smtplib.SMTP_SSL(smtp_server, smtp_port, context=context, timeout=30)
            elif smtp_port == 587:
                # 587端口使用STARTTLS
                logger.info(f"使用STARTTLS连接: {smtp_server}:{smtp_port}")
                self.smtp_server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
                import ssl
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                self.smtp_server.starttls(context=context)
            elif self.config.get('use_tls', False):
                # 其他端口，根据use_tls配置使用STARTTLS
                logger.info(f"使用STARTTLS连接: {smtp_server}:{smtp_port}")
                self.smtp_server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
                import ssl
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                self.smtp_server.starttls(context=context)
            else:
                # 默认使用SSL连接
                logger.info(f"使用SSL连接: {smtp_server}:{smtp_port}")
                self.smtp_server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=30)
            
            if self.config['username'] and self.config['password']:
                self.smtp_server.login(
                    self.config['username'], 
                    self.config['password']
                )
            
            logger.info("SMTP服务器连接成功")
            return True
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"SMTP服务器连接失败: {error_msg}")
            logger.error(f"异常类型: {type(e).__name__}")
            logger.error(f"连接配置: host={self.config.get('smtp_server')}, port={self.config.get('smtp_port')}")
            # 重新抛出异常，让上层能获取具体错误信息
            raise e
    
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
    
    def test_connection(
        self, 
        smtp_host: str = None,
        smtp_port: int = None,
        from_email: str = None,
        from_password: str = None,
        use_ssl: bool = None
    ) -> bool:
        """
        测试邮件服务连接
        
        Args:
            smtp_host: SMTP服务器地址
            smtp_port: SMTP端口
            from_email: 发件人邮箱
            from_password: 邮箱密码
            use_ssl: 是否使用SSL
            
        Returns:
            bool: 连接是否成功
        """
        try:
            # 使用传入的参数或默认配置
            test_config = self.config.copy()
            if smtp_host:
                test_config['smtp_server'] = smtp_host
            if smtp_port:
                test_config['smtp_port'] = smtp_port
            if from_email:
                test_config['from_email'] = from_email
                test_config['username'] = from_email
            if from_password:
                test_config['password'] = from_password
            if use_ssl is not None:
                # 根据端口和SSL设置决定使用TLS还是SSL
                if smtp_port == 587:
                    test_config['use_tls'] = use_ssl
                elif smtp_port == 465:
                    # 465端口固定使用SSL，不需要设置use_tls
                    pass
                else:
                    test_config['use_tls'] = use_ssl
            
            # 验证必要参数
            if not test_config.get('smtp_server') or not test_config.get('from_email'):
                logger.error("SMTP服务器或发件人邮箱未配置")
                return False
            
            # 临时保存原配置
            original_config = self.config
            self.config = test_config
            
            try:
                self.connect()
                self.disconnect()
                logger.info("邮件服务连接测试成功")
                return True
            except Exception as connect_error:
                logger.error(f"邮件服务连接测试失败: {connect_error}")
                # 重新抛出异常，让API层能获取具体错误信息
                raise connect_error
            finally:
                # 恢复原配置
                self.config = original_config
            
        except Exception as e:
            logger.error(f"邮件服务连接测试异常: {e}")
            # 重新抛出异常，让API层能获取具体错误信息
            raise e

# 全局邮件服务实例
email_service = EmailService() 