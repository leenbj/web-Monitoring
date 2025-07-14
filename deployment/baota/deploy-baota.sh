#!/bin/bash

# 网址监控系统 - 宝塔面板一键部署脚本
# 使用方法: ./deploy-baota.sh [init|update|restart|backup|clean]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 配置变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="/www/website-monitor"
WEB_ROOT="/www/wwwroot"
BACKUP_DIR="/www/backup/website-monitor"
LOG_FILE="/tmp/deploy-baota.log"

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1" | tee -a "$LOG_FILE"
}

# 检查系统环境
check_environment() {
    log_info "检查系统环境..."
    
    # 检查是否为root用户
    if [[ $EUID -ne 0 ]]; then
        log_error "请使用root权限运行此脚本"
        exit 1
    fi
    
    # 检查宝塔面板
    if [ ! -f "/www/server/panel/BT-Panel" ]; then
        log_error "未检测到宝塔面板，请先安装宝塔面板"
        exit 1
    fi
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请在宝塔面板中安装Docker"
        exit 1
    fi
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请在宝塔面板中安装Docker Compose"
        exit 1
    fi
    
    # 检查Nginx
    if ! command -v nginx &> /dev/null; then
        log_error "Nginx未安装，请在宝塔面板中安装Nginx"
        exit 1
    fi
    
    log_success "系统环境检查完成"
}

# 读取配置
load_config() {
    log_info "加载配置文件..."
    
    # 检查配置文件
    if [ ! -f ".env" ]; then
        if [ -f ".env.baota" ]; then
            log_warning "未找到.env文件，正在复制.env.baota"
            cp .env.baota .env
        else
            log_error "未找到环境配置文件"
            exit 1
        fi
    fi
    
    # 加载环境变量
    source .env
    
    # 验证必要的配置
    if [ -z "$DOCKERHUB_USERNAME" ] || [ -z "$DB_PASSWORD" ] || [ -z "$SECRET_KEY" ]; then
        log_error "请在.env文件中配置必要的环境变量"
        exit 1
    fi
    
    # 设置域名 (从环境变量或提示用户输入)
    if [ -z "$DOMAIN_NAME" ]; then
        read -p "请输入域名 (例: monitor.yourdomain.com): " DOMAIN_NAME
        if [ -z "$DOMAIN_NAME" ]; then
            log_error "域名不能为空"
            exit 1
        fi
    fi
    
    log_success "配置文件加载完成"
}

# 初始化项目目录
init_directories() {
    log_info "初始化项目目录..."
    
    # 创建项目目录
    mkdir -p "$PROJECT_DIR"
    mkdir -p "$PROJECT_DIR/data/mysql"
    mkdir -p "$PROJECT_DIR/data/redis"
    mkdir -p "$PROJECT_DIR/data/backend"
    mkdir -p "$PROJECT_DIR/logs/backend"
    mkdir -p "$PROJECT_DIR/uploads"
    mkdir -p "$PROJECT_DIR/downloads"
    mkdir -p "$PROJECT_DIR/user_files"
    mkdir -p "$PROJECT_DIR/backups"
    mkdir -p "$PROJECT_DIR/mysql/init"
    mkdir -p "$PROJECT_DIR/mysql/conf"
    mkdir -p "$PROJECT_DIR/redis/conf"
    
    # 创建网站目录
    mkdir -p "$WEB_ROOT/$DOMAIN_NAME"
    
    # 创建备份目录
    mkdir -p "$BACKUP_DIR"
    
    # 设置权限
    chmod -R 755 "$PROJECT_DIR"
    chmod -R 755 "$WEB_ROOT/$DOMAIN_NAME"
    
    log_success "项目目录初始化完成"
}

# 复制配置文件
copy_configs() {
    log_info "复制配置文件..."
    
    # 复制Docker配置
    cp docker-compose.yml "$PROJECT_DIR/"
    cp .env "$PROJECT_DIR/"
    
    # 生成MySQL初始化脚本
    cat > "$PROJECT_DIR/mysql/init/01-init.sql" << EOF
-- 网址监控系统数据库初始化脚本
CREATE DATABASE IF NOT EXISTS $DB_NAME DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '$DB_USER'@'%' IDENTIFIED BY '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'%';
FLUSH PRIVILEGES;
EOF
    
    # 生成MySQL配置
    cat > "$PROJECT_DIR/mysql/conf/custom.cnf" << EOF
[mysqld]
character-set-server=utf8mb4
collation-server=utf8mb4_unicode_ci
default-time-zone='+8:00'
max_connections=200
innodb_buffer_pool_size=256M
EOF
    
    log_success "配置文件复制完成"
}

