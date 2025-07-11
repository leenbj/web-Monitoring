<template>
  <div class="results-page">
    <div class="page-header">
      <div class="header-left">
        <h2>检测结果</h2>
        <el-tag v-if="taskName" type="primary" size="large" class="task-tag">
          <el-icon><DataAnalysis /></el-icon>
          任务：{{ taskName }}
        </el-tag>
      </div>
      <div class="actions">
        <el-button type="success" @click="exportResults">
          <el-icon><Download /></el-icon>
          导出结果
        </el-button>
        <el-button type="primary" @click="loadResults">
          <el-icon><Refresh /></el-icon>
          刷新数据
        </el-button>
        <el-button type="danger" @click="clearDataWithConfirm">
          <el-icon><Delete /></el-icon>
          清除数据
        </el-button>
      </div>
    </div>

    <!-- 统计面板 -->
    <div class="stats-panel">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="stat-card success-card" shadow="hover">
            <div class="stat-content">
              <div class="stat-icon">
                <el-icon><CircleCheck /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-number">{{ stats.standard_count }}</div>
                <div class="stat-label">正常访问</div>
                <div class="stat-percent">{{ stats.standard_rate?.toFixed(1) }}%</div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="stat-card warning-card" shadow="hover">
            <div class="stat-content">
              <div class="stat-icon">
                <el-icon><Warning /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-number">{{ stats.redirect_count }}</div>
                <div class="stat-label">跳转访问</div>
                <div class="stat-percent">{{ stats.redirect_rate?.toFixed(1) }}%</div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="stat-card danger-card" shadow="hover">
            <div class="stat-content">
              <div class="stat-icon">
                <el-icon><CircleClose /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-number">{{ stats.failed_count }}</div>
                <div class="stat-label">无法访问</div>
                <div class="stat-percent">{{ stats.failed_rate?.toFixed(1) }}%</div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="stat-card info-card" shadow="hover">
            <div class="stat-content">
              <div class="stat-icon">
                <el-icon><DataAnalysis /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-number">{{ stats.total_checks }}</div>
                <div class="stat-label">总检测数</div>
                <div class="stat-percent">网站{{ stats.total_websites }}个</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 筛选条件 -->
    <el-card class="filter-card" shadow="never">
      <div class="filter-section">
        <el-row :gutter="20" align="middle">
          <el-col :span="4">
            <el-select v-model="statusFilter" placeholder="检测状态" clearable @change="loadResults">
              <el-option label="全部状态" value="" />
              <el-option label="正常访问" value="standard" />
              <el-option label="跳转访问" value="redirect" />
              <el-option label="无法访问" value="failed" />
            </el-select>
          </el-col>
          <el-col :span="6">
            <el-date-picker
              v-model="dateRange"
              type="datetimerange"
              start-placeholder="开始时间"
              end-placeholder="结束时间"
              @change="loadResults"
              style="width: 100%"
            />
          </el-col>
          <el-col :span="1">
            <!-- 间距列 -->
          </el-col>
          <el-col :span="6">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索网站名称或域名"
              @input="debouncedSearch"
              clearable
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </el-col>
          <el-col :span="7">
            <div class="filter-summary">
              <el-tag type="info">共 {{ total }} 条记录</el-tag>
              <el-tag v-if="statusFilter" :type="getStatusTagType(statusFilter)">
                {{ getStatusText(statusFilter) }}
              </el-tag>
              <el-tag v-if="dateRange && dateRange.length === 2" type="warning">
                时间范围筛选
              </el-tag>
            </div>
          </el-col>
        </el-row>
      </div>
    </el-card>

    <!-- 结果表格 -->
    <el-card class="table-card" shadow="never">
      <el-table 
        :data="results" 
        v-loading="loading" 
        stripe 
        border 
        class="results-table"
        @selection-change="handleSelectionChange"
        ref="multipleTableRef"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="website_name" label="网站名称" min-width="150" show-overflow-tooltip />
        
        <el-table-column prop="website_domain" label="域名" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">
            <el-link :href="'http://' + row.website_domain" target="_blank" type="primary">
              {{ row.website_domain }}
            </el-link>
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="检测状态" width="140" align="center">
          <template #default="{ row }">
            <el-tag 
              :type="getStatusType(row.status)" 
              size="large"
              class="status-tag-large"
              effect="dark"
            >
              <el-icon class="status-icon">
                <CircleCheck v-if="row.status === 'standard'" />
                <Warning v-else-if="row.status === 'redirect'" />
                <CircleClose v-else />
              </el-icon>
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="response_time" label="响应时间" width="120" align="center">
          <template #default="{ row }">
            <span v-if="row.response_time" class="response-time">
              <el-tag 
                :type="getResponseTimeType(row.response_time)" 
                size="small"
                effect="plain"
              >
                {{ parseFloat(row.response_time).toFixed(2) }}ms
              </el-tag>
            </span>
            <span v-else class="no-data">-</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="http_status_code" label="状态码" width="100" align="center">
          <template #default="{ row }">
            <el-tag 
              v-if="row.http_status_code"
              :type="getHttpStatusType(row.http_status_code)"
              size="small"
            >
              {{ row.http_status_code }}
            </el-tag>
            <span v-else class="no-data">-</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="final_url" label="最终URL" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <div v-if="row.final_url && row.final_url !== ('http://' + row.website_domain)">
              <el-link :href="row.final_url" target="_blank" type="warning">
                {{ row.final_url }}
              </el-link>
              <el-tag type="warning" size="small" class="redirect-tag">跳转</el-tag>
            </div>
            <span v-else class="no-redirect">未跳转</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="error_message" label="错误信息" min-width="150" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.error_message" class="error-message">
              {{ row.error_message }}
            </span>
            <span v-else class="no-error">正常</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="detected_at" label="检测时间" width="180">
          <template #default="{ row }">
            <div class="check-time">
              <div>{{ formatDate(row.detected_at) }}</div>
              <small class="time-ago">{{ getTimeAgo(row.detected_at) }}</small>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 分页 -->
    <div class="pagination-container">
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
</template>

