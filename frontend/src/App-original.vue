<template>
  <div id="app">
    <el-container class="layout-container">
      <!-- 头部导航 -->
      <el-header class="header">
        <div class="header-content">
          <h1 class="title">
            <el-icon><Monitor /></el-icon>
            网址监控工具
          </h1>
          <el-menu
            mode="horizontal"
            :default-active="$route.path"
            router
            class="nav-menu"
          >
            <el-menu-item index="/websites">
              <el-icon><Globe /></el-icon>
              网站管理
            </el-menu-item>
            <el-menu-item index="/tasks">
              <el-icon><Timer /></el-icon>
              任务管理
            </el-menu-item>
            <el-menu-item index="/results">
              <el-icon><DataAnalysis /></el-icon>
              检测结果
            </el-menu-item>
            <el-menu-item index="/files">
              <el-icon><Document /></el-icon>
              文件管理
            </el-menu-item>
          </el-menu>
        </div>
      </el-header>

      <!-- 主内容区域 -->
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script>
import { Monitor, Globe, Timer, DataAnalysis, Document } from '@element-plus/icons-vue'

export default {
  name: 'App',
  components: {
    Monitor,
    Globe,
    Timer,
    DataAnalysis,
    Document
  }
}
</script>

<style scoped>
.layout-container {
  min-height: 100vh;
}

.header {
  background-color: #409eff;
  color: white;
  display: flex;
  align-items: center;
  padding: 0 20px;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.title {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 24px;
  font-weight: 600;
}

.nav-menu {
  background-color: transparent;
  border-bottom: none;
}

.nav-menu .el-menu-item {
  color: white;
  border-bottom: 2px solid transparent;
}

.nav-menu .el-menu-item:hover,
.nav-menu .el-menu-item.is-active {
  background-color: rgba(255, 255, 255, 0.1);
  border-bottom-color: white;
  color: white;
}

.main-content {
  padding: 20px;
  background-color: #f5f5f5;
  min-height: calc(100vh - 60px);
}

/* 全局样式 */
:global(body) {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
}

:global(#app) {
  min-height: 100vh;
}
</style> 