<template>
  <el-card class="llm-card user-card" shadow="hover">
    <template #header>
      <div class="card-header card-header--fold">
        <span class="card-title">AI 模型（自带密钥）</span>
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
          <el-form-item label="API 基址">
            <el-input
              v-model="form.baseUrl"
              placeholder="例如 http://10.16.54.177:1234（可省略 /v1，保存时自动补全）"
              clearable
              autocomplete="off"
              @blur="onBaseUrlBlur"
            />
          </el-form-item>
          <el-form-item label="模型标识">
            <el-input
              v-model="form.model"
              placeholder="留空则使用服务端默认"
              clearable
              autocomplete="off"
            />
          </el-form-item>
          <el-form-item label="个人密钥">
            <span v-if="status.hasStoredApiKey" class="llm-key-status">
              已保存（后四位：{{ status.apiKeyLast4 || '—' }}）
            </span>
            <span v-else class="llm-key-status llm-key-status--muted">未配置，将使用服务端默认密钥策略</span>
          </el-form-item>
          <el-form-item label="修改 API 密钥">
            <div class="llm-switch-row">
              <el-switch v-model="form.editApiKey" />
              <span class="llm-switch-hint">
                开启后可输入新密钥；若留空并保存，将清除已保存的个人密钥。
              </span>
            </div>
          </el-form-item>
          <el-form-item v-show="form.editApiKey" label="新 API Key">
            <el-input
              v-model="form.apiKey"
              type="password"
              show-password
              autocomplete="new-password"
              placeholder="输入新密钥"
              clearable
            />
          </el-form-item>
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
import { ref, reactive, watch } from 'vue'
import { userApi } from '@/api/user'
import { ElMessage } from 'element-plus'
import { ArrowDown } from '@element-plus/icons-vue'
import { normalizeOpenAiCompatibleBaseUrl } from '@/utils/common'

const props = defineProps({
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  status: {
    type: Object,
    default: () => ({ hasStoredApiKey: false, apiKeyLast4: null })
  },
  baseUrl: { type: String, default: '' },
  model: { type: String, default: '' },
  defaultVisible: { type: Boolean, default: false }
})

const emit = defineEmits(['save', 'update:status'])

const visible = ref(props.defaultVisible)
const saving = ref(false)

const form = reactive({
  baseUrl: props.baseUrl,
  model: props.model,
  apiKey: '',
  editApiKey: false
})

watch(
  () => props.baseUrl,
  (val) => {
    form.baseUrl = val
  }
)

watch(
  () => props.model,
  (val) => {
    form.model = val
  }
)

function applyBaseUrlNormalization(showToast = true) {
  const raw = form.baseUrl.trim()
  if (!raw) return raw
  const normalized = normalizeOpenAiCompatibleBaseUrl(raw)
  if (!normalized || normalized === raw) return raw
  form.baseUrl = normalized
  if (showToast) {
    ElMessage.info(`已自动将 API 基址规范为：${normalized}`)
  }
  return normalized
}

function onBaseUrlBlur() {
  applyBaseUrlNormalization(true)
}

async function handleSave() {
  saving.value = true
  try {
    const baseUrl = applyBaseUrlNormalization(false) ?? form.baseUrl.trim()
    const payload = {
      baseUrl,
      model: form.model.trim(),
      apiKey: form.apiKey.trim() || null,
      retainApiKey: !form.editApiKey
    }
    const s = await userApi.putLLMSettings(payload)
    emit('update:status', { hasStoredApiKey: !!s.hasStoredApiKey, apiKeyLast4: s.apiKeyLast4 ?? null })
    if (s.baseUrl) {
      form.baseUrl = s.baseUrl
    }
    form.apiKey = ''
    form.editApiKey = false
    ElMessage.success('模型设置已保存')
    emit('save', s)
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
  color: #303133;
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
</style>
