<template>
  <div class="websites-page">
    <!-- 页面标题和操作按钮 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h2>网站管理</h2>
          <span class="subtitle">管理和监控您的网站列表</span>
        </div>
        <div class="actions">
          <el-button type="primary" @click="showCreateDialog" size="default">
            <el-icon><Plus /></el-icon>
            添加网站
          </el-button>
          <el-button @click="showBatchCreateDialog" size="default">
            <el-icon><Plus /></el-icon>
            批量添加
          </el-button>
          <el-upload
            :show-file-list="false"
            :before-upload="handleFileImport"
            accept=".xlsx,.xls,.csv"
          >
            <el-button size="default">
              <el-icon><Upload /></el-icon>
              导入文件
            </el-button>
          </el-upload>
        </div>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <el-card class="search-card" shadow="never">
      <div class="search-section">
        <el-row :gutter="16" align="middle">
          <el-col :span="8">
            <el-input
              v-model="searchQuery"
              placeholder="搜索网站名称或网址"
              clearable
              @input="handleSearch"
              size="default"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </el-col>
          <el-col :span="4">
            <el-select v-model="statusFilter" placeholder="筛选状态" clearable @change="loadWebsites" size="default">
              <el-option label="全部状态" value="" />
              <el-option label="启用" value="true" />
              <el-option label="禁用" value="false" />
            </el-select>
          </el-col>
          <el-col :span="4">
            <el-select v-model="groupFilter" placeholder="筛选分组" clearable @change="loadWebsites" size="default">
              <el-option label="全部分组" value="" />
              <el-option label="未分组" value="null" />
              <el-option 
                v-for="group in groups" 
                :key="group.id" 
                :label="group.name" 
                :value="group.id"
              />
            </el-select>
          </el-col>
          <el-col :span="4">
            <el-button @click="loadWebsites" size="default">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </el-col>
          <el-col :span="4">
            <div class="results-summary">
              <el-tag type="info" size="small">共 {{ total }} 个网站</el-tag>
            </div>
          </el-col>
        </el-row>
      </div>
    </el-card>

    <!-- 网站列表表格 -->
    <el-card class="table-card" shadow="never">
      <el-table
        :data="websites"
        v-loading="loading"
        class="websites-table"
        :header-cell-style="{ background: '#f8fafc', color: '#374151', fontWeight: '600' }"
      >
      <el-table-column type="selection" width="55" />
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="网站名称" min-width="150" />
      <el-table-column prop="url" label="网址" min-width="200">
        <template #default="{ row }">
          <a :href="row.url" target="_blank" class="website-link">
            {{ row.url }}
          </a>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="描述" min-width="150" />
      <el-table-column prop="group_name" label="分组" width="120">
        <template #default="{ row }">
          <span v-if="row.group_name">{{ row.group_name }}</span>
          <span v-else class="text-muted">未分组</span>
        </template>
      </el-table-column>
      <el-table-column prop="is_active" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'danger'">
            {{ row.is_active ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button
            size="small"
            @click="editWebsite(row)"
          >
            编辑
          </el-button>
          <el-button
            size="small"
            :type="row.is_active ? 'warning' : 'success'"
            @click="toggleStatus(row)"
          >
            {{ row.is_active ? '禁用' : '启用' }}
          </el-button>
          <el-button
            size="small"
            type="danger"
            @click="deleteWebsite(row)"
          >
            删除
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
  </el-card>

    <!-- 创建/编辑网站对话框 -->
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
        <el-form-item label="网站名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入网站名称" />
        </el-form-item>
        <el-form-item label="网址" prop="url">
          <el-input v-model="form.url" placeholder="请输入网址" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入描述"
          />
        </el-form-item>
        <el-form-item label="分组" prop="group_id">
          <el-select v-model="form.group_id" placeholder="选择分组" clearable>
            <el-option 
              v-for="group in groups" 
              :key="group.id" 
              :label="group.name" 
              :value="group.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>

    <!-- 批量创建对话框 -->
    <el-dialog
      v-model="batchDialogVisible"
      title="批量添加网站"
      width="800px"
    >
      <el-form>
        <el-form-item label="网站列表">
          <el-input
            v-model="batchText"
            type="textarea"
            :rows="10"
            placeholder="请输入网站信息，每行一个，格式：网站名称|网址|描述（描述可选）"
          />
        </el-form-item>
        <el-form-item>
          <div class="batch-help">
            <p>格式说明：</p>
            <p>1. 每行一个网站</p>
            <p>2. 格式：网站名称|网址|描述（描述可选）</p>
            <p>3. 示例：百度|https://www.baidu.com|搜索引擎</p>
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="batchDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitBatchForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Upload, Search, Refresh } from '@element-plus/icons-vue'
import { websiteApi, groupApi } from '../utils/api'

export default {
  name: 'Websites',
  components: {
    Plus,
    Upload,
    Search,
    Refresh
  },
  setup() {
    // 响应式数据
    const loading = ref(false)
    const websites = ref([])
    const total = ref(0)
    const currentPage = ref(1)
    const pageSize = ref(20)
    const searchQuery = ref('')
    const statusFilter = ref('')
    const groupFilter = ref('')
    const groups = ref([])

    // 对话框相关
    const dialogVisible = ref(false)
    const dialogTitle = ref('')
    const batchDialogVisible = ref(false)
    const batchText = ref('')
    const editingId = ref(null)

    // 表单数据
    const form = reactive({
      name: '',
      url: '',
      description: '',
      group_id: null
    })

    // 表单验证规则
    const rules = {
      name: [
        { required: true, message: '请输入网站名称', trigger: 'blur' }
      ],
      url: [
        { required: true, message: '请输入网址', trigger: 'blur' },
        { 
          pattern: /^https?:\/\/.+/, 
          message: '请输入有效的网址', 
          trigger: 'blur' 
        }
      ]
    }

    // 引用
    const formRef = ref(null)

    // 方法
    const loadWebsites = async () => {
      loading.value = true
      try {
        const params = {
          page: currentPage.value,
          per_page: pageSize.value
        }
        
        if (searchQuery.value) {
          params.search = searchQuery.value
        }
        
        if (statusFilter.value !== '') {
          params.is_active = statusFilter.value
        }
        
        if (groupFilter.value !== '') {
          if (groupFilter.value === 'null') {
            params.group_id = ''  // 未分组
          } else {
            params.group_id = groupFilter.value
          }
        }

        const response = await websiteApi.getList(params)
        websites.value = response.data.websites
        total.value = response.data.pagination.total
      } catch (error) {
        console.error('加载网站列表失败:', error)
      } finally {
        loading.value = false
      }
    }

    const loadGroups = async () => {
      try {
        const response = await groupApi.getList()
        groups.value = response.data.groups
      } catch (error) {
        console.error('加载分组列表失败:', error)
      }
    }

    const showCreateDialog = () => {
      dialogTitle.value = '添加网站'
      editingId.value = null
      resetForm()
      dialogVisible.value = true
    }

    const showBatchCreateDialog = () => {
      batchText.value = ''
      batchDialogVisible.value = true
    }

    const editWebsite = (website) => {
      dialogTitle.value = '编辑网站'
      editingId.value = website.id
      form.name = website.name
      form.url = website.url
      form.description = website.description || ''
      form.group_id = website.group_id || null
      dialogVisible.value = true
    }

    const resetForm = () => {
      form.name = ''
      form.url = ''
      form.description = ''
      form.group_id = null
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
              await websiteApi.update(editingId.value, form)
              ElMessage.success('网站更新成功')
            } else {
              await websiteApi.create(form)
              ElMessage.success('网站创建成功')
            }
            
            dialogVisible.value = false
            await loadWebsites()
          } catch (error) {
            console.error('提交失败:', error)
          }
        }
      })
    }

    const submitBatchForm = async () => {
      if (!batchText.value.trim()) {
        ElMessage.warning('请输入网站信息')
        return
      }

      const lines = batchText.value.trim().split('\n')
      const websites = []

      for (const line of lines) {
        const parts = line.split('|')
        if (parts.length >= 2) {
          websites.push({
            name: parts[0].trim(),
            url: parts[1].trim(),
            description: parts[2] ? parts[2].trim() : ''
          })
        }
      }

      if (websites.length === 0) {
        ElMessage.warning('没有有效的网站信息')
        return
      }

      try {
        await websiteApi.batchCreate({ websites })
        ElMessage.success('批量创建成功')
        batchDialogVisible.value = false
        await loadWebsites()
      } catch (error) {
        console.error('批量创建失败:', error)
      }
    }

    const toggleStatus = async (website) => {
      try {
        await websiteApi.toggleStatus(website.id)
        ElMessage.success('状态切换成功')
        await loadWebsites()
      } catch (error) {
        console.error('状态切换失败:', error)
      }
    }

    const deleteWebsite = async (website) => {
      try {
        await ElMessageBox.confirm(
          `确定要删除网站 "${website.name}" 吗？`,
          '确认删除',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )

        await websiteApi.delete(website.id)
        ElMessage.success('删除成功')
        await loadWebsites()
      } catch (error) {
        if (error !== 'cancel') {
          console.error('删除失败:', error)
        }
      }
    }

    const handleFileImport = async (file) => {
      const formData = new FormData()
      formData.append('file', file)

      try {
        await websiteApi.import(formData)
        ElMessage.success('文件导入成功')
        await loadWebsites()
      } catch (error) {
        console.error('文件导入失败:', error)
      }
      
      return false // 阻止默认上传行为
    }

    const handleSearch = () => {
      currentPage.value = 1
      loadWebsites()
    }

    const handleSizeChange = (newSize) => {
      pageSize.value = newSize
      currentPage.value = 1
      loadWebsites()
    }

    const handleCurrentChange = (newPage) => {
      currentPage.value = newPage
      loadWebsites()
    }

    const formatDate = (dateString) => {
      if (!dateString) return ''
      return new Date(dateString).toLocaleString('zh-CN')
    }

    // 生命周期
    onMounted(() => {
      loadWebsites()
      loadGroups()
    })

    return {
      // 数据
      loading,
      websites,
      total,
      currentPage,
      pageSize,
      searchQuery,
      statusFilter,
      groupFilter,
      groups,
      dialogVisible,
      dialogTitle,
      batchDialogVisible,
      batchText,
      form,
      rules,
      formRef,

      // 方法
      loadWebsites,
      loadGroups,
      showCreateDialog,
      showBatchCreateDialog,
      editWebsite,
      submitForm,
      submitBatchForm,
      toggleStatus,
      deleteWebsite,
      handleFileImport,
      handleSearch,
      handleSizeChange,
      handleCurrentChange,
      formatDate
    }
  }
}
</script>

