import { createApp } from 'vue'
import { createPinia } from 'pinia'

// 使用全量导入Element Plus，避免循环依赖
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router/index.js'
import { useUserStore } from './stores/user.js'
import { performanceMonitor } from './utils/performance.js'
import './styles/claude-theme.css'
import './styles/element-plus-override.css'

// 创建应用
const app = createApp(App)

// 创建 Pinia 实例
const pinia = createPinia()

// 注册所有Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 使用插件
app.use(pinia)
app.use(ElementPlus) // 使用全量导入的Element Plus
app.use(router)

// 初始化用户状态
const initializeApp = async () => {
  try {
    const userStore = useUserStore()
    await userStore.initializeAuth()
  } catch (error) {
    console.error('应用初始化失败:', error)
  }
}

// 挂载应用并初始化用户状态
initializeApp().then(() => {
  app.mount('#app')
}).catch(error => {
  console.error('应用挂载失败:', error)
  // 尝试直接挂载，不进行用户状态初始化
  app.mount('#app')
}) 