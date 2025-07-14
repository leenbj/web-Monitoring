#!/bin/bash

# Docker容器内部调试脚本
# 专门用于诊断后端容器内部的API服务问题

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

echo "==========================================="
echo "    🐳 Docker容器内部调试工具"
echo "==========================================="
echo

# 1. 查找后端容器
find_backend_container() {
    log_info "1. 查找后端容器..."
    
    # 尝试不同的容器名称
    local container_names=(
        "website-monitor-backend"
        "website-monitor_backend"
        "backend"
        "website_monitor_backend"
        "monitor-backend"
    )
    
    local found_container=""
    
    for name in "${container_names[@]}"; do
        if docker ps --format "{{.Names}}" | grep -q "^${name}$"; then
            found_container="$name"
            log_success "找到后端容器: $found_container"
            break
        fi
    done
    
    # 如果没找到，尝试通过端口查找
    if [ -z "$found_container" ]; then
        log_warning "未找到标准名称的容器，尝试通过端口查找..."
        found_container=$(docker ps --format "{{.Names}}\t{{.Ports}}" | grep -E "(5013|5000)" | head -1 | cut -f1)
        if [ -n "$found_container" ]; then
            log_success "通过端口找到容器: $found_container"
        fi
    fi
    
    # 如果还是没找到，列出所有容器让用户选择
    if [ -z "$found_container" ]; then
        log_error "无法自动找到后端容器，所有运行的容器:"
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Image}}"
        echo
        read -p "请输入后端容器名称: " found_container
    fi
    
    if [ -z "$found_container" ]; then
        log_error "没有指定容器名称，退出"
        exit 1
    fi
    
    # 验证容器是否存在
    if ! docker ps --format "{{.Names}}" | grep -q "^${found_container}$"; then
        log_error "容器 $found_container 不存在或未运行"
        exit 1
    fi
    
    export BACKEND_CONTAINER="$found_container"
    log_success "使用容器: $BACKEND_CONTAINER"
}

# 2. 检查容器基本信息
check_container_info() {
    log_info "2. 检查容器基本信息..."
    
    echo "容器详细信息:"
    docker inspect "$BACKEND_CONTAINER" --format='
容器名称: {{.Name}}
容器状态: {{.State.Status}}
启动时间: {{.State.StartedAt}}
重启次数: {{.RestartCount}}
镜像: {{.Config.Image}}
端口映射: {{range $p, $conf := .NetworkSettings.Ports}}{{$p}} -> {{(index $conf 0).HostPort}}{{end}}
工作目录: {{.Config.WorkingDir}}
入口点: {{.Config.Entrypoint}}
命令: {{.Config.Cmd}}
'
    echo
    
    # 检查容器状态
    local container_status=$(docker inspect "$BACKEND_CONTAINER" --format='{{.State.Status}}')
    if [ "$container_status" != "running" ]; then
        log_error "容器状态异常: $container_status"
        return 1
    fi
    
    # 检查重启次数
    local restart_count=$(docker inspect "$BACKEND_CONTAINER" --format='{{.RestartCount}}')
    if [ "$restart_count" -gt 0 ]; then
        log_warning "容器已重启 $restart_count 次，可能存在问题"
    fi
}

# 3. 检查容器内端口监听
check_container_ports() {
    log_info "3. 检查容器内端口监听..."
    
    log_info "容器内监听的端口:"
    docker exec "$BACKEND_CONTAINER" netstat -tulpn 2>/dev/null || \
    docker exec "$BACKEND_CONTAINER" ss -tulpn 2>/dev/null || \
    log_warning "无法获取端口信息 (netstat/ss命令不可用)"
    
    # 检查特定端口
    for port in 5000 5013 8000 3000; do
        if docker exec "$BACKEND_CONTAINER" netstat -tulpn 2>/dev/null | grep ":$port " >/dev/null; then
            log_success "容器内端口 $port 正在监听"
        fi
    done
    
    echo
}

