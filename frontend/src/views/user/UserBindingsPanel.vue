<template>
  <el-card class="bindings-card user-card" shadow="hover">
    <template #header>
      <div class="card-header card-header--fold">
        <span class="card-title">账号绑定</span>
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
      <div v-show="visible" v-loading="loading" class="section-fold-panel">
        <!-- 昵称修改 -->
        <div class="binding-section">
          <div class="binding-item">
            <div class="binding-info">
              <span class="binding-label">昵称</span>
              <span class="binding-value">{{ displayName }}</span>
            </div>
            <el-button size="small" @click="showNicknameDialog = true">修改</el-button>
          </div>
        </div>

        <el-divider />

        <!-- GitHub 绑定 -->
        <div class="binding-section">
          <div class="binding-item">
            <div class="binding-info">
              <div class="binding-platform">
                <img v-if="bindings.github?.avatar_url" :src="bindings.github.avatar_url" class="platform-avatar" alt="GitHub Avatar" />
                <span v-else class="platform-icon">🐙</span>
                <div>
                  <div class="binding-label-row">
                    <span class="binding-label">GitHub</span>
                    <span v-if="bindings.github" class="binding-status binding-status--bound">已绑定</span>
                    <span v-else class="binding-status binding-status--unbound">未绑定</span>
                  </div>
                  <span v-if="bindings.github?.provider_username" class="binding-sub">
                    @{{ bindings.github.provider_username }}
                  </span>
                  <span v-if="bindings.github && !bindings.github.provider_username" class="binding-sub">
                    ID: {{ bindings.github.openid }}
                  </span>
                </div>
              </div>
            </div>
            <div class="binding-actions">
              <el-button
                v-if="bindings.github"
                size="small"
                type="danger"
                plain
                :loading="unbindingGithub"
                @click="handleUnbindGithub"
              >
                解除
              </el-button>
              <el-button
                v-else
                size="small"
                type="primary"
                :loading="bindingGithub"
                @click="handleBindGithub"
              >
                绑定
              </el-button>
            </div>
          </div>
        </div>

        <el-divider />

        <!-- 邮箱绑定 -->
        <div class="binding-section">
          <div class="binding-item">
            <div class="binding-info">
              <div class="binding-platform">
                <span class="platform-icon">📧</span>
                <div>
                  <span class="binding-label">邮箱</span>
                  <span v-if="bindings.email" class="binding-status binding-status--bound">
                    {{ bindings.email }}
                    <el-tag v-if="bindings.email_verified" size="small" type="success" effect="light" style="margin-left: 4px;">已验证</el-tag>
                  </span>
                  <span v-else class="binding-status binding-status--unbound">未绑定</span>
                </div>
              </div>
            </div>
            <div class="binding-actions">
              <el-button
                v-if="bindings.email && bindings.has_password"
                size="small"
                type="warning"
                plain
                @click="showChangeEmailDialog = true"
              >
                换绑
              </el-button>
              <el-button
                v-if="bindings.email && bindings.has_password"
                size="small"
                type="danger"
                plain
                @click="showUnbindEmailDialog = true"
              >
                解除
              </el-button>
              <el-button
                v-if="!bindings.email"
                size="small"
                type="primary"
                @click="showBindEmailDialog = true"
              >
                绑定
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- 修改昵称对话框 -->
    <el-dialog v-model="showNicknameDialog" title="修改昵称" width="400px" destroy-on-close>
      <el-form :model="nicknameForm" label-width="80px">
        <el-form-item label="新昵称">
          <el-input v-model="nicknameForm.nickname" placeholder="请输入新昵称（2-32字符）" clearable />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showNicknameDialog = false">取消</el-button>
        <el-button type="primary" :loading="savingNickname" @click="handleUpdateNickname">保存</el-button>
      </template>
    </el-dialog>

    <!-- 绑定邮箱对话框 -->
    <el-dialog v-model="showBindEmailDialog" title="绑定邮箱" width="400px" destroy-on-close>
      <el-form :model="bindEmailForm" label-width="80px">
        <el-form-item label="邮箱">
          <el-input v-model="bindEmailForm.email" placeholder="请输入邮箱地址" clearable />
        </el-form-item>
        <el-form-item label="验证码">
          <div class="code-input-row">
            <el-input v-model="bindEmailForm.code" placeholder="请输入验证码" clearable />
            <el-button
              :disabled="bindCodeCooldown > 0"
              :loading="sendingBindCode"
              @click="handleSendBindCode"
            >
              {{ bindCodeCooldown > 0 ? `${bindCodeCooldown}s` : '发送验证码' }}
            </el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showBindEmailDialog = false">取消</el-button>
        <el-button type="primary" :loading="bindingEmail" @click="handleBindEmail">确认绑定</el-button>
      </template>
    </el-dialog>

    <!-- 换绑邮箱对话框 -->
    <el-dialog v-model="showChangeEmailDialog" title="换绑邮箱" width="400px" destroy-on-close>
      <el-form :model="changeEmailForm" label-width="80px">
        <el-form-item label="新邮箱">
          <el-input v-model="changeEmailForm.email" placeholder="请输入新邮箱地址" clearable />
        </el-form-item>
        <el-form-item label="验证码">
          <div class="code-input-row">
            <el-input v-model="changeEmailForm.code" placeholder="请输入验证码" clearable />
            <el-button
              :disabled="changeCodeCooldown > 0"
              :loading="sendingChangeCode"
              @click="handleSendChangeCode"
            >
              {{ changeCodeCooldown > 0 ? `${changeCodeCooldown}s` : '发送验证码' }}
            </el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showChangeEmailDialog = false">取消</el-button>
        <el-button type="primary" :loading="changingEmail" @click="handleChangeEmail">确认换绑</el-button>
      </template>
    </el-dialog>

    <!-- 解除邮箱绑定对话框 -->
    <el-dialog v-model="showUnbindEmailDialog" title="解除邮箱绑定" width="400px" destroy-on-close>
      <p style="color: var(--el-text-color-regular); margin-bottom: 16px;">解除邮箱绑定后，您需要使用其他方式（GitHub）登录。请确认您的 GitHub 已绑定。</p>
      <el-form :model="unbindEmailForm" label-width="80px">
        <el-form-item label="密码" required>
          <el-input
            v-model="unbindEmailForm.password"
            type="password"
            placeholder="请输入当前密码"
            show-password
            clearable
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUnbindEmailDialog = false">取消</el-button>
        <el-button type="danger" :loading="unbindingEmail" @click="handleUnbindEmail">确认解除</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useUserStore } from '@/store'
