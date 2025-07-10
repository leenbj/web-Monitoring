#!/usr/bin/env python3
"""
重置admin用户密码脚本
"""

import pymysql
from werkzeug.security import generate_password_hash

def reset_admin_password():
    """重置admin用户密码"""
    try:
        print("🔧 开始重置admin用户密码...")
        
        # 连接到MySQL数据库（容器内连接）
        connection = pymysql.connect(
            host='mysql',
            port=3306,
            user='monitor_user',
            password='BaotaUser2024!',
            database='website_monitor',
            charset='utf8mb4'
        )
        
        print("✅ 成功连接到MySQL数据库")
        
        with connection.cursor() as cursor:
            # 生成新密码的哈希值
            new_password = 'admin123'
            password_hash = generate_password_hash(new_password)
            
            print(f"🔑 新密码: {new_password}")
            print(f"🔒 密码哈希: {password_hash[:50]}...")
            
            # 更新admin用户密码
            cursor.execute(
                "UPDATE users SET password_hash = %s WHERE username = 'admin'",
                (password_hash,)
            )
            
            # 检查更新是否成功
            if cursor.rowcount > 0:
                connection.commit()
                print("✅ admin用户密码重置成功!")
                
                # 验证用户信息
                cursor.execute("SELECT id, username, email, role, status FROM users WHERE username = 'admin'")
                user = cursor.fetchone()
                
                if user:
                    print(f"📊 用户信息:")
                    print(f"   ID: {user[0]}")
                    print(f"   用户名: {user[1]}")
                    print(f"   邮箱: {user[2]}")
                    print(f"   角色: {user[3]}")
                    print(f"   状态: {user[4]}")
                
                return True
            else:
                print("❌ 未找到admin用户")
                return False
    
    except Exception as e:
        print(f"❌ 重置失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        if 'connection' in locals():
            connection.close()
            print("数据库连接已关闭")


def test_login():
    """测试登录"""
    try:
        print(f"\n🔧 测试admin用户登录...")
        
        import requests
        import json
        
        login_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        
        # 从容器内测试
        response = requests.post(
            'http://localhost:5000/api/auth/login',
            json=login_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"响应内容: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            if result.get('code') == 200:
                print("✅ 登录测试成功!")
                user_info = result.get('data', {}).get('user', {})
                print(f"📊 登录用户信息:")
                print(f"   用户名: {user_info.get('username')}")
                print(f"   邮箱: {user_info.get('email')}")
                print(f"   角色: {user_info.get('role')}")
                print(f"   状态: {user_info.get('status')}")
                return True
            else:
                print(f"❌ 登录失败: {result.get('message')}")
                return False
        else:
            print(f"❌ HTTP请求失败: {response.status_code}")
            print(f"错误内容: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 登录测试失败: {e}")
        return False


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 重置admin用户密码工具")
    print("=" * 60)
    
    # 重置密码
    if reset_admin_password():
        print("\n" + "=" * 60)
        print("🧪 测试登录功能")
        print("=" * 60)
        
        # 测试登录
        test_login()
    else:
        print("❌ 密码重置失败")
        exit(1) 