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
