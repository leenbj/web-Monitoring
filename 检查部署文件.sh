#\!/bin/bash

echo "=== 网址监控系统部署文件检查 ==="
echo "当前目录: $(pwd)"
echo ""

echo "1. 检查 .env.baota 文件："
if [ -f ".env.baota" ]; then
    echo "✓ .env.baota 文件存在"
    echo "文件大小: $(wc -c < .env.baota) 字节"
    echo "修改时间: $(stat -f "%Sm" .env.baota)"
else
    echo "✗ .env.baota 文件不存在"
fi

echo ""
echo "2. 检查所有宝塔相关文件："
echo "--- Dockerfile.baota ---"
ls -la Dockerfile.baota 2>/dev/null || echo "不存在"

echo "--- docker-compose.baota.yml ---"
ls -la docker-compose.baota.yml 2>/dev/null || echo "不存在"

echo "--- nginx.baota.conf ---"
ls -la nginx.baota.conf 2>/dev/null || echo "不存在"

echo "--- .env.baota ---"
ls -la .env.baota 2>/dev/null || echo "不存在"

echo ""
echo "3. 所有环境配置文件："
ls -la .env* 2>/dev/null || echo "没有找到 .env* 文件"

echo ""
echo "4. 如果您在 Finder 中看不到 .env.baota 文件，请："
echo "   - 在 Finder 中按 Cmd+Shift+. 显示隐藏文件"
echo "   - 或者在终端中使用 ls -la 命令查看"
echo ""

echo "=== 检查完成 ==="
