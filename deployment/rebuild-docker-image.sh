#!/bin/bash

# 重新构建Docker镜像脚本
# 解决之前发现的所有依赖和配置问题

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
IMAGE_NAME="leenbj68719929/website-monitor-backend"
IMAGE_TAG="fixed"
CONTAINER_NAME="website-monitor-backend"

echo "==========================================="
echo "    🔨 Docker镜像重新构建工具"
echo "==========================================="
echo "镜像名称: $IMAGE_NAME:$IMAGE_TAG"
echo "容器名称: $CONTAINER_NAME"
echo

# 1. 预构建检查
pre_build_check() {
    log_info "1. 预构建检查..."
    
    # 检查必要文件
    local required_files=(
        "Dockerfile.fixed"
        "requirements.txt.fixed"
        "backend/"
        "run_backend.py"
        "init_database.py"
    )
    
    for file in "${required_files[@]}"; do
        if [ -e "$file" ]; then
            log_success "发现文件: $file"
        else
            log_error "缺少文件: $file"
            return 1
        fi
    done
    
    # 检查Docker是否运行
    if ! docker ps >/dev/null 2>&1; then
        log_error "Docker服务未运行"
        return 1
    fi
    
    log_success "预构建检查通过"
}

# 2. 备份当前配置
backup_current_config() {
    log_info "2. 备份当前配置..."
    
    # 备份原始文件
    if [ -f "Dockerfile" ]; then
        cp Dockerfile Dockerfile.backup.$(date +%Y%m%d_%H%M%S)
        log_success "已备份原始Dockerfile"
    fi
    
    if [ -f "requirements.txt" ]; then
        cp requirements.txt requirements.txt.backup.$(date +%Y%m%d_%H%M%S)
        log_success "已备份原始requirements.txt"
    fi
}

# 3. 应用修复的配置
apply_fixed_configs() {
    log_info "3. 应用修复的配置..."
    
    # 使用修复版的配置文件
    cp Dockerfile.fixed Dockerfile
    cp requirements.txt.fixed requirements.txt
    
    log_success "已应用修复版配置文件"
}

# 4. 停止现有容器
stop_current_container() {
    log_info "4. 停止现有容器..."
    
    if docker ps --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
        log_info "停止容器: $CONTAINER_NAME"
        docker stop "$CONTAINER_NAME"
    fi
    
    if docker ps -a --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
        log_info "删除容器: $CONTAINER_NAME"
        docker rm "$CONTAINER_NAME"
    fi
    
    log_success "容器清理完成"
}

# 5. 构建新镜像
build_new_image() {
    log_info "5. 构建新镜像..."
    
    log_info "开始Docker镜像构建..."
    docker build \
        --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --build-arg VCS_REF="$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')" \
        --build-arg VERSION="fixed-$(date +%Y%m%d)" \
        -t "$IMAGE_NAME:$IMAGE_TAG" \
        -t "$IMAGE_NAME:latest" \
        .
    
    if [ $? -eq 0 ]; then
        log_success "镜像构建成功"
    else
        log_error "镜像构建失败"
        return 1
    fi
}

# 6. 测试新镜像
test_new_image() {
    log_info "6. 测试新镜像..."
    
    # 启动测试容器
    log_info "启动测试容器..."
    docker run -d \
        --name "${CONTAINER_NAME}-test" \
        --network host \
        -e DATABASE_URL="mysql+pymysql://test:test@localhost:3306/test" \
        -e REDIS_URL="redis://localhost:6379/0" \
        -e SECRET_KEY="test-secret-key-12345678901234567890" \
        -e JWT_SECRET_KEY="test-jwt-secret-key-12345678901234567890" \
        "$IMAGE_NAME:$IMAGE_TAG"
    
    # 等待容器启动
    log_info "等待容器启动 (15秒)..."
    sleep 15
    
    # 检查容器状态
    if docker ps --format "{{.Names}}" | grep -q "${CONTAINER_NAME}-test"; then
        log_success "测试容器启动成功"
    else
        log_error "测试容器启动失败"
        docker logs "${CONTAINER_NAME}-test" --tail 20
        return 1
    fi
    
    # 测试Python模块导入
    log_info "测试Python模块导入..."
    docker exec "${CONTAINER_NAME}-test" python -c "
import flask, pymysql, redis, requests, chardet, mysqlclient
import flask_sqlalchemy, flask_jwt_extended, flask_cors
print('✅ 所有关键模块导入成功')
"
    
    if [ $? -eq 0 ]; then
        log_success "Python模块测试通过"
    else
        log_error "Python模块测试失败"
        return 1
    fi
    
    # 测试Flask应用创建
    log_info "测试Flask应用创建..."
    docker exec "${CONTAINER_NAME}-test" python -c "
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
        log_success "Flask应用测试通过"
    else
        log_error "Flask应用测试失败"
        docker logs "${CONTAINER_NAME}-test" --tail 20
        return 1
    fi
    
    # 清理测试容器
    docker stop "${CONTAINER_NAME}-test" >/dev/null 2>&1
    docker rm "${CONTAINER_NAME}-test" >/dev/null 2>&1
    
    log_success "镜像测试完成"
}

