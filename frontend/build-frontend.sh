#\!/bin/bash
# 网址监控系统前端构建脚本

set -e

echo "=== 网址监控系统前端构建 ==="
echo "构建时间: $(date)"

# 进入前端目录
cd frontend

# 安装依赖
echo "安装前端依赖..."
npm ci

# 清理旧构建
echo "清理旧的构建文件..."
rm -rf dist

# 构建生产版本
echo "开始构建生产版本..."
export NODE_ENV=production
npm run build

# 检查构建结果
if [ -d "dist" ] && [ -f "dist/index.html" ]; then
    echo "前端构建成功！"
    echo "构建目录: $(pwd)/dist"
else
    echo "构建失败！"
    exit 1
fi
EOF < /dev/null