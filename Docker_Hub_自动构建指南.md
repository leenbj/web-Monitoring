# Docker Hub 自动构建指南

## 📋 目录

1. [项目概述](#项目概述)
2. [准备工作](#准备工作)
3. [GitHub 仓库设置](#github-仓库设置)
4. [Docker Hub 账户准备](#docker-hub-账户准备)
5. [自动构建设置](#自动构建设置)
6. [多架构构建支持](#多架构构建支持)
7. [部署验证](#部署验证)
8. [常见问题解决](#常见问题解决)
9. [维护与更新](#维护与更新)

## 📖 项目概述

网址监控系统是一个基于 Flask + Vue.js 的全栈网站监控解决方案。通过 Docker Hub 自动构建，我们可以：

- ✅ 解决架构兼容性问题（支持 AMD64/ARM64）
- ✅ 自动化构建和发布流程
- ✅ 确保镜像质量和安全性
- ✅ 简化部署流程

## 🛠️ 准备工作

### 1. 环境要求

- GitHub 账户
- Docker Hub 账户
- Git 工具
- 本地 Docker 环境（可选，用于测试）

### 2. 项目文件清理

项目已经通过清理脚本优化，当前项目大小：**15MB**（从 581MB 减少 98%）

```bash
# 查看项目大小
du -sh .
# 15M    .
```

### 3. 核心文件结构

```
网址监控/
├── Dockerfile              # 主构建文件
├── start.sh                # 启动脚本
├── docker-compose.yml      # 部署配置
├── requirements.txt        # Python依赖
├── .dockerignore          # 构建忽略文件
├── .gitignore             # Git忽略文件
├── backend/               # 后端代码
├── frontend/              # 前端代码
├── database/              # 数据库初始化
├── init_database.py       # 数据库初始化脚本
└── run_backend.py         # 后端启动脚本
```

## 📁 GitHub 仓库设置

### 1. 创建 GitHub 仓库

```bash
# 1. 在 GitHub 创建新仓库
# 仓库名建议：web-monitor 或 website-monitor

# 2. 克隆或推送代码到仓库
git init
git add .
git commit -m "Initial commit: 网址监控系统"
git remote add origin https://github.com/你的用户名/web-monitor.git
git push -u origin main
```

### 2. 仓库结构优化

确保仓库包含以下必要文件：

```bash
# 检查必要文件
ls -la Dockerfile start.sh docker-compose.yml requirements.txt

# 应该显示：
# -rw-r--r-- 1 user user 6.2K Dockerfile
# -rw-r--r-- 1 user user 2.1K start.sh
# -rw-r--r-- 1 user user 3.8K docker-compose.yml
# -rw-r--r-- 1 user user 771B requirements.txt
```

### 3. 添加构建标签

在仓库中添加适当的标签：

```bash
# 创建版本标签
git tag -a v1.0.0 -m "网址监控系统 v1.0.0"
git push origin v1.0.0

# 创建latest标签
git tag -a latest -m "最新稳定版"
git push origin latest
```

## 🐳 Docker Hub 账户准备

### 1. 注册 Docker Hub 账户

访问 [Docker Hub](https://hub.docker.com) 注册账户。

### 2. 创建仓库

1. 登录 Docker Hub
2. 点击 "Create Repository"
3. 填写仓库信息：
   - **Repository Name**: `webmonitor-backend`
   - **Description**: `网址监控系统后端服务 - 支持多架构部署`
   - **Visibility**: Public（或 Private）

### 3. 获取访问令牌

1. 进入 Account Settings > Security
2. 点击 "New Access Token"
3. 创建令牌：
   - **Token Name**: `GitHub Actions`
   - **Permissions**: Read, Write, Delete
4. 复制并保存令牌

## ⚙️ 自动构建设置

### 方案一：Docker Hub 自动构建（推荐）

#### 1. 连接 GitHub

1. 在 Docker Hub 仓库页面，点击 "Builds" 标签
2. 点击 "Configure Automated Builds"
3. 选择 GitHub，授权连接
4. 选择你的 GitHub 仓库

#### 2. 配置构建规则

| 源类型 | 源         | Docker 标签 | Dockerfile 位置 | 构建上下文 |
|--------|------------|-------------|----------------|------------|
| Branch | main       | latest      | Dockerfile     | /          |
| Tag    | /^v.*$/    | {sourceref} | Dockerfile     | /          |

#### 3. 高级设置

```yaml
# 构建环境变量
BUILD_DATE: {BUILD_DATE}
VCS_REF: {SOURCE_COMMIT}
VERSION: {DOCKER_TAG}
```

### 方案二：GitHub Actions 自动构建

创建 `.github/workflows/docker-build.yml`：

```yaml
name: Docker Build and Push

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout
      uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Login to Docker Hub
      uses: docker/login-action@v2
      with:
        username: ${{ secrets.DOCKERHUB_USERNAME }}
        password: ${{ secrets.DOCKERHUB_TOKEN }}
    
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v4
      with:
        images: ${{ secrets.DOCKERHUB_USERNAME }}/webmonitor-backend
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}
          type=raw,value=latest,enable={{is_default_branch}}
    
    - name: Build and push
      uses: docker/build-push-action@v4
      with:
        context: .
        file: ./Dockerfile
        platforms: linux/amd64,linux/arm64
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        build-args: |
          BUILD_DATE=${{ fromJSON(steps.meta.outputs.json).labels['org.opencontainers.image.created'] }}
          VCS_REF=${{ fromJSON(steps.meta.outputs.json).labels['org.opencontainers.image.revision'] }}
          VERSION=${{ fromJSON(steps.meta.outputs.json).labels['org.opencontainers.image.version'] }}
```

### GitHub Secrets 配置

在 GitHub 仓库设置中添加以下 Secrets：

- `DOCKERHUB_USERNAME`: 你的 Docker Hub 用户名
- `DOCKERHUB_TOKEN`: 之前创建的访问令牌

## 🏗️ 多架构构建支持

### 1. 构建支持的架构

- `linux/amd64`: X86_64 架构（Intel/AMD 处理器）
- `linux/arm64`: ARM64 架构（Apple Silicon, ARM 服务器）

### 2. 本地测试多架构构建

```bash
# 创建新的构建器
docker buildx create --name multiarch-builder --use

# 构建多架构镜像
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag 你的用户名/webmonitor-backend:latest \
  --push .

# 验证多架构支持
docker buildx imagetools inspect 你的用户名/webmonitor-backend:latest
```

## 📦 部署验证

### 1. 更新 docker-compose.yml

```yaml
services:
  backend:
    # 使用你的 Docker Hub 镜像
    image: 你的用户名/webmonitor-backend:latest
    # ... 其他配置
```

### 2. 拉取镜像

```bash
# 拉取最新镜像
docker pull 你的用户名/webmonitor-backend:latest

# 检查镜像信息
docker images | grep webmonitor-backend
```

### 3. 启动服务

```bash
# 启动完整服务
docker-compose up -d

# 检查服务状态
docker-compose ps

# 检查后端健康状态
curl http://localhost:5012/api/health
```

### 4. 验证架构兼容性

```bash
# 检查容器架构
docker inspect 你的用户名/webmonitor-backend:latest | grep Architecture

# 检查运行中的容器
docker exec webmonitor-backend uname -m
```

## 🔧 常见问题解决

### 1. 构建失败

**问题**: Docker Hub 构建失败
**解决方案**:
```bash
# 检查 Dockerfile 语法
docker build --no-cache -t test-build .

# 检查构建日志
# 在 Docker Hub 构建页面查看详细日志
```

### 2. 镜像拉取失败

**问题**: 拉取镜像时出现架构不匹配
**解决方案**:
```bash
# 指定特定架构
docker pull --platform linux/amd64 你的用户名/webmonitor-backend:latest

# 或者使用 Docker Buildx
docker buildx build --platform linux/amd64 -t local-test .
```

### 3. 服务启动失败

**问题**: 容器启动后立即退出
**解决方案**:
```bash
# 查看容器日志
docker logs webmonitor-backend

# 进入容器调试
docker run -it --rm 你的用户名/webmonitor-backend:latest bash

# 检查启动脚本
docker run -it --rm 你的用户名/webmonitor-backend:latest cat /app/start.sh
```

### 4. 网络连接问题

**问题**: 容器间无法通信
**解决方案**:
```bash
# 检查网络配置
docker network ls
docker network inspect webmonitor_default

# 检查容器网络
docker exec webmonitor-backend ping mysql
docker exec webmonitor-backend ping redis
```

## 📝 维护与更新

### 1. 版本管理

```bash
# 发布新版本
git tag -a v1.1.0 -m "添加新功能"
git push origin v1.1.0

# 自动触发构建
# Docker Hub 或 GitHub Actions 会自动构建新版本
```

### 2. 镜像清理

```bash
# 定期清理旧镜像
docker image prune -a

# 清理未使用的卷
docker volume prune

# 清理未使用的网络
docker network prune
```

### 3. 安全更新

```bash
# 定期更新基础镜像
# 在 Dockerfile 中使用固定版本号
FROM python:3.11-slim-bullseye

# 定期检查依赖更新
pip list --outdated
```

### 4. 监控与日志

```bash
# 查看应用日志
docker-compose logs -f backend

# 监控资源使用
docker stats webmonitor-backend

# 健康检查
curl http://localhost:5012/api/health
```

## 🎯 最佳实践

### 1. 安全性

- 使用非 root 用户运行容器
- 定期更新基础镜像
- 扫描镜像漏洞
- 使用 secrets 管理敏感信息

### 2. 性能优化

- 使用多阶段构建
- 优化镜像层数
- 使用 .dockerignore 减少构建上下文
- 利用构建缓存

### 3. 可靠性

- 实现健康检查
- 使用重启策略
- 配置适当的资源限制
- 监控应用状态

## 📞 技术支持

如果在构建过程中遇到问题，可以：

1. 查看 Docker Hub 构建日志
2. 检查 GitHub Actions 运行状态
3. 验证 Dockerfile 语法
4. 测试本地构建

---

**构建状态检查清单**:

- [ ] GitHub 仓库创建并推送代码
- [ ] Docker Hub 仓库创建
- [ ] 自动构建配置完成
- [ ] 多架构构建支持
- [ ] 镜像成功推送
- [ ] 部署测试通过
- [ ] 健康检查正常
- [ ] 监控和日志配置

完成以上步骤后，你的网址监控系统将拥有完全自动化的构建和部署流程！🚀 