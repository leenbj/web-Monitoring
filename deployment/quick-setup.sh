#!/bin/bash

# 网址监控系统 - 快速配置脚本
# Docker Hub用户名: leenbj68719929

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# 显示欢迎信息
show_welcome() {
    echo "=========================================="
    echo "    🚀 网址监控系统快速配置"
    echo "=========================================="
    echo "Docker Hub用户名: leenbj68719929"
    echo "镜像名称: leenbj68719929/website-monitor-backend"
    echo "=========================================="
    echo
}

# 检测环境
detect_environment() {
    log_info "检测部署环境..."
    
    if [ -f "/www/server/panel/BT-Panel" ]; then
        ENVIRONMENT="baota"
        log_success "检测到宝塔面板环境"
    elif command -v docker &> /dev/null; then
        ENVIRONMENT="docker"
        log_success "检测到Docker环境"
    else
        ENVIRONMENT="manual"
        log_warning "未检测到特定环境，使用手动配置"
    fi
}

# 配置GitHub Secrets信息
show_github_config() {
    echo
    log_info "📋 GitHub Secrets配置信息："
    echo "=========================================="
    echo "请在GitHub仓库中配置以下Secrets："
    echo
    echo "DOCKERHUB_USERNAME=leenbj68719929"
    echo "DOCKERHUB_TOKEN=你的Docker Hub Access Token"
    echo
    echo "配置路径:"
    echo "GitHub仓库 → Settings → Secrets and variables → Actions"
    echo "=========================================="
    echo
}

# 生成配置文件
generate_config() {
    local env_file=".env"
    
    log_info "生成环境配置文件..."
    
    case $ENVIRONMENT in
        "baota")
            if [ ! -f "baota/.env.baota" ]; then
                log_error "宝塔配置模板不存在"
                exit 1
            fi
            cp baota/.env.baota "$env_file"
            log_success "已生成宝塔面板环境配置: $env_file"
            ;;
        "docker")
            if [ ! -f ".env.production" ]; then
                log_error "生产环境配置模板不存在"
                exit 1
            fi
            cp .env.production "$env_file"
            log_success "已生成Docker环境配置: $env_file"
            ;;
        *)
            if [ ! -f ".env.example" ]; then
                log_error "配置模板不存在"
                exit 1
            fi
            cp .env.example "$env_file"
            log_success "已生成通用环境配置: $env_file"
            ;;
    esac
}

# 配置提醒
show_config_reminders() {
    echo
    log_warning "📝 重要配置提醒："
    echo "=========================================="
    echo "1. 邮件配置 (必须修改):"
    echo "   MAIL_USERNAME=你的邮箱@qq.com"
    echo "   MAIL_PASSWORD=你的QQ应用密码"
    echo
    echo "2. 域名配置 (必须修改):"
    echo "   DOMAIN_NAME=你的域名.com"
    echo
    echo "3. 安全密钥 (建议重新生成):"
    echo "   SECRET_KEY=32位随机字符串"
    echo "   JWT_SECRET_KEY=32位随机字符串"
    echo
    echo "4. 数据库密码 (可选修改):"
    echo "   DB_PASSWORD=当前已设置强密码"
    echo "   DB_ROOT_PASSWORD=当前已设置强密码"
    echo "=========================================="
    echo
}

# 显示部署指令
show_deploy_commands() {
    echo
    log_info "🚀 部署命令："
    echo "=========================================="
    
    case $ENVIRONMENT in
        "baota")
            echo "# 宝塔面板部署"
            echo "cd baota"
            echo "./deploy-baota.sh init"
            ;;
        "docker")
            echo "# Docker Compose部署"
            echo "docker-compose -f docker-compose.prod.yml up -d"
            ;;
        *)
            echo "# 手动部署"
            echo "1. 编辑 .env 文件"
            echo "2. 运行部署脚本"
            echo "3. 配置Nginx"
            ;;
    esac
    
    echo "=========================================="
    echo
}

# 显示验证步骤
show_verification() {
    echo
    log_info "✅ 验证步骤："
    echo "=========================================="
    echo "1. 检查Docker镜像:"
    echo "   docker pull leenbj68719929/website-monitor-backend:latest"
    echo
    echo "2. 验证GitHub Actions:"
    echo "   GitHub仓库 → Actions → 检查构建状态"
    echo
    echo "3. 测试API接口:"
    echo "   curl http://localhost:5000/api/health"
    echo
    echo "4. 访问前端:"
    echo "   https://你的域名.com"
    echo "=========================================="
    echo
}

# 显示Docker Hub信息
show_dockerhub_info() {
    echo
    log_info "🐳 Docker Hub信息："
    echo "=========================================="
    echo "用户名: leenbj68719929"
    echo "仓库: leenbj68719929/website-monitor-backend"
    echo "链接: https://hub.docker.com/r/leenbj68719929/website-monitor-backend"
    echo "标签: latest, main, 时间戳版本"
    echo "架构: linux/amd64, linux/arm64"
    echo "=========================================="
    echo
}

# 主函数
main() {
    show_welcome
    detect_environment
    show_github_config
    generate_config
    show_config_reminders
    show_deploy_commands
    show_verification
    show_dockerhub_info
    
    log_success "配置完成！请按照上述说明进行部署。"
    echo
    echo "需要帮助？查看详细文档:"
    echo "- 宝塔部署: deployment/baota/README.md"
    echo "- Docker部署: deployment/README.md"
    echo "- Docker Hub: deployment/DOCKER_HUB_SETUP.md"
}

# 运行主函数
main "$@"