<template>
  <Layout>
    <div class="user-center-container">
      <el-card class="user-info-card">
        <div class="user-avatar">
          <el-avatar :size="120" icon="User" />
        </div>
        <div class="user-details">
          <h2>{{ userStore.user?.username }}</h2>
          <p class="user-email">{{ userStore.user?.email }}</p>
          <p class="join-date">注册时间：{{ formatDate(userStore.user?.created_at) }}</p>
        </div>
      </el-card>
      
      <el-card title="修改密码">
        <el-form :model="passwordForm" label-width="120px">
          <el-form-item label="当前密码" prop="currentPassword">
            <el-input v-model="passwordForm.currentPassword" type="password" placeholder="请输入当前密码" />
          </el-form-item>
          <el-form-item label="新密码" prop="newPassword">
            <el-input v-model="passwordForm.newPassword" type="password" placeholder="请输入新密码" />
          </el-form-item>
          <el-form-item label="确认新密码" prop="confirmPassword">
            <el-input v-model="passwordForm.confirmPassword" type="password" placeholder="请确认新密码" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="changePassword" :loading="changingPassword">
              {{ changingPassword ? '修改中...' : '修改密码' }}
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
      
      <el-card title="账号统计">
        <el-row :gutter="20">
          <el-col :span="8">
            <div class="stat-item">
              <IconDocument :size="32" color="#409eff" />
              <div class="stat-value">{{ noteCount }}</div>
              <div class="stat-label">笔记数量</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="stat-item">
              <IconMagic :size="32" color="#67c23a" />
              <div class="stat-value">{{ aiUsage }}</div>
              <div class="stat-label">AI使用次数</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="stat-item">
              <IconClock :size="32" color="#f5a623" />
              <div class="stat-value">{{ formatDays(daysActive) }}</div>
              <div class="stat-label">活跃天数</div>
            </div>
          </el-col>
        </el-row>
      </el-card>
      
      <el-card>
        <el-button type="danger" @click="handleLogout">
          <IconLogout :size="18" />
          退出登录
        </el-button>
      </el-card>
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
import { IconDocument, IconMagic, IconClock, IconLogout } from '@/components/icons'

const router = useRouter()
const userStore = useUserStore()
const noteStore = useNoteStore()

const changingPassword = ref(false)
const noteCount = ref(0)
const aiUsage = ref(0)
const daysActive = ref(0)

const passwordForm = ref({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

onMounted(async () => {
  await loadStats()
})

async function loadStats() {
  try {
    const notes = await noteApi.getNotes()
    noteCount.value = notes.length
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

async function changePassword() {
  if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) return
  
  changingPassword.value = true
  try {
    await userApi.changePassword(passwordForm.value)
    passwordForm.value = {
      currentPassword: '',
      newPassword: '',
      confirmPassword: ''
    }
  } catch (error) {
    console.error('修改密码失败:', error)
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
  padding: 20px 0;
  max-width: 800px;
}

.user-info-card {
  display: flex;
  align-items: center;
  gap: 30px;
  margin-bottom: 20px;
}

.user-avatar {
  flex-shrink: 0;
}

.user-details h2 {
  margin: 0 0 10px 0;
  font-size: 24px;
}

.user-email {
  margin: 0 0 5px 0;
  color: #606266;
}

.join-date {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.stat-item {
  text-align: center;
  padding: 20px;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #409eff;
  margin: 10px 0 5px 0;
}

.stat-label {
  color: #909399;
  font-size: 14px;
}
</style>