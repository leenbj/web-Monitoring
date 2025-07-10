#!/bin/bash

echo "正在启动后端服务..."

# 等待数据库连接
echo "等待数据库连接..."
for i in {1..30}; do
    if python -c "
from backend.database import test_database_connection
import sys
if test_database_connection():
    print('数据库连接成功')
    sys.exit(0)
else:
    sys.exit(1)
" 2>/dev/null; then
        echo "数据库连接就绪"
        break
    fi
    echo "等待数据库... ($i/30)"
    sleep 2
done

# 启动Flask应用
echo "启动Flask应用..."
exec python /app/backend/app.py