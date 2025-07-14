#!/bin/bash

# 一键修复管理员登录问题
# 使用方法: bash quick_fix_admin.sh

echo "🔧 一键修复管理员登录问题..."

# 检查是否在项目根目录
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ 请在项目根目录运行此脚本"
    exit 1
fi

# 检查容器是否运行
if ! docker compose ps | grep -q "backend"; then
    echo "❌ 后端容器未运行，请先启动: docker compose up -d"
    exit 1
fi

echo "🔄 正在修复管理员用户..."

# 在后端容器内执行修复
docker compose exec backend python3 -c "
import sys
import os

# 设置环境变量
os.environ['DATABASE_URL'] = 'mysql://webmonitor:webmonitor123@mysql:3306/website_monitor'
os.environ['FLASK_ENV'] = 'production'

# 设置路径
sys.path.insert(0, '/app')

try:
    from backend.app import create_app
    from backend.models import User
    from backend.database import get_db
    
    print('🔄 开始修复...')
    
    app = create_app()
    with app.app_context():
        with get_db() as db:
            # 删除现有admin用户
            existing = db.query(User).filter(User.username == 'admin').first()
            if existing:
                db.delete(existing)
                db.commit()
                print('🗑️  已删除现有admin用户')
            
            # 创建新的管理员用户
            admin = User(
                username='admin',
                email='admin@example.com',
                role='admin',
                status='active'
            )
            admin.set_password('admin123')
            
            db.add(admin)
            db.commit()
            
            print('✅ 管理员用户创建成功!')
            print('📋 登录信息:')
            print('   用户名: admin')
            print('   密码: admin123')
            
            # 验证密码
            if admin.check_password('admin123'):
                print('✅ 密码验证成功!')
            else:
                print('❌ 密码验证失败!')
                exit(1)
                
except Exception as e:
    print(f'❌ 修复失败: {e}')
    import traceback
    traceback.print_exc()
    exit(1)
"

# 检查执行结果
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 修复完成！"
    echo "🌐 现在可以使用以下信息登录:"
    echo "   用户名: admin"
    echo "   密码: admin123"
    echo "   前端地址: http://localhost:8080"
    echo "   后端地址: http://localhost:5012"
else
    echo ""
    echo "❌ 修复失败！请检查错误信息"
    exit 1
fi