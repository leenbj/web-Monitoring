#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库用户表更新脚本
移除real_name字段，修复数据库结构
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

def update_user_table():
    """更新用户表结构"""
    try:
        from backend.database import get_db
        
        with get_db() as db:
            # 检查是否存在users表
            result = db.execute(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'website_monitor' AND table_name = 'users'"
            ).fetchone()
            
            if result[0] == 0:
                print("用户表不存在，跳过更新")
                return
            
            # 检查是否存在real_name字段
            result = db.execute(
                "SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = 'website_monitor' AND table_name = 'users' AND column_name = 'real_name'"
            ).fetchone()
            
            if result[0] > 0:
                print("发现real_name字段，准备删除...")
                
                # 删除real_name字段
                db.execute("ALTER TABLE website_monitor.users DROP COLUMN real_name")
                print("✅ 已删除real_name字段")
            else:
                print("real_name字段不存在，无需删除")
            
            # 检查是否存在管理员用户
            result = db.execute(
                "SELECT COUNT(*) FROM website_monitor.users WHERE username = 'admin'"
            ).fetchone()
            
            if result[0] == 0:
                print("准备创建管理员用户...")
                
                # 生成密码哈希
                from werkzeug.security import generate_password_hash
                password_hash = generate_password_hash('admin123')
                
                # 创建管理员用户
                db.execute(
                    "INSERT INTO website_monitor.users (username, email, password_hash, role, status, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, NOW(), NOW())",
                    ('admin', 'admin@example.com', password_hash, 'admin', 'active')
                )
                print("✅ 管理员用户创建成功: admin/admin123")
            else:
                print("管理员用户已存在")
                
        print("✅ 用户表更新完成")
        
    except Exception as e:
        print(f"❌ 用户表更新失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    update_user_table()