import { userApi, oauthApi } from '@/api/user'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowDown } from '@element-plus/icons-vue'

const props = defineProps({
  loading: { type: Boolean, default: false },
  bindings: {
    type: Object,
    default: () => ({
      email: null,
      email_verified: false,
      has_password: false,
      github: null
    })
  },
  defaultVisible: { type: Boolean, default: false }
})

const emit = defineEmits(['nickname-updated', 'bindings-changed', 'reload-user'])

const userStore = useUserStore()
const visible = ref(props.defaultVisible)

const displayName = computed(() => {
  const u = userStore.user
  if (!u) return ''
  return u.nickname || u.username || (u.email ? u.email.split('@')[0] : '')
})

// 昵称修改
const showNicknameDialog = ref(false)
const nicknameForm = reactive({ nickname: '' })
const savingNickname = ref(false)

// GitHub 绑定
const bindingGithub = ref(false)
const unbindingGithub = ref(false)

// 邮箱绑定
const showBindEmailDialog = ref(false)
const showChangeEmailDialog = ref(false)
const showUnbindEmailDialog = ref(false)
const bindEmailForm = reactive({ email: '', code: '' })
const changeEmailForm = reactive({ email: '', code: '' })
const unbindEmailForm = reactive({ password: '' })
const sendingBindCode = ref(false)
const sendingChangeCode = ref(false)
const bindingEmail = ref(false)
const changingEmail = ref(false)
const unbindingEmail = ref(false)
const bindCodeCooldown = ref(0)
const changeCodeCooldown = ref(0)
let bindCodeTimer = null
let changeCodeTimer = null

