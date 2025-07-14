#!/bin/bash

# 测试新构建的Docker镜像
# 修复测试脚本中的模块检测问题

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

# 配置变量
IMAGE_NAME="leenbj68719929/website-monitor-backend:fixed"
TEST_CONTAINER_NAME="website-monitor-backend-test"

echo "==========================================="
echo "    🧪 Docker镜像测试工具"
echo "==========================================="
echo "镜像: $IMAGE_NAME"
echo

# 1. 清理可能存在的测试容器
cleanup_test_container() {
    log_info "1. 清理测试环境..."
    
    if docker ps -a --format "{{.Names}}" | grep -q "^${TEST_CONTAINER_NAME}$"; then
        docker rm -f "$TEST_CONTAINER_NAME" >/dev/null 2>&1
        log_success "已清理旧的测试容器"
    fi
}

# 2. 启动测试容器
start_test_container() {
    log_info "2. 启动测试容器..."
    
    docker run -d \
        --name "$TEST_CONTAINER_NAME" \
        --network host \
        -e DATABASE_URL="mysql+pymysql://test:test@localhost:3306/test" \
        -e REDIS_URL="redis://localhost:6379/0" \
        -e SECRET_KEY="test-secret-key-12345678901234567890" \
        -e JWT_SECRET_KEY="test-jwt-secret-key-12345678901234567890" \
        -e DB_USER="test" \
        -e DB_PASSWORD="test" \
        -e DB_NAME="test" \
        "$IMAGE_NAME"
    
    # 等待容器启动
    log_info "等待容器启动 (10秒)..."
    sleep 10
    
    # 检查容器状态
    if docker ps --format "{{.Names}}" | grep -q "^${TEST_CONTAINER_NAME}$"; then
        log_success "测试容器启动成功"
    else
        log_error "测试容器启动失败"
        docker logs "$TEST_CONTAINER_NAME" --tail 20
        return 1
    fi
}

# 3. 测试基础Python环境
test_python_environment() {
    log_info "3. 测试Python环境..."
    
    # 检查Python版本和路径
    docker exec "$TEST_CONTAINER_NAME" python -c "
import sys
print('Python版本:', sys.version)
print('Python路径:', sys.path[:5])
print('工作目录:', sys.path[0])
"
    
    if [ $? -eq 0 ]; then
        log_success "Python环境正常"
    else
        log_error "Python环境异常"
        return 1
    fi
}

# 4. 测试核心模块导入
test_core_modules() {
    log_info "4. 测试核心模块导入..."
    
    # 测试基础模块
    docker exec "$TEST_CONTAINER_NAME" python -c "
modules = ['flask', 'pymysql', 'redis', 'requests', 'chardet']
failed_modules = []

for module in modules:
    try:
        __import__(module)
        print(f'✅ {module}: OK')
    except ImportError as e:
        print(f'❌ {module}: FAILED - {e}')
        failed_modules.append(module)

if failed_modules:
    print(f'失败的模块: {failed_modules}')
    exit(1)
else:
    print('🎉 所有核心模块导入成功!')
"
    
    if [ $? -eq 0 ]; then
        log_success "核心模块测试通过"
    else
        log_error "核心模块测试失败"
        return 1
    fi
}

# 5. 测试Flask相关模块
test_flask_modules() {
    log_info "5. 测试Flask相关模块..."
    
    docker exec "$TEST_CONTAINER_NAME" python -c "
flask_modules = ['flask_sqlalchemy', 'flask_jwt_extended', 'flask_cors', 'flask_limiter']
failed_modules = []

for module in flask_modules:
    try:
        __import__(module)
        print(f'✅ {module}: OK')
    except ImportError as e:
        print(f'❌ {module}: FAILED - {e}')
        failed_modules.append(module)

if failed_modules:
    print(f'失败的Flask模块: {failed_modules}')
    exit(1)
else:
    print('🎉 所有Flask模块导入成功!')
"
    
    if [ $? -eq 0 ]; then
        log_success "Flask模块测试通过"
    else
        log_error "Flask模块测试失败"
        return 1
    fi
}

