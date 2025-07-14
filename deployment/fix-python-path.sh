#!/bin/bash

# 修复Python模块路径问题
# 将依赖安装到系统路径而不是用户目录

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
echo "    🐍 Python模块路径修复工具"
echo "==========================================="
echo

# 检查容器是否存在
if ! docker ps --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
    log_error "容器 $CONTAINER_NAME 不存在或未运行"
    exit 1
fi

log_success "找到容器: $CONTAINER_NAME"

# 检查当前状态
check_current_status() {
    log_info "1. 检查当前Python环境..."
    
    echo "Python版本和路径:"
    docker exec "$CONTAINER_NAME" python -c "
import sys
print('Python版本:', sys.version)
print('Python路径:')
for path in sys.path:
    print(f'  {path}')
"
    
    echo
    echo "当前用户:"
    docker exec "$CONTAINER_NAME" whoami
    
    echo
    echo "已安装包的位置:"
    docker exec -u root "$CONTAINER_NAME" find /usr/local/lib /root/.local -name "flask*" -type d 2>/dev/null | head -10
}

# 安装到系统路径
install_to_system_path() {
    log_info "2. 安装Python依赖到系统路径..."
    
    # 使用--system-site-packages和--target参数安装到系统路径
    docker exec -u root "$CONTAINER_NAME" pip install --target /usr/local/lib/python3.11/site-packages \
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
        log_success "系统路径安装完成"
    else
        log_error "系统路径安装失败"
        return 1
    fi
}

# 清理用户安装的包
cleanup_user_packages() {
    log_info "3. 清理用户目录中的包..."
    
    # 删除root用户目录中的包
    docker exec -u root "$CONTAINER_NAME" rm -rf /root/.local/lib/python3.11/site-packages/* 2>/dev/null || true
    
    log_success "用户目录清理完成"
}

# 修复包路径权限
fix_package_permissions() {
    log_info "4. 修复包路径权限..."
    
    # 确保所有用户都能读取系统包
    docker exec -u root "$CONTAINER_NAME" chmod -R 755 /usr/local/lib/python3.11/site-packages
    
    log_success "权限修复完成"
}

# 测试模块导入
test_module_import() {
    log_info "5. 测试模块导入..."
    
    docker exec "$CONTAINER_NAME" python -c "
import sys
print('当前Python路径:')
for path in sys.path:
    print(f'  {path}')
print()

modules = ['flask', 'pymysql', 'redis', 'flask_sqlalchemy', 'flask_jwt_extended', 'flask_cors']
failed_modules = []

for module in modules:
    try:
        mod = __import__(module)
        print(f'✅ {module}: OK (位置: {mod.__file__ if hasattr(mod, \"__file__\") else \"内置模块\"})')
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

# 测试Flask应用
test_flask_application() {
    log_info "6. 测试Flask应用..."
    
    # 测试应用创建
    docker exec "$CONTAINER_NAME" python -c "
import sys
sys.path.insert(0, '/app')
try:
    from backend.app import create_app
    app = create_app()
    print('✅ Flask应用创建成功')
    print(f'应用名称: {app.name}')
except Exception as e:
    print(f'❌ Flask应用创建失败: {e}')
    import traceback
    traceback.print_exc()
    exit(1)
"
    
    if [ $? -eq 0 ]; then
        log_success "Flask应用创建正常"
    else
        log_error "Flask应用创建失败"
        return 1
    fi
}

# 手动启动测试
manual_start_test() {
    log_info "7. 手动启动测试..."
    
    log_info "尝试启动Flask应用 (8秒测试)..."
    timeout 8 docker exec "$CONTAINER_NAME" bash -c "cd /app && python run_backend.py" || {
        log_info "手动启动测试完成"
    }
}

# 重启容器并验证
restart_and_verify() {
    log_info "8. 重启容器并验证..."
    
    log_info "重启容器..."
    docker restart "$CONTAINER_NAME"
    
    log_info "等待容器启动 (20秒)..."
    sleep 20
    
    # 检查容器状态
    if docker ps --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
        log_success "容器重启成功"
    else
        log_error "容器重启失败"
        return 1
    fi
    
    # 等待应用启动
    log_info "等待应用完全启动 (15秒)..."
    sleep 15
    
    # 测试API
    log_info "测试API响应..."
    api_response=$(docker exec "$CONTAINER_NAME" curl -s -m 5 "http://localhost:5000/api/health" 2>/dev/null || echo "failed")
    
    if [ "$api_response" != "failed" ] && [ -n "$api_response" ]; then
        log_success "容器内API响应正常: $api_response"
    else
        log_warning "容器内API无响应"
    fi
    
    # 测试外部访问
    external_response=$(curl -s -m 5 "http://localhost:5013/api/health" 2>/dev/null || echo "failed")
    if [ "$external_response" != "failed" ] && [ -n "$external_response" ]; then
        log_success "外部API访问正常: $external_response"
    else
        log_warning "外部API访问失败"
    fi
    
    # 显示容器日志
    echo
    log_info "容器启动日志 (最后15行):"
    docker logs "$CONTAINER_NAME" --tail 15
}

# 提供后续建议
provide_suggestions() {
    echo
    log_info "9. 后续建议..."
    echo
    echo "🎯 如果API仍然无响应，请检查:"
    echo "1. 数据库连接: docker logs $CONTAINER_NAME | grep -i mysql"
    echo "2. Redis连接: docker logs $CONTAINER_NAME | grep -i redis"
    echo "3. 应用启动: docker exec $CONTAINER_NAME ps aux | grep python"
    echo "4. 手动启动: docker exec -it $CONTAINER_NAME bash"
    echo "                cd /app && python run_backend.py"
    echo
    echo "🔧 测试命令:"
    echo "curl http://localhost:5013/api/health"
    echo "./backend-service-test.sh"
    echo
}

# 主函数
main() {
    check_current_status
    
    if ! install_to_system_path; then
        log_error "系统路径安装失败"
        exit 1
    fi
    
    cleanup_user_packages
    fix_package_permissions
    
    if ! test_module_import; then
        log_error "模块导入测试失败"
        exit 1
    fi
    
    if ! test_flask_application; then
        log_warning "Flask应用测试失败，但继续重启容器"
    fi
    
    manual_start_test
    restart_and_verify
    provide_suggestions
    
    echo "==========================================="
    echo "           修复完成"
    echo "==========================================="
    echo "Python模块路径已修复，请测试API功能"
}

# 运行主函数
main "$@"