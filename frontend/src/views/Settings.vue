<template>
  <div class="settings-page">
    <div class="page-header">
      <h2>系统设置</h2>
      <p class="page-description">配置系统参数和邮件通知设置</p>
    </div>

    <!-- 邮件通知设置 -->
    <el-card class="settings-card" shadow="never">
      <template #header>
        <div class="card-header">
          <h3>
            <el-icon><Message /></el-icon>
            邮件通知设置
          </h3>
          <el-switch
            v-model="emailSettings.enabled"
            @change="updateEmailSettings"
            active-text="启用"
            inactive-text="禁用"
          />
        </div>
      </template>

      <div v-if="emailSettings.enabled" class="email-config">
        <!-- SMTP配置 -->
        <el-form :model="emailSettings" label-width="120px" class="email-form">
          <el-divider content-position="left">SMTP服务器配置</el-divider>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="SMTP服务器">
                <el-input v-model="emailSettings.smtp_host" placeholder="例如: smtp.qq.com" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="端口">
                <el-input-number v-model="emailSettings.smtp_port" :min="1" :max="65535" placeholder="465" />
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="发件邮箱">
                <el-input v-model="emailSettings.from_email" placeholder="your@email.com" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="邮箱密码">
                <el-input 
                  v-model="emailSettings.from_password" 
                  type="password" 
                  show-password
                  placeholder="邮箱授权码或密码" 
                />
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item label="发件人名称">
            <el-input v-model="emailSettings.from_name" placeholder="中网网址在线监控" />
          </el-form-item>

          <el-form-item label="使用SSL">
            <el-switch v-model="emailSettings.use_ssl" active-text="是" inactive-text="否" />
          </el-form-item>

          <el-divider content-position="left">收件人配置</el-divider>
          
          <!-- 收件人列表 -->
          <el-form-item label="收件人列表">
            <div class="recipients-section">
              <div v-for="(email, index) in emailSettings.recipients" :key="index" class="recipient-item">
                <el-input 
                  v-model="emailSettings.recipients[index]" 
                  placeholder="收件人邮箱地址"
                  style="flex: 1; margin-right: 10px;"
                />
                <el-button 
                  type="danger" 
                  size="small" 
                  @click="removeRecipient(index)"
                  :disabled="emailSettings.recipients.length <= 1"
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
              <el-button 
                type="primary" 
                size="small" 
                @click="addRecipient"
                style="margin-top: 10px;"
              >
                <el-icon><Plus /></el-icon>
                添加收件人
              </el-button>
            </div>
          </el-form-item>

          <el-divider content-position="left">通知规则</el-divider>

          <el-form-item label="通知触发条件">
            <el-checkbox-group v-model="emailSettings.notification_types">
              <el-checkbox label="website_failed">网站变为不可访问</el-checkbox>
              <el-checkbox label="website_recovered">网站恢复访问</el-checkbox>
              <el-checkbox label="status_changed">网站状态变化</el-checkbox>
            </el-checkbox-group>
          </el-form-item>

          <el-form-item label="发送频率限制">
            <el-radio-group v-model="emailSettings.frequency_limit">
              <el-radio label="immediate">立即发送</el-radio>
              <el-radio label="hourly">每小时汇总</el-radio>
              <el-radio label="daily">每日汇总</el-radio>
            </el-radio-group>
          </el-form-item>
        </el-form>

        <!-- 操作按钮 -->
        <div class="action-buttons">
          <el-button type="primary" @click="saveEmailSettings" :loading="saving">
            <el-icon><Check /></el-icon>
            保存设置
          </el-button>
          <el-button @click="testEmailConnection" :loading="testing">
            <el-icon><Promotion /></el-icon>
            测试连接
          </el-button>
          <el-button type="info" @click="quickTestConnection" :loading="quickTesting" size="small">
            <el-icon><Lightning /></el-icon>
            快速测试(587)
          </el-button>
          <el-button @click="sendTestEmail" :loading="sendingTest">
            <el-icon><Message /></el-icon>
            发送测试邮件
          </el-button>
          <el-button @click="resetEmailSettings">
            <el-icon><RefreshLeft /></el-icon>
            重置
          </el-button>
        </div>

        <!-- 连接提示 -->
        <div class="connection-tips">
          <el-alert
            title="连接测试说明"
            type="info"
            :closable="false"
            show-icon
          >
            <template #default>
              <div class="tips-content">
                <p><strong>如果连接测试失败，请尝试以下解决方案：</strong></p>
                <ul>
                  <li><strong>腾讯企业邮箱</strong>：推荐使用587端口 + 关闭SSL</li>
                  <li><strong>网络问题</strong>：检查防火墙是否允许SMTP连接</li>
                  <li><strong>认证问题</strong>：确认使用授权码而非登录密码</li>
                  <li><strong>端口问题</strong>：尝试587(STARTTLS)或465(SSL)端口</li>
                </ul>
              </div>
            </template>
          </el-alert>
        </div>
      </div>

      <div v-else class="email-disabled">
        <el-empty description="邮件通知功能已禁用">
          <el-button type="primary" @click="emailSettings.enabled = true">启用邮件通知</el-button>
        </el-empty>
      </div>
    </el-card>

    <!-- 其他系统设置 -->
    <el-card class="settings-card" shadow="never">
      <template #header>
        <h3>
          <el-icon><Tools /></el-icon>
          系统参数
        </h3>
      </template>

      <el-form :model="systemSettings" label-width="120px">
        <el-form-item label="系统名称">
          <el-input v-model="systemSettings.system_name" />
        </el-form-item>
        
        <el-form-item label="数据保留天数">
          <el-input-number 
            v-model="systemSettings.data_retention_days" 
            :min="1" 
            :max="365"
            style="width: 200px;"
          />
          <span class="form-tip">超过此天数的检测记录将被自动清理</span>
        </el-form-item>

        <el-form-item label="默认检测超时">
          <el-input-number 
            v-model="systemSettings.default_timeout" 
            :min="5" 
            :max="300"
            style="width: 200px;"
          />
          <span class="form-tip">秒</span>
        </el-form-item>

        <el-form-item label="默认重试次数">
          <el-input-number 
            v-model="systemSettings.default_retry_times" 
            :min="0" 
            :max="10"
            style="width: 200px;"
          />
        </el-form-item>

        <div class="action-buttons">
          <el-button type="primary" @click="saveSystemSettings" :loading="savingSystem">
            <el-icon><Check /></el-icon>
            保存设置
          </el-button>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Message,
  Delete,
  Plus,
  Check,
  Promotion,
  RefreshLeft,
  Tools,
  Lightning
} from '@element-plus/icons-vue'
import { settingsApi } from '../utils/api'

