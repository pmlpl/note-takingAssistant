<template>
  <div class="login-container">
    <div class="login-wrapper">
      <el-card class="login-card">
        <div class="login-header">
          <AppLogo :size="52" />
          <h2>智能笔记助手</h2>
          <p class="login-subtitle">登录您的账号</p>
        </div>

        <el-tabs v-model="activeTab" class="login-tabs">
          <el-tab-pane label="邮箱密码" name="password">
            <el-form :model="passwordForm" ref="passwordFormRef" label-width="0" :rules="passwordRules">
              <el-form-item prop="email">
                <el-input v-model="passwordForm.email" placeholder="请输入邮箱" :prefix-icon="Message" />
              </el-form-item>
              <el-form-item prop="password">
                <el-input v-model="passwordForm.password" type="password" placeholder="请输入密码" show-password :prefix-icon="Lock" />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="handlePasswordLogin" :loading="passwordLoading" class="login-btn">
                  {{ passwordLoading ? '登录中...' : '登 录' }}
                </el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>

          <el-tab-pane label="邮箱验证码" name="code">
            <el-form :model="codeForm" ref="codeFormRef" label-width="0" :rules="codeRules">
              <el-form-item prop="email">
                <el-input v-model="codeForm.email" placeholder="请输入邮箱" :prefix-icon="Message" />
              </el-form-item>
              <el-form-item prop="code">
                <div class="code-input-wrap">
                  <el-input v-model="codeForm.code" placeholder="请输入验证码" :prefix-icon="Key" />
                  <el-button
                    type="primary"
                    plain
                    @click="sendCode"
                    :disabled="codeCountdown > 0"
                    class="send-code-btn"
                  >
                    {{ codeCountdown > 0 ? `${codeCountdown}s后重发` : '获取验证码' }}
                  </el-button>
                </div>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="handleCodeLogin" :loading="codeLoading" class="login-btn">
                  {{ codeLoading ? '登录中...' : '登录 / 注册' }}
                </el-button>
              </el-form-item>
              <p class="login-tip">未注册的邮箱将自动创建账号</p>
            </el-form>
          </el-tab-pane>
        </el-tabs>

        <div class="divider-section">
          <span class="divider-line"></span>
          <span class="divider-text">其他登录方式</span>
          <span class="divider-line"></span>
        </div>

        <div class="oauth-buttons" v-if="githubEnabled">
          <el-button @click="handleGithubLogin" class="oauth-btn github-btn" :loading="githubLoading">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
              <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
            </svg>
            <span>GitHub 登录</span>
          </el-button>
        </div>

        <div class="login-footer">
          <span>还没有账号？</span>
          <el-button link @click="navigate('/register')">立即注册</el-button>
        </div>
      </el-card>
    </div>

    <div class="deco deco-1"></div>
    <div class="deco deco-2"></div>
    <div class="deco deco-3"></div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/store'
import { userApi, oauthApi } from '@/api/user'
import { AppLogo } from '@/components/icons'
import { ElMessage } from 'element-plus'
import { Message, Lock, Key } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const passwordFormRef = ref(null)
const codeFormRef = ref(null)
const passwordLoading = ref(false)
const codeLoading = ref(false)
const githubLoading = ref(false)
const codeCountdown = ref(0)
const activeTab = ref('password')
const githubEnabled = ref(false)

const passwordForm = ref({
  email: '',
  password: ''
})

const codeForm = ref({
  email: '',
  code: ''
})

const passwordRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ]
}

const codeRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入验证码', trigger: 'blur' },
    { len: 6, message: '验证码为6位数字', trigger: 'blur' }
  ]
}

onMounted(() => {
  checkGithubConfig()
  handleUrlToken()
})

async function checkGithubConfig() {
  try {
    const res = await oauthApi.githubConfig()
    githubEnabled.value = res.enabled
  } catch (e) {
    githubEnabled.value = false
  }
}

function handleUrlToken() {
  const token = route.query.token
  const provider = route.query.provider
  const error = route.query.error

  if (error) {
    const errorMap = {
      'github_access_denied': 'GitHub 授权被取消',
      'github_token_failed': 'GitHub 登录失败，请重试',
      'github_user_failed': '获取 GitHub 用户信息失败',
      'github_no_code': 'GitHub 登录参数错误',
      'github_no_email': 'GitHub 账号未公开邮箱',
    }
    ElMessage.error(errorMap[error] || '登录失败，请重试')
    router.replace({ query: {} })
    return
  }

  if (token) {
    userStore.login(token, {})
    userApi.getUserInfo().then(res => {
      userStore.login(token, res)
      ElMessage.success(`${provider === 'github' ? 'GitHub' : ''}登录成功！`)
      router.push('/home')
    }).catch(() => {
      ElMessage.error('获取用户信息失败')
    })
    router.replace({ query: {} })
  }
}

async function handlePasswordLogin() {
  if (!passwordFormRef.value) return
  try {
    await passwordFormRef.value.validate()
  } catch {
    return
  }

  passwordLoading.value = true
  try {
    const response = await userApi.login(passwordForm.value)
    userStore.login(response.access_token, response.user)
    ElMessage.success('登录成功！')
    router.push('/home')
  } catch (error) {
    if (error.response?.status === 401) {
      ElMessage.error('邮箱或密码错误，请重试')
    } else if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('登录失败，请检查网络连接')
    }
  } finally {
    passwordLoading.value = false
  }
}

