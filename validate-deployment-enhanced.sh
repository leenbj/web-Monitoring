#!/bin/bash
# 网址监控系统部署验证脚本 - 增强版
# 包含更详细的错误诊断信息

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo "============================================="
echo "    网址监控系统 - 部署验证工具 (增强版)"
echo "============================================="
echo "验证时间: $(date)"
echo "当前目录: $(pwd)"
echo "脚本路径: $(realpath "$0")"
echo

# 检查是否在正确的目录
check_directory() {
    info "检查项目目录..."
    
    if [ ! -f "backend/app.py" ]; then
        error "当前目录不是项目根目录"
        echo "请在项目根目录运行此脚本"
        echo "项目根目录应该包含以下文件:"
        echo "  - backend/app.py"
        echo "  - frontend/package.json"
        echo "  - requirements.txt"
        exit 1
    fi
    
    success "项目目录检查通过"
}

# 检查文件完整性
check_files() {
    info "检查核心文件..."
    
    required_files=(
        "backend/app.py"
        "backend/models.py" 
        "backend/database.py"
        "backend/config.py"
        "requirements.txt"
        "run_backend.py"
        "frontend/package.json"
        "frontend/vite.config.js"
        "frontend/src/main.js"
        "Dockerfile.baota"
        "docker-compose.baota.yml"
        "nginx.baota.conf"
        "baota.txt"
        "init_mysql.sql"
        "migrate_to_mysql.py"
        "deploy-baota.sh"
        "build-frontend.sh"
    )
    
    missing_files=()
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            missing_files+=("$file")
        fi
    done
    
    if [ ${#missing_files[@]} -eq 0 ]; then
        success "所有核心文件完整"
    else
        error "缺少以下文件:"
        for file in "${missing_files[@]}"; do
            echo "  - $file"
        done
        
        # 提供更详细的诊断信息
        echo
        warning "文件诊断信息:"
        echo "当前目录内容:"
        ls -la
        echo
        echo "查找可能的 .env.baota 文件:"
        find . -name ".env.baota" -type f 2>/dev/null || echo "未找到 .env.baota 文件"
        echo
        echo "查找可能的 .env* 文件:"
        find . -name ".env*" -type f 2>/dev/null || echo "未找到 .env* 文件"
        
        return 1
    fi
}

# 检查环境配置
check_env_config() {
    info "检查环境配置..."
    
    if [ ! -f "baota.txt" ]; then
        error "环境配置文件不存在"
        echo "诊断信息:"
        echo "  - 当前目录: $(pwd)"
        echo "  - 脚本位置: $(dirname "$0")"
        echo "  - 文件权限: $(ls -la .env* 2>/dev/null || echo '无 .env* 文件')"
        
        # 尝试创建默认配置文件
        warning "尝试创建默认配置文件..."
        cat > baota.txt << 'EOF'
# 网址监控系统 - 宝塔面板部署环境配置

# 数据库配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=website_monitor
MYSQL_USER=monitor_user
MYSQL_PASSWORD=BaotaUser2024!

# 安全配置
SECRET_KEY=WebMonitorBaotaSecretKey2024ChangeMe
JWT_SECRET_KEY=JWTBaotaSecretKey2024ChangeMe

# 应用配置
FLASK_ENV=production
PORT=5001
DEBUG=false
LOG_LEVEL=INFO

# 检测配置
DEFAULT_TIMEOUT=30
DEFAULT_RETRY_TIMES=3
DEFAULT_MAX_CONCURRENT=20
DEFAULT_INTERVAL_HOURS=6

# 性能配置
WORKERS=2
THREADS=4
TIMEOUT=120
MAX_MEMORY_MB=512

# 域名配置
FRONTEND_DOMAIN=your-domain.com
API_DOMAIN=your-domain.com

# 时区
TZ=Asia/Shanghai
EOF
        
        if [ -f "baota.txt" ]; then
            success "默认配置文件创建成功"
        else
            error "配置文件创建失败"
            return 1
        fi
    fi
    
    # 检查关键配置项
    required_vars=("MYSQL_HOST" "MYSQL_DATABASE" "MYSQL_USER" "MYSQL_PASSWORD" "SECRET_KEY")
    for var in "${required_vars[@]}"; do
        if ! grep -q "^$var=" baota.txt; then
            error "环境配置缺少: $var"
            echo "文件内容:"
            cat baota.txt
            return 1
        fi
    done
    
    # 检查是否使用默认密码
    if grep -q "BaotaUser2024!" baota.txt; then
        warning "检测到默认数据库密码，建议修改"
    fi
    
    if grep -q "ChangeMe" baota.txt; then
        warning "检测到默认密钥，建议修改"
    fi
    
    success "环境配置检查通过"
}

# 生成部署报告
generate_report() {
    info "生成部署报告..."
    
    report_file="deployment-validation-report.txt"
    
    cat > "$report_file" << EOF
网址监控系统部署验证报告
========================

验证时间: $(date)
验证目录: $(pwd)
验证工具版本: 2.0 (增强版)

环境检查:
- 项目目录: ✓ 正确
- 核心文件: ✓ 完整
- 环境配置: ✓ 正常

文件清单:
- 后端代码: backend/
- 前端代码: frontend/
- Docker配置: Dockerfile.baota, docker-compose.baota.yml
- Nginx配置: nginx.baota.conf
- 数据库脚本: init_mysql.sql, migrate_to_mysql.py
- 部署脚本: deploy-baota.sh, build-frontend.sh
- 环境配置: baota.txt

部署建议:
1. 确保服务器已安装宝塔面板
2. 安装必要的软件: MySQL 8.0, Nginx, Docker
3. 配置域名DNS解析
4. 修改 baota.txt 中的默认密码和密钥:
   - MYSQL_PASSWORD
   - SECRET_KEY  
   - JWT_SECRET_KEY
   - FRONTEND_DOMAIN
   - API_DOMAIN
5. 执行部署脚本: ./deploy-baota.sh

下一步:
1. 上传项目到服务器
2. 在项目根目录运行: ./deploy-baota.sh
3. 访问系统进行测试 (admin/admin123)

验证完成时间: $(date)
EOF
    
    success "部署报告已生成: $report_file"
}

# 主函数
main() {
    local failed=0
    
    check_directory || failed=1
    check_files || failed=1
    check_env_config || failed=1
    
    echo
    if [ $failed -eq 0 ]; then
        success "所有验证项目通过！"
        generate_report
        echo
        echo "============================================="
        echo "  ✓ 系统已准备就绪，可以开始部署"
        echo "============================================="
        echo "下一步:"
        echo "1. 修改 baota.txt 中的域名和密码配置"
        echo "2. 执行部署脚本: ./deploy-baota.sh"
        echo "3. 访问系统进行测试"
        echo
        echo "重要提醒:"
        echo "- 请在服务器的项目根目录运行部署脚本"
        echo "- 确保宝塔面板已安装 MySQL 8.0, Nginx, Docker"
        echo "- 修改默认密码和密钥后再部署"
        echo "- 部署时请将 baota.txt 重命名为 .env.baota"
        echo
    else
        error "验证失败，请查看上述错误信息"
        echo
        echo "常见问题解决:"
        echo "1. 确保在项目根目录运行脚本"
        echo "2. 检查文件权限和路径"
        echo "3. 重新下载项目文件"
        exit 1
    fi
}

# 执行主函数
main "$@"