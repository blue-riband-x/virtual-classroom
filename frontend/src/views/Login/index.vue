<template>
  <div class="login-page">
    <!-- 背景装饰 -->
    <div class="bg-decor">
      <div class="bg-orb orb-1"></div>
      <div class="bg-orb orb-2"></div>
      <div class="bg-orb orb-3"></div>
    </div>

    <div class="login-container">
      <!-- Logo 区域 -->
      <div class="login-header">
        <div class="login-icon-wrap">
          <span class="login-icon">🏰</span>
          <div class="icon-ring"></div>
        </div>
        <h1 class="login-title">AI 虚拟课堂</h1>
        <p class="login-subtitle">开启你的AI学习之旅</p>
      </div>

      <!-- 登录表单卡片 -->
      <div class="login-card">
        <!-- Tab 切换 -->
        <div class="login-tabs">
          <button
            :class="['tab-btn', { active: mode === 'login' }]"
            @click="mode = 'login'"
          >
            🔑 登录
          </button>
          <button
            :class="['tab-btn', { active: mode === 'register' }]"
            @click="mode = 'register'"
          >
            ✨ 注册
          </button>
        </div>

        <!-- 表单 -->
        <div class="login-form" v-if="mode === 'login'">
          <div class="form-group">
            <label class="form-label">👤 用户名</label>
            <input
              v-model="loginForm.username"
              class="form-input"
              placeholder="输入用户名"
              @keyup.enter="handleLogin"
            />
          </div>
          <div class="form-group">
            <label class="form-label">🔒 密码</label>
            <input
              v-model="loginForm.password"
              class="form-input"
              type="password"
              placeholder="输入密码"
              @keyup.enter="handleLogin"
            />
          </div>

          <!-- 错误提示 -->
          <div v-if="loginError" class="error-msg">
            ⚠️ {{ loginError }}
          </div>

          <button
            class="btn btn-primary btn-lg login-btn"
            :disabled="loading"
            @click="handleLogin"
          >
            <span v-if="!loading">开始学习</span>
            <span v-else class="loading-dots">
              登录中<span class="dot">.</span><span class="dot">.</span><span class="dot">.</span>
            </span>
          </button>

          <!-- 快速登录提示 -->
          <div class="login-hint">
            <span class="hint-icon">💡</span>
            <span>测试账号: dev / 123456</span>
          </div>
        </div>

        <!-- 注册表单 -->
        <div class="login-form" v-else>
          <div class="form-group">
            <label class="form-label">👤 用户名</label>
            <input
              v-model="registerForm.username"
              class="form-input"
              placeholder="3-20个字符"
            />
          </div>
          <div class="form-group">
            <label class="form-label">🎯 昵称</label>
            <input
              v-model="registerForm.nickname"
              class="form-input"
              placeholder="你的昵称"
            />
          </div>
          <div class="form-group">
            <label class="form-label">📧 邮箱</label>
            <input
              v-model="registerForm.email"
              class="form-input"
              placeholder="example@mail.com"
            />
          </div>
          <div class="form-group">
            <label class="form-label">🔒 密码</label>
            <input
              v-model="registerForm.password"
              class="form-input"
              type="password"
              placeholder="至少6个字符"
            />
          </div>

          <div v-if="loginError" class="error-msg">
            ⚠️ {{ loginError }}
          </div>

          <button
            class="btn btn-accent btn-lg login-btn"
            :disabled="loading"
            @click="handleRegister"
          >
            <span v-if="!loading">✨ 创建学习档案</span>
            <span v-else class="loading-dots">
              注册中<span class="dot">.</span><span class="dot">.</span><span class="dot">.</span>
            </span>
          </button>
        </div>
      </div>

      <!-- 底部装饰 -->
      <div class="login-footer">
        <span class="footer-icon">🌳</span>
        <span>探索知识的无限可能</span>
        <span class="footer-icon">🌟</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores'
import { authAPI } from '@/services/api'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const mode = ref('login')
const loading = ref(false)
const loginError = ref('')

const loginForm = reactive({
  username: '',
  password: ''
})

const registerForm = reactive({
  username: '',
  nickname: '',
  email: '',
  password: ''
})

const handleLogin = async () => {
  loginError.value = ''

  if (!loginForm.username.trim() || !loginForm.password.trim()) {
    loginError.value = '请输入用户名和密码'
    return
  }

  loading.value = true
  try {
    const success = await userStore.login(loginForm.username, loginForm.password)
    if (success) {
      router.push(route.query.redirect || '/home')
    } else {
      loginError.value = userStore.error || '用户名或密码错误'
    }
  } catch (err) {
    loginError.value = err.message || '登录失败，请检查网络连接'
  } finally {
    loading.value = false
  }
}

