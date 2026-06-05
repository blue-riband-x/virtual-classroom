<template>
  <div class="profile-page">
    <Navbar />
    
    <div class="profile-container">
      <!-- 用户信息卡片 -->
      <div class="profile-header">
        <div class="avatar-section">
          <div class="avatar-wrapper">
            <div class="avatar-main">{{ userStore.userInfo.avatar }}</div>
            <button class="avatar-edit">✏️</button>
          </div>
          <div class="level-badge">Lv.{{ userStore.userInfo.level }}</div>
        </div>
        <div class="profile-info">
          <h1>{{ userStore.userInfo.nickname }}</h1>
          <p class="profile-meta">
            <span>{{ userStore.userInfo.grade }}</span>
            <span class="dot">·</span>
            <span>{{ userStore.userInfo.subjects.join('、') }}</span>
          </p>
          <div class="profile-stats">
            <div class="stat">
              <span class="stat-value">{{ userStore.userInfo.totalLearningHours }}</span>
              <span class="stat-label">学习时长(h)</span>
            </div>
            <div class="stat">
              <span class="stat-value">{{ userStore.unlockedAchievements.length }}</span>
              <span class="stat-label">成就数</span>
            </div>
            <div class="stat">
              <span class="stat-value">{{ userStore.learningHistory.length }}</span>
              <span class="stat-label">学习次数</span>
            </div>
          </div>
        </div>
      </div>

      <!-- XP进度 -->
      <div class="xp-card">
        <div class="xp-header">
          <span>⚡ 经验值</span>
          <span class="xp-hint">升级还需 {{ userStore.userInfo.xpToNextLevel - userStore.userInfo.xp }} XP</span>
        </div>
        <XPProgress 
          :current="userStore.userInfo.xp" 
          :total="userStore.userInfo.xpToNextLevel"
          :level="userStore.userInfo.level"
        />
      </div>

      <!-- 学习历史 -->
      <div class="history-section">
        <div class="section-header">
          <h2>📚 学习历史</h2>
          <span class="view-all">查看全部</span>
        </div>
        <div class="history-list">
          <div 
            v-for="item in userStore.learningHistory" 
            :key="item.id"
            class="history-item"
          >
            <div class="history-icon">
              {{ getSubjectIcon(item.topic) }}
            </div>
            <div class="history-info">
              <h4>{{ item.topic }}</h4>
              <p>{{ item.date }} · {{ item.duration }}分钟</p>
            </div>
            <div class="history-score">
              <div class="score-badge" :class="getScoreClass(item.score)">
                {{ item.score }}
              </div>
              <span class="xp-badge">+{{ item.xp }} XP</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 我的大纲 -->
      <div class="outlines-section" v-if="myOutlines.length">
        <div class="section-header">
          <h2>📋 我的大纲</h2>
          <span class="view-all">{{ myOutlines.length }} 份</span>
        </div>
        <div class="outline-list">
          <div
            v-for="o in myOutlines"
            :key="o.id"
            class="outline-card"
            @click="handleSelectOutline(o)"
          >
            <div class="outline-card-header">
              <!-- 可编辑的大纲名称 -->
              <span v-if="editingOutlineId !== o.id" class="oc-topic oc-topic-editable" @click.stop="startEditTitle(o)">{{ o.title }}</span>
              <input
                v-else
                class="oc-topic-input"
                v-model="editTitleValue"
                @blur="saveTitle(o)"
                @keyup.enter="saveTitle(o)"
                @click.stop
                maxlength="100"
              />
              <span class="oc-level">{{ levelMap[o.level] || o.level }}</span>
            </div>
            <div class="oc-meta">
              <span>{{ o.module_count }} 模块</span>
              <span>{{ o.total_duration }} 分钟</span>
              <span>{{ formatDate(o.created_at) }}</span>
            </div>
            <!-- 展开查看模块 -->
            <div v-if="selectedOutline?.id === o.id" class="outline-modules">
              <div v-for="(m, mi) in getModulesWithStatus(o)" :key="mi" class="outline-module">
                <div class="om-header">
                  <span class="om-name">{{ m.name }}</span>
                  <span class="om-dur">{{ m.duration }}分钟</span>
                  <!-- 模块状态标记 -->
                  <span class="om-status" :class="m.contentStatus">
                    <template v-if="m.contentStatus === 'completed'">✅ 已生成</template>
                    <template v-else-if="m.contentStatus === 'generating'">⏳ 生成中</template>
                    <template v-else-if="m.contentStatus === 'failed'">❌ 失败</template>
                  </span>
                  <!-- 生成按钮 -->
                  <button
                    v-if="m.contentStatus !== 'completed' && m.contentStatus !== 'generating'"
                    class="om-gen-btn"
                    @click.stop="generateModuleForOutline(o.id, mi + 1)"
                  >⚡ 生成课程</button>
                </div>
                <div class="om-points">
                  <span v-for="(p, pi) in (m.keyPoints || [])" :key="pi" class="om-point">{{ p }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 设置菜单 -->
      <div class="settings-section">
        <h2>⚙️ 设置</h2>
        <div class="settings-list">
          <div class="setting-item">
            <span class="setting-icon">🔊</span>
            <div class="setting-info">
              <span class="setting-name">语音设置</span>
              <span class="setting-value">{{ userStore.settings.voiceType === 'female' ? '女声' : '男声' }} · {{ userStore.settings.voiceSpeed === 'medium' ? '中速' : userStore.settings.voiceSpeed }}</span>
            </div>
            <span class="setting-arrow">→</span>
          </div>
          <!-- 教师风格 -->
          <div class="setting-item" @click="showTeacherStyle = true">
            <span class="setting-icon">🧑‍🏫</span>
            <div class="setting-info">
              <span class="setting-name">教师风格</span>
              <span class="setting-value">{{ teacherStyleText }}</span>
            </div>
            <span class="setting-arrow">→</span>
          </div>
          <div class="setting-item">
            <span class="setting-icon">🔔</span>
            <div class="setting-info">
              <span class="setting-name">消息通知</span>
              <span class="setting-value">{{ userStore.settings.notifications ? '已开启' : '已关闭' }}</span>
            </div>
            <label class="toggle">
              <input type="checkbox" v-model="userStore.settings.notifications" />
              <span class="toggle-slider"></span>
            </label>
          </div>
          <div class="setting-item">
            <span class="setting-icon">🔤</span>
            <div class="setting-info">
              <span class="setting-name">界面字体</span>
              <span class="setting-value">{{ fontSizeText }}</span>
            </div>
            <span class="setting-arrow">→</span>
          </div>
          <div class="setting-item" @click="$router.push('/profile')">
            <span class="setting-icon">👤</span>
            <div class="setting-info">
              <span class="setting-name">账号信息</span>
              <span class="setting-value">{{ userStore.userInfo.phone }}</span>
            </div>
            <span class="setting-arrow">→</span>
          </div>
        </div>
      </div>

      <!-- 功能入口 -->
      <div class="feature-section">
        <h2>📱 更多功能</h2>
        <div class="feature-grid">
          <div class="feature-item" @click="$router.push('/game')">
            <span class="feature-icon">🏅</span>
            <span class="feature-name">成就墙</span>
          </div>
          <div class="feature-item" @click="$router.push('/leaderboard')">
            <span class="feature-icon">🏆</span>
            <span class="feature-name">排行榜</span>
          </div>
          <div class="feature-item">
            <span class="feature-icon">📄</span>
            <span class="feature-name">我的报告</span>
          </div>
          <div class="feature-item">
            <span class="feature-icon">📝</span>
            <span class="feature-name">错题集</span>
          </div>
          <div class="feature-item">
            <span class="feature-icon">📦</span>
            <span class="feature-name">课后作业</span>
          </div>
          <div class="feature-item">
            <span class="feature-icon">⚙️</span>
            <span class="feature-name">帮助反馈</span>
          </div>
        </div>
      </div>

      <!-- 退出登录 -->
      <button class="logout-btn" @click="handleLogout">
        退出登录
      </button>
    </div>

    <!-- 教师风格选择弹窗 -->
    <transition name="fade">
      <div v-if="showTeacherStyle" class="modal-overlay" @click.self="showTeacherStyle = false">
        <div class="modal-content">
          <h3 class="modal-title">选择教师风格</h3>
          <div class="style-options">
            <div 
              class="style-option" 
              :class="{ active: userStore.settings.teacherStyle === 'default' }"
              @click="selectTeacherStyle('default')"
            >
              <span class="style-emoji">🙂</span>
              <div class="style-info">
                <span class="style-name">默认风格</span>
                <span class="style-desc">友好耐心，专业解答</span>
              </div>
              <span v-if="userStore.settings.teacherStyle === 'default'" class="style-check">✓</span>
            </div>
            <div 
              class="style-option" 
              :class="{ active: userStore.settings.teacherStyle === 'humorous' }"
              @click="selectTeacherStyle('humorous')"
            >
              <span class="style-emoji">😄</span>
              <div class="style-info">
                <span class="style-name">幽默风趣</span>
                <span class="style-desc">脱口秀风格，寓教于乐</span>
              </div>
              <span v-if="userStore.settings.teacherStyle === 'humorous'" class="style-check">✓</span>
            </div>
            <div 
              class="style-option" 
              :class="{ active: userStore.settings.teacherStyle === 'rigorous' }"
              @click="selectTeacherStyle('rigorous')"
            >
              <span class="style-emoji">👨‍🏫</span>
              <div class="style-info">
                <span class="style-name">严谨认真</span>
                <span class="style-desc">教授风格，系统专业</span>
              </div>
              <span v-if="userStore.settings.teacherStyle === 'rigorous'" class="style-check">✓</span>
            </div>
          </div>
          <button class="modal-close" @click="showTeacherStyle = false">确定</button>
        </div>
      </div>
    </transition>

    <BottomNav />
  </div>
</template>

<script setup>
import { computed, ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import Navbar from '../../components/layout/Navbar.vue'
import BottomNav from '../../components/layout/BottomNav.vue'
import XPProgress from '../../components/common/XPProgress.vue'
import { useUserStore } from '../../stores'

const router = useRouter()
const userStore = useUserStore()

const handleLogout = () => {
  userStore.logout()
  router.push('/login')
}

const showTeacherStyle = ref(false)

const teacherStyleText = computed(() => {
  const map = { default: '默认', humorous: '幽默风趣', rigorous: '严谨认真' }
  return map[userStore.settings.teacherStyle] || '默认'
})

const selectTeacherStyle = (style) => {
  userStore.settings.teacherStyle = style
  localStorage.setItem('teacherStyle', style)
}

// 我的大纲
const myOutlines = ref([])
const selectedOutline = ref(null)
const levelMap = { beginner: '入门', intermediate: '中级', advanced: '高级' }
const editingOutlineId = ref(null)
const editTitleValue = ref('')
const titleInput = ref(null)

const fetchOutlines = async () => {
  try {
    const token = localStorage.getItem('token') || ''
    const res = await fetch('/api/v1/outline/my', {
      headers: { Authorization: `Bearer ${token}` }
    })
    if (res.ok) myOutlines.value = await res.json()
  } catch (e) { /* 静默 */ }
}

const startEditTitle = (o) => {
  editingOutlineId.value = o.id
  editTitleValue.value = o.title
  nextTick(() => {
    const inputs = document.querySelectorAll('.oc-topic-input')
    if (inputs.length) inputs[inputs.length - 1]?.focus()
  })
}

const saveTitle = async (o) => {
  const newTitle = editTitleValue.value.trim()
  if (!newTitle || newTitle === o.title) {
    editingOutlineId.value = null
    return
  }
  try {
    const token = localStorage.getItem('token') || ''
    const res = await fetch(`/api/v1/outline/${o.id}/rename`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ title: newTitle })
    })
    if (res.ok) {
      o.title = newTitle
    }
  } catch (e) { /* ignore */ }
  editingOutlineId.value = null
}

