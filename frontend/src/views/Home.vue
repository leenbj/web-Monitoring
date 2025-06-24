<template>
  <div class="home-page fade-in-container">
    <!-- 快速操作面板 -->
    <div class="quick-actions-panel">
      <div class="action-card main-control">
        <div class="control-header">
          <div class="status-indicator">
            <div class="status-dot" :class="{ active: monitorStatus }"></div>
            <span class="status-text">{{ monitorStatus ? '监控运行中' : '监控已停止' }}</span>
          </div>
          <el-switch
            v-model="monitorStatus"
            size="large"
            active-text="开启"
            inactive-text="关闭" 
            @change="toggleMonitor"
            class="main-switch"
          />
        </div>
      </div>
      
      <div class="action-card">
        <el-button 
          type="primary" 
          size="large"
          @click="startQuickDetection"
          :loading="quickDetecting"
          :disabled="!hasWebsites"
          class="action-btn"
        >
          <el-icon><Search /></el-icon>
          立即检测
        </el-button>
      </div>
      
      <div class="action-card">
        <el-button 
          size="large"
          @click="refreshStatus"
          :loading="refreshing"
          class="action-btn secondary"
        >
          <el-icon><Refresh /></el-icon>
          刷新状态
        </el-button>
      </div>
    </div>

    <!-- 监控控制面板 -->
    <el-card class="monitor-control-card" shadow="never">
      <template #header>
        <div class="card-header">
          <h2>
            <el-icon class="monitor-icon"><Monitor /></el-icon>
            监控概览
          </h2>
          <div class="control-info">
            <el-tag type="info" size="small">
              监控网站 {{ statistics.total_websites }} 个
            </el-tag>
          </div>
        </div>
      </template>

      <!-- 简化的控制面板内容 -->
      <div class="monitor-summary">
        <div class="summary-item">
          <span class="label">总检测数</span>
          <span class="value">{{ statistics.total_checks }}</span>
        </div>
        <div class="summary-item">
          <span class="label">成功率</span>
          <span class="value success">{{ ((statistics.standard_count + statistics.redirect_count) / statistics.total_checks * 100 || 0).toFixed(1) }}%</span>
        </div>
      </div>
    </el-card>

    <!-- 实时统计面板 -->
    <div class="stats-grid">
      <div class="stat-card success-card">
        <div class="stat-content">
          <div class="stat-icon">
            <el-icon><Check /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-number">{{ statistics.standard_count }}</div>
            <div class="stat-label">正常访问</div>
            <div class="stat-percent">{{ ((statistics.standard_count / statistics.total_checks) * 100 || 0).toFixed(1) }}%</div>
          </div>
        </div>
      </div>
      
      <div class="stat-card warning-card">
        <div class="stat-content">
          <div class="stat-icon">
            <el-icon><Warning /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-number">{{ statistics.redirect_count }}</div>
            <div class="stat-label">跳转访问</div>
            <div class="stat-percent">{{ ((statistics.redirect_count / statistics.total_checks) * 100 || 0).toFixed(1) }}%</div>
          </div>
        </div>
      </div>
      
      <div class="stat-card danger-card">
        <div class="stat-content">
          <div class="stat-icon">
            <el-icon><Close /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-number">{{ statistics.failed_count }}</div>
            <div class="stat-label">无法访问</div>
            <div class="stat-percent">{{ ((statistics.failed_count / statistics.total_checks) * 100 || 0).toFixed(1) }}%</div>
          </div>
        </div>
      </div>
      
      <div class="stat-card info-card">
        <div class="stat-content">
          <div class="stat-icon">
            <el-icon><DataAnalysis /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-number">{{ statistics.total_websites }}</div>
            <div class="stat-label">监控网站</div>
            <div class="stat-percent">{{ statistics.total_checks }} 次检测</div>
          </div>
        </div>
      </div>
    </div>



    <!-- 最新检测结果 -->
    <el-card class="recent-results-card" shadow="never">
      <template #header>
        <div class="card-header">
          <h3>最新检测结果</h3>
          <el-button type="primary" size="small" @click="$router.push('/results')">
            查看全部
          </el-button>
        </div>
      </template>

      <div class="results-container">
        <el-table :data="recentResults" class="results-table">
          <el-table-column prop="website_name" label="网站名称" min-width="120" show-overflow-tooltip />
          <el-table-column prop="website_domain" label="域名" min-width="140" show-overflow-tooltip>
            <template #default="{ row }">
              <el-link :href="'http://' + row.website_domain" target="_blank" type="primary" size="small">
                {{ row.website_domain }}
              </el-link>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag 
                :type="getStatusType(row.status)" 
                size="small"
                effect="plain"
              >
                <el-icon class="status-icon">
                  <Check v-if="row.status === 'standard'" />
                  <Warning v-else-if="row.status === 'redirect'" />
                  <Close v-else />
                </el-icon>
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="response_time" label="响应时间" width="100" align="center">
            <template #default="{ row }">
              <span v-if="row.response_time" class="response-time">{{ parseFloat(row.response_time).toFixed(2) }}ms</span>
              <span v-else class="no-data">-</span>
            </template>
          </el-table-column>
          <el-table-column prop="detected_at" label="检测时间" min-width="140">
            <template #default="{ row }">
              <div class="check-time">
                <div class="time-main">{{ formatDate(row.detected_at) }}</div>
                <small class="time-ago">{{ getTimeAgo(row.detected_at) }}</small>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>
  </div>
