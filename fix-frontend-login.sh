#!/bin/bash
# 修复前端登录问题并重新构建

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
echo "    修复前端登录问题并重新构建"
echo "============================================="

# 1. 进入前端目录
info "1. 进入前端目录..."
cd frontend

# 2. 检查Node.js和npm
info "2. 检查开发环境..."
if ! command -v node &> /dev/null; then
    error "Node.js 未安装"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    error "npm 未安装"
    exit 1
fi

NODE_VERSION=$(node --version)
NPM_VERSION=$(npm --version)
info "Node.js: $NODE_VERSION"
info "npm: $NPM_VERSION"

# 3. 安装依赖
info "3. 安装依赖..."
if [ ! -d "node_modules" ]; then
    npm install
else
    info "依赖已存在，跳过安装"
fi

# 4. 构建项目
info "4. 构建生产版本..."
npm run build

if [ $? -eq 0 ]; then
    success "前端构建成功"
else
    error "前端构建失败"
    exit 1
fi

# 5. 检查构建结果
info "5. 检查构建结果..."
if [ -d "dist" ]; then
    success "构建目录存在"
    ls -la dist/
else
    error "构建目录不存在"
    exit 1
fi

# 6. 返回项目根目录
cd ..

# 7. 创建部署压缩包
info "7. 创建部署压缩包..."
if [ -d "frontend/dist" ]; then
    # 创建压缩包
    tar -czf frontend-dist.tar.gz -C frontend/dist .
    success "前端部署包创建成功: frontend-dist.tar.gz"
    
    # 显示文件大小
    FILE_SIZE=$(du -h frontend-dist.tar.gz | cut -f1)
    info "压缩包大小: $FILE_SIZE"
else
    error "前端构建目录不存在"
    exit 1
fi

# 8. 创建服务器部署指令
info "8. 创建服务器部署指令..."
cat > deploy-frontend-to-server.sh << 'EOF'
#!/bin/bash
# 在服务器上执行此脚本部署前端

# 设置变量
WEBSITE_ROOT="/www/wwwroot/w4.799n.com"
BACKUP_DIR="/root/website-monitor-backup"
FRONTEND_PACKAGE="frontend-dist.tar.gz"

# 创建备份
echo "创建备份..."
mkdir -p $BACKUP_DIR
if [ -d "$WEBSITE_ROOT" ]; then
    tar -czf "$BACKUP_DIR/frontend-backup-$(date +%Y%m%d-%H%M%S).tar.gz" -C "$WEBSITE_ROOT" .
    echo "备份创建成功"
fi

# 创建网站目录
echo "创建网站目录..."
mkdir -p $WEBSITE_ROOT

# 解压前端文件
echo "部署前端文件..."
if [ -f "$FRONTEND_PACKAGE" ]; then
    tar -xzf "$FRONTEND_PACKAGE" -C "$WEBSITE_ROOT"
    echo "前端文件部署成功"
else
    echo "错误：前端包文件不存在"
    exit 1
fi

# 设置权限
echo "设置文件权限..."
chown -R www:www $WEBSITE_ROOT
chmod -R 755 $WEBSITE_ROOT

# 检查部署结果
echo "检查部署结果..."
if [ -f "$WEBSITE_ROOT/index.html" ]; then
    echo "✓ 前端文件部署成功"
    echo "✓ 网站根目录: $WEBSITE_ROOT"
    echo "✓ 文件数量: $(find $WEBSITE_ROOT -type f | wc -l)"
    echo "✓ 部署完成时间: $(date)"
else
    echo "✗ 前端文件部署失败"
    exit 1
fi

echo "前端部署完成！"
EOF

chmod +x deploy-frontend-to-server.sh
success "服务器部署脚本创建成功: deploy-frontend-to-server.sh"

echo ""
echo "============================================="
echo "           修复完成"
echo "============================================="
success "前端登录问题已修复并重新构建！"
echo ""
echo "文件清单:"
echo "  - frontend-dist.tar.gz - 前端部署包"
echo "  - deploy-frontend-to-server.sh - 服务器部署脚本"
echo ""
echo "部署步骤:"
echo "1. 上传以下文件到服务器:"
echo "   - frontend-dist.tar.gz"
echo "   - deploy-frontend-to-server.sh"
echo ""
echo "2. 在服务器上执行:"
echo "   chmod +x deploy-frontend-to-server.sh"
echo "   ./deploy-frontend-to-server.sh"
echo ""
echo "3. 测试网站访问:"
echo "   https://w4.799n.com"
echo ""
echo "主要修复内容:"
echo "  - 修复了API响应格式兼容性问题"
echo "  - 修复了登录成功后的错误处理逻辑"
echo "  - 支持后端简化版的响应格式"
echo ""
echo "============================================="