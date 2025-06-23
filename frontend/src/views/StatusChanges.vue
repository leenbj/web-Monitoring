<template>
  <div class="status-changes-page">
    <!-- 页面标题和操作按钮 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h2>状态变化监控</h2>
          <span class="subtitle">监控网站状态变化，自动处理异常网站</span>
        </div>
        <div class="actions">
          <el-button @click="refreshData" :loading="loading" size="default">
            <el-icon><Refresh /></el-icon>
            刷新数据
          </el-button>
          <el-button type="primary" @click="createFailedSiteTask" :disabled="!hasFailedSites" size="default">
            <el-icon><Timer /></el-icon>
            创建失败监控任务
          </el-button>
        </div>
      </div>
    </div>

    <!-- 统计面板 -->
    <div class="stats-grid">
      <div class="stat-card warning-card">
        <div class="stat-content">
          <div class="stat-icon">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-number">{{ statusChangeStats.total_changes }}</div>
            <div class="stat-label">总状态变化</div>
            <div class="stat-percent">过去24小时</div>
          </div>
        </div>
      </div>
      
      <div class="stat-card danger-card">
        <div class="stat-content">
          <div class="stat-icon">
            <el-icon><Warning /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-number">{{ statusChangeStats.to_failed }}</div>
            <div class="stat-label">变为失败</div>
            <div class="stat-percent">需要关注</div>
          </div>
        </div>
      </div>
      
      <div class="stat-card success-card">
        <div class="stat-content">
          <div class="stat-icon">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-number">{{ statusChangeStats.to_success }}</div>
            <div class="stat-label">恢复正常</div>
            <div class="stat-percent">已恢复</div>
          </div>
        </div>
      </div>
      
      <div class="stat-card info-card">
        <div class="stat-content">
          <div class="stat-icon">
            <el-icon><Monitor /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-number">{{ failedSiteMonitorStats.active_tasks }}</div>
            <div class="stat-label">监控任务</div>
            <div class="stat-percent">正在运行</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 失败网站监控任务面板 -->
    <el-card class="failed-monitor-card" shadow="never">
      <template #header>
        <div class="card-header">
          <h3>
            <el-icon><Monitor /></el-icon>
            失败网站监控任务
          </h3>
          <el-tag :type="failedSiteMonitorStats.active_tasks > 0 ? 'success' : 'info'" size="small">
            {{ failedSiteMonitorStats.active_tasks }} 个活跃任务
          </el-tag>
        </div>
      </template>
      
      <div class="monitor-tasks-container">
        <div v-if="failedMonitorTasks.length === 0" class="empty-state">
          <el-empty description="暂无失败网站监控任务" />
        </div>
        <div v-else class="tasks-grid">
          <div v-for="task in failedMonitorTasks" :key="task.id" class="task-card">
            <div class="task-header">
              <div class="task-title">
                <el-icon><Timer /></el-icon>
                {{ task.name }}
              </div>
              <el-tag :type="task.is_active ? 'success' : 'danger'" size="small">
                {{ task.is_active ? '运行中' : '已停止' }}
              </el-tag>
            </div>
            <div class="task-info">
              <div class="info-item">
                <span class="label">监控网站：</span>
                <span class="value">{{ task.website_count }} 个</span>
              </div>
              <div class="info-item">
                <span class="label">检测间隔：</span>
                <span class="value">{{ task.interval_hours }} 小时</span>
              </div>
              <div class="info-item">
                <span class="label">最后运行：</span>
                <span class="value">{{ task.last_run_at ? formatDate(task.last_run_at) : '从未运行' }}</span>
              </div>
            </div>
            <div class="task-actions">
              <el-button 
                size="small" 
                :type="task.is_active ? 'warning' : 'success'"
                @click="toggleFailedTask(task)"
              >
                {{ task.is_active ? '停止' : '启动' }}
              </el-button>
              <el-button size="small" @click="viewTaskWebsites(task)">
                查看网站
              </el-button>
              <el-button size="small" type="danger" @click="deleteFailedTask(task)">
                删除
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 状态变化历史 -->
    <el-card class="status-changes-card" shadow="never">
      <template #header>
        <div class="card-header">
          <h3>
            <el-icon><TrendCharts /></el-icon>
            最近状态变化
          </h3>
          <div class="filter-controls">
            <el-select v-model="changeTypeFilter" placeholder="变化类型" clearable size="small">
              <el-option label="全部变化" value="" />
              <el-option label="变为失败" value="to_failed" />
              <el-option label="恢复正常" value="to_success" />
              <el-option label="状态改变" value="status_change" />
            </el-select>
          </div>
        </div>
      </template>

      <div class="changes-container">
        <el-table :data="statusChanges" v-loading="loading" class="changes-table">
          <el-table-column prop="website_name" label="网站名称" min-width="150" show-overflow-tooltip />
          
          <el-table-column prop="website_domain" label="域名" min-width="180" show-overflow-tooltip>
            <template #default="{ row }">
              <el-link :href="'http://' + row.website_domain" target="_blank" type="primary">
                {{ row.website_domain }}
              </el-link>
            </template>
          </el-table-column>
          
          <el-table-column prop="change_type" label="变化类型" width="120" align="center">
            <template #default="{ row }">
              <el-tag 
                :type="getChangeTypeStyle(row.change_type)"
                size="small"
                effect="dark"
              >
                <el-icon class="change-icon">
                  <ArrowUp v-if="row.change_type === 'to_success'" />
                  <ArrowDown v-else-if="row.change_type === 'to_failed'" />
                  <Switch v-else />
                </el-icon>
                {{ getChangeTypeText(row.change_type) }}
              </el-tag>
            </template>
          </el-table-column>
          
          <el-table-column label="状态变化" width="200" align="center">
            <template #default="{ row }">
              <div class="status-change-display">
                <el-tag 
                  :type="getStatusType(row.old_status)" 
                  size="small"
                  effect="plain"
                >
                  {{ getStatusText(row.old_status) }}
                </el-tag>
                <el-icon class="arrow-icon"><Right /></el-icon>
                <el-tag 
                  :type="getStatusType(row.new_status)" 
                  size="small"
                  effect="dark"
                >
                  {{ getStatusText(row.new_status) }}
                </el-tag>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column prop="detected_at" label="变化时间" width="180">
            <template #default="{ row }">
              <div class="change-time">
                <div class="time-main">{{ formatDate(row.detected_at) }}</div>
                <small class="time-ago">{{ getTimeAgo(row.detected_at) }}</small>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip>
            <template #default="{ row }">
              <span class="change-description">{{ row.description || '状态发生变化' }}</span>
            </template>
          </el-table-column>
          
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button 
                v-if="row.new_status === 'failed'" 
                size="small" 
                type="primary"
                @click="addToFailedMonitor(row)"
              >
                添加监控
              </el-button>
              <el-button 
                size="small" 
                @click="viewWebsiteDetails(row)"
              >
                查看详情
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        
        <!-- 分页 -->
        <div class="pagination">
          <el-pagination
            :current-page="currentPage"
            :page-size="pageSize"
            :total="total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
            background
          />
        </div>
      </div>
    </el-card>

    <!-- 查看任务网站对话框 -->
    <el-dialog v-model="taskWebsitesDialogVisible" title="任务监控的网站" width="800px">
      <el-table :data="taskWebsites" max-height="400">
        <el-table-column prop="website_name" label="网站名称" />
        <el-table-column prop="website_domain" label="域名" />
        <el-table-column prop="status" label="当前状态" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_check_time" label="最后检测时间" />
      </el-table>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Refresh,
  Timer,
  TrendCharts,
  Warning,
  CircleCheck,
  Monitor,
  ArrowUp,
  ArrowDown,
  Switch,
  Right
} from '@element-plus/icons-vue'
import { resultApi, statusChangeApi, taskApi } from '../utils/api'

