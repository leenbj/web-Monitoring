"""
网址监控工具 - 数据库连接管理
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

# 创建数据库引擎 - 大规模监控优化配置
engine = create_engine(
    config.SQLALCHEMY_DATABASE_URI,
    echo=getattr(config, 'SQLALCHEMY_ECHO', False),
    # 优化连接池配置 - 降低资源占用
    poolclass=QueuePool,
    pool_size=10,                 # 连接池大小（从50降到10）
    max_overflow=20,              # 最大溢出连接数（从100降到20）
    pool_timeout=30,              # 获取连接超时时间（从60降到30）
    pool_recycle=1800,            # 连接回收时间(30分钟，从1小时降低)
    pool_pre_ping=True,           # 连接前检查
    # SQLite优化配置
    connect_args={
        "check_same_thread": False,  # SQLite特有配置
        "timeout": 60,               # SQLite连接超时（增加）
        "isolation_level": None,     # 自动提交模式
    } if 'sqlite' in config.SQLALCHEMY_DATABASE_URI else {
        # PostgreSQL/MySQL 优化配置
        "connect_timeout": 60,
        "server_side_cursors": True
    }
)

# 创建会话工厂
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    expire_on_commit=False  # 避免session过期问题
)


def init_db():
    """初始化数据库表"""
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_db():
    """获取数据库会话（上下文管理器）"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
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
        # 关闭所有活跃连接
        engine.dispose()
        logger.info("所有数据库连接已关闭")
    except Exception as e:
        logger.error(f"关闭数据库连接时出错: {e}")


def get_connection_stats():
    """获取连接池统计信息"""
    try:
        pool = engine.pool
        return {
            'pool_size': pool.size(),
            'checked_in': pool.checkedin(),
            'checked_out': pool.checkedout(),
            'overflow': pool.overflow(),
            'invalid': pool.invalidated()
        }
    except Exception as e:
        logger.error(f"获取连接池统计信息失败: {e}")
        return None