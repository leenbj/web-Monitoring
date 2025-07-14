#!/bin/bash

# 修复管理员登录问题的脚本
# 适用于 Docker 部署后的环境

echo "🔧 开始修复管理员登录问题..."

# 检查 Docker 容器状态
echo "📋 检查容器状态..."
docker compose ps

# 检查数据库连接
echo "🔍 检查数据库连接..."
docker compose exec mysql mysqladmin ping -h localhost -u webmonitor -pwebmonitor123

# 在后端容器内执行修复脚本
echo "🔄 在后端容器内执行管理员用户修复..."
docker compose exec backend python3 -c "
import sys
import os
sys.path.insert(0, '/app')

# 设置环境变量
os.environ['DATABASE_URL'] = 'mysql://webmonitor:webmonitor123@mysql:3306/website_monitor'
os.environ['FLASK_ENV'] = 'production'

from backend.app import create_app
from backend.models import User
from backend.database import get_db

print('🔄 正在修复管理员用户...')

app = create_app()
with app.app_context():
    with get_db() as db:
        # 删除现有admin用户
        existing_admin = db.query(User).filter(User.username == 'admin').first()
        if existing_admin:
            db.delete(existing_admin)
            db.commit()
            print('🗑️  已删除现有admin用户')
        
        # 创建新的管理员用户
        admin_user = User(
            username='admin',
            email='admin@example.com',
            role='admin',
            status='active'
        )
        admin_user.set_password('admin123')
        
        db.add(admin_user)
        db.commit()
        
        print('✅ 管理员用户创建成功!')
        print('📋 登录信息:')
        print('   用户名: admin')
        print('   密码: admin123')
        
        # 验证密码
        if admin_user.check_password('admin123'):
            print('✅ 密码验证成功!')
        else:
            print('❌ 密码验证失败!')
"

# 重启后端容器以确保更改生效
echo "🔄 重启后端容器..."
docker compose restart backend

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务健康状态
echo "🏥 检查服务健康状态..."
docker compose exec backend curl -f http://localhost:5000/api/health || echo "❌ 健康检查失败"

echo "✅ 管理员登录修复完成！"
echo "🎉 现在可以使用以下信息登录:"
echo "   用户名: admin"
echo "   密码: admin123"
echo "   前端地址: http://localhost:8080"
echo "   后端地址: http://localhost:5012"