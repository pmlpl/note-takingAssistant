<template>
  <Layout>
    <div class="user-center-container">
      <!-- 用户信息卡片 -->
      <el-card class="user-info-card" shadow="hover">
        <div class="user-header">
          <div class="user-avatar-wrapper">
            <el-upload
              class="avatar-uploader"
              :show-file-list="false"
              :before-upload="beforeAvatarUpload"
              :http-request="handleAvatarUpload"
            >
              <el-avatar :size="100" :src="avatarUrl" icon="User" />
              <div class="avatar-overlay">
                <IconEdit :size="20" color="#fff" />
                <span class="overlay-text">更换</span>
              </div>
            </el-upload>
          </div>
          <div class="user-details">
            <h2 class="username">{{ userStore.user?.username }}</h2>
            <p class="user-email">
              <el-icon><Message /></el-icon>
              {{ userStore.user?.email }}
            </p>
            <p class="join-date">
              <el-icon><Calendar /></el-icon>
              注册于 {{ formatDate(userStore.user?.created_at) }}
            </p>
          </div>
        </div>
      </el-card>
      
      <!-- 统计数据卡片 -->
      <el-card class="stats-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span class="card-title">数据统计</span>
          </div>
        </template>
        <el-row :gutter="20">
          <el-col :xs="24" :sm="8">
            <div class="stat-item stat-notes">
              <div class="stat-icon">
                <IconDocument :size="36" color="#409eff" />
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ noteCount }}</div>
                <div class="stat-label">笔记数量</div>
              </div>
            </div>
          </el-col>
          <el-col :xs="24" :sm="8">
            <div class="stat-item stat-ai">
              <div class="stat-icon">
                <IconMagic :size="36" color="#67c23a" />
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ aiUsage }}</div>
                <div class="stat-label">AI使用次数</div>
              </div>
            </div>
          </el-col>
          <el-col :xs="24" :sm="8">
            <div class="stat-item stat-active">
              <div class="stat-icon">
                <IconClock :size="36" color="#f5a623" />
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ formatDays(daysActive) }}</div>
                <div class="stat-label">活跃天数</div>
              </div>
            </div>
          </el-col>
        </el-row>
      </el-card>
      
      <!-- 修改密码卡片 -->
      <el-card class="password-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span class="card-title">安全设置</span>
          </div>
        </template>
        <el-form :model="passwordForm" label-width="100px" class="password-form">
          <el-form-item label="当前密码">
            <el-input 
              v-model="passwordForm.currentPassword" 
              type="password" 
              placeholder="请输入当前密码"
              show-password
              clearable
            />
          </el-form-item>
          <el-form-item label="新密码">
            <el-input 
              v-model="passwordForm.newPassword" 
              type="password" 
              placeholder="请输入新密码（至少6位）"
              show-password
              clearable
            />
          </el-form-item>
          <el-form-item label="确认密码">
            <el-input 
              v-model="passwordForm.confirmPassword" 
              type="password" 
              placeholder="请再次输入新密码"
              show-password
              clearable
            />
          </el-form-item>
          <el-form-item>
            <el-button 
              type="primary" 
              @click="changePassword" 
              :loading="changingPassword"
              class="submit-btn"
            >
              {{ changingPassword ? '修改中...' : '确认修改' }}
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
      
      <!-- 退出登录按钮 -->
      <div class="logout-section">
        <el-button 
          type="danger" 
          @click="handleLogout"
          size="large"
          class="logout-btn"
        >
          <IconLogout :size="18" />
          退出登录
        </el-button>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore, useNoteStore } from '@/store'
import { userApi } from '@/api/user'
import { noteApi } from '@/api/note'
import Layout from '@/components/Layout.vue'
import { IconDocument, IconMagic, IconClock, IconLogout, IconEdit } from '@/components/icons'
import { ElMessage } from 'element-plus'
import { Message, Calendar } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()
const noteStore = useNoteStore()

const changingPassword = ref(false)
const uploadingAvatar = ref(false)
const noteCount = ref(0)
const aiUsage = ref(0)
const daysActive = ref(0)
const avatarUrl = ref('')

