<template>
  <div class="login-container">
    <div class="login-content">
      <!-- 左侧品牌区域 -->
      <div class="brand-section">
        <div class="brand-content">
          <div class="logo-section">
            <el-icon class="logo-icon" size="48"><Monitor /></el-icon>
            <h1 class="brand-title">网址监控系统</h1>
          </div>
          <p class="brand-description">
            专业的网站监控解决方案，实时监测网站状态，确保业务稳定运行
          </p>
          <div class="feature-list">
            <div class="feature-item">
              <el-icon class="feature-icon"><Check /></el-icon>
              <span>实时监控网站状态</span>
            </div>
            <div class="feature-item">
              <el-icon class="feature-icon"><Check /></el-icon>
              <span>智能故障检测</span>
            </div>
            <div class="feature-item">
              <el-icon class="feature-icon"><Check /></el-icon>
              <span>多种通知方式</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧登录区域 -->
      <div class="login-section">
        <div class="login-card">
          <div class="login-header">
            <h2 class="login-title">欢迎回来</h2>
            <p class="login-subtitle">请登录您的账户以继续使用</p>
          </div>
          
          <el-form
            ref="loginForm"
            :model="loginData"
            :rules="rules"
            class="login-form"
            @submit.prevent="handleLogin"
          >
            <el-form-item prop="username">
              <el-input
                v-model="loginData.username"
                placeholder="请输入用户名"
                size="large"
                :prefix-icon="User"
                :disabled="loading"
                @keyup.enter="handleLogin"
                class="login-input"
              />
            </el-form-item>
            
            <el-form-item prop="password">
              <el-input
                v-model="loginData.password"
                type="password"
                placeholder="请输入密码"
                size="large"
                :prefix-icon="Lock"
                :disabled="loading"
                show-password
                @keyup.enter="handleLogin"
                class="login-input"
              />
            </el-form-item>
            
            <el-form-item>
              <el-button
                type="primary"
                size="large"
                :loading="loading"
                @click="handleLogin"
                class="login-button"
              >
                {{ loading ? '登录中...' : '登录' }}
              </el-button>
            </el-form-item>
          </el-form>
          
          <div class="login-footer">
            <div class="default-account">
              <el-icon class="info-icon"><InfoFilled /></el-icon>
              <div class="account-info">
                <p class="account-text">默认管理员账号</p>
                <p class="account-credentials">用户名: admin / 密码: admin123</p>
                <p class="security-tip">首次登录后请及时修改默认密码</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Monitor, Check, InfoFilled } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

// 响应式数据
const loading = ref(false)
const loginForm = ref(null)

const loginData = reactive({
  username: '',
  password: ''
})

// 表单验证规则
const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 50, message: '用户名长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 50, message: '密码长度在 6 到 50 个字符', trigger: 'blur' }
  ]
}

// 处理登录
const handleLogin = async () => {
  if (!loginForm.value) return
  
  try {
    // 验证表单
    await loginForm.value.validate()
    
    loading.value = true
    
    // 调用登录API
    await userStore.login(loginData.username, loginData.password)
    
    ElMessage.success('登录成功')
    
    // 跳转到首页
    router.push('/')
    
  } catch (error) {
    console.error('登录失败:', error)
    ElMessage.error(error.message || '登录失败，请检查用户名和密码')
  } finally {
    loading.value = false
  }
}

// 页面挂载时检查是否已登录
onMounted(() => {
  if (userStore.isLoggedIn) {
    router.push('/')
  }
})
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  background-color: #ffffff;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.login-content {
  min-height: 100vh;
  display: flex;
}

/* 左侧品牌区域 */
.brand-section {
  flex: 1;
  background-color: #f9fafb;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  border-right: 1px solid #e5e7eb;
}

.brand-content {
  max-width: 480px;
  text-align: center;
}

.logo-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 32px;
}

.logo-icon {
  color: #1f2937;
  margin-bottom: 16px;
}

.brand-title {
  font-size: 32px;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
  letter-spacing: -0.025em;
}

.brand-description {
  font-size: 16px;
  color: #6b7280;
  line-height: 1.6;
  margin: 0 0 40px 0;
}

.feature-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  text-align: left;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  color: #374151;
}

.feature-icon {
  color: #10b981;
  font-size: 16px;
}

/* 右侧登录区域 */
.login-section {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  background-color: #ffffff;
}

.login-card {
  width: 100%;
  max-width: 400px;
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-title {
  font-size: 28px;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 8px 0;
  letter-spacing: -0.025em;
}

.login-subtitle {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
  line-height: 1.5;
}

.login-form {
  margin-bottom: 24px;
}

.login-form .el-form-item {
  margin-bottom: 20px;
}

.login-input {
  border-radius: 8px;
}

.login-input :deep(.el-input__wrapper) {
  border: 1px solid #d1d5db;
  border-radius: 8px;
  box-shadow: none;
  transition: all 0.2s ease;
}

.login-input :deep(.el-input__wrapper:hover) {
  border-color: #9ca3af;
}

.login-input :deep(.el-input__wrapper.is-focus) {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.login-button {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 8px;
  background-color: #1f2937;
  border-color: #1f2937;
  transition: all 0.2s ease;
}

.login-button:hover {
  background-color: #111827;
  border-color: #111827;
}

.login-button:focus {
  background-color: #111827;
  border-color: #111827;
  box-shadow: 0 0 0 3px rgba(31, 41, 55, 0.2);
}

.login-footer {
  margin-top: 24px;
}

.default-account {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background-color: #fef3c7;
  border: 1px solid #fbbf24;
  border-radius: 8px;
}

.info-icon {
  color: #f59e0b;
  font-size: 18px;
  margin-top: 2px;
}

.account-info {
  flex: 1;
  text-align: left;
}

.account-text {
  font-size: 14px;
  font-weight: 600;
  color: #92400e;
  margin: 0 0 4px 0;
}

.account-credentials {
  font-size: 13px;
  color: #92400e;
  margin: 0 0 4px 0;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.security-tip {
  font-size: 12px;
  color: #78350f;
  margin: 0;
  line-height: 1.4;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .login-content {
    flex-direction: column;
  }
  
  .brand-section {
    flex: none;
    min-height: 300px;
    border-right: none;
    border-bottom: 1px solid #e5e7eb;
  }
  
  .brand-content {
    max-width: 100%;
  }
  
  .feature-list {
    flex-direction: row;
    justify-content: center;
    flex-wrap: wrap;
    gap: 24px;
  }
}

@media (max-width: 768px) {
  .brand-section,
  .login-section {
    padding: 24px;
  }
  
  .brand-title {
    font-size: 28px;
  }
  
  .login-title {
    font-size: 24px;
  }
  
  .feature-list {
    flex-direction: column;
    gap: 12px;
  }
}

@media (max-width: 480px) {
  .brand-section,
  .login-section {
    padding: 20px;
  }
  
  .brand-title {
    font-size: 24px;
  }
  
  .login-title {
    font-size: 22px;
  }
  
  .default-account {
    flex-direction: column;
    gap: 8px;
    text-align: center;
  }
  
  .account-info {
    text-align: center;
  }
}
</style>
