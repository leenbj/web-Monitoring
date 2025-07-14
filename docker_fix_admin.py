#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Docker 容器内修复管理员用户脚本
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

def docker_fix_admin():
    """在 Docker 容器内修复管理员用户"""
    try:
        # 设置环境变量以匹配 Docker 配置
        os.environ['DATABASE_URL'] = 'mysql://webmonitor:webmonitor123@mysql:3306/website_monitor'
        os.environ['FLASK_ENV'] = 'production'
        
        from backend.app import create_app
        from backend.models import User
        from backend.database import get_db
        
        # 创建应用实例
        app = create_app()
        
        with app.app_context():
            try:
                with get_db() as db:
                    # 检查数据库连接
                    print("🔍 检查数据库连接...")
                    
                    # 查询现有用户
                    existing_users = db.query(User).all()
                    print(f"📊 当前用户数量: {len(existing_users)}")
                    
                    for user in existing_users:
                        print(f"   - 用户: {user.username}, 角色: {user.role}, 状态: {user.status}")
                    
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
                        
                    # 再次查询验证
                    verification_user = db.query(User).filter(User.username == 'admin').first()
                    if verification_user:
                        print(f"🔍 验证查询: 用户 {verification_user.username} 存在")
                        print(f"   - 密码哈希: {verification_user.password_hash[:20]}...")
                        if verification_user.check_password('admin123'):
                            print("✅ 验证成功：密码正确!")
                        else:
                            print("❌ 验证失败：密码错误!")
                    else:
                        print("❌ 验证失败：用户不存在!")
                        
            except Exception as db_error:
                print(f"❌ 数据库操作失败: {db_error}")
                import traceback
                traceback.print_exc()
                
    except Exception as e:
        print(f"❌ 修复管理员用户失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    docker_fix_admin()