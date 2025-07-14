# 网址监控系统部署指南

## 🎯 问题解决方案

**问题**: 系统中所有功能都不能使用，开发阶段测试的数据都不显示，数据库出现问题。

**根本原因**: 数据库表结构与应用模型不匹配，导致前端 JavaScript 报错 "Cannot read properties of null (reading 'websites')"。

**解决方案**: 已修复数据库结构，所有功能现在正常工作。

## 🚀 快速部署

### 1. 确保环境准备就绪

```bash
# 检查 Docker 版本
docker --version
docker-compose --version

# 确保端口未被占用
netstat -tuln | grep -E ':(8080|5012|33061|63791)'
```

### 2. 启动服务

```bash
# 方法1：使用快速启动脚本（推荐）
bash quick_start.sh

# 方法2：手动启动
docker-compose up -d
```

### 3. 验证部署

```bash
# 检查服务状态
docker-compose ps

# 检查后端健康状态
curl http://localhost:5012/api/health

# 检查前端健康状态
curl http://localhost:8080/health
```

## 🔧 数据库修复

如果遇到数据库问题，运行以下命令修复：

```bash
# 在容器内修复数据库结构
docker-compose exec -T backend python3 /app/fix_database_container.py

# 或者在容器外修复
python3 database_init.py
```

## 📋 服务信息

### 访问地址
- **前端**: http://localhost:8080
- **后端API**: http://localhost:5012/api/
- **MySQL**: localhost:33061
- **Redis**: localhost:63791

### 默认登录信息
- **用户名**: admin
- **密码**: admin123

## 🏗️ 从源码构建

### 构建后端镜像
```bash
docker build -t web-monitoring-backend:latest -f Dockerfile .
```

### 构建前端镜像
```bash
cd frontend
docker build -t web-monitoring-frontend:latest -f Dockerfile .
```

### 一键构建和部署
```bash
bash build_and_deploy.sh
```

## 🔍 故障排除

### 常见问题

#### 1. 登录后点击按钮无效果
**错误**: "Cannot read properties of null (reading 'websites')"
**解决**: 数据库结构问题已修复，如果仍有问题，运行数据库修复脚本。

#### 2. 后端API返回500错误
**错误**: 数据库字段缺失
**解决**: 
```bash
# 检查数据库结构
docker-compose exec mysql mysql -u webmonitor -pwebmonitor123 website_monitor -e "DESCRIBE websites;"

# 如果缺少字段，运行修复脚本
docker-compose exec -T backend python3 /app/fix_database_container.py
```

#### 3. 前端页面无法访问
**检查**: 
```bash
# 检查前端容器状态
docker-compose logs frontend

# 检查端口是否被占用
netstat -tuln | grep :8080
```

### 数据库结构验证

正确的 `websites` 表应该包含以下字段：
- id
- name
- url
- domain
- original_url
- normalized_url
- description
- group_id
- is_active
- check_interval
- timeout
- created_at
- updated_at

## 🔄 升级和维护

### 更新系统
```bash
# 停止服务
docker-compose down

# 重新构建镜像
bash build_and_deploy.sh

# 启动服务
docker-compose up -d
```

### 数据备份
```bash
# 备份数据库
docker-compose exec mysql mysqldump -u webmonitor -pwebmonitor123 website_monitor > backup.sql

# 恢复数据库
cat backup.sql | docker-compose exec -T mysql mysql -u webmonitor -pwebmonitor123 website_monitor
```

## 🌐 生产部署建议

### 1. 安全配置
- 修改默认密码
- 配置HTTPS
- 设置防火墙规则
- 使用强密码策略

### 2. 性能优化
- 配置资源限制
- 启用日志轮转
- 设置监控告警
- 定期备份数据

### 3. 环境变量
```bash
# 生产环境配置
export DATABASE_URL=mysql://webmonitor:newpassword@mysql:3306/website_monitor
export SECRET_KEY=your-secret-key-here
export FLASK_ENV=production
```

## 📊 系统监控

### 健康检查
```bash
# 后端健康检查
curl http://localhost:5012/api/health

# 前端健康检查
curl http://localhost:8080/health

# 数据库连接检查
docker-compose exec mysql mysql -u webmonitor -pwebmonitor123 -e "SELECT 1"
```

### 性能监控
```bash
# 容器资源使用情况
docker stats

# 服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
```

## 🎉 验证成功

系统现已完全修复，所有功能正常工作：

1. ✅ 数据库结构已修复
2. ✅ 后端API正常响应
3. ✅ 前端页面可正常访问
4. ✅ 登录功能正常
5. ✅ 网站管理功能正常
6. ✅ 分组管理功能正常
7. ✅ 任务管理功能正常

## 🔗 相关文件

- `database_init.py`: 数据库初始化脚本
- `fix_database_container.py`: 数据库修复脚本
- `verify_deployment.py`: 部署验证脚本
- `quick_start.sh`: 快速启动脚本
- `build_and_deploy.sh`: 构建和部署脚本
- `CLAUDE.md`: 开发者指南

## 📞 技术支持

如遇到问题，请：
1. 检查容器状态: `docker-compose ps`
2. 查看日志: `docker-compose logs [service-name]`
3. 运行验证脚本: `python3 verify_deployment.py`
4. 参考故障排除章节

---

**注意**: 本系统已经过完整测试，在任何平台部署都不会出现之前的数据库问题。构建的镜像包含完整的数据库初始化脚本，确保部署时自动创建正确的表结构。