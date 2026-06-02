<template>
    <div class="user-center-container">
      <div class="user-center-toolbar">
        <el-button size="small" :loading="profileLoading || statsLoading || llmLoading" @click="reloadAll">
          重新加载
        </el-button>
      </div>

      <!-- 用户信息卡片 -->
      <el-card class="user-info-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span class="card-title">个人信息</span>
          </div>
        </template>
        <div class="section-fold-panel" v-loading="profileLoading">
            <el-alert
              v-if="profileError && !profileLoading"
              type="error"
              :title="profileError"
              show-icon
              :closable="false"
              class="section-alert"
            />
            <div class="user-header">
              <div class="user-avatar-wrapper" v-loading="uploadingAvatar">
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
          </div>
      </el-card>

      <!-- 统计数据卡片 -->
      <el-card class="stats-card" shadow="hover">
        <template #header>
          <div class="card-header card-header--fold">
            <span class="card-title">数据统计</span>
            <el-button
              text
              type="primary"
              class="section-toggle-btn"
              @click="showStatsPanel = !showStatsPanel"
            >
              <el-icon class="section-toggle-icon" :class="{ 'is-open': showStatsPanel }">
                <ArrowDown />
              </el-icon>
              <span>展开</span>
            </el-button>
          </div>
        </template>
        <Transition name="section-fold">
          <div v-show="showStatsPanel" class="section-fold-panel" v-loading="statsLoading">
            <el-alert
              v-if="statsError && !statsLoading"
              type="error"
              :title="statsError"
              show-icon
              :closable="false"
              class="section-alert"
            />
            <el-row :gutter="20">
          <el-col :xs="24" :sm="8">
            <div
              class="stat-item stat-notes stat-item--clickable"
              role="button"
              tabindex="0"
              @click="goNotes"
              @keydown.enter.prevent="goNotes"
            >
              <div class="stat-icon">
                <IconDocument :size="36" color="#409eff" />
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ noteCount }}</div>
                <div class="stat-label">
                  <el-tooltip placement="top" :show-after="300">
                    <template #content>
                      当前账号在系统中的笔记总条数。点击前往「我的笔记」列表。
                    </template>
                    <span class="stat-label-inner">笔记数量</span>
                  </el-tooltip>
                </div>
              </div>
            </div>
          </el-col>
          <el-col :xs="24" :sm="8">
            <div
              class="stat-item stat-ai stat-item--clickable"
              role="button"
              tabindex="0"
              @click="goHomeAi"
              @keydown.enter.prevent="goHomeAi"
            >
              <div class="stat-icon">
                <IconMagic :size="36" color="#67c23a" />
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ aiUsage }}</div>
                <div class="stat-label">
                  <el-tooltip placement="top" :show-after="300">
                    <template #content>
                      AI 生成、摘要、对话等功能的累计调用次数（后端 ai_usage_logs 统计）。点击前往首页 AI 助手。
                    </template>
                    <span class="stat-label-inner">AI使用次数</span>
                  </el-tooltip>
                </div>
              </div>
            </div>
          </el-col>
          <el-col :xs="24" :sm="8">
            <div
              class="stat-item stat-active stat-item--clickable"
              role="button"
              tabindex="0"
              @click="goHistory"
              @keydown.enter.prevent="goHistory"
            >
              <div class="stat-icon">
                <IconClock :size="36" color="#f5a623" />
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ formatDays(daysActive) }}</div>
                <div class="stat-label">
                  <el-tooltip placement="top" :show-after="300">
                    <template #content>
                      您曾创建过笔记的不同日期天数（按笔记创建日去重）。点击前往历史笔记。
                    </template>
                    <span class="stat-label-inner">活跃天数</span>
                  </el-tooltip>
                </div>
              </div>
            </div>
          </el-col>
        </el-row>
          </div>
        </Transition>
      </el-card>

      <!-- AI / BYOK 设置 -->
      <el-card class="llm-card" shadow="hover">
        <template #header>
          <div class="card-header card-header--fold">
            <span class="card-title">AI 模型（自带密钥）</span>
            <el-button
              text
              type="primary"
              class="section-toggle-btn"
              @click="showLlmPanel = !showLlmPanel"
            >
              <el-icon class="section-toggle-icon" :class="{ 'is-open': showLlmPanel }">
                <ArrowDown />
              </el-icon>
              <span>展开</span>
            </el-button>
          </div>
        </template>
        <Transition name="section-fold">
          <div v-show="showLlmPanel" class="section-fold-panel" v-loading="llmLoading">
            <el-alert
              v-if="llmError && !llmLoading"
              type="error"
              :title="llmError"
              show-icon
              :closable="false"
              class="section-alert"
            />
            <el-form :model="llmForm" label-width="128px" class="llm-form">
          <el-form-item label="API 基址">
            <el-input
              v-model="llmForm.baseUrl"
              placeholder="例如 http://10.16.54.177:1234（可省略 /v1，保存时自动补全）"
              clearable
              autocomplete="off"
              @blur="onLlmBaseUrlBlur"
            />
          </el-form-item>
          <el-form-item label="模型标识">
            <el-input
              v-model="llmForm.model"
              placeholder="留空则使用服务端默认"
              clearable
              autocomplete="off"
            />
          </el-form-item>
          <el-form-item label="个人密钥">
            <span v-if="llmStatus.hasStoredApiKey" class="llm-key-status">
              已保存（后四位：{{ llmStatus.apiKeyLast4 || '—' }}）
            </span>
            <span v-else class="llm-key-status llm-key-status--muted">未配置，将使用服务端默认密钥策略</span>
          </el-form-item>
          <el-form-item label="修改 API 密钥">
            <div class="llm-switch-row">
              <el-switch v-model="llmForm.editApiKey" />
              <span class="llm-switch-hint">
                开启后可输入新密钥；若留空并保存，将清除已保存的个人密钥。
              </span>
            </div>
          </el-form-item>
          <el-form-item v-show="llmForm.editApiKey" label="新 API Key">
            <el-input
              v-model="llmForm.apiKey"
              type="password"
              show-password
              autocomplete="new-password"
              placeholder="输入新密钥"
              clearable
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="llmSaving" @click="saveLlmSettings">
              {{ llmSaving ? '保存中…' : '保存设置' }}
            </el-button>
          </el-form-item>
        </el-form>
          </div>
        </Transition>
      </el-card>

      <!-- 关于与本机 -->
      <el-card class="about-card" shadow="hover">
        <template #header>
          <div class="card-header card-header--fold">
            <span class="card-title">关于与本机</span>
            <el-button
              text
              type="primary"
              class="section-toggle-btn"
              @click="showAboutPanel = !showAboutPanel"
            >
              <el-icon class="section-toggle-icon" :class="{ 'is-open': showAboutPanel }">
                <ArrowDown />
              </el-icon>
              <span>展开</span>
            </el-button>
          </div>
        </template>
        <Transition name="section-fold">
          <div v-show="showAboutPanel" class="section-fold-panel">
            <el-descriptions :column="1" border size="small" class="about-descriptions">
              <el-descriptions-item label="用户 ID">{{ aboutUserId }}</el-descriptions-item>
              <el-descriptions-item label="应用名称">{{ aboutDevice.appName }}</el-descriptions-item>
              <el-descriptions-item label="版本号">{{ aboutDevice.appVersion }}</el-descriptions-item>
              <el-descriptions-item label="运行模式">{{ aboutDevice.mode }}</el-descriptions-item>
              <el-descriptions-item label="API 基址（开发）">{{ aboutDevice.apiBase }}</el-descriptions-item>
              <el-descriptions-item label="时区">{{ aboutDevice.tz }}</el-descriptions-item>
              <el-descriptions-item label="界面语言">{{ aboutDevice.lang }}</el-descriptions-item>
              <el-descriptions-item label="屏幕分辨率">{{ aboutDevice.screen }}</el-descriptions-item>
              <el-descriptions-item label="设备像素比">{{ aboutDevice.dpr }}</el-descriptions-item>
              <el-descriptions-item label="浏览器 UA">
                <div class="ua-row">
                  <span class="ua-wrap">{{ aboutDevice.ua }}</span>
                  <el-button size="small" type="primary" plain @click="copyUserAgent">复制</el-button>
                </div>
              </el-descriptions-item>
            </el-descriptions>
            <div class="legal-links">
              <el-link type="primary" underline="never" @click.prevent="termsDialogVisible = true">用户协议</el-link>
              <span class="link-sep">|</span>
              <el-link type="primary" underline="never" @click.prevent="privacyDialogVisible = true">隐私政策</el-link>
            </div>
          </div>
        </Transition>
      </el-card>

      <!-- 安全设置：修改密码（默认折叠） -->
      <el-card class="password-card" shadow="hover">
        <template #header>
          <div class="card-header card-header--fold">
            <span class="card-title">安全设置</span>
            <el-button
              text
              type="primary"
              class="section-toggle-btn"
              @click="showPasswordForm = !showPasswordForm"
            >
              <el-icon class="section-toggle-icon" :class="{ 'is-open': showPasswordForm }">
                <ArrowDown />
              </el-icon>
              <span>展开</span>
            </el-button>
          </div>
        </template>
        <Transition name="section-fold">
          <div v-show="showPasswordForm" class="section-fold-panel">
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
              <el-form-item v-if="passwordForm.newPassword" label="强度">
                <el-progress
                  :percentage="passwordStrength.score"
                  :color="passwordStrength.color"
                  :stroke-width="10"
                  :format="() => (passwordStrength.score ? `${passwordStrength.label} · ${passwordStrength.score}%` : '')"
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
          </div>
        </Transition>
      </el-card>

      <!-- 退出登录按钮 -->
      <div class="logout-section">
        <el-button type="danger" @click="handleLogout" size="large" class="logout-btn">
          <IconLogout :size="18" />
          退出登录
        </el-button>
      </div>

      <el-dialog
        v-model="termsDialogVisible"
        title="用户协议"
        width="min(92vw, 560px)"
        class="legal-dialog"
        destroy-on-close
      >
        <p class="legal-doc-note">以下为通用模板，正式对外服务前请由部署方替换为定稿文本。</p>
        <div class="legal-doc-body">
          <section v-for="(sec, idx) in TERMS_SECTIONS" :key="'term-' + idx" class="legal-doc-section">
            <h4 class="legal-doc-h">{{ sec.h }}</h4>
            <p v-for="(para, pidx) in sec.p" :key="'term-' + idx + '-p-' + pidx" class="legal-doc-p">{{ para }}</p>
          </section>
        </div>
      </el-dialog>

      <el-dialog
        v-model="privacyDialogVisible"
        title="隐私政策"
        width="min(92vw, 560px)"
        class="legal-dialog"
        destroy-on-close
      >
        <p class="legal-doc-note">以下为通用模板，正式对外服务前请由部署方替换为定稿文本。</p>
        <div class="legal-doc-body">
          <section v-for="(sec, idx) in PRIVACY_SECTIONS" :key="'priv-' + idx" class="legal-doc-section">
            <h4 class="legal-doc-h">{{ sec.h }}</h4>
            <p v-for="(para, pidx) in sec.p" :key="'priv-' + idx + '-p-' + pidx" class="legal-doc-p">{{ para }}</p>
          </section>
        </div>
      </el-dialog>
    </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store'