export default {
  name: 'Settings',
  components: {
    Message,
    Delete,
    Plus,
    Check,
    Promotion,
    RefreshLeft,
    Tools,
    Lightning
  },
  setup() {
    const saving = ref(false)
    const testing = ref(false)
    const quickTesting = ref(false)
    const sendingTest = ref(false)
    const savingSystem = ref(false)

    // 邮件设置
    const emailSettings = reactive({
      enabled: false,
      smtp_host: '',
      smtp_port: 465,
      from_email: '',
      from_password: '',
      from_name: '中网网址在线监控',
      use_ssl: true,
      recipients: [''],
      notification_types: ['website_failed', 'website_recovered'],
      frequency_limit: 'immediate'
    })

    // 系统设置
    const systemSettings = reactive({
      system_name: '中网网址在线监控',
      data_retention_days: 30,
      default_timeout: 30,
      default_retry_times: 3
    })

    // 加载设置
    const loadSettings = async () => {
      try {
        const response = await settingsApi.getEmailSettings()
        if (response.success) {
          Object.assign(emailSettings, response.data)
          // 确保至少有一个收件人
          if (!emailSettings.recipients || emailSettings.recipients.length === 0) {
            emailSettings.recipients = ['']
          }
        }

        const systemResponse = await settingsApi.getSystemSettings()
        if (systemResponse.success) {
          Object.assign(systemSettings, systemResponse.data)
        }
      } catch (error) {
        console.error('加载设置失败:', error)
      }
    }

    // 保存邮件设置
    const saveEmailSettings = async () => {
      try {
        saving.value = true
        
        // 验证必填字段
        if (emailSettings.enabled) {
          if (!emailSettings.smtp_host || !emailSettings.from_email || !emailSettings.from_password) {
            ElMessage.error('请填写完整的SMTP配置信息')
            return
          }
          
          // 验证收件人
          const validRecipients = emailSettings.recipients.filter(email => 
            email && email.includes('@')
          )
          if (validRecipients.length === 0) {
            ElMessage.error('请至少添加一个有效的收件人邮箱')
            return
          }
          emailSettings.recipients = validRecipients
        }

        const response = await settingsApi.saveEmailSettings(emailSettings)
        if (response.success) {
          ElMessage.success('邮件设置保存成功')
        } else {
          // 如果后端返回业务失败，直接使用后端的错误信息
          ElMessage.error(`保存失败: ${response.message || '未知错误'}`)
        }
      } catch (error) {
        // 如果发生网络层或代码异常，捕获并显示
        console.error('保存邮件设置失败:', error)
        ElMessage.error('保存失败: ' + (error.message || '网络或程序异常'))
      } finally {
        saving.value = false
      }
    }

    // 保存系统设置
    const saveSystemSettings = async () => {
      try {
        savingSystem.value = true
        const response = await settingsApi.saveSystemSettings(systemSettings)
        if (response.success) {
          ElMessage.success('系统设置保存成功')
        } else {
          throw new Error(response.message || '保存失败')
        }
      } catch (error) {
        console.error('保存系统设置失败:', error)
        ElMessage.error('保存失败: ' + (error.message || '未知错误'))
      } finally {
        savingSystem.value = false
      }
    }

    // 测试邮箱连接
    const testEmailConnection = async () => {
      try {
        // 验证必填字段
        if (!emailSettings.smtp_host || !emailSettings.from_email || !emailSettings.from_password) {
          ElMessage.warning('请先填写SMTP服务器、发件邮箱和密码')
          return
        }
        
        testing.value = true
        const response = await settingsApi.testEmailConnection(emailSettings)
        
        if (response.success) {
          ElMessage.success('SMTP连接测试成功')
        } else {
          // 从后端响应中获取详细错误信息
          const errorMsg = response.message || '连接测试失败，未返回具体错误'

          // 提供更友好的错误提示和解决建议
          let friendlyMessage = `连接测试失败: ${errorMsg}`
          let suggestions = []

          if (errorMsg.includes('timed out') || errorMsg.includes('超时')) {
            suggestions.push('• 检查网络连接是否正常')
            suggestions.push('• 确认防火墙允许SMTP连接')
            suggestions.push('• 尝试使用587端口并关闭SSL')
          }

          if (errorMsg.includes('Connection refused') || errorMsg.includes('拒绝连接')) {
            suggestions.push('• 检查SMTP服务器地址是否正确')
            suggestions.push('• 确认端口号是否正确')
            suggestions.push('• 联系邮箱服务商确认SMTP服务状态')
          }

          if (errorMsg.includes('认证失败') || errorMsg.includes('authentication')) {
            suggestions.push('• 检查邮箱地址是否正确')
            suggestions.push('• 确认使用的是授权码而非登录密码')
            suggestions.push('• 确认邮箱已开启SMTP服务')
          }

          if (suggestions.length > 0) {
            friendlyMessage += '\n\n建议解决方案:\n' + suggestions.join('\n')
          }

          ElMessage({
            message: friendlyMessage,
            type: 'error',
            duration: 10000, // 10秒显示时间
            showClose: true,
            dangerouslyUseHTMLString: false
          })
        }
      } catch (error) {
        // 处理网络层或拦截器抛出的错误
        const errorMsg = error.message || '发生未知网络错误'
        ElMessage({
          message: `连接测试失败: ${errorMsg}`,
          type: 'error',
          duration: 7000,
          showClose: true,
        })
      } finally {
        testing.value = false
      }
    }

    // 快速测试连接（使用587端口）
    const quickTestConnection = async () => {
      try {
        // 验证必填字段
        if (!emailSettings.smtp_host || !emailSettings.from_email || !emailSettings.from_password) {
          ElMessage.warning('请先填写SMTP服务器、发件邮箱和密码')
          return
        }

        quickTesting.value = true

        // 使用587端口和STARTTLS进行快速测试
        const testConfig = {
          smtp_host: emailSettings.smtp_host,
          smtp_port: 587,
          from_email: emailSettings.from_email,
          from_password: emailSettings.from_password,
          use_ssl: false // 587端口通常使用STARTTLS
        }

        const response = await settingsApi.testEmailConnection(testConfig)

        if (response.success) {
          ElMessage.success('快速测试成功！建议使用587端口配置')
        } else {
          const errorMsg = response.message || '快速测试失败'
          ElMessage({
            message: `快速测试失败: ${errorMsg}`,
            type: 'warning',
            duration: 5000,
            showClose: true,
          })
        }
      } catch (error) {
        const errorMsg = error.message || '发生未知网络错误'
        ElMessage({
          message: `快速测试失败: ${errorMsg}`,
          type: 'warning',
          duration: 5000,
          showClose: true,
        })
      } finally {
        quickTesting.value = false
      }
    }

    // 发送测试邮件
    const sendTestEmail = async () => {
      try {
        sendingTest.value = true
        const response = await settingsApi.sendTestEmail()
        if (response.success) {
          ElMessage.success('测试邮件发送成功，请检查收件箱')
        } else {
          throw new Error(response.message || '发送失败')
        }
      } catch (error) {
        console.error('发送测试邮件失败:', error)
        ElMessage.error('发送失败: ' + (error.message || '未知错误'))
      } finally {
        sendingTest.value = false
      }
    }

    // 添加收件人
    const addRecipient = () => {
      emailSettings.recipients.push('')
    }

    // 删除收件人
    const removeRecipient = (index) => {
      if (emailSettings.recipients.length > 1) {
        emailSettings.recipients.splice(index, 1)
      }
    }

    // 重置邮件设置
    const resetEmailSettings = () => {
      ElMessageBox.confirm(
        '确定要重置邮件设置吗？所有配置将被清除。',
        '重置确认',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      ).then(() => {
        Object.assign(emailSettings, {
          enabled: false,
          smtp_host: '',
          smtp_port: 465,
          from_email: '',
          from_password: '',
          from_name: '中网网址在线监控',
          use_ssl: true,
          recipients: [''],
          notification_types: ['website_failed', 'website_recovered'],
          frequency_limit: 'immediate'
        })
        ElMessage.success('邮件设置已重置')
      }).catch(() => {
        // 用户取消
      })
    }

    // 更新邮件设置开关
    const updateEmailSettings = async () => {
      if (!emailSettings.enabled) {
        // 立即保存禁用状态
        await saveEmailSettings()
      }
    }

    onMounted(() => {
      loadSettings()
    })

    return {
      saving,
      testing,
      quickTesting,
      sendingTest,
      savingSystem,
      emailSettings,
      systemSettings,
      saveEmailSettings,
      saveSystemSettings,
      testEmailConnection,
      quickTestConnection,
      sendTestEmail,
      addRecipient,
      removeRecipient,
      resetEmailSettings,
      updateEmailSettings
    }
  }
}
</script>

