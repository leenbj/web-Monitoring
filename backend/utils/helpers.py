"""
网址监控工具 - 通用帮助函数
包含URL处理、文件操作、时间处理等通用功能
"""

import os
import re
import uuid
import hashlib
import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

import chardet
import requests
import logging

logger = logging.getLogger(__name__)

# 北京时区
BEIJING_TZ = timezone(timedelta(hours=8))


def get_beijing_time() -> datetime:
    """
    获取北京时间
    
    Returns:
        北京时间
    """
    return datetime.now(BEIJING_TZ)


def get_beijing_timezone():
    """
    获取北京时区对象
    
    Returns:
        北京时区
    """
    return BEIJING_TZ


def utc_to_beijing(dt: datetime) -> datetime:
    """
    将UTC时间转换为北京时间
    
    Args:
        dt: UTC时间
        
    Returns:
        北京时间
    """
    if dt is None:
        return None
    
    # 如果datetime对象没有时区信息，假设它是UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    # 转换为北京时间
    return dt.astimezone(BEIJING_TZ)


def normalize_url(url: str) -> str:
    """
    标准化URL格式 - 增强版
    
    Args:
        url: 原始URL
        
    Returns:
        标准化后的URL
    """
    if not url:
        return ""
    
    # 去除首尾空白字符和特殊字符
    url = url.strip().replace('\n', '').replace('\r', '').replace('\t', '')
    
    # 移除可能的引号
    url = url.strip('"\'')
    
    # 处理常见的格式问题
    if url.startswith('//'):
        url = 'http:' + url
    elif url.startswith('www.') and not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    elif not url.startswith(('http://', 'https://')) and '.' in url:
        url = 'http://' + url
    
    try:
        # 解析URL
        parsed = urllib.parse.urlparse(url)
        
        # 验证域名部分
        if not parsed.netloc:
            return ""
        
        # 处理中文域名编码
        netloc = parsed.netloc.lower()
        try:
            # 如果包含中文字符，先转换为IDNA编码再解码
            if any('\u4e00' <= c <= '\u9fff' for c in netloc):
                netloc = netloc.encode('idna').decode('ascii')
        except Exception:
            # 如果编码失败，保持原样
            pass
        
        # 重新组装URL
        normalized = urllib.parse.urlunparse((
            parsed.scheme,
            netloc,
            parsed.path or '/',     # 如果没有路径，添加/
            parsed.params,
            parsed.query,
            ''  # 移除fragment部分，减少变化
        ))
        
        return normalized
    except Exception as e:
        logger.warning(f"URL标准化失败: {url}, 错误: {e}")
        return url


def extract_domain(url: str) -> str:
    """
    从URL中提取域名
    
    Args:
        url: URL地址
        
    Returns:
        域名部分
    """
    try:
        parsed = urllib.parse.urlparse(normalize_url(url))
        return parsed.netloc.lower()
    except Exception as e:
        logger.warning(f"域名提取失败: {url}, 错误: {e}")
        return ""


def is_chinese_domain(domain: str) -> bool:
    """
    判断是否为中文域名
    
    Args:
        domain: 域名
        
    Returns:
        是否为中文域名
    """
    if not domain:
        return False
    
    # 检查是否包含中文字符
    chinese_pattern = re.compile(r'[\u4e00-\u9fff]+')
    return bool(chinese_pattern.search(domain))


def detect_url_redirect_type(original_url: str, final_url: str) -> str:
    """
    检测URL重定向类型 - 增强版
    
    Args:
        original_url: 原始URL
        final_url: 最终URL
        
    Returns:
        重定向类型: 'standard', 'redirect', 'failed'
    """
    if not final_url:
        return 'failed'
    
    try:
        import urllib.parse
        
        original_parsed = urllib.parse.urlparse(original_url)
        final_parsed = urllib.parse.urlparse(final_url)
        
        original_domain = original_parsed.netloc.lower()
        final_domain = final_parsed.netloc.lower()
        
        # 去除www前缀进行比较
        original_domain_clean = original_domain.replace('www.', '')
        final_domain_clean = final_domain.replace('www.', '')
        
        # 1. 如果域名完全相同，认为是标准解析
        if original_domain == final_domain:
            return 'standard'
        
        # 2. 如果去除www后相同，也认为是标准解析
        if original_domain_clean == final_domain_clean:
            return 'standard'
        
        # 3. 检查是否只是协议变化（HTTP -> HTTPS）
        if (original_domain_clean == final_domain_clean and 
            original_parsed.scheme != final_parsed.scheme):
            return 'standard'
        
        # 4. 检查是否是中文域名的各种编码转换
        if is_chinese_domain(original_domain):
            try:
                # 将中文域名转换为Punycode
                punycode_domain = original_domain.encode('idna').decode('ascii')
                if punycode_domain == final_domain or punycode_domain.replace('www.', '') == final_domain_clean:
                    return 'standard'  # 中文域名正常解析为Punycode
            except Exception:
                pass
        
        # 5. 检查最终URL是否也是中文域名
        if is_chinese_domain(final_domain):
            try:
                # 将最终域名转换为Punycode，与原始域名比较
                final_punycode = final_domain.encode('idna').decode('ascii')
                if final_punycode == original_domain or final_punycode.replace('www.', '') == original_domain_clean:
                    return 'standard'
            except Exception:
                pass
        
        # 6. 检查是否是子域名或父域名的跳转
        if '.' in original_domain_clean and '.' in final_domain_clean:
            # 提取主域名（去除子域名）
            original_main = '.'.join(original_domain_clean.split('.')[-2:])
            final_main = '.'.join(final_domain_clean.split('.')[-2:])
            
            # 如果主域名相同，可能是子域名跳转，仍认为是标准解析
            if original_main == final_main:
                return 'standard'
        
        # 7. 其他情况认为是跳转
        return 'redirect'
        
    except Exception as e:
        logger.warning(f"重定向类型检测失败: {original_url} -> {final_url}, 错误: {e}")
        return 'failed'


