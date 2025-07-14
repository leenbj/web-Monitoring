#!/bin/bash

# 网址监控系统 - 部署修复脚本
# 修复Docker镜像地址问题

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示修复信息
show_fix_info() {
    echo "=========================================="
    echo "    🔧 Docker镜像地址修复"
    echo "=========================================="
    echo "原镜像: ghcr.io/yourusername/website-monitor/backend"
    echo "新镜像: leenbj68719929/website-monitor-backend"
    echo "=========================================="
    echo
}

# 停止现有服务
stop_services() {
    log_info "停止现有服务..."
    
    # 尝试停止可能运行的容器
    docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
    docker stop website-monitor-backend 2>/dev/null || true
    docker stop website-monitor-mysql 2>/dev/null || true
    docker stop website-monitor-redis 2>/dev/null || true
    
    log_success "服务已停止"
}

# 清理旧镜像
cleanup_images() {
    log_info "清理旧镜像..."
    
    # 删除可能存在的错误镜像
    docker rmi ghcr.io/yourusername/website-monitor/backend:latest 2>/dev/null || true
    docker image prune -f
    
    log_success "镜像清理完成"
}

# 拉取正确的镜像
pull_correct_image() {
    log_info "拉取正确的Docker镜像..."
    
    # 拉取Docker Hub镜像
    if docker pull leenbj68719929/website-monitor-backend:latest; then
        log_success "镜像拉取成功: leenbj68719929/website-monitor-backend:latest"
    else
        log_error "镜像拉取失败，请检查网络连接"
        exit 1
    fi
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."
    
    mkdir -p data/mysql
    mkdir -p data/redis
    mkdir -p data/backend
    mkdir -p logs/backend
    mkdir -p uploads
    mkdir -p downloads
    mkdir -p user_files
    mkdir -p backups
    mkdir -p mysql/init
    mkdir -p mysql/conf
    mkdir -p redis/conf
    
    # 设置权限
    chmod -R 755 data/
    chmod -R 755 logs/
    chmod -R 755 uploads/
    chmod -R 755 downloads/
    chmod -R 755 user_files/
    
    log_success "目录创建完成"
}

# 生成MySQL初始化脚本
generate_mysql_init() {
    log_info "生成MySQL初始化脚本..."
    
    cat > mysql/init/01-init.sql << 'EOF'
-- 网址监控系统数据库初始化脚本
CREATE DATABASE IF NOT EXISTS website_monitor DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'monitor_user'@'%' IDENTIFIED BY 'Monitor123!@#';
GRANT ALL PRIVILEGES ON website_monitor.* TO 'monitor_user'@'%';
FLUSH PRIVILEGES;
EOF
    
    log_success "MySQL初始化脚本已生成"
}

# 生成MySQL配置
generate_mysql_config() {
    log_info "生成MySQL配置..."
    
    cat > mysql/conf/custom.cnf << 'EOF'
[mysqld]
character-set-server=utf8mb4
collation-server=utf8mb4_unicode_ci
default-time-zone='+8:00'
max_connections=200
innodb_buffer_pool_size=256M
EOF
    
    log_success "MySQL配置已生成"
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    # 使用修复后的配置文件
    if docker-compose -f docker-compose.server.yml up -d; then
        log_success "服务启动成功"
    else
        log_error "服务启动失败"
        exit 1
    fi
}

# 等待服务就绪
wait_for_services() {
    log_info "等待服务就绪..."
    
    # 等待MySQL就绪
    echo -n "等待MySQL启动"
    for i in {1..30}; do
        if docker-compose -f docker-compose.server.yml exec -T mysql mysqladmin ping -h localhost --silent 2>/dev/null; then
            echo
            log_success "MySQL已就绪"
            break
        fi
        echo -n "."
        sleep 2
    done
    
    # 等待后端API就绪
    echo -n "等待后端API启动"
    for i in {1..30}; do
        if curl -f http://localhost:5000/api/health >/dev/null 2>&1; then
            echo
            log_success "后端API已就绪"
            break
        fi
        echo -n "."
        sleep 2
    done
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    # 检查容器状态
    if docker-compose -f docker-compose.server.yml ps | grep "Up" > /dev/null; then
        log_success "容器状态正常"
    else
        log_error "容器状态异常"
        docker-compose -f docker-compose.server.yml ps
        exit 1
    fi
    
    # 检查API
    if curl -f http://localhost:5000/api/health >/dev/null 2>&1; then
        log_success "API健康检查通过"
    else
        log_warning "API健康检查失败，请检查日志"
    fi
}

# 显示访问信息
show_access_info() {
    log_success "部署完成！"
    echo
    echo "=========================================="
    echo "           🚀 访问信息"
    echo "=========================================="
    echo "🔧 后端API: http://localhost:5000"
    echo "🔍 健康检查: http://localhost:5000/api/health"
    echo "📊 PhpMyAdmin: http://localhost:8080"
    echo "🐳 Docker镜像: leenbj68719929/website-monitor-backend:latest"
    echo "=========================================="
    echo "👤 数据库信息:"
    echo "用户名: monitor_user"
    echo "密码: Monitor123!@#"
    echo "数据库: website_monitor"
    echo "=========================================="
    echo "📋 常用命令:"
    echo "查看日志: docker-compose -f docker-compose.server.yml logs -f backend"
    echo "重启服务: docker-compose -f docker-compose.server.yml restart"
    echo "停止服务: docker-compose -f docker-compose.server.yml down"
    echo "=========================================="
}

# 主函数
main() {
    show_fix_info
    stop_services
    cleanup_images
    pull_correct_image
    create_directories
    generate_mysql_init
    generate_mysql_config
    start_services
    wait_for_services
    health_check
    show_access_info
}

# 运行主函数
main "$@"