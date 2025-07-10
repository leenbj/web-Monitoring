#\!/bin/bash

# 简单修复脚本 - 创建环境配置文件

echo "🔧 创建环境配置文件..."

# 创建 .env.baota 文件
cat > .env.baota << 'ENVEOF'
# 网址监控系统 - 宝塔面板环境配置
FLASK_ENV=production
SECRET_KEY=BaotaWebMonitorSecretKey2024
LOG_LEVEL=INFO
TZ=Asia/Shanghai
BAOTA_PANEL=true
DOMAIN=w3.799n.com

# MySQL配置
MYSQL_ROOT_PASSWORD=BaotaMonitor2024\!
MYSQL_PASSWORD=BaotaUser2024\!
MYSQL_PORT=13306

# Redis配置
REDIS_PASSWORD=BaotaRedis2024\!
REDIS_PORT=16379

# 服务端口配置
BACKEND_PORT=15000
FRONTEND_PORT=10080
FRONTEND_SSL_PORT=10443

# 邮件配置
MAIL_SERVER=smtp.qq.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_DEFAULT_SENDER=

# 网络配置
NETWORK_SUBNET=172.22.0.0/16
NETWORK_GATEWAY=172.22.0.1
DATA_DIR=./data

# API配置
API_BASE_URL=http://w3.799n.com:15000

# 安全配置
JWT_SECRET_KEY=BaotaWebMonitorSecretKey2024
JWT_ACCESS_TOKEN_EXPIRES=3600
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax

# 监控配置
DETECTION_TIMEOUT=30
DETECTION_RETRY_TIMES=3
DETECTION_MAX_CONCURRENT=10
DATA_RETENTION_DAYS=90
LOG_RETENTION_DAYS=30

# 宝塔面板配置
BAOTA_PATH=/www/server/panel
BAOTA_USER=www
BAOTA_GROUP=www
BAOTA_LOG_PATH=/www/wwwlogs

# 性能优化配置
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
DEBUG=False
SQLALCHEMY_ECHO=False
MYSQL_INNODB_BUFFER_POOL_SIZE=128M
REDIS_MAXMEMORY=128mb
ENVEOF

echo "✅ 已创建 .env.baota 文件"

# 复制为其他需要的文件
cp .env.baota .env.example
cp .env.baota .env

echo "✅ 已创建 .env.example 和 .env 文件"

# 创建必要目录
mkdir -p backend/logs backend/uploads backend/downloads backend/user_files
mkdir -p database mysql/init mysql/conf mysql/data mysql/logs
mkdir -p nginx/logs data/mysql data/redis logs

echo "✅ 已创建必要目录"

# 设置权限
chmod -R 755 backend database mysql nginx data logs 2>/dev/null || true
chmod +x *.sh 2>/dev/null || true

echo "✅ 已设置权限"

echo ""
echo "🎉 修复完成！现在可以运行部署脚本："
echo "   ./deploy-docker-baota.sh"
echo ""