// ─── 模块状态管理（异步生成课程） ───
const moduleStatusCache = ref({})  // { [outlineId]: { [moduleIndex]: status } }

const loadModuleStatuses = async (outlineId) => {
  if (moduleStatusCache.value[outlineId]) return
  const token = localStorage.getItem('token') || ''
  try {
    const res = await fetch(`/api/v1/ai/tutor/modules/${outlineId}`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    if (res.ok) {
      const data = await res.json()
      const statuses = {}
      for (const m of data.modules) {
        statuses[m.module_index] = {
          contentStatus: m.content_status,
          hasContent: m.has_content
        }
      }
      moduleStatusCache.value[outlineId] = statuses
    }
  } catch (e) { /* ignore */ }
}

const getModulesWithStatus = (outline) => {
  const mods = outline.modules_data || []
  const statuses = moduleStatusCache.value[outline.id] || {}
  return mods.map((m, i) => ({
    ...m,
    contentStatus: statuses[i + 1]?.contentStatus || 'pending'
  }))
}

const generateModuleForOutline = async (outlineId, moduleIndex) => {
  if (!moduleStatusCache.value[outlineId]) {
    moduleStatusCache.value[outlineId] = {}
  }
  const status = moduleStatusCache.value[outlineId]
  status[moduleIndex] = { contentStatus: 'generating', hasContent: false }
  moduleStatusCache.value = { ...moduleStatusCache.value }  // 触发响应

  const token = localStorage.getItem('token') || ''
  try {
    const res = await fetch('/api/v1/ai/tutor/generate-module', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({
        outline_id: outlineId,
        module_index: moduleIndex,
        teacher_style: 'default'
      })
    })
    const data = await res.json()
    if (data.stream_url) {
      const evtSource = new EventSource(`http://127.0.0.1:8000${data.stream_url}?token=${encodeURIComponent(token)}`)
      evtSource.addEventListener('completed', () => {
        status[moduleIndex] = { contentStatus: 'completed', hasContent: true }
        moduleStatusCache.value = { ...moduleStatusCache.value }
        evtSource.close()
      })
      evtSource.addEventListener('error', () => {
        status[moduleIndex] = { contentStatus: 'failed', hasContent: false }
        moduleStatusCache.value = { ...moduleStatusCache.value }
        evtSource.close()
      })
    }
  } catch (e) {
    status[moduleIndex] = { contentStatus: 'failed', hasContent: false }
    moduleStatusCache.value = { ...moduleStatusCache.value }
  }
}

