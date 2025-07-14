#!/bin/bash

# 修复MySQL连接问题
# 解决 No module named 'MySQLdb' 错误

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
echo "    🗄️ MySQL连接问题修复工具"
echo "==========================================="
echo

# 检查容器是否存在
if ! docker ps --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
    log_error "容器 $CONTAINER_NAME 不存在或未运行"
    exit 1
fi

log_success "找到容器: $CONTAINER_NAME"

# 1. 检查当前问题
check_current_issue() {
    log_info "1. 检查当前MySQL连接问题..."
    
    echo "测试PyMySQL导入:"
    docker exec "$CONTAINER_NAME" python -c "
try:
    import pymysql
    print('✅ PyMySQL导入成功')
except ImportError as e:
    print(f'❌ PyMySQL导入失败: {e}')
"
    
    echo
    echo "测试MySQLdb导入:"
    docker exec "$CONTAINER_NAME" python -c "
try:
    import MySQLdb
    print('✅ MySQLdb导入成功')
except ImportError as e:
    print(f'❌ MySQLdb导入失败: {e}')
"
    
    echo
    echo "检查数据库URL配置:"
    docker exec "$CONTAINER_NAME" env | grep DATABASE_URL
}

# 2. 安装MySQL客户端依赖
install_mysql_dependencies() {
    log_info "2. 安装MySQL客户端依赖..."
    
    # 方案A: 安装mysqlclient (推荐)
    log_info "方案A: 安装mysqlclient..."
    docker exec -u root "$CONTAINER_NAME" apt-get update
    docker exec -u root "$CONTAINER_NAME" apt-get install -y default-libmysqlclient-dev pkg-config gcc
    docker exec -u root "$CONTAINER_NAME" pip install --target /usr/local/lib/python3.11/site-packages mysqlclient
    
    if [ $? -eq 0 ]; then
        log_success "mysqlclient安装成功"
        return 0
    fi
    
    # 方案B: 如果mysqlclient失败，尝试mysql-connector-python
    log_warning "mysqlclient安装失败，尝试mysql-connector-python..."
    docker exec -u root "$CONTAINER_NAME" pip install --target /usr/local/lib/python3.11/site-packages mysql-connector-python
    
    if [ $? -eq 0 ]; then
        log_success "mysql-connector-python安装成功"
        return 0
    fi
    
    log_error "所有MySQL驱动安装失败"
    return 1
}

# 3. 修改数据库配置使用PyMySQL
configure_pymysql() {
    log_info "3. 配置应用使用PyMySQL..."
    
    # 检查数据库配置文件
    log_info "检查数据库配置..."
    docker exec "$CONTAINER_NAME" find /app -name "*.py" -exec grep -l "MySQLdb\|mysql://" {} \; 2>/dev/null | head -5
    
    # 修改数据库URL使用pymysql驱动
    log_info "修改数据库URL使用pymysql驱动..."
    docker exec "$CONTAINER_NAME" bash -c "
        cd /app
        # 查找并替换数据库URL
        find . -name '*.py' -exec sed -i 's/mysql:\\/\\//mysql+pymysql:\\/\\//g' {} \\;
        
        # 在app初始化时添加pymysql.install_as_MySQLdb()
        if [ -f backend/app.py ]; then
            # 检查是否已经添加了pymysql配置
            if ! grep -q 'pymysql.install_as_MySQLdb' backend/app.py; then
                # 在imports后添加pymysql配置
                sed -i '1i import pymysql\\npymysql.install_as_MySQLdb()\\n' backend/app.py
            fi
        fi
        
        # 同样处理database.py
        if [ -f backend/database.py ]; then
            if ! grep -q 'pymysql.install_as_MySQLdb' backend/database.py; then
                sed -i '1i import pymysql\\npymysql.install_as_MySQLdb()\\n' backend/database.py
            fi
        fi
    "
    
    log_success "PyMySQL配置完成"
}

