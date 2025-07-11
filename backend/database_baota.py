"""
网址监控工具 - 宝塔面板数据库连接管理
修复PyMySQL兼容性问题，优化MySQL连接配置
"""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool, QueuePool
from contextlib import contextmanager
from .config import get_config
from .models import Base

logger = logging.getLogger(__name__)

# 获取配置
config = get_config()

def create_database_engine():
    """创建优化的数据库引擎"""
    
    # 解析数据库URL
    db_url = config.SQLALCHEMY_DATABASE_URI
    
    # 基础连接参数
    connect_args = {}
    
    # 根据数据库类型设置连接参数
    if 'mysql' in db_url:
        # MySQL特定配置 - 修复PyMySQL兼容性
        connect_args = {
            "connect_timeout": 60,
            "charset": "utf8mb4",
            "autocommit": False,
            "isolation_level": "READ_COMMITTED",
            # 移除不兼容的server_side_cursors参数
            "init_command": "SET SESSION sql_mode='STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION'"
        }
        
        # 连接池配置
        pool_config = {
            'poolclass': QueuePool,
            'pool_size': 8,                    # 连接池大小
            'max_overflow': 15,                # 最大溢出连接
            'pool_timeout': 30,                # 获取连接超时
            'pool_recycle': 3600,             # 连接回收时间(1小时)
            'pool_pre_ping': True,            # 连接前检查
        }
        
    elif 'sqlite' in db_url:
        # SQLite特定配置
        connect_args = {
            "check_same_thread": False,
            "timeout": 60,
            "isolation_level": None,
        }
        
        # SQLite连接池配置
        pool_config = {
            'poolclass': StaticPool,
            'pool_size': 5,
            'max_overflow': 10,
            'pool_timeout': 30,
            'pool_recycle': 1800,
            'pool_pre_ping': True,
        }
    
    else:
        # PostgreSQL和其他数据库
        connect_args = {
            "connect_timeout": 60,
        }
        
        pool_config = {
            'poolclass': QueuePool,
            'pool_size': 5,
            'max_overflow': 10,
            'pool_timeout': 30,
            'pool_recycle': 3600,
            'pool_pre_ping': True,
        }
    
    # 创建引擎
    engine = create_engine(
        db_url,
        echo=getattr(config, 'SQLALCHEMY_ECHO', False),
        connect_args=connect_args,
        **pool_config
    )
    
    logger.info(f"数据库引擎创建成功: {db_url.split('://')[0]}")
    return engine


# 创建数据库引擎
engine = create_database_engine()

# 创建会话工厂
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    expire_on_commit=False  # 避免session过期问题
)


def init_db():
    """初始化数据库表"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表初始化成功")
    except Exception as e:
        logger.error(f"数据库表初始化失败: {e}")
        raise


@contextmanager
def get_db():
    """获取数据库会话（上下文管理器）"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"数据库操作失败: {e}")
        raise
    finally:
        db.close()


def get_db_session():
    """获取数据库会话（用于依赖注入）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_session():
    """创建新的数据库会话（需要手动关闭）"""
    return SessionLocal()


def close_all_connections():
    """关闭所有数据库连接"""
    try:
        engine.dispose()
        logger.info("所有数据库连接已关闭")
    except Exception as e:
        logger.error(f"关闭数据库连接时出错: {e}")


def test_database_connection():
    """测试数据库连接"""
    try:
        with get_db() as db:
            from sqlalchemy import text
            result = db.execute(text('SELECT 1 as test'))
            test_value = result.fetchone()[0]
            
            if test_value == 1:
                logger.info("数据库连接测试成功")
                return True
            else:
                logger.error("数据库连接测试失败")
                return False
    except Exception as e:
        logger.error(f"数据库连接测试异常: {e}")
        return False


def get_connection_stats():
    """获取连接池统计信息"""
    try:
        pool = engine.pool
        stats = {
            'pool_size': pool.size(),
            'checked_in': pool.checkedin(),
            'checked_out': pool.checkedout(),
            'overflow': pool.overflow(),
            'invalid': pool.invalidated()
        }
        return stats
    except Exception as e:
        logger.error(f"获取连接池统计信息失败: {e}")
        return None


def optimize_mysql_settings():
    """优化MySQL设置"""
    try:
        with get_db() as db:
            from sqlalchemy import text
            
            # 检查MySQL版本
            result = db.execute(text("SELECT VERSION()"))
            version = result.fetchone()[0]
            logger.info(f"MySQL版本: {version}")
            
            # 设置会话参数
            db.execute(text("SET SESSION sql_mode='STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION'"))
            db.execute(text("SET SESSION transaction_isolation='READ-COMMITTED'"))
            db.execute(text("SET SESSION wait_timeout=28800"))
            db.execute(text("SET SESSION interactive_timeout=28800"))
            
            logger.info("MySQL设置优化完成")
            return True
            
    except Exception as e:
        logger.error(f"MySQL设置优化失败: {e}")
        return False


# 在模块加载时测试连接
if __name__ != '__main__':
    if test_database_connection():
        logger.info("模块加载时数据库连接测试通过")
        # 如果是MySQL，应用优化设置
        if 'mysql' in config.SQLALCHEMY_DATABASE_URI:
            optimize_mysql_settings()
    else:
        logger.warning("模块加载时数据库连接测试失败")