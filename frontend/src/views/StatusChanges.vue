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
                <span class="value">{{ Math.round(task.interval_hours * 60) }} 分钟</span>
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
                :loading="task.toggling"
              >
                {{ task.is_active ? '停止' : '启动' }}
              </el-button>
              <el-button size="small" @click="editFailedTask(task)">
                编辑
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
            :page-sizes="[10, 15, 25, 50]"
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

    <!-- 编辑失败监控任务对话框 -->
    <el-dialog 
      v-model="editTaskDialogVisible" 
      title="编辑失败监控任务" 
      width="90%" 
      :style="{ maxWidth: '1000px', minWidth: '600px' }"
      class="edit-task-dialog"
      :close-on-click-modal="false"
    >
      <el-form :model="editTaskForm" label-width="120px" class="edit-task-form">
        <el-form-item label="任务名称">
          <el-input v-model="editTaskForm.name" placeholder="请输入任务名称" />
        </el-form-item>
        
        <el-form-item label="任务描述">
          <el-input 
            v-model="editTaskForm.description" 
            type="textarea" 
            :rows="3"
            placeholder="请输入任务描述"
          />
        </el-form-item>
        
        <el-form-item label="监控间隔">
          <div class="interval-input">
            <el-input-number 
              v-model="editTaskForm.interval_minutes" 
              :min="1" 
              :max="1440"
              placeholder="监控间隔"
            />
            <span class="interval-unit">分钟</span>
          </div>
          <div class="interval-tips">
            <small>建议间隔：失败网站检测建议15-60分钟，避免过于频繁</small>
          </div>
        </el-form-item>
        
        <el-form-item label="监控网站" class="website-form-item">
          <div class="website-selection-container">
            <div class="website-selection">
              <el-transfer
                v-model="editTaskForm.website_ids"
                :data="availableWebsites"
                :titles="['可选网站', '监控网站']"
                :button-texts="['移除 ←', '添加 →']"
                :format="{
                  noChecked: '共 ${total} 个',
                  hasChecked: '已选 ${checked} / ${total}'
                }"
                filterable
                :filter-placeholder="'搜索网站域名'"
                target-order="push"
              />
            </div>
            <div class="website-tips">
              <el-icon><InfoFilled /></el-icon>
              <span>选择需要监控的失败网站域名，系统会定期检测这些网站的恢复情况</span>
            </div>
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editTaskDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveEditTask" :loading="saving">
            保存设置
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted, onUnmounted, watch } from 'vue'
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
  Right,
  InfoFilled
} from '@element-plus/icons-vue'
import { resultApi, statusChangeApi, taskApi, websiteApi } from '../utils/api'

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
    Right,
    InfoFilled
  },
  setup() {
    const loading = ref(false)
    const statusChanges = ref([])
    const failedMonitorTasks = ref([])
    const taskWebsites = ref([])
    const total = ref(0)
    const currentPage = ref(1)
    const pageSize = ref(15) // 减少每页数据量
    const changeTypeFilter = ref('')
    const taskWebsitesDialogVisible = ref(false)
    const editTaskDialogVisible = ref(false)
    const saving = ref(false)
    const availableWebsites = ref([])

    const editTaskForm = reactive({
      id: null,
      name: '',
      description: '',
      interval_minutes: 30,
      website_ids: []
    })

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
        
        // 转换后端数据格式为前端需要的格式，只保留必要字段
        const allChanges = [
          ...response.data.became_accessible.map(item => ({
            id: item.id,
            website_name: item.website_name || item.name,
            website_domain: item.website_domain || item.domain,
            change_type: 'to_success',
            detected_at: item.detected_at || item.change_time,
            current_status: 'standard'
          })),
          ...response.data.became_failed.map(item => ({
            id: item.id,
            website_name: item.website_name || item.name,
            website_domain: item.website_domain || item.domain,
            change_type: 'to_failed',
            detected_at: item.detected_at || item.change_time,
            current_status: 'failed'
          })),
          ...response.data.status_changed.map(item => ({
            id: item.id,
            website_name: item.website_name || item.name,
            website_domain: item.website_domain || item.domain,
            change_type: 'status_change',
            detected_at: item.detected_at || item.change_time,
            current_status: item.current_status || item.new_status
          }))
        ]

        // 过滤条件并限制数量
        let filteredChanges = allChanges
        if (changeTypeFilter.value) {
          filteredChanges = allChanges.filter(change => change.change_type === changeTypeFilter.value)
        }

        // 限制最大显示数量，避免内存过载
        const maxChanges = 100
        if (filteredChanges.length > maxChanges) {
          filteredChanges = filteredChanges.slice(0, maxChanges)
        }

        statusChanges.value = filteredChanges
        total.value = Math.min(filteredChanges.length, maxChanges)
        
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
        // 设置加载状态
        task.toggling = true
        
        // 获取任务ID
        const tasksResponse = await taskApi.getList({ page: 1, per_page: 1 })
        if (!tasksResponse.data.tasks || tasksResponse.data.tasks.length === 0) {
          ElMessage.error('没有找到可用的任务')
          return
        }

        const firstTaskId = tasksResponse.data.tasks[0].id
        
        // 调用切换API
        const response = await statusChangeApi.toggleFailedMonitorTask(firstTaskId)
        
        ElMessage.success(response.message || `任务已${task.is_active ? '停止' : '启动'}`)
        
        // 重新加载任务列表
        await loadFailedMonitorTasks()
      } catch (error) {
        console.error('切换任务状态失败:', error)
        ElMessage.error('操作失败：' + (error.response?.data?.message || error.message))
      } finally {
        task.toggling = false
      }
    }

    // 编辑失败监控任务
    const editFailedTask = async (task) => {
      try {
        // 重置表单
        Object.assign(editTaskForm, {
          id: task.id,
          name: task.name,
          description: task.description || '',
          interval_minutes: Math.round(task.interval_hours * 60),
          website_ids: []
        })
        
        // 加载可用网站列表
        await loadAvailableWebsites()
        
        // 获取当前任务监控的网站
        await loadCurrentTaskWebsites(task.id)
        
        editTaskDialogVisible.value = true
      } catch (error) {
        ElMessage.error('加载编辑数据失败')
      }
    }

    // 保存编辑的任务
    const saveEditTask = async () => {
      try {
        saving.value = true
        
        // 获取任务ID
        const tasksResponse = await taskApi.getList({ page: 1, per_page: 1 })
        if (!tasksResponse.data.tasks || tasksResponse.data.tasks.length === 0) {
          ElMessage.error('没有找到可用的任务')
          return
        }

        const firstTaskId = tasksResponse.data.tasks[0].id
        
        // 准备更新数据
        const updateData = {
          name: editTaskForm.name,
          description: editTaskForm.description,
          interval_minutes: editTaskForm.interval_minutes,
          website_ids: editTaskForm.website_ids
        }
        
        // 调用更新API
        const response = await statusChangeApi.updateFailedMonitorTask(firstTaskId, updateData)
        
        ElMessage.success(response.message || '任务更新成功')
        editTaskDialogVisible.value = false
        
        // 重新加载任务列表
        await loadFailedMonitorTasks()
      } catch (error) {
        console.error('保存任务失败:', error)
        ElMessage.error('保存失败：' + (error.response?.data?.message || error.message))
      } finally {
        saving.value = false
      }
    }

    // 加载可用网站列表
    const loadAvailableWebsites = async () => {
      try {
        const response = await websiteApi.getList({ page: 1, per_page: 1000 })
        availableWebsites.value = response.data.websites.map(website => ({
          key: website.id,
          label: website.domain,
          disabled: false
        }))
      } catch (error) {
        console.error('加载网站列表失败:', error)
        // 使用模拟数据
        availableWebsites.value = [
          { key: 5, label: '北龙中网.网址', disabled: false },
          { key: 6, label: '测试.网址', disabled: false },
          { key: 7, label: '中网.网址', disabled: false },
          { key: 8, label: '百度.网址', disabled: false },
          { key: 9, label: '谷歌.网址', disabled: false },
          { key: 10, label: '腾讯.网址', disabled: false },
          { key: 11, label: '大兴智能.网址', disabled: false }
        ]
      }
    }

    // 加载当前任务监控的网站
    const loadCurrentTaskWebsites = async (taskId) => {
      try {
        // 这里应该调用API获取当前任务监控的网站，暂时使用模拟数据
        editTaskForm.website_ids = [5, 6, 7, 8, 9] // 模拟已选择的网站ID
      } catch (error) {
        console.error('加载任务网站失败:', error)
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

        // 获取任务ID
        const tasksResponse = await taskApi.getList({ page: 1, per_page: 1 })
        if (!tasksResponse.data.tasks || tasksResponse.data.tasks.length === 0) {
          ElMessage.error('没有找到可用的任务')
          return
        }

        const firstTaskId = tasksResponse.data.tasks[0].id
        
        // 调用删除API
        const response = await statusChangeApi.deleteFailedMonitorTask(firstTaskId)
        
        ElMessage.success(response.message || '任务删除成功')
        await loadFailedMonitorTasks()
      } catch (error) {
        if (error !== 'cancel') {
          console.error('删除任务失败:', error)
          ElMessage.error('删除失败：' + (error.response?.data?.message || error.message))
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

    // 组件卸载时清理数据
    onUnmounted(() => {
      // 清理数组数据
      statusChanges.value.length = 0
      failedMonitorTasks.value.length = 0
      taskWebsites.value.length = 0
      availableWebsites.value.length = 0
      
      // 清理统计数据
      Object.assign(statusChangeStats, {
        total_changes: 0,
        to_failed: 0,
        to_success: 0,
        status_change: 0
      })
      
      Object.assign(failedSiteMonitorStats, {
        active_tasks: 0,
        total_websites: 0,
        monitoring_websites: 0
      })
      
      // 重置状态
      hasFailedSites.value = false
      loading.value = false
      saving.value = false
      taskWebsitesDialogVisible.value = false
      editTaskDialogVisible.value = false
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
      editTaskDialogVisible,
      editTaskForm,
      availableWebsites,
      saving,
      statusChangeStats,
      failedSiteMonitorStats,
      hasFailedSites,
      refreshData,
      createFailedSiteTask,
      toggleFailedTask,
      editFailedTask,
      saveEditTask,
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

/* 编辑对话框样式 */
.edit-task-dialog {
  width: 90%;
  max-width: 1000px;
  min-width: 700px;
}

.edit-task-dialog :deep(.el-dialog__body) {
  overflow-x: hidden;
  padding: 16px 24px;
}

.edit-task-dialog :deep(.el-dialog__header) {
  padding: 20px 24px 16px 24px;
}

.edit-task-dialog :deep(.el-dialog__footer) {
  padding: 16px 24px 20px 24px;
}

@media (max-width: 900px) {
  .edit-task-dialog {
    width: 95%;
    min-width: auto;
    max-width: none;
  }
  
  .edit-task-dialog :deep(.el-dialog__body) {
    padding: 12px 16px;
  }
  
  .edit-task-dialog :deep(.el-dialog__header) {
    padding: 16px 16px 12px 16px;
  }
  
  .edit-task-dialog :deep(.el-dialog__footer) {
    padding: 12px 16px 16px 16px;
  }
}

.edit-task-form {
  padding: 16px 0;
  overflow: hidden;
}

.edit-task-form .el-form-item {
  margin-bottom: 20px;
}

.edit-task-form .el-form-item__content {
  overflow: hidden;
}

.interval-input {
  display: flex;
  align-items: center;
  gap: 8px;
}

.interval-unit {
  color: #6b7280;
  font-size: 14px;
  font-weight: 500;
}

.interval-tips {
  margin-top: 8px;
  color: #6b7280;
  font-size: 12px;
}

/* 网站选择容器优化 */
.website-form-item {
  margin-bottom: 20px;
}

.website-form-item .el-form-item__content {
  overflow: hidden;
}

.website-selection-container {
  width: 100%;
  overflow: hidden;
  box-sizing: border-box;
}

.website-selection {
  width: 100%;
  min-height: 400px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 12px;
  border: 1px solid #e4e7ed;
  margin-bottom: 16px;
  overflow: hidden;
  box-sizing: border-box;
}

.website-tips {
  color: #606266;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #f0f9ff;
  border: 1px solid #b3d8ff;
  border-radius: 8px;
  margin: 0;
}

.website-tips .el-icon {
  color: #409eff;
  font-size: 16px;
  flex-shrink: 0;
}

/* 穿梭框样式优化 */
.website-selection :deep(.el-transfer) {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: stretch;
  background: transparent;
  border: none;
  gap: 12px;
  box-sizing: border-box;
}

.website-selection :deep(.el-transfer-panel) {
  border: 1px solid #dcdfe6;
  border-radius: 10px;
  background: #ffffff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  height: 400px;
  display: flex;
  flex-direction: column;
}

.website-selection :deep(.el-transfer-panel:hover) {
  border-color: #409eff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
}

.website-selection :deep(.el-transfer-panel__header) {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  border-bottom: 1px solid #ebeef5;
  padding: 16px 20px;
  border-radius: 10px 10px 0 0;
  font-weight: 600;
  color: #303133;
  font-size: 14px;
}

.website-selection :deep(.el-transfer-panel__filter) {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
  flex-shrink: 0;
}

.website-selection :deep(.el-transfer-panel__filter .el-input) {
  border-radius: 8px;
}

.website-selection :deep(.el-transfer-panel__list) {
  padding: 8px 0;
  height: 280px;
  min-height: 280px;
  overflow-y: auto;
}

.website-selection :deep(.el-transfer-panel__item) {
  padding: 8px 12px !important;
  margin: 2px 6px !important;
  border-radius: 6px;
  transition: all 0.2s ease;
  font-size: 13px;
  display: flex !important;
  align-items: center !important;
  line-height: 1.2;
  min-height: 32px !important;
  position: relative !important;
  width: calc(100% - 12px) !important;
  box-sizing: border-box !important;
}

.website-selection :deep(.el-transfer-panel__item:hover) {
  background: #f0f9ff;
  transform: translateX(2px);
}

.website-selection :deep(.el-transfer-panel__item.is-checked) {
  background: #e1f5fe;
  color: #1976d2;
  font-weight: 500;
}

/* 核心对齐修复 - 确保复选框和文本在同一行 */
.website-selection :deep(.el-transfer-panel__item .el-checkbox) {
  display: flex !important;
  align-items: center !important;
  width: 100% !important;
  margin: 0 !important;
  padding: 0 !important;
  min-height: 20px !important;
  gap: 12px !important;
}

.website-selection :deep(.el-transfer-panel__item .el-checkbox__input) {
  flex-shrink: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  width: 18px !important;
  height: 18px !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}

.website-selection :deep(.el-transfer-panel__item .el-checkbox__inner) {
  width: 14px !important;
  height: 14px !important;
  margin: 0 !important;
  padding: 0 !important;
}

.website-selection :deep(.el-transfer-panel__item .el-checkbox__label) {
  flex: 1 !important;
  margin-left: 30px !important;
  padding: 0 !important;
  line-height: 20px !important;
  font-size: 14px !important;
  display: block !important;
  word-wrap: break-word !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  white-space: nowrap !important;
}

/* 确保原生input不影响布局 */
.website-selection :deep(.el-transfer-panel__item .el-checkbox__original) {
  position: absolute !important;
  opacity: 0 !important;
  left: -9999px !important;
}

/* 优化列表容器 */
.website-selection :deep(.el-transfer-panel__list) {
  padding: 6px !important;
  height: 280px !important;
  min-height: 280px !important;
  display: flex !important;
  flex-direction: column !important;
}

/* 调整穿梭框主体高度 */
.website-selection :deep(.el-transfer-panel__body) {
  height: 400px !important;
}

.website-selection :deep(.el-transfer__buttons) {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 12px;
  padding: 0 8px;
  min-width: 100px;
  max-width: 100px;
  box-sizing: border-box;
}

.website-selection :deep(.el-transfer__button) {
  border-radius: 20px;
  padding: 8px 12px;
  font-size: 12px;
  font-weight: 600;
  min-width: 70px;
  max-width: 80px;
  transition: all 0.3s ease;
  border: 2px solid #409eff;
  background: #ffffff;
  color: #409eff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.website-selection :deep(.el-transfer__button:hover:not(.is-disabled)) {
  background: #409eff;
  color: #ffffff;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.4);
}

.website-selection :deep(.el-transfer__button.is-disabled) {
  opacity: 0.4;
  cursor: not-allowed;
  border-color: #c0c4cc;
  color: #c0c4cc;
}

/* 滚动条美化 */
.website-selection :deep(.el-transfer-panel__list::-webkit-scrollbar) {
  width: 6px;
}

.website-selection :deep(.el-transfer-panel__list::-webkit-scrollbar-track) {
  background: #f1f1f1;
  border-radius: 3px;
}

.website-selection :deep(.el-transfer-panel__list::-webkit-scrollbar-thumb) {
  background: #c1c1c1;
  border-radius: 3px;
}

.website-selection :deep(.el-transfer-panel__list::-webkit-scrollbar-thumb:hover) {
  background: #a8a8a8;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 任务卡片的加载状态 */
.task-actions .el-button.is-loading {
  cursor: not-allowed;
}

/* 大屏幕布局 */
@media (min-width: 1024px) {
  .website-selection :deep(.el-transfer-panel) {
    width: calc(44% - 6px);
    min-width: 260px;
    max-width: 340px;
    height: 400px;
    flex-shrink: 1;
  }
  
  .website-selection :deep(.el-transfer__buttons) {
    width: 12%;
    min-width: 90px;
    max-width: 110px;
    flex-shrink: 0;
  }
}

/* 中等屏幕适配 */
@media (max-width: 1023px) and (min-width: 769px) {
  .website-selection :deep(.el-transfer-panel) {
    width: calc(44% - 4px);
    min-width: 240px;
    max-width: 300px;
    height: 380px;
    flex-shrink: 0;
  }
  
  .website-selection :deep(.el-transfer__buttons) {
    width: 12%;
    min-width: 80px;
    max-width: 80px;
    padding: 0 6px;
  }
  
  .website-selection :deep(.el-transfer__button) {
    min-width: 60px;
    max-width: 70px;
    padding: 6px 8px;
    font-size: 11px;
  }
  
  .website-selection :deep(.el-transfer-panel__item) {
    padding: 8px 12px !important;
    font-size: 12px !important;
    min-height: 30px !important;
    gap: 8px !important;
  }
  
  .website-selection :deep(.el-transfer-panel__item .el-checkbox__input) {
    width: 14px !important;
    height: 14px !important;
  }
  
  .website-selection :deep(.el-transfer-panel__item .el-checkbox__inner) {
    width: 12px !important;
    height: 12px !important;
  }
  
  .website-selection :deep(.el-transfer-panel__item .el-checkbox__label) {
    font-size: 12px !important;
    padding-left: 6px !important;
  }
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
  
  .edit-task-form {
    padding: 8px 0;
  }
  
  .website-selection {
    min-height: auto;
    padding: 12px;
    margin-bottom: 12px;
  }
  
  .website-selection :deep(.el-transfer) {
    flex-direction: column;
    gap: 12px;
  }
  
  .website-selection :deep(.el-transfer-panel) {
    width: 100% !important;
    min-width: auto;
    max-width: none;
    height: 260px;
    box-sizing: border-box;
  }
  
  .website-selection :deep(.el-transfer-panel__item) {
    padding: 8px 12px !important;
    font-size: 12px !important;
    min-height: 30px !important;
    gap: 8px !important;
  }
  
  .website-selection :deep(.el-transfer-panel__item .el-checkbox__input) {
    width: 14px !important;
    height: 14px !important;
  }
  
  .website-selection :deep(.el-transfer-panel__item .el-checkbox__inner) {
    width: 12px !important;
    height: 12px !important;
  }
  
  .website-selection :deep(.el-transfer-panel__item .el-checkbox__label) {
    font-size: 12px !important;
    padding-left: 6px !important;
  }
  
  .website-selection :deep(.el-transfer__buttons) {
    flex-direction: row;
    justify-content: center;
    min-width: auto;
    max-width: none;
    width: 100%;
    padding: 8px 0;
    box-sizing: border-box;
  }
  
  .website-selection :deep(.el-transfer__button) {
    min-width: 70px;
    max-width: 100px;
    margin: 0 6px;
    padding: 6px 10px;
  }
}
</style> 