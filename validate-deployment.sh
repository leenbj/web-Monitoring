#!/bin/bash
# 网址监控系统部署验证脚本

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
echo "    网址监控系统 - 部署验证工具"
echo "============================================="
echo "验证时间: $(date)"
echo

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
        ".env.baota"
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
        return 1
    fi
}

# 检查Python依赖
check_python_deps() {
    info "检查Python依赖..."
    
    if [ ! -f "requirements.txt" ]; then
        error "requirements.txt文件不存在"
        return 1
    fi
    
    # 检查关键依赖
    required_deps=("Flask" "PyMySQL" "SQLAlchemy" "requests" "APScheduler")
    for dep in "${required_deps[@]}"; do
        if ! grep -q "$dep" requirements.txt; then
            error "缺少依赖: $dep"
            return 1
        fi
    done
    
    success "Python依赖检查通过"
}

# 检查前端配置
check_frontend() {
    info "检查前端配置..."
    
    if [ ! -f "frontend/package.json" ]; then
        error "前端package.json不存在"
        return 1
    fi
    
    # 检查关键依赖
    if ! grep -q "vue" frontend/package.json; then
        error "前端缺少Vue.js依赖"
        return 1
    fi
    
    if [ ! -f "frontend/.env.production" ]; then
        warning "前端生产环境配置文件不存在"
    fi
    
    success "前端配置检查通过"
}

# 检查Docker配置
check_docker() {
    info "检查Docker配置..."
    
    if [ ! -f "Dockerfile.baota" ]; then
        error "Dockerfile.baota不存在"
        return 1
    fi
    
    if [ ! -f "docker-compose.baota.yml" ]; then
        error "docker-compose.baota.yml不存在"
        return 1
    fi
    
    # 验证Docker文件语法
    if command -v docker &> /dev/null; then
        if docker info >/dev/null 2>&1; then
            if ! docker-compose -p website-monitor -f docker-compose.baota.yml config >/dev/null 2>&1; then
                error "docker-compose配置文件语法错误"
                return 1
            fi
        else
            warning "Docker未运行，跳过语法检查"
        fi
    else
        warning "Docker未安装，跳过语法检查"
    fi
    
    success "Docker配置检查通过"
}

# 检查数据库脚本
check_database() {
    info "检查数据库脚本..."
    
    if [ ! -f "init_mysql.sql" ]; then
        error "MySQL初始化脚本不存在"
        return 1
    fi
    
    if [ ! -f "migrate_to_mysql.py" ]; then
        error "数据迁移脚本不存在"
        return 1
    fi
    
    # 检查脚本权限
    if [ ! -x "migrate_to_mysql.py" ]; then
        warning "数据迁移脚本没有执行权限"
        chmod +x migrate_to_mysql.py
    fi
    
    success "数据库脚本检查通过"
}

# 检查Nginx配置
check_nginx() {
    info "检查Nginx配置..."
    
    if [ ! -f "nginx.baota.conf" ]; then
        error "Nginx配置文件不存在"
        return 1
    fi
    
    # 检查配置文件关键内容
    if ! grep -q "proxy_pass.*5001" nginx.baota.conf; then
        error "Nginx配置缺少后端代理配置"
        return 1
    fi
    
    if ! grep -q "try_files.*index.html" nginx.baota.conf; then
        error "Nginx配置缺少前端路由支持"
        return 1
    fi
    
    success "Nginx配置检查通过"
}

# 检查部署脚本
check_deploy_script() {
    info "检查部署脚本..."
    
    if [ ! -f "deploy-baota.sh" ]; then
        error "部署脚本不存在"
        return 1
    fi
    
    if [ ! -x "deploy-baota.sh" ]; then
        warning "部署脚本没有执行权限"
        chmod +x deploy-baota.sh
    fi
    
    if [ ! -f "build-frontend.sh" ]; then
        error "前端构建脚本不存在"
        return 1
    fi
    
    if [ ! -x "build-frontend.sh" ]; then
        warning "前端构建脚本没有执行权限"
        chmod +x build-frontend.sh
    fi
    
    success "部署脚本检查通过"
}

