<template>
  <div class="tasks-page">
    <div class="page-header">
      <h2>任务管理</h2>
      <el-button type="primary" @click="showCreateDialog">
        <el-icon><Plus /></el-icon>
        创建任务
      </el-button>
    </div>

    <el-card class="table-card" shadow="never">
      <el-table :data="tasks" v-loading="loading" stripe border style="width: 100%">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="任务名称" width="200" show-overflow-tooltip />
      <el-table-column prop="interval_hours" label="检测间隔" width="100" align="center">
        <template #default="{ row }">
          {{ row.interval_hours }}小时
        </template>
      </el-table-column>
      <el-table-column prop="is_active" label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
            {{ row.is_active ? '运行中' : '已停止' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" min-width="360">
        <template #default="{ row }">
          <div class="action-buttons">
            <el-button 
              size="small" 
              type="info"
              @click="viewResults(row)"
            >
              <el-icon><View /></el-icon>
              结果
            </el-button>
            <el-button 
              size="small" 
              type="warning"
              @click="viewStatusChanges(row)"
            >
              <el-icon><TrendCharts /></el-icon>
              变化
            </el-button>
            <el-button
              size="small"
              :type="row.is_active ? 'warning' : 'success'"
              @click="toggleTask(row)"
            >
              <el-icon v-if="row.is_active"><VideoPause /></el-icon>
              <el-icon v-else><VideoPlay /></el-icon>
              {{ row.is_active ? '停止' : '启动' }}
            </el-button>
            <el-button
              size="small"
              type="primary"
              @click="editTask(row)"
            >
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button
              size="small"
              type="danger"
              @click="deleteTask(row)"
            >
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>
    </el-card>

    <!-- 创建/编辑任务对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEditing ? '编辑检测任务' : '创建检测任务'" width="600px">
      <el-form :model="form" label-width="120px">
        <el-form-item label="任务名称">
          <el-input v-model="form.name" placeholder="请输入任务名称" />
        </el-form-item>
        <el-form-item label="任务描述">
          <el-input v-model="form.description" type="textarea" placeholder="请输入任务描述(可选)" />
        </el-form-item>
        <el-form-item label="检测间隔(小时)">
          <el-input-number v-model="form.interval_hours" :min="1" :max="168" />
        </el-form-item>
        <el-form-item label="选择分组">
          <el-checkbox-group v-model="form.group_ids">
            <el-checkbox
              v-for="group in groups"
              :key="group.id"
              :label="group.id"
            >
              <span :style="{ color: group.color }">{{ group.name }}</span>
              <el-tag size="small" type="info" style="margin-left: 8px;">
                {{ group.website_count }}个网站
              </el-tag>
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, View, VideoPlay, VideoPause, TrendCharts } from '@element-plus/icons-vue'
import { taskApi, groupApi } from '../utils/api'
import { useRouter } from 'vue-router'

export default {
  name: 'Tasks',
  components: { Plus, Edit, Delete, View, VideoPlay, VideoPause, TrendCharts },
  setup() {
    const router = useRouter()
    const loading = ref(false)
    const tasks = ref([])
    const groups = ref([])
    const dialogVisible = ref(false)
    const isEditing = ref(false)
    const editingTaskId = ref(null)
    
    const form = reactive({
      name: '',
      description: '',
      interval_hours: 6,
      group_ids: []
    })

    const loadTasks = async () => {
      loading.value = true
      try {
        const response = await taskApi.getList()
        tasks.value = response.data.tasks
      } catch (error) {
        console.error('加载任务失败:', error)
      } finally {
        loading.value = false
      }
    }

    const loadGroups = async () => {
      try {
        const response = await groupApi.getList({ include_stats: true })
        groups.value = response.data.groups
      } catch (error) {
        console.error('加载分组失败:', error)
      }
    }

    const resetForm = () => {
      form.name = ''
      form.description = ''
      form.interval_hours = 6
      form.group_ids = []
    }

    const showCreateDialog = () => {
      isEditing.value = false
      editingTaskId.value = null
      resetForm()
      dialogVisible.value = true
      loadGroups()
    }

    const editTask = async (task) => {
      try {
        // 获取任务详情
        const response = await taskApi.getDetail(task.id)
        const taskDetail = response.data
        
        // 填充表单
        form.name = taskDetail.name
        form.description = taskDetail.description || ''
        form.interval_hours = taskDetail.interval_minutes ? Math.round(taskDetail.interval_minutes / 60) : 6
        form.group_ids = taskDetail.groups ? taskDetail.groups.map(g => g.id) : []
        
        isEditing.value = true
        editingTaskId.value = task.id
        dialogVisible.value = true
        await loadGroups()
      } catch (error) {
        console.error('获取任务详情失败:', error)
        ElMessage.error('获取任务详情失败')
      }
    }

    const deleteTask = async (task) => {
      try {
        await ElMessageBox.confirm(
          `确定要删除任务 "${task.name}" 吗？删除后将无法恢复！`,
          '确认删除',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning',
          }
        )
        
        await taskApi.delete(task.id)
        ElMessage.success('删除任务成功')
        await loadTasks()
      } catch (error) {
        if (error !== 'cancel') {
          console.error('删除任务失败:', error)
          ElMessage.error('删除任务失败')
        }
      }
    }

    const submitForm = async () => {
      try {
        // 将小时转换为分钟
        const formData = {
          ...form,
          interval_minutes: form.interval_hours * 60
        }
        delete formData.interval_hours
        
        if (isEditing.value) {
          await taskApi.update(editingTaskId.value, formData)
          ElMessage.success('更新任务成功')
        } else {
          await taskApi.create(formData)
          ElMessage.success('任务创建成功')
        }
        dialogVisible.value = false
        await loadTasks()
      } catch (error) {
        console.error(isEditing.value ? '更新任务失败:' : '创建任务失败:', error)
        ElMessage.error(isEditing.value ? '更新任务失败' : '创建任务失败')
      }
    }

    const toggleTask = async (task) => {
      try {
        if (task.is_active) {
          await taskApi.stop(task.id)
        } else {
          await taskApi.schedule(task.id)
        }
        ElMessage.success('操作成功')
        await loadTasks()
      } catch (error) {
        console.error('操作失败:', error)
        ElMessage.error('操作失败: ' + (error.response?.data?.message || error.message))
      }
    }

    const viewResults = (task) => {
      // 跳转到结果页面，传递任务ID参数
      router.push({
        name: 'Results',
        query: {
          task_id: task.id,
          task_name: task.name
        }
      })
    }

    const viewStatusChanges = (task) => {
      // 跳转到状态变化页面，传递任务ID参数
      router.push({
        name: 'StatusChanges',
        query: {
          task_id: task.id,
          task_name: task.name
        }
      })
    }

    const formatDate = (dateString) => {
      if (!dateString) return ''
      return new Date(dateString).toLocaleString('zh-CN')
    }

    onMounted(() => {
      loadTasks()
    })

    return {
      loading,
      tasks,
      groups,
      dialogVisible,
      isEditing,
      form,
      loadTasks,
      showCreateDialog,
      editTask,
      deleteTask,
      submitForm,
      toggleTask,
      viewResults,
      viewStatusChanges,
      formatDate
    }
  }
}
</script>

