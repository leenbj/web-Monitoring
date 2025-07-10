import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/utils/api'

export const useUserStore = defineStore('user', () => {
  // 状态
  const user = ref(null)
  const token = ref(localStorage.getItem('auth_token') || '')
  const refreshToken = ref(localStorage.getItem('refresh_token') || '')

  // 计算属性
  const isLoggedIn = computed(() => !!token.value && !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const userRole = computed(() => user.value?.role || 'guest')

  // 方法
  
  /**
   * 用户登录
   */
  const login = async (username, password) => {
    try {
      const response = await api.post('/auth/login', {
        username,
        password
      })

      if (response.code === 200 || response.success === true) {
        // 支持两种响应格式
        const responseData = response.data || response
        const { access_token, refresh_token, user: userInfo, token: simpleToken } = responseData
        
        // 兼容简单token格式
        const finalToken = access_token || simpleToken || 'simple-token-' + Date.now()
        
        // 保存token
        token.value = finalToken
        refreshToken.value = refresh_token || ''
        localStorage.setItem('auth_token', finalToken)
        if (refresh_token) {
          localStorage.setItem('refresh_token', refresh_token)
        }
        
        // 保存用户信息（如果有的话）
        const finalUserInfo = userInfo || { 
          id: 1, 
          username: 'admin', 
          role: 'admin', 
          nickname: '管理员' 
        }
        user.value = finalUserInfo
        localStorage.setItem('user_info', JSON.stringify(finalUserInfo))
        
        // 设置API默认的Authorization头
        api.defaults.headers.common['Authorization'] = `Bearer ${finalToken}`
        
        return finalUserInfo
      } else {
        throw new Error(response.message || '登录失败')
      }
    } catch (error) {
      console.error('登录错误:', error)
      throw new Error(error.response?.data?.message || error.message || '登录失败')
    }
  }

  /**
   * 刷新token
   */
  const refreshAccessToken = async () => {
    try {
      if (!refreshToken.value) {
        throw new Error('没有refresh token')
      }

      const response = await api.post('/auth/refresh', {}, {
        headers: {
          'Authorization': `Bearer ${refreshToken.value}`
        }
      })

      if (response.code === 200) {
        const { access_token } = response.data
        
        token.value = access_token
        localStorage.setItem('auth_token', access_token)
        
        // 更新API默认的Authorization头
        api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
        
        return access_token
      } else {
        throw new Error(response.message || 'Token刷新失败')
      }
    } catch (error) {
      console.error('Token刷新错误:', error)
      // Token刷新失败，清除所有认证信息
      logout()
      throw error
    }
  }

  /**
   * 获取当前用户信息
   */
  const getCurrentUser = async () => {
    try {
      const response = await api.get('/auth/me')
      
      if (response.code === 200) {
        user.value = response.data
        localStorage.setItem('user_info', JSON.stringify(response.data))
        return response.data
      } else {
        throw new Error(response.message || '获取用户信息失败')
      }
    } catch (error) {
      console.error('获取用户信息错误:', error)
      throw error
    }
  }

  /**
   * 用户登出
   */
  const logout = async () => {
    try {
      // 调用后端登出API
      if (token.value) {
        await api.post('/auth/logout')
      }
    } catch (error) {
      console.error('登出API调用失败:', error)
      // 即使API调用失败，也继续清除本地数据
    } finally {
      // 清除本地存储
      clearAuthData()
    }
  }

  /**
   * 清除认证数据
   */
  const clearAuthData = () => {
    user.value = null
    token.value = ''
    refreshToken.value = ''
    localStorage.removeItem('auth_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user_info')
    
    // 清除API默认的Authorization头
    delete api.defaults.headers.common['Authorization']
  }

  /**
   * 初始化用户状态（从localStorage恢复）
   */
  const initializeAuth = async () => {
    try {
      const storedToken = localStorage.getItem('auth_token')
      const storedRefreshToken = localStorage.getItem('refresh_token')
      const storedUser = localStorage.getItem('user_info')
      
      if (storedToken && storedUser) {
        token.value = storedToken
        refreshToken.value = storedRefreshToken || ''
        user.value = JSON.parse(storedUser)
        
        // 设置API默认的Authorization头
        api.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`
        
        // 验证token是否仍然有效
        try {
          await getCurrentUser()
          console.log('用户状态恢复成功:', user.value)
        } catch (error) {
          console.log('Token验证失败，尝试刷新...')
          // token无效，尝试刷新
          if (refreshToken.value) {
            try {
              await refreshAccessToken()
              await getCurrentUser()
              console.log('Token刷新成功，用户状态恢复完成')
            } catch (refreshError) {
              console.error('Token刷新失败:', refreshError)
              // 刷新失败，清除所有数据
              clearAuthData()
            }
          } else {
            console.log('没有refresh token，清除认证数据')
            clearAuthData()
          }
        }
      } else {
        console.log('没有找到存储的认证信息')
      }
    } catch (error) {
      console.error('初始化认证状态失败:', error)
      clearAuthData()
    }
  }

  /**
   * 更新用户信息
   */
  const updateUser = (userInfo) => {
    user.value = { ...user.value, ...userInfo }
    localStorage.setItem('user_info', JSON.stringify(user.value))
  }

  /**
   * 检查是否有特定权限
   */
  const hasPermission = (permission) => {
    if (!user.value) return false
    
    // 管理员拥有所有权限
    if (user.value.role === 'admin') return true
    
    // 这里可以根据需要扩展权限检查逻辑
    switch (permission) {
      case 'user_management':
        return user.value.role === 'admin'
      case 'system_settings':
        return user.value.role === 'admin'
      default:
        return true // 普通功能默认允许
    }
  }

  return {
    // 状态
    user,
    token,
    refreshToken,
    
    // 计算属性
    isLoggedIn,
    isAdmin,
    userRole,
    
    // 方法
    login,
    logout,
    refreshAccessToken,
    getCurrentUser,
    initializeAuth,
    updateUser,
    hasPermission,
    clearAuthData
  }
}, {
  persist: {
    key: 'website-monitor-user',
    storage: localStorage,
    paths: ['user', 'token', 'refreshToken']
  }
}) 
