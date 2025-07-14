# 后端API服务修复命令集

## 🚨 问题现状
- ✅ Docker容器已启动
- ❌ API接口无法访问 (Connection reset by peer)
- ❌ curl http://localhost:5013/api/health 失败

## 🔍 立即执行的诊断命令

### 1. 运行容器内部诊断
```bash
cd deployment
./docker-container-debug.sh
```

### 2. 快速检查命令
```bash
# 查看容器状态
docker ps | grep -E "(website|monitor|backend)"

# 查看容器日志
docker logs website-monitor-backend --tail 50

# 检查容器内端口监听
docker exec website-monitor-backend netstat -tulpn | grep -E "(5000|5013)"

# 测试容器内API
docker exec website-monitor-backend curl -s http://localhost:5000/api/health
```

## 🛠️ 常见问题及快速修复

### 问题1: 应用端口配置错误

**检查命令:**
```bash
# 查看容器端口映射
docker port website-monitor-backend

# 查看环境变量
docker exec website-monitor-backend env | grep -E "(PORT|FLASK)"
```

**修复方案:**
```bash
# 如果应用运行在5000端口，但映射到5013
# 检查docker-compose配置
cat docker-compose.backend-only.yml | grep -A5 -B5 ports

# 修复端口映射 (应该是)
ports:
  - "5013:5000"  # 外部5013映射到容器内5000
```

### 问题2: Flask应用启动失败

**检查命令:**
```bash
# 进入容器检查
docker exec -it website-monitor-backend bash

# 在容器内执行
cd /app
ls -la
python --version
which python

# 手动启动应用
python run_backend.py
# 或
flask run --host=0.0.0.0 --port=5000
```

**修复方案:**
```bash
# 如果缺少依赖
pip install -r requirements.txt

# 如果启动文件有问题，检查
cat run_backend.py
# 确保包含: app.run(host='0.0.0.0', port=5000)
```

### 问题3: 数据库连接问题

**检查命令:**
```bash
# 检查数据库容器
docker ps | grep mysql

# 检查网络连接
docker exec website-monitor-backend ping mysql -c 3

# 测试数据库连接
docker exec website-monitor-backend python -c "
import pymysql
import os
try:
    conn = pymysql.connect(
        host=os.getenv('DB_HOST', 'mysql'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME', 'website_monitor')
    )
    print('数据库连接成功')
    conn.close()
except Exception as e:
    print(f'数据库连接失败: {e}')
"
```

**修复方案:**
```bash
# 重启数据库容器
docker restart website-monitor-mysql

# 检查环境变量
docker exec website-monitor-backend env | grep DB_

# 确保数据库已初始化
docker exec website-monitor-mysql mysql -u root -p[password] -e "SHOW DATABASES;"
```

### 问题4: Redis连接问题

**检查命令:**
```bash
# 检查Redis容器
docker ps | grep redis

# 测试Redis连接
docker exec website-monitor-backend python -c "
import redis
import os
try:
    r = redis.Redis(
        host=os.getenv('REDIS_HOST', 'redis'),
        port=int(os.getenv('REDIS_PORT', '6379')),
        password=os.getenv('REDIS_PASSWORD')
    )
    r.ping()
    print('Redis连接成功')
except Exception as e:
    print(f'Redis连接失败: {e}')
"
```

### 问题5: 应用配置错误

**检查命令:**
```bash
# 检查配置文件
docker exec website-monitor-backend cat /app/config.py
docker exec website-monitor-backend cat /app/.env

# 检查关键环境变量
docker exec website-monitor-backend env | grep -E "(SECRET|DATABASE|REDIS|FLASK)"
```

## ⚡ 一键修复脚本

创建快速修复脚本：
```bash
#!/bin/bash
echo "=== 后端服务快速修复 ==="

# 1. 重启后端容器
echo "重启后端容器..."
docker restart website-monitor-backend
sleep 10

# 2. 检查容器状态
echo "检查容器状态..."
docker ps | grep website-monitor-backend

# 3. 查看启动日志
echo "查看启动日志..."
docker logs website-monitor-backend --tail 20

# 4. 测试内部API
echo "测试内部API..."
docker exec website-monitor-backend curl -s http://localhost:5000/api/health

# 5. 检查端口监听
echo "检查端口监听..."
docker exec website-monitor-backend netstat -tulpn | grep -E "(5000|5013)"

echo "=== 修复完成 ==="
```

## 🎯 验证修复结果

修复后执行以下验证：
```bash
# 1. 容器内测试
docker exec website-monitor-backend curl http://localhost:5000/api/health

# 2. 宿主机测试
curl http://localhost:5013/api/health

# 3. 外部测试
curl http://w3.799n.com:5013/api/health

# 4. 完整测试
./backend-service-test.sh
```

## 🆘 如果仍然无法解决

1. **收集完整诊断信息**:
```bash
./docker-container-debug.sh > debug-report.txt
docker logs website-monitor-backend > container-logs.txt
```

2. **重新构建容器**:
```bash
docker-compose -f docker-compose.backend-only.yml down
docker-compose -f docker-compose.backend-only.yml pull
docker-compose -f docker-compose.backend-only.yml up -d --force-recreate
```

3. **手动进入容器调试**:
```bash
docker exec -it website-monitor-backend bash
cd /app
python run_backend.py  # 查看具体错误信息
```

执行这些命令应该能找到并解决API服务的具体问题！