# 配置Nginx
setup_nginx() {
    log_info "配置Nginx..."
    
    # 创建Nginx配置文件
    NGINX_CONF="/www/server/nginx/conf/vhost/$DOMAIN_NAME.conf"
    
    # 复制Nginx配置模板并替换域名
    sed "s/monitor\.yourdomain\.com/$DOMAIN_NAME/g" nginx.conf > "$NGINX_CONF"
    
    # 创建SSL证书目录
    mkdir -p "/www/server/panel/vhost/cert/$DOMAIN_NAME"
    
    # 测试Nginx配置
    if nginx -t; then
        log_success "Nginx配置验证通过"
        systemctl reload nginx
        log_success "Nginx配置重载完成"
    else
        log_error "Nginx配置验证失败"
        exit 1
    fi
}

# 部署Docker服务
deploy_docker() {
    log_info "部署Docker服务..."
    
    cd "$PROJECT_DIR"
    
    # 拉取最新镜像
    log_info "拉取Docker镜像..."
    docker-compose pull
    
    # 启动服务
    log_info "启动Docker服务..."
    docker-compose up -d
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 30
    
    # 检查服务状态
    if docker-compose ps | grep "Up"; then
        log_success "Docker服务启动成功"
    else
        log_error "Docker服务启动失败"
        docker-compose logs
        exit 1
    fi
}

# 初始化数据库
init_database() {
    log_info "初始化数据库..."
    
    cd "$PROJECT_DIR"
    
    # 等待数据库就绪
    log_info "等待数据库就绪..."
    for i in {1..30}; do
        if docker-compose exec -T mysql mysqladmin ping -h localhost --silent; then
            break
        fi
        sleep 2
    done
    
    # 检查后端容器是否包含初始化脚本
    if docker-compose exec -T backend test -f init_database.py; then
        log_info "执行数据库初始化..."
        docker-compose exec -T backend python init_database.py
        log_success "数据库初始化完成"
    else
        log_warning "未找到数据库初始化脚本，跳过数据库初始化"
    fi
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    # 检查Docker服务
    cd "$PROJECT_DIR"
    if ! docker-compose ps | grep "Up" > /dev/null; then
        log_error "Docker服务未正常运行"
        return 1
    fi
    
    # 检查后端API
    for i in {1..10}; do
        if curl -f http://localhost:5000/api/health > /dev/null 2>&1; then
            log_success "后端API健康检查通过"
            break
        fi
        if [ $i -eq 10 ]; then
            log_error "后端API健康检查失败"
            return 1
        fi
        sleep 3
    done
    
    # 检查前端
    if [ -f "$WEB_ROOT/$DOMAIN_NAME/index.html" ]; then
        log_success "前端文件检查通过"
    else
        log_warning "前端文件未部署，请手动上传前端文件到 $WEB_ROOT/$DOMAIN_NAME/"
    fi
    
    # 检查数据库
    cd "$PROJECT_DIR"
    if docker-compose exec -T mysql mysqladmin ping -h localhost --silent; then
        log_success "数据库健康检查通过"
    else
        log_error "数据库健康检查失败"
        return 1
    fi
    
    log_success "健康检查完成"
    return 0
}

# 备份数据
backup_data() {
    log_info "备份数据..."
    
    local backup_time=$(date +%Y%m%d_%H%M%S)
    local backup_path="$BACKUP_DIR/backup_$backup_time"
    
    mkdir -p "$backup_path"
    
    cd "$PROJECT_DIR"
    
    # 备份数据库
    log_info "备份数据库..."
    docker-compose exec -T mysql mysqldump -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" > "$backup_path/database.sql"
    
    # 备份应用数据
    log_info "备份应用数据..."
    tar -czf "$backup_path/data.tar.gz" data/ uploads/ downloads/ user_files/
    
    # 备份配置文件
    log_info "备份配置文件..."
    tar -czf "$backup_path/config.tar.gz" docker-compose.yml .env
    
    # 备份前端文件
    if [ -d "$WEB_ROOT/$DOMAIN_NAME" ]; then
        log_info "备份前端文件..."
        tar -czf "$backup_path/frontend.tar.gz" -C "$WEB_ROOT" "$DOMAIN_NAME"
    fi
    
    log_success "数据备份完成: $backup_path"
    
    # 清理旧备份 (保留7天)
    find "$BACKUP_DIR" -type d -name "backup_*" -mtime +7 -exec rm -rf {} \; 2>/dev/null || true
}