import { userApi } from '@/api/user'
import { IconDocument, IconMagic, IconClock, IconLogout, IconEdit } from '@/components/icons'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Message, Calendar, ArrowDown } from '@element-plus/icons-vue'
import appPkg from '../../../package.json'
import { TERMS_SECTIONS, PRIVACY_SECTIONS } from '@/constants/userCenterLegal'
import { normalizeOpenAiCompatibleBaseUrl } from '@/utils/common'

const router = useRouter()
const userStore = useUserStore()

const changingPassword = ref(false)
const uploadingAvatar = ref(false)
const profileLoading = ref(false)
const statsLoading = ref(false)
const profileError = ref('')
const statsError = ref('')
const noteCount = ref(0)
const aiUsage = ref(0)
const daysActive = ref(0)
const avatarUrl = ref('')
const showStatsPanel = ref(false)
const showLlmPanel = ref(false)
const showPasswordForm = ref(false)
const showAboutPanel = ref(false)
const termsDialogVisible = ref(false)
const privacyDialogVisible = ref(false)

const llmLoading = ref(false)
const llmSaving = ref(false)
const llmError = ref('')
const llmStatus = ref({ hasStoredApiKey: false, apiKeyLast4: null })
const llmForm = ref({
  baseUrl: '',
  model: '',
  apiKey: '',
  editApiKey: false
})

