#!/bin/bash

# 网址监控系统 - 端口配置管理脚本
# 支持自定义Nginx和其他服务端口

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

# 显示当前端口配置
show_current_config() {
    log_info "当前端口配置:"
    echo "=========================================="
    
    if [ -f ".env" ]; then
        echo "Nginx HTTP端口: $(grep NGINX_HTTP_PORT .env | cut -d'=' -f2 || echo '85')"
        echo "Nginx HTTPS端口: $(grep NGINX_HTTPS_PORT .env | cut -d'=' -f2 || echo '448')"
        echo "后端API端口: $(grep BACKEND_PORT .env | cut -d'=' -f2 || echo '5000')"
        echo "MySQL端口: $(grep MYSQL_PORT .env | cut -d'=' -f2 || echo '3306')"
        echo "Redis端口: $(grep REDIS_PORT .env | cut -d'=' -f2 || echo '6379')"
        echo "PhpMyAdmin端口: $(grep PHPMYADMIN_PORT .env | cut -d'=' -f2 || echo '8080')"
    else
        echo "未找到.env配置文件"
        echo "默认端口配置:"
        echo "Nginx HTTP端口: 85"
        echo "Nginx HTTPS端口: 448"
        echo "后端API端口: 5000"
        echo "MySQL端口: 3306"
        echo "Redis端口: 6379"
        echo "PhpMyAdmin端口: 8080"
    fi
    echo "=========================================="
    echo
}

# 检查端口是否被占用
check_port_usage() {
    local port=$1
    local service_name=$2
    
    if netstat -tuln 2>/dev/null | grep ":$port " > /dev/null; then
        log_warning "端口 $port ($service_name) 已被占用"
        if command -v lsof >/dev/null 2>&1; then
            echo "占用进程:"
            lsof -i :$port 2>/dev/null || echo "无法获取详细信息"
        fi
        return 1
    else
        log_success "端口 $port ($service_name) 可用"
        return 0
    fi
}

# 批量检查端口
check_all_ports() {
    log_info "检查所有端口占用情况..."
    echo
    
    local nginx_http=${NGINX_HTTP_PORT:-85}
    local nginx_https=${NGINX_HTTPS_PORT:-448}
    local backend=${BACKEND_PORT:-5000}
    local mysql=${MYSQL_PORT:-3306}
    local redis=${REDIS_PORT:-6379}
    local phpmyadmin=${PHPMYADMIN_PORT:-8080}
    
    check_port_usage $nginx_http "Nginx HTTP"
    check_port_usage $nginx_https "Nginx HTTPS"
    check_port_usage $backend "后端API"
    check_port_usage $mysql "MySQL"
    check_port_usage $redis "Redis"
    check_port_usage $phpmyadmin "PhpMyAdmin"
    echo
}

# 交互式配置端口
configure_ports_interactive() {
    log_info "交互式端口配置..."
    echo
    
    # 读取当前配置
    source .env 2>/dev/null || true
    
    # Nginx HTTP端口
    echo -n "Nginx HTTP端口 (当前: ${NGINX_HTTP_PORT:-85}): "
    read new_http_port
    new_http_port=${new_http_port:-${NGINX_HTTP_PORT:-85}}
    
    # Nginx HTTPS端口
    echo -n "Nginx HTTPS端口 (当前: ${NGINX_HTTPS_PORT:-448}): "
    read new_https_port
    new_https_port=${new_https_port:-${NGINX_HTTPS_PORT:-448}}
    
    # 后端API端口
    echo -n "后端API端口 (当前: ${BACKEND_PORT:-5000}): "
    read new_backend_port
    new_backend_port=${new_backend_port:-${BACKEND_PORT:-5000}}
    
    # MySQL端口
    echo -n "MySQL端口 (当前: ${MYSQL_PORT:-3306}): "
    read new_mysql_port
    new_mysql_port=${new_mysql_port:-${MYSQL_PORT:-3306}}
    
    # Redis端口
    echo -n "Redis端口 (当前: ${REDIS_PORT:-6379}): "
    read new_redis_port
    new_redis_port=${new_redis_port:-${REDIS_PORT:-6379}}
    
    # PhpMyAdmin端口
    echo -n "PhpMyAdmin端口 (当前: ${PHPMYADMIN_PORT:-8080}): "
    read new_phpmyadmin_port
    new_phpmyadmin_port=${new_phpmyadmin_port:-${PHPMYADMIN_PORT:-8080}}
    
    # 检查新端口是否可用
    echo
    log_info "检查新端口配置..."
    
    local all_available=true
    check_port_usage $new_http_port "Nginx HTTP" || all_available=false
    check_port_usage $new_https_port "Nginx HTTPS" || all_available=false
    check_port_usage $new_backend_port "后端API" || all_available=false
    check_port_usage $new_mysql_port "MySQL" || all_available=false
    check_port_usage $new_redis_port "Redis" || all_available=false
    check_port_usage $new_phpmyadmin_port "PhpMyAdmin" || all_available=false
    
    if [ "$all_available" = false ]; then
        echo
        read -p "部分端口被占用，是否继续配置? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "配置已取消"
            return 1
        fi
    fi
    
    # 更新环境变量
    update_env_file $new_http_port $new_https_port $new_backend_port $new_mysql_port $new_redis_port $new_phpmyadmin_port
}

