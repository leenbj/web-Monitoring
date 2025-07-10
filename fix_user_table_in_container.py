#!/usr/bin/env python3
"""
在Docker容器内修复用户表结构脚本
添加缺失的字段并迁移现有数据
"""

import pymysql
import os
from datetime import datetime

def fix_user_table_schema():
    """修复用户表结构"""
    try:
        print("🔧 开始修复用户表结构...")
        
        # 连接到MySQL数据库（容器内连接）
        connection = pymysql.connect(
            host='mysql',          # 使用Docker网络中的mysql容器名
            port=3306,             # 容器内部端口
            user='monitor_user',
            password='BaotaUser2024!',
            database='website_monitor',
            charset='utf8mb4'
        )
        
        print("✅ 成功连接到MySQL数据库")
        
        with connection.cursor() as cursor:
            print("📊 检查当前users表结构...")
            
            # 检查表结构
            cursor.execute("DESCRIBE users")
            columns_info = cursor.fetchall()
            columns = [col[0] for col in columns_info]
            print(f"当前字段: {columns}")
            
            # 需要添加的字段
            missing_fields = []
            
            if 'real_name' not in columns:
                missing_fields.append('real_name')
            if 'role' not in columns:
                missing_fields.append('role')
            if 'status' not in columns:
                missing_fields.append('status')
            if 'last_login_at' not in columns:
                missing_fields.append('last_login_at')
            
            print(f"缺失字段: {missing_fields}")
            
            # 执行迁移
            if missing_fields:
                print("🔧 开始添加缺失字段...")
                
                # 添加 real_name 字段
                if 'real_name' in missing_fields:
                    print("添加 real_name 字段...")
                    cursor.execute("ALTER TABLE users ADD COLUMN real_name VARCHAR(100) DEFAULT ''")
                    # 使用 username 作为默认 real_name
                    cursor.execute("UPDATE users SET real_name = username WHERE real_name = '' OR real_name IS NULL")
                    cursor.execute("ALTER TABLE users MODIFY real_name VARCHAR(100) NOT NULL")
                
                # 添加 role 字段并从 is_admin 迁移数据
                if 'role' in missing_fields:
                    print("添加 role 字段...")
                    cursor.execute("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user'")
                    # 从 is_admin 迁移数据
                    cursor.execute("UPDATE users SET role = 'admin' WHERE is_admin = 1")
                    cursor.execute("UPDATE users SET role = 'user' WHERE is_admin = 0")
                    cursor.execute("ALTER TABLE users MODIFY role VARCHAR(20) NOT NULL")
                
                # 添加 status 字段并从 is_active 迁移数据
                if 'status' in missing_fields:
                    print("添加 status 字段...")
                    cursor.execute("ALTER TABLE users ADD COLUMN status VARCHAR(20) DEFAULT 'active'")
                    # 从 is_active 迁移数据
                    cursor.execute("UPDATE users SET status = 'active' WHERE is_active = 1")
                    cursor.execute("UPDATE users SET status = 'inactive' WHERE is_active = 0")
                    cursor.execute("ALTER TABLE users MODIFY status VARCHAR(20) NOT NULL")
                
                # 添加 last_login_at 字段
                if 'last_login_at' in missing_fields:
                    print("添加 last_login_at 字段...")
                    cursor.execute("ALTER TABLE users ADD COLUMN last_login_at DATETIME NULL")
                
                # 提交更改
                connection.commit()
                print("✅ 字段添加完成")
                
                # 验证更新后的表结构
                print("📊 验证更新后的表结构...")
                cursor.execute("DESCRIBE users")
                updated_columns_info = cursor.fetchall()
                updated_columns = [col[0] for col in updated_columns_info]
                print(f"更新后字段: {updated_columns}")
                
                # 显示用户数据
                print("📊 检查用户数据...")
                cursor.execute("SELECT id, username, email, role, status, real_name FROM users")
                users = cursor.fetchall()
                
                for user in users:
                    print(f"   - ID:{user[0]} 用户名:{user[1]} 邮箱:{user[2]} 角色:{user[3]} 状态:{user[4]} 真实姓名:{user[5]}")
                
                print("✅ 用户表结构修复完成!")
                return True
                
            else:
                print("✅ 用户表结构已是最新，无需修复")
                return True
    
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        if 'connection' in locals():
            connection.close()
            print("数据库连接已关闭")


def test_login_after_fix():
    """修复后测试登录"""
    try:
        print(f"\n🔧 测试登录功能...")
        
        import requests
        import json
        
        login_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        
        # 从容器内测试，使用容器的内部端口
        response = requests.post(
            'http://localhost:5000/api/auth/login',  # 容器内部端口
            json=login_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"响应内容: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            if result.get('code') == 200:
                print("✅ 登录测试成功!")
                print(f"用户信息: {result.get('data', {}).get('user', {})}")
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
    print("🚀 Docker容器内用户表结构修复工具")
    print("=" * 60)
    
    # 修复表结构
    if fix_user_table_schema():
        print("\n" + "=" * 60)
        print("🧪 测试登录功能")
        print("=" * 60)
        
        # 测试登录
        test_login_after_fix()
    else:
        print("❌ 表结构修复失败")
        exit(1) 