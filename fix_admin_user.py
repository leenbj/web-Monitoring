#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复管理员用户创建脚本
适配 Docker 环境和应用配置
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

def fix_admin_user():
    """修复管理员用户"""
    try:
        from backend.app import create_app
        from backend.models import User
        from backend.database import get_db
        
        # 创建应用实例
        app = create_app()
        
        with app.app_context():
            with get_db() as db:
                # 删除现有的admin用户
                existing_admin = db.query(User).filter(User.username == 'admin').first()
                if existing_admin:
                    db.delete(existing_admin)
                    db.commit()
                    print("🗑️  已删除现有admin用户")
                
                # 创建新的管理员用户
                admin_user = User(
                    username='admin',
                    email='admin@example.com',
                    role='admin',
                    status='active'
                )
                
                # 设置密码
                admin_user.set_password('admin123')
                
                # 保存到数据库
                db.add(admin_user)
                db.commit()
                
                print("✅ 管理员用户创建成功!")
                print("📋 登录信息:")
                print(f"   用户名: admin")
                print(f"   密码: admin123")
                print(f"   角色: admin")
                print(f"   状态: active")
                
                # 验证密码
                if admin_user.check_password('admin123'):
                    print("🔓 密码验证成功!")
                else:
                    print("❌ 密码验证失败!")
                    
    except Exception as e:
        print(f"❌ 修复管理员用户失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    fix_admin_user()