# 更新环境变量文件
update_env_file() {
    local http_port=$1
    local https_port=$2
    local backend_port=$3
    local mysql_port=$4
    local redis_port=$5
    local phpmyadmin_port=$6
    
    log_info "更新环境变量文件..."
    
    # 创建临时文件
    local temp_file=$(mktemp)
    
    # 如果.env文件不存在，从模板复制
    if [ ! -f ".env" ]; then
        if [ -f ".env.production" ]; then
            cp .env.production .env
            log_info "从.env.production创建.env文件"
        else
            log_error "未找到环境变量模板文件"
            return 1
        fi
    fi
    
    # 更新端口配置
    sed -e "s/^NGINX_HTTP_PORT=.*/NGINX_HTTP_PORT=$http_port/" \
        -e "s/^NGINX_HTTPS_PORT=.*/NGINX_HTTPS_PORT=$https_port/" \
        -e "s/^BACKEND_PORT=.*/BACKEND_PORT=$backend_port/" \
        -e "s/^MYSQL_PORT=.*/MYSQL_PORT=$mysql_port/" \
        -e "s/^REDIS_PORT=.*/REDIS_PORT=$redis_port/" \
        -e "s/^PHPMYADMIN_PORT=.*/PHPMYADMIN_PORT=$phpmyadmin_port/" \
        .env > $temp_file
    
    # 如果没有找到对应配置，则添加
    if ! grep -q "NGINX_HTTP_PORT=" $temp_file; then
        echo "NGINX_HTTP_PORT=$http_port" >> $temp_file
    fi
    if ! grep -q "NGINX_HTTPS_PORT=" $temp_file; then
        echo "NGINX_HTTPS_PORT=$https_port" >> $temp_file
    fi
    
    # 替换原文件
    mv $temp_file .env
    
    log_success "环境变量文件已更新"
    
    # 显示新配置
    echo
    log_info "新的端口配置:"
    echo "=========================================="
    echo "Nginx HTTP端口: $http_port"
    echo "Nginx HTTPS端口: $https_port"
    echo "后端API端口: $backend_port"
    echo "MySQL端口: $mysql_port"
    echo "Redis端口: $redis_port"
    echo "PhpMyAdmin端口: $phpmyadmin_port"
    echo "=========================================="
}

# 快速设置常用端口组合
quick_setup() {
    log_info "快速端口配置选项:"
    echo "=========================================="
    echo "1. 默认配置 (推荐)"
    echo "   HTTP:85, HTTPS:448, API:5000, MySQL:3306, Redis:6379, PhpMyAdmin:8080"
    echo
    echo "2. 高端口配置 (避免冲突)"
    echo "   HTTP:8080, HTTPS:8443, API:8000, MySQL:3307, Redis:6380, PhpMyAdmin:8081"
    echo
    echo "3. 开发配置"
    echo "   HTTP:3000, HTTPS:3001, API:5000, MySQL:3306, Redis:6379, PhpMyAdmin:8080"
    echo
    echo "4. 自定义配置"
    echo "=========================================="
    echo
    
    read -p "请选择配置 (1-4): " choice
    
    case $choice in
        1)
            update_env_file 85 448 5000 3306 6379 8080
            ;;
        2)
            update_env_file 8080 8443 8000 3307 6380 8081
            ;;
        3)
            update_env_file 3000 3001 5000 3306 6379 8080
            ;;
        4)
            configure_ports_interactive
            ;;
        *)
            log_error "无效选择"
            return 1
            ;;
    esac
}

# 显示使用说明
show_usage() {
    echo "端口配置管理工具使用说明："
    echo
    echo "命令:"
    echo "  $0 show     - 显示当前端口配置"
    echo "  $0 check    - 检查端口占用情况"
    echo "  $0 config   - 交互式配置端口"
    echo "  $0 quick    - 快速配置端口"
    echo "  $0 reset    - 重置为默认端口"
    echo
    echo "示例:"
    echo "  $0 show     # 查看当前配置"
    echo "  $0 quick    # 快速设置"
    echo "  $0 config   # 自定义配置"
}

# 重置为默认端口
reset_to_default() {
    log_info "重置为默认端口配置..."
    update_env_file 85 448 5000 3306 6379 8080
    log_success "已重置为默认端口配置"
}

# 显示部署命令
show_deploy_commands() {
    echo
    log_info "部署命令:"
    echo "=========================================="
    echo "1. 无Nginx版本 (仅后端服务):"
    echo "   docker-compose -f docker-compose.no-nginx.yml up -d"
    echo
    echo "2. 包含Nginx版本 (完整服务):"
    echo "   ./generate-ssl.sh  # 生成SSL证书"
    echo "   docker-compose -f docker-compose.with-nginx.yml up -d"
    echo
    echo "3. 服务器版本 (基础服务):"
    echo "   docker-compose -f docker-compose.server.yml up -d"
    echo "=========================================="
    echo
    echo "访问地址 (根据配置的端口):"
    source .env 2>/dev/null || true
    echo "HTTP:  http://localhost:${NGINX_HTTP_PORT:-85}"
    echo "HTTPS: https://localhost:${NGINX_HTTPS_PORT:-448}"
    echo "API:   http://localhost:${BACKEND_PORT:-5000}"
    echo "PhpMyAdmin: http://localhost:${PHPMYADMIN_PORT:-8080}"
}

# 主函数
main() {
    local command=${1:-show}
    
    echo "=========================================="
    echo "    ⚙️ 网址监控系统端口配置管理"
    echo "=========================================="
    echo
    
    case $command in
        show)
            show_current_config
            ;;
        check)
            # 加载环境变量
            source .env 2>/dev/null || true
            check_all_ports
            ;;
        config)
            configure_ports_interactive
            show_deploy_commands
            ;;
        quick)
            quick_setup
            show_deploy_commands
            ;;
        reset)
            reset_to_default
            show_deploy_commands
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            log_error "未知命令: $command"
            show_usage
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"