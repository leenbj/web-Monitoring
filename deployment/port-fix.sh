#!/bin/bash

# 网址监控系统 - 端口冲突修复脚本
# 解决80端口被占用问题

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

# 检查端口占用情况
check_ports() {
    log_info "检查端口占用情况..."
    
    echo "=========================================="
    echo "           端口占用检查"
    echo "=========================================="
    
    # 检查80端口
    if netstat -tuln | grep ":80 " > /dev/null; then
        log_warning "端口80已被占用:"
        netstat -tuln | grep ":80 "
        echo
    else
        log_success "端口80可用"
    fi
    
    # 检查443端口
    if netstat -tuln | grep ":443 " > /dev/null; then
        log_warning "端口443已被占用:"
        netstat -tuln | grep ":443 "
        echo
    else
        log_success "端口443可用"
    fi
    
    # 检查3306端口
    if netstat -tuln | grep ":3306 " > /dev/null; then
        log_warning "端口3306已被占用:"
        netstat -tuln | grep ":3306 "
        echo
    else
        log_success "端口3306可用"
    fi
    
    # 检查6379端口
    if netstat -tuln | grep ":6379 " > /dev/null; then
        log_warning "端口6379已被占用:"
        netstat -tuln | grep ":6379 "
        echo
    else
        log_success "端口6379可用"
    fi
    
    echo "=========================================="
}

# 检查什么服务占用了80端口
check_port_80_usage() {
    log_info "检查80端口使用情况..."
    
    if command -v lsof >/dev/null 2>&1; then
        echo "80端口被以下进程占用:"
        lsof -i :80 || echo "无法获取详细信息"
    elif command -v ss >/dev/null 2>&1; then
        echo "80端口使用情况:"
        ss -tuln | grep ":80 "
    else
        echo "使用netstat检查:"
        netstat -tuln | grep ":80 "
    fi
    echo
}

# 停止冲突的容器
stop_conflicting_containers() {
    log_info "停止可能冲突的容器..."
    
    # 停止所有相关容器
    docker stop website-monitor-nginx 2>/dev/null || true
    docker stop website-monitor-backend 2>/dev/null || true
    docker stop website-monitor-mysql 2>/dev/null || true
    docker stop website-monitor-redis 2>/dev/null || true
    docker stop website-monitor-phpmyadmin 2>/dev/null || true
    
    # 停止docker-compose服务
    docker-compose down 2>/dev/null || true
    docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
    docker-compose -f docker-compose.server.yml down 2>/dev/null || true
    
    log_success "容器已停止"
}

# 清理容器和网络
cleanup_resources() {
    log_info "清理Docker资源..."
    
    # 删除可能存在的容器
    docker rm -f website-monitor-nginx 2>/dev/null || true
    docker rm -f website-monitor-backend 2>/dev/null || true
    docker rm -f website-monitor-mysql 2>/dev/null || true
    docker rm -f website-monitor-redis 2>/dev/null || true
    docker rm -f website-monitor-phpmyadmin 2>/dev/null || true
    
    # 清理网络
    docker network prune -f
    
    log_success "资源清理完成"
}

# 提供解决方案选择
show_solutions() {
    echo
    log_info "🔧 解决方案选择:"
    echo "=========================================="
    echo "1. 使用无Nginx版本 (推荐)"
    echo "   - 不启动Nginx容器"
    echo "   - 使用现有Nginx反向代理"
    echo "   - 端口: 5000(后端), 3307(MySQL), 6380(Redis), 8081(PhpMyAdmin)"
    echo
    echo "2. 停止系统Nginx服务"
    echo "   - 停止占用80端口的服务"
    echo "   - 使用Docker Nginx"
    echo "   - 需要管理员权限"
    echo
    echo "3. 修改端口映射"
    echo "   - 使用非标准端口"
    echo "   - 如8080代替80端口"
    echo "=========================================="
    echo
}

