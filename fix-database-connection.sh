#!/bin/bash
# 云端服务器 - 修复Docker容器数据库连接问题

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo "============================================="
echo "    修复Docker容器数据库连接问题"
echo "============================================="
echo "修复时间: $(date)"
echo ""

# 1. 检查当前网络配置
info "1. 检查Docker网络配置..."
docker network ls
echo ""

# 获取宿主机IP地址
HOST_IP=$(ip route show default | awk '/default/ {print $3}')
DOCKER_GATEWAY=$(docker network inspect bridge | grep -i gateway | awk -F'"' '{print $4}' | head -1)

info "宿主机默认网关: $HOST_IP"
info "Docker网关地址: $DOCKER_GATEWAY"
echo ""

# 2. 检查MySQL在宿主机上的监听状态
info "2. 检查MySQL监听状态..."
netstat -tlnp | grep :3306 || warning "MySQL可能未在3306端口监听"
echo ""

# 3. 创建修复后的环境配置
info "3. 创建修复后的环境配置..."
cat > .env.baota << EOF
# 网址监控系统 - 宝塔面板部署环境配置

# 数据库配置 - 使用Docker网关地址访问宿主机MySQL
MYSQL_HOST=$DOCKER_GATEWAY
MYSQL_PORT=3306
MYSQL_DATABASE=website_monitor
MYSQL_USER=monitor_user
MYSQL_PASSWORD=BaotaUser2024!

# 安全配置
SECRET_KEY=WebMonitorBaotaSecretKey2024ChangeMe
JWT_SECRET_KEY=JWTBaotaSecretKey2024ChangeMe

# 应用配置
FLASK_ENV=production
PORT=5011
DEBUG=false
LOG_LEVEL=INFO

# 检测配置
DEFAULT_TIMEOUT=30
DEFAULT_RETRY_TIMES=3
DEFAULT_MAX_CONCURRENT=20
DEFAULT_INTERVAL_HOURS=6

# 性能配置
WORKERS=2
THREADS=4
TIMEOUT=120
MAX_MEMORY_MB=512

# 域名配置
FRONTEND_DOMAIN=w4.799n.com
API_DOMAIN=w4.799n.com

# 时区
TZ=Asia/Shanghai
EOF

success "环境配置文件已更新"
echo ""

# 4. 创建修复后的docker-compose配置
info "4. 创建修复后的docker-compose配置..."
cat > docker-compose.baota.yml << EOF
version: '3.8'

# 网址监控系统 - 宝塔面板部署版本
name: website-monitor-baota

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.baota
    container_name: website-monitor-backend
    restart: unless-stopped
    ports:
      - "5011:5011"
    env_file:
      - .env.baota
    environment:
      # 数据库配置 - 使用Docker网关访问宿主机MySQL
      - MYSQL_HOST=$DOCKER_GATEWAY
      - MYSQL_PORT=3306
      - MYSQL_DATABASE=website_monitor
      - MYSQL_USER=monitor_user
      - MYSQL_PASSWORD=BaotaUser2024!
      
      # Flask配置
      - SECRET_KEY=WebMonitorBaotaSecretKey2024ChangeMe
      - JWT_SECRET_KEY=JWTBaotaSecretKey2024ChangeMe
      - FLASK_ENV=production
      - PORT=5011
      - DEBUG=false
      - LOG_LEVEL=INFO
      
      # 应用配置
      - PYTHONPATH=/app
      - PYTHONUNBUFFERED=1
      - PYTHONDONTWRITEBYTECODE=1
      - TZ=Asia/Shanghai
      
      # 性能配置
      - WORKERS=2
      - THREADS=4
      - TIMEOUT=120
      - MAX_MEMORY_MB=512
      
      # 检测配置
      - DEFAULT_TIMEOUT=30
      - DEFAULT_RETRY_TIMES=3
      - DEFAULT_MAX_CONCURRENT=20
      - DEFAULT_INTERVAL_HOURS=6
      
      # 文件配置
      - MAX_CONTENT_LENGTH=16777216
      - UPLOAD_FOLDER=/app/uploads
      - DOWNLOAD_FOLDER=/app/downloads
      
      # 域名配置
      - FRONTEND_DOMAIN=w4.799n.com
      - API_DOMAIN=w4.799n.com
      
    volumes:
      - ./database:/app/database
      - ./logs:/app/logs
      - ./uploads:/app/uploads
      - ./downloads:/app/downloads
      - ./user_files:/app/user_files
      
    # 添加宿主机访问配置
    extra_hosts:
      - "host.docker.internal:$DOCKER_GATEWAY"
      
    # 健康检查
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5011/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
EOF

