<template>
  <div class="profile">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">个人信息</h1>
        <p class="page-description">查看和修改您的个人账户信息</p>
      </div>
    </div>

    <div class="profile-content">
      <!-- 基本信息卡片 -->
      <div class="info-card">
        <div class="card-header">
          <h2 class="card-title">基本信息</h2>
          <el-button 
            type="primary" 
            :icon="Edit" 
            @click="showEditDialog"
            size="small"
          >
            编辑信息
          </el-button>
        </div>
        
        <div class="info-content">
          <div class="info-row">
            <label class="info-label">用户名</label>
            <span class="info-value">{{ userInfo.username }}</span>
          </div>
          <div class="info-row">
            <label class="info-label">姓名</label>
            <span class="info-value">{{ userInfo.real_name || '-' }}</span>
          </div>
          <div class="info-row">
            <label class="info-label">邮箱</label>
            <span class="info-value">{{ userInfo.email || '-' }}</span>
          </div>
          <div class="info-row">
            <label class="info-label">角色</label>
            <el-tag :type="userInfo.role === 'admin' ? 'danger' : 'primary'" size="small">
              {{ userInfo.role === 'admin' ? '管理员' : '普通用户' }}
            </el-tag>
          </div>
          <div class="info-row">
            <label class="info-label">状态</label>
            <el-tag :type="getStatusType(userInfo.status)" size="small">
              {{ getStatusText(userInfo.status) }}
            </el-tag>
          </div>
          <div class="info-row">
            <label class="info-label">注册时间</label>
            <span class="info-value">{{ formatDateTime(userInfo.created_at) }}</span>
          </div>
          <div class="info-row">
            <label class="info-label">最后登录</label>
            <span class="info-value">{{ formatDateTime(userInfo.last_login_at) }}</span>
          </div>
        </div>
      </div>

      <!-- 安全设置卡片 -->
      <div class="info-card">
        <div class="card-header">
          <h2 class="card-title">安全设置</h2>
          <el-button 
            type="warning" 
            :icon="Key" 
            @click="showPasswordDialog"
            size="small"
          >
            修改密码
          </el-button>
        </div>
        
        <div class="info-content">
          <div class="info-row">
            <label class="info-label">密码</label>
            <span class="info-value">••••••••</span>
          </div>
          <div class="security-tip">
            <el-icon class="tip-icon"><InfoFilled /></el-icon>
            <span>为了您的账户安全，建议定期更换密码</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 编辑信息对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑个人信息"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="editFormRef"
        :model="editForm"
        :rules="editFormRules"
        label-width="80px"
        class="edit-form"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="editForm.username"
            placeholder="请输入用户名"
            disabled
          />
          <div class="form-tip">用户名不可修改</div>
        </el-form-item>
        <el-form-item label="姓名" prop="real_name">
          <el-input
            v-model="editForm.real_name"
            placeholder="请输入真实姓名"
          />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input
            v-model="editForm.email"
            placeholder="请输入邮箱地址"
            type="email"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button 
            type="primary" 
            @click="handleUpdateInfo"
            :loading="updating"
          >
            保存
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 修改密码对话框 -->
    <el-dialog
      v-model="passwordDialogVisible"
      title="修改密码"
      width="450px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="passwordFormRef"
        :model="passwordForm"
        :rules="passwordFormRules"
        label-width="100px"
        class="password-form"
      >
        <el-form-item label="当前密码" prop="currentPassword">
          <el-input
            v-model="passwordForm.currentPassword"
            placeholder="请输入当前密码"
            type="password"
            show-password
          />
        </el-form-item>
        <el-form-item label="新密码" prop="newPassword">
          <el-input
            v-model="passwordForm.newPassword"
            placeholder="请输入新密码"
            type="password"
            show-password
          />
        </el-form-item>
        <el-form-item label="确认新密码" prop="confirmPassword">
          <el-input
            v-model="passwordForm.confirmPassword"
            placeholder="请再次输入新密码"
            type="password"
            show-password
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="passwordDialogVisible = false">取消</el-button>
          <el-button 
            type="primary" 
            @click="handleChangePassword"
            :loading="changingPassword"
          >
            修改密码
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Edit, Key, InfoFilled } from '@element-plus/icons-vue'
import { userApi } from '@/utils/api'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

// 响应式数据
const userInfo = ref({})
const loading = ref(false)

// 编辑信息对话框
const editDialogVisible = ref(false)
const updating = ref(false)
const editFormRef = ref(null)

// 修改密码对话框
const passwordDialogVisible = ref(false)
const changingPassword = ref(false)
const passwordFormRef = ref(null)

// 编辑表单数据
const editForm = reactive({
  username: '',
  real_name: '',
  email: ''
})

