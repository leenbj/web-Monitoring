<template>
  <div id="app">
    <!-- 登录页面单独显示 -->
    <div v-if="$route.name === 'Login'" class="login-layout">
      <router-view />
    </div>

    <!-- 主应用布局 -->
    <el-container v-else class="layout-container">
      <!-- 侧边导航栏 -->
      <el-aside class="sidebar" :width="isCollapsed ? '64px' : '240px'">
        <div class="sidebar-header">
          <div class="logo">
            <el-icon class="logo-icon" size="32"><Monitor /></el-icon>
            <transition name="fade">
              <span v-show="!isCollapsed" class="logo-text">网址监控</span>
            </transition>
          </div>
          <el-button 
            class="collapse-btn" 
            @click="toggleSidebar"
            :icon="isCollapsed ? Expand : Fold"
            circle
            size="small"
          />
        </div>
        
        <el-menu
          :default-active="$route.path"
          router
          class="nav-menu"
          :collapse="isCollapsed"
          :collapse-transition="false"
        >
          <el-menu-item index="/" class="menu-item">
            <el-icon><House /></el-icon>
            <template #title>监控首页</template>
          </el-menu-item>
          <el-menu-item index="/websites" class="menu-item">
            <el-icon><Link /></el-icon>
            <template #title>网站管理</template>
          </el-menu-item>
          <el-menu-item index="/groups" class="menu-item">
            <el-icon><Collection /></el-icon>
            <template #title>分组管理</template>
          </el-menu-item>
          <el-menu-item index="/tasks" class="menu-item">
            <el-icon><Timer /></el-icon>
            <template #title>任务管理</template>
          </el-menu-item>
          <el-menu-item index="/results" class="menu-item">
            <el-icon><DataAnalysis /></el-icon>
            <template #title>检测结果</template>
          </el-menu-item>
          <el-menu-item index="/status-changes" class="menu-item">
            <el-icon><Warning /></el-icon>
            <template #title>状态变化</template>
          </el-menu-item>
          <el-menu-item index="/files" class="menu-item">
            <el-icon><Document /></el-icon>
            <template #title>文件管理</template>
          </el-menu-item>

          <!-- 系统设置子菜单 -->
          <el-sub-menu index="settings" class="menu-item">
            <template #title>
              <el-icon><Setting /></el-icon>
              <span>系统设置</span>
            </template>
            <el-menu-item index="/profile" class="sub-menu-item">
              <el-icon><UserFilled /></el-icon>
              <template #title>个人信息</template>
            </el-menu-item>
            <el-menu-item v-if="userStore.isAdmin" index="/users" class="sub-menu-item">
              <el-icon><User /></el-icon>
              <template #title>用户管理</template>
            </el-menu-item>
            <el-menu-item v-if="userStore.isAdmin" index="/settings" class="sub-menu-item">
              <el-icon><Setting /></el-icon>
              <template #title>系统配置</template>
            </el-menu-item>
          </el-sub-menu>
        </el-menu>
      </el-aside>

      <!-- 主内容区域 -->
      <el-container class="main-container">
        <!-- 顶部状态栏 -->
        <el-header class="header" height="60px">
          <div class="header-content">
            <div class="breadcrumb">
              <span class="current-page">{{ getCurrentPageTitle() }}</span>
            </div>
            <div class="header-actions">
              <!-- 用户信息 -->
              <div class="user-info">
                <el-dropdown @command="handleUserCommand">
                  <span class="user-dropdown">
                    <el-icon class="user-icon"><UserFilled /></el-icon>
                    <span class="username">{{ userStore.user?.username || '用户' }}</span>
                    <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
                  </span>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="profile">
                        <el-icon><UserFilled /></el-icon>
                        个人信息
                      </el-dropdown-item>
                      <el-dropdown-item v-if="userStore.isAdmin" command="users">
                        <el-icon><User /></el-icon>
                        用户管理
                      </el-dropdown-item>
                      <el-dropdown-item divided command="logout">
                        <el-icon><SwitchButton /></el-icon>
                        退出登录
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>

              <el-tooltip :content="systemStatus ? '系统在线 - 点击切换' : '系统离线 - 点击切换'" placement="bottom">
                <div class="system-status-indicator" @click="toggleSystemStatus">
                  <div
                    class="status-dot"
                    :class="{
                      'online': systemStatus,
                      'offline': !systemStatus
                    }"
                  >
                    <div class="status-pulse"></div>
                  </div>
                  <span class="status-text">{{ systemStatus ? '在线' : '离线' }}</span>
                </div>
              </el-tooltip>
            </div>
          </div>
        </el-header>

        <!-- 主内容 -->
        <el-main class="main-content">
          <div class="content-container">
            <router-view />
          </div>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'