// 展开大纲时加载模块状态
const handleSelectOutline = (o) => {
  if (selectedOutline.value?.id === o.id) {
    selectedOutline.value = null
  } else {
    selectedOutline.value = o
    loadModuleStatuses(o.id)
  }
}

const formatDate = (iso) => {
  if (!iso) return ''
  const d = new Date(iso)
  return `${d.getMonth()+1}/${d.getDate()}`
}

onMounted(() => {
  fetchOutlines()
})

const fontSizeText = computed(() => {
  const map = { small: '小', medium: '中', large: '大' }
  return map[userStore.settings.fontSize] || '中'
})

const getSubjectIcon = (topic) => {
  if (topic.includes('Python')) return '🐍'
  if (topic.includes('JavaScript')) return '💛'
  if (topic.includes('Vue')) return '💚'
  if (topic.includes('数据结构')) return '📊'
  if (topic.includes('算法')) return '🧮'
  return '📚'
}

const getScoreClass = (score) => {
  if (score >= 90) return 'excellent'
  if (score >= 80) return 'good'
  if (score >= 70) return 'ok'
  return 'low'
}
</script>

<style scoped>
.profile-page {
  min-height: 100vh;
  padding-top: 64px;
  padding-bottom: 80px;
  background: var(--bg-primary);
}

