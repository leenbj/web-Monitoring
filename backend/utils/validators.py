"""
网址监控工具 - 数据验证工具
包含各种数据验证功能
"""

import re
import os
import urllib.parse
from typing import List, Optional, Tuple

def is_valid_url(url: str) -> bool:
    """验证URL是否有效"""
    if not url or not isinstance(url, str):
        return False
    
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        
        result = urllib.parse.urlparse(url)
        return bool(result.netloc and result.scheme in ('http', 'https'))
    except Exception:
        return False


def validate_url(url: str) -> Tuple[bool, str]:
    """
    验证URL并返回结果
    
    Args:
        url: 待验证的URL
        
    Returns:
        验证结果元组 (是否有效, 错误信息)
    """
    if not url:
        return False, "URL不能为空"
    
    if not isinstance(url, str):
        return False, "URL必须是字符串类型"
    
    url = url.strip()
    if not url:
        return False, "URL不能为空"
    
    if len(url) > 2048:
        return False, "URL长度不能超过2048个字符"
    
    if not is_valid_url(url):
        return False, "URL格式不正确"
    
    return True, ""


def is_valid_domain(domain: str) -> bool:
    """验证域名是否有效"""
    if not domain or not isinstance(domain, str) or len(domain) > 253:
        return False
    
    domain = domain.replace('http://', '').replace('https://', '').split('/')[0]
    domain_pattern = re.compile(r'^[a-zA-Z0-9\u4e00-\u9fff][a-zA-Z0-9\u4e00-\u9fff\-\.]*[a-zA-Z0-9\u4e00-\u9fff]$')
    return bool(domain_pattern.match(domain))


def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
    """验证文件扩展名"""
    if not filename or not allowed_extensions:
        return False
    
    _, ext = os.path.splitext(filename.lower())
    ext = ext.lstrip('.')
    return ext in [e.lower().lstrip('.') for e in allowed_extensions]


def validate_excel_file(file_path: str) -> Tuple[bool, str]:
    """验证Excel文件"""
    if not os.path.exists(file_path):
        return False, "文件不存在"
    
    if not validate_file_extension(file_path, ['xlsx', 'xls']):
        return False, "文件格式不正确，请上传Excel文件"
    
    # 检查文件大小（16MB限制）
    file_size = os.path.getsize(file_path)
    if file_size > 16 * 1024 * 1024:
        return False, "文件大小超过16MB限制"
    
    return True, ""


def validate_csv_file(file_path: str) -> Tuple[bool, str]:
    """验证CSV文件"""
    if not os.path.exists(file_path):
        return False, "文件不存在"
    
    if not validate_file_extension(file_path, ['csv']):
        return False, "文件格式不正确，请上传CSV文件"
    
    # 检查文件大小（16MB限制）
    file_size = os.path.getsize(file_path)
    if file_size > 16 * 1024 * 1024:
        return False, "文件大小超过16MB限制"
    
    return True, ""


def validate_task_config(config: dict) -> Tuple[bool, List[str]]:
    """验证检测任务配置"""
    errors = []
    
    if not config.get('name'):
        errors.append("任务名称不能为空")
    elif len(config['name']) > 255:
        errors.append("任务名称不能超过255个字符")
    
    interval = config.get('interval_hours')
    if not interval or not isinstance(interval, int) or interval < 1:
        errors.append("检测间隔不能少于1小时")
    elif interval > 168:
        errors.append("检测间隔不能超过7天(168小时)")
    
    return len(errors) == 0, errors 