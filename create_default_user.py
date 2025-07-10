#!/usr/bin/env python3
"""
创建默认用户脚本
用于检查和创建系统默认管理员用户
"""

import sys
import os
sys.path.append('/app')
sys.path.append('.')

def create_default_user():
    """创建默认用户"""
    try:
        print("🔧 开始检查和创建默认用户...")
        
        # 导入必要模块
        from backend.app import create_app
        from backend.database import get_db
        from backend.models import User
        from datetime import datetime
        
        print("✅ 成功导入应用模块")
        
        # 创建应用
        app = create_app()
        
        with app.app_context():
            print("✅ Flask应用上下文创建成功")
            
            # 检查现有用户
            with get_db() as db:
                existing_users = db.query(User).all()
                print(f"📊 当前用户数量: {len(existing_users)}")
                
                for user in existing_users:
                    print(f"   - {user.username} ({user.role}) - {user.status}")
                
                # 检查是否已有管理员用户
                admin_user = db.query(User).filter(User.role == 'admin').first()
                
                if admin_user:
                    print(f"✅ 管理员用户已存在: {admin_user.username}")
                    
                    # 测试密码
                    test_passwords = ['admin123', '123456', 'admin', 'password']
                    for pwd in test_passwords:
                        if admin_user.check_password(pwd):
                            print(f"✅ 管理员密码验证成功: {pwd}")
                            return admin_user.username, pwd
                    
                    print("❌ 无法验证管理员密码，将重置为: admin123")
                    admin_user.set_password('admin123')
                    db.commit()
                    print("✅ 管理员密码已重置为: admin123")
                    return admin_user.username, 'admin123'
                
                else:
                    print("❌ 未找到管理员用户，创建默认管理员...")
                    
                    # 创建默认管理员用户
                    new_admin = User(
                        username='admin',
                        email='admin@localhost.com',
                        real_name='系统管理员',
                        role='admin',
                        status='active'
                    )
                    new_admin.set_password('admin123')
                    
                    db.add(new_admin)
                    db.commit()
                    db.refresh(new_admin)
                    
                    print(f"✅ 默认管理员用户创建成功:")
                    print(f"   用户名: admin")
                    print(f"   密码: admin123")
                    print(f"   邮箱: admin@localhost.com")
                    
                    return 'admin', 'admin123'
                    
    except Exception as e:
        print(f"❌ 操作失败: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def test_login(username, password):
    """测试登录"""
    try:
        print(f"\n🔧 测试用户登录: {username}")
        
        import requests
        import json
        
        login_data = {
            'username': username,
            'password': password
        }
        
        response = requests.post(
            'http://localhost:15000/api/auth/login',
            json=login_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 200:
                print("✅ 登录测试成功!")
                return True
            else:
                print(f"❌ 登录失败: {result.get('message')}")
                return False
        else:
            print(f"❌ HTTP请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 登录测试失败: {e}")
        return False


if __name__ == '__main__':
    print("=" * 50)
    print("🚀 默认用户创建和验证工具")
    print("=" * 50)
    
    # 创建或检查默认用户
    username, password = create_default_user()
    
    if username and password:
        print(f"\n📋 登录信息:")
        print(f"   用户名: {username}")
        print(f"   密码: {password}")
        
        # 测试登录
        test_login(username, password)
    else:
        print("❌ 无法创建或验证默认用户")
        sys.exit(1) 