.profile-container {
  max-width: 600px;
  margin: 0 auto;
  padding: 1.5rem;
}

/* Profile Header */
.profile-header {
  display: flex;
  gap: 1.5rem;
  padding: 1.5rem;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  margin-bottom: 1rem;
}

.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.avatar-wrapper {
  position: relative;
}

.avatar-main {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  border-radius: 50%;
  font-size: 2.5rem;
}

.avatar-edit {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-secondary);
  border: 2px solid var(--bg-card);
  border-radius: 50%;
  font-size: 0.75rem;
  cursor: pointer;
}

.level-badge {
  padding: 0.25rem 0.75rem;
  background: linear-gradient(135deg, #ffd700, #ffa500);
  color: #1a1a2e;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 700;
}

.profile-info {
  flex: 1;
}

.profile-info h1 {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
}

.profile-meta {
  font-size: 0.875rem;
  color: var(--text-muted);
  margin-bottom: 1rem;
}

.dot {
  margin: 0 0.5rem;
}

.profile-stats {
  display: flex;
  gap: 1.5rem;
}

.stat {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 1.25rem;
  font-weight: 700;
}

.stat-label {
  font-size: 0.625rem;
  color: var(--text-muted);
}

/* XP Card */
.xp-card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 1.5rem;
  margin-bottom: 1rem;
  border: 1px solid var(--border);
}

