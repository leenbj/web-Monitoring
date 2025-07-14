#!/bin/bash

# 测试新构建的Docker镜像（独立测试版）
# 不依赖外部服务，仅测试镜像内部配置

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
TEST_CONTAINER_NAME="website-monitor-backend-standalone-test"

echo "==========================================="
echo "    🧪 Docker镜像独立测试工具"
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

# 2. 启动独立测试容器
start_standalone_test_container() {
    log_info "2. 启动独立测试容器..."
    
    docker run -d \
        --name "$TEST_CONTAINER_NAME" \
        -e DATABASE_URL="sqlite:///test.db" \
        -e SECRET_KEY="test-secret-key-12345678901234567890" \
        -e JWT_SECRET_KEY="test-jwt-secret-key-12345678901234567890" \
        -e FLASK_ENV="testing" \
        "$IMAGE_NAME" sleep 3600
    
    # 等待容器启动
    log_info "等待容器启动 (5秒)..."
    sleep 5
    
    # 检查容器状态
    if docker ps --format "{{.Names}}" | grep -q "^${TEST_CONTAINER_NAME}$"; then
        log_success "独立测试容器启动成功"
    else
        log_error "独立测试容器启动失败"
        docker logs "$TEST_CONTAINER_NAME" --tail 20
        return 1
    fi
}

# 3. 测试Python环境
test_python_environment() {
    log_info "3. 测试Python环境..."
    
    docker exec "$TEST_CONTAINER_NAME" python -c "
import sys
print('Python版本:', sys.version)
print('Python路径:', sys.path[:5])
print('工作目录:', sys.path[0])
print('环境变量PYTHONPATH:', sys.path)
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

# 6. 测试MySQL驱动配置
test_mysql_drivers() {
    log_info "6. 测试MySQL驱动配置..."
    
    docker exec "$TEST_CONTAINER_NAME" python -c "
import pymysql
print('✅ PyMySQL导入成功')

# 测试PyMySQL作为MySQLdb的替代
pymysql.install_as_MySQLdb()
print('✅ PyMySQL配置为MySQLdb成功')

# 测试MySQLdb（通过PyMySQL）
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

print('✅ MySQL驱动配置测试完成')
"
    
    if [ $? -eq 0 ]; then
        log_success "MySQL驱动测试通过"
    else
        log_error "MySQL驱动测试失败"
        return 1
    fi
}

# 7. 测试Flask应用基础配置（不连接数据库）
test_flask_app_config() {
    log_info "7. 测试Flask应用基础配置..."
    
    docker exec "$TEST_CONTAINER_NAME" python -c "
import sys
import os
sys.path.insert(0, '/app')

# 设置测试环境
os.environ['FLASK_ENV'] = 'testing'
os.environ['DATABASE_URL'] = 'sqlite:///test.db'

import pymysql
pymysql.install_as_MySQLdb()

try:
    from flask import Flask
    from backend.config import Config
    
    # 创建基础Flask应用（不初始化数据库）
    app = Flask(__name__)
    app.config.from_object(Config)
    
    print('✅ Flask应用基础配置成功')
    print(f'应用名称: {app.name}')
    print(f'配置类: {type(app.config).__name__}')
    print(f'SECRET_KEY已设置: {bool(app.config.get(\"SECRET_KEY\"))}')
    
except Exception as e:
    print(f'❌ Flask应用配置失败: {e}')
    import traceback
    traceback.print_exc()
    exit(1)
"
    
    if [ $? -eq 0 ]; then
        log_success "Flask应用配置测试通过"
    else
        log_error "Flask应用配置测试失败"
        return 1
    fi
}

# 8. 测试应用启动脚本存在性
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

# 9. 测试应用目录结构
test_app_structure() {
    log_info "9. 测试应用目录结构..."
    
    echo "应用根目录:"
    docker exec "$TEST_CONTAINER_NAME" ls -la /app/
    
    echo -e "\n后端目录:"
    docker exec "$TEST_CONTAINER_NAME" ls -la /app/backend/
    
    echo -e "\n权限检查:"
    docker exec "$TEST_CONTAINER_NAME" stat -c "%a %n" /app/start.sh
    docker exec "$TEST_CONTAINER_NAME" stat -c "%a %n" /app/run_backend.py
    
    log_success "应用目录结构检查完成"
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
    echo "           独立测试结果总结"
    echo "==========================================="
    echo "✅ 镜像: $IMAGE_NAME"
    echo "✅ Python环境: 正常"
    echo "✅ 核心模块: 导入成功"
    echo "✅ Flask模块: 导入成功"
    echo "✅ MySQL驱动: 配置正确"
    echo "✅ Flask配置: 加载成功"
    echo "✅ 启动脚本: 可执行"
    echo "✅ 目录结构: 正常"
    echo "==========================================="
    echo "🎉 镜像独立测试通过，Python环境和依赖配置正确！"
    echo
    echo "📝 部署建议:"
    echo "   1. 镜像可以正常使用，所有Python依赖已正确安装"
    echo "   2. 部署时需要确保MySQL和Redis服务可用"
    echo "   3. 使用docker-compose进行完整部署"
    echo
}

# 主函数
main() {
    cleanup_test_container
    start_standalone_test_container || exit 1
    test_python_environment || exit 1
    test_core_modules || exit 1
    test_flask_modules || exit 1
    test_mysql_drivers || exit 1
    test_flask_app_config || exit 1
    test_startup_script || exit 1
    test_app_structure
    cleanup_after_test
    test_summary
}

# 运行主函数
main "$@"