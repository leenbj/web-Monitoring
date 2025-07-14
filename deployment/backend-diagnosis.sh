#!/bin/bash

# 后端服务问题诊断脚本
# 用于全面诊断w3.799n.com:5013后端服务问题

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
echo "    🔍 后端服务问题诊断工具"
echo "==========================================="
echo

# 1. 检查本地Docker服务
check_local_docker() {
    log_info "1. 检查本地Docker服务状态..."
    
    if command -v docker >/dev/null 2>&1; then
        log_success "Docker命令可用"
        
        # 检查Docker服务状态
        if docker ps >/dev/null 2>&1; then
            log_success "Docker服务运行正常"
            
            # 列出所有容器
            echo "当前运行的容器:"
            docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Image}}"
            echo
            
            # 检查网址监控相关容器
            if docker ps --format "{{.Names}}" | grep -E "(website|monitor|backend)" >/dev/null 2>&1; then
                log_success "发现网址监控相关容器:"
                docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(website|monitor|backend)"
            else
                log_warning "未发现网址监控相关容器"
            fi
            
            # 检查端口5013的容器
            if docker ps --format "{{.Ports}}" | grep "5013" >/dev/null 2>&1; then
                log_success "发现使用端口5013的容器:"
                docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep "5013"
            else
                log_warning "未发现使用端口5013的容器"
            fi
            
        else
            log_error "Docker服务未运行"
        fi
    else
        log_warning "Docker命令不可用"
    fi
}

# 2. 检查端口占用情况
check_port_usage() {
    log_info "2. 检查端口5013占用情况..."
    
    # 检查端口监听
    if netstat -tulpn 2>/dev/null | grep ":5013 " >/dev/null; then
        log_success "端口5013正在被监听:"
        netstat -tulpn 2>/dev/null | grep ":5013 "
        echo
        
        # 尝试获取进程信息
        if command -v lsof >/dev/null 2>&1; then
            log_info "端口5013的进程信息:"
            lsof -i :5013 2>/dev/null || log_warning "无法获取进程详细信息"
        fi
    else
        log_error "端口5013没有被监听"
    fi
    
    # 检查常见的后端端口
    log_info "检查其他常见后端端口..."
    for port in 5000 8000 3000 8080; do
        if netstat -tulpn 2>/dev/null | grep ":$port " >/dev/null; then
            echo "端口 $port 正在被使用:"
            netstat -tulpn 2>/dev/null | grep ":$port " | head -3
        fi
    done
    echo
}

# 3. 检查网络连通性
check_network_connectivity() {
    log_info "3. 检查网络连通性..."
    
    # 检查本地回环接口
    log_info "测试本地回环接口..."
    if curl -s --connect-timeout 5 http://127.0.0.1:5013/ >/dev/null 2>&1; then
        log_success "本地5013端口HTTP可访问"
    else
        log_error "本地5013端口HTTP不可访问"
    fi
    
    if curl -s --connect-timeout 5 http://localhost:5013/ >/dev/null 2>&1; then
        log_success "localhost:5013 HTTP可访问"
    else
        log_error "localhost:5013 HTTP不可访问"
    fi
    
    # 检查外部访问
    log_info "测试外部域名访问..."
    if ping -c 1 w3.799n.com >/dev/null 2>&1; then
        log_success "w3.799n.com 域名可以解析"
        echo "IP地址: $(ping -c 1 w3.799n.com | grep 'PING' | sed 's/.*(\([^)]*\)).*/\1/')"
    else
        log_error "w3.799n.com 域名解析失败"
    fi
    
    if nc -z w3.799n.com 5013 2>/dev/null; then
        log_success "w3.799n.com:5013 端口可连接"
    else
        log_error "w3.799n.com:5013 端口连接失败"
    fi
}

# 4. 检查防火墙设置
check_firewall() {
    log_info "4. 检查防火墙设置..."
    
    # 检查iptables (Linux)
    if command -v iptables >/dev/null 2>&1; then
        log_info "检查iptables规则..."
        if iptables -L -n | grep "5013" >/dev/null 2>&1; then
            log_warning "发现5013端口相关的iptables规则:"
            iptables -L -n | grep "5013"
        else
            log_info "未发现5013端口相关的iptables规则"
        fi
    fi
    
    # 检查ufw (Ubuntu)
    if command -v ufw >/dev/null 2>&1; then
        log_info "检查ufw状态..."
        ufw_status=$(ufw status 2>/dev/null || echo "inactive")
        echo "UFW状态: $ufw_status"
        if echo "$ufw_status" | grep -q "5013"; then
            echo "发现5013端口规则:"
            ufw status | grep "5013"
        fi
    fi
    
    # 检查firewalld (CentOS/RHEL)
    if command -v firewall-cmd >/dev/null 2>&1; then
        log_info "检查firewalld状态..."
        if systemctl is-active firewalld >/dev/null 2>&1; then
            log_info "firewalld正在运行"
            if firewall-cmd --list-ports 2>/dev/null | grep "5013" >/dev/null; then
                log_success "端口5013已在firewalld中开放"
            else
                log_warning "端口5013未在firewalld中开放"
            fi
        else
            log_info "firewalld未运行"
        fi
    fi
}