const aboutUserId = computed(() => {
  const id = userStore.user?.id
  return id != null && id !== '' ? String(id) : '—'
})

/** 本机时区：IANA + 中文名称 + 与 UTC 的偏移，避免只显示英文 ID 被误认为「不对」 */
function formatAboutTimeZone() {
  if (typeof Intl === 'undefined') return '-'
  const id = Intl.DateTimeFormat().resolvedOptions().timeZone
  if (!id) return '-'
  try {
    const now = new Date()
    const longCn =
      new Intl.DateTimeFormat('zh-CN', { timeZone: id, timeZoneName: 'long' })
        .formatToParts(now)
        .find((p) => p.type === 'timeZoneName')?.value || ''
    const offset =
      new Intl.DateTimeFormat('en-US', { timeZone: id, timeZoneName: 'shortOffset' })
        .formatToParts(now)
        .find((p) => p.type === 'timeZoneName')?.value || ''
    const ordered = []
    for (const b of [longCn, id, offset]) {
      if (b && !ordered.includes(b)) ordered.push(b)
    }
    return ordered.length ? ordered.join(' · ') : id
  } catch {
    return id
  }
}

function resolveAppDisplayName() {
  const fromEnv = import.meta.env.VITE_APP_DISPLAY_NAME
  if (typeof fromEnv === 'string' && fromEnv.trim()) return fromEnv.trim()
  const dn = appPkg.displayName
  if (typeof dn === 'string' && dn.trim()) return dn.trim()
  return '智能笔记助手'
}

