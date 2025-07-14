#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复的管理员用户创建脚本
解决数据库会话管理和环境配置问题
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

def create_admin_user():
    """创建管理员用户 - 修复版本"""
    try:
        # 确保环境变量设置正确
        if not os.environ.get('DATABASE_URL'):
            # 设置默认的 Docker 环境数据库连接
            os.environ['DATABASE_URL'] = 'mysql://webmonitor:webmonitor123@localhost:33061/website_monitor'
        
        from backend.app import create_app
        from backend.models import User
        from backend.database import get_db
        
        # 创建应用实例
        app = create_app()
        
        print("🔄 正在创建管理员用户...")
        
        with app.app_context():
            with get_db() as db:
                # 检查数据库连接
                print("🔍 检查数据库连接...")
                
                # 删除现有的admin用户
                existing_admin = db.query(User).filter(User.username == 'admin').first()
                if existing_admin:
                    print("🗑️  发现现有admin用户，正在删除...")
                    db.delete(existing_admin)
                    db.commit()
                    print("✅ 现有admin用户已删除")
                
                # 创建新的管理员用户
                print("👤 创建新的管理员用户...")
                admin_user = User(
                    username='admin',
                    email='admin@example.com',
                    role='admin',
                    status='active'
                )
                
                # 设置密码
                admin_user.set_password('admin123')
                print("🔒 密码设置完成")
                
                # 保存到数据库
                db.add(admin_user)
                db.commit()
                
                print("✅ 管理员用户创建成功!")
                print("📋 登录信息:")
                print(f"   用户名: admin")
                print(f"   密码: admin123")
                print(f"   角色: admin")
                print(f"   状态: active")
                print(f"   邮箱: admin@example.com")
                
                # 验证密码
                print("🔍 验证密码...")
                if admin_user.check_password('admin123'):
                    print("✅ 密码验证成功!")
                else:
                    print("❌ 密码验证失败!")
                    return False
                
                # 重新从数据库查询验证
                print("🔍 从数据库重新查询验证...")
                verification_user = db.query(User).filter(User.username == 'admin').first()
                if verification_user:
                    print(f"✅ 用户查询成功: {verification_user.username}")
                    print(f"   - 角色: {verification_user.role}")
                    print(f"   - 状态: {verification_user.status}")
                    print(f"   - 邮箱: {verification_user.email}")
                    
                    # 验证密码
                    if verification_user.check_password('admin123'):
                        print("✅ 最终验证成功：可以使用 admin/admin123 登录!")
                        return True
                    else:
                        print("❌ 最终验证失败：密码验证错误!")
                        return False
                else:
                    print("❌ 用户查询失败：用户不存在!")
                    return False
                    
    except Exception as e:
        print(f"❌ 创建管理员用户失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = create_admin_user()
    if success:
        print("\n🎉 管理员用户创建完成！现在可以使用 admin/admin123 登录系统。")
    else:
        print("\n❌ 管理员用户创建失败！请检查数据库连接和配置。")
        sys.exit(1)