# 4. 检查容器内进程
check_container_processes() {
    log_info "4. 检查容器内进程..."
    
    log_info "容器内运行的进程:"
    docker exec "$BACKEND_CONTAINER" ps aux 2>/dev/null || \
    docker exec "$BACKEND_CONTAINER" ps -ef 2>/dev/null || \
    log_warning "无法获取进程信息"
    
    # 查找Python/Flask相关进程
    log_info "查找Python/Flask进程:"
    docker exec "$BACKEND_CONTAINER" ps aux 2>/dev/null | grep -E "(python|flask|gunicorn|uwsgi)" | grep -v grep || \
    log_warning "未找到Python/Flask相关进程"
    
    echo
}

# 5. 检查应用日志
check_application_logs() {
    log_info "5. 检查应用日志..."
    
    log_info "容器启动日志 (最近50行):"
    docker logs --tail 50 "$BACKEND_CONTAINER"
    echo
    
    # 检查应用内部日志文件
    log_info "检查应用内部日志文件:"
    docker exec "$BACKEND_CONTAINER" find /app -name "*.log" -type f 2>/dev/null | head -10 | while read logfile; do
        if [ -f "$logfile" ]; then
            echo "=== $logfile (最后20行) ==="
            docker exec "$BACKEND_CONTAINER" tail -20 "$logfile" 2>/dev/null || echo "无法读取日志文件"
            echo
        fi
    done
}

# 6. 测试容器内API
test_internal_api() {
    log_info "6. 测试容器内API服务..."
    
    # 测试容器内的API接口
    log_info "从容器内部测试API..."
    
    # 尝试不同的端口和接口
    for port in 5000 5013 8000; do
        log_info "测试端口 $port:"
        
        # 测试根路径
        if docker exec "$BACKEND_CONTAINER" curl -s -m 5 "http://localhost:$port/" >/dev/null 2>&1; then
            log_success "端口 $port 根路径可访问"
            
            # 测试健康检查
            health_response=$(docker exec "$BACKEND_CONTAINER" curl -s -m 5 "http://localhost:$port/api/health" 2>/dev/null || echo "failed")
            if [ "$health_response" != "failed" ] && [ -n "$health_response" ]; then
                log_success "端口 $port 健康检查响应: $health_response"
            else
                log_warning "端口 $port 健康检查无响应"
            fi
        else
            log_warning "端口 $port 不可访问"
        fi
    done
    echo
}

# 7. 检查环境变量和配置
check_environment() {
    log_info "7. 检查环境变量和配置..."
    
    log_info "关键环境变量:"
    docker exec "$BACKEND_CONTAINER" env | grep -E "(PORT|DATABASE|REDIS|FLASK|DEBUG|SECRET)" | sort || \
    log_warning "无法获取环境变量"
    
    echo
    
    # 检查配置文件
    log_info "检查配置文件:"
    for config_file in "/app/config.py" "/app/.env" "/app/backend/config.py"; do
        if docker exec "$BACKEND_CONTAINER" test -f "$config_file" 2>/dev/null; then
            log_info "发现配置文件: $config_file"
            docker exec "$BACKEND_CONTAINER" head -20 "$config_file" 2>/dev/null | grep -v -E "(PASSWORD|SECRET|KEY)" || echo "无法读取配置文件"
        fi
    done
    echo
}