const aboutDevice = computed(() => ({
  appName: resolveAppDisplayName(),
  appVersion: appPkg.version || '-',
  mode: import.meta.env.MODE,
  apiBase: import.meta.env.VITE_API_BASE_URL || '（未设置，开发环境通常走 Vite 代理 /api）',
  ua: typeof navigator !== 'undefined' ? navigator.userAgent : '-',
  lang: typeof navigator !== 'undefined' ? navigator.language : '-',
  tz: formatAboutTimeZone(),
  screen: typeof screen !== 'undefined' ? `${screen.width}×${screen.height}` : '-',
  dpr: typeof window !== 'undefined' ? String(window.devicePixelRatio || 1) : '-'
}))

const passwordForm = ref({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const passwordStrength = computed(() => {
  const p = passwordForm.value.newPassword
  if (!p) {
    return { score: 0, label: '', color: '#909399' }
  }
  let score = 0
  if (p.length >= 6) score += 20
  if (p.length >= 10) score += 15
  if (/[a-z]/.test(p)) score += 15
  if (/[A-Z]/.test(p)) score += 15
  if (/\d/.test(p)) score += 15
  if (/[^a-zA-Z0-9]/.test(p)) score += 20
  score = Math.min(100, score)
  let label = '弱'
  let color = '#f56c6c'
  if (score >= 45) {
    label = '中'
    color = '#e6a23c'
  }
  if (score >= 75) {
    label = '强'
    color = '#67c23a'
  }
  return { score, label, color }
})

async function copyUserAgent() {
  const ua = aboutDevice.value.ua
  if (!ua || ua === '-') {
    ElMessage.warning('暂无可复制的 UA')
    return
  }
  try {
    await navigator.clipboard.writeText(ua)
    ElMessage.success('已复制到剪贴板')
  } catch {
    ElMessage.warning('复制失败，请手动选择文字复制（需 HTTPS 或 localhost）')
  }
}

function apiBase() {
  return import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
}

/** 头像 URL 加缓存戳，避免上传后仍显示旧图 */
function buildAvatarUrl(avatarPath) {
  if (!avatarPath) return ''
  if (/^https?:\/\//i.test(avatarPath)) {
    const base = avatarPath.split('?')[0]
    return `${base}?t=${Date.now()}`
  }
  const path = avatarPath.startsWith('/') ? avatarPath : `/${avatarPath}`
  return `${apiBase()}${path}?t=${Date.now()}`
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
    avatarUrl.value = userInfo.avatar_url ? buildAvatarUrl(userInfo.avatar_url) : ''
  } catch (error) {
    profileError.value = error.response?.data?.detail || error.message || '加载用户信息失败'
    ElMessage.error(profileError.value)
  } finally {
    profileLoading.value = false
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
    llmForm.value.baseUrl = s.baseUrl ?? ''
    llmForm.value.model = s.model ?? ''
    llmForm.value.apiKey = ''
    llmForm.value.editApiKey = false
  } catch (error) {
    llmError.value = error.response?.data?.detail || error.message || '加载模型设置失败'
    ElMessage.error(llmError.value)
  } finally {
    llmLoading.value = false
  }
}

function applyLlmBaseUrlNormalization(showToast = true) {
  const raw = llmForm.value.baseUrl.trim()
  if (!raw) return raw
  const normalized = normalizeOpenAiCompatibleBaseUrl(raw)
  if (!normalized || normalized === raw) return raw
  llmForm.value.baseUrl = normalized
  if (showToast) {
    ElMessage.info(`已自动将 API 基址规范为：${normalized}`)
  }
  return normalized
}

function onLlmBaseUrlBlur() {
  applyLlmBaseUrlNormalization(true)
}

async function saveLlmSettings() {
  llmSaving.value = true
  try {
    const baseUrl = applyLlmBaseUrlNormalization(false) ?? llmForm.value.baseUrl.trim()
    const payload = {
      baseUrl,
      model: llmForm.value.model.trim(),
      apiKey: llmForm.value.apiKey.trim() || null,
      retainApiKey: !llmForm.value.editApiKey
    }
    const s = await userApi.putLLMSettings(payload)
    llmStatus.value = { hasStoredApiKey: !!s.hasStoredApiKey, apiKeyLast4: s.apiKeyLast4 ?? null }
    if (s.baseUrl) {
      llmForm.value.baseUrl = s.baseUrl
    }
    llmForm.value.apiKey = ''
    llmForm.value.editApiKey = false
    ElMessage.success('模型设置已保存')
  } catch (error) {
    const d = error.response?.data?.detail
    const msg = typeof d === 'string' ? d : error.message || '保存失败'
    ElMessage.error(msg)
  } finally {
    llmSaving.value = false
  }
}

async function reloadAll() {
  await Promise.all([loadUserData(), loadStats(), loadLlmSettings()])
}

onMounted(async () => {
  await reloadAll()
})

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
  } catch (error) {
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
    showPasswordForm.value = false
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '修改密码失败')
  } finally {
    changingPassword.value = false
  }
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

