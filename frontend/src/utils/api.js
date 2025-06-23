import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建axios实例
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    const { data } = response
    
    // 如果返回的状态码为200，说明请求成功
    if (data.code === 200) {
      return data
    } else {
      // 显示错误消息
      ElMessage.error(data.message || '请求失败')
      return Promise.reject(new Error(data.message || '请求失败'))
    }
  },
  error => {
    // 处理HTTP错误
    let message = '网络错误'
    
    if (error.response) {
      switch (error.response.status) {
        case 400:
          message = '请求参数错误'
          break
        case 401:
          message = '未授权'
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
    
    ElMessage.error(message)
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
  runFailedMonitorTask: (taskId) => api.post(`/status-changes/task/${taskId}/failed-monitor/run`)
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
  saveSystemSettings: (data) => api.post('/settings/system', data)
}

export default api 