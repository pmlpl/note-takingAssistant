<template>
  <el-card class="llm-card user-card" shadow="hover">
    <template #header>
      <div class="card-header card-header--fold">
        <span class="card-title">AI模型配置</span>
        <el-button
          text
          type="primary"
          class="section-toggle-btn"
          @click="visible = !visible"
        >
          <el-icon class="section-toggle-icon" :class="{ 'is-open': visible }">
            <ArrowDown />
          </el-icon>
          <span>{{ visible ? '收起' : '展开' }}</span>
        </el-button>
      </div>
    </template>
    <Transition name="section-fold">
      <div v-show="visible" class="section-fold-panel" v-loading="loading">
        <el-alert
          v-if="error && !loading"
          type="error"
          :title="error"
          show-icon
          :closable="false"
          class="section-alert"
        />
        <el-form :model="form" label-width="128px" class="llm-form">
          <el-form-item label="使用本地模型">
            <div class="llm-switch-row">
              <el-switch v-model="form.useLocal" />
              <span class="llm-switch-hint">
                开启后AI功能直连本地模型（数据不经过服务器）；关闭则使用云端模型。
              </span>
            </div>
          </el-form-item>

          <template v-if="form.useLocal">
            <el-alert
              type="info"
              title="本地模型配置仅存储在本地，数据不经过服务器"
              show-icon
              :closable="false"
              class="section-alert"
            />
            <el-form-item label="API 基址">
              <el-input
                v-model="localForm.baseUrl"
                placeholder="例如 http://127.0.0.1:1234/v1"
                clearable
                autocomplete="off"
                @blur="onLocalBaseUrlBlur"
              />
              <div class="llm-form-tip">
                支持 LM Studio、vLLM、Ollama 等 OpenAI 兼容接口
              </div>
            </el-form-item>
            <el-form-item label="模型标识">
              <el-input
                v-model="localForm.model"
                placeholder="例如 qwen3.5-9b"
                clearable
                autocomplete="off"
              />
            </el-form-item>
            <el-form-item label="API Key（可选）">
              <div v-if="localSaved.hasKey" class="llm-key-display">
                <span>已配置（后四位：{{ localSaved.apiKeyLast4 }}）</span>
                <el-button text type="danger" size="small" @click="clearLocalApiKey">清除</el-button>
              </div>
              <el-input
                v-else
                v-model="localForm.apiKey"
                type="password"
                show-password
                placeholder="多数本地模型无需密钥，留空即可"
                @keydown.enter.prevent="handleSave"
              />
            </el-form-item>
          </template>

          <template v-else>
            <el-alert
              type="warning"
              title="云端模型数据经过服务器转发，请使用可信的API服务"
              show-icon
              :closable="false"
              class="section-alert"
            />
            <el-form-item label="API 基址">
              <el-input
                v-model="cloudForm.baseUrl"
                placeholder="例如 https://api.deepseek.com/v1"
                clearable
                autocomplete="off"
                @blur="onCloudBaseUrlBlur"
              />
              <div class="llm-form-tip">
                填写OpenAI兼容接口地址，如DeepSeek、通义千问等
              </div>
            </el-form-item>
            <el-form-item label="模型标识">
              <el-input
                v-model="cloudForm.model"
                placeholder="例如 deepseek-chat"
                clearable
                autocomplete="off"
              />
            </el-form-item>
            <el-form-item label="API Key">
              <div v-if="cloudSaved.hasKey" class="llm-key-display">
                <span>已配置（后四位：{{ cloudSaved.apiKeyLast4 }}）</span>
                <el-button text type="danger" size="small" @click="clearCloudApiKey">清除</el-button>
              </div>
              <el-input
                v-else
                v-model="cloudForm.apiKey"
                type="password"
                show-password
                placeholder="输入API Key"
                @keydown.enter.prevent="handleSave"
              />
              <div v-if="cloudSaved.hasKey" class="llm-form-tip">
                开启下方开关可修改密钥
              </div>
            </el-form-item>
            <el-form-item v-if="cloudSaved.hasKey" label="修改密钥">
              <div class="llm-switch-row">
                <el-switch v-model="cloudEditKey" />
                <span class="llm-switch-hint">
                  开启后可输入新密钥；若留空并保存，将清除已保存的密钥。
                </span>
              </div>
            </el-form-item>
            <el-form-item v-if="cloudEditKey && cloudSaved.hasKey" label="新 API Key">
              <el-input
                v-model="cloudForm.apiKey"
                type="password"
                show-password
                placeholder="输入新密钥"
                @keydown.enter.prevent="handleSave"
              />
            </el-form-item>
          </template>

          <el-form-item>
            <el-button type="primary" :loading="saving" @click="handleSave">
              {{ saving ? '保存中…' : '保存设置' }}
            </el-button>
          </el-form-item>
        </el-form>
      </div>
    </Transition>
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowDown } from '@element-plus/icons-vue'
import { normalizeOpenAiCompatibleBaseUrl } from '@/utils/common'
import { validateLocalModelUrl } from '@/utils/localLlmClient'
import { userApi } from '@/api/user'

const props = defineProps({
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  defaultVisible: { type: Boolean, default: false }
})

const emit = defineEmits(['save', 'update:status'])

const visible = ref(props.defaultVisible)
const saving = ref(false)

const form = reactive({
  useLocal: false
})

const localForm = reactive({
  baseUrl: 'http://127.0.0.1:1234/v1',
  model: '',
  apiKey: ''
})

const localSaved = reactive({
  hasKey: false,
  apiKeyLast4: null
})

const cloudForm = reactive({
  baseUrl: '',
  model: '',
  apiKey: ''
})