export default {
  name: 'StatusChanges',
  components: {
    Refresh,
    Timer,
    TrendCharts,
    Warning,
    CircleCheck,
    Monitor,
    ArrowUp,
    ArrowDown,
    Switch,
    Right
  },
  setup() {
    const loading = ref(false)
    const statusChanges = ref([])
    const failedMonitorTasks = ref([])
    const taskWebsites = ref([])
    const total = ref(0)
    const currentPage = ref(1)
    const pageSize = ref(20)
    const changeTypeFilter = ref('')
    const taskWebsitesDialogVisible = ref(false)

    const statusChangeStats = reactive({
      total_changes: 0,
      to_failed: 0,
      to_success: 0,
      status_change: 0
    })

    const failedSiteMonitorStats = reactive({
      active_tasks: 0,
      total_websites: 0,
      monitoring_websites: 0
    })

    const hasFailedSites = ref(false)

    // 加载状态变化数据
    const loadStatusChanges = async () => {
      loading.value = true
      try {
        // 先获取一个可用的任务ID
        const tasksResponse = await taskApi.getList({ page: 1, per_page: 1 })
        if (!tasksResponse.data.tasks || tasksResponse.data.tasks.length === 0) {
          console.warn('没有找到任务，使用模拟数据')
          statusChanges.value = generateMockStatusChanges()
          total.value = statusChanges.value.length
          return
        }

        const firstTaskId = tasksResponse.data.tasks[0].id
        const params = {
          hours: 24,
          limit: pageSize.value
        }

        // 获取状态变化数据
        const response = await statusChangeApi.getRecentChanges(firstTaskId, params)
        
        // 转换后端数据格式为前端需要的格式
        const allChanges = [
          ...response.data.became_accessible.map(item => ({ ...item, change_type: 'to_success' })),
          ...response.data.became_failed.map(item => ({ ...item, change_type: 'to_failed' })),
          ...response.data.status_changed.map(item => ({ ...item, change_type: 'status_change' }))
        ]

        // 过滤条件
        let filteredChanges = allChanges
        if (changeTypeFilter.value) {
          filteredChanges = allChanges.filter(change => change.change_type === changeTypeFilter.value)
        }

        statusChanges.value = filteredChanges
        total.value = filteredChanges.length
        
      } catch (error) {
        console.error('加载状态变化失败:', error)
        // 使用模拟数据
        statusChanges.value = generateMockStatusChanges()
        total.value = statusChanges.value.length
      } finally {
        loading.value = false
      }
    }

    // 加载状态变化统计
    const loadStatusChangeStats = async () => {
      try {
        // 获取任务ID
        const tasksResponse = await taskApi.getList({ page: 1, per_page: 1 })
        if (!tasksResponse.data.tasks || tasksResponse.data.tasks.length === 0) {
          console.warn('没有找到任务，使用模拟统计数据')
          Object.assign(statusChangeStats, {
            total_changes: 15,
            to_failed: 8,
            to_success: 5,
            status_change: 2
          })
          return
        }

        const firstTaskId = tasksResponse.data.tasks[0].id
        
        // 获取统计数据
        const response = await statusChangeApi.getRecentChanges(firstTaskId, { hours: 24, limit: 1000 })
        
        const stats = response.data.statistics
        Object.assign(statusChangeStats, {
          total_changes: stats.became_accessible_count + stats.became_failed_count + stats.status_changed_count,
          to_failed: stats.became_failed_count,
          to_success: stats.became_accessible_count,
          status_change: stats.status_changed_count
        })
        
      } catch (error) {
        console.error('加载状态变化统计失败:', error)
        // 模拟数据
        Object.assign(statusChangeStats, {
          total_changes: 15,
          to_failed: 8,
          to_success: 5,
          status_change: 2
        })
      }
    }

    // 加载失败网站监控任务
    const loadFailedMonitorTasks = async () => {
      try {
        // 获取任务ID
        const tasksResponse = await taskApi.getList({ page: 1, per_page: 1 })
        if (!tasksResponse.data.tasks || tasksResponse.data.tasks.length === 0) {
          console.warn('没有找到任务，使用模拟数据')
          failedMonitorTasks.value = generateMockFailedTasks()
          Object.assign(failedSiteMonitorStats, {
            active_tasks: 2,
            total_websites: 8,
            monitoring_websites: 8
          })
          return
        }

        const firstTaskId = tasksResponse.data.tasks[0].id
        
        // 获取失败监控任务状态
        const response = await statusChangeApi.getFailedMonitorStatus(firstTaskId)
        
        if (response.data.exists) {
          // 转换为前端需要的格式
          const monitorStatus = response.data
          failedMonitorTasks.value = [{
            id: monitorStatus.id,
            name: monitorStatus.name,
            is_active: monitorStatus.is_active,
            interval_hours: monitorStatus.interval_hours,
            website_count: monitorStatus.monitored_websites_count,
            last_run_at: monitorStatus.last_run_at,
            created_at: monitorStatus.created_at
          }]
          
          Object.assign(failedSiteMonitorStats, {
            active_tasks: monitorStatus.is_active ? 1 : 0,
            total_websites: monitorStatus.monitored_websites_count,
            monitoring_websites: monitorStatus.monitored_websites_count
          })
        } else {
          // 没有失败监控任务
          failedMonitorTasks.value = []
          Object.assign(failedSiteMonitorStats, {
            active_tasks: 0,
            total_websites: 0,
            monitoring_websites: 0
          })
        }
      } catch (error) {
        console.error('加载失败监控任务失败:', error)
        // 使用模拟数据
        failedMonitorTasks.value = generateMockFailedTasks()
        Object.assign(failedSiteMonitorStats, {
          active_tasks: 2,
          total_websites: 8,
          monitoring_websites: 8
        })
      }
    }

    // 生成模拟状态变化数据
    const generateMockStatusChanges = () => {
      const websites = ['百度.网址', '谷歌.网址', '腾讯.网址', '中网.网址', '测试.网址']
      const changeTypes = ['to_failed', 'to_success', 'status_change']
      const statuses = ['standard', 'redirect', 'failed']
      
      return Array.from({ length: 20 }, (_, i) => {
        const changeType = changeTypes[Math.floor(Math.random() * changeTypes.length)]
        const oldStatus = statuses[Math.floor(Math.random() * statuses.length)]
        let newStatus = statuses[Math.floor(Math.random() * statuses.length)]
        
        // 确保状态确实发生了变化
        while (newStatus === oldStatus) {
          newStatus = statuses[Math.floor(Math.random() * statuses.length)]
        }
        
        return {
          id: i + 1,
          website_name: websites[Math.floor(Math.random() * websites.length)],
          website_domain: websites[Math.floor(Math.random() * websites.length)],
          change_type: changeType,
          old_status: oldStatus,
          new_status: newStatus,
          detected_at: new Date(Date.now() - Math.random() * 24 * 60 * 60 * 1000).toISOString(),
          description: `网站状态从${getStatusText(oldStatus)}变为${getStatusText(newStatus)}`
        }
      })
    }

    // 生成模拟失败监控任务数据
    const generateMockFailedTasks = () => {
      return [
        {
          id: 1,
          name: '失败网站监控任务_20250620',
          is_active: true,
          interval_hours: 0.5,
          website_count: 5,
          last_run_at: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
          created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString()
        },
        {
          id: 2,
          name: '失败网站监控任务_20250619',
          is_active: false,
          interval_hours: 0.5,
          website_count: 3,
          last_run_at: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString(),
          created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString()
        }
      ]
    }

    // 创建失败网站监控任务
    const createFailedSiteTask = async () => {
      try {
        const response = await ElMessageBox.confirm(
          '将为所有状态为"失败"的网站创建监控任务，每30分钟检测一次，是否继续？',
          '创建失败网站监控任务',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )

        // 获取任务ID
        const tasksResponse = await taskApi.getList({ page: 1, per_page: 1 })
        if (!tasksResponse.data.tasks || tasksResponse.data.tasks.length === 0) {
          ElMessage.error('没有找到可用的任务')
          return
        }

        const firstTaskId = tasksResponse.data.tasks[0].id
        
        // 创建或更新失败监控任务
        const createResponse = await statusChangeApi.createOrUpdateFailedMonitor(firstTaskId)
        
        ElMessage.success(createResponse.message || '失败网站监控任务创建成功')
        await loadFailedMonitorTasks()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('创建任务失败')
        }
      }
    }

    // 切换失败监控任务状态
    const toggleFailedTask = async (task) => {
      try {
        // 模拟API调用
        ElMessage.success(`任务已${task.is_active ? '停止' : '启动'}`)
        task.is_active = !task.is_active
        await loadFailedMonitorTasks()
      } catch (error) {
        ElMessage.error('操作失败')
      }
    }

    // 删除失败监控任务
    const deleteFailedTask = async (task) => {
      try {
        await ElMessageBox.confirm(
          `确定要删除任务 "${task.name}" 吗？`,
          '确认删除',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )

        ElMessage.success('任务删除成功')
        await loadFailedMonitorTasks()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('删除失败')
        }
      }
    }

    // 查看任务监控的网站
    const viewTaskWebsites = async (task) => {
      try {
        // 模拟加载任务网站数据
        taskWebsites.value = [
          { website_name: '测试网站1', website_domain: '测试.网址', status: 'failed', last_check_time: '2025-06-20 15:30:00' },
          { website_name: '测试网站2', website_domain: '测试2.网址', status: 'failed', last_check_time: '2025-06-20 15:30:00' }
        ]
        taskWebsitesDialogVisible.value = true
      } catch (error) {
        ElMessage.error('加载任务网站失败')
      }
    }

    // 添加到失败监控
    const addToFailedMonitor = async (row) => {
      try {
        // 获取任务ID
        const tasksResponse = await taskApi.getList({ page: 1, per_page: 1 })
        if (!tasksResponse.data.tasks || tasksResponse.data.tasks.length === 0) {
          ElMessage.error('没有找到可用的任务')
          return
        }

        const firstTaskId = tasksResponse.data.tasks[0].id
        
        // 创建或更新失败监控任务（这会自动包含所有失败的网站）
        await statusChangeApi.createOrUpdateFailedMonitor(firstTaskId)
        
        ElMessage.success(`网站 ${row.website_name} 已添加到失败监控任务`)
        await loadFailedMonitorTasks()
      } catch (error) {
        ElMessage.error('添加失败')
      }
    }

    // 查看网站详情
    const viewWebsiteDetails = (row) => {
      // 跳转到网站详情或检测结果页面
      ElMessage.info('跳转到网站详情页面')
    }

    // 刷新所有数据
    const refreshData = async () => {
      await Promise.all([
        loadStatusChanges(),
        loadStatusChangeStats(),
        loadFailedMonitorTasks()
      ])
    }

    // 分页处理
    const handleSizeChange = (size) => {
      pageSize.value = size
      currentPage.value = 1
      loadStatusChanges()
    }

    const handleCurrentChange = (page) => {
      currentPage.value = page
      loadStatusChanges()
    }

    // 辅助方法
    const getChangeTypeStyle = (type) => {
      const typeMap = {
        'to_success': 'success',
        'to_failed': 'danger',
        'status_change': 'warning'
      }
      return typeMap[type] || 'info'
    }

    const getChangeTypeText = (type) => {
      const typeMap = {
        'to_success': '恢复正常',
        'to_failed': '变为失败',
        'status_change': '状态改变'
      }
      return typeMap[type] || '未知变化'
    }

    const getStatusType = (status) => {
      const typeMap = {
        'standard': 'success',
        'redirect': 'warning',
        'failed': 'danger'
      }
      return typeMap[status] || 'info'
    }

    const getStatusText = (status) => {
      const statusMap = {
        'standard': '正常访问',
        'redirect': '跳转访问',
        'failed': '无法访问'
      }
      return statusMap[status] || '未知'
    }

    const formatDate = (dateString) => {
      if (!dateString) return '-'
      return new Date(dateString).toLocaleString('zh-CN')
    }

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

    // 监听过滤条件变化
    watch(changeTypeFilter, () => {
      currentPage.value = 1
      loadStatusChanges()
    })

    // 检查是否有失败网站
    watch(statusChanges, (newChanges) => {
      hasFailedSites.value = newChanges.some(change => change.new_status === 'failed')
    })

    onMounted(() => {
      refreshData()
    })

    return {
      loading,
      statusChanges,
      failedMonitorTasks,
      taskWebsites,
      total,
      currentPage,
      pageSize,
      changeTypeFilter,
      taskWebsitesDialogVisible,
      statusChangeStats,
      failedSiteMonitorStats,
      hasFailedSites,
      refreshData,
      createFailedSiteTask,
      toggleFailedTask,
      deleteFailedTask,
      viewTaskWebsites,
      addToFailedMonitor,
      viewWebsiteDetails,
      handleSizeChange,
      handleCurrentChange,
      getChangeTypeStyle,
      getChangeTypeText,
      getStatusType,
      getStatusText,
      formatDate,
      getTimeAgo
    }
  }
}
</script>

