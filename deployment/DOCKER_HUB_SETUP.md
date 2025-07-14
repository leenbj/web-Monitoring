# Docker Hub 配置指南

## 🔧 解决构建错误："Error: Forbidden"

### 问题原因
GitHub Actions在更新Docker Hub仓库描述时遇到权限问题，主要原因：
1. Docker Hub Access Token权限不足
2. 仓库不存在或名称不匹配
3. README文件过大

### 🔧 解决方案

#### 步骤1: 重新创建Docker Hub Access Token

1. **登录Docker Hub**
   - 访问 [https://hub.docker.com/](https://hub.docker.com/)
   - 登录你的账户

2. **创建新的Access Token**
   ```
   右上角头像 → Account Settings → Security → New Access Token
   ```

3. **设置Token权限**
   ```
   Token名称: github-actions-website-monitor
   权限: 选择 "Read, Write, Delete" (全部权限)
   ```

4. **复制Token**
   - ⚠️ **重要**: Token只显示一次，必须立即复制保存

#### 步骤2: 更新GitHub Secrets

1. **进入GitHub仓库设置**
   ```
   仓库页面 → Settings → Secrets and variables → Actions
   ```

2. **更新Secrets**
   ```bash
   # 更新或添加以下Secrets:
   DOCKERHUB_USERNAME=你的Docker Hub用户名
   DOCKERHUB_TOKEN=刚创建的新Token
   ```

3. **验证用户名格式**
   ```bash
   # 确保用户名格式正确，例如:
   ✅ 正确: mycompany
   ✅ 正确: john-doe
   ❌ 错误: MyCompany (大小写敏感)
   ❌ 错误: my company (不能有空格)
   ```

#### 步骤3: 验证Docker Hub仓库

1. **检查仓库是否存在**
   - 访问: `https://hub.docker.com/r/你的用户名/website-monitor-backend`
   - 如果不存在，首次推送时会自动创建

2. **检查仓库权限**
   - 确保你对该仓库有写入权限
   - 如果是组织仓库，确保你有管理员权限

### 🚀 测试构建

#### 方法1: 推送代码触发
```bash
# 提交并推送修复后的代码
git add .
git commit -m "fix: 修复Docker Hub构建权限问题"
git push origin main
```

#### 方法2: 手动触发构建
```bash
# 在GitHub仓库页面:
Actions → Backend Docker Build and Push to Docker Hub → Run workflow
```

### 📊 验证构建成功

#### 1. 检查GitHub Actions日志
```bash
# 成功的构建日志应该显示:
✅ Checkout code
✅ Set up Docker Buildx  
✅ Log in to Docker Hub
✅ Extract metadata
✅ Build and push Docker image
✅ Image build summary
```

#### 2. 检查Docker Hub
```bash
# 访问Docker Hub仓库页面，应该能看到:
- 新的镜像标签 (latest, main-xxx等)
- 更新的推送时间
- 镜像大小信息
```

#### 3. 本地测试拉取
```bash
# 测试能否拉取构建的镜像
docker pull 你的用户名/website-monitor-backend:latest
docker run --rm 你的用户名/website-monitor-backend:latest echo "构建成功!"
```

### 🔧 常见问题排查

#### 问题1: "Repository not found"
```bash
解决方案:
1. 检查用户名是否正确
2. 检查仓库名称是否匹配
3. 确保仓库为public (如果使用免费账户)
```

#### 问题2: "Authentication failed"
```bash
解决方案:
1. 重新生成Docker Hub Access Token
2. 确保Token权限为 "Read, Write, Delete"
3. 检查GitHub Secrets中的Token是否正确
```

#### 问题3: "Rate limit exceeded"
```bash
解决方案:
1. 等待一段时间后重试
2. 如果是免费账户，考虑升级到付费计划
3. 减少构建频率
```

#### 问题4: 镜像构建成功但描述更新失败
```bash
解决方案:
1. 这是正常的，主要功能(镜像构建)已成功
2. 可以手动在Docker Hub网页上更新描述
3. 或者删除描述更新步骤(已在新版本中删除)
```

### 📋 最佳实践

#### 1. Token管理
- 为每个项目创建单独的Token
- 定期轮换Token (建议3-6个月)
- 不要在代码中硬编码Token
- 使用GitHub Secrets安全存储

#### 2. 构建优化
```yaml
# 推荐的构建触发条件:
on:
  push:
    branches: [ main ]  # 只在主分支构建
    paths:             # 只在相关文件变化时构建
      - 'backend/**'
      - 'requirements.txt'
      - 'Dockerfile'
```

#### 3. 版本管理
```bash
# 使用语义化版本标签
git tag v1.0.0
git push origin v1.0.0

# 这将触发构建标签版本的镜像
```

### 🎯 验证清单

构建成功后，确认以下项目：

- [ ] GitHub Actions工作流运行成功
- [ ] Docker Hub仓库中有新镜像
- [ ] 镜像标签正确 (latest, main-xxx等)  
- [ ] 能够本地拉取镜像
- [ ] 镜像大小合理 (~200MB)
- [ ] 支持多架构 (amd64/arm64)

### 📞 获取帮助

如果仍然遇到问题：

1. **检查GitHub Actions日志**: 点击失败的构建查看详细错误
2. **查看Docker Hub状态**: https://status.docker.com/
3. **参考官方文档**: https://docs.docker.com/docker-hub/access-tokens/
4. **GitHub Issues**: 在项目仓库创建Issue求助

---

*© 2024 网址监控系统 | Docker Hub配置指南 v1.0*