const cloudSaved = reactive({
  hasKey: false,
  apiKeyLast4: null
})

const cloudEditKey = ref(false)

let isLoadingSettings = false

async function loadSettings() {
  isLoadingSettings = true
  try {
    const localSettings = await window.electronAPI?.store?.get('local_llm_settings')
    if (localSettings && typeof localSettings === 'object') {
      form.useLocal = localSettings.enabled || false
      if (localSettings.baseUrl) localForm.baseUrl = localSettings.baseUrl
      if (localSettings.model) localForm.model = localSettings.model
      if (localSettings.apiKey) {
        localSaved.hasKey = true
        localSaved.apiKeyLast4 = localSettings.apiKey.slice(-4)
      }
    }
  } catch {
    /* ignore */
  }

  try {
    const s = await userApi.getLLMSettings()
    cloudForm.baseUrl = s.baseUrl || ''
    cloudForm.model = s.model || ''
    cloudSaved.hasKey = !!s.hasStoredApiKey
    cloudSaved.apiKeyLast4 = s.apiKeyLast4 || null
  } catch {
    /* ignore */
  } finally {
    isLoadingSettings = false
  }
}

watch(() => form.useLocal, async (newVal) => {
  if (isLoadingSettings) return
  try {
    const current = await window.electronAPI?.store?.get('local_llm_settings')
    const updated = { ...(current || {}), enabled: newVal }
    await window.electronAPI?.store?.set('local_llm_settings', updated)
  } catch {
    /* ignore */
  }
})

onMounted(() => {
  loadSettings()
})

function onLocalBaseUrlBlur() {
  const raw = localForm.baseUrl.trim()
  if (!raw) return
  const normalized = normalizeOpenAiCompatibleBaseUrl(raw)
  if (normalized && normalized !== raw) {
    localForm.baseUrl = normalized
    ElMessage.info(`已自动将 API 基址规范为：${normalized}`)
  }
}

function onCloudBaseUrlBlur() {
  const raw = cloudForm.baseUrl.trim()
  if (!raw) return
  const normalized = normalizeOpenAiCompatibleBaseUrl(raw)
  if (normalized && normalized !== raw) {
    cloudForm.baseUrl = normalized
    ElMessage.info(`已自动将 API 基址规范为：${normalized}`)
  }
}

function clearLocalApiKey() {
  localSaved.hasKey = false
  localSaved.apiKeyLast4 = null
  localForm.apiKey = ''
}

function clearCloudApiKey() {
  cloudEditKey.value = true
  cloudForm.apiKey = ''
}

async function handleSave() {
  saving.value = true
  try {
    if (form.useLocal) {
      const baseUrl = localForm.baseUrl.trim()
      if (!baseUrl) {
        ElMessage.error('请填写 API 基址')
        return
      }

      const validation = validateLocalModelUrl(baseUrl)
      if (!validation.valid) {
        ElMessage.error(validation.message)
        return
      }

      let apiKeyToSave = ''
      if (localSaved.hasKey && !localForm.apiKey) {
        const settings = await window.electronAPI?.store?.get('local_llm_settings')
        apiKeyToSave = settings?.apiKey || ''
      } else {
        apiKeyToSave = localForm.apiKey.trim()
      }

      const settings = {
        enabled: true,
        baseUrl,
        model: localForm.model.trim(),
        apiKey: apiKeyToSave
      }

      await window.electronAPI?.store?.set('local_llm_settings', settings)

      localSaved.hasKey = !!apiKeyToSave
      localSaved.apiKeyLast4 = apiKeyToSave ? apiKeyToSave.slice(-4) : null
      localForm.apiKey = ''

      ElMessage.success('本地模型设置已保存')
      emit('save', { useLocal: true, ...settings })
    } else {
      await window.electronAPI?.store?.set('local_llm_settings', { enabled: false })

      const baseUrl = cloudForm.baseUrl.trim()
      const payload = {
        baseUrl,
        model: cloudForm.model.trim(),
        apiKey: cloudEditKey.value ? (cloudForm.apiKey.trim() || null) : undefined,
        retainApiKey: !cloudEditKey.value
      }

      const s = await userApi.putLLMSettings(payload)
      cloudSaved.hasKey = !!s.hasStoredApiKey
      cloudSaved.apiKeyLast4 = s.apiKeyLast4 || null
      if (s.baseUrl) cloudForm.baseUrl = s.baseUrl
      cloudForm.apiKey = ''
      cloudEditKey.value = false

      emit('update:status', {
        hasStoredApiKey: !!s.hasStoredApiKey,
        apiKeyLast4: s.apiKeyLast4 || null
      })
      ElMessage.success('云端模型设置已保存')
      emit('save', { useLocal: false, ...s })
    }
  } catch (error) {
    const d = error.response?.data?.detail
    const msg = typeof d === 'string' ? d : error.message || '保存失败'
    ElMessage.error(msg)
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.llm-card {
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
  color: var(--color-text-primary) !important;
}

.section-fold-panel {
  overflow: hidden;
  padding: 4px 0 20px;
}

.section-alert {
  margin-bottom: 16px;
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

.llm-form {
  max-width: 640px;
}

.llm-form :deep(.el-form-item) {
  margin-bottom: 18px;
}

.llm-form-tip {
  font-size: 12px;
  color: var(--color-text-muted);
  margin-top: 8px;
}

.llm-key-display {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  color: var(--color-text-primary);
}

.llm-switch-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  flex-wrap: wrap;
}

.llm-switch-hint {
  font-size: 13px;
  color: var(--color-text-muted);
  line-height: 1.5;
  flex: 1;
  min-width: 200px;
}
</style>
