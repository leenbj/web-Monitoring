#!/bin/bash

# 后端服务测试脚本
# 用于验证w3.799n.com:5013后端服务是否正常运行

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

# 后端服务配置
BACKEND_DOMAIN="w3.799n.com"
BACKEND_PORT="5013"
BACKEND_URL="https://${BACKEND_DOMAIN}:${BACKEND_PORT}"

echo "==========================================="
echo "    🔍 后端服务连接测试工具"
echo "==========================================="
echo "测试目标: ${BACKEND_URL}"
echo

# 1. 基础连通性测试
test_connectivity() {
    log_info "1. 测试基础连通性..."
    
    if ping -c 1 ${BACKEND_DOMAIN} >/dev/null 2>&1; then
        log_success "域名 ${BACKEND_DOMAIN} 可以解析"
    else
        log_error "域名 ${BACKEND_DOMAIN} 解析失败"
        return 1
    fi
    
    if nc -z ${BACKEND_DOMAIN} ${BACKEND_PORT} 2>/dev/null; then
        log_success "端口 ${BACKEND_PORT} 可以连接"
    else
        log_error "端口 ${BACKEND_PORT} 连接失败"
        return 1
    fi
}

# 2. HTTP服务测试
test_http_service() {
    log_info "2. 测试HTTP服务响应..."
    
    # 测试根路径
    log_info "测试根路径..."
    if curl -s -I ${BACKEND_URL}/ | head -1 | grep -q "200\|301\|302"; then
        log_success "根路径响应正常"
    else
        log_warning "根路径响应异常"
        curl -s -I ${BACKEND_URL}/ | head -5
    fi
    
    # 测试健康检查接口
    log_info "测试健康检查接口..."
    health_response=$(curl -s -w "%{http_code}" ${BACKEND_URL}/api/health -o /tmp/health_response.json)
    
    if [ "$health_response" = "200" ]; then
        log_success "健康检查接口正常"
        if [ -f /tmp/health_response.json ]; then
            echo "响应内容:"
            cat /tmp/health_response.json | jq . 2>/dev/null || cat /tmp/health_response.json
            rm -f /tmp/health_response.json
        fi
    else
        log_error "健康检查接口异常 (HTTP $health_response)"
        if [ -f /tmp/health_response.json ]; then
            cat /tmp/health_response.json
            rm -f /tmp/health_response.json
        fi
    fi
}

# 3. API接口测试
test_api_endpoints() {
    log_info "3. 测试主要API接口..."
    
    # 测试用户认证接口 (不发送数据，只测试接口可达性)
    log_info "测试认证接口可达性..."
    auth_response=$(curl -s -w "%{http_code}" -X OPTIONS ${BACKEND_URL}/api/auth/login -o /dev/null)
    
    if [ "$auth_response" = "200" ] || [ "$auth_response" = "204" ]; then
        log_success "认证接口可达"
    else
        log_warning "认证接口响应异常 (HTTP $auth_response)"
    fi
    
    # 测试网站列表接口
    log_info "测试网站列表接口..."
    websites_response=$(curl -s -w "%{http_code}" ${BACKEND_URL}/api/websites -o /tmp/websites_response.json)
    
    if [ "$websites_response" = "200" ] || [ "$websites_response" = "401" ]; then
        log_success "网站列表接口可达 (HTTP $websites_response)"
        if [ -f /tmp/websites_response.json ] && [ "$websites_response" = "200" ]; then
            echo "响应内容:"
            cat /tmp/websites_response.json | jq . 2>/dev/null || cat /tmp/websites_response.json
        fi
        rm -f /tmp/websites_response.json
    else
        log_error "网站列表接口异常 (HTTP $websites_response)"
    fi
}

