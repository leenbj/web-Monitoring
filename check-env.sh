#\!/bin/bash
echo "当前目录: $(pwd)"
echo "检查 .env.baota 文件:"
if [ -f ".env.baota" ]; then
    echo "✓ .env.baota 文件存在"
    echo "文件大小: $(wc -c < .env.baota) bytes"
    echo "文件内容前5行:"
    head -5 .env.baota
else
    echo "✗ .env.baota 文件不存在"
fi

echo "当前目录下的 .env* 文件:"
ls -la .env* 2>/dev/null || echo "没有找到 .env* 文件"
