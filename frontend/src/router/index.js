import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Login from '../views/Login.vue'
import Websites from '../views/Websites.vue'
import Tasks from '../views/Tasks.vue'
import Results from '../views/Results.vue'
import Files from '../views/Files.vue'
import Groups from '../views/Groups.vue'
import StatusChanges from '../views/StatusChanges.vue'
import Settings from '../views/Settings.vue'
import UserManagement from '../views/UserManagement.vue'
import Profile from '../views/Profile.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: {
      title: '用户登录',
      public: true // 公开页面，不需要认证
    }
  },
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: {
      title: '监控首页',
      requiresAuth: true
    }
  },
  {
    path: '/websites',
    name: 'Websites',
    component: Websites,
    meta: {
      title: '网站管理',
      requiresAuth: true
    }
  },
  {
    path: '/tasks',
    name: 'Tasks',
    component: Tasks,
    meta: {
      title: '任务管理',
      requiresAuth: true
    }
  },
  {
    path: '/results',
    name: 'Results',
    component: Results,
    meta: {
      title: '检测结果',
      requiresAuth: true
    }
  },
  {
    path: '/files',
    name: 'Files',
    component: Files,
    meta: {
      title: '文件管理',
      requiresAuth: true
    }
  },
  {
    path: '/groups',
    name: 'Groups',
    component: Groups,
    meta: {
      title: '分组管理',
      requiresAuth: true
    }
  },
  {
    path: '/status-changes',
    name: 'StatusChanges',
    component: StatusChanges,
    meta: {
      title: '状态变化',
      requiresAuth: true
    }
  },
  {
    path: '/users',
    name: 'UserManagement',
    component: UserManagement,
    meta: {
      title: '用户管理',
      requiresAuth: true,
      requiresAdmin: true
    }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: Profile,
    meta: {
      title: '个人信息',
      requiresAuth: true
    }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings,
    meta: {
      title: '系统设置',
      requiresAuth: true,
      requiresAdmin: true
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  // 动态导入用户store（确保Pinia已初始化）
  const { useUserStore } = await import('@/stores/user')
  const userStore = useUserStore()

  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - 网址监控系统` : '网址监控系统'

  // 如果是公开页面，直接放行
  if (to.meta.public) {
    // 如果已登录用户访问登录页面，重定向到首页
    if (to.name === 'Login' && userStore.isLoggedIn) {
      next('/')
      return
    }
    next()
    return
  }

  // 需要认证的页面
  if (to.meta.requiresAuth) {
    // 检查是否已登录
    if (!userStore.isLoggedIn) {
      next({
        name: 'Login',
        query: { redirect: to.fullPath } // 记录原本要访问的页面
      })
      return
    }

    // 检查是否需要管理员权限
    if (to.meta.requiresAdmin && !userStore.isAdmin) {
      // 可以跳转到403页面或者首页
      next('/')
      return
    }
  }

  next()
})

export default router