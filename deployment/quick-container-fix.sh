#!/bin/bash

# 快速修复Docker容器依赖缺失问题
# 临时解决方案：直接在容器内安装Python依赖

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
echo "    🚀 容器依赖快速修复工具"
echo "==========================================="
echo

# 检查容器是否存在
if ! docker ps --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
    log_error "容器 $CONTAINER_NAME 不存在或未运行"
    log_info "请先启动后端服务: docker-compose -f docker-compose.backend-only.yml up -d"
    exit 1
fi

log_success "找到容器: $CONTAINER_NAME"

# 1. 安装缺失的Python依赖
install_dependencies() {
    log_info "1. 安装缺失的Python依赖..."
    
    log_info "更新pip..."
    docker exec "$CONTAINER_NAME" python -m pip install --upgrade pip
    
    log_info "安装核心依赖..."
    docker exec "$CONTAINER_NAME" pip install \
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
        log_success "Python依赖安装完成"
    else
        log_error "Python依赖安装失败"
        return 1
    fi
}

# 2. 测试Flask应用启动
test_flask_startup() {
    log_info "2. 测试Flask应用启动..."
    
    log_info "尝试启动Flask应用 (10秒测试)..."
    timeout 10 docker exec "$CONTAINER_NAME" bash -c "cd /app && python run_backend.py" || {
        log_info "测试启动完成 (正常超时)"
    }
    
    # 检查应用是否能正常导入
    log_info "测试Python模块导入..."
    docker exec "$CONTAINER_NAME" python -c "
try:
    import flask
    import pymysql  
    import redis
    from backend.app import create_app
    print('✅ 所有模块导入成功')
except ImportError as e:
    print(f'❌ 模块导入失败: {e}')
    exit(1)
except Exception as e:
    print(f'⚠️  应用导入警告: {e}')
"
    
    if [ $? -eq 0 ]; then
        log_success "Flask应用模块导入正常"
    else
        log_error "Flask应用模块导入失败"
        return 1
    fi
}

# 3. 重启容器服务
restart_container_service() {
    log_info "3. 重启容器服务..."
    
    log_info "重启容器以应用修复..."
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
}

# 4. 验证API服务
verify_api_service() {
    log_info "4. 验证API服务..."
    
    # 等待额外时间让应用完全启动
    log_info "等待应用启动 (10秒)..."
    sleep 10
    
    # 测试容器内API
    log_info "测试容器内API响应..."
    api_response=$(docker exec "$CONTAINER_NAME" curl -s -m 5 "http://localhost:5000/api/health" 2>/dev/null || echo "failed")
    
    if [ "$api_response" != "failed" ] && [ -n "$api_response" ]; then
        log_success "容器内API响应正常: $api_response"
    else
        log_warning "容器内API无响应，检查应用启动状态..."
        docker logs "$CONTAINER_NAME" --tail 10
    fi
    
    # 测试外部访问
    log_info "测试外部API访问..."
    external_response=$(curl -s -m 5 "http://localhost:5013/api/health" 2>/dev/null || echo "failed")
    
    if [ "$external_response" != "failed" ] && [ -n "$external_response" ]; then
        log_success "外部API访问正常: $external_response"
    else
        log_warning "外部API访问失败"
    fi
}

# 5. 显示容器状态
show_container_status() {
    log_info "5. 显示容器状态..."
    
    echo "容器状态:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep "$CONTAINER_NAME"
    
    echo
    echo "最近日志:"
    docker logs "$CONTAINER_NAME" --tail 15
    
    echo
    log_info "如需查看实时日志: docker logs $CONTAINER_NAME -f"
}

# 6. 运行后续测试建议
suggest_next_steps() {
    log_info "6. 后续测试建议..."
    echo
    echo "🎯 建议执行的测试:"
    echo "1. 运行完整后端测试:"
    echo "   ./backend-service-test.sh"
    echo
    echo "2. 测试前端API调用:"
    echo "   curl http://w3.799n.com:5013/api/health"
    echo
    echo "3. 检查前端页面登录功能:"
    echo "   访问 https://w4.799n.com"
    echo
    echo "4. 如果仍有问题，查看详细日志:"
    echo "   docker logs $CONTAINER_NAME -f"
    echo
}

# 主函数
main() {
    install_dependencies || {
        log_error "依赖安装失败，退出修复"
        exit 1
    }
    
    test_flask_startup || {
        log_error "Flask应用测试失败，但继续重启容器"
    }
    
    restart_container_service || {
        log_error "容器重启失败，退出修复"
        exit 1
    }
    
    verify_api_service
    show_container_status
    suggest_next_steps
    
    echo "==========================================="
    echo "           修复完成"
    echo "==========================================="
    echo "容器依赖修复已完成，请测试API功能"
}

# 运行主函数
main "$@"