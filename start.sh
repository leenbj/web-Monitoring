#!/bin/bash
set -e

echo "=== 网址监控系统后端启动 ==="
echo "启动时间: $(date)"
echo "环境: ${FLASK_ENV:-production}"
echo "Python版本: $(python --version)"
echo "构建平台: ${BUILDPLATFORM:-unknown}"
echo "目标平台: ${TARGETPLATFORM:-unknown}"
echo "版本: ${VERSION:-dev}"

# 检查必要的环境变量
if [ -z "$SECRET_KEY" ]; then
    echo "警告: SECRET_KEY 未设置，使用默认值"
    export SECRET_KEY="WebMonitorSecretKey2024ChangeMeInProduction"
fi

# 等待MySQL数据库连接
echo "等待MySQL数据库连接..."
max_attempts=60
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if nc -z mysql 3306 2>/dev/null; then
        echo "MySQL数据库连接成功"
        break
    fi
    attempt=$((attempt + 1))
    echo "等待MySQL连接... ($attempt/$max_attempts)"
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "MySQL数据库连接超时，使用SQLite备用方案"
    export DATABASE_URL="sqlite:///app/database/website_monitor.db"
fi

# 等待Redis连接
echo "等待Redis缓存连接..."
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if nc -z redis 6379 2>/dev/null; then
        echo "Redis缓存连接成功"
        break
    fi
    attempt=$((attempt + 1))
    echo "等待Redis连接... ($attempt/$max_attempts)"
    sleep 1
done

if [ $attempt -eq $max_attempts ]; then
    echo "Redis连接超时，继续启动（功能可能受限）"
fi

# 初始化数据库
echo "初始化数据库..."
python init_database.py || echo "数据库初始化跳过（可能已存在）"

# 检查数据库连接
echo "检查数据库连接..."
python -c "
import sys
sys.path.append('/app')
try:
    from backend.database import get_db
    db = get_db()
    print('数据库连接测试成功')
except Exception as e:
    print(f'数据库连接测试失败: {e}')
    sys.exit(1)
" || {
    echo "数据库连接失败，退出启动"
    exit 1
}

# 设置文件权限
chmod -R 755 /app/backend/logs /app/backend/uploads /app/backend/downloads /app/backend/user_files /app/database

# 启动应用
echo "启动后端服务 (端口: 5000)..."
echo "健康检查地址: http://localhost:5000/api/health"
exec python run_backend.py 