# 解决方案1: 无Nginx版本部署
deploy_without_nginx() {
    log_info "执行方案1: 无Nginx版本部署..."
    
    # 拉取镜像
    docker pull leenbj68719929/website-monitor-backend:latest
    
    # 创建必要目录
    mkdir -p data/mysql data/redis data/backend logs/backend uploads downloads user_files backups mysql/init mysql/conf
    
    # 生成MySQL初始化脚本
    cat > mysql/init/01-init.sql << 'EOF'
CREATE DATABASE IF NOT EXISTS website_monitor DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'monitor_user'@'%' IDENTIFIED BY 'Monitor123!@#';
GRANT ALL PRIVILEGES ON website_monitor.* TO 'monitor_user'@'%';
FLUSH PRIVILEGES;
EOF
    
    # 启动服务
    docker-compose -f docker-compose.no-nginx.yml up -d
    
    log_success "无Nginx版本部署完成"
    echo
    echo "访问地址:"
    echo "- 后端API: http://localhost:5000"
    echo "- 健康检查: http://localhost:5000/api/health"
    echo "- PhpMyAdmin: http://localhost:8081"
    echo "- MySQL: localhost:3307"
    echo "- Redis: localhost:6380"
}

# 解决方案2: 停止系统服务
stop_system_services() {
    log_warning "执行方案2: 停止系统服务 (需要管理员权限)..."
    
    # 检查并停止可能的服务
    if systemctl is-active --quiet nginx; then
        echo "停止Nginx服务..."
        systemctl stop nginx
        log_success "Nginx服务已停止"
    fi
    
    if systemctl is-active --quiet apache2; then
        echo "停止Apache服务..."
        systemctl stop apache2
        log_success "Apache服务已停止"
    fi
    
    if systemctl is-active --quiet httpd; then
        echo "停止HTTPD服务..."
        systemctl stop httpd
        log_success "HTTPD服务已停止"
    fi
    
    # 现在可以使用80端口了
    docker-compose -f docker-compose.server.yml up -d
    
    log_success "系统服务已停止，Docker服务已启动"
}

# 解决方案3: 修改端口
deploy_with_custom_ports() {
    log_info "执行方案3: 使用自定义端口..."
    
    # 创建自定义端口配置
    sed 's/:80/:8080/g; s/:443/:8443/g' docker-compose.server.yml > docker-compose.custom-ports.yml
    
    docker-compose -f docker-compose.custom-ports.yml up -d
    
    log_success "自定义端口部署完成"
    echo
    echo "访问地址:"
    echo "- 前端: http://localhost:8080"
    echo "- HTTPS: https://localhost:8443"
}

# 主菜单
main_menu() {
    while true; do
        echo
        echo "请选择解决方案:"
        echo "1) 无Nginx版本部署 (推荐)"
        echo "2) 停止系统Web服务"
        echo "3) 使用自定义端口"
        echo "4) 重新检查端口"
        echo "5) 退出"
        echo
        read -p "请输入选择 (1-5): " choice
        
        case $choice in
            1)
                deploy_without_nginx
                break
                ;;
            2)
                if [ "$EUID" -ne 0 ]; then
                    log_error "需要root权限执行此操作"
                else
                    stop_system_services
                    break
                fi
                ;;
            3)
                deploy_with_custom_ports
                break
                ;;
            4)
                check_ports
                check_port_80_usage
                ;;
            5)
                log_info "退出修复脚本"
                exit 0
                ;;
            *)
                log_error "无效选择，请重新输入"
                ;;
        esac
    done
}

# 验证部署
verify_deployment() {
    log_info "验证部署状态..."
    
    sleep 5
    
    # 检查容器状态
    echo "容器状态:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo
    
    # 检查API健康状态
    if curl -f http://localhost:5000/api/health >/dev/null 2>&1; then
        log_success "✅ API健康检查通过"
    else
        log_warning "⚠️ API健康检查失败，请检查容器日志"
    fi
}

# 主函数
main() {
    echo "=========================================="
    echo "    🔧 网址监控系统端口冲突修复"
    echo "=========================================="
    echo
    
    check_ports
    check_port_80_usage
    stop_conflicting_containers
    cleanup_resources
    show_solutions
    main_menu
    verify_deployment
    
    log_success "修复完成！"
}

# 运行主函数
main "$@"