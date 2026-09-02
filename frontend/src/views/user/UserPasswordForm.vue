<template>
  <el-card class="password-card user-card" shadow="hover">
    <template #header>
      <div class="card-header card-header--fold">
        <span class="card-title">安全设置</span>
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
        <el-form :model="form" label-width="100px" class="password-form">
          <el-form-item label="当前密码">
            <el-input
              v-model="form.currentPassword"
              type="password"
              placeholder="请输入当前密码"
              show-password
              clearable
            />
          </el-form-item>
          <el-form-item label="新密码">
            <el-input
              v-model="form.newPassword"
              type="password"
              placeholder="请输入新密码（至少8位，含字母和数字）"
              show-password
              clearable
            />
          </el-form-item>
          <el-form-item v-if="form.newPassword" label="强度">
            <el-progress
              :percentage="passwordStrength.score"
              :color="passwordStrength.color"
              :stroke-width="10"
              :format="() => (passwordStrength.score ? `${passwordStrength.label} · ${passwordStrength.score}%` : '')"
            />
          </el-form-item>
          <el-form-item label="确认密码">
            <el-input
              v-model="form.confirmPassword"
              type="password"
              placeholder="请再次输入新密码"
              show-password
              clearable
            />
          </el-form-item>
          <el-form-item>
            <el-button
              type="primary"
              @click="handleChange"
              :loading="changing"
              class="submit-btn"
            >
              {{ changing ? '修改中...' : '确认修改' }}
            </el-button>
          </el-form-item>
        </el-form>
      </div>
    </Transition>
  </el-card>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { userApi } from '@/api/user'
import { ElMessage } from 'element-plus'
import { ArrowDown } from '@element-plus/icons-vue'

const props = defineProps({
  defaultVisible: { type: Boolean, default: false }
})

const emit = defineEmits(['changed'])

const visible = ref(props.defaultVisible)
const changing = ref(false)

const form = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const passwordStrength = computed(() => {
  const p = form.newPassword
  if (!p) {
    return { score: 0, label: '', color: '#909399' }
  }
  let score = 0
  if (p.length >= 8) score += 20
  if (p.length >= 12) score += 15
  if (/[a-z]/.test(p)) score += 15
  if (/[A-Z]/.test(p)) score += 15
  if (/\d/.test(p)) score += 15
  if (/[^a-zA-Z0-9]/.test(p)) score += 20
  score = Math.min(100, score)
  // 强度条为图形指示器：硬编码 token 值并保持与 CSS 同步
  // （--color-accent #c62828 / --color-warning-deep #b45309 / --color-green #2e7d32）
  let label = '弱'
  let color = '#c62828'
  if (score >= 45) {
    label = '中'
    color = '#b45309'
  }
  if (score >= 75) {
    label = '强'
    color = '#2e7d32'
  }
  return { score, label, color }
})

async function handleChange() {
  if (!form.currentPassword) {
    ElMessage.warning('请输入当前密码')
    return
  }
  if (!form.newPassword) {
    ElMessage.warning('请输入新密码')
    return
  }
  if (form.newPassword !== form.confirmPassword) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }
  if (form.newPassword.length < 8) {
    ElMessage.warning('密码长度至少为8位')
    return
  }
  if (!/[A-Za-z]/.test(form.newPassword) || !/\d/.test(form.newPassword)) {
    ElMessage.warning('密码必须同时包含字母和数字')
    return
  }

  changing.value = true
  try {
    await userApi.changePassword(form)
    ElMessage.success('密码修改成功！')
    form.currentPassword = ''
    form.newPassword = ''
    form.confirmPassword = ''
    visible.value = false
    emit('changed')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '修改密码失败')
  } finally {
    changing.value = false
  }
}
</script>

<style scoped>
.password-card {
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
  color: var(--el-text-color-primary);
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

@media (max-width: 768px) {
  .password-form {
    max-width: 100%;
  }
}
</style>
