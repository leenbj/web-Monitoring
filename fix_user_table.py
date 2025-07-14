#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复用户表结构脚本
将数据库中的用户表结构更新为与User模型匹配
"""

import pymysql
from werkzeug.security import generate_password_hash
from datetime import datetime

# 数据库连接配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 33061,
    'user': 'webmonitor',
    'password': 'webmonitor123',
    'database': 'website_monitor',
    'charset': 'utf8mb4'
}

def fix_user_table():
    """修复用户表结构"""
    try:
        # 连接数据库
        connection = pymysql.connect(**DB_CONFIG)
        
        with connection.cursor() as cursor:
            print("🔍 检查用户表结构...")
            
            # 检查当前表结构
            cursor.execute("DESCRIBE users")
            columns = [row[0] for row in cursor.fetchall()]
            print(f"当前表字段: {columns}")
            
            # 检查是否需要添加新字段
            if 'role' not in columns:
                print("➕ 添加 role 字段...")
                cursor.execute("ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user'")
                
            if 'status' not in columns:
                print("➕ 添加 status 字段...")
                cursor.execute("ALTER TABLE users ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'active'")
                
            if 'last_login_at' not in columns:
                print("➕ 添加 last_login_at 字段...")
                cursor.execute("ALTER TABLE users ADD COLUMN last_login_at DATETIME NULL")
            
            # 如果存在旧的 is_admin 字段，迁移数据
            if 'is_admin' in columns:
                print("🔄 迁移 is_admin 数据到 role 字段...")
                cursor.execute("UPDATE users SET role = 'admin' WHERE is_admin = 1")
                cursor.execute("UPDATE users SET role = 'user' WHERE is_admin = 0")
                
                print("🗑️ 删除旧的 is_admin 字段...")
                cursor.execute("ALTER TABLE users DROP COLUMN is_admin")
                
            # 如果存在旧的 is_active 字段，迁移数据
            if 'is_active' in columns:
                print("🔄 迁移 is_active 数据到 status 字段...")
                cursor.execute("UPDATE users SET status = 'active' WHERE is_active = 1")
                cursor.execute("UPDATE users SET status = 'inactive' WHERE is_active = 0")
                
                print("🗑️ 删除旧的 is_active 字段...")
                cursor.execute("ALTER TABLE users DROP COLUMN is_active")
            
            # 检查是否存在管理员用户
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
            admin_count = cursor.fetchone()[0]
            
            if admin_count == 0:
                print("👤 创建默认管理员用户...")
                password_hash = generate_password_hash('admin123')
                cursor.execute(
                    "INSERT INTO users (username, email, password_hash, role, status, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    ('admin', 'admin@example.com', password_hash, 'admin', 'active', datetime.now(), datetime.now())
                )
                print("✅ 管理员用户创建成功: admin/admin123")
            else:
                print("👤 管理员用户已存在")
            
            # 提交更改
            connection.commit()
            print("✅ 用户表结构修复完成!")
            
            # 显示最终表结构
            cursor.execute("DESCRIBE users")
            print("\n最终表结构:")
            for row in cursor.fetchall():
                print(f"  {row[0]}: {row[1]}")
            
    except Exception as e:
        print(f"❌ 修复用户表失败: {e}")
        return False
    finally:
        connection.close()
    
    return True

if __name__ == '__main__':
    success = fix_user_table()
    if success:
        print("\n🎉 用户表修复成功！现在可以使用 admin/admin123 登录了。")
    else:
        print("\n💥 用户表修复失败！")