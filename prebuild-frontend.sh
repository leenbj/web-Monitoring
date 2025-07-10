#!/bin/bash

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔨 网址监控系统前端预构建脚本"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 检查是否在正确的目录
if [ ! -d "frontend" ]; then
    echo "[ERROR] 请在项目根目录执行此脚本"
    exit 1
fi

# 进入前端目录
cd frontend

echo "[INFO] 当前目录: $(pwd)"

# 检查Node.js和npm版本
echo "[INFO] Node.js版本: $(node --version)"
echo "[INFO] npm版本: $(npm --version)"

# 备份原始配置
echo "[INFO] 备份原始配置文件..."
cp package.json package.json.bak 2>/dev/null || true
cp vite.config.js vite.config.js.bak 2>/dev/null || true

# 使用优化的配置文件
echo "[INFO] 使用优化的配置文件..."
cp ../package-baota.json ./package.json
cp ../vite.config-baota.js ./vite.config.js

# 清理旧的构建文件
echo "[INFO] 清理旧的构建文件..."
rm -rf node_modules dist package-lock.json yarn.lock

# 安装依赖
echo "[INFO] 安装依赖..."
npm install --legacy-peer-deps --no-package-lock

# 检查依赖是否安装成功
if [ ! -f "node_modules/.bin/vite" ]; then
    echo "[ERROR] Vite 安装失败"
    exit 1
fi

# 构建项目
echo "[INFO] 开始构建项目..."
npm run build

# 检查构建结果
if [ ! -d "dist" ]; then
    echo "[ERROR] 构建失败，dist目录不存在"
    exit 1
fi

echo "[INFO] 构建完成，检查结果:"
ls -la dist/

# 恢复原始配置
echo "[INFO] 恢复原始配置文件..."
mv package.json.bak package.json 2>/dev/null || true
mv vite.config.js.bak vite.config.js 2>/dev/null || true

# 创建部署包
echo "[INFO] 创建部署包..."
cd ..
tar -czf frontend-dist.tar.gz frontend/dist/

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 前端预构建完成!"
echo "📦 部署包: frontend-dist.tar.gz"
echo "📁 构建目录: frontend/dist/"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🚀 部署说明:"
echo "1. 上传 frontend-dist.tar.gz 到服务器"
echo "2. 解压: tar -xzf frontend-dist.tar.gz"
echo "3. 使用 Dockerfile.frontend-baota-simple 构建镜像"
echo "4. 或直接将 dist 目录内容复制到 nginx 容器"