<template>
  <div class="groups-page">
    <!-- 页面标题和操作按钮 -->
    <div class="page-header">
      <h2>分组管理</h2>
      <div class="actions">
        <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>
          添加分组
        </el-button>
      </div>
    </div>

    <!-- 分组列表 -->
    <el-card class="table-card" shadow="never">
      <el-table
      :data="groups"
      v-loading="loading"
      stripe
      border
      style="width: 100%"
    >
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="分组名称" min-width="150">
        <template #default="{ row }">
          <el-tag v-if="row.is_default" type="info" size="small">默认</el-tag>
          {{ row.name }}
        </template>
      </el-table-column>
      <el-table-column prop="description" label="描述" min-width="200" />
      <el-table-column prop="website_count" label="网站数量" width="120">
        <template #default="{ row }">
          <el-tag type="info" size="small">{{ row.website_count }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="280" fixed="right">
        <template #default="{ row }">
          <div class="action-buttons">
            <el-button
              size="small"
              type="primary"
              @click="editGroup(row)"
            >
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button
              size="small"
              type="info"
              @click="viewGroupWebsites(row)"
            >
              <el-icon><View /></el-icon>
              查看网站
            </el-button>
            <el-button
              v-if="!row.is_default"
              size="small"
              type="danger"
              @click="deleteGroup(row)"
            >
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>
    </el-card>

    <!-- 创建/编辑分组对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="500px"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="80px"
      >
        <el-form-item label="分组名称" prop="name">
          <el-input 
            v-model="form.name" 
            :disabled="isEditingDefaultGroup"
            placeholder="请输入分组名称" 
          />
          <div v-if="isEditingDefaultGroup" class="form-tip">默认分组名称不可修改</div>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入描述"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>

    <!-- 分组网站详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      :title="`分组：${selectedGroup?.name} - 网站列表`"
      width="800px"
    >
      <el-table
        :data="groupWebsites"
        v-loading="detailLoading"
        stripe
        border
        style="width: 100%"
      >
        <el-table-column prop="name" label="网站名称" min-width="150" />
        <el-table-column prop="url" label="网址" min-width="200">
          <template #default="{ row }">
            <a :href="row.url" target="_blank" class="website-link">
              {{ row.url }}
            </a>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
      
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, View, Delete } from '@element-plus/icons-vue'
import { groupApi } from '../utils/api'

export default {
  name: 'Groups',
  components: {
    Plus,
    Edit,
    View,
    Delete
  },
  setup() {
    // 响应式数据
    const loading = ref(false)
    const groups = ref([])
    const groupWebsites = ref([])
    const selectedGroup = ref(null)

    // 对话框相关
    const dialogVisible = ref(false)
    const dialogTitle = ref('')
    const detailDialogVisible = ref(false)
    const detailLoading = ref(false)
    const editingId = ref(null)

    // 表单数据
    const form = reactive({
      name: '',
      description: ''
    })

    // 表单验证规则
    const rules = {
      name: [
        { required: true, message: '请输入分组名称', trigger: 'blur' }
      ]
    }

    // 引用
    const formRef = ref(null)

    // 计算属性
    const isEditingDefaultGroup = computed(() => {
      if (!editingId.value) return false
      const group = groups.value.find(g => g.id === editingId.value)
      return group?.is_default || false
    })

    // 方法
    const loadGroups = async () => {
      loading.value = true
      try {
        const response = await groupApi.getList({ include_stats: true })
        groups.value = response.data.groups
      } catch (error) {
        console.error('加载分组列表失败:', error)
      } finally {
        loading.value = false
      }
    }

    const showCreateDialog = () => {
      dialogTitle.value = '添加分组'
      editingId.value = null
      resetForm()
      dialogVisible.value = true
    }

    const editGroup = (group) => {
      dialogTitle.value = group.is_default ? '编辑分组（名称不可修改）' : '编辑分组'
      editingId.value = group.id
      form.name = group.name
      form.description = group.description || ''
      dialogVisible.value = true
    }

    const resetForm = () => {
      form.name = ''
      form.description = ''
      if (formRef.value) {
        formRef.value.resetFields()
      }
    }

    const submitForm = async () => {
      if (!formRef.value) return
      
      await formRef.value.validate(async (valid) => {
        if (valid) {
          try {
            if (editingId.value) {
              await groupApi.update(editingId.value, form)
              ElMessage.success('分组更新成功')
            } else {
              await groupApi.create(form)
              ElMessage.success('分组创建成功')
            }
            
            dialogVisible.value = false
            await loadGroups()
          } catch (error) {
            console.error('提交失败:', error)
          }
        }
      })
    }

    const deleteGroup = async (group) => {
      try {
        await ElMessageBox.confirm(
          `确定要删除分组 "${group.name}" 吗？该分组下的网站将移动到默认分组。`,
          '确认删除',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )

        await groupApi.delete(group.id)
        ElMessage.success('删除成功')
        await loadGroups()
      } catch (error) {
        if (error !== 'cancel') {
          console.error('删除失败:', error)
        }
      }
    }

    const viewGroupWebsites = async (group) => {
      selectedGroup.value = group
      detailLoading.value = true
      detailDialogVisible.value = true
      
      try {
        const response = await groupApi.getDetail(group.id)
        groupWebsites.value = response.data.websites || []
      } catch (error) {
        console.error('加载分组网站失败:', error)
      } finally {
        detailLoading.value = false
      }
    }

    const formatDate = (dateString) => {
      if (!dateString) return ''
      return new Date(dateString).toLocaleString('zh-CN')
    }

    // 生命周期
    onMounted(() => {
      loadGroups()
    })

    return {
      // 数据
      loading,
      groups,
      groupWebsites,
      selectedGroup,
      dialogVisible,
      dialogTitle,
      detailDialogVisible,
      detailLoading,
      form,
      rules,
      formRef,

      // 计算属性
      isEditingDefaultGroup,

      // 方法
      loadGroups,
      showCreateDialog,
      editGroup,
      submitForm,
      deleteGroup,
      viewGroupWebsites,
      formatDate
    }
  }
}
</script>

