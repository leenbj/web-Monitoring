#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
容器内运行的登录修复脚本
直接在 Docker 容器内执行
"""

import os
import sys
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_login_in_container():
    """在容器内修复登录问题"""
    try:
        # 设置环境变量
        os.environ['DATABASE_URL'] = 'mysql://webmonitor:webmonitor123@mysql:3306/website_monitor'
        os.environ['FLASK_ENV'] = 'production'
        
        # 导入应用模块
        sys.path.insert(0, '/app')
        from backend.app import create_app
        from backend.models import User
        from backend.database import get_db
        
        logger.info("🔄 开始修复管理员登录问题...")
        
        # 创建应用实例
        app = create_app()
        
        with app.app_context():
            with get_db() as db:
                logger.info("🔍 检查数据库连接...")
                
                # 查询所有用户
                users = db.query(User).all()
                logger.info(f"📊 当前用户数量: {len(users)}")
                
                # 删除现有的admin用户
                existing_admin = db.query(User).filter(User.username == 'admin').first()
                if existing_admin:
                    logger.info("🗑️  发现现有admin用户，正在删除...")
                    db.delete(existing_admin)
                    db.commit()
                    logger.info("✅ 现有admin用户已删除")
                
                # 创建新的管理员用户
                logger.info("👤 创建新的管理员用户...")
                admin_user = User(
                    username='admin',
                    email='admin@example.com',
                    role='admin',
                    status='active'
                )
                
                # 设置密码
                admin_user.set_password('admin123')
                logger.info("🔒 密码设置完成")
                
                # 保存到数据库
                db.add(admin_user)
                db.commit()
                
                logger.info("✅ 管理员用户创建成功!")
                logger.info("📋 登录信息:")
                logger.info(f"   用户名: admin")
                logger.info(f"   密码: admin123")
                logger.info(f"   角色: admin")
                logger.info(f"   状态: active")
                
                # 验证密码
                logger.info("🔍 验证密码...")
                if admin_user.check_password('admin123'):
                    logger.info("✅ 密码验证成功!")
                else:
                    logger.error("❌ 密码验证失败!")
                    return False
                
                # 重新查询验证
                verification_user = db.query(User).filter(User.username == 'admin').first()
                if verification_user and verification_user.check_password('admin123'):
                    logger.info("✅ 最终验证成功：可以使用 admin/admin123 登录!")
                    return True
                else:
                    logger.error("❌ 最终验证失败!")
                    return False
                    
    except Exception as e:
        logger.error(f"❌ 修复登录失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = fix_login_in_container()
    if success:
        print("\n🎉 管理员登录修复完成！现在可以使用 admin/admin123 登录系统。")
    else:
        print("\n❌ 管理员登录修复失败！请检查错误日志。")
        sys.exit(1)