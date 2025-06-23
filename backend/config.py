"""
网址监控工具 - 配置文件
包含应用的所有配置参数
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    """基础配置类"""
    
    # Flask基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production'
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{BASE_DIR}/database/website_monitor.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # 文件上传配置
    UPLOAD_FOLDER = str(BASE_DIR / 'uploads')
    DOWNLOAD_FOLDER = str(BASE_DIR / 'downloads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB 最大文件大小
    ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
    
    # 日志配置
    LOG_FOLDER = str(BASE_DIR / 'logs')
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # 邮件配置
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.qq.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'False').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # 网站检测配置
    DETECTION_CONFIG = {
        'min_interval_minutes': 10,      # 最短检测间隔（分钟）
        'max_concurrent': 20,            # 最大并发检测数
        'timeout_seconds': 30,           # 请求超时时间（秒）
        'retry_times': 3,                # 重试次数
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'follow_redirects': True,        # 是否跟随重定向
        'verify_ssl': False,             # 是否验证SSL证书
    }
    
    # 任务调度配置
    SCHEDULER_CONFIG = {
        'timezone': 'Asia/Shanghai',
        'job_defaults': {
            'coalesce': False,           # 是否合并错过的任务
            'max_instances': 3,          # 同一任务最大实例数
        }
    }
    
    # 数据保留配置
    DATA_RETENTION = {
        'detection_records_days': 90,    # 检测记录保留天数
        'log_files_days': 30,           # 日志文件保留天数
        'upload_files_days': 7,         # 上传文件保留天数
    }
    
    # API配置
    API_CONFIG = {
        'pagination_per_page': 50,      # 分页每页数量
        'max_export_records': 10000,    # 最大导出记录数
    }


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_ECHO = True  # 打印SQL语句


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    SQLALCHEMY_ECHO = False
    
    # 生产环境安全配置
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


# 配置映射
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """获取当前环境配置"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default']) 