# 更新服务
update_service() {
    log_info "更新服务..."
    
    # 备份当前数据
    backup_data
    
    cd "$PROJECT_DIR"
    
    # 拉取最新镜像
    log_info "拉取最新镜像..."
    docker-compose pull
    
    # 重启服务
    log_info "重启服务..."
    docker-compose up -d
    
    # 健康检查
    sleep 10
    if health_check; then
        log_success "服务更新完成"
    else
        log_error "服务更新后健康检查失败"
        exit 1
    fi
}

# 重启服务
restart_service() {
    log_info "重启服务..."
    
    cd "$PROJECT_DIR"
    
    # 重启Docker服务
    docker-compose restart
    
    # 重启Nginx
    systemctl restart nginx
    
    # 健康检查
    sleep 10
    if health_check; then
        log_success "服务重启完成"
    else
        log_error "服务重启后健康检查失败"
        exit 1
    fi
}

# 清理系统
clean_system() {
    log_info "清理系统..."
    
    # 清理Docker资源
    docker system prune -f
    docker volume prune -f
    
    # 清理日志
    find /www/wwwlogs/ -name "*.log" -mtime +7 -delete 2>/dev/null || true
    find "$PROJECT_DIR/logs/" -name "*.log" -mtime +7 -delete 2>/dev/null || true
    
    # 清理临时文件
    rm -rf /tmp/deploy-*.log
    
    log_success "系统清理完成"
}

# 显示部署信息
show_info() {
    log_success "部署完成！"
    echo
    echo "=========================================="
    echo "           🚀 部署信息"
    echo "=========================================="
    echo "🌐 前端地址: https://$DOMAIN_NAME"
    echo "🔧 后端API: https://$DOMAIN_NAME/api"
    echo "📊 PhpMyAdmin: https://$DOMAIN_NAME/phpmyadmin"
    echo "🔍 Redis管理: https://$DOMAIN_NAME/redis"
    echo "=========================================="
    echo "👤 默认账号: admin"
    echo "🔑 默认密码: admin123"
    echo "=========================================="
    echo
    echo "📋 常用命令:"
    echo "查看状态: cd $PROJECT_DIR && docker-compose ps"
    echo "查看日志: cd $PROJECT_DIR && docker-compose logs -f backend"
    echo "重启服务: $0 restart"
    echo "更新服务: $0 update"
    echo "备份数据: $0 backup"
    echo "清理系统: $0 clean"
    echo "=========================================="
    echo
    echo "📁 重要路径:"
    echo "项目目录: $PROJECT_DIR"
    echo "网站目录: $WEB_ROOT/$DOMAIN_NAME"
    echo "备份目录: $BACKUP_DIR"
    echo "Nginx配置: /www/server/nginx/conf/vhost/$DOMAIN_NAME.conf"
    echo "=========================================="
}

# 显示帮助信息
show_help() {
    echo "网址监控系统 - 宝塔面板一键部署脚本"
    echo
    echo "使用方法:"
    echo "  $0 [命令]"
    echo
    echo "命令:"
    echo "  init     初始化部署 (首次部署)"
    echo "  update   更新服务"
    echo "  restart  重启服务"
    echo "  backup   备份数据"
    echo "  clean    清理系统"
    echo "  health   健康检查"
    echo "  help     显示帮助信息"
    echo
    echo "示例:"
    echo "  $0 init      # 首次部署"
    echo "  $0 update    # 更新服务"
    echo "  $0 restart   # 重启服务"
    echo "  $0 backup    # 备份数据"
}

# 主函数
main() {
    local command=${1:-init}
    
    echo "=========================================="
    echo "    🐼 网址监控系统 - 宝塔面板部署"
    echo "=========================================="
    echo
    
    # 切换到脚本目录
    cd "$SCRIPT_DIR"
    
    case $command in
        init)
            check_environment
            load_config
            init_directories
            copy_configs
            setup_nginx
            deploy_docker
            init_database
            health_check
            show_info
            ;;
        update)
            check_environment
            load_config
            update_service
            ;;
        restart)
            check_environment
            load_config
            restart_service
            ;;
        backup)
            check_environment
            load_config
            backup_data
            ;;
        clean)
            check_environment
            clean_system
            ;;
        health)
            check_environment
            load_config
            health_check
            ;;
        help)
            show_help
            ;;
        *)
            log_error "未知命令: $command"
            show_help
            exit 1
            ;;
    esac
}

# 信号处理
cleanup() {
    log_info "脚本执行中断"
    exit 1
}

trap cleanup INT TERM

# 运行主函数
main "$@"