const handleRegister = async () => {
  loginError.value = ''

  if (!registerForm.username.trim() || !registerForm.password.trim()) {
    loginError.value = '用户名和密码为必填项'
    return
  }
  if (registerForm.password.length < 6) {
    loginError.value = '密码至少6个字符'
    return
  }

  loading.value = true
  try {
    await authAPI.register({
      username: registerForm.username,
      nickname: registerForm.nickname || registerForm.username,
      email: registerForm.email || `${registerForm.username}@test.com`,
      password: registerForm.password
    })
    // 注册成功后自动切换到登录
    mode.value = 'login'
    loginForm.username = registerForm.username
    loginError.value = ''
    loginForm.password = ''
  } catch (err) {
    loginError.value = err.message || '注册失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(180deg, #E3F0FA 0%, #C5DFF5 30%, #D4E8F7 60%, #E8F1F9 100%);
  position: relative;
  overflow: hidden;
}

/* 背景装饰球 */
.bg-decor { pointer-events: none; }
.bg-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  opacity: 0.35;
}
.orb-1 {
  width: 300px; height: 300px;
  background: radial-gradient(circle, #7CB8E4, transparent);
  top: -80px; left: -60px;
  animation: orbFloat 8s ease-in-out infinite;
}
.orb-2 {
  width: 250px; height: 250px;
  background: radial-gradient(circle, #A8D0F0, transparent);
  bottom: -50px; right: -40px;
  animation: orbFloat 10s ease-in-out infinite reverse;
}
.orb-3 {
  width: 180px; height: 180px;
  background: radial-gradient(circle, #B8DAF5, transparent);
  top: 50%; left: 60%;
  animation: orbFloat 7s ease-in-out 1s infinite;
}
@keyframes orbFloat {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(20px, -20px) scale(1.05); }
  66% { transform: translate(-15px, 10px) scale(0.95); }
}

/* 容器 */
.login-container {
  position: relative;
  z-index: 1;
  width: 420px;
  max-width: 90vw;
  animation: fadeInUp 0.6s ease;
}
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(30px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Logo */
.login-header {
  text-align: center;
  margin-bottom: 2rem;
}
.login-icon-wrap {
  position: relative;
  display: inline-block;
  margin-bottom: 0.75rem;
}
.login-icon {
  font-size: 3.5rem;
  display: block;
  position: relative;
  z-index: 1;
  animation: iconBounce 2s ease-in-out infinite;
}
@keyframes iconBounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}
.icon-ring {
  position: absolute;
  inset: -12px;
  border: 2px solid rgba(74, 144, 217, 0.4);
  border-radius: 50%;
  opacity: 0.5;
  animation: ringPulse 2s ease-in-out infinite;
}
@keyframes ringPulse {
  0%, 100% { transform: scale(1); opacity: 0.5; }
  50% { transform: scale(1.15); opacity: 0.1; }
}
.login-title {
  font-size: 1.75rem;
  font-weight: 800;
  color: #2C4A6E;
  margin-bottom: 0.25rem;
}
.login-subtitle {
  font-size: 0.9375rem;
  color: #6B8AAD;
  font-weight: 500;
}

/* 卡片 */
.login-card {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(8px);
  border-radius: 20px;
  padding: 2rem;
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: 0 4px 20px rgba(74, 144, 217, 0.1);
  position: relative;
  overflow: hidden;
}
.login-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 4px;
  background: linear-gradient(90deg, #7CB8E4, #4A90D9, #A8D0F0);
}

/* Tab */
.login-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}
.tab-btn {
  flex: 1;
  padding: 0.625rem 1rem;
  border-radius: 14px;
  border: 1.5px solid rgba(74, 144, 217, 0.12);
  background: rgba(255, 255, 255, 0.6);
  color: #6B8AAD;
  font-size: 0.9375rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}
.tab-btn.active {
  background: linear-gradient(135deg, #4A90D9, #3A7BC8);
  color: white;
  border-color: transparent;
  box-shadow: 0 2px 10px rgba(74, 144, 217, 0.25);
}
.tab-btn:hover:not(.active) {
  border-color: rgba(74, 144, 217, 0.3);
  color: #4A90D9;
}

/* 表单 */
.login-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}
.form-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #2C4A6E;
}
.form-input {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1.5px solid rgba(74, 144, 217, 0.12);
  border-radius: 12px;
  font-size: 0.9375rem;
  color: #2C4A6E;
  background: rgba(255, 255, 255, 0.7);
  transition: all 0.3s ease;
  outline: none;
  font-family: inherit;
}
.form-input:focus {
  border-color: #4A90D9;
  background: white;
  box-shadow: 0 0 0 3px rgba(74, 144, 217, 0.08);
}
.form-input::placeholder {
  color: #AAC0D8;
}

/* 错误 */
.error-msg {
  padding: 0.75rem 1rem;
  background: #fff2f0;
  border: 1px solid #ffccc7;
  border-radius: 12px;
  color: #cf1322;
  font-size: 0.875rem;
  font-weight: 500;
  animation: wiggle 0.4s ease;
}
@keyframes wiggle {
  0%, 100% { transform: translateX(0); }
  20% { transform: translateX(-6px); }
  40% { transform: translateX(6px); }
  60% { transform: translateX(-4px); }
  80% { transform: translateX(4px); }
}

/* 按钮 */
.login-btn {
  width: 100%;
  margin-top: 0.5rem;
  font-size: 1.0625rem;
}

/* 加载动画 */
.loading-dots .dot {
  animation: dotPulse 1.5s infinite;
}
.loading-dots .dot:nth-child(2) { animation-delay: 0.2s; }
.loading-dots .dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes dotPulse {
  0%, 20% { opacity: 0; }
  50% { opacity: 1; }
  100% { opacity: 0; }
}

/* 提示 */
.login-hint {
  margin-top: 1rem;
  padding: 0.625rem 1rem;
  background: rgba(74, 144, 217, 0.06);
  border-radius: 12px;
  border: 1px dashed rgba(74, 144, 217, 0.15);
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8125rem;
  color: #6B8AAD;
}
.hint-icon { font-size: 1rem; }

/* Footer */
.login-footer {
  text-align: center;
  margin-top: 1.5rem;
  font-size: 0.8125rem;
  color: #8AA4C0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  font-weight: 500;
}
.footer-icon {
  font-size: 1.125rem;
}

/* 响应式 */
@media (max-width: 480px) {
  .login-card {
    padding: 1.5rem;
    border-radius: 16px;
  }
  .login-icon { font-size: 2.75rem; }
  .login-title { font-size: 1.5rem; }
}
</style>
