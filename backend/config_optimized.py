"""
优化后的配置文件
专门针对低资源占用进行优化
"""

import os
from datetime import timedelta


class OptimizedConfig:
    """优化配置类 - 最小化资源占用"""
    
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'optimized-website-monitor-key'
    
    # 数据库配置
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///database/website_monitor.db'
    
    # 日志配置 - 优化版本
    LOG_LEVEL = 'WARNING'  # 从INFO改为WARNING，减少日志量
    LOG_FILE = 'logs/app.log'
    LOG_MAX_SIZE = 3 * 1024 * 1024  # 3MB（进一步减小）
    LOG_BACKUP_COUNT = 2  # 只保留2个备份
    
    # 检测配置 - 大幅优化
    DETECTION_CONFIG = {
        'timeout_seconds': 15,      # 从30降到15
        'retry_times': 1,           # 从3降到1
        'max_concurrent': 8,        # 从20降到8
        'verify_ssl': False,
        'user_agent': 'WebMonitor/1.0'  # 简化UA
    }
    
    # 异步检测配置 - 极度优化
    ASYNC_DETECTION_CONFIG = {
        'max_concurrent': 12,       # 从20进一步降到12
        'max_per_host': 3,          # 从5降到3
        'timeout_total': 12,        # 从15降到12
        'timeout_connect': 6,       # 从8降到6
        'timeout_read': 8,          # 从12降到8
        'max_redirects': 2,         # 从3降到2
        'max_content_size': 256*1024,  # 从512KB降到256KB
        'dns_cache_ttl': 900,       # 从600提高到900
        'keep_alive': True
    }
    
    # 内存管理配置 - 严格限制
    MEMORY_CONFIG = {
        'warning_percent': 50.0,    # 从60%降到50%
        'critical_percent': 65.0,   # 从75%降到65%
        'cleanup_percent': 55.0,    # 从65%降到55%
        'max_memory_mb': 256,       # 从512降到256MB
        'gc_interval': 600,         # 从300提高到600秒
        'monitor_interval': 60      # 从30提高到60秒
    }
    
    # 调度器配置 - 最小化资源
    SCHEDULER_CONFIG = {
        'max_workers': 1,           # 从2降到1
        'poll_interval': 120,       # 从60提高到120秒
        'cleanup_interval_hours': 48  # 从24提高到48小时
    }
    
    # 数据库连接池配置
    DB_POOL_CONFIG = {
        'pool_size': 3,             # 小连接池
        'max_overflow': 2,          # 最小溢出
        'pool_timeout': 10,         # 快速超时
        'pool_recycle': 1800        # 30分钟回收连接
    }
    
    # 缓存配置
    CACHE_CONFIG = {
        'default_timeout': 300,     # 5分钟缓存
        'max_entries': 100,         # 最多100个缓存项
        'cleanup_interval': 600     # 10分钟清理一次
    }
    
    # 文件清理配置
    FILE_CLEANUP_CONFIG = {
        'log_retention_days': 3,    # 从7天降到3天
        'temp_file_retention_hours': 2,  # 从24小时降到2小时
        'max_file_size_mb': 50,     # 单文件最大50MB
        'cleanup_batch_size': 10    # 批量清理10个文件
    }
    
    # API限流配置
    RATE_LIMIT_CONFIG = {
        'requests_per_minute': 30,  # 每分钟30个请求
        'burst_limit': 10,          # 突发限制10个
        'cleanup_interval': 300     # 5分钟清理一次
    }


class ProductionOptimizedConfig(OptimizedConfig):
    """生产环境优化配置"""
    
    # 更严格的生产环境限制
    LOG_LEVEL = 'ERROR'  # 生产环境只记录错误
    
    DETECTION_CONFIG = {
        **OptimizedConfig.DETECTION_CONFIG,
        'max_concurrent': 5,        # 生产环境进一步降低
        'timeout_seconds': 10       # 更短超时
    }
    
    ASYNC_DETECTION_CONFIG = {
        **OptimizedConfig.ASYNC_DETECTION_CONFIG,
        'max_concurrent': 8,        # 生产环境更保守
        'max_per_host': 2           # 每主机最多2个连接
    }
    
    MEMORY_CONFIG = {
        **OptimizedConfig.MEMORY_CONFIG,
        'max_memory_mb': 128,       # 生产环境限制128MB
        'warning_percent': 40.0,    # 更早警告
        'critical_percent': 55.0    # 更早清理
    }


# 根据环境选择配置
def get_optimized_config():
    """获取优化配置"""
    env = os.environ.get('FLASK_ENV', 'development')
    
    if env == 'production':
        return ProductionOptimizedConfig()
    else:
        return OptimizedConfig()


# 导出配置实例
optimized_config = get_optimized_config() 