function persistUserToStorage() {
  if (userStore.user) {
    try {
      localStorage.setItem('user', JSON.stringify(userStore.user))
    } catch {
      /* ignore */
    }
  }
}

// 昵称修改
async function handleUpdateNickname() {
  if (!nicknameForm.nickname || nicknameForm.nickname.length < 2) {
    ElMessage.warning('请输入有效的昵称（至少2个字符）')
    return
  }
  savingNickname.value = true
  try {
    const result = await userApi.updateNickname(nicknameForm.nickname)
    userStore.user.nickname = result.nickname
    persistUserToStorage()
    ElMessage.success('昵称修改成功')
    showNicknameDialog.value = false
    nicknameForm.nickname = ''
    emit('nickname-updated', result.nickname)
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '修改昵称失败')
  } finally {
    savingNickname.value = false
  }
}

// GitHub 绑定
async function handleBindGithub() {
  bindingGithub.value = true
  try {
    const config = await oauthApi.githubConfig()
    if (!config.enabled) {
      ElMessage.error('GitHub 登录未配置，请联系管理员')
      return
    }
    const result = await oauthApi.githubAuthorize()
    const authWindow = window.open(result.authorize_url, '_blank', 'width=600,height=700')

    function handleMessage(event) {
      if (event.data && event.data.type === 'oauth-bind-result') {
        window.removeEventListener('message', handleMessage)
        if (event.data.success) {
          ElMessage.success('GitHub 绑定成功')
        } else {
          ElMessage.error(event.data.error || '绑定失败')
        }
        emit('bindings-changed')
        emit('reload-user')
        bindingGithub.value = false
      }
    }
    window.addEventListener('message', handleMessage)

    const checkInterval = setInterval(() => {
      try {
        if (authWindow.closed) {
          clearInterval(checkInterval)
          setTimeout(() => {
            window.removeEventListener('message', handleMessage)
            emit('bindings-changed')
            emit('reload-user')
            bindingGithub.value = false
          }, 500)
        }
      } catch {
        // ignore
      }
    }, 1000)
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '获取授权链接失败')
    bindingGithub.value = false
  }
}

async function handleUnbindGithub() {
  try {
    await ElMessageBox.confirm('确定要解除 GitHub 绑定吗？', '提示', {
      confirmButtonText: '解除',
      cancelButtonText: '取消',
      type: 'warning'
    })
  } catch {
    return
  }
  unbindingGithub.value = true
  try {
    await userApi.unbindGithub()
    emit('bindings-changed')
    ElMessage.success('GitHub 已解除绑定')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '解除绑定失败')
  } finally {
    unbindingGithub.value = false
  }
}

// 邮箱绑定 - 发送验证码
async function handleSendBindCode() {
  if (!bindEmailForm.email) {
    ElMessage.warning('请输入邮箱地址')
    return
  }
  sendingBindCode.value = true
  try {
    await oauthApi.sendBindCode({ email: bindEmailForm.email, action: 'bind' })
    ElMessage.success('验证码已发送')
    bindCodeCooldown.value = 60
    if (bindCodeTimer) clearInterval(bindCodeTimer)
    bindCodeTimer = setInterval(() => {
      bindCodeCooldown.value--
      if (bindCodeCooldown.value <= 0) {
        clearInterval(bindCodeTimer)
        bindCodeTimer = null
      }
    }, 1000)
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '发送验证码失败')
  } finally {
    sendingBindCode.value = false
  }
}

async function handleBindEmail() {
  if (!bindEmailForm.email || !bindEmailForm.code) {
    ElMessage.warning('请输入邮箱和验证码')
    return
  }
  bindingEmail.value = true
  try {
    await oauthApi.bindEmail({
      email: bindEmailForm.email,
      code: bindEmailForm.code,
      action: 'bind'
    })
    emit('bindings-changed')
    emit('reload-user')
    ElMessage.success('邮箱绑定成功')
    showBindEmailDialog.value = false
    bindEmailForm.email = ''
    bindEmailForm.code = ''
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '绑定邮箱失败')
  } finally {
    bindingEmail.value = false
  }
}

