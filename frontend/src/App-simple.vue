<template>
  <div id="app">
    <h1>🔧 网址监控工具测试</h1>
    <p>如果你看到这个页面，说明Vue应用运行正常！</p>
    
    <div style="background: #f0f9ff; padding: 20px; border-radius: 8px; margin: 20px 0;">
      <h2>📊 系统状态</h2>
      <ul>
        <li>✅ Vue.js 3 正常运行</li>
        <li>✅ 组件渲染正常</li>
        <li id="api-status">🔄 正在检查API连接...</li>
      </ul>
    </div>

    <div style="margin: 20px 0;">
      <button @click="testAPI" style="background: #3b82f6; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer;">
        测试API连接
      </button>
      <button @click="goToMain" style="background: #10b981; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; margin-left: 10px;">
        进入主应用
      </button>
    </div>

    <div v-if="error" style="background: #fef2f2; border: 1px solid #fecaca; color: #b91c1c; padding: 15px; border-radius: 4px; margin: 20px 0;">
      <strong>错误信息：</strong> {{ error }}
    </div>

    <div v-if="apiResult" style="background: #f0fdf4; border: 1px solid #bbf7d0; color: #166534; padding: 15px; border-radius: 4px; margin: 20px 0;">
      <strong>API响应：</strong> {{ apiResult }}
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'

export default {
  name: 'AppSimple',
  setup() {
    const error = ref('')
    const apiResult = ref('')

    const testAPI = async () => {
      try {
        error.value = ''
        apiResult.value = ''
        
        const response = await fetch('/api/websites/')
        const data = await response.json()
        
        if (response.ok) {
          apiResult.value = `API连接正常 - 状态码: ${data.code}`
          document.getElementById('api-status').textContent = '✅ API连接正常'
        } else {
          throw new Error(`API返回错误: ${data.message || response.statusText}`)
        }
      } catch (err) {
        error.value = err.message
        document.getElementById('api-status').textContent = '❌ API连接失败'
      }
    }

    const goToMain = () => {
      // 恢复原始App.vue
      window.location.reload()
    }

    onMounted(() => {
      // 自动测试API
      setTimeout(testAPI, 1000)
    })

    return {
      error,
      apiResult,
      testAPI,
      goToMain
    }
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  text-align: center;
  color: #2c3e50;
  margin: 50px auto;
  max-width: 800px;
  padding: 20px;
}

h1 {
  color: #3b82f6;
}
</style> 