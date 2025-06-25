"""
邮件通知服务
处理邮件发送和状态变化通知
"""

import smtplib
import json
import logging
import ssl
import socket
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
            
        Raises:
            Exception: 连接失败时抛出具体的异常信息
        """
        server = None
        try:
            logger.info(f"开始测试SMTP连接: {smtp_host}:{smtp_port}")
            
            # 特殊处理腾讯企业邮箱
            if 'exmail.qq.com' in smtp_host:
                logger.info("检测到腾讯企业邮箱，使用优化连接策略")
                return self._test_tencent_exmail(smtp_host, smtp_port, from_email, from_password)
            
            # 创建SSL上下文
            context = ssl.create_default_context()
            # 对于某些邮件服务器，可能需要降低SSL安全级别
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            # 针对不同端口的连接策略
            if smtp_port == 465:
                # 465端口使用SSL连接
                logger.info(f"使用SSL连接: {smtp_host}:{smtp_port}")
                server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=20, context=context)
            elif smtp_port == 587:
                # 587端口使用STARTTLS
                logger.info(f"使用STARTTLS连接: {smtp_host}:{smtp_port}")
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=20)
                server.starttls(context=context)
            elif smtp_port == 25:
                # 25端口通常不使用加密
                logger.info(f"使用普通连接: {smtp_host}:{smtp_port}")
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=20)
            else:
                # 其他端口根据use_ssl参数决定
                if use_ssl:
                    logger.info(f"使用SSL连接: {smtp_host}:{smtp_port}")
                    server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=20, context=context)
                else:
                    logger.info(f"使用STARTTLS连接: {smtp_host}:{smtp_port}")
                    server = smtplib.SMTP(smtp_host, smtp_port, timeout=20)
                    server.starttls(context=context)
            
            # 发送EHLO命令确保连接稳定
            logger.info("SMTP连接建立成功，发送EHLO命令")
            server.ehlo()
            
            # 尝试登录
            logger.info("尝试登录")
            server.login(from_email, from_password)
            
            # 发送NOOP命令测试连接稳定性
            server.noop()
            logger.info("SMTP登录成功，连接稳定")
            
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            error_code = str(e).split()[0] if str(e) else ""
            if "535" in error_code:
                error_msg = "认证失败: 用户名或密码错误，请检查邮箱账号和授权码"
            else:
                error_msg = f"SMTP认证失败: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except smtplib.SMTPConnectError as e:
            error_msg = f"无法连接到SMTP服务器 {smtp_host}:{smtp_port}，请检查服务器地址和端口"
            logger.error(f"SMTP连接错误: {e}")
            raise Exception(error_msg)
        except smtplib.SMTPServerDisconnected as e:
            error_msg = f"服务器意外断开连接，请检查网络连接或更换端口(建议尝试587端口): {e}"
            logger.error(f"SMTP服务器断开连接: {e}")
            raise Exception(error_msg)
        except ssl.SSLError as e:
            error_msg = f"SSL连接失败，请检查端口({smtp_port})和加密设置是否正确"
            logger.error(f"SSL错误详情: {e}")
            raise Exception(error_msg)
        except (socket.timeout, TimeoutError):
            error_msg = f"连接超时(30秒)，请检查网络连接或防火墙设置"
            logger.error(f"连接超时: {smtp_host}:{smtp_port}")
            raise Exception(error_msg)
        except socket.gaierror as e:
            error_msg = f"无法解析服务器地址 {smtp_host}，请检查服务器地址是否正确"
            logger.error(f"DNS解析错误: {e}")
            raise Exception(error_msg)
        except Exception as e:
            import traceback
            error_msg = f"连接测试失败: {str(e)}"
            logger.error(f"未知错误: {e}")
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            raise Exception(error_msg)
        finally:
            if server:
                try:
                    server.quit()
                except:
                    pass
    
    def _test_tencent_exmail(self, smtp_host: str, smtp_port: int, from_email: str, from_password: str) -> bool:
        """
        专门针对腾讯企业邮箱的连接测试 - 优化版
        """
        logger.info("=== 腾讯企业邮箱连接测试开始 ===")
        logger.info(f"目标服务器: {smtp_host}:{smtp_port}")
        logger.info(f"用户邮箱: {from_email}")
        
        # 重新排序连接配置，优先使用STARTTLS
        connection_configs = [
            {
                'name': 'STARTTLS_587_优先',
                'host': smtp_host,
                'port': 587,
                'method': 'starttls',
                'timeout': 15
            },
            {
                'name': 'STARTTLS_25',
                'host': smtp_host,
                'port': 25,
                'method': 'starttls',
                'timeout': 15
            },
            {
                'name': 'SSL_465_宽松',
                'host': smtp_host,
                'port': 465,
                'method': 'ssl_relaxed',
                'timeout': 15
            },
            {
                'name': 'SSL_465_标准',
                'host': smtp_host,
                'port': 465,
                'method': 'ssl_default',
                'timeout': 15
            },
            {
                'name': 'STARTTLS_2525',
                'host': smtp_host,
                'port': 2525,
                'method': 'starttls',
                'timeout': 15
            }
        ]
        
        errors = []
        
        for i, config in enumerate(connection_configs):
            try:
                logger.info(f"[{i+1}/{len(connection_configs)}] 尝试: {config['name']} ({config['host']}:{config['port']})")
                
                success = self._test_enhanced_connection(
                    config['host'],
                    config['port'],
                    from_email,
                    from_password,
                    config['method'],
                    config['timeout']
                )
                
                if success:
                    logger.info(f"✓ 连接成功！使用配置: {config['name']}")
                    return True
                    
            except Exception as e:
                error_msg = f"{config['name']}: {str(e)}"
                errors.append(error_msg)
                logger.warning(f"✗ {config['name']} 失败: {e}")
                
                # 如果是认证错误，直接返回，不再尝试其他配置
                if "authentication failed" in str(e).lower() or "535" in str(e):
                    raise Exception("认证失败: 用户名或密码错误，请检查邮箱账号和授权码")
                
                continue
        
        # 所有配置都失败，提供详细的错误报告
        logger.error("=== 所有连接配置均失败 ===")
        for error in errors:
            logger.error(f"  - {error}")
        
        raise Exception(f"所有连接方式均失败。尝试了{len(connection_configs)}种配置，建议检查网络连接或联系邮箱服务商")
    
    def _test_enhanced_connection(self, smtp_host: str, smtp_port: int, from_email: str, from_password: str, method: str, timeout: int) -> bool:
        """
        增强的连接测试方法
        """
        server = None
        try:
            logger.info(f"  → 开始连接 {smtp_host}:{smtp_port} (方法: {method}, 超时: {timeout}s)")
            
            # 根据方法创建连接
            if method == 'starttls':
                # STARTTLS连接 (推荐)
                logger.info(f"  → 建立普通SMTP连接...")
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=timeout)
                server.set_debuglevel(0)  # 关闭调试避免日志过多
                
                logger.info(f"  → 发送EHLO命令...")
                server.ehlo()
                
                logger.info(f"  → 启动STARTTLS加密...")
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                context.set_ciphers('HIGH:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!MD5:!PSK:!SRP:!CAMELLIA')
                server.starttls(context=context)
                
                # STARTTLS后需要重新EHLO
                server.ehlo()
                
            elif method == 'ssl_relaxed':
                # 宽松SSL连接
                logger.info(f"  → 建立宽松SSL连接...")
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                context.set_ciphers('HIGH:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!MD5:!PSK:!SRP:!CAMELLIA')
                
                # 对于一些老旧的服务器，可能需要更宽松的设置
                try:
                    context.minimum_version = ssl.TLSVersion.TLSv1
                except:
                    pass  # 某些Python版本可能不支持
                
                server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=timeout, context=context)
                server.set_debuglevel(0)
                server.ehlo()
                
            elif method == 'ssl_default':
                # 标准SSL连接
                logger.info(f"  → 建立标准SSL连接...")
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=timeout, context=context)
                server.set_debuglevel(0)
                server.ehlo()
                
            else:
                raise Exception(f"不支持的连接方法: {method}")
            
            # 测试连接稳定性
            logger.info(f"  → 测试连接稳定性...")
            server.noop()
            
            # 尝试登录
            logger.info(f"  → 尝试登录用户: {from_email}")
            server.login(from_email, from_password)
            
            # 再次测试连接
            server.noop()
            
            logger.info(f"  ✓ 连接和认证成功！")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"  ✗ 认证失败: {e}")
            raise Exception(f"认证失败: 用户名或密码错误")
        except smtplib.SMTPConnectError as e:
            logger.error(f"  ✗ 连接失败: {e}")
            raise Exception(f"无法连接到服务器")
        except smtplib.SMTPServerDisconnected as e:
            logger.error(f"  ✗ 服务器断开连接: {e}")
            raise Exception(f"服务器意外断开连接")
        except ssl.SSLError as e:
            logger.error(f"  ✗ SSL错误: {e}")
            raise Exception(f"SSL/TLS握手失败")
        except socket.timeout as e:
            logger.error(f"  ✗ 连接超时: {e}")
            raise Exception(f"连接超时({timeout}秒)")
        except socket.gaierror as e:
            logger.error(f"  ✗ DNS解析失败: {e}")
            raise Exception(f"无法解析服务器地址")
        except Exception as e:
            logger.error(f"  ✗ 其他错误: {e}")
            raise Exception(f"连接失败: {str(e)}")
        finally:
            if server:
                try:
                    logger.info(f"  → 关闭连接...")
                    server.quit()
                except Exception as quit_error:
                    logger.warning(f"  → 关闭连接时出错: {quit_error}")
                    pass
    
    
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
            smtp_port = self.settings.get('smtp_port', 465)
            smtp_host = self.settings.get('smtp_host')
            
            # 针对不同邮箱服务商的连接处理
            if smtp_port == 465:
                # 465端口使用SSL连接
                try:
                    # 尝试默认SSL配置
                    server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30)
                except ssl.SSLError:
                    # 如果默认SSL失败，尝试自定义SSL上下文
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    server = smtplib.SMTP_SSL(smtp_host, smtp_port, context=context, timeout=30)
            elif smtp_port == 587:
                # 587端口使用STARTTLS
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=30)
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                server.starttls(context=context)
            elif smtp_port == 25:
                # 25端口通常不使用加密
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=30)
            else:
                # 其他端口根据use_ssl参数决定
                if self.settings.get('use_ssl', True):
                    server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30)
                else:
                    server = smtplib.SMTP(smtp_host, smtp_port, timeout=30)
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    server.starttls(context=context)
            
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