// 邮箱换绑 - 发送验证码
async function handleSendChangeCode() {
  if (!changeEmailForm.email) {
    ElMessage.warning('请输入新邮箱地址')
    return
  }
  sendingChangeCode.value = true
  try {
    await oauthApi.sendBindCode({ email: changeEmailForm.email, action: 'change' })
    ElMessage.success('验证码已发送')
    changeCodeCooldown.value = 60
    if (changeCodeTimer) clearInterval(changeCodeTimer)
    changeCodeTimer = setInterval(() => {
      changeCodeCooldown.value--
      if (changeCodeCooldown.value <= 0) {
        clearInterval(changeCodeTimer)
        changeCodeTimer = null
      }
    }, 1000)
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '发送验证码失败')
  } finally {
    sendingChangeCode.value = false
  }
}

async function handleChangeEmail() {
  if (!changeEmailForm.email || !changeEmailForm.code) {
    ElMessage.warning('请输入新邮箱和验证码')
    return
  }
  changingEmail.value = true
  try {
    await oauthApi.bindEmail({
      email: changeEmailForm.email,
      code: changeEmailForm.code,
      action: 'change'
    })
    emit('bindings-changed')
    emit('reload-user')
    ElMessage.success('邮箱换绑成功')
    showChangeEmailDialog.value = false
    changeEmailForm.email = ''
    changeEmailForm.code = ''
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '换绑邮箱失败')
  } finally {
    changingEmail.value = false
  }
}

// 解除邮箱绑定
async function handleUnbindEmail() {
  if (!unbindEmailForm.password) {
    ElMessage.warning('请输入当前密码')
    return
  }
  try {
    await ElMessageBox.confirm('确定要解除邮箱绑定吗？解除后您需要使用 GitHub 登录。', '警告', {
      confirmButtonText: '解除',
      cancelButtonText: '取消',
      type: 'warning'
    })
  } catch {
    return
  }
  unbindingEmail.value = true
  try {
    await userApi.unbindEmail(unbindEmailForm.password)
    emit('bindings-changed')
    emit('reload-user')
    ElMessage.success('邮箱已解除绑定')
    showUnbindEmailDialog.value = false
    unbindEmailForm.password = ''
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '解除绑定失败')
  } finally {
    unbindingEmail.value = false
  }
}
</script>

<style scoped>
.bindings-card {
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

.binding-section {
  padding: 8px 0;
}

.binding-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.binding-info {
  flex: 1;
}

.binding-platform {
  display: flex;
  align-items: center;
  gap: 12px;
}

.platform-icon {
  font-size: 24px;
}

.platform-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid var(--el-border-color-light);
}

.binding-label-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.binding-label {
  font-weight: 500;
  color: var(--el-text-color-primary);
  margin-right: 8px;
}

.binding-value {
  color: var(--el-text-color-regular);
}

.binding-sub {
  display: block;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 2px;
}

.binding-status {
  font-size: 14px;
}

/* P1 修复：原 #67c23a 白底 2.24:1，改用 --color-green（#2e7d32 ≈ 5.13:1 AA） */
.binding-status--bound {
  color: var(--color-green);
}

.binding-status--unbound {
  color: var(--el-text-color-secondary);
}

.binding-actions {
  display: flex;
  gap: 8px;
}

/* P1 修复：换绑按钮（warning plain）原 #ff9f43 于浅底 1.9:1 近乎不可读，
   改用 --color-warning-deep（#b45309 ≈ 5.02:1 AA）并略增字号 */
.binding-actions :deep(.el-button--warning.is-plain) {
  color: var(--color-warning-deep);
  font-size: 13px;
}
.binding-actions :deep(.el-button--warning.is-plain:hover),
.binding-actions :deep(.el-button--warning.is-plain:focus) {
  color: #fff;
}

.code-input-row {
  display: flex;
  gap: 8px;
}

.code-input-row .el-input {
  flex: 1;
}
</style>