</template>

<script>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElNotification } from 'element-plus'
import { 
  Monitor, 
  Search, 
  Refresh, 
  Check, 
  Close, 
  Warning, 
  DataAnalysis,
  CircleCheck,
  CircleClose
} from '@element-plus/icons-vue'
import { taskApi, resultApi, websiteApi } from '../utils/api'

export default {
  name: 'Home',
  components: {
    Monitor,
    Search, 
    Refresh,
    Check,
    Close,
    Warning,
    DataAnalysis,
    CircleCheck,
    CircleClose
  },
  setup() {
    const monitorStatus = ref(false)
    const quickDetecting = ref(false)
    const refreshing = ref(false)
    const hasWebsites = ref(false)
    const onlineWebsiteCount = ref(0)
    const recentResults = ref([])

    
    const statistics = reactive({
      total_checks: 0,
      total_websites: 0,
      standard_count: 0,
      redirect_count: 0,
      failed_count: 0,
      success_rate: 0
    })

    let statusCheckInterval = null

    // 切换监控状态
    const toggleMonitor = async (status) => {
      try {
        if (status) {
          // 启动监控 - 创建或启动任务
          await startMonitoring()
          ElNotification({
            title: '监控已启动',
            message: '网址监控系统已开始运行',
            type: 'success',
            position: 'top-right'
          })
        } else {
          // 停止监控
          await stopMonitoring()
          ElNotification({
            title: '监控已停止',
            message: '网址监控系统已停止运行',
            type: 'warning',
            position: 'top-right'
          })
        }
        await refreshStatus()
      } catch (error) {
        ElMessage.error('操作失败: ' + error.message)
        // 回滚状态
        monitorStatus.value = !status
      }
    }

    // 启动监控
    const startMonitoring = async () => {
      try {
        // 获取或创建默认任务
        const tasks = await taskApi.getList()
        let defaultTask = tasks.data.tasks.find(task => task.name === '默认监控任务')
        
        if (!defaultTask) {
          // 创建默认任务
          const websites = await websiteApi.getList({ per_page: 1000 })
          const websiteIds = websites.data.websites.map(w => w.id)
          
          if (websiteIds.length === 0) {
            throw new Error('请先添加要监控的网站')
          }
          
          const newTask = await taskApi.create({
            name: '默认监控任务',
            interval_minutes: 30,
            website_ids: websiteIds
          })
          defaultTask = newTask.data
        }
        
        // 确保任务存在
        if (!defaultTask || !defaultTask.id) {
          throw new Error('无法获取或创建默认监控任务')
        }
        
        // 启动定时调度（而不是单次执行）
        try {
          await taskApi.schedule(defaultTask.id)
        } catch (startError) {
          // 如果启动失败，可能是任务状态问题，尝试重新获取任务信息
          if (startError.response && startError.response.status === 400) {
            console.warn('任务调度启动失败，可能是状态问题，尝试重新启动')
            // 等待一秒后重试
            await new Promise(resolve => setTimeout(resolve, 1000))
            await taskApi.schedule(defaultTask.id)
          } else {
            throw startError
          }
        }
      } catch (error) {
        console.error('启动监控失败:', error)
        throw error
      }
    }

    // 停止监控
    const stopMonitoring = async () => {
      try {
        const tasks = await taskApi.getList()
        const activeTasks = tasks.data.tasks.filter(task => task.is_active)
        
        for (const task of activeTasks) {
          await taskApi.stop(task.id)
        }
      } catch (error) {
        throw error
      }
    }

    // 立即检测
    const startQuickDetection = async () => {
      quickDetecting.value = true
      try {
        // 获取现有的活跃任务
        const tasksResponse = await taskApi.getList()
        const activeTasks = tasksResponse.data.tasks.filter(task => task.is_active)
        
        if (activeTasks.length === 0) {
          ElMessage.warning('没有活跃的检测任务，请先在任务管理中创建或启动任务')
          return
        }
        
        // 选择第一个活跃任务进行立即执行
        const selectedTask = activeTasks[0]
        
        // 立即执行选中的任务
        await taskApi.start(selectedTask.id)
        
        ElMessage.success(`正在执行任务：${selectedTask.name}，请稍后查看结果`)
        
        // 3秒后刷新数据
        setTimeout(() => {
          refreshStatus()
        }, 3000)
        
      } catch (error) {
        console.error('启动检测失败:', error)
        ElMessage.error('启动检测失败: ' + (error.response?.data?.message || error.message))
      } finally {
        quickDetecting.value = false
      }
    }

    // 刷新状态
    const refreshStatus = async () => {
      refreshing.value = true
      try {
        await Promise.all([
          loadStatistics(),
          loadRecentResults(),
          checkMonitorStatus(),
          checkWebsiteCount()
        ])
      } catch (error) {
        console.error('刷新状态失败:', error)
      } finally {
        refreshing.value = false
      }
    }

    // 加载统计数据
    const loadStatistics = async () => {
      try {
        const response = await resultApi.getStats()
        Object.assign(statistics, response.data.overview)
        onlineWebsiteCount.value = statistics.standard_count + statistics.redirect_count
      } catch (error) {
        console.error('加载统计数据失败:', error)
      }
    }

    // 加载最新结果
    const loadRecentResults = async () => {
      try {
        const response = await resultApi.getList({ 
          page: 1, 
          per_page: 10,
          order_by: 'check_time',
          order: 'desc'
        })
        recentResults.value = response.data.results
      } catch (error) {
        console.error('加载最新结果失败:', error)
      }
    }



    // 检查监控状态
    const checkMonitorStatus = async () => {
      try {
        const response = await taskApi.getList()
        const activeTasks = response.data.tasks.filter(task => task.is_active)
        monitorStatus.value = activeTasks.length > 0
      } catch (error) {
        console.error('检查监控状态失败:', error)
      }
    }

    // 检查网站数量
    const checkWebsiteCount = async () => {
      try {
        const response = await websiteApi.getList({ per_page: 1 })
        const total = response.data.pagination?.total || response.data.total || 0
        hasWebsites.value = total > 0
      } catch (error) {
        console.error('检查网站数量失败:', error)
        hasWebsites.value = false
      }
    }

    // 状态文本转换
    const getStatusText = (status) => {
      const statusMap = {
        'standard': '正常访问',
        'redirect': '跳转访问', 
        'failed': '无法访问'
      }
      return statusMap[status] || '未知'
    }

    // 状态类型转换
    const getStatusType = (status) => {
      const typeMap = {
        'standard': 'success',
        'redirect': 'warning',
        'failed': 'danger'
      }
      return typeMap[status] || 'info'
    }

    // 格式化时间
    const formatDate = (dateString) => {
      if (!dateString) return '-'
      return new Date(dateString).toLocaleString('zh-CN')
    }

    // 获取相对时间
    const getTimeAgo = (dateString) => {
      if (!dateString) return ''
      const now = new Date()
      const date = new Date(dateString)
      const diff = now - date
      
      const minutes = Math.floor(diff / 60000)
      const hours = Math.floor(diff / 3600000)
      const days = Math.floor(diff / 86400000)
      
      if (days > 0) return `${days}天前`
      if (hours > 0) return `${hours}小时前`
      if (minutes > 0) return `${minutes}分钟前`
      return '刚刚'
    }



    // 启动定时刷新
    const startStatusCheck = () => {
      statusCheckInterval = setInterval(() => {
        refreshStatus()
      }, 120000) // 2分钟刷新一次（从30秒改为120秒，减少频繁刷新）
    }

    // 停止定时刷新
    const stopStatusCheck = () => {
      if (statusCheckInterval) {
        clearInterval(statusCheckInterval)
        statusCheckInterval = null
      }
    }

    onMounted(() => {
      refreshStatus()
      startStatusCheck()
    })

    onUnmounted(() => {
      stopStatusCheck()
    })

    return {
      monitorStatus,
      quickDetecting,
      refreshing,
      hasWebsites,
      onlineWebsiteCount,
      statistics,
      recentResults,
      toggleMonitor,
      startQuickDetection,
      refreshStatus,
      getStatusText,
      getStatusType,
      formatDate,
      getTimeAgo
    }
  }
}
</script>

