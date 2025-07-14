# 重定向循环问题修复指南

## 🚨 问题分析

### 错误现象
```
GET https://w4.799n.com/api/auth/login net::ERR_TOO_MANY_REDIRECTS
```

### 问题原因
1. **Host头错误**: 前端Nginx代理时设置了 `proxy_set_header Host $host;`，这会导致后端接收到w4.799n.com的Host头
2. **端口不匹配**: 配置中使用了5000端口，但实际后端服务运行在5013端口
3. **缺少redirect控制**: 没有设置 `proxy_redirect off;` 来防止自动重定向

## 🔧 修复方案

### 1. 更新前端Nginx配置

```nginx
# 在 location /api/ 块中修复
location /api/ {
    # 代理到后端服务 (端口5013)
    proxy_pass http://w3.799n.com:5013;
    
    # 关键修复: 设置正确的Host头
    proxy_set_header Host w3.799n.com;  # ← 不是 $host
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # 关键修复: 禁止自动重定向
    proxy_redirect off;  # ← 新增
    
    # 其他配置...
}
```

### 2. 配置解释

**原来的问题配置:**
```nginx
proxy_set_header Host $host;  # ❌ 发送w4.799n.com到后端
```

**修复后的配置:**
```nginx
proxy_set_header Host w3.799n.com;  # ✅ 发送正确的后端域名
proxy_redirect off;                  # ✅ 防止重定向循环
```

## 🧪 后端服务测试方法

### 方法1: 使用测试脚本 (推荐)
```bash
# 运行综合测试脚本
cd deployment
./backend-service-test.sh

# 脚本会测试:
# - 域名解析和端口连通性
# - HTTP服务响应
# - API接口可达性
# - CORS配置
# - SSL证书
# - 响应性能
```

### 方法2: 手动命令测试
```bash
# 1. 测试域名解析
ping w3.799n.com

# 2. 测试端口连通性
nc -z w3.799n.com 5013

# 3. 测试HTTP响应
curl -I https://w3.799n.com:5013/

# 4. 测试健康检查接口
curl https://w3.799n.com:5013/api/health

# 5. 测试认证接口可达性
curl -X OPTIONS https://w3.799n.com:5013/api/auth/login

# 6. 测试CORS配置
curl -H "Origin: https://w4.799n.com" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Authorization,Content-Type" \
     -X OPTIONS \
     https://w3.799n.com:5013/api/auth/login \
     -v
```

### 方法3: 浏览器直接测试
```
1. 直接访问: https://w3.799n.com:5013/api/health
2. 应该看到JSON响应 (不是HTML页面)
3. 检查响应头是否包含CORS设置
```

## 🔍 故障排除步骤

### 步骤1: 验证后端服务状态
```bash
# 检查Docker容器
docker ps | grep website-monitor

# 检查端口监听
netstat -tulpn | grep 5013

# 检查服务日志
docker logs website-monitor-backend
```

### 步骤2: 验证Nginx配置
```bash
# 测试Nginx配置语法
nginx -t

# 重新加载配置
nginx -s reload

# 检查Nginx错误日志
tail -f /www/wwwlogs/w4.799n.com.error.log
```

### 步骤3: 验证网络连接
```bash
# 从前端服务器测试后端连接
curl -H "Host: w3.799n.com" http://w3.799n.com:5013/api/health

# 检查DNS解析
nslookup w3.799n.com
```

## 📊 预期测试结果

### 成功的健康检查响应
```json
{
  "status": "ok",
  "timestamp": "2024-01-01T00:00:00Z",
  "database": "connected",
  "redis": "connected"
}
```

### 成功的CORS响应头
```
Access-Control-Allow-Origin: https://w4.799n.com
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization
Access-Control-Allow-Credentials: true
```

## ⚡ 快速验证命令

```bash
# 一键测试后端服务
curl -s https://w3.799n.com:5013/api/health | jq .

# 一键测试CORS
curl -H "Origin: https://w4.799n.com" -X OPTIONS https://w3.799n.com:5013/api/auth/login -v 2>&1 | grep "Access-Control"

# 一键测试完整链路 (从前端视角)
curl -H "Host: w4.799n.com" https://w4.799n.com/api/health
```

修复这些配置后，重定向循环问题应该得到解决！