const passwordForm = ref({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

onMounted(async () => {
  await loadUserData()
  await loadStats()
})

async function loadUserData() {
  try {
    // 加载用户信息，包括头像
    const userInfo = await userApi.getUserInfo()
    if (userInfo.avatar_url) {
      // 构建完整的头像URL
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
      avatarUrl.value = baseUrl + userInfo.avatar_url
    } else {
      avatarUrl.value = ''
    }
  } catch (error) {
    console.error('加载用户数据失败:', error)
  }
}

async function loadStats() {
  try {
    const stats = await userApi.getUserStats()
    noteCount.value = stats.note_count || 0
    aiUsage.value = stats.ai_usage || 0
    daysActive.value = stats.days_active || 0
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

// 头像上传前的验证
function beforeAvatarUpload(file) {
  const isImage = file.type.startsWith('image/')
  const isLt5M = file.size / 1024 / 1024 < 5

  if (!isImage) {
    ElMessage.error('只能上传图片文件！')
    return false
  }
  if (!isLt5M) {
    ElMessage.error('图片大小不能超过 5MB！')
    return false
  }
  return true
}

// 处理头像上传
async function handleAvatarUpload(options) {
  const { file } = options
  uploadingAvatar.value = true
  
  try {
    const response = await userApi.uploadAvatar(file)
    console.log('上传响应:', response)
    // 构建完整的头像URL
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    avatarUrl.value = baseUrl + response.avatar_url
    console.log('新头像URL:', avatarUrl.value)
    ElMessage.success('头像上传成功！')
    
    // 更新本地存储的用户信息
    const userInfo = await userApi.getUserInfo()
    userStore.user = userInfo
  } catch (error) {
    console.error('头像上传失败:', error)
    ElMessage.error(error.response?.data?.detail || '头像上传失败')
  } finally {
    uploadingAvatar.value = false
  }
}

async function changePassword() {
  if (!passwordForm.value.currentPassword) {
    ElMessage.warning('请输入当前密码')
    return
  }
  if (!passwordForm.value.newPassword) {
    ElMessage.warning('请输入新密码')
    return
  }
  if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }
  if (passwordForm.value.newPassword.length < 6) {
    ElMessage.warning('密码长度至少为6位')
    return
  }
  
  changingPassword.value = true
  try {
    await userApi.changePassword(passwordForm.value)
    ElMessage.success('密码修改成功！')
    passwordForm.value = {
      currentPassword: '',
      newPassword: '',
      confirmPassword: ''
    }
  } catch (error) {
    console.error('修改密码失败:', error)
    ElMessage.error(error.response?.data?.detail || '修改密码失败')
  } finally {
    changingPassword.value = false
  }
}

function handleLogout() {
  userStore.logout()
  router.push('/login')
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

function formatDays(days) {
  return days > 0 ? `${days}天` : '-'
}
</script>

<style scoped>
.user-center-container {
  padding: 24px;
  max-width: 900px;
  margin: 0 auto;
}

/* 用户信息卡片 */
.user-info-card {
  margin-bottom: 24px;
  border-radius: 12px;
  overflow: hidden;
}

.user-header {
  display: flex;
  align-items: center;
  gap: 32px;
  padding: 8px 0;
}

.user-avatar-wrapper {
  position: relative;
  flex-shrink: 0;
}

.avatar-uploader {
  cursor: pointer;
  display: inline-block;
}

.avatar-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100px;
  height: 100px;
  background: rgba(0, 0, 0, 0.6);
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: all 0.3s ease;
  color: white;
  gap: 4px;
}

.overlay-text {
  font-size: 12px;
  font-weight: 500;
}

.avatar-uploader:hover .avatar-overlay {
  opacity: 1;
  background: rgba(0, 0, 0, 0.7);
}

.user-details {
  flex: 1;
}

.username {
  margin: 0 0 12px 0;
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  line-height: 1.2;
}

.user-email,
.join-date {
  margin: 0 0 8px 0;
  color: #606266;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-email :deep(.el-icon),
.join-date :deep(.el-icon) {
  color: #909399;
  font-size: 16px;
}

.join-date {
  margin: 0;
  color: #909399;
}

/* 卡片通用样式 */
.stats-card,
.password-card {
  margin-bottom: 24px;
  border-radius: 12px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

/* 统计项样式 */
.stat-item {
  display: flex;
  align-items: center;
  padding: 24px 16px;
  border-radius: 8px;
  transition: all 0.3s ease;
  background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
}

.stat-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.stat-notes:hover {
  background: linear-gradient(135deg, #e3f2fd 0%, #ffffff 100%);
}

.stat-ai:hover {
  background: linear-gradient(135deg, #e8f5e9 0%, #ffffff 100%);
}

.stat-active:hover {
  background: linear-gradient(135deg, #fff3e0 0%, #ffffff 100%);
}

.stat-icon {
  flex-shrink: 0;
  margin-right: 16px;
  padding: 12px;
  border-radius: 12px;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 4px;
  line-height: 1;
}

.stat-label {
  color: #909399;
  font-size: 14px;
  font-weight: 500;
}

/* 密码表单样式 */
.password-form {
  max-width: 600px;
}

.password-form :deep(.el-form-item) {
  margin-bottom: 20px;
}

.password-form :deep(.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
}

.submit-btn {
  min-width: 120px;
  border-radius: 8px;
  font-weight: 500;
}

/* 退出登录区域 */
.logout-section {
  display: flex;
  justify-content: center;
  padding: 24px 0;
}

.logout-btn {
  min-width: 160px;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.logout-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(245, 108, 108, 0.3);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .user-center-container {
    padding: 16px;
  }
  
  .user-header {
    flex-direction: column;
    text-align: center;
    gap: 20px;
  }
  
  .username {
    font-size: 24px;
  }
  
  .user-email,
  .join-date {
    justify-content: center;
  }
  
  .stat-item {
    padding: 20px 12px;
  }
  
  .stat-value {
    font-size: 28px;
  }
  
  .password-form {
    max-width: 100%;
  }
}
</style>