.xp-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 1rem;
  font-size: 0.875rem;
}

.xp-hint {
  color: var(--text-muted);
}

/* History Section */
.history-section {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 1.5rem;
  margin-bottom: 1rem;
  border: 1px solid var(--border);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.section-header h2 {
  font-size: 1.125rem;
}

.view-all {
  font-size: 0.875rem;
  color: var(--primary);
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem;
  background: var(--bg-secondary);
  border-radius: var(--radius);
}

.history-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-primary);
  border-radius: var(--radius);
  font-size: 1.25rem;
}

.history-info {
  flex: 1;
}

.history-info h4 {
  font-size: 0.9375rem;
  margin-bottom: 0.125rem;
}

.history-info p {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.history-score {
  text-align: right;
}

.score-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 700;
  margin-bottom: 0.25rem;
}

.score-badge.excellent {
  background: rgba(16, 185, 129, 0.2);
  color: var(--success);
}

.score-badge.good {
  background: rgba(59, 130, 246, 0.2);
  color: var(--info);
}

.score-badge.ok {
  background: rgba(245, 158, 11, 0.2);
  color: var(--warning);
}

.score-badge.low {
  background: rgba(239, 68, 68, 0.2);
  color: var(--danger);
}

.xp-badge {
  font-size: 0.625rem;
  color: var(--warning);
}

/* Settings */
.settings-section {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 1.5rem;
  margin-bottom: 1rem;
  border: 1px solid var(--border);
}

.settings-section h2 {
  font-size: 1.125rem;
  margin-bottom: 1rem;
}

.settings-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.setting-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: var(--bg-secondary);
  border-radius: var(--radius);
  cursor: pointer;
  transition: all 0.3s ease;
}

.setting-item:hover {
  background: rgba(102, 126, 234, 0.1);
}

.setting-icon {
  font-size: 1.25rem;
}

.setting-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.setting-name {
  font-size: 0.9375rem;
  font-weight: 500;
}

.setting-value {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.setting-arrow {
  color: var(--text-muted);
}

/* Toggle */
.toggle {
  position: relative;
  width: 48px;
  height: 28px;
}

.toggle input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  cursor: pointer;
  inset: 0;
  background: var(--border);
  border-radius: 14px;
  transition: 0.3s;
}

.toggle-slider::before {
  content: '';
  position: absolute;
  width: 20px;
  height: 20px;
  left: 4px;
  bottom: 4px;
  background: white;
  border-radius: 50%;
  transition: 0.3s;
}

.toggle input:checked + .toggle-slider {
  background: var(--primary);
}

.toggle input:checked + .toggle-slider::before {
  transform: translateX(20px);
}

/* Features */
.feature-section {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 1.5rem;
  margin-bottom: 1rem;
  border: 1px solid var(--border);
}

