#!/usr/bin/env python3
"""
宝塔面板部署 - 用户表初始化脚本
预防性修复用户表结构，确保云端部署成功
"""

import os
import sys
import logging
from datetime import datetime

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('user_table_init.log')
    ]
)
logger = logging.getLogger(__name__)

def check_and_create_user_table():
    """检查并创建正确的用户表结构"""
    try:
        logger.info("🔧 开始检查用户表结构...")
        
        # 导入必要模块
        from backend.app import create_app
        from backend.database import get_db
        from sqlalchemy import text
        
        # 创建应用
        app = create_app()
        
        with app.app_context():
            logger.info("✅ Flask应用上下文创建成功")
            
            with get_db() as db:
                # 检查是否存在用户表
                try:
                    result = db.execute(text("SHOW TABLES LIKE 'users'"))
                    table_exists = result.fetchone() is not None
                    
                    if not table_exists:
                        logger.info("📊 用户表不存在，开始创建...")
                        create_user_table_sql = """
                        CREATE TABLE users (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            username VARCHAR(50) UNIQUE NOT NULL,
                            password_hash VARCHAR(128) NOT NULL,
                            email VARCHAR(100) UNIQUE NOT NULL,
                            real_name VARCHAR(100) NOT NULL,
                            role VARCHAR(20) NOT NULL DEFAULT 'user',
                            status VARCHAR(20) NOT NULL DEFAULT 'active',
                            last_login_at DATETIME NULL,
                            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                            INDEX idx_username (username),
                            INDEX idx_email (email)
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                        """
                        db.execute(text(create_user_table_sql))
                        logger.info("✅ 用户表创建成功")
                    else:
                        logger.info("📊 用户表已存在，检查字段...")
                        
                        # 检查表结构
                        result = db.execute(text("DESCRIBE users"))
                        columns = [row[0] for row in result.fetchall()]
                        logger.info(f"当前字段: {columns}")
                        
                        # 需要添加的字段
                        missing_fields = []
                        
                        field_definitions = {
                            'real_name': 'VARCHAR(100) NOT NULL',
                            'role': 'VARCHAR(20) NOT NULL DEFAULT \'user\'',
                            'status': 'VARCHAR(20) NOT NULL DEFAULT \'active\'',
                            'last_login_at': 'DATETIME NULL'
                        }
                        
                        for field, definition in field_definitions.items():
                            if field not in columns:
                                missing_fields.append((field, definition))
                        
                        if missing_fields:
                            logger.info(f"缺失字段: {[f[0] for f in missing_fields]}")
                            
                            # 添加缺失字段
                            for field, definition in missing_fields:
                                logger.info(f"添加字段: {field}")
                                db.execute(text(f"ALTER TABLE users ADD COLUMN {field} {definition}"))
                                
                                # 如果是real_name，用username填充
                                if field == 'real_name':
                                    db.execute(text("UPDATE users SET real_name = username WHERE real_name = '' OR real_name IS NULL"))
                                
                                # 如果是role，从is_admin迁移
                                if field == 'role' and 'is_admin' in columns:
                                    db.execute(text("UPDATE users SET role = 'admin' WHERE is_admin = 1"))
                                    db.execute(text("UPDATE users SET role = 'user' WHERE is_admin = 0"))
                                
                                # 如果是status，从is_active迁移
                                if field == 'status' and 'is_active' in columns:
                                    db.execute(text("UPDATE users SET status = 'active' WHERE is_active = 1"))
                                    db.execute(text("UPDATE users SET status = 'inactive' WHERE is_active = 0"))
                        
                        logger.info("✅ 字段检查和添加完成")
                    
                    # 提交更改
                    db.commit()
                    
                    # 创建默认用户
                    create_default_user(db)
                    
                    logger.info("✅ 用户表初始化完成")
                    return True
                    
                except Exception as e:
                    logger.error(f"❌ 用户表操作失败: {e}")
                    return False
                    
    except Exception as e:
        logger.error(f"❌ 用户表初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_default_user(db):
    """创建默认管理员用户"""
    try:
        # 检查是否已有用户
        result = db.execute(text("SELECT COUNT(*) FROM users"))
        user_count = result.fetchone()[0]
        
        if user_count == 0:
            logger.info("🔧 创建默认管理员用户...")
            
            # 生成密码哈希
            from werkzeug.security import generate_password_hash
            password_hash = generate_password_hash('admin123')
            
            # 插入默认用户
            insert_sql = """
            INSERT INTO users (username, password_hash, email, real_name, role, status, created_at, updated_at)
            VALUES ('admin', %s, 'admin@example.com', '系统管理员', 'admin', 'active', %s, %s)
            """
            
            now = datetime.now()
            db.execute(text(insert_sql), (password_hash, now, now))
            
            logger.info("✅ 默认管理员用户创建成功")
            logger.info("   用户名: admin")
            logger.info("   密码: admin123")
            logger.info("   邮箱: admin@example.com")
        else:
            logger.info("✅ 已存在用户，跳过默认用户创建")
            
    except Exception as e:
        logger.error(f"❌ 创建默认用户失败: {e}")


def test_user_table():
    """测试用户表功能"""
    try:
        logger.info("🧪 测试用户表功能...")
        
        from backend.app import create_app
        from backend.database import get_db
        from sqlalchemy import text
        
        app = create_app()
        
        with app.app_context():
            with get_db() as db:
                # 查询用户
                result = db.execute(text("SELECT id, username, email, real_name, role, status FROM users"))
                users = result.fetchall()
                
                logger.info(f"✅ 用户表测试成功，共找到 {len(users)} 个用户:")
                for user in users:
                    logger.info(f"   - ID:{user[0]} 用户名:{user[1]} 邮箱:{user[2]} 姓名:{user[3]} 角色:{user[4]} 状态:{user[5]}")
                
                return True
                
    except Exception as e:
        logger.error(f"❌ 用户表测试失败: {e}")
        return False


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("🚀 宝塔面板用户表初始化工具")
    logger.info("=" * 60)
    
    # 检查并创建用户表
    if check_and_create_user_table():
        logger.info("\n" + "=" * 60)
        logger.info("🧪 测试用户表功能")
        logger.info("=" * 60)
        
        # 测试用户表
        if test_user_table():
            logger.info("\n🎉 用户表初始化成功！")
            return 0
        else:
            logger.error("\n💥 用户表测试失败")
            return 1
    else:
        logger.error("\n💥 用户表初始化失败")
        return 1


if __name__ == '__main__':
    sys.exit(main())