<style scoped>
/* Claude网站风格样式 */
.tasks-page {
  padding: 24px;
  min-height: calc(100vh - 100px);
  background: #fafafa;
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

.page-header h2 {
  margin: 0;
  color: #111827;
  font-size: 20px;
  font-weight: 600;
  letter-spacing: -0.025em;
}

/* 主按钮样式 - Claude橙色主题 */
.page-header .el-button[type="primary"] {
  background: #d97706;
  border-color: #d97706;
  font-weight: 500;
  border-radius: 8px;
  transition: all 0.15s ease;
  font-size: 14px;
}

.page-header .el-button[type="primary"]:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  background: #b45309;
  border-color: #b45309;
}

/* 表格卡片 - Claude风格 */
.table-card {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #ffffff;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

/* 表格样式优化 */
.table-card .el-table {
  border-radius: 12px;
}

.table-card .el-table__header {
  background: #f8fafc;
}

.table-card .el-table__header-wrapper th {
  background: #f8fafc;
  color: #374151;
  font-weight: 600;
  font-size: 13px;
  border-bottom: 1px solid #e5e7eb;
}

.table-card .el-table__body tr:hover > td {
  background-color: #f9fafb;
}

.table-card .el-table__body tr > td {
  border-bottom: 1px solid #f3f4f6;
  color: #374151;
  font-size: 14px;
}

/* 操作按钮容器 */
.action-buttons {
  display: flex;
  gap: 6px;
  flex-wrap: nowrap;
  align-items: center;
  justify-content: flex-start;
  width: 100%;
  overflow-x: auto;
  scrollbar-width: thin;
  scrollbar-color: #d1d5db transparent;
}

.action-buttons::-webkit-scrollbar {
  height: 2px;
}

.action-buttons::-webkit-scrollbar-track {
  background: transparent;
}

.action-buttons::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 2px;
}

