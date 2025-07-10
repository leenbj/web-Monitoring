#!/usr/bin/env python3
"""
简化的数据库初始化脚本
用于在Docker容器内修复数据库问题
"""

import sqlite3
import hashlib
from datetime import datetime

def create_admin_user():
    """创建默认管理员用户"""
    db_path = '/app/database/website_monitor.db'
    
    try:
        print("连接数据库...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查用户表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
        if not cursor.fetchone():
            print("❌ 用户表不存在，需要先创建数据库表")
            
            # 创建用户表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(128) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    real_name VARCHAR(100) NOT NULL,
                    role VARCHAR(20) NOT NULL DEFAULT 'user',
                    status VARCHAR(20) NOT NULL DEFAULT 'active',
                    last_login_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)
            print("✅ 用户表创建成功")
        
        # 检查是否已有admin用户
        cursor.execute("SELECT username, role, status FROM users WHERE username='admin';")
        existing_user = cursor.fetchone()
        
        if existing_user:
            print(f"✅ admin用户已存在: {existing_user}")
            return True
        
        # 生成密码哈希 (使用简单的方法，因为可能没有werkzeug)
        import hashlib
        password = 'admin123'
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), b'salt', 100000).hex()
        
        # 插入默认管理员用户
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO users (username, password_hash, email, real_name, role, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ('admin', password_hash, 'admin@example.com', '系统管理员', 'admin', 'active', now, now))
        
        conn.commit()
        print("✅ 默认管理员用户创建成功")
        print("用户名: admin")
        print("密码: admin123")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据库操作失败: {e}")
        return False
    finally:
        if conn:
            conn.close()

def check_database_structure():
    """检查数据库结构"""
    db_path = '/app/database/website_monitor.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("=== 数据库结构检查 ===")
        
        # 检查所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"数据库表数量: {len(tables)}")
        for table in tables:
            print(f"  - {table[0]}")
        
        # 检查用户表结构
        if any('users' in table for table in tables):
            cursor.execute("PRAGMA table_info(users);")
            columns = cursor.fetchall()
            print("\n用户表结构:")
            for col in columns:
                print(f"  {col[1]} {col[2]} {'NOT NULL' if col[3] else ''}")
            
            # 检查用户数据
            cursor.execute("SELECT username, role, status FROM users;")
            users = cursor.fetchall()
            print(f"\n用户数据 ({len(users)}条):")
            for user in users:
                print(f"  {user[0]} - {user[1]} - {user[2]}")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    print("=== 数据库初始化工具 ===")
    
    # 检查数据库
    if check_database_structure():
        print("\n数据库检查完成")
    
    # 创建管理员用户
    if create_admin_user():
        print("\n✅ 数据库初始化成功")
    else:
        print("\n❌ 数据库初始化失败")