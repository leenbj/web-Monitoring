"""
网址监控工具 - 资源优化配置文件
专门针对低资源占用场景的配置
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent


class ResourceOptimizedConfig:
    """资源优化配置类 - 最大化降低资源占用"""
    
    # Flask基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'optimized-secret-key'
    DEBUG = False  # 强制关闭DEBUG模式
    
    # 数据库配置 - 极度优化
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{BASE_DIR}/database/website_monitor.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,  # 5分钟回收
        'pool_size': 2,       # 最小连接池
        'max_overflow': 3,    # 最小溢出
        'pool_timeout': 10,   # 短超时
    }
    
    # 文件上传配置
    UPLOAD_FOLDER = str(BASE_DIR / 'uploads')
    DOWNLOAD_FOLDER = str(BASE_DIR / 'downloads')
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8MB 最大文件大小（降低）
    ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
    
    # 日志配置
    LOG_FOLDER = str(BASE_DIR / 'logs')
    LOG_LEVEL = 'WARNING'  # 只记录警告和错误
    
    # 邮件配置
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.qq.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # 网站检测配置 - 极度优化
    DETECTION_CONFIG = {
        'min_interval_minutes': 30,      # 最短检测间隔（提高到30分钟）
        'max_concurrent': 3,             # 最大并发检测数（大幅降低）
        'timeout_seconds': 8,            # 请求超时时间（大幅降低）
        'retry_times': 1,                # 重试次数（最小化）
        'user_agent': 'OptimizedBot/1.0',
        'follow_redirects': True,
        'verify_ssl': False,
    }
    
    # 任务调度配置 - 极度优化
    SCHEDULER_CONFIG = {
        'timezone': 'Asia/Shanghai',
        'job_defaults': {
            'coalesce': True,            # 合并错过的任务
            'max_instances': 1,          # 同一任务最大实例数（降到1）
        },
        'thread_pool_size': 1,           # 线程池大小（最小化）
        'check_interval': 300,           # 检查间隔（5分钟）
    }
    
    # 数据保留配置 - 更激进的清理
    DATA_RETENTION = {
        'detection_records_days': 30,    # 检测记录保留天数（从90降到30）
        'log_files_days': 7,            # 日志文件保留天数（从30降到7）
        'upload_files_days': 1,         # 上传文件保留天数（从7降到1）
    }
    
    # API配置 - 降低负载
    API_CONFIG = {
        'pagination_per_page': 20,      # 分页每页数量（从50降到20）
        'max_export_records': 5000,     # 最大导出记录数（从10000降到5000）
        'rate_limit': '100/hour',       # 添加速率限制
    }
    
    # 批量检测配置 - 极度优化
    BATCH_DETECTION_CONFIG = {
        'batch_size': 5,                # 批次大小（最小化）
        'max_concurrent': 3,            # 最大并发数（最小化）
        'timeout_seconds': 8,           # 超时时间（最小化）
        'retry_times': 1,               # 重试次数（最小化）
        'memory_limit_mb': 64,          # 内存限制（最小化）
        'enable_async': False,          # 禁用异步（减少复杂性）
    }
    
    # 失败网站监控配置 - 大幅优化
    FAILED_MONITOR_CONFIG = {
        'interval_hours': 4,            # 检测间隔（4小时）
        'max_concurrent': 2,            # 最大并发数
        'timeout_seconds': 8,           # 超时时间
        'retry_times': 1,               # 重试次数
    }
    
    # 缓存配置
    CACHE_CONFIG = {
        'enable_cache': True,
        'cache_timeout': 300,           # 5分钟缓存
        'max_cache_size': 50,           # 最大缓存条目数
    }
    
    # 内存管理配置
    MEMORY_CONFIG = {
        'max_memory_mb': 256,           # 最大内存使用（256MB）
        'gc_threshold': 200,            # GC触发阈值（200MB）
        'monitor_interval': 60,         # 监控间隔（1分钟）
    }


def get_optimized_config():
    """获取资源优化配置"""
    return ResourceOptimizedConfig