.action-buttons::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}

/* 表格内按钮样式 - Claude风格 */
.action-buttons .el-button {
  margin: 0;
  padding: 5px 10px;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
  border-radius: 6px;
  transition: all 0.15s ease;
  line-height: 1;
  flex-shrink: 0;
  min-width: auto;
}

/* 默认按钮样式 */
.action-buttons .el-button:not([type]) {
  background: #f9fafb;
  color: #374151;
  border: 1px solid #e5e7eb;
}

.action-buttons .el-button:not([type]):hover {
  background: #f3f4f6;
  border-color: #d1d5db;
  transform: translateY(-0.5px);
  box-shadow: 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

/* 信息按钮 */
.action-buttons .el-button[type="info"] {
  background: #f0f9ff;
  color: #0369a1;
  border: 1px solid #7dd3fc;
}

.action-buttons .el-button[type="info"]:hover {
  background: #e0f2fe;
  border-color: #38bdf8;
  transform: translateY(-0.5px);
}

/* 警告按钮 */
.action-buttons .el-button[type="warning"] {
  background: #fef3e2;
  color: #d97706;
  border: 1px solid #f3d08a;
}

.action-buttons .el-button[type="warning"]:hover {
  background: #fde68a;
  border-color: #f59e0b;
  transform: translateY(-0.5px);
}

/* 成功按钮 */
.action-buttons .el-button[type="success"] {
  background: #f0fdf4;
  color: #16a34a;
  border: 1px solid #86efac;
}

.action-buttons .el-button[type="success"]:hover {
  background: #dcfce7;
  border-color: #4ade80;
  transform: translateY(-0.5px);
}

/* 主要按钮 */
.action-buttons .el-button[type="primary"] {
  background: #eff6ff;
  color: #2563eb;
  border: 1px solid #93c5fd;
}

.action-buttons .el-button[type="primary"]:hover {
  background: #dbeafe;
  border-color: #60a5fa;
  transform: translateY(-0.5px);
}

/* 危险按钮 */
.action-buttons .el-button[type="danger"] {
  background: #fef2f2;
  color: #dc2626;
  border: 1px solid #fca5a5;
}

.action-buttons .el-button[type="danger"]:hover {
  background: #fee2e2;
  border-color: #f87171;
  transform: translateY(-0.5px);
}

/* 图标样式 */
.action-buttons .el-button .el-icon {
  margin-right: 4px;
  font-size: 12px;
}

/* 状态标签样式 */
.table-card .el-tag {
  font-weight: 500;
  border-radius: 6px;
  font-size: 12px;
}

/* 响应式设计 */
@media (max-width: 1400px) {
  .action-buttons .el-button {
    padding: 4px 8px;
    font-size: 11px;
  }
  
  .action-buttons .el-button .el-icon {
    margin-right: 3px;
    font-size: 11px;
  }
}

@media (max-width: 1200px) {
  .action-buttons .el-button {
    padding: 3px 6px;
    font-size: 10px;
  }
  
  .action-buttons .el-button .el-icon {
    margin-right: 2px;
    font-size: 10px;
  }
}

@media (max-width: 768px) {
  .tasks-page {
    padding: 16px;
  }
  
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
    padding: 16px;
  }
  
  .action-buttons {
    gap: 3px;
    justify-content: space-between;
  }
  
  .action-buttons .el-button {
    padding: 3px 5px;
    font-size: 10px;
    flex: 1;
    text-align: center;
    min-width: 0;
  }
  
  .action-buttons .el-button .el-icon {
    margin-right: 2px;
    font-size: 10px;
  }
}

/* 对话框表单样式 */
.el-dialog .el-form-item__label {
  color: #374151;
  font-weight: 500;
}

.el-dialog .el-input__wrapper {
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.el-dialog .el-input__wrapper:hover {
  border-color: #d1d5db;
}

.el-dialog .el-input__wrapper.is-focus {
  border-color: #d97706;
  box-shadow: 0 0 0 3px rgba(217, 119, 6, 0.1);
}

/* 复选框组样式 */
.el-checkbox-group .el-checkbox {
  margin-bottom: 12px;
  display: block;
}

.el-checkbox-group .el-checkbox__label {
  color: #374151;
  font-weight: 500;
}

.el-checkbox-group .el-tag {
  margin-left: 8px;
  background: #fef3e2;
  color: #d97706;
  border: 1px solid #f3d08a;
}
</style> 