#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建管理员用户脚本
"""

import pymysql
from werkzeug.security import generate_password_hash
from datetime import datetime

# 数据库连接配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'monitor_user',
    'password': 'Monitor123!@#',
    'database': 'website_monitor',
    'charset': 'utf8mb4'
}

def create_admin_user():
    """创建管理员用户"""
    try:
        # 连接数据库
        connection = pymysql.connect(**DB_CONFIG)
        
        with connection.cursor() as cursor:
            # 删除现有的admin用户
            cursor.execute("DELETE FROM users WHERE username = 'admin'")
            
            # 生成密码哈希
            password_hash = generate_password_hash('admin123')
            
            # 插入新的admin用户
            cursor.execute(
                "INSERT INTO users (username, email, password_hash, role, status, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                ('admin', 'admin@example.com', password_hash, 'admin', 'active', datetime.now(), datetime.now())
            )
            
            # 提交更改
            connection.commit()
            
            print("✅ 管理员用户创建成功: admin/admin123")
            
    except Exception as e:
        print(f"❌ 创建管理员用户失败: {e}")
    finally:
        connection.close()

if __name__ == '__main__':
    create_admin_user()