async function sendCode() {
  const email = codeForm.value.email.trim()
  if (!email) {
    ElMessage.warning('请先输入邮箱')
    return
  }
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(email)) {
    ElMessage.warning('请输入正确的邮箱格式')
    return
  }

  try {
    await oauthApi.sendEmailCode({ email })
    ElMessage.success('验证码已发送，请注意查收')
    codeCountdown.value = 60
    const timer = setInterval(() => {
      codeCountdown.value--
      if (codeCountdown.value <= 0) {
        clearInterval(timer)
      }
    }, 1000)
  } catch (error) {
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('验证码发送失败，请稍后重试')
    }
  }
}

async function handleCodeLogin() {
  if (!codeFormRef.value) return
  try {
    await codeFormRef.value.validate()
  } catch {
    return
  }

  codeLoading.value = true
  try {
    const response = await oauthApi.verifyEmailCode(codeForm.value)
    userStore.login(response.access_token, response.user)
    ElMessage.success('登录成功！')
    router.push('/home')
  } catch (error) {
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('登录失败，请稍后重试')
    }
  } finally {
    codeLoading.value = false
  }
}

async function handleGithubLogin() {
  githubLoading.value = true
  try {
    const res = await oauthApi.githubAuthorize()
    if (res.authorize_url) {
      window.location.href = res.authorize_url
    }
  } catch (error) {
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('GitHub 登录暂不可用')
    }
  } finally {
    githubLoading.value = false
  }
}

function navigate(path) {
  router.push(path)
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--color-paper);
  background-image: radial-gradient(var(--color-muted) 1px, transparent 1px);
  background-size: 24px 24px;
  position: relative;
  overflow: hidden;
  padding: 40px 20px;
}

.login-wrapper {
  width: 100%;
  max-width: 1200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 40px;
  position: relative;
  z-index: 1;
}

.login-card {
  width: 100%;
  max-width: 440px;
  padding: 0;
  position: relative;
}
.login-card :deep(.el-card__body) {
  padding: 40px 36px 30px;
}

.login-card::before {
  content: '';
  position: absolute;
  top: -12px;
  left: 50%;
  transform: translateX(-50%) rotate(3deg);
  width: 22px;
  height: 22px;
  background: var(--color-accent);
  border-radius: 50%;
  box-shadow: 1px 1px 0px 0px rgba(0,0,0,0.3);
  z-index: 2;
  border: 3px solid #fff;
}

.login-card::after {
  content: '';
  position: absolute;
  top: 16px;
  left: 50%;
  transform: translateX(-50%) rotate(-2deg);
  width: 90px;
  height: 18px;
  background: rgba(200, 200, 200, 0.3);
  border-radius: 2px;
  pointer-events: none;
}

.login-header {
  text-align: center;
  margin-bottom: 20px;
}

.login-header h2 {
  margin: 12px 0 4px;
  font-family: var(--font-heading);
  font-size: 28px;
  font-weight: 700;
  color: var(--color-pencil);
}

.login-subtitle {
  color: #888;
  font-family: var(--font-body);
  font-size: 15px;
  margin: 0;
}

.login-tabs {
  margin-bottom: 10px;
}
.login-tabs :deep(.el-tabs__header) {
  margin-bottom: 20px;
}
.login-tabs :deep(.el-tabs__nav-wrap::after) {
  background-color: var(--color-muted);
}
.login-tabs :deep(.el-tabs__item) {
  font-size: 15px;
}

.login-btn {
  width: 100%;
  font-size: 18px !important;
  padding: 12px 0 !important;
  height: auto !important;
}

.code-input-wrap {
  display: flex;
  gap: 10px;
  width: 100%;
}
.code-input-wrap .el-input {
  flex: 1;
}
.send-code-btn {
  white-space: nowrap;
  width: auto;
}

.login-tip {
  text-align: center;
  color: #999;
  font-size: 12px;
  margin: -5px 0 0 0;
}

.divider-section {
  display: flex;
  align-items: center;
  margin: 20px 0;
  gap: 12px;
}
.divider-line {
  flex: 1;
  height: 1px;
  background: var(--color-muted);
}
.divider-text {
  color: #999;
  font-size: 13px;
}

.oauth-buttons {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.oauth-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 42px;
  font-size: 15px !important;
}

.github-btn {
  background: #24292e;
  border-color: #24292e;
  color: white;
}
.github-btn:hover {
  background: #2f363d;
  border-color: #2f363d;
  color: white;
}

.login-footer {
  text-align: center;
  margin-top: 10px;
  font-family: var(--font-body);
  color: #888;
}

.deco {
  position: absolute;
  border-radius: 50%;
  border: 3px dashed var(--color-muted);
  pointer-events: none;
  opacity: 0.5;
}
.deco-1 {
  width: 180px;
  height: 180px;
  top: 12%;
  left: 8%;
  animation: floatDeco 8s ease-in-out infinite;
}
.deco-2 {
  width: 120px;
  height: 120px;
  bottom: 18%;
  right: 10%;
  background: var(--color-yellow);
  border-style: solid;
  animation: floatDeco 6s ease-in-out infinite reverse;
}
.deco-3 {
  width: 70px;
  height: 70px;
  top: 25%;
  right: 18%;
  background: var(--color-accent);
  opacity: 0.25;
  border-style: solid;
  animation: floatDeco 7s ease-in-out infinite 1s;
}

@keyframes floatDeco {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  33%  { transform: translateY(-15px) rotate(3deg); }
  66%  { transform: translateY(8px) rotate(-2deg); }
}
</style>