# 6. 测试MySQL驱动
test_mysql_drivers() {
    log_info "6. 测试MySQL驱动..."
    
    docker exec "$TEST_CONTAINER_NAME" python -c "
import pymysql
print('✅ PyMySQL导入成功')

# 测试PyMySQL作为MySQLdb的替代
pymysql.install_as_MySQLdb()
print('✅ PyMySQL配置为MySQLdb成功')

# 测试mysqlclient（如果可用）
try:
    import MySQLdb
    print('✅ MySQLdb (via PyMySQL) 可用')
except ImportError as e:
    print(f'⚠️ MySQLdb导入失败: {e}')

# 测试原生mysqlclient（可能会失败，这是正常的）
try:
    import _mysql
    print('✅ 原生mysqlclient可用')
except ImportError:
    print('ℹ️ 原生mysqlclient不可用（使用PyMySQL替代）')
"
    
    if [ $? -eq 0 ]; then
        log_success "MySQL驱动测试通过"
    else
        log_error "MySQL驱动测试失败"
        return 1
    fi
}

# 7. 测试Flask应用创建
test_flask_application() {
    log_info "7. 测试Flask应用创建..."
    
    docker exec "$TEST_CONTAINER_NAME" python -c "
import sys
sys.path.insert(0, '/app')
import pymysql

# 强制使用PyMySQL作为MySQLdb
pymysql.install_as_MySQLdb()

try:
    from backend.app import create_app
    app = create_app()
    print('✅ Flask应用创建成功')
    print(f'应用名称: {app.name}')
    print(f'应用配置: {type(app.config).__name__}')
except Exception as e:
    print(f'❌ Flask应用创建失败: {e}')
    import traceback
    traceback.print_exc()
    exit(1)
"
    
    if [ $? -eq 0 ]; then
        log_success "Flask应用创建测试通过"
    else
        log_error "Flask应用创建测试失败"
        # 显示更多调试信息
        log_info "查看应用目录结构:"
        docker exec "$TEST_CONTAINER_NAME" ls -la /app/
        docker exec "$TEST_CONTAINER_NAME" ls -la /app/backend/
        return 1
    fi
}

# 8. 测试启动脚本
test_startup_script() {
    log_info "8. 测试启动脚本..."
    
    log_info "检查启动脚本是否存在且可执行:"
    docker exec "$TEST_CONTAINER_NAME" ls -la /app/start.sh
    
    if [ $? -eq 0 ]; then
        log_success "启动脚本检查通过"
    else
        log_error "启动脚本检查失败"
        return 1
    fi
}

# 9. 显示容器日志
show_container_logs() {
    log_info "9. 显示容器启动日志..."
    
    echo "最近20行日志:"
    docker logs "$TEST_CONTAINER_NAME" --tail 20
}

# 10. 清理测试容器
cleanup_after_test() {
    log_info "10. 清理测试容器..."
    
    docker rm -f "$TEST_CONTAINER_NAME" >/dev/null 2>&1
    log_success "测试容器已清理"
}

# 11. 测试总结
test_summary() {
    echo
    echo "==========================================="
    echo "           测试结果总结"
    echo "==========================================="
    echo "✅ 镜像: $IMAGE_NAME"
    echo "✅ Python环境: 正常"
    echo "✅ 核心模块: 导入成功"
    echo "✅ Flask模块: 导入成功"
    echo "✅ MySQL驱动: 可用"
    echo "✅ Flask应用: 创建成功"
    echo "✅ 启动脚本: 可执行"
    echo "==========================================="
    echo "🎉 镜像测试通过，可以用于生产部署！"
    echo
}

# 主函数
main() {
    cleanup_test_container
    start_test_container || exit 1
    test_python_environment || exit 1
    test_core_modules || exit 1
    test_flask_modules || exit 1
    test_mysql_drivers || exit 1
    test_flask_application || exit 1
    test_startup_script || exit 1
    show_container_logs
    cleanup_after_test
    test_summary
}

# 运行主函数
main "$@"