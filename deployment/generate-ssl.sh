#!/bin/bash

# 生成SSL自签名证书脚本
# 用于HTTPS端口448的SSL配置

set -e

# 颜色定义
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

# 创建SSL目录
create_ssl_directory() {
    log_info "创建SSL证书目录..."
    mkdir -p ssl
    cd ssl
}

# 生成自签名证书
generate_self_signed_cert() {
    log_info "生成SSL自签名证书..."
    
    # 获取域名信息
    read -p "请输入域名 (默认: localhost): " DOMAIN
    DOMAIN=${DOMAIN:-localhost}
    
    # 生成私钥
    log_info "生成私钥..."
    openssl genrsa -out nginx-selfsigned.key 2048
    
    # 生成证书签名请求配置
    cat > cert.conf << EOF
[req]
default_bits = 2048
prompt = no
default_md = sha256
distinguished_name = dn
req_extensions = v3_req

[dn]
C=CN
ST=Beijing
L=Beijing
O=Website Monitor
OU=IT Department
CN=$DOMAIN

[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = $DOMAIN
DNS.2 = localhost
DNS.3 = *.${DOMAIN}
IP.1 = 127.0.0.1
IP.2 = ::1
EOF
    
    # 生成自签名证书
    log_info "生成自签名证书..."
    openssl req -new -x509 -key nginx-selfsigned.key -out nginx-selfsigned.crt -days 365 -config cert.conf -extensions v3_req
    
    # 设置权限
    chmod 600 nginx-selfsigned.key
    chmod 644 nginx-selfsigned.crt
    
    # 清理临时文件
    rm cert.conf
    
    cd ..
}

# 验证证书
verify_certificate() {
    log_info "验证SSL证书..."
    
    echo "证书信息:"
    openssl x509 -in ssl/nginx-selfsigned.crt -text -noout | grep -E "(Subject:|DNS:|IP Address:)"
    echo
    
    echo "证书有效期:"
    openssl x509 -in ssl/nginx-selfsigned.crt -dates -noout
    echo
}

# 显示使用说明
show_usage_info() {
    log_success "SSL证书生成完成！"
    echo
    echo "=========================================="
    echo "           SSL证书信息"
    echo "=========================================="
    echo "证书文件: ssl/nginx-selfsigned.crt"
    echo "私钥文件: ssl/nginx-selfsigned.key"
    echo "域名: $DOMAIN"
    echo "有效期: 365天"
    echo "=========================================="
    echo
    log_warning "注意事项:"
    echo "1. 这是自签名证书，浏览器会显示安全警告"
    echo "2. 生产环境建议使用正式CA签发的证书"
    echo "3. 可以使用Let's Encrypt免费证书"
    echo
    echo "Let's Encrypt证书获取命令:"
    echo "certbot --nginx -d $DOMAIN"
    echo
    echo "现在可以启动包含HTTPS的Docker服务:"
    echo "docker-compose -f docker-compose.with-nginx.yml up -d"
    echo
    echo "访问地址:"
    echo "HTTP:  http://$DOMAIN:85"
    echo "HTTPS: https://$DOMAIN:448"
}

# 检查OpenSSL
check_openssl() {
    if ! command -v openssl &> /dev/null; then
        log_error "OpenSSL未安装，请先安装OpenSSL"
        exit 1
    fi
}

# 主函数
main() {
    echo "=========================================="
    echo "    🔒 SSL证书生成工具"
    echo "=========================================="
    echo
    
    check_openssl
    create_ssl_directory
    generate_self_signed_cert
    verify_certificate
    show_usage_info
}

# 运行主函数
main "$@"