# 8. 检查数据库连接
check_database_connection() {
    log_info "8. 检查数据库连接..."
    
    # 检查是否可以连接到MySQL
    log_info "测试MySQL连接..."
    if docker exec "$BACKEND_CONTAINER" python -c "
import os, sys
try:
    import pymysql
    host = os.getenv('DB_HOST', 'mysql')
    user = os.getenv('DB_USER', 'root')
    password = os.getenv('DB_PASSWORD', '')
    db = os.getenv('DB_NAME', 'website_monitor')
    conn = pymysql.connect(host=host, user=user, password=password, database=db)
    print('MySQL连接成功')
    conn.close()
except Exception as e:
    print(f'MySQL连接失败: {e}')
" 2>/dev/null; then
        log_success "数据库连接测试完成"
    else
        log_warning "无法测试数据库连接 (可能缺少pymysql或环境变量)"
    fi
    
    # 检查Redis连接
    log_info "测试Redis连接..."
    if docker exec "$BACKEND_CONTAINER" python -c "
import os, sys
try:
    import redis
    host = os.getenv('REDIS_HOST', 'redis')
    port = int(os.getenv('REDIS_PORT', '6379'))
    password = os.getenv('REDIS_PASSWORD', None)
    r = redis.Redis(host=host, port=port, password=password)
    r.ping()
    print('Redis连接成功')
except Exception as e:
    print(f'Redis连接失败: {e}')
" 2>/dev/null; then
        log_success "Redis连接测试完成"
    else
        log_warning "无法测试Redis连接 (可能缺少redis库或环境变量)"
    fi
    echo
}

# 9. 手动启动应用测试
manual_start_test() {
    log_info "9. 手动启动测试..."
    
    log_info "尝试在容器内手动启动Flask应用..."
    echo "如果看到Flask启动信息，说明应用代码正常"
    echo "按Ctrl+C退出测试"
    echo "---"
    
    # 尝试手动启动Flask
    docker exec -it "$BACKEND_CONTAINER" bash -c "
        cd /app
        export FLASK_ENV=development
        export FLASK_DEBUG=1
        if [ -f 'run_backend.py' ]; then
            timeout 10 python run_backend.py
        elif [ -f 'app.py' ]; then
            timeout 10 python app.py
        elif [ -f 'main.py' ]; then
            timeout 10 python main.py
        else
            echo '未找到启动文件'
            ls -la
        fi
    " 2>&1 || log_info "手动启动测试完成"
    echo
}

# 10. 提供修复建议
provide_fix_suggestions() {
    log_info "10. 修复建议..."
    echo
    
    echo "🔧 根据诊断结果，可能的解决方案:"
    echo
    echo "1️⃣ 如果端口监听异常:"
    echo "   # 检查应用配置中的端口设置"
    echo "   docker exec $BACKEND_CONTAINER env | grep PORT"
    echo "   # 修改环境变量重启容器"
    echo
    
    echo "2️⃣ 如果应用启动失败:"
    echo "   # 查看详细启动日志"
    echo "   docker logs $BACKEND_CONTAINER"
    echo "   # 重启容器"
    echo "   docker restart $BACKEND_CONTAINER"
    echo
    
    echo "3️⃣ 如果数据库连接失败:"
    echo "   # 检查数据库容器状态"
    echo "   docker ps | grep mysql"
    echo "   # 检查网络连接"
    echo "   docker network ls"
    echo
    
    echo "4️⃣ 如果应用代码有问题:"
    echo "   # 进入容器检查代码"
    echo "   docker exec -it $BACKEND_CONTAINER bash"
    echo "   # 手动运行应用查看错误"
    echo "   cd /app && python run_backend.py"
    echo
    
    echo "5️⃣ 如果配置文件有问题:"
    echo "   # 检查环境变量配置"
    echo "   docker exec $BACKEND_CONTAINER env | grep -E '(DB_|REDIS_|SECRET_)'"
    echo "   # 更新配置重启"
    echo
}

# 主函数
main() {
    find_backend_container
    check_container_info
    check_container_ports
    check_container_processes
    check_application_logs
    test_internal_api
    check_environment
    check_database_connection
    manual_start_test
    provide_fix_suggestions
    
    echo "==========================================="
    echo "           诊断完成"
    echo "==========================================="
    echo "请根据上述信息找出具体问题并修复"
    echo "如需进入容器手动调试: docker exec -it $BACKEND_CONTAINER bash"
}

# 运行主函数
main "$@"