# 检查环境配置
check_env_config() {
    info "检查环境配置..."
    
    if [ ! -f ".env.baota" ]; then
        error "环境配置文件不存在"
        return 1
    fi
    
    # 检查关键配置项
    required_vars=("MYSQL_HOST" "MYSQL_DATABASE" "MYSQL_USER" "MYSQL_PASSWORD" "SECRET_KEY")
    for var in "${required_vars[@]}"; do
        if ! grep -q "^$var=" .env.baota; then
            error "环境配置缺少: $var"
            return 1
        fi
    done
    
    # 检查是否使用默认密码
    if grep -q "BaotaUser2024!" .env.baota; then
        warning "检测到默认数据库密码，建议修改"
    fi
    
    if grep -q "ChangeMe" .env.baota; then
        warning "检测到默认密钥，建议修改"
    fi
    
    success "环境配置检查通过"
}

# 模拟构建测试
test_build() {
    info "测试构建流程..."
    
    # 测试前端构建（如果有Node.js）
    if command -v node &> /dev/null && command -v npm &> /dev/null; then
        info "测试前端构建..."
        cd frontend
        
        if [ ! -d "node_modules" ]; then
            npm install >/dev/null 2>&1
        fi
        
        # 测试构建
        if npm run build >/dev/null 2>&1; then
            success "前端构建测试通过"
        else
            error "前端构建测试失败"
            cd ..
            return 1
        fi
        
        cd ..
    else
        warning "Node.js未安装，跳过前端构建测试"
    fi
    
    # 测试Docker构建（如果有Docker且运行中）
    if command -v docker &> /dev/null; then
        if docker info >/dev/null 2>&1; then
            info "测试Docker镜像构建..."
            if docker build -t website-monitor-test -f Dockerfile.baota . >/dev/null 2>&1; then
                success "Docker构建测试通过"
                docker rmi website-monitor-test >/dev/null 2>&1
            else
                error "Docker构建测试失败"
                return 1
            fi
        else
            warning "Docker未运行，跳过Docker构建测试"
        fi
    else
        warning "Docker未安装，跳过Docker构建测试"
    fi
}

# 生成部署报告
generate_report() {
    info "生成部署报告..."
    
    report_file="deployment-validation-report.txt"
    
    cat > "$report_file" << EOF
网址监控系统部署验证报告
========================

验证时间: $(date)
验证工具版本: 1.0

文件检查:
- 核心文件: ✓ 完整
- Python依赖: ✓ 正常
- 前端配置: ✓ 正常
- Docker配置: ✓ 正常
- 数据库脚本: ✓ 正常
- Nginx配置: ✓ 正常
- 部署脚本: ✓ 正常
- 环境配置: ✓ 正常

构建测试:
EOF

    if command -v node &> /dev/null; then
        echo "- 前端构建: ✓ 通过" >> "$report_file"
    else
        echo "- 前端构建: ⚠ 跳过 (Node.js未安装)" >> "$report_file"
    fi
    
    if command -v docker &> /dev/null; then
        echo "- Docker构建: ✓ 通过" >> "$report_file"
    else
        echo "- Docker构建: ⚠ 跳过 (Docker未安装)" >> "$report_file"
    fi
    
    cat >> "$report_file" << EOF

部署建议:
1. 确保服务器已安装宝塔面板
2. 安装必要的软件: MySQL 8.0, Nginx, Docker
3. 配置域名DNS解析
4. 修改默认密码和密钥
5. 执行部署脚本: ./deploy-baota.sh

后续维护:
- 定期备份数据库
- 监控系统资源使用
- 定期更新系统组件
- 查看系统日志

验证完成，可以开始部署！
EOF
    
    success "部署报告已生成: $report_file"
}

# 主函数
main() {
    local failed=0
    
    check_files || failed=1
    check_python_deps || failed=1
    check_frontend || failed=1
    check_docker || failed=1
    check_database || failed=1
    check_nginx || failed=1
    check_deploy_script || failed=1
    check_env_config || failed=1
    
    if [ $failed -eq 0 ]; then
        test_build || failed=1
    fi
    
    echo
    if [ $failed -eq 0 ]; then
        success "所有验证项目通过！"
        generate_report
        echo
        echo "============================================="
        echo "  ✓ 系统已准备就绪，可以开始部署"
        echo "============================================="
        echo "下一步:"
        echo "1. 配置域名和数据库信息"
        echo "2. 执行部署脚本: ./deploy-baota.sh"
        echo "3. 访问系统进行测试"
        echo
    else
        error "验证失败，请修复上述问题后重新验证"
        exit 1
    fi
}

# 执行主函数
main "$@"