success "Docker配置文件已更新"
echo ""

# 5. 测试数据库连接
info "5. 测试数据库连接..."
if command -v mysql >/dev/null 2>&1; then
    info "使用新的数据库地址测试连接: $DOCKER_GATEWAY"
    if mysql -h"$DOCKER_GATEWAY" -umonitor_user -pBaotaUser2024! -e "USE website_monitor;" 2>/dev/null; then
        success "数据库连接测试通过"
    else
        error "数据库连接失败"
        info "可能需要在宝塔面板中："
        echo "1. 创建数据库: website_monitor"
        echo "2. 创建用户: monitor_user"
        echo "3. 设置密码: BaotaUser2024!"
        echo "4. 授予所有权限"
        echo "5. 允许远程连接 (%) 或具体IP ($DOCKER_GATEWAY)"
    fi
else
    warning "mysql客户端不可用，跳过连接测试"
fi
echo ""

# 6. 停止当前容器
info "6. 停止当前容器..."
docker stop website-monitor-backend 2>/dev/null || true
docker rm website-monitor-backend 2>/dev/null || true
success "容器已停止"
echo ""

# 7. 重新构建和启动
info "7. 重新构建和启动容器..."
docker-compose -f docker-compose.baota.yml build --no-cache
docker-compose -f docker-compose.baota.yml up -d

# 等待容器启动
sleep 10

# 8. 验证容器状态
info "8. 验证容器状态..."
CONTAINER_STATUS=$(docker ps --format "table {{.Names}}\t{{.Status}}" | grep website-monitor-backend)
if [ -n "$CONTAINER_STATUS" ]; then
    success "容器启动成功"
    echo "$CONTAINER_STATUS"
else
    error "容器启动失败"
    info "检查容器日志..."
    docker logs website-monitor-backend --tail 20
    exit 1
fi
echo ""

# 9. 健康检查
info "9. 进行健康检查..."
for i in {1..12}; do
    if curl -s http://localhost:5011/api/health >/dev/null 2>&1; then
        success "健康检查通过"
        HEALTH_RESPONSE=$(curl -s http://localhost:5011/api/health)
        info "健康检查响应: $HEALTH_RESPONSE"
        break
    else
        warning "健康检查失败，等待服务启动 ($i/12)..."
        sleep 5
    fi
    
    if [ $i -eq 12 ]; then
        error "健康检查超时失败"
        info "容器详细日志:"
        docker logs website-monitor-backend --tail 50
        exit 1
    fi
done

echo ""
echo "============================================="
echo "           修复完成"
echo "============================================="
success "Docker容器数据库连接问题已修复！"
echo ""
echo "关键修复内容:"
echo "1. 数据库地址: localhost → $DOCKER_GATEWAY"
echo "2. 容器网络: 添加 extra_hosts 配置"
echo "3. 端口映射: 5011:5011"
echo ""
echo "容器状态:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep website-monitor-backend
echo ""
echo "端口监听:"
netstat -tlnp | grep :5011
echo ""
echo "下一步:"
echo "1. 确认宝塔面板中MySQL用户权限"
echo "2. 配置nginx反向代理"
echo "3. 上传前端静态文件"
echo ""
echo "完成时间: $(date)"
echo "============================================="