.user-center-toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 12px;
}

.section-alert {
  margin-bottom: 16px;
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
.password-card,
.about-card,
.llm-card {
  margin-bottom: 24px;
  border-radius: 12px;
}

.about-descriptions {
  margin-bottom: 16px;
}

.ua-wrap {
  display: inline-block;
  max-width: 100%;
  word-break: break-all;
  font-size: 12px;
  color: #606266;
}

.legal-links {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.link-sep {
  color: #dcdfe6;
  user-select: none;
}

.ua-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  flex-wrap: wrap;
}

.ua-row .ua-wrap {
  flex: 1;
  min-width: 0;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-header--password,
.card-header--fold {
  width: 100%;
}

.password-toggle-btn,
.section-toggle-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.password-toggle-icon,
.section-toggle-icon {
  transition: transform 0.36s cubic-bezier(0.33, 1, 0.68, 1);
}

.password-toggle-icon.is-open,
.section-toggle-icon.is-open {
  transform: rotate(-180deg);
}

.user-info-card :deep(.el-card__body),
.stats-card :deep(.el-card__body),
.llm-card :deep(.el-card__body),
.about-card :deep(.el-card__body),
.password-card :deep(.el-card__body) {
  padding-top: 0;
  padding-bottom: 0;
}

.section-fold-panel,
.password-fold-panel {
  overflow: hidden;
  padding: 4px 0 20px;
}

.password-fold-enter-active,
.password-fold-leave-active,
.section-fold-enter-active,
.section-fold-leave-active {
  transition:
    max-height 0.4s cubic-bezier(0.33, 1, 0.68, 1),
    opacity 0.32s ease,
    transform 0.32s ease;
}

.password-fold-enter-from,
.password-fold-leave-to,
.section-fold-enter-from,
.section-fold-leave-to {
  max-height: 0;
  opacity: 0;
  transform: translateY(-6px);
}

.password-fold-enter-to,
.password-fold-leave-from,
.section-fold-enter-to,
.section-fold-leave-from {
  max-height: 960px;
  opacity: 1;
  transform: translateY(0);
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.llm-form {
  max-width: 640px;
}

.llm-form :deep(.el-form-item) {
  margin-bottom: 18px;
}

.llm-key-status {
  font-size: 14px;
  color: #303133;
}

.llm-key-status--muted {
  color: #909399;
}

.llm-switch-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  flex-wrap: wrap;
}

.llm-switch-hint {
  font-size: 13px;
  color: #909399;
  line-height: 1.5;
  flex: 1;
  min-width: 200px;
}

.llm-base-url-hint {
  margin: 6px 0 0;
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
}

.llm-base-url-hint code {
  font-size: 11px;
  padding: 0 4px;
  background: #f4f4f5;
  border-radius: 3px;
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

.stat-item--clickable {
  cursor: pointer;
}

.stat-item--clickable:focus {
  outline: 2px solid #409eff;
  outline-offset: 2px;
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

.stat-label-inner {
  border-bottom: 1px dashed #c0c4cc;
  cursor: help;
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

<style>
/* el-dialog 默认 teleport 到 body，scoped 无法作用到正文，故单独写 */
.legal-dialog .legal-doc-note {
  margin: 0 0 12px;
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
}

.legal-dialog .legal-doc-body {
  max-height: min(58vh, 440px);
  overflow-y: auto;
  padding-right: 4px;
}

.legal-dialog .legal-doc-section {
  margin-bottom: 18px;
}

.legal-dialog .legal-doc-section:last-child {
  margin-bottom: 0;
}

.legal-dialog .legal-doc-h {
  margin: 0 0 8px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.legal-dialog .legal-doc-p {
  margin: 0 0 8px;
  font-size: 13px;
  line-height: 1.65;
  color: #606266;
}

.legal-dialog .legal-doc-p:last-child {
  margin-bottom: 0;
}
</style>