<script>
import { ref, reactive, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Download, 
  Refresh, 
  Search,
  CircleCheck,
  CircleClose,
  Warning,
  DataAnalysis,
  Delete
} from '@element-plus/icons-vue'
import { resultApi } from '../utils/api'
import { useRoute } from 'vue-router'

export default {
  name: 'Results',
  components: { 
    Download, 
    Refresh, 
    Search,
    CircleCheck,
    CircleClose,
    Warning,
    DataAnalysis,
    Delete
  },
  setup() {
    const route = useRoute()
    const loading = ref(false)
    const results = ref([])
    const total = ref(0)
    const currentPage = ref(1)
    const pageSize = ref(15) // 从20减少到15，减少单页数据量
    const statusFilter = ref('')
    const dateRange = ref([])
    const searchKeyword = ref('')
    const taskId = ref(null)
    const taskName = ref('')

    const stats = reactive({
      total_websites: 0,
      total_checks: 0,
      standard_count: 0,
      redirect_count: 0,
      failed_count: 0,
      success_rate: 0,
      standard_rate: 0,
      redirect_rate: 0,
      failed_rate: 0
    })

    let searchTimeout = null

    const loadResults = async () => {
      loading.value = true
      try {
        const params = {
          page: currentPage.value,
          per_page: pageSize.value
        }

        if (statusFilter.value) {
          params.status = statusFilter.value
        }

        if (dateRange.value && dateRange.value.length === 2) {
          params.start_date = dateRange.value[0].toISOString()
          params.end_date = dateRange.value[1].toISOString()
        }

        if (searchKeyword.value) {
          params.search = searchKeyword.value
        }

        if (taskId.value) {
          params.task_id = taskId.value
        }

        const response = await resultApi.getList(params)
        
        // 只保留必要字段，减少内存占用
        results.value = (response.data.results || []).map(item => ({
          id: item.id,
          website_id: item.website_id,
          website_name: item.website_name,
          website_url: item.website_url,
          status: item.status,
          final_url: item.final_url,
          response_time: item.response_time,
          http_status_code: item.http_status_code,
          detected_at: item.detected_at,
          error_message: item.error_message?.substring(0, 100) || '' // 截断错误信息
        }))
        
        total.value = response.data.pagination?.total || 0
        
        // 仅在首次加载或手动刷新时加载统计信息
        if (currentPage.value === 1 || params.force_refresh) {
          await loadStats()
        }
      } catch (error) {
        console.error('加载检测结果失败:', error)
        ElMessage.error('加载数据失败')
      } finally {
        loading.value = false
      }
    }

    const loadStats = async () => {
      try {
        const response = await resultApi.getStats()
        Object.assign(stats, response.data.overview)
      } catch (error) {
        console.error('加载统计信息失败:', error)
      }
    }

    const debouncedSearch = () => {
      if (searchTimeout) {
        clearTimeout(searchTimeout)
      }
      // 增加防抖时间，减少频繁请求
      searchTimeout = setTimeout(() => {
        currentPage.value = 1
        loadResults()
      }, 800)
    }

    const exportResults = async () => {
      try {
        const params = { format: 'excel' }

        if (statusFilter.value) {
          params.status = statusFilter.value
        }

        if (dateRange.value && dateRange.value.length === 2) {
          params.start_date = dateRange.value[0].toISOString()
          params.end_date = dateRange.value[1].toISOString()
        }

        if (searchKeyword.value) {
          params.search = searchKeyword.value
        }

        if (taskId.value) {
          params.task_id = taskId.value
        }

        // 第一步：调用导出API生成文件
        const response = await resultApi.export(params)
        
        if (response.code === 200 && response.data && response.data.download_url) {
          // 第二步：使用返回的下载URL下载文件
          const downloadUrl = `http://localhost:5001${response.data.download_url}`
          const link = document.createElement('a')
          link.href = downloadUrl
          link.download = response.data.download_url.split('/').pop() // 获取文件名
          document.body.appendChild(link)
          link.click()
          document.body.removeChild(link)
          
          ElMessage.success(`导出成功，共 ${response.data.record_count} 条记录`)
        } else {
          throw new Error(response.message || '导出失败')
        }
      } catch (error) {
        console.error('导出失败:', error)
        ElMessage.error('导出失败: ' + (error.message || error))
      }
    }

    const handleSizeChange = (size) => {
      pageSize.value = size
      currentPage.value = 1
      loadResults()
    }

    const handleCurrentChange = (page) => {
      currentPage.value = page
      loadResults()
    }

    // 状态相关方法
    const getStatusText = (status) => {
      const statusMap = {
        'standard': '正常访问',
        'redirect': '跳转访问',
        'failed': '无法访问'
      }
      return statusMap[status] || '未知'
    }

    const getStatusType = (status) => {
      const typeMap = {
        'standard': 'success',
        'redirect': 'warning',
        'failed': 'danger'
      }
      return typeMap[status] || 'info'
    }

    const getStatusTagType = (status) => {
      return getStatusType(status)
    }

    const getResponseTimeType = (time) => {
      if (time < 1000) return 'success'
      if (time < 3000) return 'warning'
      return 'danger'
    }

    const getHttpStatusType = (code) => {
      if (code >= 200 && code < 300) return 'success'
      if (code >= 300 && code < 400) return 'warning'
      return 'danger'
    }



    const formatDate = (dateString) => {
      if (!dateString) return '-'
      const date = new Date(dateString)
      return date.toLocaleString('zh-CN')
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

    // 清除数据确认弹窗
    const clearDataWithConfirm = () => {
      ElMessageBox.confirm(
        '确定要清除所有检测数据吗？此操作将删除数据库中的所有检测记录且不可恢复。',
        '清除数据确认',
        {
          confirmButtonText: '确定清除',
          cancelButtonText: '取消',
          type: 'warning',
          dangerouslyUseHTMLString: false
        }
      ).then(() => {
        clearData()
      }).catch(() => {
        ElMessage.info('已取消清除操作')
      })
    }

    // 清除检测数据
    const clearData = async () => {
      try {
        loading.value = true
        
        // 调用清除数据API，清除所有检测数据
        const response = await resultApi.clearAllData()
        
        if (response.success) {
          ElMessage.success(`清除成功，已删除${response.data.deleted_count}条检测记录`)
          // 重新加载数据
          await loadResults()
        } else {
          throw new Error(response.message || '清除数据失败')
        }
      } catch (error) {
        console.error('清除数据失败:', error)
        ElMessage.error('清除数据失败: ' + (error.message || '未知错误'))
      } finally {
        loading.value = false
      }
    }

    // 监听路由参数变化
    watch(() => route.query, (newQuery) => {
      taskId.value = newQuery.task_id || null
      taskName.value = newQuery.task_name || ''
      currentPage.value = 1
      loadResults()
    }, { immediate: true })

    onMounted(() => {
      // 初始化时已通过watch处理路由参数
    })

    // 组件卸载时清理数据
    onUnmounted(() => {
      // 清理定时器
      if (searchTimeout) {
        clearTimeout(searchTimeout)
        searchTimeout = null
      }
      
      // 清理数据
      results.value.length = 0
      Object.assign(stats, {
        total_websites: 0,
        total_checks: 0,
        standard_count: 0,
        redirect_count: 0,
        failed_count: 0,
        success_rate: 0,
        standard_rate: 0,
        redirect_rate: 0,
        failed_rate: 0
      })
    })

    return {
      loading,
      results,
      total,
      currentPage,
      pageSize,
      statusFilter,
      dateRange,
      searchKeyword,
      taskId,
      taskName,
      stats,
      loadResults,
      exportResults,
      clearDataWithConfirm,
      handleSizeChange,
      handleCurrentChange,
      debouncedSearch,
      getStatusText,
      getStatusType,
      getStatusTagType,
      getResponseTimeType,
      getHttpStatusType,
      formatDate,
      getTimeAgo
    }
  }
}
</script>

<style scoped>
/* Claude网站风格样式 */
.results-page {
  padding: 24px;
  background: #fafafa;
  min-height: calc(100vh - 100px);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

/* 页面头部 - Claude风格 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px 24px;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.page-header h2 {
  margin: 0;
  color: #111827;
  font-size: 20px;
  font-weight: 600;
  letter-spacing: -0.025em;
}

.task-tag {
  font-size: 14px;
  font-weight: 600;
  background: #fef3e2;
  color: #d97706;
  border: 1px solid #f3d08a;
}

.actions {
  display: flex;
  gap: 12px;
}

.actions .el-button[type="success"] {
  background: #f0fdf4;
  color: #16a34a;
  border: 1px solid #86efac;
  font-weight: 500;
  border-radius: 8px;
  transition: all 0.15s ease;
}

.actions .el-button[type="success"]:hover {
  background: #dcfce7;
  border-color: #4ade80;
  transform: translateY(-1px);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.actions .el-button[type="primary"] {
  background: #d97706;
  border-color: #d97706;
  font-weight: 500;
  border-radius: 8px;
  transition: all 0.15s ease;
}

.actions .el-button[type="primary"]:hover {
  background: #b45309;
  border-color: #b45309;
  transform: translateY(-1px);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

/* 统计面板 - Claude风格 */
.stats-panel {
  margin-bottom: 24px;
}

.stat-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  overflow: hidden;
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
  padding: 20px;
}

.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: white;
}

