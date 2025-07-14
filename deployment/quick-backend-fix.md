# 后端服务快速修复指南

## 🚨 问题现状

根据测试结果，后端服务存在以下问题：
- ✅ 域名w3.799n.com可以解析
- ✅ 端口5013可以连接
- ❌ HTTP服务无响应 (Connection refused)
- ❌ API接口不可访问

## 🔍 问题诊断

### 运行诊断脚本
```bash
cd deployment
./backend-diagnosis.sh
```

## 🛠️ 快速修复步骤

### 1. 检查Docker服务状态
```bash
# 检查Docker是否运行
docker ps

# 查找网址监控相关容器
docker ps | grep -E "(website|monitor|backend)"

# 如果没有容器运行，启动服务
cd /opt/website-monitor  # 替换为你的实际部署目录
docker-compose -f docker-compose.backend-only.yml up -d
```

### 2. 检查端口配置
```bash
# 检查.env文件中的端口配置
cat .env | grep -E "(BACKEND_PORT|PORT)"

# 应该包含：
# BACKEND_PORT=5013
```

如果端口配置错误，编辑.env文件：
```bash
vim .env
# 修改或添加：
BACKEND_PORT=5013
```

### 3. 检查Docker Compose配置
```bash
# 检查docker-compose配置中的端口映射
grep -A5 -B5 "5013" docker-compose.backend-only.yml

# 应该看到类似：
# ports:
#   - "5013:5000"  # 外部5013映射到容器内5000
```

### 4. 重启后端服务
```bash
# 停止现有服务
docker-compose -f docker-compose.backend-only.yml down

# 重新启动
docker-compose -f docker-compose.backend-only.yml up -d

# 查看启动日志
docker-compose -f docker-compose.backend-only.yml logs -f backend
```

### 5. 检查防火墙设置
```bash
# CentOS/RHEL 系统
sudo firewall-cmd --list-ports
sudo firewall-cmd --add-port=5013/tcp --permanent
sudo firewall-cmd --reload

# Ubuntu 系统
sudo ufw status
sudo ufw allow 5013

# 检查iptables
sudo iptables -L -n | grep 5013
```

### 6. 验证本地服务
```bash
# 测试本地访问
curl http://127.0.0.1:5013/api/health
curl http://localhost:5013/api/health

# 检查端口监听
netstat -tulpn | grep 5013
# 或
ss -tulpn | grep 5013
```

## 📋 常见问题及解决方案

### 问题1: Docker容器未运行
**现象**: `docker ps` 没有显示相关容器

**解决方案**:
```bash
cd /opt/website-monitor
docker-compose -f docker-compose.backend-only.yml up -d
```

### 问题2: 端口映射错误
**现象**: 容器运行但端口不是5013

**解决方案**:
```bash
# 编辑docker-compose文件
vim docker-compose.backend-only.yml

# 确保ports配置为:
ports:
  - "${BACKEND_PORT:-5013}:5000"

# 重启服务
docker-compose -f docker-compose.backend-only.yml restart
```

### 问题3: 防火墙阻止访问
**现象**: 本地可访问，外部无法访问

**解决方案**:
```bash
# 开放端口5013
sudo firewall-cmd --add-port=5013/tcp --permanent
sudo firewall-cmd --reload

# 或使用ufw
sudo ufw allow 5013
```

### 问题4: 反向代理配置问题
**现象**: 后端服务正常，但通过域名无法访问

**解决方案**:
检查w3.799n.com的Nginx配置，确保包含：
```nginx
server {
    server_name w3.799n.com;
    
    location / {
        proxy_pass http://127.0.0.1:5013;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 问题5: 容器启动失败
**现象**: `docker-compose up` 报错

**解决方案**:
```bash
# 查看详细错误日志
docker-compose -f docker-compose.backend-only.yml logs

# 检查配置文件语法
docker-compose -f docker-compose.backend-only.yml config

# 拉取最新镜像
docker-compose -f docker-compose.backend-only.yml pull

# 重新构建启动
docker-compose -f docker-compose.backend-only.yml up -d --force-recreate
```

## 🎯 验证修复结果

修复后运行以下命令验证：

```bash
# 1. 检查容器状态
docker ps | grep website-monitor

# 2. 测试本地接口
curl http://127.0.0.1:5013/api/health

# 3. 测试外部域名
curl http://w3.799n.com:5013/api/health

# 4. 运行完整测试
./backend-service-test.sh
```

## 🆘 如果仍然无法解决

1. **提供详细信息**:
   ```bash
   # 收集系统信息
   ./backend-diagnosis.sh > diagnosis-report.txt
   
   # 查看容器日志
   docker-compose -f docker-compose.backend-only.yml logs > docker-logs.txt
   ```

2. **检查部署目录**:
   确认你在正确的部署目录中操作，包含以下文件：
   - `docker-compose.backend-only.yml`
   - `.env`
   - `data/` 目录

3. **重新部署**:
   如果问题持续，考虑完全重新部署：
   ```bash
   docker-compose -f docker-compose.backend-only.yml down -v
   docker system prune -f
   # 重新配置.env文件
   docker-compose -f docker-compose.backend-only.yml up -d
   ```

按照这些步骤应该能解决后端服务的问题！