import {
  Monitor,
  House,
  Link,
  Collection,
  Timer,
  DataAnalysis,
  Document,
  Expand,
  Fold,
  CircleCheck,
  CircleClose,
  Warning,
  Setting,
  User,
  UserFilled,
  ArrowDown,
  SwitchButton
} from '@element-plus/icons-vue'

export default {
  name: 'App',
  components: {
    Monitor,
    House,
    Link,
    Collection,
    Timer,
    DataAnalysis,
    Document,
    Expand,
    Fold,
    CircleCheck,
    CircleClose,
    Warning,
    Setting,
    User,
    UserFilled,
    ArrowDown,
    SwitchButton
  },
  setup() {
    const route = useRoute()
    const router = useRouter()
    const userStore = useUserStore()
    const isCollapsed = ref(false)
    const systemStatus = ref(true)
    const statusBadge = ref('')
    
    const statusType = computed(() => {
      return systemStatus.value ? 'success' : 'danger'
    })

    const toggleSidebar = () => {
      isCollapsed.value = !isCollapsed.value
    }

    const toggleSystemStatus = () => {
      systemStatus.value = !systemStatus.value
    }

    const getCurrentPageTitle = () => {
      const titleMap = {
        '/': '监控首页',
        '/websites': '网站管理',
        '/groups': '分组管理',
        '/tasks': '任务管理',
        '/results': '检测结果',
        '/status-changes': '状态变化',
        '/files': '文件管理',
        '/users': '用户管理',
        '/profile': '个人信息',
        '/settings': '系统设置'
      }
      return titleMap[route.path] || '网址监控工具'
    }

    // 处理用户下拉菜单命令
    const handleUserCommand = async (command) => {
      switch (command) {
        case 'profile':
          router.push('/profile')
          break
        case 'users':
          router.push('/users')
          break
        case 'logout':
          try {
            await ElMessageBox.confirm('确定要退出登录吗？', '确认退出', {
              confirmButtonText: '确定',
              cancelButtonText: '取消',
              type: 'warning'
            })

            await userStore.logout()
            ElMessage.success('退出登录成功')
            router.push('/login')
          } catch (error) {
            if (error !== 'cancel') {
              console.error('退出登录失败:', error)
              ElMessage.error('退出登录失败')
            }
          }
          break
      }
    }

    return {
      userStore,
      isCollapsed,
      systemStatus,
      statusBadge,
      statusType,
      toggleSidebar,
      toggleSystemStatus,
      getCurrentPageTitle,
      handleUserCommand
    }
  }
}
</script>

<style scoped>
.layout-container {
  min-height: 100vh;
  background-color: #fafafa;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

/* 侧边栏样式 - Claude风格 */
.sidebar {
  background: #ffffff;
  border-right: 1px solid #e5e7eb;
  box-shadow: none;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.sidebar-header {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  border-bottom: 1px solid #f3f4f6;
  background: #ffffff;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #111827;
  font-weight: 600;
  font-size: 18px;
  letter-spacing: -0.025em;
}

.logo-icon {
  color: #1a1a1a;
  filter: none;
}

.logo-text {
  white-space: nowrap;
  overflow: hidden;
  color: #111827;
}

.collapse-btn {
  background: transparent;
  border: none;
  color: #6b7280;
  padding: 6px;
  border-radius: 6px;
}

.collapse-btn:hover {
  background: #f9fafb;
  color: #374151;
}

/* 导航菜单样式 - Claude风格 + 黄色动画特效 */
.nav-menu {
  background: transparent;
  border: none;
  margin-top: 8px;
  padding: 0 12px;
}

.nav-menu .el-menu-item {
  color: #6b7280;
  border-radius: 8px;
  margin: 2px 0;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  height: 40px;
  line-height: 40px;
  font-weight: 500;
  font-size: 14px;
  padding: 0 12px;
  position: relative;
  overflow: hidden;
}

.nav-menu .el-menu-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(0, 0, 0, 0.1), transparent);
  transition: left 0.5s ease;
}