# 4. CORS配置测试
test_cors_configuration() {
    log_info "4. 测试CORS配置..."
    
    cors_response=$(curl -s -H "Origin: https://w4.799n.com" \
                         -H "Access-Control-Request-Method: POST" \
                         -H "Access-Control-Request-Headers: Authorization,Content-Type" \
                         -X OPTIONS \
                         ${BACKEND_URL}/api/auth/login \
                         -w "%{http_code}" \
                         -D /tmp/cors_headers.txt \
                         -o /dev/null)
    
    if [ "$cors_response" = "200" ] || [ "$cors_response" = "204" ]; then
        log_success "CORS预检请求成功 (HTTP $cors_response)"
        
        if grep -q "Access-Control-Allow-Origin" /tmp/cors_headers.txt; then
            log_success "CORS Allow-Origin 头存在"
        else
            log_warning "CORS Allow-Origin 头缺失"
        fi
        
        if grep -q "Access-Control-Allow-Methods" /tmp/cors_headers.txt; then
            log_success "CORS Allow-Methods 头存在"
        else
            log_warning "CORS Allow-Methods 头缺失"
        fi
        
        echo "CORS响应头:"
        grep "Access-Control" /tmp/cors_headers.txt || echo "无CORS头"
        rm -f /tmp/cors_headers.txt
    else
        log_error "CORS预检请求失败 (HTTP $cors_response)"
    fi
}

# 5. SSL证书测试
test_ssl_certificate() {
    log_info "5. 测试SSL证书..."
    
    if openssl s_client -connect ${BACKEND_DOMAIN}:${BACKEND_PORT} -servername ${BACKEND_DOMAIN} </dev/null 2>/dev/null | openssl x509 -noout -dates > /tmp/ssl_info.txt 2>/dev/null; then
        log_success "SSL证书有效"
        cat /tmp/ssl_info.txt
        rm -f /tmp/ssl_info.txt
    else
        log_warning "SSL证书检查失败或使用HTTP"
    fi
}

# 6. 性能测试
test_performance() {
    log_info "6. 性能测试..."
    
    log_info "测试响应时间..."
    response_time=$(curl -s -w "%{time_total}" ${BACKEND_URL}/api/health -o /dev/null)
    
    if [ $(echo "$response_time < 2.0" | bc -l 2>/dev/null || echo "1") = "1" ]; then
        log_success "响应时间正常: ${response_time}s"
    else
        log_warning "响应时间较慢: ${response_time}s"
    fi
}

# 7. Docker容器状态检查 (如果有访问权限)
test_docker_status() {
    log_info "7. 检查Docker容器状态..."
    
    if command -v docker >/dev/null 2>&1; then
        if docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(website-monitor|5013)" >/dev/null 2>&1; then
            log_success "发现相关Docker容器:"
            docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(website-monitor|5013)"
        else
            log_warning "未发现相关Docker容器 (可能运行在其他环境)"
        fi
    else
        log_info "Docker命令不可用，跳过容器状态检查"
    fi
}

# 主测试流程
main() {
    local test_passed=0
    local test_total=6
    
    # 检查依赖工具
    for tool in curl ping nc; do
        if ! command -v $tool >/dev/null 2>&1; then
            log_error "缺少必要工具: $tool"
            exit 1
        fi
    done
    
    # 执行测试
    test_connectivity && ((test_passed++))
    test_http_service && ((test_passed++))
    test_api_endpoints && ((test_passed++))
    test_cors_configuration && ((test_passed++))
    test_ssl_certificate && ((test_passed++))
    test_performance && ((test_passed++))
    test_docker_status
    
    echo
    echo "==========================================="
    echo "           测试结果汇总"
    echo "==========================================="
    echo "通过测试: $test_passed/$test_total"
    
    if [ $test_passed -eq $test_total ]; then
        log_success "后端服务运行正常！"
        echo
        echo "✅ 可以正常访问的接口:"
        echo "   - 健康检查: ${BACKEND_URL}/api/health"
        echo "   - 认证接口: ${BACKEND_URL}/api/auth/login"
        echo "   - 网站列表: ${BACKEND_URL}/api/websites"
        echo
        echo "🔧 前端配置建议:"
        echo "   - API基础URL: ${BACKEND_URL}"
        echo "   - 确保前端代理配置正确"
        exit 0
    elif [ $test_passed -gt $((test_total/2)) ]; then
        log_warning "后端服务部分功能正常，但存在问题需要解决"
        exit 1
    else
        log_error "后端服务存在严重问题，请检查配置"
        exit 2
    fi
}

# 运行主函数
main "$@"