#!/bin/bash
# 完整后端部署前置检查

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
echo "    完整后端部署前置检查"
echo "============================================="

ERRORS=0

# 1. 检查系统环境
info "1. 检查系统环境..."

# 检查操作系统
if [ -f /etc/redhat-release ]; then
    SYSTEM="centos"
    info "系统类型: CentOS/RHEL"
elif [ -f /etc/debian_version ]; then
    SYSTEM="debian"
    info "系统类型: Debian/Ubuntu"
else
    SYSTEM="unknown"
    warning "未知系统类型"
fi

# 检查Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    success "Python: $PYTHON_VERSION"
else
    error "Python3 未安装"
    ((ERRORS++))
fi

# 检查pip
if command -v pip3 &> /dev/null; then
    PIP_VERSION=$(pip3 --version)
    success "pip: $PIP_VERSION"
else
    error "pip3 未安装"
    ((ERRORS++))
fi

# 2. 检查MySQL服务
info "2. 检查MySQL服务..."

if command -v mysql &> /dev/null; then
    success "MySQL客户端已安装"
    
    # 检查MySQL服务状态
    if systemctl is-active --quiet mysql || systemctl is-active --quiet mysqld; then
        success "MySQL服务正在运行"
    else
        error "MySQL服务未运行"
        ((ERRORS++))
    fi
    
    # 检查数据库连接
    info "测试数据库连接..."
    if mysql -hlocalhost -uroot -e "SHOW DATABASES;" &>/dev/null; then
        success "MySQL root连接成功"
    else
        warning "MySQL root连接失败，请检查root密码"
    fi
    
else
    error "MySQL客户端未安装"
    ((ERRORS++))
fi

# 3. 检查网络连接
info "3. 检查网络连接..."

# 检查外网连接
if ping -c 1 8.8.8.8 &>/dev/null; then
    success "外网连接正常"
else
    warning "外网连接失败，可能影响依赖包安装"
fi

# 检查国内镜像源
if curl -s --connect-timeout 5 https://pypi.tuna.tsinghua.edu.cn/simple/ &>/dev/null; then
    success "清华大学PyPI镜像源可访问"
else
    warning "清华大学PyPI镜像源不可访问"
fi

# 4. 检查端口占用
info "4. 检查端口占用..."

if netstat -tlnp | grep -q ":5011 "; then
    PORT_INFO=$(netstat -tlnp | grep ":5011 ")
    warning "端口5011已被占用: $PORT_INFO"
else
    success "端口5011可用"
fi

# 5. 检查磁盘空间
info "5. 检查磁盘空间..."

DISK_USAGE=$(df -h . | awk 'NR==2 {print $5}' | sed 's/%//')
AVAILABLE_SPACE=$(df -h . | awk 'NR==2 {print $4}')

if [ "$DISK_USAGE" -lt 80 ]; then
    success "磁盘空间充足 (使用率: ${DISK_USAGE}%, 可用: $AVAILABLE_SPACE)"
else
    warning "磁盘空间不足 (使用率: ${DISK_USAGE}%, 可用: $AVAILABLE_SPACE)"
fi

# 6. 检查内存
info "6. 检查内存..."

TOTAL_MEM=$(free -h | grep "^Mem:" | awk '{print $2}')
AVAILABLE_MEM=$(free -h | grep "^Mem:" | awk '{print $7}')
MEM_USAGE=$(free | grep "^Mem:" | awk '{printf "%.1f", $3/$2 * 100.0}')

if [ $(echo "$MEM_USAGE < 80" | bc -l) -eq 1 ]; then
    success "内存充足 (总计: $TOTAL_MEM, 可用: $AVAILABLE_MEM, 使用率: ${MEM_USAGE}%)"
else
    warning "内存使用率较高 (总计: $TOTAL_MEM, 可用: $AVAILABLE_MEM, 使用率: ${MEM_USAGE}%)"
fi

# 7. 检查必要的系统包
info "7. 检查必要的系统包..."

REQUIRED_PACKAGES=("curl" "wget" "gcc" "make")
MISSING_PACKAGES=()

for package in "${REQUIRED_PACKAGES[@]}"; do
    if command -v "$package" &> /dev/null; then
        success "$package 已安装"
    else
        error "$package 未安装"
        MISSING_PACKAGES+=("$package")
        ((ERRORS++))
    fi
done

# 8. 检查Python开发环境
info "8. 检查Python开发环境..."

if python3 -c "import distutils.util" &>/dev/null; then
    success "Python distutils 可用"
else
    warning "Python distutils 不可用"
fi

if python3 -c "import venv" &>/dev/null; then
    success "Python venv 可用"
else
    error "Python venv 不可用"
    ((ERRORS++))
fi

# 9. 检查项目文件
info "9. 检查项目文件..."

REQUIRED_FILES=("backend/app.py" "backend/models.py" "backend/database.py" "requirements.txt")
MISSING_FILES=()

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        success "$file 存在"
    else
        error "$file 不存在"
        MISSING_FILES+=("$file")
        ((ERRORS++))
    fi
done

# 10. 生成修复建议
echo ""
echo "============================================="
echo "           检查结果总结"
echo "============================================="

if [ $ERRORS -eq 0 ]; then
    success "所有检查通过！可以开始部署完整后端服务。"
    echo ""
    echo "下一步执行:"
    echo "1. 在宝塔面板执行MySQL配置:"
    echo "   - 上传并执行 setup-mysql-for-full-backend.sql"
    echo "2. 部署完整后端:"
    echo "   chmod +x deploy-full-backend.sh"
    echo "   ./deploy-full-backend.sh"
else
    error "发现 $ERRORS 个问题，需要先修复:"
    echo ""
    
    if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
        echo "安装缺失的系统包:"
        if [ "$SYSTEM" = "centos" ]; then
            echo "  yum install -y ${MISSING_PACKAGES[*]}"
        elif [ "$SYSTEM" = "debian" ]; then
            echo "  apt-get update && apt-get install -y ${MISSING_PACKAGES[*]}"
        fi
        echo ""
    fi
    
    if [ ${#MISSING_FILES[@]} -gt 0 ]; then
        echo "缺失的项目文件:"
        printf "  - %s\n" "${MISSING_FILES[@]}"
        echo "  请确保上传了完整的项目代码"
        echo ""
    fi
    
    echo "修复问题后重新运行此检查脚本。"
fi

echo ""
echo "系统信息摘要:"
echo "  - 操作系统: $SYSTEM"
echo "  - Python: $(python3 --version 2>/dev/null || echo '未安装')"
echo "  - MySQL: $(mysql --version 2>/dev/null | cut -d' ' -f1-3 || echo '未安装')"
echo "  - 磁盘使用率: ${DISK_USAGE}%"
echo "  - 内存使用率: ${MEM_USAGE}%"
echo "  - 端口5011: $(netstat -tlnp | grep -q ":5011 " && echo "占用" || echo "可用")"
echo ""
echo "============================================="

exit $ERRORS