#!/bin/bash

# 网址监控系统 - 一键部署脚本
# 使用方法: ./deploy.sh [环境]
# 环境: dev | prod | test

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
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

# 检查依赖
check_dependencies() {
    log_info "检查系统依赖..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    
    # 检查Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js未安装，请先安装Node.js"
        exit 1
    fi
    
    # 检查npm
    if ! command -v npm &> /dev/null; then
        log_error "npm未安装，请先安装npm"
        exit 1
    fi
    
    log_success "系统依赖检查完成"
}

# 环境配置
setup_environment() {
    local env=$1
    log_info "设置环境: $env"
    
    # 检查环境变量文件
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            log_warning "未找到.env文件，正在复制.env.example"
            cp .env.example .env
            log_warning "请编辑.env文件并填写正确的配置值"
            read -p "是否现在编辑.env文件? (y/n): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                ${EDITOR:-vi} .env
            fi
        else
            log_error "未找到.env.example文件"
            exit 1
        fi
    fi
    
    # 加载环境变量
    source .env
    
    # 验证必要的环境变量
    if [ -z "$DB_PASSWORD" ] || [ -z "$SECRET_KEY" ] || [ -z "$JWT_SECRET_KEY" ]; then
        log_error "请在.env文件中配置必要的环境变量"
        exit 1
    fi
    
    log_success "环境配置完成"
}

# 构建前端
build_frontend() {
    log_info "开始构建前端..."
    
    cd frontend
    
    # 安装依赖
    log_info "安装前端依赖..."
    npm install
    
    # 构建生产版本
    log_info "构建前端生产版本..."
    npm run build
    
    cd ..
    
    log_success "前端构建完成"
}

# 构建后端镜像
build_backend() {
    log_info "开始构建后端镜像..."
    
    # 构建Docker镜像
    docker build -t website-monitor-backend:latest .
    
    log_success "后端镜像构建完成"
}

# 部署服务
deploy_services() {
    local env=$1
    log_info "部署服务 (环境: $env)..."
    
    # 选择compose文件
    local compose_file
    case $env in
        prod)
            compose_file="docker-compose.prod.yml"
            ;;
        dev)
            compose_file="../docker-compose.yml"
            ;;
        test)
            compose_file="docker-compose.test.yml"
            ;;
        *)
            log_error "不支持的环境: $env"
            exit 1
            ;;
    esac
    
    # 停止现有服务
    log_info "停止现有服务..."
    docker-compose -f $compose_file down
    
    # 启动服务
    log_info "启动服务..."
    docker-compose -f $compose_file up -d
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 30
    
    # 检查服务状态
    log_info "检查服务状态..."
    docker-compose -f $compose_file ps
    
    log_success "服务部署完成"
}

# 初始化数据库
init_database() {
    log_info "初始化数据库..."
    
    # 等待数据库就绪
    log_info "等待数据库就绪..."
    sleep 10
    
    # 运行数据库初始化
    docker-compose -f $compose_file exec backend python init_database.py
    
    log_success "数据库初始化完成"
}

# 配置Nginx
setup_nginx() {
    log_info "配置Nginx..."
    
    # 检查Nginx是否安装
    if ! command -v nginx &> /dev/null; then
        log_warning "Nginx未安装，跳过Nginx配置"
        return
    fi
    
    # 复制前端文件
    log_info "复制前端文件..."
    sudo mkdir -p /var/www/website-monitor
    sudo cp -r frontend/dist/* /var/www/website-monitor/
    sudo chown -R www-data:www-data /var/www/website-monitor
    
    # 复制Nginx配置
    log_info "复制Nginx配置..."
    sudo cp nginx/website-monitor.conf /etc/nginx/sites-available/
    sudo ln -sf /etc/nginx/sites-available/website-monitor.conf /etc/nginx/sites-enabled/
    
    # 测试Nginx配置
    log_info "测试Nginx配置..."
    sudo nginx -t
    
    # 重载Nginx
    log_info "重载Nginx..."
    sudo systemctl reload nginx
    
    log_success "Nginx配置完成"
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    # 检查后端API
    log_info "检查后端API..."
    if curl -f http://localhost:5000/api/health > /dev/null 2>&1; then
        log_success "后端API健康检查通过"
    else
        log_error "后端API健康检查失败"
        return 1
    fi
    
    # 检查前端
    log_info "检查前端..."
    if curl -f http://localhost/ > /dev/null 2>&1; then
        log_success "前端健康检查通过"
    else
        log_warning "前端健康检查失败，可能需要配置Nginx"
    fi
    
    # 检查数据库
    log_info "检查数据库..."
    if docker-compose -f $compose_file exec mysql mysqladmin ping -h localhost --silent; then
        log_success "数据库健康检查通过"
    else
        log_error "数据库健康检查失败"
        return 1
    fi
    
    log_success "健康检查完成"
}

# 显示部署信息
show_deployment_info() {
    log_success "部署完成！"
    echo
    echo "=========================================="
    echo "           部署信息"
    echo "=========================================="
    echo "前端地址: http://localhost"
    echo "后端API: http://localhost:5000"
    echo "默认账号: admin"
    echo "默认密码: admin123"
    echo "=========================================="
    echo
    echo "常用命令:"
    echo "查看日志: docker-compose -f $compose_file logs -f"
    echo "重启服务: docker-compose -f $compose_file restart"
    echo "停止服务: docker-compose -f $compose_file down"
    echo "=========================================="
}

# 清理函数
cleanup() {
    log_info "清理临时文件..."
    # 清理Docker构建缓存
    docker builder prune -f
    log_success "清理完成"
}

# 主函数
main() {
    local env=${1:-prod}
    
    echo "=========================================="
    echo "    网址监控系统 - 一键部署脚本"
    echo "=========================================="
    echo
    
    # 检查参数
    if [[ ! "$env" =~ ^(dev|prod|test)$ ]]; then
        log_error "无效的环境参数: $env"
        echo "使用方法: $0 [dev|prod|test]"
        exit 1
    fi
    
    # 检查是否为root用户
    if [[ "$env" == "prod" && $EUID -ne 0 ]]; then
        log_error "生产环境部署需要root权限"
        exit 1
    fi
    
    # 切换到deployment目录
    cd "$(dirname "$0")"
    
    # 设置全局变量
    compose_file="docker-compose.prod.yml"
    
    # 执行部署步骤
    check_dependencies
    setup_environment $env
    build_frontend
    build_backend
    deploy_services $env
    init_database
    
    if [[ "$env" == "prod" ]]; then
        setup_nginx
    fi
    
    health_check
    show_deployment_info
    cleanup
    
    log_success "部署完成！"
}

# 信号处理
trap cleanup EXIT

# 运行主函数
main "$@"