<style scoped>
/* Claude网站风格样式 */
.websites-page {
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

/* 搜索卡片 - Claude风格 */
.search-card {
  margin-bottom: 24px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #ffffff;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
}

.search-section {
  padding: 20px;
}

.results-summary {
  display: flex;
  justify-content: flex-end;
}

/* 表格卡片 - Claude风格 */
.table-card {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #ffffff;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
}

.websites-table {
  border-radius: 12px;
  overflow: hidden;
}

.websites-table .el-table__row {
  transition: all 0.15s ease;
}

.websites-table .el-table__row:hover {
  background-color: #f9fafb;
}

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

.pagination {
  margin-top: 24px;
  display: flex;
  justify-content: center;
  padding: 16px 0;
}

/* 对话框样式 - Claude风格 */
.batch-help {
  background: #f9fafb;
  padding: 20px;
  border-radius: 8px;
  color: #374151;
  font-size: 14px;
  border: 1px solid #e5e7eb;
}

.batch-help p {
  margin: 4px 0;
  line-height: 1.5;
  color: #6b7280;
}

.text-muted {
  color: #9ca3af;
  font-size: 13px;
  font-style: italic;
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

/* 表格内按钮样式 - Claude风格 */
.websites-table .el-button {
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
  transition: all 0.15s ease;
}

.websites-table .el-button:not([type]) {
  background: #f9fafb;
  border-color: #e5e7eb;
  color: #374151;
}

.websites-table .el-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px -1px rgba(0, 0, 0, 0.06), 0 1px 2px -1px rgba(0, 0, 0, 0.06);
}

/* 状态标签样式 - Claude风格 */
.websites-table .el-tag {
  font-weight: 500;
  border-radius: 6px;
  font-size: 12px;
}

/* 表格头部样式 */
.websites-table .el-table__header {
  background: #f8fafc;
}

.websites-table .el-table__header-wrapper th {
  background: #f8fafc;
  color: #374151;
  font-weight: 600;
  font-size: 13px;
  border-bottom: 1px solid #e5e7eb;
}

/* 输入框和选择器样式 */
.search-section .el-input__wrapper {
  border-radius: 8px;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  border: 1px solid #e5e7eb;
}

.search-section .el-input__wrapper:hover {
  border-color: #d1d5db;
}

.search-section .el-select .el-input__wrapper {
  border-radius: 8px;
}

/* 标签样式 */
.results-summary .el-tag {
  background: #fef3e2;
  color: #d97706;
  border: 1px solid #f3d08a;
  font-weight: 500;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .websites-page {
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
  
  .search-section .el-row {
    flex-direction: column;
    gap: 12px;
  }
  
  .search-section .el-col {
    width: 100%;
  }
  
  .search-section {
    padding: 16px;
  }
}

/* 表格样式优化 */
.websites-table .el-table__body tr:hover > td {
  background-color: #f9fafb;
}

.websites-table .el-table__body tr > td {
  border-bottom: 1px solid #f3f4f6;
  color: #374151;
  font-size: 14px;
}

/* 分页样式 */
.pagination .el-pagination {
  --el-pagination-bg-color: #ffffff;
  --el-pagination-text-color: #374151;
  --el-pagination-border-radius: 8px;
}

.pagination .el-pagination .btn-next,
.pagination .el-pagination .btn-prev {
  border-radius: 8px;
}

.pagination .el-pagination .el-pager li {
  border-radius: 8px;
  margin: 0 2px;
}
</style> 