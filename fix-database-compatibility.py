#!/usr/bin/env python3
"""
数据库兼容性修复测试脚本
测试PyMySQL连接是否正常工作
"""

import sys
import os
sys.path.append('/app')

def test_database_connection():
    """测试数据库连接"""
    try:
        print("🔧 开始测试数据库连接兼容性...")
        
        # 导入应用
        from backend.app import create_app
        from backend.database import get_db
        from sqlalchemy import text
        
        print("✅ 成功导入应用模块")
        
        # 创建应用
        app = create_app()
        
        with app.app_context():
            print("✅ Flask应用上下文创建成功")
            
            # 测试数据库连接
            with get_db() as db:
                result = db.execute(text('SELECT 1 as test'))
                test_value = result.fetchone()[0]
                
                if test_value == 1:
                    print("✅ 数据库连接测试成功")
                    return True
                else:
                    print("❌ 数据库连接测试返回值异常")
                    return False
                    
    except Exception as e:
        print(f"❌ 数据库连接测试失败: {e}")
        return False

def test_auth_functionality():
    """测试认证功能"""
    try:
        print("🔧 开始测试用户认证功能...")
        
        from backend.app import create_app
        from backend.database import get_db
        from backend.models import User
        
        app = create_app()
        
        with app.app_context():
            # 尝试查询用户
            with get_db() as db:
                user_count = db.query(User).count()
                print(f"✅ 用户查询成功，当前用户数: {user_count}")
                return True
                
    except Exception as e:
        print(f"❌ 认证功能测试失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("  数据库兼容性修复验证")
    print("=" * 50)
    
    # 测试数据库连接
    db_success = test_database_connection()
    
    # 测试认证功能
    auth_success = test_auth_functionality()
    
    print("\n" + "=" * 50)
    print("  修复验证结果")
    print("=" * 50)
    print(f"数据库连接: {'✅ 通过' if db_success else '❌ 失败'}")
    print(f"用户认证: {'✅ 通过' if auth_success else '❌ 失败'}")
    
    if db_success and auth_success:
        print("\n🎉 兼容性修复成功！")
        return 0
    else:
        print("\n💥 兼容性修复失败，需要进一步检查")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 