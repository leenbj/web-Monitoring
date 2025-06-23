"""
网址监控工具 - 装饰器工具
"""

from functools import wraps
from flask import g
from sqlalchemy.orm import Session
from ..database import get_db
import logging

logger = logging.getLogger(__name__)


def with_db_session(f):
    """
    数据库会话管理装饰器
    自动管理数据库会话的创建和关闭
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 如果已经有会话，直接使用
        if hasattr(g, 'db_session'):
            return f(*args, **kwargs)
        
        # 创建新的数据库会话
        db = get_db()
        g.db_session = db
        
        try:
            result = f(*args, **kwargs)
            db.commit()  # 自动提交事务
            return result
        except Exception as e:
            db.rollback()  # 出错时回滚
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            db.close()  # 确保关闭会话
            if hasattr(g, 'db_session'):
                delattr(g, 'db_session')
    
    return decorated_function


def get_current_db() -> Session:
    """
    获取当前请求的数据库会话
    """
    if hasattr(g, 'db_session'):
        return g.db_session
    else:
        # 如果没有会话，创建一个新的
        return get_db() 