def generate_unique_filename(original_filename: str, upload_dir: str = None) -> str:
    """
    生成唯一文件名
    
    Args:
        original_filename: 原始文件名
        upload_dir: 上传目录（可选）
        
    Returns:
        唯一文件名
    """
    # 获取文件扩展名
    _, ext = os.path.splitext(original_filename)
    
    # 生成UUID作为文件名
    unique_name = str(uuid.uuid4()) + ext
    
    # 如果指定了目录，确保文件名在该目录下唯一
    if upload_dir and os.path.exists(upload_dir):
        counter = 1
        base_name = unique_name
        while os.path.exists(os.path.join(upload_dir, unique_name)):
            name, ext = os.path.splitext(base_name)
            unique_name = f"{name}_{counter}{ext}"
            counter += 1
    
    return unique_name


def get_file_size_human(size_bytes: int) -> str:
    """
    将文件大小转换为人类可读格式
    
    Args:
        size_bytes: 文件大小（字节）
        
    Returns:
        格式化的文件大小
    """
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.2f}{size_names[i]}"


def detect_file_encoding(file_path: str) -> str:
    """
    检测文件编码
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件编码
    """
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            return result.get('encoding', 'utf-8')
    except Exception as e:
        logger.warning(f"文件编码检测失败: {file_path}, 错误: {e}")
        return 'utf-8'


def ensure_dir(directory: str) -> bool:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        directory: 目录路径
        
    Returns:
        是否成功创建或目录已存在
    """
    return create_directory_if_not_exists(directory)


def create_directory_if_not_exists(directory: str) -> bool:
    """
    创建目录（如果不存在）
    
    Args:
        directory: 目录路径
        
    Returns:
        是否创建成功
    """
    try:
        Path(directory).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"创建目录失败: {directory}, 错误: {e}")
        return False


def clean_old_files(directory: str, days: int) -> int:
    """
    清理指定天数前的旧文件
    
    Args:
        directory: 目录路径
        days: 保留天数
        
    Returns:
        清理的文件数量
    """
    if not os.path.exists(directory):
        return 0
    
    cutoff_time = datetime.now() - timedelta(days=days)
    cleaned_count = 0
    
    try:
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                # 获取文件修改时间
                mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                if mtime < cutoff_time:
                    os.remove(file_path)
                    cleaned_count += 1
                    logger.info(f"清理旧文件: {file_path}")
    except Exception as e:
        logger.error(f"清理旧文件失败: {directory}, 错误: {e}")
    
    return cleaned_count


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    格式化日期时间
    
    Args:
        dt: 日期时间对象
        format_str: 格式字符串
        
    Returns:
        格式化的日期时间字符串
    """
    if not dt:
        return ""
    return dt.strftime(format_str)


def parse_datetime(date_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime]:
    """
    解析日期时间字符串
    
    Args:
        date_str: 日期时间字符串
        format_str: 格式字符串
        
    Returns:
        日期时间对象
    """
    try:
        return datetime.strptime(date_str, format_str)
    except Exception as e:
        logger.warning(f"日期时间解析失败: {date_str}, 错误: {e}")
        return None


def calculate_time_ago(dt: datetime) -> str:
    """
    计算相对时间（多久前）
    
    Args:
        dt: 日期时间对象
        
    Returns:
        相对时间描述
    """
    if not dt:
        return "未知"
    
    # 使用北京时间计算
    now = get_beijing_time()
    
    # 如果输入的时间没有时区信息，转换为北京时间
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc).astimezone(BEIJING_TZ)
    elif dt.tzinfo != BEIJING_TZ:
        dt = dt.astimezone(BEIJING_TZ)
    
    diff = now - dt
    
    if diff.days > 0:
        return f"{diff.days}天前"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours}小时前"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes}分钟前"
    else:
        return "刚刚"


def get_file_hash(file_path: str, algorithm: str = 'md5') -> str:
    """
    计算文件哈希值
    
    Args:
        file_path: 文件路径
        algorithm: 哈希算法（md5, sha1, sha256）
        
    Returns:
        文件哈希值
    """
    try:
        hash_func = hashlib.new(algorithm)
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except Exception as e:
        logger.error(f"计算文件哈希失败: {file_path}, 错误: {e}")
        return ""


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断文本
    
    Args:
        text: 原始文本
        max_length: 最大长度
        suffix: 后缀
        
    Returns:
        截断后的文本
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def safe_get_dict_value(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    安全获取字典值
    
    Args:
        data: 字典数据
        key: 键名，支持点号分隔的嵌套键
        default: 默认值
        
    Returns:
        字典值
    """
    try:
        keys = key.split('.')
        value = data
        for k in keys:
            value = value[k]
        return value
    except (KeyError, TypeError, AttributeError):
        return default


def batch_process_list(items: List[Any], batch_size: int = 100):
    """
    批量处理列表
    
    Args:
        items: 待处理的项目列表
        batch_size: 批次大小
        
    Yields:
        每个批次的项目列表
    """
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size] 