.feature-section h2 {
  font-size: 1.125rem;
  margin-bottom: 1rem;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.75rem;
}

.feature-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem;
  background: var(--bg-secondary);
  border-radius: var(--radius);
  cursor: pointer;
  transition: all 0.3s ease;
}

.feature-item:hover {
  background: rgba(102, 126, 234, 0.1);
  transform: translateY(-2px);
}

.feature-icon {
  font-size: 1.5rem;
}

.feature-name {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

/* Logout */
.logout-btn {
  width: 100%;
  padding: 1rem;
  background: transparent;
  border: 1px solid var(--danger);
  border-radius: var(--radius);
  color: var(--danger);
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.logout-btn:hover {
  background: rgba(239, 68, 68, 0.1);
}

/* 教师风格弹窗 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.modal-content {
  background: white;
  border-radius: 20px;
  padding: 28px 24px;
  width: 100%;
  max-width: 360px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

.modal-title {
  font-size: 18px;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 20px;
  text-align: center;
}

.style-options {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
}

.style-option {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  border-radius: 14px;
  border: 2px solid #eee;
  cursor: pointer;
  transition: all 0.2s;
}

.style-option:hover {
  border-color: #667eea;
  background: #f8f9ff;
}

.style-option.active {
  border-color: #667eea;
  background: linear-gradient(135deg, #f0f3ff, #e8ecff);
}

.style-emoji {
  font-size: 28px;
  flex-shrink: 0;
}

.style-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.style-name {
  font-size: 15px;
  font-weight: 600;
  color: #1a1a2e;
}

.style-desc {
  font-size: 12px;
  color: #999;
}

.style-check {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #667eea;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  flex-shrink: 0;
}

.modal-close {
  width: 100%;
  padding: 14px;
  border: none;
  border-radius: 14px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}

.modal-close:hover {
  opacity: 0.9;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 我的大纲 */
.outlines-section {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 1.5rem;
  margin-bottom: 1rem;
  border: 1px solid var(--border);
}

.outline-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.outline-card {
  background: var(--bg-secondary);
  border-radius: var(--radius);
  padding: 14px 16px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.outline-card:hover {
  border-color: #667eea;
  background: rgba(102, 126, 234, 0.05);
}

.outline-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.oc-topic {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.oc-topic-editable {
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 4px;
  transition: all 0.15s;
}

.oc-topic-editable:hover {
  background: rgba(102, 126, 234, 0.12);
  color: #667eea;
}

.oc-topic-input {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  background: var(--bg-card);
  border: 1px solid #667eea;
  border-radius: 4px;
  padding: 2px 6px;
  outline: none;
  flex: 1;
  min-width: 0;
}

.oc-title {
  font-size: 12px;
  color: var(--text-muted);
  display: block;
  margin-bottom: 6px;
}

.oc-meta {
  display: flex;
  gap: 12px;
  font-size: 11px;
  color: var(--text-muted);
}

.outline-modules {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.outline-module {
  padding: 8px 0;
}

.om-header {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.om-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  margin-right: 8px;
}

.om-dur {
  font-size: 11px;
  color: var(--text-muted);
}

.om-status {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 10px;
  white-space: nowrap;
}

.om-status.completed {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
}

.om-status.generating {
  background: rgba(234, 179, 8, 0.15);
  color: #eab308;
}

.om-status.failed {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.om-gen-btn {
  padding: 3px 10px;
  border-radius: 6px;
  background: rgba(102, 126, 234, 0.15);
  color: #667eea;
  border: 1px solid rgba(102, 126, 234, 0.3);
  font-size: 11px;
  cursor: pointer;
  white-space: nowrap;
}

.om-gen-btn:hover {
  background: rgba(102, 126, 234, 0.3);
}

.om-points {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 4px;
}

.om-point {
  font-size: 11px;
  padding: 2px 8px;
  background: rgba(102, 126, 234, 0.06);
  border-radius: 6px;
  color: var(--text-secondary);
}
</style>
