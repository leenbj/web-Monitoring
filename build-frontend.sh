#!/bin/bash

# 前端静态页面构建脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_blue() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 获取后端API地址
get_api_url() {
    local backend_host=${1:-localhost}
    local backend_port=${2:-15000}
    
    if [ "$backend_host" = "localhost" ] || [ "$backend_host" = "127.0.0.1" ]; then
        echo "http://${backend_host}:${backend_port}"
    else
        echo "https://${backend_host}:${backend_port}"
    fi
}

# 构建前端
build_frontend() {
    log_blue "构建前端静态页面..."
    
    # 读取配置
    BACKEND_HOST=${BACKEND_HOST:-localhost}
    BACKEND_PORT=${BACKEND_PORT:-15000}
    API_BASE_URL=$(get_api_url $BACKEND_HOST $BACKEND_PORT)
    
    log_info "后端API地址: $API_BASE_URL"
    
    # 进入前端目录
    cd frontend
    
    # 清理现有依赖和构建
    log_info "清理现有文件..."
    rm -rf node_modules package-lock.json dist
    
    # 创建生产环境配置
    log_info "创建生产环境配置..."
    cat > .env.production << EOF
VITE_API_BASE_URL=$API_BASE_URL/api
VITE_APP_TITLE=网址监控系统
VITE_APP_MODE=production
EOF
    
    # 安装依赖
    log_info "安装依赖..."
    npm install
    
    # 处理esbuild兼容性问题
    log_info "处理esbuild兼容性..."
    npm uninstall esbuild 2>/dev/null || true
    npm install esbuild-wasm --save-dev
    
    # 构建项目
    log_info "构建项目..."
    npm run build
    
    # 验证构建结果
    if [ -d "dist" ] && [ -f "dist/index.html" ]; then
        log_info "前端构建成功"
        
        # 显示构建信息
        echo ""
        echo "构建完成信息："
        echo "  构建目录: $(pwd)/dist"
        echo "  文件数量: $(find dist -type f | wc -l)"
        echo "  总大小: $(du -sh dist | cut -f1)"
        echo ""
        
        # 返回项目根目录
        cd ..
        return 0
    else
        log_error "前端构建失败"
        cd ..
        return 1
    fi
}

# 部署到Nginx
deploy_to_nginx() {
    log_blue "部署到Nginx..."
    
    local web_root=${1:-/www/wwwroot/website-monitor}
    
    # 创建Web根目录
    log_info "创建Web目录: $web_root"
    mkdir -p "$web_root"
    
    # 复制构建文件
    log_info "复制静态文件..."
    cp -r frontend/dist/* "$web_root/"
    
    # 设置权限
    log_info "设置权限..."
    chown -R www:www "$web_root" 2>/dev/null || chown -R nginx:nginx "$web_root" 2>/dev/null || true
    chmod -R 755 "$web_root"
    
    log_info "静态文件部署完成"
}

# 创建Nginx配置
create_nginx_config() {
    log_blue "创建Nginx配置..."
    
    local domain=${1:-localhost}
    local backend_port=${2:-15000}
    local web_root=${3:-/www/wwwroot/website-monitor}
    
    cat > nginx-website-monitor.conf << EOF
server {
    listen 80;
    server_name $domain;
    root $web_root;
    index index.html;
    
    # 前端静态文件
    location / {
        try_files \$uri \$uri/ /index.html;
        
        # 缓存设置
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # API代理到后端Docker容器
    location /api {
        proxy_pass http://127.0.0.1:$backend_port;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # CORS处理
        proxy_set_header Access-Control-Allow-Origin *;
        proxy_set_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        proxy_set_header Access-Control-Allow-Headers "Content-Type, Authorization, X-Requested-With";
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # 错误处理
        proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
    }
    
    # 安全设置
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # 日志
    access_log /var/log/nginx/website_monitor_access.log;
    error_log /var/log/nginx/website_monitor_error.log;
    
    # Gzip压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/xml+rss
        application/json;
}
EOF
    
    log_info "Nginx配置文件已创建: nginx-website-monitor.conf"
    echo ""
    echo "请将此配置添加到Nginx或复制到:"
    echo "  /etc/nginx/sites-available/"
    echo "  /www/server/nginx/conf/vhost/"
    echo ""
}

# 显示部署结果
show_deployment_info() {
    echo ""
    echo "========================================="
    echo "🎉 前端静态页面构建完成！"
    echo "========================================="
    echo ""
    echo "📁 文件位置："
    echo "  构建文件: frontend/dist/"
    echo "  Nginx配置: nginx-website-monitor.conf"
    echo ""
    echo "🔧 后续步骤："
    echo "  1. 启动后端服务: docker-compose -f docker-compose-backend-only.yml up -d"
    echo "  2. 配置Nginx使用生成的配置文件"
    echo "  3. 重载Nginx配置"
    echo ""
    echo "🌐 访问地址："
    echo "  前端: http://$DOMAIN"
    echo "  后端API: http://$DOMAIN/api"
    echo ""
}

# 主函数
main() {
    echo ""
    echo "========================================="
    echo "🚀 前端静态页面构建脚本"
    echo "========================================="
    echo ""
    
    # 检查Node.js环境
    if ! command -v npm &> /dev/null; then
        log_error "Node.js/npm 未安装"
        exit 1
    fi
    
    # 检查前端目录
    if [ ! -d "frontend" ]; then
        log_error "frontend目录不存在"
        exit 1
    fi
    
    # 读取环境变量
    DOMAIN=${DOMAIN:-localhost}
    BACKEND_HOST=${BACKEND_HOST:-localhost}
    BACKEND_PORT=${BACKEND_PORT:-15000}
    WEB_ROOT=${WEB_ROOT:-/www/wwwroot/website-monitor}
    
    # 构建前端
    if build_frontend; then
        # 创建Nginx配置
        create_nginx_config "$DOMAIN" "$BACKEND_PORT" "$WEB_ROOT"
        
        # 如果指定了Web根目录且有权限，则部署
        if [ "$WEB_ROOT" != "/www/wwwroot/website-monitor" ] || [ "$(id -u)" = "0" ]; then
            deploy_to_nginx "$WEB_ROOT"
        else
            log_warn "跳过自动部署，请手动复制frontend/dist/*到Web目录"
        fi
        
        show_deployment_info
    else
        log_error "前端构建失败"
        exit 1
    fi
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi