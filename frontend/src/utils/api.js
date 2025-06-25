import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建axios实例
const api = axios.create({
  baseURL: '/api',
  timeout: 65000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    // 从localStorage获取token并添加到请求头
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 用于避免重复刷新token的标志
let isRefreshing = false
let failedQueue = []

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  
  failedQueue = []
}

// 响应拦截器
api.interceptors.response.use(
  response => {
    const { data } = response

    // 如果返回的状态码为200，说明请求成功
    if (data.code === 200) {
      return { success: true, ...data }
    } else {
      // 不自动显示错误消息，让调用方处理
      return { success: false, ...data }
    }
  },
  async error => {
    const originalRequest = error.config
    
    // 处理HTTP错误
    let message = '网络错误'
    
    if (error.response) {
      const { data } = error.response
      
      // 如果是400或500错误且有JSON响应，返回响应数据让调用方处理
      if ((error.response.status === 400 || error.response.status === 500) && data && data.code) {
        return Promise.resolve({ success: false, ...data })
      }
      
      // 处理401 token过期
      if (error.response.status === 401 && !originalRequest._retry) {
        if (isRefreshing) {
          // 如果正在刷新token，将请求加入队列
          return new Promise((resolve, reject) => {
            failedQueue.push({ resolve, reject })
          }).then(token => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            return api(originalRequest)
          }).catch(err => {
            return Promise.reject(err)
          })
        }

        originalRequest._retry = true
        isRefreshing = true

        const refreshToken = localStorage.getItem('refresh_token')
        
        if (refreshToken) {
          try {
            const response = await axios.post('/api/auth/refresh', {}, {
              headers: {
                'Authorization': `Bearer ${refreshToken}`
              }
            })

            if (response.data.code === 200) {
              const { access_token } = response.data.data
              localStorage.setItem('auth_token', access_token)
              api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
              
              processQueue(null, access_token)
              
              // 重试原始请求
              originalRequest.headers.Authorization = `Bearer ${access_token}`
              return api(originalRequest)
            } else {
              throw new Error('Token刷新失败')
            }
          } catch (refreshError) {
            processQueue(refreshError, null)
            
            // 刷新失败，清除认证信息并跳转到登录页
            localStorage.removeItem('auth_token')
            localStorage.removeItem('refresh_token')
            localStorage.removeItem('user_info')
            delete api.defaults.headers.common['Authorization']
            
            // 跳转到登录页
            if (window.location.pathname !== '/login') {
              window.location.href = '/login'
            }
            
            return Promise.reject(refreshError)
          } finally {
            isRefreshing = false
          }
        } else {
          // 没有refresh token，直接跳转到登录页
          localStorage.removeItem('auth_token')
          localStorage.removeItem('refresh_token')
          localStorage.removeItem('user_info')
          delete api.defaults.headers.common['Authorization']
          
          if (window.location.pathname !== '/login') {
            window.location.href = '/login'
          }
        }
      }
      
      switch (error.response.status) {
        case 400:
          message = '请求参数错误'
          break
        case 401:
          message = '登录已过期，请重新登录'
          break
        case 403:
          message = '拒绝访问'
          break
        case 404:
          message = '请求资源不存在'
          break
        case 500:
          message = '服务器内部错误'
          break
        default:
          message = `连接错误${error.response.status}`
      }
    } else if (error.request) {
      message = '网络连接失败'
    }
    
    // 对于401错误，不显示错误消息（因为会自动跳转登录）
    if (error.response?.status !== 401) {
      ElMessage.error(message)
    }
    return Promise.reject(error)
  }
)