.success-card .stat-icon {
  background: linear-gradient(135deg, #10b981, #059669);
}

.warning-card .stat-icon {
  background: linear-gradient(135deg, #f59e0b, #d97706);
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
  margin: 4px 0;
}

.stat-percent {
  font-size: 12px;
  color: #9ca3af;
  font-weight: 500;
}

/* 筛选卡片 - Claude风格 */
.filter-card {
  margin-bottom: 24px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #ffffff;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
}

.filter-section {
  padding: 20px;
}

.filter-summary {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.filter-summary .el-tag {
  background: #fef3e2;
  color: #d97706;
  border: 1px solid #f3d08a;
  font-weight: 500;
}

/* 表格相关样式 - Claude风格 */
.table-card {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #ffffff;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.results-table {
  margin-bottom: 0;
  border-radius: 12px;
  overflow: hidden;
}

.results-table .el-table__header {
  background: #f8fafc;
}

.results-table .el-table__header-wrapper th {
  background: #f8fafc;
  color: #374151;
  font-weight: 600;
  font-size: 13px;
  border-bottom: 1px solid #e5e7eb;
}

.results-table .el-table__body tr:hover > td {
  background-color: #f9fafb;
}

.results-table .el-table__body tr > td {
  border-bottom: 1px solid #f3f4f6;
  color: #374151;
  font-size: 14px;
}

/* 状态标签样式 */
.status-tag-large {
  padding: 8px 12px;
  font-size: 13px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
  border-radius: 8px;
}

.status-icon {
  font-size: 16px;
}

/* 响应时间样式 */
.response-time {
  font-weight: 600;
}

.response-time .el-tag {
  font-weight: 500;
  border-radius: 6px;
}

/* 重定向相关样式 */
.redirect-tag {
  margin-left: 8px;
  background: #fef3e2;
  color: #d97706;
  border: 1px solid #f3d08a;
  font-weight: 500;
}

.no-redirect {
  color: #9ca3af;
  font-style: italic;
  font-size: 13px;
}

/* 错误信息样式 */
.error-message {
  color: #ef4444;
  font-size: 12px;
  font-weight: 500;
}

.no-error {
  color: #10b981;
  font-style: italic;
  font-size: 13px;
  font-weight: 500;
}

.no-data {
  color: #9ca3af;
  font-style: italic;
  font-size: 13px;
}

/* 时间显示样式 */
.check-time {
  text-align: center;
}

.check-time > div {
  font-size: 14px;
  color: #111827;
  font-weight: 500;
  line-height: 1.2;
}

.time-ago {
  color: #6b7280;
  font-size: 12px;
  margin-top: 2px;
}

/* 分页样式 */
.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 24px;
  padding: 20px 0;
}

.pagination-container .el-pagination {
  --el-pagination-bg-color: #ffffff;
  --el-pagination-text-color: #374151;
  --el-pagination-border-radius: 8px;
}

.pagination-container .el-pagination .btn-next,
.pagination-container .el-pagination .btn-prev {
  border-radius: 8px;
}

.pagination-container .el-pagination .el-pager li {
  border-radius: 8px;
  margin: 0 2px;
}

/* 链接样式 */
.results-table .el-link {
  font-weight: 500;
  transition: color 0.15s ease;
}

.results-table .el-link[type="primary"] {
  color: #3b82f6;
}

.results-table .el-link[type="primary"]:hover {
  color: #2563eb;
}

.results-table .el-link[type="warning"] {
  color: #f59e0b;
}

.results-table .el-link[type="warning"]:hover {
  color: #d97706;
}

/* 输入框和选择器样式 */
.filter-section .el-input__wrapper {
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  transition: all 0.15s ease;
}

.filter-section .el-input__wrapper:hover {
  border-color: #d1d5db;
}

.filter-section .el-input__wrapper.is-focus {
  border-color: #d97706;
  box-shadow: 0 0 0 3px rgba(217, 119, 6, 0.1);
}

.filter-section .el-select .el-input__wrapper {
  border-radius: 8px;
}

.filter-section .el-date-editor {
  border-radius: 8px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .results-page {
    padding: 16px;
  }
  
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
    padding: 16px;
  }
  
  .header-left {
    width: 100%;
    justify-content: space-between;
  }
  
  .actions {
    width: 100%;
    justify-content: flex-start;
  }
  
  .filter-section {
    padding: 16px;
  }
  
  .filter-section .el-row {
    flex-direction: column;
    gap: 12px;
  }
  
  .filter-section .el-col {
    width: 100%;
  }
  
  .status-tag-large {
    flex-direction: column;
    gap: 4px;
    padding: 6px 8px;
    font-size: 12px;
  }
}
</style> 