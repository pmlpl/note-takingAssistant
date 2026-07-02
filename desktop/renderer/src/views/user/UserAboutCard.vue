<template>
  <el-card class="about-card user-card" shadow="hover">
    <template #header>
      <div class="card-header card-header--fold">
        <span class="card-title">关于与本机</span>
        <el-button
          text
          type="primary"
          class="section-toggle-btn"
          @click="visible = !visible"
        >
          <el-icon class="section-toggle-icon" :class="{ 'is-open': visible }">
            <ArrowDown />
          </el-icon>
          <span>展开</span>
        </el-button>
      </div>
    </template>
    <Transition name="section-fold">
      <div v-show="visible" class="section-fold-panel">
        <el-descriptions :column="1" border size="small" class="about-descriptions">
          <el-descriptions-item label="用户 ID">{{ userId }}</el-descriptions-item>
          <el-descriptions-item label="应用名称">{{ aboutDevice.appName }}</el-descriptions-item>
          <el-descriptions-item label="版本号">{{ aboutDevice.appVersion }}</el-descriptions-item>
          <el-descriptions-item label="运行模式">{{ aboutDevice.mode }}</el-descriptions-item>
          <el-descriptions-item label="API 基址（开发）">{{ aboutDevice.apiBase }}</el-descriptions-item>
          <template v-if="isDesktop">
            <el-descriptions-item label="服务器地址">
              <div class="server-url-row">
                <el-input
                  v-model="serverUrlInput"
                  size="small"
                  placeholder="https://example.com/api"
                  style="flex: 1; min-width: 0"
                />
                <el-button size="small" type="primary" @click="saveServerUrl">保存</el-button>
                <el-button size="small" @click="resetServerUrl">恢复默认</el-button>
              </div>
            </el-descriptions-item>
          </template>
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
          <el-link type="primary" underline="never" @click.prevent="$emit('show-terms')">用户协议</el-link>
          <span class="link-sep">|</span>
          <el-link type="primary" underline="never" @click.prevent="$emit('show-privacy')">隐私政策</el-link>
        </div>
      </div>
    </Transition>
  </el-card>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/store'
import { ElMessage } from 'element-plus'
import { ArrowDown } from '@element-plus/icons-vue'
import appPkg from '../../../package.json'
import { DESKTOP_STORAGE_KEY, DESKTOP_DEFAULT_API_BASE } from '@/config/desktop'
import { updateBaseUrl } from '@/api'

const props = defineProps({
  defaultVisible: { type: Boolean, default: false }
})

defineEmits(['show-terms', 'show-privacy'])

const userStore = useUserStore()
const visible = ref(props.defaultVisible)

const isDesktop = typeof window !== 'undefined' && window.electronAPI?.isDesktop === true
const serverUrlInput = ref('')

async function loadServerUrl() {
  if (!isDesktop) return
  try {
    if (window.electronAPI?.store?.get) {
      const result = await window.electronAPI.store.get(DESKTOP_STORAGE_KEY, DESKTOP_DEFAULT_API_BASE)
      serverUrlInput.value = (result?.data) || DESKTOP_DEFAULT_API_BASE
    }
  } catch {
    serverUrlInput.value = DESKTOP_DEFAULT_API_BASE
  }
}

async function saveServerUrl() {
  if (!isDesktop) return
  const url = serverUrlInput.value.trim()
  if (!url) {
    ElMessage.warning('请输入服务器地址')
    return
  }
  if (!/^https?:\/\//.test(url)) {
    ElMessage.warning('地址必须以 http:// 或 https:// 开头')
    return
  }
  try {
    const cleanUrl = url.replace(/\/+$/, '')
    await window.electronAPI.store.set(DESKTOP_STORAGE_KEY, cleanUrl)
    updateBaseUrl(cleanUrl)
    ElMessage.success('服务器地址已保存')
  } catch (err) {
    ElMessage.error('保存失败：' + err.message)
  }
}

function resetServerUrl() {
  serverUrlInput.value = DESKTOP_DEFAULT_API_BASE
}

onMounted(() => {
  loadServerUrl()
})

const userId = computed(() => {
  const id = userStore.user?.id
  return id != null && id !== '' ? String(id) : '—'
})

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
  return 'NoteMind'
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
</script>

<style scoped>
.about-card {
  margin-bottom: 24px;
  border-radius: 12px;
}

.user-card :deep(.el-card__body) {
  padding-top: 0;
  padding-bottom: 0;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-header--fold {
  width: 100%;
}

.section-toggle-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.section-toggle-icon {
  transition: transform 0.36s cubic-bezier(0.33, 1, 0.68, 1);
}

.section-toggle-icon.is-open {
  transform: rotate(-180deg);
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-heading) !important;
}

.section-fold-panel {
  overflow: hidden;
  padding: 4px 0 20px;
}

.section-fold-enter-active,
.section-fold-leave-active {
  transition:
    max-height 0.4s cubic-bezier(0.33, 1, 0.68, 1),
    opacity 0.32s ease,
    transform 0.32s ease;
}

.section-fold-enter-from,
.section-fold-leave-to {
  max-height: 0;
  opacity: 0;
  transform: translateY(-6px);
}

.section-fold-enter-to,
.section-fold-leave-from {
  max-height: 960px;
  opacity: 1;
  transform: translateY(0);
}

.about-descriptions {
  margin-bottom: 16px;
}

.ua-wrap {
  display: inline-block;
  max-width: 100%;
  word-break: break-all;
  font-size: 12px;
  color: var(--color-text-secondary);
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

.legal-links {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.link-sep {
  color: var(--color-muted);
  user-select: none;
}

.server-url-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