# 5. 检查服务配置文件
check_service_config() {
    log_info "5. 检查服务配置文件..."
    
    # 检查docker-compose文件
    for compose_file in docker-compose.yml docker-compose.backend-only.yml docker-compose.*.yml; do
        if [ -f "$compose_file" ]; then
            log_info "检查 $compose_file"
            if grep -q "5013" "$compose_file"; then
                log_success "在 $compose_file 中发现端口5013配置:"
                grep -n "5013" "$compose_file"
            else
                log_warning "在 $compose_file 中未发现端口5013配置"
                if grep -q "5000" "$compose_file"; then
                    log_info "发现端口5000配置 (可能需要更新):"
                    grep -n "5000" "$compose_file"
                fi
            fi
            echo
        fi
    done
    
    # 检查环境变量文件
    for env_file in .env .env.production .env.local; do
        if [ -f "$env_file" ]; then
            log_info "检查 $env_file"
            if grep -q "5013" "$env_file"; then
                log_success "在 $env_file 中发现端口5013配置:"
                grep "5013" "$env_file"
            else
                log_warning "在 $env_file 中未发现端口5013配置"
                if grep -q "BACKEND_PORT\|PORT" "$env_file"; then
                    log_info "发现端口相关配置:"
                    grep "BACKEND_PORT\|PORT" "$env_file"
                fi
            fi
            echo
        fi
    done
}

# 6. 检查日志文件
check_logs() {
    log_info "6. 检查日志文件..."
    
    # Docker容器日志
    if command -v docker >/dev/null 2>&1; then
        log_info "检查Docker容器日志..."
        for container in $(docker ps --format "{{.Names}}" | grep -E "(website|monitor|backend)"); do
            log_info "容器 $container 的最近日志:"
            docker logs --tail 10 "$container" 2>&1 | head -20
            echo "---"
        done
    fi
    
    # Nginx日志
    for log_file in /www/wwwlogs/w3.799n.com.error.log /var/log/nginx/error.log /www/wwwlogs/w4.799n.com.error.log; do
        if [ -f "$log_file" ]; then
            log_info "检查 $log_file 最近错误:"
            tail -10 "$log_file" 2>/dev/null | grep -E "(error|fail|refused)" || log_info "无相关错误"
            echo
        fi
    done
}

# 7. 提供解决方案
provide_solutions() {
    log_info "7. 问题解决方案建议..."
    echo
    
    echo "🔧 可能的解决方案:"
    echo
    echo "1️⃣ 如果后端服务未启动:"
    echo "   cd /opt/website-monitor  # 或你的部署目录"
    echo "   docker-compose -f docker-compose.backend-only.yml up -d"
    echo
    
    echo "2️⃣ 如果端口配置错误:"
    echo "   # 检查 .env 文件中的 BACKEND_PORT 设置"
    echo "   grep BACKEND_PORT .env"
    echo "   # 应该是: BACKEND_PORT=5013"
    echo
    
    echo "3️⃣ 如果防火墙阻止访问:"
    echo "   # CentOS/RHEL:"
    echo "   firewall-cmd --add-port=5013/tcp --permanent"
    echo "   firewall-cmd --reload"
    echo "   # Ubuntu:"
    echo "   ufw allow 5013"
    echo
    
    echo "4️⃣ 如果Docker容器问题:"
    echo "   # 重启容器"
    echo "   docker restart website-monitor-backend"
    echo "   # 或重新部署"
    echo "   docker-compose -f docker-compose.backend-only.yml down"
    echo "   docker-compose -f docker-compose.backend-only.yml up -d"
    echo
    
    echo "5️⃣ 如果是反向代理配置问题:"
    echo "   # 检查w3.799n.com的Nginx配置"
    echo "   # 确保有正确的反向代理到127.0.0.1:5013"
    echo
    
    echo "6️⃣ 如果服务运行在其他端口:"
    echo "   # 检查所有监听端口"
    echo "   netstat -tulpn | grep LISTEN"
    echo "   # 更新配置文件中的端口号"
    echo
}

# 主函数
main() {
    check_local_docker
    check_port_usage
    check_network_connectivity
    check_firewall
    check_service_config
    check_logs
    provide_solutions
    
    echo "==========================================="
    echo "           诊断完成"
    echo "==========================================="
    echo "请根据上述信息排查后端服务问题"
    echo "如果需要更多帮助，请提供具体的错误信息"
}

# 运行主函数
main "$@"