#!/bin/bash

# 修复Docker容器权限问题并安装Python依赖
# 解决OSError: [Errno 13] Permission denied 问题

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

CONTAINER_NAME="website-monitor-backend"

echo "==========================================="
echo "    🔧 容器权限修复工具"
echo "==========================================="
echo

# 检查容器是否存在
if ! docker ps --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
    log_error "容器 $CONTAINER_NAME 不存在或未运行"
    exit 1
fi

log_success "找到容器: $CONTAINER_NAME"

# 方案1: 使用root用户安装依赖
install_as_root() {
    log_info "方案1: 使用root用户安装Python依赖..."
    
    # 以root用户执行pip安装
    docker exec -u root "$CONTAINER_NAME" pip install --no-cache-dir \
        flask \
        flask-sqlalchemy \
        flask-jwt-extended \
        flask-cors \
        pymysql \
        redis \
        APScheduler \
        requests \
        beautifulsoup4 \
        python-dotenv \
        gunicorn \
        cryptography \
        Werkzeug
    
    if [ $? -eq 0 ]; then
        log_success "Python依赖安装完成 (root用户)"
        return 0
    else
        log_error "root用户安装失败"
        return 1
    fi
}

# 方案2: 修复权限后安装
fix_permissions_and_install() {
    log_info "方案2: 修复权限后安装依赖..."
    
    # 修复home目录权限
    docker exec -u root "$CONTAINER_NAME" chown -R appuser:appuser /home/appuser 2>/dev/null || {
        log_info "创建appuser用户目录..."
        docker exec -u root "$CONTAINER_NAME" mkdir -p /home/appuser
        docker exec -u root "$CONTAINER_NAME" chown -R appuser:appuser /home/appuser
    }
    
    # 修复Python包目录权限
    docker exec -u root "$CONTAINER_NAME" chown -R appuser:appuser /usr/local/lib/python*/site-packages 2>/dev/null || true
    
    # 以appuser用户安装
    docker exec -u appuser "$CONTAINER_NAME" pip install --user --no-cache-dir \
        flask \
        flask-sqlalchemy \
        flask-jwt-extended \
        flask-cors \
        pymysql \
        redis \
        APScheduler \
        requests \
        beautifulsoup4 \
        python-dotenv \
        gunicorn \
        cryptography \
        Werkzeug
    
    if [ $? -eq 0 ]; then
        log_success "Python依赖安装完成 (用户目录)"
        return 0
    else
        log_error "用户目录安装失败"
        return 1
    fi
}

# 方案3: 使用系统级安装
system_level_install() {
    log_info "方案3: 系统级安装..."
    
    # 使用--break-system-packages参数强制安装
    docker exec -u root "$CONTAINER_NAME" pip install --break-system-packages --no-cache-dir \
        flask \
        flask-sqlalchemy \
        flask-jwt-extended \
        flask-cors \
        pymysql \
        redis \
        APScheduler \
        requests \
        beautifulsoup4 \
        python-dotenv \
        gunicorn \
        cryptography \
        Werkzeug
    
    if [ $? -eq 0 ]; then
        log_success "Python依赖安装完成 (系统级)"
        return 0
    else
        log_error "系统级安装失败"
        return 1
    fi
}

# 测试Python模块导入
test_python_imports() {
    log_info "测试Python模块导入..."
    
    docker exec "$CONTAINER_NAME" python -c "
import sys
print('Python版本:', sys.version)
print('Python路径:', sys.path)
print()

modules = ['flask', 'pymysql', 'redis', 'flask_sqlalchemy', 'flask_jwt_extended', 'flask_cors']
failed_modules = []

for module in modules:
    try:
        __import__(module)
        print(f'✅ {module}: OK')
    except ImportError as e:
        print(f'❌ {module}: FAILED - {e}')
        failed_modules.append(module)

if failed_modules:
    print(f'\\n失败的模块: {failed_modules}')
    exit(1)
else:
    print('\\n🎉 所有模块导入成功!')
"
    
    if [ $? -eq 0 ]; then
        log_success "所有Python模块导入正常"
        return 0
    else
        log_error "部分Python模块导入失败"
        return 1
    fi
}

# 测试Flask应用启动
test_flask_app() {
    log_info "测试Flask应用启动..."
    
    log_info "尝试启动应用 (5秒测试)..."
    timeout 5 docker exec "$CONTAINER_NAME" bash -c "cd /app && python run_backend.py" 2>&1 | head -10 || {
        log_info "启动测试完成"
    }
    
    # 检查应用是否能创建
    docker exec "$CONTAINER_NAME" python -c "
import sys
sys.path.insert(0, '/app')
try:
    from backend.app import create_app
    app = create_app()
    print('✅ Flask应用创建成功')
except Exception as e:
    print(f'❌ Flask应用创建失败: {e}')
    exit(1)
"
    
    if [ $? -eq 0 ]; then
        log_success "Flask应用可以正常创建"
        return 0
    else
        log_error "Flask应用创建失败"
        return 1
    fi
}

# 重启容器并验证
restart_and_verify() {
    log_info "重启容器并验证..."
    
    log_info "重启容器..."
    docker restart "$CONTAINER_NAME"
    
    log_info "等待容器启动 (15秒)..."
    sleep 15
    
    # 检查容器状态
    if docker ps --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
        log_success "容器重启成功"
    else
        log_error "容器重启失败"
        return 1
    fi
    
    # 等待应用启动
    log_info "等待应用启动 (10秒)..."
    sleep 10
    
    # 测试API
    log_info "测试API响应..."
    api_response=$(docker exec "$CONTAINER_NAME" curl -s -m 5 "http://localhost:5000/api/health" 2>/dev/null || echo "failed")
    
    if [ "$api_response" != "failed" ] && [ -n "$api_response" ]; then
        log_success "API响应正常: $api_response"
    else
        log_warning "API无响应，查看容器日志:"
        docker logs "$CONTAINER_NAME" --tail 10
    fi
    
    # 测试外部访问
    external_response=$(curl -s -m 5 "http://localhost:5013/api/health" 2>/dev/null || echo "failed")
    if [ "$external_response" != "failed" ] && [ -n "$external_response" ]; then
        log_success "外部API访问正常: $external_response"
    else
        log_warning "外部API访问失败"
    fi
}

# 主函数
main() {
    log_info "开始修复容器权限并安装依赖..."
    
    # 尝试不同的安装方案
    if install_as_root; then
        log_success "方案1成功: root用户安装"
    elif fix_permissions_and_install; then
        log_success "方案2成功: 权限修复后安装"
    elif system_level_install; then
        log_success "方案3成功: 系统级安装"
    else
        log_error "所有安装方案都失败了"
        exit 1
    fi
    
    # 测试导入
    if ! test_python_imports; then
        log_error "模块导入测试失败"
        exit 1
    fi
    
    # 测试Flask应用
    if ! test_flask_app; then
        log_warning "Flask应用测试失败，但继续重启容器"
    fi
    
    # 重启并验证
    restart_and_verify
    
    echo "==========================================="
    echo "           修复完成"
    echo "==========================================="
    echo "权限问题已修复，Python依赖已安装"
    echo "请测试API功能: curl http://localhost:5013/api/health"
}

# 运行主函数
main "$@"