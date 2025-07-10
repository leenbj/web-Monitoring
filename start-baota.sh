#\!/bin/bash
set -e

echo "=== 网址监控系统 - 宝塔部署版本 ==="
echo "启动时间: $(date)"
echo "Python版本: $(python --version)"

# 设置默认环境变量
export SECRET_KEY="${SECRET_KEY:-WebMonitorBaotaSecretKey2024}"
export JWT_SECRET_KEY="${JWT_SECRET_KEY:-JWTBaotaSecretKey2024}"

# 等待MySQL连接
echo "检查MySQL数据库连接..."
if [ \! -z "$MYSQL_HOST" ]; then
    max_attempts=30
    attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if nc -z $MYSQL_HOST 3306 2>/dev/null; then
            echo "MySQL数据库连接成功"
            break
        fi
        attempt=$((attempt + 1))
        echo "等待MySQL连接... ($attempt/$max_attempts)"
        sleep 2
    done
    
    if [ $attempt -eq $max_attempts ]; then
        echo "错误: MySQL数据库连接超时"
        exit 1
    fi
fi

# 设置数据库连接
if [ \! -z "$MYSQL_HOST" ] && [ \! -z "$MYSQL_USER" ] && [ \! -z "$MYSQL_PASSWORD" ] && [ \! -z "$MYSQL_DATABASE" ]; then
    export DATABASE_URL="mysql+pymysql://$MYSQL_USER:$MYSQL_PASSWORD@$MYSQL_HOST:3306/$MYSQL_DATABASE?charset=utf8mb4"
    echo "使用MySQL数据库: $MYSQL_HOST/$MYSQL_DATABASE"
else
    echo "使用SQLite数据库"
    export DATABASE_URL="sqlite:////app/database/website_monitor.db"
fi

# 初始化数据库（如果需要）
echo "初始化数据库..."
python init_database.py || echo "数据库初始化跳过"

# 测试数据库连接
echo "测试数据库连接..."
python -c "
import sys
sys.path.append('/app')
try:
    from backend.database import get_db
    with get_db() as db:
        result = db.execute('SELECT 1').fetchone()
        print('数据库连接测试成功')
except Exception as e:
    print(f'数据库连接失败: {e}')
    sys.exit(1)
"

# 设置文件权限
chmod -R 755 /app/logs /app/uploads /app/downloads /app/user_files /app/database

# 启动应用
echo "启动网址监控后端服务 (端口: $PORT)..."
echo "健康检查: http://localhost:$PORT/api/health"
exec python run_backend.py
EOF < /dev/null