<style scoped>
/* Claude网站风格样式 */
.groups-page {
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

/* 操作按钮区域 */
.actions {
  display: flex;
  gap: 12px;
}

.actions .el-button[type="primary"] {
  background: #d97706;
  border-color: #d97706;
  font-weight: 500;
  border-radius: 8px;
  transition: all 0.15s ease;
  font-size: 14px;
}

.actions .el-button[type="primary"]:hover {
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



/* 网站链接样式 */
.website-link {
  color: #3b82f6;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.15s ease;
}

.website-link:hover {
  text-decoration: underline;
  color: #2563eb;
}

/* 表单提示样式 */
.form-tip {
  font-size: 12px;
  color: #6b7280;
  margin-top: 6px;
  font-weight: 500;
}

/* 操作按钮组 */
.action-buttons {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  align-items: center;
}

/* 表格内按钮样式 - Claude风格 */
.action-buttons .el-button {
  margin: 0;
  padding: 6px 10px;
  font-size: 12px;
  font-weight: 500;
  border-radius: 6px;
  transition: all 0.15s ease;
  line-height: 1;
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

/* 状态标签样式 */
.table-card .el-tag {
  font-weight: 500;
  border-radius: 6px;
  font-size: 12px;
}

.table-card .el-tag[type="info"] {
  background: #fef3e2;
  color: #d97706;
  border: 1px solid #f3d08a;
}

/* 对话框样式 */
.el-dialog .el-form-item__label {
  color: #374151;
  font-weight: 500;
  font-size: 14px;
}

.el-dialog .el-input__wrapper {
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  transition: all 0.15s ease;
}

.el-dialog .el-input__wrapper:hover {
  border-color: #d1d5db;
}

.el-dialog .el-input__wrapper.is-focus {
  border-color: #d97706;
  box-shadow: 0 0 0 3px rgba(217, 119, 6, 0.1);
}

.el-dialog .el-textarea__inner {
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  font-family: inherit;
}

.el-dialog .el-textarea__inner:hover {
  border-color: #d1d5db;
}

.el-dialog .el-textarea__inner:focus {
  border-color: #d97706;
  box-shadow: 0 0 0 3px rgba(217, 119, 6, 0.1);
}


/* 响应式设计 */
@media (max-width: 768px) {
  .groups-page {
    padding: 16px;
  }
  
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
    padding: 16px;
  }
  
  .actions {
    width: 100%;
    justify-content: flex-start;
  }
  
  .action-buttons {
    flex-direction: column;
    gap: 4px;
    align-items: stretch;
  }
  
  .action-buttons .el-button {
    justify-content: flex-start;
  }
}


/* 默认分组特殊样式 */
.table-card .el-table__body .el-tag[type="info"]:first-child {
  background: #fef3e2;
  color: #d97706;
  border: 1px solid #f3d08a;
  margin-right: 8px;
  font-weight: 600;
}
</style> 