// API接口定义
export const websiteApi = {
  // 获取网站列表
  getList: (params) => api.get('/websites/', { params }),
  
  // 创建网站
  create: (data) => api.post('/websites/', data),
  
  // 批量创建网站
  batchCreate: (data) => api.post('/websites/batch', data),
  
  // 获取网站详情
  getDetail: (id) => api.get(`/websites/${id}`),
  
  // 更新网站
  update: (id, data) => api.put(`/websites/${id}`, data),
  
  // 删除网站
  delete: (id) => api.delete(`/websites/${id}`),
  
  // 批量删除网站
  batchDelete: (data) => api.post('/websites/batch/delete', data),
  
  // 切换网站状态
  toggleStatus: (id) => api.post(`/websites/toggle-status/${id}`),
  
  // 导入网站
  import: (formData) => api.post('/websites/import', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

export const taskApi = {
  // 获取任务列表
  getList: (params) => api.get('/tasks/', { params }),
  
  // 创建任务
  create: (data) => api.post('/tasks/', data),
  
  // 获取任务详情
  getDetail: (id) => api.get(`/tasks/${id}`),
  
  // 更新任务
  update: (id, data) => api.put(`/tasks/${id}/update`, data),
  
  // 启动任务
  start: (id) => api.post(`/tasks/${id}/start`),
  
  // 停止任务
  stop: (id) => api.post(`/tasks/${id}/stop`),
  
  // 删除任务
  delete: (id) => api.delete(`/tasks/${id}/delete`),
  
  // 定时调度任务
  schedule: (id) => api.post(`/tasks/${id}/schedule`),
  
  // 获取任务结果
  getResults: (id, params) => api.get(`/tasks/${id}/results`, { params })
}

export const resultApi = {
  // 获取检测结果
  getList: (params) => api.get('/results/', { params }),
  
  // 获取统计信息
  getStats: (params) => api.get('/results/statistics', { params }),
  
  // 导出结果
  export: (data) => api.post('/results/export', data),
  
  // 清除数据（默认清除所有数据）
  clearAllData: () => api.delete('/results/clear-old-data'),
  
  // 清除过期数据（保留指定天数的数据）
  clearOldData: (retainDays) => api.delete('/results/clear-old-data', { 
    params: { retain_days: retainDays } 
  })
}

export const fileApi = {
  // 获取文件列表
  getList: () => api.get('/files/'),
  
  // 下载文件
  download: (filename) => api.get(`/files/download/${filename}`, {
    responseType: 'blob'
  }),
  
  // 删除文件
  delete: (filename) => api.delete(`/files/${filename}`)
}

export const groupApi = {
  // 获取分组列表
  getList: (params) => api.get('/groups/', { params }),
  
  // 创建分组
  create: (data) => api.post('/groups/', data),
  
  // 获取分组详情
  getDetail: (id) => api.get(`/groups/${id}`),
  
  // 更新分组
  update: (id, data) => api.put(`/groups/${id}`, data),
  
  // 删除分组
  delete: (id) => api.delete(`/groups/${id}`),
  
  // 分配网站到分组
  assignWebsites: (id, data) => api.post(`/groups/${id}/websites`, data)
}

export const statusChangeApi = {
  // 获取任务的最近状态变化
  getRecentChanges: (taskId, params) => api.get(`/status-changes/task/${taskId}/recent`, { params }),
  
  // 获取任务的可访问性摘要
  getAccessibilitySummary: (taskId, params) => api.get(`/status-changes/task/${taskId}/summary`, { params }),
  
  // 获取失败网站监控任务状态
  getFailedMonitorStatus: (taskId) => api.get(`/status-changes/task/${taskId}/failed-monitor`),
  
  // 创建或更新失败网站监控任务
  createOrUpdateFailedMonitor: (taskId) => api.post(`/status-changes/task/${taskId}/failed-monitor`),
  
  // 获取最近恢复的网站列表
  getRecoveredWebsites: (taskId, params) => api.get(`/status-changes/task/${taskId}/recovered`, { params }),
  
  // 手动运行失败网站监控任务
  runFailedMonitorTask: (taskId) => api.post(`/status-changes/task/${taskId}/failed-monitor/run`),
  
  // 启动或停止失败网站监控任务
  toggleFailedMonitorTask: (taskId) => api.post(`/status-changes/task/${taskId}/failed-monitor/toggle`),
  
  // 更新失败网站监控任务设置
  updateFailedMonitorTask: (taskId, data) => api.put(`/status-changes/task/${taskId}/failed-monitor/update`, data),
  
  // 删除失败网站监控任务
  deleteFailedMonitorTask: (taskId) => api.delete(`/status-changes/task/${taskId}/failed-monitor/delete`)
}

export const settingsApi = {
  // 获取邮件设置
  getEmailSettings: () => api.get('/settings/email'),

  // 保存邮件设置
  saveEmailSettings: (data) => api.post('/settings/email', data),

  // 测试邮箱连接
  testEmailConnection: (data) => api.post('/settings/email/test-connection', data),

  // 发送测试邮件
  sendTestEmail: () => api.post('/settings/email/test-send'),

  // 获取系统设置
  getSystemSettings: () => api.get('/settings/system'),

  // 保存系统设置
  saveSystemSettings: (data) => api.post('/settings/system', data),

  // Dify API密钥管理
  getDifyApiKeys: () => api.get('/settings/dify-api-keys'),
  createDifyApiKey: (data) => api.post('/settings/dify-api-keys', data),
  deleteDifyApiKey: (keyId) => api.delete(`/settings/dify-api-keys/${keyId}`)
}

export const userApi = {
  // 获取用户列表（仅管理员）
  getList: (params) => api.get('/auth/users', { params }),

  // 创建用户（仅管理员）
  create: (data) => api.post('/auth/users', data),

  // 获取当前用户信息
  getCurrentUser: () => api.get('/auth/me'),

  // 更新用户信息
  update: (id, data) => api.put(`/auth/users/${id}`, data),

  // 删除用户（仅管理员）
  delete: (id) => api.delete(`/auth/users/${id}`),

  // 修改密码
  changePassword: (id, data) => api.put(`/auth/users/${id}`, data),

  // 重置密码（仅管理员）
  resetPassword: (id, data) => api.put(`/auth/users/${id}`, data)
}

export default api