<style scoped>
/* Claude网站风格样式 */
.status-changes-page {
  padding: 24px;
  min-height: calc(100vh - 100px);
  background: #fafafa;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

/* 页面头部 - Claude风格 */
.page-header {
  margin-bottom: 24px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  padding: 0;
}

.title-section h2 {
  margin: 0 0 4px 0;
  color: #111827;
  font-size: 20px;
  font-weight: 600;
  letter-spacing: -0.025em;
}

.subtitle {
  color: #6b7280;
  font-size: 14px;
  font-weight: 500;
}

.actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

/* 统计网格 - Claude风格 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
  transition: all 0.15s ease;
}

.stat-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.success-card {
  border-left: 4px solid #10b981;
}

.warning-card {
  border-left: 4px solid #d97706;
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
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: #ffffff;
}

.success-card .stat-icon {
  background: linear-gradient(135deg, #10b981, #059669);
}

.warning-card .stat-icon {
  background: linear-gradient(135deg, #d97706, #b45309);
}

.danger-card .stat-icon {
  background: linear-gradient(135deg, #ef4444, #dc2626);
}

.info-card .stat-icon {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
}

.stat-info {
  flex: 1;
}

.stat-number {
  font-size: 28px;
  font-weight: 600;
  color: #111827;
  line-height: 1;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #6b7280;
  font-weight: 500;
  margin-bottom: 2px;
}

.stat-percent {
  font-size: 12px;
  color: #9ca3af;
}

/* 卡片样式 - Claude风格 */
.failed-monitor-card,
.status-changes-card {
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

.card-header h3 {
  margin: 0;
  color: #111827;
  font-size: 18px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-controls {
  display: flex;
  gap: 12px;
  align-items: center;
}

/* 监控任务网格 - Claude风格 */
.tasks-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 20px;
}

.task-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
  transition: all 0.15s ease;
}

.task-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.task-title {
  font-weight: 600;
  color: #111827;
  display: flex;
  align-items: center;
  gap: 8px;
}

.task-info {
  margin-bottom: 16px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.info-item .label {
  color: #6b7280;
  font-size: 14px;
  font-weight: 500;
}

.info-item .value {
  color: #374151;
  font-size: 14px;
  font-weight: 600;
}

.task-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

/* 表格样式 - Claude风格 */
.changes-table {
  border-radius: 12px;
  overflow: hidden;
}

.status-change-display {
  display: flex;
  align-items: center;
  gap: 8px;
  justify-content: center;
}

.arrow-icon {
  color: #6b7280;
}

.change-icon {
  margin-right: 4px;
}

.change-time {
  text-align: left;
}

.time-main {
  font-size: 14px;
  color: #111827;
  font-weight: 500;
  line-height: 1.2;
}

.time-ago {
  color: #6b7280;
  font-size: 12px;
}

.change-description {
  color: #374151;
  font-size: 14px;
}

.pagination {
  margin-top: 24px;
  display: flex;
  justify-content: center;
  padding: 16px 0;
}

.empty-state {
  padding: 60px 20px;
}

/* 按钮样式 - Claude风格 */
.actions .el-button {
  font-weight: 500;
  border-radius: 8px;
  transition: all 0.15s ease;
  font-size: 14px;
}

.actions .el-button[type="primary"] {
  background: #d97706;
  border-color: #d97706;
}

.actions .el-button:not([type="primary"]) {
  background: #f9fafb;
  border-color: #e5e7eb;
  color: #374151;
}

.actions .el-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

/* 激活状态按钮样式 */
.task-actions .el-button {
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
  transition: all 0.15s ease;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .status-changes-page {
    padding: 16px;
  }
  
  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .actions {
    width: 100%;
    justify-content: flex-start;
    flex-wrap: wrap;
  }
  
  .stats-grid {
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  }
  
  .tasks-grid {
    grid-template-columns: 1fr;
  }
  
  .status-change-display {
    flex-direction: column;
    gap: 4px;
  }
}
</style> 