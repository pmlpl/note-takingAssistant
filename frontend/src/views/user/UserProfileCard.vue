<template>
  <el-card class="user-info-card user-card" shadow="hover">
    <template #header>
      <div class="card-header">
        <span class="card-title">个人信息</span>
      </div>
    </template>
    <div v-loading="loading" class="section-fold-panel">
      <el-alert
        v-if="error && !loading"
        type="error"
        :title="error"
        show-icon
        :closable="false"
        class="section-alert"
      />
      <div class="user-header">
        <div v-loading="uploadingAvatar" class="user-avatar-wrapper">
          <el-upload
            class="avatar-uploader"
            :show-file-list="false"
            :before-upload="beforeAvatarUpload"
            :http-request="handleAvatarUpload"
            :disabled="uploadingAvatar"
          >
            <el-avatar :size="100" :src="avatarUrl" icon="User" />
            <div class="avatar-overlay">
              <IconEdit :size="20" color="#fff" />
              <span class="overlay-text">更换</span>
            </div>
          </el-upload>
        </div>
        <div class="user-details">
          <h2 class="username">{{ displayName }}</h2>
          <p class="user-email">
            <el-icon><Message /></el-icon>
            {{ email || '未绑定邮箱' }}
            <el-tag v-if="emailVerified" size="small" type="success" effect="light" style="margin-left: 8px;">已验证</el-tag>
          </p>
          <p class="join-date">
            <el-icon><Calendar /></el-icon>
            注册于 {{ formatDate(createdAt) }}
          </p>
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useUserStore } from '@/store'
import { userApi } from '@/api/user'
import { IconEdit } from '@/components/icons'
import { ElMessage } from 'element-plus'
import { Message, Calendar } from '@element-plus/icons-vue'

defineProps({
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' }
})

const emit = defineEmits(['avatar-updated'])

const userStore = useUserStore()
const uploadingAvatar = ref(false)
const avatarUrl = ref('')

const displayName = computed(() => {
  const u = userStore.user
  if (!u) return ''
  return u.nickname || u.username || (u.email ? u.email.split('@')[0] : '')
})

const email = computed(() => userStore.user?.email || '')
const emailVerified = computed(() => userStore.user?.email_verified || false)
const createdAt = computed(() => userStore.user?.created_at || '')

function buildAvatarUrl(avatarPath) {
  if (!avatarPath) return ''
  if (/^https?:\/\//i.test(avatarPath)) {
    const base = avatarPath.split('?')[0]
    return `${base}?t=${Date.now()}`
  }
  const path = avatarPath.startsWith('/') ? avatarPath : `/${avatarPath}`
  return `${path}?t=${Date.now()}`
}

function persistUserToStorage() {
  if (userStore.user) {
    try {
      localStorage.setItem('user', JSON.stringify(userStore.user))
    } catch {
      /* ignore */
    }
  }
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

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

async function handleAvatarUpload(options) {
  const { file } = options
  uploadingAvatar.value = true

  try {
    const response = await userApi.uploadAvatar(file)
    const path = response.avatar_url
    avatarUrl.value = path ? buildAvatarUrl(path) : ''

    const userInfo = await userApi.getUserInfo()
    userStore.user = { ...(userStore.user || {}), ...userInfo }
    persistUserToStorage()

    ElMessage.success('头像上传成功！')
    emit('avatar-updated')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '头像上传失败')
  } finally {
    uploadingAvatar.value = false
  }
}

function setAvatarFromPath(path) {
  avatarUrl.value = path ? buildAvatarUrl(path) : ''
}

defineExpose({ setAvatarFromPath })
</script>

<style scoped>
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
  min-width: 100px;
  min-height: 100px;
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
  color: var(--el-text-color-primary);
  line-height: 1.2;
}

.user-email,
.join-date {
  margin: 0 0 8px 0;
  color: var(--el-text-color-regular);
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-email :deep(.el-icon),
.join-date :deep(.el-icon) {
  color: var(--el-text-color-secondary);
  font-size: 16px;
}

.join-date {
  margin: 0;
  color: var(--el-text-color-secondary);
}

.user-card :deep(.el-card__body) {
  padding-top: 0;
  padding-bottom: 0;
}

.section-fold-panel {
  overflow: hidden;
  padding: 4px 0 20px;
}

.section-alert {
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

@media (max-width: 768px) {
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
}
</style>
