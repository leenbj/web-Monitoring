"""
网址监控工具 - 系统设置API路由
处理系统设置和邮件配置
"""

from flask import Blueprint, request, jsonify
from typing import Dict, List
import json
import traceback

from sqlalchemy.orm import Session
from ..database import get_db
from ..models import SystemSetting
from ..services.email_notification_service import EmailService

import logging

logger = logging.getLogger(__name__)

bp = Blueprint('settings', __name__, url_prefix='/api/settings')


@bp.route('/email', methods=['GET'])
def get_email_settings():
    """
    获取邮件设置
    """
    try:
        with get_db() as db:
            # 获取所有邮件相关设置
            email_settings = {}
            
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
            result = {**default_settings, **email_settings}
            
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': result
            })
        
    except Exception as e:
        logger.error(f"获取邮件设置失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'获取邮件设置失败: {str(e)}',
            'data': None
        }), 500


@bp.route('/email', methods=['POST'])
def save_email_settings():
    """
    保存邮件设置
    """
    try:
        with get_db() as db:
            data = request.get_json() or {}
            
            # 设置映射
            setting_map = {
                'enabled': ('email_enabled', 'boolean'),
                'smtp_host': ('email_smtp_host', 'string'),
                'smtp_port': ('email_smtp_port', 'integer'),
                'from_email': ('email_from_email', 'string'),
                'from_password': ('email_from_password', 'string'),
                'from_name': ('email_from_name', 'string'),
                'use_ssl': ('email_use_ssl', 'boolean'),
                'recipients': ('email_recipients', 'json'),
                'notification_types': ('email_notification_types', 'json'),
                'frequency_limit': ('email_frequency_limit', 'string')
            }
            
            for key, value in data.items():
                if key in setting_map:
                    setting_key, data_type = setting_map[key]
                    
                    # 查找或创建设置
                    setting = db.query(SystemSetting).filter(
                        SystemSetting.key == setting_key
                    ).first()
                    
                    if not setting:
                        setting = SystemSetting(
                            key=setting_key,
                            category='email',
                            data_type=data_type,
                            description=f'邮件设置 - {key}'
                        )
                        db.add(setting)
                    
                    # 设置值
                    if data_type == 'json':
                        setting.value = json.dumps(value, ensure_ascii=False)
                    elif data_type == 'boolean':
                        setting.value = str(bool(value)).lower()
                    else:
                        setting.value = str(value)
            
            db.commit()
            
            logger.info("邮件设置保存成功")
            
            return jsonify({
                'code': 200,
                'message': '邮件设置保存成功',
                'data': None
            })
        
    except Exception as e:
        logger.error(f"保存邮件设置失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'保存邮件设置失败: {str(e)}',
            'data': None
        }), 500


@bp.route('/email/test-connection', methods=['POST'])
def test_email_connection():
    """
    测试邮箱连接
    """
    try:
        data = request.get_json() or {}
        
        # 创建邮件服务实例
        email_service = EmailService()
        
        # 测试连接
        success = email_service.test_connection(
            smtp_host=data.get('smtp_host'),
            smtp_port=data.get('smtp_port', 465),
            from_email=data.get('from_email'),
            from_password=data.get('from_password'),
            use_ssl=data.get('use_ssl', True)
        )
        
        if success:
            return jsonify({
                'code': 200,
                'message': 'SMTP连接测试成功',
                'data': None
            })
        else:
            return jsonify({
                'code': 400,
                'message': 'SMTP连接测试失败',
                'data': None
            }), 400
        
    except Exception as e:
        logger.error(f"测试邮箱连接失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'测试连接失败: {str(e)}',
            'data': None
        }), 500


@bp.route('/email/test-send', methods=['POST'])
def send_test_email():
    """
    发送测试邮件
    """
    try:
        with get_db() as db:
            # 获取邮件设置
            email_service = EmailService()
            settings = email_service.load_settings(db)
            
            if not settings.get('enabled'):
                return jsonify({
                    'code': 400,
                    'message': '邮件通知功能未启用',
                    'data': None
                }), 400
            
            recipients = settings.get('recipients', [])
            if not recipients:
                return jsonify({
                    'code': 400,
                    'message': '未配置收件人',
                    'data': None
                }), 400
            
            # 发送测试邮件
            success = email_service.send_test_email(recipients)
            
            if success:
                return jsonify({
                    'code': 200,
                    'message': f'测试邮件已发送至 {len(recipients)} 个收件人',
                    'data': None
                })
            else:
                return jsonify({
                    'code': 400,
                    'message': '测试邮件发送失败',
                    'data': None
                }), 400
        
    except Exception as e:
        logger.error(f"发送测试邮件失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'发送测试邮件失败: {str(e)}',
            'data': None
        }), 500


@bp.route('/system', methods=['GET'])
def get_system_settings():
    """
    获取系统设置
    """
    try:
        with get_db() as db:
            # 默认设置
            default_settings = {
                'system_name': '中网网址在线监控',
                'data_retention_days': 30,
                'default_timeout': 30,
                'default_retry_times': 3
            }
            
            # 从数据库获取设置
            system_settings = {}
            settings = db.query(SystemSetting).filter(
                SystemSetting.category == 'system',
                SystemSetting.is_active == True
            ).all()
            
            for setting in settings:
                key = setting.key.replace('system_', '')  # 移除前缀
                if setting.data_type == 'integer':
                    system_settings[key] = int(setting.value)
                elif setting.data_type == 'boolean':
                    system_settings[key] = setting.value.lower() in ('true', '1', 'yes')
                else:
                    system_settings[key] = setting.value
            
            # 合并默认设置
            result = {**default_settings, **system_settings}
            
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': result
            })
        
    except Exception as e:
        logger.error(f"获取系统设置失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'获取系统设置失败: {str(e)}',
            'data': None
        }), 500


@bp.route('/system', methods=['POST'])
def save_system_settings():
    """
    保存系统设置
    """
    try:
        with get_db() as db:
            data = request.get_json() or {}
            
            # 设置映射
            setting_map = {
                'system_name': ('system_system_name', 'string'),
                'data_retention_days': ('system_data_retention_days', 'integer'),
                'default_timeout': ('system_default_timeout', 'integer'),
                'default_retry_times': ('system_default_retry_times', 'integer')
            }
            
            for key, value in data.items():
                if key in setting_map:
                    setting_key, data_type = setting_map[key]
                    
                    # 查找或创建设置
                    setting = db.query(SystemSetting).filter(
                        SystemSetting.key == setting_key
                    ).first()
                    
                    if not setting:
                        setting = SystemSetting(
                            key=setting_key,
                            category='system',
                            data_type=data_type,
                            description=f'系统设置 - {key}'
                        )
                        db.add(setting)
                    
                    # 设置值
                    setting.value = str(value)
            
            db.commit()
            
            logger.info("系统设置保存成功")
            
            return jsonify({
                'code': 200,
                'message': '系统设置保存成功',
                'data': None
            })
        
    except Exception as e:
        logger.error(f"保存系统设置失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'保存系统设置失败: {str(e)}',
            'data': None
        }), 500