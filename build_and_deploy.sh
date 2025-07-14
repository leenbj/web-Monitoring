#!/bin/bash

# 网址监控系统 - 本地构建和部署脚本
# 用于构建前后端镜像并本地部署

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目信息
PROJECT_NAME="web-monitoring"
BACKEND_IMAGE="web-monitoring-backend:latest"
FRONTEND_IMAGE="web-monitoring-frontend:latest"
BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
VERSION="1.0.0"

# 函数定义
print_step() {
    echo -e "${BLUE}===========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

# 检查必要的工具
check_dependencies() {
    print_step "检查依赖工具"
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装或未在PATH中"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! command -v docker &> /dev/null; then
        print_error "Docker Compose 未安装或未在PATH中"
        exit 1
    fi
    
    print_success "所有依赖工具检查通过"
}

# 清理旧镜像
cleanup_old_images() {
    print_step "清理旧镜像"
    
    if docker images | grep -q "$BACKEND_IMAGE"; then
        print_warning "删除旧的后端镜像..."
        docker rmi "$BACKEND_IMAGE" 2>/dev/null || true
    fi
    
    if docker images | grep -q "$FRONTEND_IMAGE"; then
        print_warning "删除旧的前端镜像..."
        docker rmi "$FRONTEND_IMAGE" 2>/dev/null || true
    fi
    
    # 清理无用的镜像
    docker image prune -f 2>/dev/null || true
    
    print_success "旧镜像清理完成"
}

# 构建后端镜像
build_backend() {
    print_step "构建后端镜像"
    
    echo "构建参数:"
    echo "  - 镜像名称: $BACKEND_IMAGE"
    echo "  - 构建时间: $BUILD_DATE"
    echo "  - 版本: $VERSION"
    
    # 修复 Dockerfile 中的数据库配置
    docker build \
        --build-arg BUILD_DATE="$BUILD_DATE" \
        --build-arg VERSION="$VERSION" \
        --build-arg VCS_REF="$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')" \
        -t "$BACKEND_IMAGE" \
        -f Dockerfile \
        .
    
    if [ $? -eq 0 ]; then
        print_success "后端镜像构建成功"
    else
        print_error "后端镜像构建失败"
        exit 1
    fi
}

# 构建前端镜像
build_frontend() {
    print_step "构建前端镜像"
    
    echo "构建参数:"
    echo "  - 镜像名称: $FRONTEND_IMAGE"
    echo "  - 构建时间: $BUILD_DATE"
    echo "  - 版本: $VERSION"
    
    cd frontend
    
    # 检查是否有 package.json
    if [ ! -f "package.json" ]; then
        print_error "frontend/package.json 文件不存在"
        exit 1
    fi
    
    docker build \
        --build-arg BUILD_DATE="$BUILD_DATE" \
        --build-arg VERSION="$VERSION" \
        --build-arg VCS_REF="$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')" \
        -t "$FRONTEND_IMAGE" \
        -f Dockerfile \
        .
    
    if [ $? -eq 0 ]; then
        print_success "前端镜像构建成功"
    else
        print_error "前端镜像构建失败"
        exit 1
    fi
    
    cd ..
}

# 创建本地部署的 docker-compose 文件
create_local_compose() {
    print_step "创建本地部署配置"
    
    cat > docker-compose.local.yml << 'EOF'
version: '3.8'

services:
  # MySQL 数据库
  mysql:
    image: mysql:8.0
    container_name: webmonitor-mysql-local
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: rootpassword
      MYSQL_DATABASE: website_monitor
      MYSQL_USER: webmonitor
      MYSQL_PASSWORD: webmonitor123
    volumes:
      - mysql_data_local:/var/lib/mysql
      - ./mysql/init:/docker-entrypoint-initdb.d
    ports:
      - "33062:3306"
    networks:
      - webmonitor-local
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      timeout: 20s
      retries: 10

  # Redis 缓存
  redis:
    image: redis:7-alpine
    container_name: webmonitor-redis-local
    restart: unless-stopped
    ports:
      - "63792:6379"
    volumes:
      - redis_data_local:/data
    networks:
      - webmonitor-local
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      timeout: 3s
      retries: 5

  # 后端服务 - 使用本地构建的镜像
  backend:
    image: web-monitoring-backend:latest
    container_name: webmonitor-backend-local
    restart: unless-stopped
    depends_on:
      mysql:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      # 数据库配置
      DATABASE_URL: mysql://webmonitor:webmonitor123@mysql:3306/website_monitor
      MYSQL_HOST: mysql
      MYSQL_PORT: 3306
      MYSQL_USER: webmonitor
      MYSQL_PASSWORD: webmonitor123
      MYSQL_DATABASE: website_monitor
      
      # Redis 配置
      REDIS_HOST: redis
      REDIS_PORT: 6379
      
      # 应用配置
      SECRET_KEY: WebMonitorSecretKey2024LocalBuild
      FLASK_ENV: production
      FLASK_APP: run_backend.py
      
      # 时区设置
      TZ: Asia/Shanghai
    ports:
      - "5013:5000"
    volumes:
      - backend_data_local:/app/backend/logs
      - backend_uploads_local:/app/backend/uploads
      - backend_downloads_local:/app/backend/downloads
      - backend_user_files_local:/app/backend/user_files
      - backend_database_local:/app/database
    networks:
      - webmonitor-local
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 90s

  # 前端服务 - 使用本地构建的镜像
  frontend:
    image: web-monitoring-frontend:latest
    container_name: webmonitor-frontend-local
    restart: unless-stopped
    depends_on:
      - backend
    ports:
      - "8081:80"
    networks:
      - webmonitor-local
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3

# 数据卷
volumes:
  mysql_data_local:
    driver: local
  redis_data_local:
    driver: local
  backend_data_local:
    driver: local
  backend_uploads_local:
    driver: local
  backend_downloads_local:
    driver: local
  backend_user_files_local:
    driver: local
  backend_database_local:
    driver: local

# 网络
networks:
  webmonitor-local:
    driver: bridge
EOF
    
    print_success "本地部署配置文件创建成功"
}

# 启动本地部署
start_local_deployment() {
    print_step "启动本地部署"
    
    # 停止现有服务
    print_warning "停止现有服务..."
    docker-compose -f docker-compose.local.yml down 2>/dev/null || true
    
    # 启动服务
    print_warning "启动新服务..."
    docker-compose -f docker-compose.local.yml up -d
    
    if [ $? -eq 0 ]; then
        print_success "本地部署启动成功"
    else
        print_error "本地部署启动失败"
        exit 1
    fi
}

# 等待服务启动
wait_for_services() {
    print_step "等待服务启动"
    
    echo "等待后端服务启动..."
    local attempt=0
    local max_attempts=60
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -f http://localhost:5013/api/health >/dev/null 2>&1; then
            print_success "后端服务启动成功"
            break
        fi
        attempt=$((attempt + 1))
        echo "等待中... ($attempt/$max_attempts)"
        sleep 5
    done
    
    if [ $attempt -eq $max_attempts ]; then
        print_error "后端服务启动超时"
        docker-compose -f docker-compose.local.yml logs backend
        exit 1
    fi
    
    echo "等待前端服务启动..."
    sleep 10
    
    if curl -f http://localhost:8081/health >/dev/null 2>&1; then
        print_success "前端服务启动成功"
    else
        print_warning "前端服务可能未完全启动，但会继续运行"
    fi
}

# 修复管理员用户
fix_admin_user() {
    print_step "修复管理员用户"
    
    docker-compose -f docker-compose.local.yml exec -T backend python3 -c "
import sys
import os
sys.path.insert(0, '/app')
os.environ['DATABASE_URL'] = 'mysql://webmonitor:webmonitor123@mysql:3306/website_monitor'

from backend.app import create_app
from backend.models import User
from backend.database import get_db

app = create_app()
with app.app_context():
    with get_db() as db:
        # 删除现有admin用户
        existing = db.query(User).filter(User.username == 'admin').first()
        if existing:
            db.delete(existing)
            db.commit()
        
        # 创建新的管理员用户
        admin = User(username='admin', email='admin@example.com', role='admin', status='active')
        admin.set_password('admin123')
        db.add(admin)
        db.commit()
        print('✅ 管理员用户创建成功!')
"
    
    if [ $? -eq 0 ]; then
        print_success "管理员用户修复成功"
    else
        print_error "管理员用户修复失败"
    fi
}

# 显示部署信息
show_deployment_info() {
    print_step "部署信息"
    
    echo "🎉 本地部署完成！"
    echo ""
    echo "📋 服务信息:"
    echo "  - 前端地址: http://localhost:8081"
    echo "  - 后端地址: http://localhost:5013"
    echo "  - MySQL端口: 33062"
    echo "  - Redis端口: 63792"
    echo ""
    echo "🔑 登录信息:"
    echo "  - 用户名: admin"
    echo "  - 密码: admin123"
    echo ""
    echo "🔧 管理命令:"
    echo "  - 查看日志: docker-compose -f docker-compose.local.yml logs -f"
    echo "  - 重启服务: docker-compose -f docker-compose.local.yml restart"
    echo "  - 停止服务: docker-compose -f docker-compose.local.yml down"
    echo "  - 查看状态: docker-compose -f docker-compose.local.yml ps"
}

# 主函数
main() {
    print_step "开始本地构建和部署"
    
    check_dependencies
    cleanup_old_images
    build_backend
    build_frontend
    create_local_compose
    start_local_deployment
    wait_for_services
    fix_admin_user
    show_deployment_info
    
    print_success "本地构建和部署完成！"
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi