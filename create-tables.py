#!/usr/bin/env python3
"""
数据库表创建脚本
"""

import os
import sys

# 添加项目路径
sys.path.append('/app')
sys.path.append('.')

def create_tables():
    """创建数据库表"""
    try:
        print("🔧 开始创建数据库表...")
        
        # 导入必要模块
        from backend.app import create_app
        from backend.models import db
        from sqlalchemy import text
        
        # 创建应用
        app = create_app()
        
        with app.app_context():
            print("✅ Flask应用上下文创建成功")
            
            # 创建所有表
            print("📊 创建数据库表...")
            db.create_all()
            
            # 检查创建的表
            result = db.session.execute(text('SHOW TABLES'))
            tables = [row[0] for row in result.fetchall()]
            
            print(f"✅ 数据库表创建成功")
            print(f"创建的表: {tables}")
            
            # 检查必需的表
            required_tables = [
                'users', 'websites', 'website_groups', 
                'detection_tasks', 'detection_records',
                'user_files', 'upload_records', 'system_settings'
            ]
            
            missing_tables = [t for t in required_tables if t not in tables]
            if missing_tables:
                print(f"⚠️  缺少表: {missing_tables}")
            else:
                print("✅ 所有必需表都已创建")
            
            return True
            
    except Exception as e:
        print(f"❌ 数据库表创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("🗄️  数据库表创建工具")
    print("=" * 50)
    
    if create_tables():
        print("\n🎉 数据库表创建完成！")
        return 0
    else:
        print("\n💥 数据库表创建失败")
        return 1

if __name__ == '__main__':
    sys.exit(main())