<style scoped>
/* Claude风格首页容器 */
.home-page {
  padding: 0;
  min-height: calc(100vh - 120px);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

/* 快速操作面板 - Claude风格 */
.quick-actions-panel {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  gap: 16px;
  margin-bottom: 24px;
}

.action-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #e5e7eb;
  transition: all 0.15s ease;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
}

.action-card:hover {
  border-color: #d1d5db;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.main-control {
  grid-column: 1;
}

.control-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #e5e7eb;
  transition: all 0.3s ease;
}

.status-dot.active {
  background: #10b981;
  box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);
}

.status-text {
  font-weight: 500;
  color: #111827;
  font-size: 16px;
}

.main-switch {
  transform: scale(1.1);
}

.action-btn {
  width: 100%;
  height: 48px;
  font-weight: 600;
  border-radius: 8px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  transform-origin: center;
}

.action-btn::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  transition: width 0.6s ease, height 0.6s ease;
}

.action-btn:active::before {
  width: 300px;
  height: 300px;
}

.action-btn:hover {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 8px 25px rgba(59, 130, 246, 0.3);
}

.action-btn:active {
  transform: translateY(0) scale(0.98);
  animation: buttonPulse 0.3s ease;
}

/* 检测按钮特殊效果 */
.action-btn:not(.secondary) {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  border: none;
  position: relative;
}

