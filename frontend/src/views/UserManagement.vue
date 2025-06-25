<template>
  <div class="user-management">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">用户管理</h1>
        <p class="page-description">管理系统用户账户，包括创建、编辑和删除用户</p>
      </div>
      <div class="header-actions">
        <el-button 
          type="primary" 
          :icon="Plus" 
          @click="showCreateDialog"
          class="create-btn"
        >
          添加用户
        </el-button>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <div class="filter-section">
      <div class="filter-row">
        <el-input
          v-model="searchQuery"
          placeholder="搜索用户名、姓名或邮箱"
          :prefix-icon="Search"
          clearable
          @input="handleSearch"
          class="search-input"
        />
        <el-select
          v-model="roleFilter"
          placeholder="角色筛选"
          clearable
          @change="handleFilter"
          class="filter-select"
        >
          <el-option label="管理员" value="admin" />
          <el-option label="普通用户" value="user" />
        </el-select>
        <el-select
          v-model="statusFilter"
          placeholder="状态筛选"
          clearable
          @change="handleFilter"
          class="filter-select"
        >
          <el-option label="激活" value="active" />
          <el-option label="停用" value="inactive" />
          <el-option label="锁定" value="locked" />
        </el-select>
      </div>
    </div>

    <!-- 用户列表 -->
    <div class="table-container">
      <el-table
        :data="users"
        v-loading="loading"
        stripe
        class="user-table"
        @sort-change="handleSortChange"
      >
        <el-table-column prop="id" label="ID" width="80" sortable />
        <el-table-column prop="username" label="用户名" min-width="120" sortable />
        <el-table-column prop="real_name" label="姓名" min-width="100" />
        <el-table-column prop="email" label="邮箱" min-width="180" />
        <el-table-column prop="role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : 'primary'" size="small">
              {{ row.role === 'admin' ? '管理员' : '普通用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag 
              :type="getStatusType(row.status)" 
              size="small"
            >
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_login_at" label="最后登录" width="160" sortable>
          <template #default="{ row }">
            {{ formatDateTime(row.last_login_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160" sortable>
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button
                type="primary"
                size="small"
                :icon="Edit"
                @click="showEditDialog(row)"
                link
              >
                编辑
              </el-button>
              <el-button
                type="warning"
                size="small"
                :icon="Key"
                @click="showResetPasswordDialog(row)"
                link
              >
                重置密码
              </el-button>
              <el-button
                v-if="row.id !== userStore.user?.id"
                type="danger"
                size="small"
                :icon="Delete"
                @click="handleDelete(row)"
                link
              >
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.per_page"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handlePageSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </div>

    <!-- 创建/编辑用户对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑用户' : '添加用户'"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="userFormRef"
        :model="userForm"
        :rules="userFormRules"
        label-width="80px"
        class="user-form"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="userForm.username"
            placeholder="请输入用户名"
            :disabled="isEditing"
          />
        </el-form-item>
        <el-form-item label="姓名" prop="real_name">
          <el-input
            v-model="userForm.real_name"
            placeholder="请输入真实姓名"
          />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input
            v-model="userForm.email"
            placeholder="请输入邮箱地址"
            type="email"
          />
        </el-form-item>
        <el-form-item v-if="!isEditing" label="密码" prop="password">
          <el-input
            v-model="userForm.password"
            placeholder="请输入密码"
            type="password"
            show-password
          />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="userForm.role" placeholder="请选择角色" style="width: 100%">
            <el-option label="管理员" value="admin" />
            <el-option label="普通用户" value="user" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="userForm.status" placeholder="请选择状态" style="width: 100%">
            <el-option label="激活" value="active" />
            <el-option label="停用" value="inactive" />
            <el-option label="锁定" value="locked" />
          </el-select>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button 
            type="primary" 
            @click="handleSubmit"
            :loading="submitting"
          >
            {{ isEditing ? '更新' : '创建' }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 重置密码对话框 -->
    <el-dialog
      v-model="resetPasswordVisible"
      title="重置密码"
      width="400px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="resetPasswordFormRef"
        :model="resetPasswordForm"
        :rules="resetPasswordRules"
        label-width="80px"
      >
        <el-form-item label="新密码" prop="password">
          <el-input
            v-model="resetPasswordForm.password"
            placeholder="请输入新密码"
            type="password"
            show-password
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="resetPasswordForm.confirmPassword"
            placeholder="请再次输入新密码"
            type="password"
            show-password
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="resetPasswordVisible = false">取消</el-button>
          <el-button 
            type="primary" 
            @click="handleResetPassword"
            :loading="resettingPassword"
          >
            重置密码
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Edit, Delete, Key } from '@element-plus/icons-vue'
import { userApi } from '@/utils/api'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

// 响应式数据
const loading = ref(false)
const users = ref([])
const searchQuery = ref('')
const roleFilter = ref('')
const statusFilter = ref('')

// 分页数据
const pagination = reactive({
  page: 1,
  per_page: 20,
  total: 0,
  pages: 0
})

// 对话框状态
const dialogVisible = ref(false)
const isEditing = ref(false)
const submitting = ref(false)
const userFormRef = ref(null)

// 重置密码对话框
const resetPasswordVisible = ref(false)
const resettingPassword = ref(false)
const resetPasswordFormRef = ref(null)
const currentResetUser = ref(null)

// 用户表单数据
const userForm = reactive({
  username: '',
  real_name: '',
  email: '',
  password: '',
  role: 'user',
  status: 'active'
})

// 重置密码表单
const resetPasswordForm = reactive({
  password: '',
  confirmPassword: ''
})

// 表单验证规则
const userFormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 50, message: '用户名长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  real_name: [
    { max: 100, message: '姓名长度不能超过 100 个字符', trigger: 'blur' }
  ],
  email: [
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 50, message: '密码长度在 6 到 50 个字符', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ],
  status: [
    { required: true, message: '请选择状态', trigger: 'change' }
  ]
}

const resetPasswordRules = {
  password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 50, message: '密码长度在 6 到 50 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== resetPasswordForm.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 工具方法
const getStatusType = (status) => {
  const statusMap = {
    active: 'success',
    inactive: 'warning',
    locked: 'danger'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status) => {
  const statusMap = {
    active: '激活',
    inactive: '停用',
    locked: '锁定'
  }
  return statusMap[status] || status
}

const formatDateTime = (dateTime) => {
  if (!dateTime) return '-'
  return new Date(dateTime).toLocaleString('zh-CN')
}

// 数据加载
const loadUsers = async () => {
  try {
    loading.value = true
    const params = {
      page: pagination.page,
      per_page: pagination.per_page,
      search: searchQuery.value || undefined,
      role: roleFilter.value || undefined,
      status: statusFilter.value || undefined
    }

    const response = await userApi.getList(params)
    if (response.code === 200) {
      users.value = response.data.users
      pagination.total = response.data.pagination.total
      pagination.pages = response.data.pagination.pages
    } else {
      ElMessage.error(response.message || '获取用户列表失败')
    }
  } catch (error) {
    console.error('加载用户列表失败:', error)
    ElMessage.error('加载用户列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索和筛选
const handleSearch = () => {
  pagination.page = 1
  loadUsers()
}

const handleFilter = () => {
  pagination.page = 1
  loadUsers()
}

const handleSortChange = ({ prop, order }) => {
  // 这里可以实现排序逻辑
  console.log('排序:', prop, order)
}

// 分页处理
const handlePageChange = (page) => {
  pagination.page = page
  loadUsers()
}

const handlePageSizeChange = (size) => {
  pagination.per_page = size
  pagination.page = 1
  loadUsers()
}

// 对话框操作
const showCreateDialog = () => {
  isEditing.value = false
  resetUserForm()
  dialogVisible.value = true
}

const showEditDialog = (user) => {
  isEditing.value = true
  Object.assign(userForm, {
    id: user.id,
    username: user.username,
    real_name: user.real_name || '',
    email: user.email || '',
    password: '',
    role: user.role,
    status: user.status
  })
  dialogVisible.value = true
}

const resetUserForm = () => {
  Object.assign(userForm, {
    id: null,
    username: '',
    real_name: '',
    email: '',
    password: '',
    role: 'user',
    status: 'active'
  })
  if (userFormRef.value) {
    userFormRef.value.clearValidate()
  }
}

// 提交表单
const handleSubmit = async () => {
  if (!userFormRef.value) return

  try {
    await userFormRef.value.validate()
    submitting.value = true

    const formData = { ...userForm }
    delete formData.id

    let response
    if (isEditing.value) {
      response = await userApi.update(userForm.id, formData)
    } else {
      response = await userApi.create(formData)
    }

    if (response.code === 200) {
      ElMessage.success(isEditing.value ? '用户更新成功' : '用户创建成功')
      dialogVisible.value = false
      loadUsers()
    } else {
      ElMessage.error(response.message || '操作失败')
    }
  } catch (error) {
    console.error('提交用户表单失败:', error)
    ElMessage.error('操作失败')
  } finally {
    submitting.value = false
  }
}

// 重置密码
const showResetPasswordDialog = (user) => {
  currentResetUser.value = user
  Object.assign(resetPasswordForm, {
    password: '',
    confirmPassword: ''
  })
  resetPasswordVisible.value = true
}

const handleResetPassword = async () => {
  if (!resetPasswordFormRef.value) return

  try {
    await resetPasswordFormRef.value.validate()
    resettingPassword.value = true

    const response = await userApi.update(currentResetUser.value.id, {
      password: resetPasswordForm.password
    })

    if (response.code === 200) {
      ElMessage.success('密码重置成功')
      resetPasswordVisible.value = false
    } else {
      ElMessage.error(response.message || '密码重置失败')
    }
  } catch (error) {
    console.error('重置密码失败:', error)
    ElMessage.error('密码重置失败')
  } finally {
    resettingPassword.value = false
  }
}

// 删除用户
const handleDelete = async (user) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 "${user.username}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const response = await userApi.delete(user.id)
    if (response.code === 200) {
      ElMessage.success('用户删除成功')
      loadUsers()
    } else {
      ElMessage.error(response.message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除用户失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 页面挂载
onMounted(() => {
  loadUsers()
})
</script>

<style scoped>
.user-management {
  padding: 24px;
  background-color: #ffffff;
  min-height: calc(100vh - 64px);
}

/* 页面头部 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.header-content {
  flex: 1;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 8px 0;
  letter-spacing: -0.025em;
}

.page-description {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
  line-height: 1.5;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.create-btn {
  height: 40px;
  padding: 0 20px;
  font-weight: 500;
}

/* 筛选区域 */
.filter-section {
  margin-bottom: 20px;
  padding: 20px;
  background-color: #f9fafb;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.filter-row {
  display: flex;
  gap: 16px;
  align-items: center;
  flex-wrap: wrap;
}

.search-input {
  width: 300px;
  min-width: 200px;
}

.filter-select {
  width: 150px;
  min-width: 120px;
}

/* 表格容器 */
.table-container {
  background-color: #ffffff;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
}

.user-table {
  width: 100%;
}

.user-table :deep(.el-table__header) {
  background-color: #f9fafb;
}

.user-table :deep(.el-table__header th) {
  background-color: #f9fafb;
  color: #374151;
  font-weight: 600;
  border-bottom: 1px solid #e5e7eb;
}

.user-table :deep(.el-table__row:hover) {
  background-color: #f9fafb;
}

.action-buttons {
  display: flex;
  gap: 8px;
  align-items: center;
}

.action-buttons .el-button {
  padding: 4px 8px;
  font-size: 12px;
}

/* 分页 */
.pagination-container {
  padding: 16px 20px;
  background-color: #ffffff;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: center;
}

/* 对话框样式 */
.user-form {
  padding: 0 8px;
}

.user-form .el-form-item {
  margin-bottom: 20px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .user-management {
    padding: 16px;
  }

  .page-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }

  .filter-row {
    flex-direction: column;
    align-items: stretch;
  }

  .search-input,
  .filter-select {
    width: 100%;
  }

  .user-table {
    font-size: 14px;
  }

  .action-buttons {
    flex-direction: column;
    gap: 4px;
  }
}

@media (max-width: 480px) {
  .user-management {
    padding: 12px;
  }

  .page-title {
    font-size: 20px;
  }

  .filter-section {
    padding: 16px;
  }
}
</style>
