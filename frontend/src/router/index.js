import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Websites from '../views/Websites.vue'
import Tasks from '../views/Tasks.vue'
import Results from '../views/Results.vue'
import Files from '../views/Files.vue'
import Groups from '../views/Groups.vue'
import StatusChanges from '../views/StatusChanges.vue'
import Settings from '../views/Settings.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: {
      title: '监控首页'
    }
  },
  {
    path: '/websites',
    name: 'Websites',
    component: Websites,
    meta: {
      title: '网站管理'
    }
  },
  {
    path: '/tasks',
    name: 'Tasks',
    component: Tasks,
    meta: {
      title: '任务管理'
    }
  },
  {
    path: '/results',
    name: 'Results',
    component: Results,
    meta: {
      title: '检测结果'
    }
  },
  {
    path: '/files',
    name: 'Files',
    component: Files,
    meta: {
      title: '文件管理'
    }
  },
  {
    path: '/groups',
    name: 'Groups',
    component: Groups,
    meta: {
      title: '分组管理'
    }
  },
  {
    path: '/status-changes',
    name: 'StatusChanges',
    component: StatusChanges,
    meta: {
      title: '状态变化'
    }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings,
    meta: {
      title: '系统设置'
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router 