# 4. 修复环境变量配置
fix_database_url() {
    log_info "4. 修复数据库URL配置..."
    
    # 获取当前数据库URL
    current_url=$(docker exec "$CONTAINER_NAME" env | grep DATABASE_URL | cut -d'=' -f2-)
    echo "当前数据库URL: $current_url"
    
    # 如果URL不包含pymysql，则修改
    if [[ "$current_url" =~ mysql:// ]] && [[ ! "$current_url" =~ mysql+pymysql:// ]]; then
        log_info "修改数据库URL使用pymysql驱动..."
        new_url=$(echo "$current_url" | sed 's/mysql:/mysql+pymysql:/')
        echo "新的数据库URL: $new_url"
        
        # 更新容器环境变量（临时）
        docker exec "$CONTAINER_NAME" bash -c "export DATABASE_URL='$new_url'"
    fi
}

# 5. 测试数据库连接
test_database_connection() {
    log_info "5. 测试数据库连接..."
    
    # 测试PyMySQL连接
    docker exec "$CONTAINER_NAME" python -c "
import pymysql
import os

# 强制使用pymysql作为MySQLdb
pymysql.install_as_MySQLdb()

try:
    # 测试直接连接
    connection = pymysql.connect(
        host='mysql',
        user=os.getenv('DB_USER', 'monitor_user'),
        password=os.getenv('DB_PASSWORD', 'Monitor123!@#'),
        database=os.getenv('DB_NAME', 'website_monitor'),
        charset='utf8mb4'
    )
    print('✅ PyMySQL直接连接成功')
    connection.close()
except Exception as e:
    print(f'❌ PyMySQL连接失败: {e}')

# 测试SQLAlchemy连接
try:
    from sqlalchemy import create_engine
    
    # 构建连接字符串
    db_user = os.getenv('DB_USER', 'monitor_user')
    db_password = os.getenv('DB_PASSWORD', 'Monitor123!@#')
    db_name = os.getenv('DB_NAME', 'website_monitor')
    
    # 使用pymysql驱动
    engine = create_engine(f'mysql+pymysql://{db_user}:{db_password}@mysql:3306/{db_name}')
    
    # 测试连接
    with engine.connect() as conn:
        result = conn.execute('SELECT 1')
        print('✅ SQLAlchemy+PyMySQL连接成功')
        
except Exception as e:
    print(f'❌ SQLAlchemy连接失败: {e}')
"
    
    if [ $? -eq 0 ]; then
        log_success "数据库连接测试完成"
    else
        log_warning "数据库连接测试部分失败"
    fi
}

# 6. 测试Flask应用启动
test_flask_startup() {
    log_info "6. 测试Flask应用启动..."
    
    log_info "尝试创建Flask应用..."
    docker exec "$CONTAINER_NAME" python -c "
import sys
sys.path.insert(0, '/app')
import pymysql
pymysql.install_as_MySQLdb()

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
        log_success "Flask应用创建成功"
    else
        log_error "Flask应用创建失败"
        return 1
    fi
}

# 7. 手动启动测试
manual_startup_test() {
    log_info "7. 手动启动测试..."
    
    log_info "尝试启动Flask应用 (10秒测试)..."
    timeout 10 docker exec "$CONTAINER_NAME" bash -c "
        cd /app
        export PYTHONPATH=/app
        python run_backend.py
    " || {
        log_info "手动启动测试完成"
    }
}

# 8. 重启容器并验证
restart_and_verify() {
    log_info "8. 重启容器并验证..."
    
    log_info "重启容器..."
    docker restart "$CONTAINER_NAME"
    
    log_info "等待容器启动 (25秒)..."
    sleep 25
    
    # 检查容器状态
    if docker ps --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
        log_success "容器重启成功"
    else
        log_error "容器重启失败"
        return 1
    fi
    
    # 等待应用启动
    log_info "等待应用完全启动 (20秒)..."
    sleep 20
    
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
    log_info "容器启动日志 (最后20行):"
    docker logs "$CONTAINER_NAME" --tail 20
}

# 9. 提供后续建议
provide_final_suggestions() {
    echo
    log_info "9. 最终建议..."
    echo
    echo "🎯 如果问题仍然存在:"
    echo "1. 检查MySQL容器状态: docker ps | grep mysql"
    echo "2. 检查网络连接: docker exec $CONTAINER_NAME ping mysql -c 3"
    echo "3. 手动调试: docker exec -it $CONTAINER_NAME bash"
    echo "4. 查看详细日志: docker logs $CONTAINER_NAME -f"
    echo
    echo "🔧 测试命令:"
    echo "curl http://localhost:5013/api/health"
    echo "./backend-service-test.sh"
    echo
    echo "📝 如果需要重新部署:"
    echo "docker-compose -f docker-compose.backend-only.yml down"
    echo "docker-compose -f docker-compose.backend-only.yml up -d"
}

# 主函数
main() {
    check_current_issue
    
    if ! install_mysql_dependencies; then
        log_warning "MySQL依赖安装失败，尝试配置PyMySQL..."
    fi
    
    configure_pymysql
    fix_database_url
    test_database_connection
    
    if ! test_flask_startup; then
        log_warning "Flask应用测试失败，但继续重启容器"
    fi
    
    manual_startup_test
    restart_and_verify
    provide_final_suggestions
    
    echo "==========================================="
    echo "           MySQL连接修复完成"
    echo "==========================================="
    echo "请测试API功能和数据库连接"
}

# 运行主函数
main "$@"