// 密码表单数据
const passwordForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// 表单验证规则
const editFormRules = {
  real_name: [
    { max: 100, message: '姓名长度不能超过 100 个字符', trigger: 'blur' }
  ],
  email: [
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ]
}

const passwordFormRules = {
  currentPassword: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 50, message: '密码长度在 6 到 50 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.newPassword) {
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

// 加载用户信息
const loadUserInfo = async () => {
  try {
    loading.value = true
    const response = await userApi.getCurrentUser()
    if (response.code === 200) {
      userInfo.value = response.data
      // 更新store中的用户信息
      userStore.updateUser(response.data)
    } else {
      ElMessage.error(response.message || '获取用户信息失败')
    }
  } catch (error) {
    console.error('加载用户信息失败:', error)
    ElMessage.error('加载用户信息失败')
  } finally {
    loading.value = false
  }
}

// 显示编辑对话框
const showEditDialog = () => {
  Object.assign(editForm, {
    username: userInfo.value.username,
    real_name: userInfo.value.real_name || '',
    email: userInfo.value.email || ''
  })
  editDialogVisible.value = true
}

// 更新个人信息
const handleUpdateInfo = async () => {
  if (!editFormRef.value) return

  try {
    await editFormRef.value.validate()
    updating.value = true

    const response = await userApi.update(userInfo.value.id, {
      real_name: editForm.real_name,
      email: editForm.email
    })

    if (response.code === 200) {
      ElMessage.success('个人信息更新成功')
      editDialogVisible.value = false
      loadUserInfo()
    } else {
      ElMessage.error(response.message || '更新失败')
    }
  } catch (error) {
    console.error('更新个人信息失败:', error)
    ElMessage.error('更新失败')
  } finally {
    updating.value = false
  }
}

// 显示修改密码对话框
const showPasswordDialog = () => {
  Object.assign(passwordForm, {
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  })
  passwordDialogVisible.value = true
}

// 修改密码
const handleChangePassword = async () => {
  if (!passwordFormRef.value) return

  try {
    await passwordFormRef.value.validate()
    changingPassword.value = true

    // 这里需要先验证当前密码，然后更新密码
    // 由于后端API设计，我们直接发送新密码
    const response = await userApi.update(userInfo.value.id, {
      password: passwordForm.newPassword
    })

    if (response.code === 200) {
      ElMessage.success('密码修改成功，请重新登录')
      passwordDialogVisible.value = false
      // 密码修改成功后，建议用户重新登录
      setTimeout(() => {
        userStore.logout()
        window.location.href = '/login'
      }, 1500)
    } else {
      ElMessage.error(response.message || '密码修改失败')
    }
  } catch (error) {
    console.error('修改密码失败:', error)
    ElMessage.error('密码修改失败')
  } finally {
    changingPassword.value = false
  }
}

// 页面挂载
onMounted(() => {
  // 如果store中有用户信息，先使用store中的数据
  if (userStore.user) {
    userInfo.value = userStore.user
  }
  // 然后加载最新的用户信息
  loadUserInfo()
})
</script>

<style scoped>
.profile {
  padding: 24px;
  background-color: #ffffff;
  min-height: calc(100vh - 64px);
}

/* 页面头部 */
.page-header {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.header-content {
  max-width: 800px;
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

/* 内容区域 */
.profile-content {
  max-width: 800px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 信息卡片 */
.info-card {
  background-color: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  background-color: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.info-content {
  padding: 24px;
}

.info-row {
  display: flex;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f3f4f6;
}

.info-row:last-child {
  border-bottom: none;
}

.info-label {
  width: 120px;
  font-weight: 500;
  color: #374151;
  font-size: 14px;
}

.info-value {
  flex: 1;
  color: #1f2937;
  font-size: 14px;
}

.security-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
  padding: 12px;
  background-color: #fef3c7;
  border-radius: 6px;
  font-size: 13px;
  color: #92400e;
}

.tip-icon {
  color: #f59e0b;
}

/* 表单样式 */
.edit-form,
.password-form {
  padding: 0 8px;
}

.edit-form .el-form-item,
.password-form .el-form-item {
  margin-bottom: 20px;
}

.form-tip {
  font-size: 12px;
  color: #6b7280;
  margin-top: 4px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .profile {
    padding: 16px;
  }

  .profile-content {
    max-width: 100%;
  }

  .card-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }

  .info-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }

  .info-label {
    width: auto;
    font-size: 13px;
    color: #6b7280;
  }

  .info-value {
    font-size: 14px;
  }
}

@media (max-width: 480px) {
  .profile {
    padding: 12px;
  }

  .page-title {
    font-size: 20px;
  }

  .info-content {
    padding: 16px;
  }

  .card-header {
    padding: 16px;
  }
}
</style>