<style scoped>
.settings-page {
  padding: 24px;
  background: #fafafa;
  min-height: calc(100vh - 100px);
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0 0 8px 0;
  color: #111827;
  font-size: 28px;
  font-weight: 600;
}

.page-description {
  margin: 0;
  color: #6b7280;
  font-size: 14px;
}

.settings-card {
  margin-bottom: 24px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  color: #374151;
  font-size: 18px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.email-config {
  padding: 20px 0;
}

.email-form .el-form-item {
  margin-bottom: 20px;
}

.recipients-section {
  width: 100%;
}

.recipient-item {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.action-buttons {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.connection-tips {
  margin-top: 20px;
}

.tips-content ul {
  margin: 10px 0 0 0;
  padding-left: 20px;
}

.tips-content li {
  margin-bottom: 5px;
  line-height: 1.5;
}

.email-disabled {
  padding: 40px 0;
  text-align: center;
}

.form-tip {
  margin-left: 10px;
  color: #6b7280;
  font-size: 12px;
}

/* 表单样式优化 */
.email-form :deep(.el-form-item__label) {
  color: #374151;
  font-weight: 500;
}

.email-form :deep(.el-input__inner) {
  border-radius: 6px;
}

.email-form :deep(.el-input-number .el-input__inner) {
  text-align: left;
}

/* 分割线样式 */
:deep(.el-divider--horizontal) {
  margin: 30px 0 20px 0;
}

:deep(.el-divider__text) {
  color: #374151;
  font-weight: 500;
}

/* 复选框组样式 */
:deep(.el-checkbox-group) {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

:deep(.el-checkbox) {
  margin-right: 0;
}

/* 按钮样式 */
.action-buttons .el-button {
  padding: 10px 20px;
  border-radius: 6px;
  font-weight: 500;
}
</style>