.nav-menu .el-menu-item:hover {
  background: #f9fafb;
  color: #374151;
  transform: translateX(2px) scale(1.02);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.nav-menu .el-menu-item:hover::before {
  left: 100%;
}

.nav-menu .el-menu-item.is-active {
  background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
  color: #ffffff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  border-left: 3px solid #000000;
  animation: menuItemGlow 2s ease-in-out infinite alternate;
}

.nav-menu .el-menu-item.is-active .el-icon {
  color: #ffffff !important;
  animation: iconPulse 1.5s ease-in-out infinite;
}

.nav-menu .el-menu-item .el-icon {
  margin-right: 10px;
  font-size: 16px;
  transition: all 0.3s ease;
}

/* 子菜单样式 */
.nav-menu .el-sub-menu {
  margin: 2px 0;
}

.nav-menu .el-sub-menu .el-sub-menu__title {
  color: #6b7280 !important;
  border-radius: 8px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  height: 40px;
  line-height: 40px;
  padding: 0 12px;
  position: relative;
  overflow: hidden;
  font-weight: 500;
  font-size: 14px;
}

.nav-menu .el-sub-menu .el-sub-menu__title .el-icon {
  margin-right: 10px;
  font-size: 16px;
  transition: all 0.3s ease;
  color: #6b7280 !important;
}

.nav-menu .el-sub-menu .el-sub-menu__title span {
  color: #6b7280 !important;
  font-weight: 500;
  font-size: 14px;
}

.nav-menu .el-sub-menu .el-sub-menu__title::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(0, 0, 0, 0.1), transparent);
  transition: left 0.5s ease;
}

