# 前后端域名分离部署方案

## 📋 域名分配策略

### 🌐 域名职责划分
```
w4.799n.com (前端域名)
├── 静态文件服务 (Vue.js应用)
├── 前端路由支持 (SPA)
└── API请求代理到后端域名

w3.799n.com (后端域名)  
├── API服务代理 (所有请求转发到Docker)
├── WebSocket支持
└── 健康检查接口
```

## 🔄 请求流程

### 前端访问流程
```
用户浏览器
    ↓ 访问 https://w4.799n.com
w4.799n.com (Nginx)
    ↓ 静态文件 (/, /about, /login等)
Vue.js 应用
    ↓ API调用
w3.799n.com (Nginx代理)
    ↓ 转发到
Docker容器 (127.0.0.1:5000)
```

### API调用链路
```
前端 (w4.799n.com)
    ↓ axios.get('/api/users')
    ↓ 被代理配置重定向到
后端 (w3.799n.com/api/users)
    ↓ Nginx代理转发
Docker Backend (127.0.0.1:5000/api/users)
    ↓ 响应数据
前端接收响应
```

## 📁 配置文件说明

### 前端配置 (bt-panel-site.conf)
```nginx
server {
    server_name w4.799n.com;
    root /www/wwwroot/w4.799n.com;
    
    # 静态文件服务
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # API代理到后端域名
    location /api/ {
        proxy_pass http://w3.799n.com:5000;
        # CORS + 其他配置
    }
}
```

### 后端配置 (bt-panel-backend.conf)
```nginx
server {
    server_name w3.799n.com;
    
    # 所有请求代理到Docker容器
    location / {
        proxy_pass http://127.0.0.1:5000;
        # 代理配置
    }
}
```

## 🛠️ 部署步骤

### 1. 前端站点设置
1. 宝塔面板创建站点 `w4.799n.com`
2. 上传前端构建文件到 `/www/wwwroot/w4.799n.com/`
3. 应用前端Nginx配置 (`bt-panel-site.conf`)
4. 配置SSL证书

### 2. 后端站点设置
1. 宝塔面板创建站点 `w3.799n.com`
2. 应用后端Nginx配置 (`bt-panel-backend.conf`)
3. 配置SSL证书
4. 启动Docker后端服务

### 3. 前端API配置
在前端项目中配置API基础URL：

```javascript
// frontend/src/utils/api.js
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'https://w3.799n.com'  // 生产环境指向后端域名
  : 'http://localhost:5000';  // 开发环境本地后端

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  withCredentials: true
});
```

## ✅ 验证清单

### 前端验证 (w4.799n.com)
- [ ] 静态页面访问正常
- [ ] 前端路由工作 (刷新不404)
- [ ] 静态资源加载正常
- [ ] SSL证书有效

### 后端验证 (w3.799n.com)
- [ ] API健康检查: `curl https://w3.799n.com/api/health`
- [ ] 直接API访问正常
- [ ] CORS头配置正确
- [ ] SSL证书有效

### 集成验证
- [ ] 前端可以调用后端API
- [ ] 登录功能正常
- [ ] 跨域问题解决
- [ ] WebSocket连接正常 (如果使用)

## 🔧 故障排除

### 常见问题

**1. CORS错误**
```bash
# 检查后端Nginx配置中的CORS头
curl -H "Origin: https://w4.799n.com" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: Authorization" \
     -X OPTIONS \
     https://w3.799n.com/api/health
```

**2. API代理失败**
```bash
# 检查前端Nginx配置的代理设置
# 确保 proxy_pass 指向正确的后端地址
```

**3. SSL证书问题**
```bash
# 检查两个域名的证书是否都配置正确
curl -I https://w4.799n.com
curl -I https://w3.799n.com
```

**4. Docker服务无法访问**
```bash
# 检查Docker容器状态
docker ps
curl http://127.0.0.1:5000/api/health
```

## 📊 性能优化建议

### 1. 缓存策略
- 前端静态资源：长期缓存
- 后端API响应：根据业务需求设置
- HTML文件：不缓存确保更新生效

### 2. 负载均衡
如果后端扩展多个实例：
```nginx
upstream backend_pool {
    server 127.0.0.1:5001;
    server 127.0.0.1:5002;
    server 127.0.0.1:5003;
}

location / {
    proxy_pass http://backend_pool;
}
```

### 3. 监控设置
- 监控两个域名的响应时间
- 监控API调用成功率
- 监控SSL证书过期时间

这种域名分离方案提供了清晰的职责划分和更好的扩展性！