.action-btn:not(.secondary)::after {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.7s ease;
}

.action-btn:not(.secondary):hover::after {
  left: 100%;
}

/* 按钮动画 */
@keyframes buttonPulse {
  0% {
    box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.7);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(59, 130, 246, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(59, 130, 246, 0);
  }
}

.action-btn.secondary {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  color: #374151;
}

.action-btn.secondary:hover {
  background: #f3f4f6;
  border-color: #d1d5db;
}

/* 监控控制卡片 - Claude风格 */
.monitor-control-card {
  margin-bottom: 24px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #ffffff;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  color: #111827;
  font-size: 18px;
  font-weight: 600;
  letter-spacing: -0.025em;
}

.monitor-icon {
  font-size: 18px;
  color: #1a1a1a;
}

.control-info {
  display: flex;
  gap: 8px;
}

.monitor-summary {
  display: flex;
  gap: 32px;
  padding: 20px 0;
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.summary-item .label {
  font-size: 14px;
  color: #6b7280;
  font-weight: 500;
}

.summary-item .value {
  font-size: 24px;
  font-weight: 600;
  color: #111827;
  letter-spacing: -0.025em;
}

.summary-item .value.success {
  color: #10b981;
}

/* 统计网格 - Claude风格 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid #e5e7eb;
  transition: all 0.15s ease;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
}

.stat-card:hover {
  border-color: #d1d5db;
  box-shadow: 0 8px 16px -1px rgba(0, 0, 0, 0.15), 0 4px 8px -1px rgba(0, 0, 0, 0.1);
  transform: translateY(-4px) scale(1.02);
}

.stat-card:hover .stat-icon {
  animation: statIconFloat 1s ease-in-out infinite alternate;
}

/* 统计图标浮动动画 */
@keyframes statIconFloat {
  0% {
    transform: translateY(0) rotate(0deg);
  }
  100% {
    transform: translateY(-2px) rotate(2deg);
  }
}

.success-card {
  border-left: 4px solid #10b981;
}

.warning-card {
  border-left: 4px solid #f59e0b;
}

.danger-card {
  border-left: 4px solid #ef4444;
}

.info-card {
  border-left: 4px solid #3b82f6;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: white;
}

.success-card .stat-icon {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.warning-card .stat-icon {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
}

.danger-card .stat-icon {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
}

.info-card .stat-icon {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
}

.stat-info {
  flex: 1;
}

.stat-number {
  font-size: 28px;
  font-weight: 700;
  color: #111827;
  line-height: 1;
  margin-bottom: 6px;
  letter-spacing: -0.025em;
}

.stat-label {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 4px;
  font-weight: 500;
}

.stat-percent {
  font-size: 12px;
  color: #9ca3af;
  font-weight: 500;
}



/* 最新结果卡片 */
.recent-results-card {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
}

.recent-results-card .card-header h3 {
  margin: 0;
  color: #1f2937;
  font-size: 18px;
  font-weight: 600;
}

.results-container {
  margin-top: 16px;
}

.results-table {
  border-radius: 8px;
  overflow: hidden;
}

.status-icon {
  margin-right: 4px;
  font-size: 14px;
}

.response-time {
  font-weight: 600;
  color: #10b981;
  font-size: 13px;
}

.no-data {
  color: #9ca3af;
  font-style: italic;
  font-size: 13px;
}

.check-time {
  text-align: left;
}

.time-main {
  font-size: 13px;
  color: #374151;
  line-height: 1.2;
}

.time-ago {
  color: #9ca3af;
  font-size: 11px;
}

/* 页面加载动画 */
.fade-in-container {
  animation: pageLoad 0.8s ease-out;
}

.quick-actions-panel > .action-card {
  animation: slideInUp 0.6s ease-out;
}

.quick-actions-panel > .action-card:nth-child(1) {
  animation-delay: 0.1s;
}

.quick-actions-panel > .action-card:nth-child(2) {
  animation-delay: 0.2s;
}

.quick-actions-panel > .action-card:nth-child(3) {
  animation-delay: 0.3s;
}

.stats-grid > .stat-card {
  animation: slideInUp 0.6s ease-out;
}

.stats-grid > .stat-card:nth-child(1) {
  animation-delay: 0.4s;
}

.stats-grid > .stat-card:nth-child(2) {
  animation-delay: 0.5s;
}

.stats-grid > .stat-card:nth-child(3) {
  animation-delay: 0.6s;
}

.stats-grid > .stat-card:nth-child(4) {
  animation-delay: 0.7s;
}

/* 页面动画关键帧 */
@keyframes pageLoad {
  0% {
    opacity: 0;
    transform: translateY(20px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideInUp {
  0% {
    opacity: 0;
    transform: translateY(30px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .quick-actions-panel {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .stats-grid {
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
  }
  
  .monitor-summary {
    flex-direction: column;
    gap: 16px;
  }
}
</style> 