.nav-menu .el-sub-menu .el-sub-menu__title:hover {
  background: #f9fafb;
  color: #374151 !important;
  transform: translateX(2px) scale(1.02);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.nav-menu .el-sub-menu .el-sub-menu__title:hover .el-icon {
  color: #374151 !important;
}

.nav-menu .el-sub-menu .el-sub-menu__title:hover span {
  color: #374151 !important;
}

.nav-menu .el-sub-menu .el-sub-menu__title:hover::before {
  left: 100%;
}

/* 子菜单父级激活时不改变标题样式，保持默认样式 */
.nav-menu .el-sub-menu.is-active .el-sub-menu__title {
  background: transparent;
  color: #6b7280 !important;
  box-shadow: none;
  border-left: none;
}

.nav-menu .el-sub-menu.is-active .el-sub-menu__title .el-icon {
  color: #6b7280 !important;
  animation: none;
}

.nav-menu .el-sub-menu.is-active .el-sub-menu__title span {
  color: #6b7280 !important;
}

/* 子菜单父级激活且悬停时的样式 */
.nav-menu .el-sub-menu.is-active .el-sub-menu__title:hover {
  background: #f9fafb;
  color: #374151 !important;
  transform: translateX(2px) scale(1.02);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.nav-menu .el-sub-menu.is-active .el-sub-menu__title:hover .el-icon {
  color: #374151 !important;
}

.nav-menu .el-sub-menu.is-active .el-sub-menu__title:hover span {
  color: #374151 !important;
}

.nav-menu .el-sub-menu .el-menu {
  background: transparent;
}

.nav-menu .el-sub-menu .el-menu-item {
  padding-left: 40px !important;
  background: rgba(249, 250, 251, 0.5);
  margin: 1px 0;
  border-radius: 6px;
}

.nav-menu .el-sub-menu .el-menu-item:hover {
  background: #e5e7eb;
  padding-left: 44px !important;
}

.nav-menu .el-sub-menu .el-menu-item.is-active {
  background: linear-gradient(135deg, #374151 0%, #1f2937 100%);
  color: #ffffff;
  border-left: 2px solid #000000;
}

/* 菜单项动画 */
@keyframes menuItemGlow {
  0% {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
  }
  100% {
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
    background: linear-gradient(135deg, #111827 0%, #000000 100%);
  }
}

@keyframes iconPulse {
  0%, 100% {
    transform: scale(1);
    filter: drop-shadow(0 0 0 rgba(255, 255, 255, 0.3));
  }
  50% {
    transform: scale(1.1);
    filter: drop-shadow(0 0 8px rgba(255, 255, 255, 0.4));
  }
}

/* 主容器样式 */
.main-container {
  background-color: #fafafa;
}

/* 顶部header样式 - Claude风格 */
.header {
  background: #ffffff;
  border-bottom: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  padding: 0 32px;
}

.breadcrumb {
  display: flex;
  align-items: center;
}

.current-page {
  font-size: 20px;
  font-weight: 600;
  color: #111827;
  letter-spacing: -0.025em;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 用户信息样式 */
.user-info {
  display: flex;
  align-items: center;
}

.user-dropdown {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(4px);
  transition: all 0.3s ease;
  cursor: pointer;
  user-select: none;
  height: 32px; /* 与系统状态指示器一致的高度 */
}

.user-dropdown:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: scale(1.05);
}

.user-dropdown:active {
  transform: scale(0.95);
  background: rgba(255, 255, 255, 0.3);
}

.user-icon {
  font-size: 16px;
  color: #374151;
}

.username {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  white-space: nowrap;
}

.dropdown-icon {
  font-size: 12px;
  color: #6b7280;
  transition: transform 0.3s ease;
}

.user-dropdown:hover .dropdown-icon {
  transform: rotate(180deg);
}

/* 用户下拉菜单项样式 */
.user-info :deep(.el-dropdown-menu) {
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  padding: 4px;
  min-width: 150px;
}

.user-info :deep(.el-dropdown-menu__item) {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  padding: 8px 12px;
  margin: 2px 0;
  border-radius: 6px;
  transition: all 0.15s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-info :deep(.el-dropdown-menu__item:hover) {
  background-color: #f9fafb;
  color: #111827;
  transform: translateX(2px);
}

.user-info :deep(.el-dropdown-menu__item.is-divided) {
  border-top: 1px solid #e5e7eb;
  margin-top: 8px;
  padding-top: 12px;
}

.user-info :deep(.el-dropdown-menu__item .el-icon) {
  font-size: 16px;
  color: #6b7280;
  transition: color 0.15s ease;
}

.user-info :deep(.el-dropdown-menu__item:hover .el-icon) {
  color: #374151;
}

/* 系统状态指示器 */
.system-status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(4px);
  transition: all 0.3s ease;
  cursor: pointer;
  user-select: none;
  height: 32px; /* 与用户信息下拉框一致的高度 */
}

.system-status-indicator:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: scale(1.05);
}

.system-status-indicator:active {
  transform: scale(0.95);
  background: rgba(255, 255, 255, 0.3);
}

.status-dot {
  position: relative;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  transition: all 0.3s ease;
}

.status-dot.online {
  background: #10b981;
  box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
  animation: breatheOnline 2s ease-in-out infinite;
}

.status-dot.offline {
  background: #ef4444;
  box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7);
  animation: breatheOffline 2s ease-in-out infinite;
}

.status-pulse {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  opacity: 0;
}

.status-dot.online .status-pulse {
  background: rgba(16, 185, 129, 0.4);
  animation: pulseOnline 2s ease-in-out infinite;
}

.status-dot.offline .status-pulse {
  background: rgba(239, 68, 68, 0.4);
  animation: pulseOffline 2s ease-in-out infinite;
}

.status-text {
  font-size: 12px;
  font-weight: 600;
  color: #374151;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* 呼吸动画 */
@keyframes breatheOnline {
  0%, 100% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
  }
  50% {
    transform: scale(1.1);
    box-shadow: 0 0 0 8px rgba(16, 185, 129, 0);
  }
}

@keyframes breatheOffline {
  0%, 100% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7);
  }
  50% {
    transform: scale(1.1);
    box-shadow: 0 0 0 8px rgba(239, 68, 68, 0);
  }
}

/* 脉冲动画 */
@keyframes pulseOnline {
  0% {
    opacity: 1;
    transform: scale(0);
  }
  100% {
    opacity: 0;
    transform: scale(2.5);
  }
}

@keyframes pulseOffline {
  0% {
    opacity: 1;
    transform: scale(0);
  }
  100% {
    opacity: 0;
    transform: scale(2.5);
  }
}

/* 主内容样式 - Claude风格优化 */
.main-content {
  padding: 32px;
  min-height: calc(100vh - 60px);
  background: #fafafa;
}

.content-container {
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

/* 过渡动画 */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

/* 全局样式 */
:global(body) {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Inter', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

:global(#app) {
  min-height: 100vh;
}

/* 登录页面布局 */
.login-layout {
  min-height: 100vh;
  width: 100%;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    z-index: 1000;
    height: 100vh;
  }
  
  .main-container {
    margin-left: 0;
  }
  
  .main-content {
    padding: 16px;
  }
}
</style> 