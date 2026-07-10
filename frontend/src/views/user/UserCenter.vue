<template>
  <div class="user-center-container">
    <div class="user-center-toolbar">
      <el-button size="small" :loading="profileLoading || statsLoading || llmLoading" @click="reloadAll">
        重新加载
      </el-button>
    </div>

    <UserProfileCard
      ref="profileCardRef"
      :loading="profileLoading"
      :error="profileError"
      @avatar-updated="onAvatarUpdated"
    />

    <UserStatsCard
      :loading="statsLoading"
      :error="statsError"
      :note-count="noteCount"
      :ai-usage="aiUsage"
      :days-active="daysActive"
      @go-notes="goNotes"
      @go-home-ai="goHomeAi"
      @go-history="goHistory"
    />

    <UserLlmSettings
      :loading="llmLoading"
      :error="llmError"
      :status="llmStatus"
      :base-url="llmForm.baseUrl"
      :model="llmForm.model"
      @update:status="(s) => llmStatus = s"
      @save="onLlmSaved"
    />

    <UserAboutCard
      @show-terms="termsDialogVisible = true"
      @show-privacy="privacyDialogVisible = true"
    />

    <UserPasswordForm
      @changed="onPasswordChanged"
    />

    <UserBindingsPanel
      :loading="bindingsLoading"
      :bindings="bindings"
      @nickname-updated="onNicknameUpdated"
      @bindings-changed="loadBindings"
      @reload-user="loadUserData"
    />

    <div class="logout-section">
      <el-button type="danger" @click="handleLogout" size="large" class="logout-btn">
        <IconLogout :size="18" />
        退出登录
      </el-button>
    </div>

    <UserLegalDialogs
      v-model:show-terms="termsDialogVisible"
      v-model:show-privacy="privacyDialogVisible"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store'
import { userApi } from '@/api/user'
import { IconLogout } from '@/components/icons'
import { ElMessage, ElMessageBox } from 'element-plus'
import UserProfileCard from './UserProfileCard.vue'
import UserStatsCard from './UserStatsCard.vue'
import UserLlmSettings from './UserLlmSettings.vue'
import UserAboutCard from './UserAboutCard.vue'
import UserPasswordForm from './UserPasswordForm.vue'
import UserBindingsPanel from './UserBindingsPanel.vue'
import UserLegalDialogs from './UserLegalDialogs.vue'

const router = useRouter()
const userStore = useUserStore()

const profileCardRef = ref(null)
const profileLoading = ref(false)
const statsLoading = ref(false)
const profileError = ref('')
const statsError = ref('')
const noteCount = ref(0)
const aiUsage = ref(0)
const daysActive = ref(0)
const termsDialogVisible = ref(false)
const privacyDialogVisible = ref(false)

const bindingsLoading = ref(false)
const bindings = ref({
  email: null,
  email_verified: false,
  has_password: false,
  github: null
})

const llmLoading = ref(false)
const llmError = ref('')
const llmStatus = ref({ hasStoredApiKey: false, apiKeyLast4: null })
const llmForm = reactive({
  baseUrl: '',
  model: ''
})

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

async function loadUserData() {
  profileLoading.value = true
  profileError.value = ''
  try {
    const userInfo = await userApi.getUserInfo()
    userStore.user = { ...(userStore.user || {}), ...userInfo }
    persistUserToStorage()
    if (profileCardRef.value && userInfo.avatar_url) {
      profileCardRef.value.setAvatarFromPath(userInfo.avatar_url)
    }
  } catch (error) {
    profileError.value = error.response?.data?.detail || error.message || '加载用户信息失败'
    ElMessage.error(profileError.value)
  } finally {
    profileLoading.value = false
  }
}

async function loadBindings() {
  bindingsLoading.value = true
  try {
    const data = await userApi.getBindings()
    bindings.value = data
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '加载绑定信息失败')
  } finally {
    bindingsLoading.value = false
  }
}

async function loadStats() {
  statsLoading.value = true
  statsError.value = ''
  try {
    const stats = await userApi.getUserStats()
    noteCount.value = stats.note_count || 0
    aiUsage.value = stats.ai_usage || 0
    daysActive.value = stats.days_active || 0
  } catch (error) {
    statsError.value = error.response?.data?.detail || error.message || '加载统计数据失败'
    ElMessage.error(statsError.value)
  } finally {
    statsLoading.value = false
  }
}

async function loadLlmSettings() {
  llmLoading.value = true
  llmError.value = ''
  try {
    const s = await userApi.getLLMSettings()
    llmStatus.value = { hasStoredApiKey: !!s.hasStoredApiKey, apiKeyLast4: s.apiKeyLast4 ?? null }
    llmForm.baseUrl = s.baseUrl ?? ''
    llmForm.model = s.model ?? ''
  } catch (error) {
    llmError.value = error.response?.data?.detail || error.message || '加载模型设置失败'
    ElMessage.error(llmError.value)
  } finally {
    llmLoading.value = false
  }
}

async function reloadAll() {
  await Promise.all([loadUserData(), loadStats(), loadLlmSettings(), loadBindings()])
}

onMounted(async () => {
  await reloadAll()
})

function onAvatarUpdated() {
  loadUserData()
}

function onNicknameUpdated() {
  loadUserData()
}

function onLlmSaved() {
  // LLM settings saved, no extra action needed
}

function onPasswordChanged() {
  // Password changed, no extra action needed
}

async function handleLogout() {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '退出',
      cancelButtonText: '取消',
      type: 'warning'
    })
  } catch {
    return
  }
  await userStore.logout()
  await router.replace('/')
}

function goNotes() {
  router.push('/notes')
}

function goHomeAi() {
  router.push('/home')
}

function goHistory() {
  router.push('/notes/history')
}
</script>

<style scoped>
.user-center-container {
  padding: 24px;
  max-width: 900px;
  margin: 0 auto;
}

.user-center-toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 12px;
}

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

@media (max-width: 768px) {
  .user-center-container {
    padding: 16px;
  }
}
</style>