# 7. 启动新的生产容器
start_production_container() {
    log_info "7. 启动新的生产容器..."
    
    # 检查是否有docker-compose配置
    if [ -f "docker-compose.backend-only.yml" ]; then
        log_info "使用docker-compose启动服务..."
        
        # 更新docker-compose文件使用新镜像
        sed -i.bak "s|image: leenbj68719929/website-monitor-backend:latest|image: $IMAGE_NAME:$IMAGE_TAG|g" docker-compose.backend-only.yml
        
        # 启动服务
        docker-compose -f docker-compose.backend-only.yml up -d
        
        log_success "docker-compose服务启动完成"
    else
        log_warning "未找到docker-compose配置，跳过自动启动"
    fi
}

# 8. 验证生产部署
verify_production_deployment() {
    log_info "8. 验证生产部署..."
    
    # 等待服务启动
    log_info "等待服务完全启动 (30秒)..."
    sleep 30
    
    # 检查容器状态
    if docker ps --format "{{.Names}}" | grep -q "$CONTAINER_NAME"; then
        log_success "生产容器运行正常"
    else
        log_error "生产容器未运行"
        return 1
    fi
    
    # 测试API响应
    log_info "测试API响应..."
    local max_attempts=10
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if api_response=$(curl -s -m 5 "http://localhost:5013/api/health" 2>/dev/null); then
            if [ -n "$api_response" ] && [ "$api_response" != "failed" ]; then
                log_success "API响应正常: $api_response"
                break
            fi
        fi
        
        attempt=$((attempt + 1))
        log_info "等待API响应... ($attempt/$max_attempts)"
        sleep 5
    done
    
    if [ $attempt -eq $max_attempts ]; then
        log_warning "API响应超时，查看容器日志:"
        docker logs "$CONTAINER_NAME" --tail 20
    fi
    
    # 显示最终状态
    echo
    log_info "最终部署状态:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(NAME|$CONTAINER_NAME|mysql|redis)"
}

# 9. 推送镜像到Docker Hub (可选)
push_to_dockerhub() {
    echo
    read -p "是否推送镜像到Docker Hub? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "推送镜像到Docker Hub..."
        
        docker push "$IMAGE_NAME:$IMAGE_TAG"
        docker push "$IMAGE_NAME:latest"
        
        if [ $? -eq 0 ]; then
            log_success "镜像推送成功"
        else
            log_error "镜像推送失败"
        fi
    else
        log_info "跳过镜像推送"
    fi
}

# 10. 清理和总结
cleanup_and_summary() {
    log_info "10. 清理和总结..."
    
    # 清理旧镜像 (可选)
    echo
    read -p "是否清理未使用的Docker镜像? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker image prune -f
        log_success "已清理未使用的镜像"
    fi
    
    echo
    echo "==========================================="
    echo "           构建完成总结"
    echo "==========================================="
    echo "✅ 新镜像: $IMAGE_NAME:$IMAGE_TAG"
    echo "✅ 容器状态: $(docker ps --format "{{.Status}}" --filter "name=$CONTAINER_NAME")"
    echo "✅ 测试命令:"
    echo "   curl http://localhost:5013/api/health"
    echo "   ./backend-service-test.sh"
    echo "==========================================="
}

# 主函数
main() {
    # 切换到项目根目录
    cd "$(dirname "$0")/.."
    
    pre_build_check || exit 1
    backup_current_config
    apply_fixed_configs
    stop_current_container
    build_new_image || exit 1
    test_new_image || exit 1
    start_production_container
    verify_production_deployment
    push_to_dockerhub
    cleanup_and_summary
    
    echo "🎉 Docker镜像重构完成！"
}

# 运行主函数
main "$@"