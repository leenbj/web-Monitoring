<template>
  <div class="files-page">
    <div class="page-header">
      <h2>文件管理</h2>
      <div class="header-actions">
        <el-upload
          ref="uploadRef"
          :action="`http://localhost:5001/api/files/upload`"
          :show-file-list="false"
          :on-success="handleUploadSuccess"
          :on-error="handleUploadError"
          :before-upload="beforeUpload"
          accept=".xlsx,.xls,.csv,.txt,.pdf,.png,.jpg,.jpeg,.gif"
        >
          <el-button type="primary">
            <el-icon><Upload /></el-icon>
            上传文件
          </el-button>
        </el-upload>
        <el-button @click="loadFiles">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <el-card class="table-card" shadow="never">
      <el-table :data="files" v-loading="loading" stripe border>
      <el-table-column prop="filename" label="文件名" min-width="200" />
      <el-table-column prop="type" label="类型" width="100">
        <template #default="{ row }">
          <el-tag :type="row.type === 'upload' ? 'success' : 'info'">
            {{ row.type === 'upload' ? '上传文件' : '导出文件' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="size" label="文件大小" width="120">
        <template #default="{ row }">
          {{ formatFileSize(row.size) }}
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <div class="action-buttons">
            <el-button 
              size="small" 
              type="info"
              @click="downloadFile(row)"
            >
              <el-icon><Download /></el-icon>
              下载
            </el-button>
            <el-button 
              size="small" 
              type="danger" 
              @click="deleteFile(row)"
            >
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>
    </el-card>

    <div v-if="files.length === 0 && !loading" class="empty-state">
      <el-empty description="暂无文件" />
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Download, Delete, Upload } from '@element-plus/icons-vue'
import { fileApi } from '../utils/api'

export default {
  name: 'Files',
  components: { Refresh, Download, Delete, Upload },
  setup() {
    const loading = ref(false)
    const files = ref([])

    const loadFiles = async () => {
      loading.value = true
      try {
        const response = await fileApi.getList()
        files.value = response.data.files
      } catch (error) {
        console.error('加载文件失败:', error)
      } finally {
        loading.value = false
      }
    }

    const downloadFile = async (file) => {
      try {
        ElMessage.info('开始下载文件...')
        
        // 直接使用浏览器下载功能
        const downloadUrl = `http://localhost:5001/api/files/download/${encodeURIComponent(file.filename)}`
        const link = document.createElement('a')
        link.href = downloadUrl
        link.download = file.filename
        link.style.display = 'none'
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        
        ElMessage.success('下载成功')
      } catch (error) {
        console.error('下载失败:', error)
        ElMessage.error('下载失败')
      }
    }

    const deleteFile = async (file) => {
      try {
        await ElMessageBox.confirm(
          `确定要删除文件 "${file.filename}" 吗？`,
          '确认删除',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )

        await fileApi.delete(file.filename)
        ElMessage.success('删除成功')
        await loadFiles()
      } catch (error) {
        if (error !== 'cancel') {
          console.error('删除失败:', error)
        }
      }
    }

    const formatFileSize = (bytes) => {
      if (!bytes) return '0 B'
      
      const sizes = ['B', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(1024))
      
      return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
    }

    const formatDate = (dateString) => {
      if (!dateString) return ''
      return new Date(dateString).toLocaleString('zh-CN')
    }

    const beforeUpload = (file) => {
      const maxSize = 100 * 1024 * 1024 // 100MB
      if (file.size > maxSize) {
        ElMessage.error('文件大小不能超过100MB')
        return false
      }
      ElMessage.info('开始上传文件...')
      return true
    }

    const handleUploadSuccess = (response) => {
      if (response.code === 200) {
        ElMessage.success('文件上传成功')
        loadFiles()
      } else {
        ElMessage.error(response.message || '上传失败')
      }
    }

    const handleUploadError = (error) => {
      console.error('上传失败:', error)
      ElMessage.error('文件上传失败')
    }

    onMounted(() => {
      loadFiles()
    })

    return {
      loading,
      files,
      loadFiles,
      downloadFile,
      deleteFile,
      formatFileSize,
      formatDate,
      beforeUpload,
      handleUploadSuccess,
      handleUploadError
    }
  }
}
</script>

<style scoped>
/* Claude网站风格样式 */
.files-page {
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

.page-header h2 {
  margin: 0;
  color: #111827;
  font-size: 20px;
  font-weight: 600;
  letter-spacing: -0.025em;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.header-actions .el-button {
  font-weight: 500;
  border-radius: 8px;
  transition: all 0.15s ease;
  font-size: 14px;
}

.header-actions .el-button[type="primary"] {
  background: #1a1a1a;
  border-color: #1a1a1a;
  color: #ffffff;
}

.header-actions .el-button:not([type="primary"]) {
  background: #f9fafb;
  border-color: #e5e7eb;
  color: #374151;
}

.header-actions .el-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
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
  gap: 8px;
  align-items: center;
  justify-content: flex-start;
}

/* 表格内按钮样式 - Claude风格 */
.action-buttons .el-button {
  margin: 0;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
  border-radius: 6px;
  transition: all 0.15s ease;
  line-height: 1;
}

/* 信息按钮 */
.action-buttons .el-button[type="info"] {
  background: #eff6ff;
  color: #3b82f6;
  border: 1px solid #bfdbfe;
}

.action-buttons .el-button[type="info"]:hover {
  background: #dbeafe;
  border-color: #93c5fd;
  color: #2563eb;
  transform: translateY(-0.5px);
  box-shadow: 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

/* 危险按钮 */
.action-buttons .el-button[type="danger"] {
  background: #fef2f2;
  color: #ef4444;
  border: 1px solid #fecaca;
}

.action-buttons .el-button[type="danger"]:hover {
  background: #fee2e2;
  border-color: #fca5a5;
  color: #dc2626;
  transform: translateY(-0.5px);
  box-shadow: 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

/* 图标样式 */
.action-buttons .el-button .el-icon {
  margin-right: 4px;
  font-size: 12px;
}

/* 状态标签样式 - Claude风格 */
.table-card .el-tag {
  font-weight: 500;
  border-radius: 6px;
  font-size: 12px;
}

.table-card .el-tag[type="success"] {
  background: #ecfdf5;
  color: #10b981;
  border: 1px solid #a7f3d0;
}

.table-card .el-tag[type="info"] {
  background: #eff6ff;
  color: #3b82f6;
  border: 1px solid #bfdbfe;
}

/* 空状态样式 */
.empty-state {
  margin-top: 48px;
  text-align: center;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 48px 24px;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .files-page {
    padding: 16px;
  }
  
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
    padding: 16px;
  }
  
  .header-actions {
    width: 100%;
    justify-content: flex-start;
    flex-wrap: wrap;
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
</style> 