<template>
  <div class="classroom-page" :class="{ 'dark-mode': true }">
    <!-- 顶部状态栏 -->
    <header class="class-header">
      <div class="class-info">
        <button class="back-btn" @click="confirmExit">←</button>
        <div class="class-title">
          <h1>{{ currentOutline?.title || currentOutline?.topic || 'AI课堂' }}</h1>
          <div class="class-progress" v-if="activeModuleIndex > 0">
            <div class="progress-text">模块{{ activeModuleIndex }}：{{ activeModuleName || '' }} · {{ teacherStyle === 'humorous' ? '幽默' : teacherStyle === 'rigorous' ? '严谨' : '默认' }}风格</div>
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: progress + '%' }"></div>
            </div>
          </div>
        </div>
      </div>
      <div class="class-stats">
        <div class="stat">
          <span class="stat-icon">⏱️</span>
          <span class="stat-value">{{ formatTime(remainingTime) }}</span>
        </div>
        <div class="stat">
          <span class="stat-icon">🔥</span>
          <span class="stat-value">{{ currentXP }} XP</span>
        </div>
        <button class="pause-btn" @click="togglePause">
          {{ isPaused ? '▶' : '⏸' }}
        </button>
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="classroom-main">
      <!-- 左侧：模块导航栏 -->
      <aside class="module-sidebar" :class="{ collapsed: sidebarCollapsed }">
        <div class="sidebar-toggle" @click="sidebarCollapsed = !sidebarCollapsed" :title="sidebarCollapsed ? '展开' : '收起'">
          {{ sidebarCollapsed ? '▶' : '◀' }}
        </div>
        <div class="sidebar-header" v-if="!sidebarCollapsed">
          <h3>📚 课程模块</h3>
          <span class="sidebar-subtitle">{{ currentOutline?.title || '未选择大纲' }}</span>
        </div>
        <div class="module-list" v-if="!sidebarCollapsed">
          <div
            v-for="mod in moduleList"
            :key="mod.module_index"
            class="module-item"
            :class="{
              active: activeModuleIndex === mod.module_index,
              generated: mod.has_content,
              pending: !mod.has_content && mod.content_status !== 'generating',
              generating: mod.content_status === 'generating',
              completed: teachingProgress?.completed_modules?.includes(mod.module_index)
            }"
            @click="selectModule(mod)"
          >
            <div class="module-num" v-if="teachingProgress?.completed_modules?.includes(mod.module_index)">✅</div>
            <div class="module-num" v-else-if="mod.content_status === 'generating'">⏳</div>
            <div class="module-num" v-else>{{ mod.module_index }}</div>
            <div class="module-info">
              <div class="module-name">{{ cleanModuleName(mod.name) }}</div>
              <div class="module-meta">{{ mod.duration }}分钟 · {{ (mod.keyPoints || []).length }}个知识点</div>
            </div>
            <div class="module-status">
              <template v-if="mod.content_status === 'generating'">
                <span class="status-badge generating">生成中</span>
              </template>
              <template v-else-if="mod.has_content">
                <button
                  v-if="activeModuleIndex !== mod.module_index"
                  class="mini-start-btn"
                  @click.stop="startModule(mod)"
                >进入</button>
                <span v-else class="status-badge teaching">讲授中</span>
              </template>
              <template v-else>
                <button
                  class="mini-gen-btn"
                  @click.stop="generateModuleContent(mod)"
                  :disabled="mod.content_status === 'generating'"
                >生成课程</button>
              </template>
            </div>
          </div>
        </div>
        <div class="module-list-mini" v-else>
          <div
            v-for="mod in moduleList"
            :key="mod.module_index"
            class="module-dot"
            :class="{ active: activeModuleIndex === mod.module_index, completed: teachingProgress?.completed_modules?.includes(mod.module_index), generated: mod.has_content }"
            @click="selectModule(mod)"
            :title="cleanModuleName(mod.name)"
          ></div>
        </div>
      </aside>

      <!-- 中间：AI讲授区 -->
      <div class="ai-section">
        <!-- AI主控 -->
        <div class="ai-teacher-card">
          <div class="ai-avatar-section">
            <div class="ai-avatar-main" :class="{ speaking: isSpeaking }">
              {{ currentAIExpression }}
            </div>
            <div class="ai-label">
              <span class="ai-role">🤖 AI主控</span>
              <span class="ai-status" :class="{ speaking: isSpeaking }">
                {{ isSpeaking ? '讲授中...' : '等待中' }}
              </span>
            </div>
            <!-- 倍速控制 -->
            <div class="speed-control">
              <button
                v-for="s in speeds"
                :key="s"
                class="speed-btn"
                :class="{ active: currentSpeed === s }"
                @click="setSpeed(s)"
                :title="`${s}x 倍速`"
              >{{ s }}x</button>
              <button
                class="speed-btn voice-btn"
                :class="{ active: voiceEnabled }"
                @click="voiceEnabled = !voiceEnabled"
                :title="voiceEnabled ? '关闭语音' : '开启语音'"
              >{{ voiceEnabled ? '🔊' : '🔇' }}</button>
            </div>
          </div>
          <div class="ai-content">
            <!-- 答题模式 -->
            <div v-if="showQuestion">
              <div class="question-area">
                <div class="question-card">
                <div class="question-type">{{ currentQuestion.type === 'choice' ? '选择题' : '填空题' }}</div>
                <div class="question-text">{{ currentQuestion.content }}</div>
                <!-- 选择题选项 -->
                <div class="options" v-if="currentQuestion.type === 'choice'">
                  <button 
                    v-for="(opt, index) in currentQuestion.options" 
                    :key="index"
                    class="option-btn"
                    :class="{ selected: selectedAnswer === index, correct: showResult && index === currentQuestion.correctAnswer, wrong: showResult && selectedAnswer === index && index !== currentQuestion.correctAnswer }"
                    @click="selectAnswer(index)"
                    :disabled="showResult"
                  >
                    <span class="option-letter">{{ ['A', 'B', 'C', 'D'][index] }}</span>
                    <span class="option-text">{{ opt }}</span>
                  </button>
                </div>
                <!-- 填空题输入 -->
                <div class="fill-input" v-else>
                  <input 
                    v-model="fillAnswer" 
                    type="text" 
                    placeholder="请输入答案..."
                    class="fill-input-field"
                    :disabled="showResult"
                  />
                  <button class="btn btn-primary" @click="submitFillAnswer" :disabled="showResult || !fillAnswer">
                    提交
                  </button>
                </div>
                <!-- 结果反馈 -->
                <div class="result-feedback" v-if="showResult">
                  <div class="feedback-icon">{{ isCorrect ? '✅' : '❌' }}</div>
                  <div class="feedback-text">{{ isCorrect ? '回答正确！' : '回答错误' }}</div>
                  <div class="feedback-explain">{{ currentQuestion.explanation }}</div>
                  <div class="xp-reward" v-if="isCorrect">+{{ questionXP }} XP</div>
                </div>
                <button 
                  v-if="showResult" 
                  class="btn btn-primary continue-btn"
                  @click="nextQuestion"
                >
                  继续学习 →
                </button>
              </div>
            </div>
          </div>

          <!-- 非答题模式：历史回看 -->
          <div v-else-if="viewingHistoryPage >= 0" class="content-text history-view">
            <div class="history-banner">
              <span>📖 正在回看第 {{ viewingHistoryPage + 1 }}/{{ lecturePages.length }} 页</span>
              <button class="back-to-live-btn" @click="goToLivePage">返回直播 →</button>
            </div>
            <p>{{ lecturePages[viewingHistoryPage]?.text || '' }}</p>
          </div>

          <!-- 非答题模式：当前直播讲授 -->
          <div v-else class="content-text lecture-live">
            <p v-if="lectureDisplay">{{ lectureDisplay }}<span class="typing-cursor" v-if="isSpeaking">|</span></p>
            <p v-else-if="isSpeaking" class="preparing-text">⏳ AI讲师准备中...</p>
            <p v-else-if="!currentOutline" class="waiting-text">请先从下方选择大纲进入课堂</p>
            <p v-else class="waiting-text">请在左侧选择课程模块开始学习</p>
          </div>

          <!-- 翻页导航（非答题模式下显示） -->
          <div class="page-nav" v-if="!showQuestion && (lecturePages.length > 0 || viewingHistoryPage >= 0)">
            <button class="page-nav-btn" @click="goToPrevPage" :disabled="lecturePages.length === 0">
              ◀ 上一页
            </button>
            <span class="page-indicator" v-if="viewingHistoryPage >= 0">
              第 {{ viewingHistoryPage + 1 }} / {{ lecturePages.length }} 页
            </span>
            <span class="page-indicator" v-else>
              讲授中 · 已存档 {{ lecturePages.length }} 页
            </span>
            <button class="page-nav-btn" @click="goToNextPage" :disabled="viewingHistoryPage >= lecturePages.length - 1">
              下一页 ▶
            </button>
          </div>
        </div>
        </div>

        <!-- 虚拟白板 -->
        <div class="whiteboard" :class="{ expanded: whiteboardExpanded }">
          <div class="whiteboard-header">
            <span>📝 知识板书（实时）</span>
            <button @click="whiteboardExpanded = !whiteboardExpanded">
              {{ whiteboardExpanded ? '收起' : '展开' }}
            </button>
          </div>
          <div class="whiteboard-content">
            <pre class="code-block" v-if="extractedCode">{{ extractedCode }}</pre>
            <div class="knowledge-points" v-else-if="whiteboardPoints.length > 0">
              <div class="point-item" v-for="(point, i) in whiteboardPoints" :key="point._key || i">
                <span class="point-num">{{ i + 1 }}</span>
                <span class="point-text">{{ point.text || point }}</span>
              </div>
            </div>
            <div class="whiteboard-empty" v-else>
              <p>📋 AI讲师正在整理知识板书...</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：学伴和工具 -->
      <div class="tools-section">
        <!-- 虚拟形象 -->
        <div class="avatar-widget">
          <div class="avatar-display">
            <div class="avatar-img">{{ userStore.userInfo.avatar }}</div>
            <div class="avatar-mood">{{ moodEmoji }}</div>
          </div>
          <div class="avatar-info">
            <span class="avatar-level">Lv.{{ userStore.userInfo.level }}</span>
            <XPProgress 
              :current="userStore.userInfo.xp" 
              :total="userStore.userInfo.xpToNextLevel"
              :level="userStore.userInfo.level"
              :showNext="false"
            />
          </div>
        </div>

        <!-- AI学伴 - 增强版 -->
        <div class="classmates enhanced">
          <div class="classmates-header">
            <h4>🤝 AI学伴</h4>
            <span class="classmates-count">{{ classmates.length }} 人在线</span>
          </div>
          
          <!-- 学伴消息区域 -->
          <div class="classmate-messages" ref="messageContainer">
            <div 
              v-for="(msg, idx) in companionMessages" 
              :key="idx"
              class="message-bubble"
              :class="[msg.sender, msg.type]"
            >
              <div class="msg-avatar">{{ msg.avatar }}</div>
              <div class="msg-content">
                <div class="msg-sender">{{ msg.senderName }}</div>
                <div class="msg-text">{{ msg.text }}</div>
                <div class="msg-time">{{ msg.time }}</div>
              </div>
            </div>
          </div>

          <!-- 学伴列表 -->
          <div class="classmate-list">
            <div 
              v-for="mate in classmates" 
              :key="mate.id"
              class="classmate-card"
              :class="[mate.type, mate.status]"
              @click="toggleCompanionAction(mate)"
            >
              <div class="classmate-avatar-wrapper">
                <div class="classmate-avatar">{{ mate.avatar }}</div>
                <div class="classmate-status-dot" :class="mate.status"></div>
              </div>
              <div class="classmate-info">
                <span class="classmate-name">{{ mate.nickname }}</span>
                <span class="classmate-type">{{ mate.type === 'active' ? '活跃型' : '基础薄弱型' }}</span>
              </div>
              <div class="classmate-action">
                <span v-if="mate.isAnswering" class="answering-indicator">✍️ 答题中...</span>
                <span v-else-if="mate.lastAction" class="last-action">{{ mate.lastAction }}</span>
              </div>
            </div>
          </div>

          <!-- 学伴互动按钮 -->
          <div class="companion-actions">
            <button class="action-btn" @click="companionAskQuestion" title="学伴提问">
              💬 向学伴提问
            </button>
            <button class="action-btn" @click="companionDiscuss" title="发起讨论">
              💡 发起讨论
            </button>
          </div>
        </div>

        <!-- 快捷操作 -->
        <div class="quick-tools">
          <button class="tool-btn" @click="askQuestion" title="向AI助教提问">
            ❓ 提问
          </button>
          <button class="tool-btn" @click="triggerEggDrop" title="随机彩蛋">
            🥚 彩蛋
          </button>
          <button class="tool-btn" @click="showHint" title="获取提示">
            💡 提示
          </button>
        </div>
      </div>
    </main>

    <!-- 彩蛋弹窗 -->
    <transition name="egg">
      <div class="egg-modal" v-if="showEgg" @click="showEgg = false">
        <div class="egg-content">
          <div class="egg-icon">{{ currentEgg.title }}</div>
          <p class="egg-text">{{ currentEgg.content }}</p>
          <div class="egg-xp">+{{ currentEgg.xp }} XP</div>
        </div>
      </div>
    </transition>

    <!-- 抢答模式 -->
    <transition name="rush-modal-anim">
      <div class="rush-modal" v-if="showRush" @click.self="rushResult || (rushAnswered = false)">
        <div class="rush-content" :class="{ answered: rushAnswered, success: rushResult === 'success', fail: rushResult === 'fail', timeout: rushResult === 'timeout' }">
          <!-- 正常状态 -->
          <div v-if="!rushResult" class="rush-normal">
            <div class="rush-header">
              <span class="rush-badge">⚡ 抢答时间</span>
              <span class="rush-countdown" :class="{ urgent: rushCountdown <= 3 }">
                {{ rushCountdown }}s
              </span>
            </div>
            <div class="rush-question">{{ rushQuestion }}</div>
            <button class="rush-btn" @click="rushAnswer" :disabled="rushAnswered">
              <span class="rush-btn-text">⚡ 抢答！</span>
              <span class="rush-btn-particles"></span>
            </button>
          </div>
          
          <!-- 成功状态 -->
          <div v-else-if="rushResult === 'success'" class="rush-result">
            <div class="rush-result-icon success-icon">🎉</div>
            <div class="rush-result-text">抢答成功！</div>
            <div class="rush-xp-gain">+20 XP</div>
            <div class="rush-particles">
              <span v-for="i in 12" :key="i" class="particle"></span>
            </div>
          </div>
          
          <!-- 失败状态 -->
          <div v-else-if="rushResult === 'fail'" class="rush-result">
            <div class="rush-result-icon fail-icon">😢</div>
            <div class="rush-result-text">抢答失败</div>
            <div class="rush-result-hint">下次更快一点哦~</div>
          </div>
          
          <!-- 超时状态 -->
          <div v-else-if="rushResult === 'timeout'" class="rush-result">
            <div class="rush-result-icon timeout-icon">⏰</div>
            <div class="rush-result-text">抢答超时</div>
            <div class="rush-result-hint">机会被其他人抢走啦~</div>
          </div>
        </div>
      </div>
    </transition>

    <!-- 底部导航 -->
    <BottomNav />
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '../../stores'
import BottomNav from '../../components/layout/BottomNav.vue'
import XPProgress from '../../components/common/XPProgress.vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

// 状态
const isPaused = ref(false)
const isSpeaking = ref(false)
const currentModule = ref(0)
const totalModules = ref(3)
const currentXP = ref(45)
const remainingTime = ref(42 * 60)

// 大纲数据
const currentOutline = ref(null)
const loadingOutline = ref(true)

// 教师风格
const teacherStyle = computed(() => userStore.settings?.teacherStyle || 'default')

// 加载大纲
const loadOutline = async () => {
  const outlineId = route.query.outline_id
  if (!outlineId) {
    loadingOutline.value = false
    return
  }
  try {
    const token = localStorage.getItem('token') || ''
    const res = await fetch('/api/v1/outline/my', {
      headers: { Authorization: `Bearer ${token}` }
    })
    if (res.ok) {
      const all = await res.json()
      currentOutline.value = all.find(o => o.id == outlineId) || null
      if (currentOutline.value) {
        const mods = currentOutline.value.modules_data || []
        totalModules.value = mods.length || 3
      }
    }
  } catch (e) {
    console.warn('加载大纲失败:', e)
  }
  loadingOutline.value = false
  // 大纲加载后自动加载模块列表
  if (currentOutline.value) {
    loadModuleList()
  }
}

// ============ 模块侧边栏 ============
const sidebarCollapsed = ref(false)
const moduleList = ref([])
const activeModuleIndex = ref(0)
const activeModuleName = ref('')
const teachingProgress = ref(null)

const loadModuleList = async () => {
  if (!currentOutline.value) return
  const outlineId = currentOutline.value.id
  const token = localStorage.getItem('token') || ''
  try {
    const res = await fetch(`/api/v1/ai/tutor/modules/${outlineId}`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    if (res.ok) {
      const data = await res.json()
      moduleList.value = data.modules || []
      teachingProgress.value = data.teaching_progress
      // 恢复上次进度
      if (teachingProgress.value) {
        activeModuleIndex.value = teachingProgress.value.current_module || 1
        const mod = moduleList.value.find(m => m.module_index === activeModuleIndex.value)
        if (mod) activeModuleName.value = cleanModuleName(mod.name)
      }
    }
  } catch (e) { console.warn('加载模块列表失败:', e) }
}

// 清洗模块名称，去掉 AI 可能附加的时间信息
const cleanModuleName = (name) => {
  if (!name) return ''
  // 去掉各种格式的时间后缀：(X小时)、[X分钟]、X小时 等
  return name
    .replace(/\s*[(（]?\d+(?:\.\d+)?\s*(?:小时|分钟|h|min|H|MIN)[)）]?/g, '')
    .trim()
}

const selectModule = (mod) => {
  activeModuleIndex.value = mod.module_index
  activeModuleName.value = cleanModuleName(mod.name)
}

// 生成单个模块的课程内容
const generateModuleContent = async (mod) => {
  if (mod.content_status === 'generating' || mod.has_content) return
  mod.content_status = 'generating'
  const token = localStorage.getItem('token') || ''
  try {
    const res = await fetch('/api/v1/ai/tutor/generate-module', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({
        outline_id: currentOutline.value.id,
        module_index: mod.module_index,
        teacher_style: teacherStyle.value
      })
    })
    const data = await res.json()
    if (data.stream_url) {
      // 直连后端避免代理缓冲
      const evtSource = new EventSource(`http://127.0.0.1:8000${data.stream_url}?token=${encodeURIComponent(token)}`)
      evtSource.addEventListener('token', (e) => {
        try { /* token received, generation in progress */ } catch { /* ignore */ }
      })
      evtSource.addEventListener('completed', (e) => {
        try {
          const d = JSON.parse(e.data)
          if (d.module_index === mod.module_index) {
            mod.content_status = 'completed'
            mod.has_content = true
          }
        } catch { /* ignore */ }
        evtSource.close()
      })
      evtSource.addEventListener('error', () => {
        mod.content_status = 'failed'
        evtSource.close()
      })
    } else {
      mod.content_status = 'failed'
    }
  } catch (e) {
    mod.content_status = 'failed'
  }
}

// 开始模块教学
const startModule = async (mod) => {
  selectModule(mod)
  // 保存进度
  if (teachingProgress.value) {
    teachingProgress.value.current_module = mod.module_index
    teachingProgress.value.module_progress = 0
  }

  isSpeaking.value = true
  viewingHistoryPage.value = -1
  lectureDisplay.value = ''
  tokenBuffer.value = ''
  lecturePages.value = []
  whiteboardPoints.value = []
  allExtractedPointKeys.clear()
  extractedCode.value = ''
  lastSpokenEnd = 0
  sseStreamDone = false
  stopSpeaking()

  // 加载板书
  if (mod.keyPoints?.length) {
    whiteboardPoints.value = mod.keyPoints.map((p, i) => ({ text: p, _key: `mod_${i}` }))
  }

  const token = localStorage.getItem('token') || ''

  fetch('/api/v1/ai/tutor/teach', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify({
      outline_id: currentOutline.value.id,
      module_index: mod.module_index,
      message: '开始上课',
      teacher_style: teacherStyle.value
    })
  }).then(res => res.json()).then(data => {
    if (data.stream_url) {
      aiEventSource?.close()
      // ⚠️ 直连后端，避免 Vue 代理缓冲 SSE 流导致数据永不送达
      const sseUrl = `http://127.0.0.1:8000${data.stream_url}?token=${encodeURIComponent(token)}`
      aiEventSource = new EventSource(sseUrl)

      // 超时保护：15秒无事件则判定失败
      let sseTimer = setTimeout(() => {
        if (isSpeaking.value && !lectureDisplay.value) {
          sseStreamDone = false
          stopTyping()
          isSpeaking.value = false
          lectureDisplay.value = '❌ AI讲师响应超时，请重试'
        }
      }, 15000)

      aiEventSource.addEventListener('token', (e) => {
        clearTimeout(sseTimer)
        try { tokenBuffer.value += JSON.parse(e.data).token } catch { /* ignore */ }
      })

      aiEventSource.addEventListener('done', () => {
        clearTimeout(sseTimer)
        // 不立即结束：标记 SSE 完成，让打字机慢慢消耗完 buffer
        sseStreamDone = true
        aiEventSource.close()
      })

      aiEventSource.addEventListener('error', () => {
        clearTimeout(sseTimer)
        endTeachingSession()
      })

      startTyping()
    }
  }).catch(() => {
    endTeachingSession()
  })
}

// 更新模块进度
const updateProgress = async (moduleIndex, progress) => {
  const token = localStorage.getItem('token') || ''
  try {
    await fetch('/api/v1/ai/tutor/progress', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({
        outline_id: currentOutline.value.id,
        module_index: moduleIndex,
        progress: progress,
        completed: progress >= 100
      })
    })
    if (teachingProgress.value) {
      teachingProgress.value.module_progress = progress
    }
  } catch (e) { console.warn('进度更新失败:', e) }
}

// ============ 讲课系统中枢 ============
// SSE 流是否已结束（但打字机可能还在消耗 buffer）
let sseStreamDone = false
const speeds = [0.75, 1, 1.5, 2]
const currentSpeed = ref(1)
// 基准 ~4字/秒，给语音留出追赶空间
const BASE_BATCH_SIZE = 2
const BASE_INTERVAL = 500
const typingBatchSize = computed(() => Math.max(1, Math.round(BASE_BATCH_SIZE * currentSpeed.value)))
const typingIntervalMs = computed(() => Math.round(BASE_INTERVAL / currentSpeed.value))

// SSE 缓冲与打字机
const tokenBuffer = ref('')
const lectureDisplay = ref('')
const fullLecture = ref('')
let typingTimer = null

// 翻页系统
const pageCharLimit = ref(500)
const lecturePages = ref([])          // [{ text, keyPoints }]
const currentPageNum = ref(0)
const viewingHistoryPage = ref(-1)    // -1 = 直播模式, >=0 = 回看某页

// 动态白板
const whiteboardExpanded = ref(false)
const whiteboardPoints = ref([])
const extractedCode = ref('')
const allExtractedPointKeys = new Set()

// 向后兼容（保留旧引用，部分函数仍会检查 teachingContent）
const currentContentIndex = ref(0)
const teachingContent = reactive([])
const currentContent = computed(() => teachingContent[currentContentIndex.value] || lectureDisplay.value)

// ============ 打字机引擎 ============
const startTyping = () => {
  if (typingTimer) return
  typingTimer = setInterval(() => {
    if (isPaused.value) return
    if (tokenBuffer.value.length === 0) {
      // 缓冲区空 + SSE 已结束 → 真正结束课堂
      if (sseStreamDone) {
        endTeachingSession()
      }
      return
    }

    // 语音开启时，限制文字显示不超过语音进度 +1 句的缓冲
    if (voiceEnabled.value && window.speechSynthesis) {
      const fullText = lectureDisplay.value
      const spokenLeft = fullText.length - lastSpokenEnd
      // 语音还有超过 1.5 句（约 40 字）没读完 → 暂停出字，等语音追上
      if (spokenLeft > 40 && window.speechSynthesis.speaking) {
        return
      }
    }

    const batchSize = typingBatchSize.value
    const chunk = tokenBuffer.value.slice(0, batchSize)
    tokenBuffer.value = tokenBuffer.value.slice(batchSize)

    lectureDisplay.value += chunk
    fullLecture.value += chunk

    // TTS 语音：新句子写完就朗读
    speakNewSentences()

    // 检查翻页
    if (lectureDisplay.value.length >= pageCharLimit.value) {
      flushCurrentPage()
    }

    // 检查段落边界，触发板书提炼
    if (chunk.includes('\n\n') || chunk.includes('。\n') || lectureDisplay.value.endsWith('。')) {
      const points = extractKeyPoints(lectureDisplay.value)
      if (points.length > 0) {
        mergeWhiteboardPoints(points)
      }
      checkCodeBlock(lectureDisplay.value)
    }
  }, typingIntervalMs.value)
}

const stopTyping = () => {
  if (typingTimer) {
    clearInterval(typingTimer)
    typingTimer = null
  }
}

const endTeachingSession = () => {
  stopTyping()
  stopSpeaking()
  if (lectureDisplay.value.trim()) flushCurrentPage()
  isSpeaking.value = false
  sseStreamDone = false
  aiEventSource?.close()
  if (currentOutline.value && activeModuleIndex.value > 0) {
    updateProgress(activeModuleIndex.value, 80)
  }
}

const restartTypingWithNewSpeed = () => {
  stopTyping()
  if (isSpeaking.value && !isPaused.value) {
    startTyping()
  }
}

// ============ 翻页逻辑 ============
const flushCurrentPage = () => {
  if (!lectureDisplay.value.trim()) return

  const pageText = lectureDisplay.value
  const points = extractKeyPoints(pageText)

  lecturePages.value.push({ text: pageText, keyPoints: points })
  currentPageNum.value = lecturePages.value.length

  // 如果有新提炼的关键点，更新白板
  if (points.length > 0) {
    whiteboardPoints.value = points.map((p, i) => ({
      text: p,
      _key: `page_${currentPageNum.value}_${i}`
    }))
  }

  // 清空当前显示，开始新页
  lectureDisplay.value = ''
  lastSpokenEnd = 0  // 重置朗读位置，否则新页文字会被跳过
}

const goToPrevPage = () => {
  if (viewingHistoryPage.value === -1) {
    // 正在看直播，切到最后一页历史
    viewingHistoryPage.value = lecturePages.value.length - 1
  } else if (viewingHistoryPage.value > 0) {
    viewingHistoryPage.value--
  }
}

const goToNextPage = () => {
  if (viewingHistoryPage.value >= 0 && viewingHistoryPage.value < lecturePages.value.length - 1) {
    viewingHistoryPage.value++
  }
}

const goToLivePage = () => {
  viewingHistoryPage.value = -1
}

// ============ 板书提炼引擎 ============
const extractKeyPoints = (text) => {
  if (!text || text.length < 20) return []

  const sentences = text
    .replace(/\n+/g, '。')
    .split(/[。！？；;]/)
    .map(s => s.trim())
    .filter(s => s.length > 8 && s.length < 80)

  const keyMarkers = [
    '首先', '其次', '最后', '然后', '接着',
    '关键', '重要', '注意', '需要记住', '请记住',
    '总结', '总之', '概括', '核心',
    '就是', '指的是', '定义', '概念',
    '例如', '比如', '举例',
    '因此', '所以', '由此可见',
    '第一种', '第二种', '第一', '第二', '第1', '第2'
  ]

  // 优先提取含关键词的句子
  let points = sentences.filter(s =>
    keyMarkers.some(m => s.includes(m))
  )

  // 如果关键词提取不到足够内容，取前几个较长的句子
  if (points.length === 0) {
    points = sentences.filter(s => s.length > 12).slice(0, 3)
  }

  // 限制最多5条
  return points.slice(0, 5)
}

const mergeWhiteboardPoints = (newPoints) => {
  newPoints.forEach(p => {
    const key = p.trim().substring(0, 20)
    if (!allExtractedPointKeys.has(key)) {
      allExtractedPointKeys.add(key)
      whiteboardPoints.value = [
        ...whiteboardPoints.value.slice(-4),  // 保留最近4条
        { text: p.trim(), _key: key }
      ]
    }
  })
}

const checkCodeBlock = (text) => {
  // 检测markdown风格的代码块
  const codeMatch = text.match(/```[\s\S]*?```/)
  if (codeMatch) {
    extractedCode.value = codeMatch[0].replace(/```/g, '').trim()
  }
}

// ============ 倍速控制 ============
const setSpeed = (speed) => {
  currentSpeed.value = speed
  stopSpeaking()      // 停止当前语音，下句用新速率
  restartTypingWithNewSpeed()   // 重启打字机定时器
}

// ─── TTS 语音输出（链式播放，逐句朗读） ───
const voiceEnabled = ref(true)
let lastSpokenEnd = 0  // 记录已朗读到的位置
let ttsKeepAlive = null // Chrome 语音长句自动暂停的 keepalive 定时器

// 预加载 voices（Chrome 需要 onvoiceschanged 事件）
if (typeof window !== 'undefined' && window.speechSynthesis) {
  window.speechSynthesis.getVoices()
  window.speechSynthesis.onvoiceschanged = () => {
    window.speechSynthesis.getVoices()
  }
}

// 清洗文本中的 Markdown 格式字符，确保语音朗读干净自然
const cleanTextForSpeech = (text) => {
  return text
    .replace(/\*\*(.+?)\*\*/g, '$1')       // **加粗**
    .replace(/\*(.+?)\*/g, '$1')            // *斜体*
    .replace(/^#{1,6}\s+/gm, '')             // # 标题
    .replace(/^>\s+/gm, '')                   // > 引用
    .replace(/^[-*+]\s+/gm, '')              // - 列表标记
    .replace(/^\d+[.、]\s*/gm, '')            // 1. 有序列表
    .replace(/~~(.+?)~~/g, '$1')             // ~~删除线~~
    .replace(/`{1,3}[^`]*`{1,3}/g, '')      // `行内代码` 和 ```代码块```
    .replace(/[_~]{1,2}/g, '')               // 残留的 _ ~ 标记
    .replace(/\s+/g, ' ')                     // 多余空白合并
    .trim()
}

const speakNewSentences = () => {
  if (!voiceEnabled.value || !window.speechSynthesis) return
  // 正在播放中不排队，等 onend 自动链式触发下一句
  if (window.speechSynthesis.speaking) return

  const fullText = lectureDisplay.value
  if (lastSpokenEnd > fullText.length) lastSpokenEnd = 0

  // 找最近一个完整句子，逐句播放不跳过
  const match = fullText.slice(lastSpokenEnd).match(/[^。！？\n.!?]+[。！？\n.!?]+/g)
  if (!match || match.length === 0) return

  const rawSentence = match[0]
  // 朗读前清洗格式字符
  const sentence = cleanTextForSpeech(rawSentence)
  lastSpokenEnd += rawSentence.length
  if (!sentence) return  // 全是格式字符，跳过
  const utterance = new SpeechSynthesisUtterance(sentence)
  utterance.lang = 'zh-CN'
  // 语音速度与倍速同步（rate=1 为正常语速 ~5字/秒）
  utterance.rate = Math.max(0.5, currentSpeed.value)

  // 选择声音
  const voices = window.speechSynthesis.getVoices()
  const zhVoices = voices.filter(v => v.lang.startsWith('zh'))
  if (userStore.settings.voiceType === 'male' && zhVoices.length > 0) {
    const maleVoice = zhVoices.find(v =>
      v.name.toLowerCase().includes('male') ||
      v.name.includes('小明') ||
      v.name.includes('云扬')
    )
    if (maleVoice) utterance.voice = maleVoice
  } else if (zhVoices.length > 0) {
    utterance.voice = zhVoices[0]
  }
  utterance.pitch = userStore.settings.voiceType === 'male' ? 0.8 : 1.2

  // Chrome keepalive：防止长句（>15s）自动暂停
  utterance.onstart = () => {
    if (ttsKeepAlive) clearInterval(ttsKeepAlive)
    ttsKeepAlive = setInterval(() => {
      if (window.speechSynthesis.paused) {
        window.speechSynthesis.resume()
      }
    }, 5000)
  }

  // 链式播放：当前句子播完 → 立即播放下一句
  utterance.onend = () => {
    if (ttsKeepAlive) { clearInterval(ttsKeepAlive); ttsKeepAlive = null }
    if (voiceEnabled.value) {
      setTimeout(() => speakNewSentences(), 100)
    }
  }

  utterance.onerror = (e) => {
    if (ttsKeepAlive) { clearInterval(ttsKeepAlive); ttsKeepAlive = null }
    // "canceled" 是正常停止，不需要重试
    if (e.error !== 'canceled' && voiceEnabled.value) {
      setTimeout(() => speakNewSentences(), 200)
    }
  }

  window.speechSynthesis.speak(utterance)
}

// 停止语音输出
const stopSpeaking = () => {
  if (window.speechSynthesis) {
    window.speechSynthesis.cancel()
    if (ttsKeepAlive) { clearInterval(ttsKeepAlive); ttsKeepAlive = null }
  }
}

// AI表情
const expressions = ['🤖', '😊', '🤔', '😮']
const currentAIExpression = computed(() => {
  if (isSpeaking.value) return '🤖'
  if (showQuestion.value) return '🤔'
  return '😊'
})

// 进度（基于教学进度数据）
const progress = computed(() => {
  if (teachingProgress.value) {
    const total = moduleList.value.length || 1
    const completed = (teachingProgress.value.completed_modules || []).length
    return (completed / total) * 100
  }
  return 0
})

// 答题相关
const showQuestion = ref(false)
const currentQuestion = ref(null)
const selectedAnswer = ref(null)
const fillAnswer = ref('')
const showResult = ref(false)
const isCorrect = ref(false)
const questionXP = ref(10)

// 学伴
const classmates = ref([])

// 学伴消息
const companionMessages = ref([
  { sender: 'system', senderName: '系统', avatar: '📢', text: '欢迎来到Python基础语法课堂！', time: '09:00', type: 'system' },
  { sender: 'mate1', senderName: '小乐', avatar: '😎', text: '大家好！今天一起学习Python～', time: '09:01', type: 'chat' },
  { sender: 'mate2', senderName: '小困', avatar: '😵', text: '变量名到底能不能用数字开头啊...', time: '09:02', type: 'chat' }
])

const messageContainer = ref(null)

// 用户表情
const moodEmoji = computed(() => {
  if (showQuestion.value) {
    return isCorrect.value ? '😄' : '🤔'
  }
  return '😊'
})

// 学伴互动方法
const toggleCompanionAction = (mate) => {
  alert(`🤝 ${mate.nickname} 的状态：${mate.status === 'online' ? '在线' : '离线'}\n点击可以与学伴互动！`)
}

const companionAskQuestion = () => {
  const question = prompt('请输入你想向学伴提问的问题：')
  if (question && question.trim()) {
    const now = new Date()
    const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`
    
    // 添加用户消息
    companionMessages.value.push({
      sender: 'user',
      senderName: '我',
      avatar: userStore.userInfo.avatar,
      text: question,
      time: timeStr,
      type: 'chat'
    })
    
    // 模拟学伴回复
    setTimeout(() => {
      const responses = [
        '这个问题问得好！让我想想...',
        '我觉得应该是这样的...',
        '我之前也遇到过类似的问题！',
        '可以试试看用 print() 函数输出一下～'
      ]
      const randomResponse = responses[Math.floor(Math.random() * responses.length)]
      const responseTime = new Date()
      const responseTimeStr = `${responseTime.getHours().toString().padStart(2, '0')}:${responseTime.getMinutes().toString().padStart(2, '0')}`
      
      companionMessages.value.push({
        sender: 'mate1',
        senderName: '小乐',
        avatar: '😎',
        text: randomResponse,
        time: responseTimeStr,
        type: 'chat'
      })
      
      // 自动滚动到底部
      if (messageContainer.value) {
        setTimeout(() => {
          messageContainer.value.scrollTop = messageContainer.value.scrollHeight
        }, 100)
      }
    }, 1500)
  }
}

const companionDiscuss = () => {
  const topic = prompt('请输入你想讨论的话题：')
  if (topic && topic.trim()) {
    const now = new Date()
    const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`
    
    companionMessages.value.push({
      sender: 'system',
      senderName: '讨论',
      avatar: '💡',
      text: `发起了关于"${topic}"的讨论`,
      time: timeStr,
      type: 'system'
    })
    
    // 学伴参与讨论
    setTimeout(() => {
      const discussResponses = [
        '我觉得这个话题很有意思！',
        '同意！我也这么认为',
        '有没有其他的理解方式呢？'
      ]
      const randomResponse = discussResponses[Math.floor(Math.random() * discussResponses.length)]
      const responseTime = new Date()
      const responseTimeStr = `${responseTime.getHours().toString().padStart(2, '0')}:${responseTime.getMinutes().toString().padStart(2, '0')}`
      
      companionMessages.value.push({
        sender: 'mate2',
        senderName: '小困',
        avatar: '😵',
        text: randomResponse,
        time: responseTimeStr,
        type: 'chat'
      })
      
      if (messageContainer.value) {
        setTimeout(() => {
          messageContainer.value.scrollTop = messageContainer.value.scrollHeight
        }, 100)
      }
    }, 2000)
  }
}

// 彩蛋
const showEgg = ref(false)
const currentEgg = ref({ title: '💡', content: '', xp: 0 })

// 抢答
const showRush = ref(false)
const rushQuestion = ref('')
const rushCountdown = ref(10)
const rushAnswered = ref(false)
const rushResult = ref(null) // 'success' | 'fail' | 'timeout'
let rushTimer = null
let rushCountdownTimer = null

// 抢答
const startRushAnswer = () => {
  showRush.value = true
  rushQuestion.value = 'Python中 print() 函数的作用是什么？'
  rushAnswered.value = false
  rushResult.value = null
  rushCountdown.value = 10
  
  // 倒计时
  rushCountdownTimer = setInterval(() => {
    rushCountdown.value--
    if (rushCountdown.value <= 0) {
      clearInterval(rushCountdownTimer)
      if (!rushAnswered.value) {
        rushResult.value = 'timeout'
        setTimeout(() => {
          showRush.value = false
        }, 2000)
      }
    }
  }, 1000)
}

const rushAnswer = () => {
  if (rushAnswered.value) return
  rushAnswered.value = true
  clearInterval(rushCountdownTimer)
  
  // 随机判定成功或失败（实际应该由后端判定）
  const success = Math.random() > 0.3
  rushResult.value = success ? 'success' : 'fail'
  
  if (success) {
    currentXP.value += 20
    userStore.addXP(20)
  }
  
  setTimeout(() => {
    showRush.value = false
  }, 2000)
}

// 定时器
let timer = null

const formatTime = (seconds) => {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

const togglePause = () => {
  isPaused.value = !isPaused.value
  if (isPaused.value) {
    stopTyping()
    stopSpeaking()
  } else if (isSpeaking.value && !typingTimer) {
    startTyping()
  }
}

const selectAnswer = (index) => {
  if (showResult.value) return
  selectedAnswer.value = index
  submitAnswer()
}

const submitAnswer = () => {
  showResult.value = true
  isCorrect.value = selectedAnswer.value === currentQuestion.value.correctAnswer
  if (isCorrect.value) {
    currentXP.value += questionXP.value
    userStore.addXP(questionXP.value)
  }
}

const submitFillAnswer = () => {
  showResult.value = true
  isCorrect.value = fillAnswer.value.toLowerCase().trim() === currentQuestion.value.correctAnswer
  if (isCorrect.value) {
    currentXP.value += questionXP.value
    userStore.addXP(questionXP.value)
  }
}

const nextQuestion = () => {
  showQuestion.value = false
  showResult.value = false
  selectedAnswer.value = null
  fillAnswer.value = ''
  
  // 检查是否所有页面都已讲完（讲义结束）
  if (lecturePages.value.length > 0 && !isSpeaking.value) {
    setTimeout(() => {
      router.push('/report')
    }, 2000)
  }
}

// 触发提问
const askQuestion = () => {
  alert('💬 请在下方输入您的问题，AI助教将尽快为您解答！')
}

// 触发彩蛋
const triggerEggDrop = () => {
  const egg = { name: 'XP礼包', xp: 20, emoji: '🎁' }
  currentEgg.value = egg
  showEgg.value = true
  currentXP.value += egg.xp
  userStore.addXP(egg.xp)
  setTimeout(() => {
    showEgg.value = false
  }, 3000)
}

// 显示提示
const showHint = () => {
  alert('💡 提示：仔细回忆变量的命名规范，不能以数字开头哦！')
}

// 确认退出
const confirmExit = () => {
  if (confirm('确定要退出课堂吗？进度将被保存。')) {
    router.push('/home')
  }
}

// 开始讲授 — 调用真实 AI SSE
let aiEventSource = null

const startTeaching = () => {
  // 初始化板书：从大纲加载默认知识点
  if (currentOutline.value) {
    const mods = currentOutline.value.modules_data || []
    if (mods.length > 0 && mods[0].keyPoints) {
      whiteboardPoints.value = mods[0].keyPoints.map((p, i) => ({
        text: p,
        _key: `outline_0_${i}`
      }))
    }
  }

  if (!currentOutline.value) {
    // 无大纲时用默认演示模式
    isSpeaking.value = true
    const demoText = '今天我们来学习Python的基础语法。\n\nPython是一种优雅且易于学习的编程语言，非常适合初学者入门。\n\n首先，让我们了解变量和数据类型。变量是存储数据的容器，Python支持多种数据类型，包括整数、浮点数、字符串和布尔值。\n\n关键概念：变量名可以由字母、数字和下划线组成，但不能以数字开头。\n\n让我们通过一个例子来理解：\n```python\nname = "Python"     # 字符串\nage = 25           # 整数\n```\n\n现在我们来做一个练习，检验一下你对变量命名规则的理解。'
    tokenBuffer.value = demoText
    startTyping()
    return
  }

  isSpeaking.value = true
  viewingHistoryPage.value = -1
  lectureDisplay.value = ''
  tokenBuffer.value = ''
  lecturePages.value = []
  whiteboardPoints.value = []
  allExtractedPointKeys.clear()
  extractedCode.value = ''

  const token = localStorage.getItem('token') || ''
  const sessionId = `classroom_${Date.now()}`
  const mods = currentOutline.value.modules_data || []
  const moduleDesc = mods.map((m, i) => `模块${i+1}: ${m.name} (${m.duration}分钟) - 要点: ${(m.keyPoints||[]).join('、')}`).join('\n')

  const stylePrompt = teacherStyle.value === 'humorous'
    ? '请用幽默风趣的脱口秀风格进行讲授，加入玩笑和比喻让课堂生动有趣。'
    : teacherStyle.value === 'rigorous'
    ? '请用严谨认真的教授风格进行讲授，注重逻辑性和系统性，像大学课堂一样。'
    : '请用友好耐心的方式进行讲授。'

  const systemPrompt = `你正在AI虚拟课堂中进行实时授课。\n${stylePrompt}\n\n当前课程大纲：\n${currentOutline.value.title || currentOutline.value.topic}\n${moduleDesc}\n\n请开始讲授第一个模块的内容。讲授要详细、有深度，包含代码示例和具体解释。`

  fetch('/api/v1/ai/tutor/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify({
      message: systemPrompt,
      outline_id: currentOutline.value?.id,
      teacher_style: teacherStyle.value
    })
  }).then(res => res.json()).then(data => {
    if (data.stream_url) {
      aiEventSource = new EventSource(`${data.stream_url}?token=${encodeURIComponent(token)}`)

      aiEventSource.addEventListener('token', (e) => {
        const d = JSON.parse(e.data)
        // SSE token 直接追加到缓冲区（不直接显示）
        tokenBuffer.value += d.token
      })

      aiEventSource.addEventListener('done', () => {
        // 排空剩余缓冲区
        stopTyping()
        if (tokenBuffer.value.length > 0) {
          lectureDisplay.value += tokenBuffer.value
          tokenBuffer.value = ''
        }
        if (lectureDisplay.value.trim()) {
          flushCurrentPage()
        }
        isSpeaking.value = false
        aiEventSource.close()
      })

      aiEventSource.addEventListener('error', () => {
        stopTyping()
        if (lectureDisplay.value.trim()) {
          flushCurrentPage()
        }
        isSpeaking.value = false
        aiEventSource?.close()
      })

      // 启动打字机
      startTyping()
    }
  }).catch(() => {
    stopTyping()
    isSpeaking.value = false
  })
}

// 触发 AI 出题
const askAIQuestion = async () => {
  if (!currentOutline.value) return
  const token = localStorage.getItem('token') || ''
  const sessionId = `question_${Date.now()}`
  const lectureText = fullLecture.value || lectureDisplay.value
  const prompt = `根据以下讲授内容出一道选择题（4个选项），测试学习者对当前模块的理解：\n${lectureText.substring(0, 800)}\n\n格式：{ "content": "题目", "options": ["A.","B.","C.","D."], "correctAnswer": 0, "explanation": "解释" }`
  
  try {
    const res = await fetch(`/api/v1/ai/tutor/${sessionId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ message: prompt })
    })
    const data = await res.json()
    if (data.ok) {
      // 简单解析AI返回的 JSON 题目
      // TODO: 完善解析逻辑
      showQuestion.value = true
      currentQuestion.value = {
        type: 'choice',
        content: '请等待AI出题...',
        options: ['A', 'B', 'C', 'D'],
        correctAnswer: 0,
        explanation: '',
        xp: 10
      }
    }
  } catch (e) { console.warn('AI出题失败:', e) }
}

// 学伴答题
const startCompanionAnswering = () => {
  classmates.value.forEach(mate => {
    mate.isAnswering = true
    mate.lastAction = '✍️ 正在答题...'
  })
  
  // 模拟学伴答题过程
  setTimeout(() => {
    const now = new Date()
    const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`
    
    companionMessages.value.push({
      sender: 'mate1',
      senderName: '小乐',
      avatar: '😎',
      text: '我选C！变量名可以有下划线～',
      time: timeStr,
      type: 'chat'
    })
    
    setTimeout(() => {
      const now2 = new Date()
      const timeStr2 = `${now2.getHours().toString().padStart(2, '0')}:${now2.getMinutes().toString().padStart(2, '0')}`
      
      companionMessages.value.push({
        sender: 'mate2',
        senderName: '小困',
        avatar: '😵',
        text: '我...我选A...不对吗？',
        time: timeStr2,
        type: 'chat'
      })
      
      // 更新学伴状态
      classmates.value[0].isAnswering = false
      classmates.value[0].lastAction = '✅ 答对了'
      classmates.value[1].isAnswering = false
      classmates.value[1].lastAction = '❌ 答错了'
      
      if (messageContainer.value) {
        setTimeout(() => {
          messageContainer.value.scrollTop = messageContainer.value.scrollHeight
        }, 100)
      }
    }, 2000)
  }, 3000)
}

// 计时器
const startTimer = () => {
  timer = setInterval(() => {
    if (!isPaused.value && remainingTime.value > 0) {
      remainingTime.value--
    }
  }, 1000)
}

onMounted(() => {
  loadOutline()
  startTimer()
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
  if (rushTimer) clearTimeout(rushTimer)
  if (rushCountdownTimer) clearInterval(rushCountdownTimer)
  if (typingTimer) clearInterval(typingTimer)
  if (aiEventSource) aiEventSource.close()
  stopSpeaking()
})
</script>

<style scoped>
.classroom-page {
  min-height: 100vh;
  padding-top: 60px;
  padding-bottom: 70px;
  background: linear-gradient(180deg, #E3F0FA 0%, #C5DFF5 30%, #D4E8F7 60%, #E8F1F9 100%);
  display: flex;
  flex-direction: column;
}

/* Header */
.class-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 60px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(74, 144, 217, 0.12);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1.5rem;
  z-index: 100;
  box-shadow: 0 1px 8px rgba(74, 144, 217, 0.06);
}

.class-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.back-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.85);
  border: none;
  border-radius: 50%;
  color: #2C4A6E;
  font-size: 1.25rem;
  cursor: pointer;
}

.class-title h1 {
  font-size: 1rem;
  margin-bottom: 0.25rem;
}

.class-progress {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.progress-text {
  font-size: 0.625rem;
  color: #8AA4C0;
}

.progress-bar {
  width: 120px;
  height: 4px;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4A90D9, #7CB8E4);
  transition: width 0.5s ease;
}

.class-stats {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.stat {
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.stat-icon {
  font-size: 1rem;
}

.stat-value {
  font-size: 0.875rem;
  font-weight: 600;
}

.pause-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.85);
  border: none;
  border-radius: 50%;
  color: #2C4A6E;
  cursor: pointer;
}

/* Main */
.classroom-main {
  flex: 1;
  display: grid;
  grid-template-columns: 240px 1fr 320px;
  gap: 1rem;
  padding: 1rem;
  overflow: hidden;
}

/* ============ 模块侧边栏 ============ */
.module-sidebar {
  background: var(--bg-card, #1e1e2e);
  border-radius: var(--radius-lg, 12px);
  border: 1px solid var(--border, #333);
  padding: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
  transition: width 0.2s;
}

.module-sidebar.collapsed {
  width: 50px;
  min-width: 50px;
}

.sidebar-toggle {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-secondary, #2a2a3e);
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  color: var(--text-muted, #888);
  z-index: 2;
  user-select: none;
}

.sidebar-toggle:hover {
  background: rgba(102, 126, 234, 0.2);
  color: #667eea;
}

.sidebar-header {
  padding: 16px 14px 8px;
  border-bottom: 1px solid var(--border, #333);
}

.sidebar-header h3 {
  margin: 0 0 4px;
  font-size: 15px;
  color: var(--text-primary, #eee);
}

.sidebar-subtitle {
  font-size: 11px;
  color: var(--text-muted, #888);
}

.module-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.module-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s;
  border: 1px solid transparent;
}

.module-item:hover {
  background: rgba(102, 126, 234, 0.08);
}

.module-item.active {
  background: rgba(102, 126, 234, 0.15);
  border-color: rgba(102, 126, 234, 0.3);
}

.module-item.completed {
  opacity: 0.75;
}

.module-num {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--bg-secondary, #2a2a3e);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted, #888);
  flex-shrink: 0;
}

.module-item.active .module-num {
  background: #667eea;
  color: #fff;
}

.module-item.completed .module-num {
  background: #22c55e;
  color: #fff;
}

.module-info {
  flex: 1;
  min-width: 0;
}

.module-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary, #eee);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.module-item.active .module-name {
  color: #667eea;
}

.module-meta {
  font-size: 10px;
  color: var(--text-muted, #888);
  margin-top: 2px;
}

.module-status {
  flex-shrink: 0;
}

.status-badge {
  font-size: 10px;
  padding: 3px 8px;
  border-radius: 10px;
  white-space: nowrap;
}

.status-badge.generating {
  background: rgba(234, 179, 8, 0.2);
  color: #eab308;
}

.status-badge.teaching {
  background: rgba(102, 126, 234, 0.2);
  color: #667eea;
}

.mini-start-btn {
  padding: 4px 10px;
  border-radius: 6px;
  background: #667eea;
  color: #fff;
  border: none;
  font-size: 11px;
  cursor: pointer;
  white-space: nowrap;
}

.mini-start-btn:hover {
  background: #5568d3;
}

.mini-gen-btn {
  padding: 4px 10px;
  border-radius: 6px;
  background: rgba(234, 179, 8, 0.2);
  color: #eab308;
  border: 1px solid rgba(234, 179, 8, 0.4);
  font-size: 11px;
  cursor: pointer;
  white-space: nowrap;
}

.mini-gen-btn:hover {
  background: rgba(234, 179, 8, 0.35);
}

.mini-gen-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* 收起时的圆点模式 */
.module-list-mini {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 40px 0;
}

.module-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--border, #444);
  cursor: pointer;
  transition: all 0.15s;
}

.module-dot.active {
  background: #667eea;
  box-shadow: 0 0 6px rgba(102, 126, 234, 0.5);
}

.module-dot.completed {
  background: #22c55e;
}

.module-dot.generated {
  border: 2px solid #667eea;
  background: transparent;
}

/* AI Section */
.ai-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.ai-teacher-card {
  background: rgba(255, 255, 255, 0.85);
  border-radius: var(--radius-lg);
  padding: 1.5rem;
  border: 1px solid rgba(74, 144, 217, 0.12);
}

.ai-avatar-section {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.ai-avatar-main {
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #4A90D9, #7CB8E4);
  border-radius: 50%;
  font-size: 2.5rem;
  transition: all 0.3s ease;
}

.ai-avatar-main.speaking {
  animation: speakingPulse 1s ease-in-out infinite;
}

@keyframes speakingPulse {
  0%, 100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(74, 144, 217, 0.4); }
  50% { transform: scale(1.05); box-shadow: 0 0 20px 10px rgba(74, 144, 217, 0.2); }
}

.ai-label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.ai-role {
  font-weight: 600;
  font-size: 0.875rem;
}

.ai-status {
  font-size: 0.75rem;
  color: #8AA4C0;
}

.ai-status.speaking {
  color: #4A90D9;
  animation: blink 1s infinite;
}

@keyframes blink {
  50% { opacity: 0.5; }
}

.content-text p {
  line-height: 1.8;
  font-size: 1rem;
}

/* 打字机光标 */
.typing-cursor {
  display: inline-block;
  color: #4A90D9;
  font-weight: 700;
  animation: cursor-blink 0.7s step-end infinite;
}

@keyframes cursor-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.preparing-text, .waiting-text {
  color: #8AA4C0;
  font-style: italic;
  text-align: center;
  padding: 1rem;
}

/* 倍速控制 */
.speed-control {
  display: flex;
  gap: 0.375rem;
  margin-left: auto;
}

.speed-btn {
  padding: 0.25rem 0.5rem;
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(74, 144, 217, 0.2);
  border-radius: 6px;
  color: #6B8AAD;
  font-size: 0.7rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.speed-btn:hover {
  border-color: #4A90D9;
  color: #4A90D9;
}

.speed-btn.active {
  background: #4A90D9;
  color: white;
  border-color: #4A90D9;
}

/* 翻页导航 */
.page-nav {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  padding: 0.75rem 0 0;
  margin-top: 0.5rem;
  border-top: 1px solid rgba(74, 144, 217, 0.08);
}

.page-nav-btn {
  padding: 0.375rem 0.75rem;
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(74, 144, 217, 0.15);
  border-radius: 6px;
  color: #4A90D9;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.page-nav-btn:hover:not(:disabled) {
  background: rgba(74, 144, 217, 0.1);
  border-color: #4A90D9;
}

.page-nav-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.page-indicator {
  font-size: 0.75rem;
  color: #6B8AAD;
  font-weight: 500;
}

/* 历史回看 */
.history-view {
  position: relative;
}

.history-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0.75rem;
  margin-bottom: 1rem;
  background: rgba(250, 173, 20, 0.1);
  border-radius: 8px;
  border-left: 3px solid #faad14;
  font-size: 0.8rem;
  color: #B8860B;
}

.back-to-live-btn {
  padding: 0.25rem 0.6rem;
  background: #4A90D9;
  border: none;
  border-radius: 6px;
  color: white;
  font-size: 0.7rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.back-to-live-btn:hover {
  background: #3A7BC8;
}

/* Question Area */
.question-area {
  margin-top: 1rem;
}

.question-card {
  background: rgba(255, 255, 255, 0.6);
  border-radius: var(--radius);
  padding: 1.5rem;
}

.question-type {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  background: #4A90D9;
  border-radius: 9999px;
  font-size: 0.75rem;
  margin-bottom: 1rem;
}

.question-text {
  font-size: 1.125rem;
  margin-bottom: 1.5rem;
  line-height: 1.6;
}

.options {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.option-btn {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  background: rgba(232, 241, 249, 0.3);
  border: 2px solid rgba(74, 144, 217, 0.12);
  border-radius: var(--radius);
  color: #2C4A6E;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: left;
}

.option-btn:hover:not(:disabled) {
  border-color: #4A90D9;
}

.option-btn.selected {
  border-color: #4A90D9;
  background: rgba(74, 144, 217, 0.1);
}

.option-btn.correct {
  border-color: #4A90D9;
  background: rgba(16, 185, 129, 0.1);
}

.option-btn.wrong {
  border-color: var(--danger);
  background: rgba(239, 68, 68, 0.1);
}

.option-letter {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 50%;
  font-weight: 600;
  font-size: 0.875rem;
}

.option-text {
  flex: 1;
}

.fill-input {
  display: flex;
  gap: 0.75rem;
}

.fill-input-field {
  flex: 1;
  padding: 0.875rem 1rem;
  background: rgba(232, 241, 249, 0.3);
  border: 2px solid rgba(74, 144, 217, 0.12);
  border-radius: var(--radius);
  color: #2C4A6E;
  font-size: 1rem;
}

.fill-input-field:focus {
  outline: none;
  border-color: #4A90D9;
}

.result-feedback {
  margin-top: 1.5rem;
  padding: 1rem;
  background: rgba(232, 241, 249, 0.3);
  border-radius: var(--radius);
  text-align: center;
}

.feedback-icon {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
}

.feedback-text {
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.feedback-explain {
  font-size: 0.875rem;
  color: #6B8AAD;
  line-height: 1.6;
}

.xp-reward {
  margin-top: 0.75rem;
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--warning);
}

.continue-btn {
  margin-top: 1rem;
  width: 100%;
}

/* Whiteboard */
.whiteboard {
  background: rgba(255, 255, 255, 0.85);
  border-radius: var(--radius-lg);
  border: 1px solid rgba(74, 144, 217, 0.12);
  overflow: hidden;
}

.whiteboard.expanded {
  flex: 1;
}

.whiteboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: rgba(255, 255, 255, 0.6);
  font-size: 0.875rem;
}

.whiteboard-header button {
  padding: 0.25rem 0.75rem;
  background: transparent;
  border: 1px solid rgba(74, 144, 217, 0.12);
  border-radius: 4px;
  color: #6B8AAD;
  font-size: 0.75rem;
  cursor: pointer;
}

.whiteboard-content {
  padding: 1rem;
  min-height: 120px;
}

.whiteboard-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 80px;
  color: #8AA4C0;
  font-size: 0.875rem;
  font-style: italic;
}

.code-block {
  background: rgba(255, 255, 255, 0.7);
  padding: 1rem;
  border-radius: var(--radius);
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 0.875rem;
  line-height: 1.6;
  overflow-x: auto;
  color: #2C4A6E;
}

.knowledge-points {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.point-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.point-num {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #4A90D9;
  border-radius: 50%;
  font-size: 0.75rem;
  font-weight: 600;
}

.point-text {
  font-size: 0.9375rem;
}

/* Tools Section */
.tools-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.avatar-widget {
  background: rgba(255, 255, 255, 0.85);
  border-radius: var(--radius);
  padding: 1rem;
  border: 1px solid rgba(74, 144, 217, 0.12);
}

.avatar-display {
  position: relative;
  width: 80px;
  height: 80px;
  margin: 0 auto 1rem;
}

.avatar-img {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #4A90D9, #7CB8E4);
  border-radius: 50%;
  font-size: 2.5rem;
}

.avatar-mood {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.85);
  border-radius: 50%;
  font-size: 1.25rem;
  border: 2px solid #4A90D9;
}

.avatar-info {
  text-align: center;
}

.avatar-level {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  background: linear-gradient(135deg, #A8D0F0, #7CB8E4);
  color: #2C4A6E;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
}

/* Classmates - 增强版 */
.classmates.enhanced {
  background: rgba(255, 255, 255, 0.85);
  border-radius: var(--radius);
  padding: 1rem;
  border: 1px solid rgba(74, 144, 217, 0.12);
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  max-height: 500px;
  overflow: hidden;
}

.classmates-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.classmates-header h4 {
  font-size: 0.875rem;
  color: #2C4A6E;
  margin: 0;
}

.classmates-count {
  font-size: 0.75rem;
  color: #8AA4C0;
  padding: 0.25rem 0.5rem;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 9999px;
}

/* 学伴消息区域 */
.classmate-messages {
  flex: 1;
  overflow-y: auto;
  max-height: 250px;
  padding: 0.5rem;
  background: rgba(255, 255, 255, 0.6);
  border-radius: var(--radius);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.message-bubble {
  display: flex;
  gap: 0.5rem;
  align-items: flex-start;
}

.message-bubble.system {
  justify-content: center;
}

.message-bubble.system .msg-content {
  background: transparent;
  padding: 0.25rem 0.75rem;
}

.message-bubble.system .msg-text {
  font-size: 0.75rem;
  color: #8AA4C0;
  font-style: italic;
}

.msg-avatar {
  font-size: 1.25rem;
  flex-shrink: 0;
}

.msg-content {
  flex: 1;
  background: rgba(255, 255, 255, 0.5);
  padding: 0.5rem 0.75rem;
  border-radius: var(--radius);
}

.msg-sender {
  font-size: 0.75rem;
  font-weight: 600;
  color: #4A90D9;
  margin-bottom: 0.25rem;
}

.message-bubble.mate2 .msg-sender {
  color: var(--warning);
}

.message-bubble.user .msg-sender {
  color: #4A90D9;
}

.msg-text {
  font-size: 0.875rem;
  line-height: 1.4;
  color: #2C4A6E;
}

.msg-time {
  font-size: 0.625rem;
  color: #8AA4C0;
  margin-top: 0.25rem;
}

/* 学伴列表 */
.classmate-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.classmate-card {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.6);
  border-radius: var(--radius);
  cursor: pointer;
  transition: all 0.3s ease;
}

.classmate-card:hover {
  background: rgba(255, 255, 255, 0.85);
  transform: translateX(4px);
}

.classmate-card.online {
  border-left: 3px solid #4A90D9;
}

.classmate-card.offline {
  border-left: 3px solid #8AA4C0;
  opacity: 0.6;
}

.classmate-avatar-wrapper {
  position: relative;
}

.classmate-avatar {
  font-size: 1.5rem;
}

.classmate-status-dot {
  position: absolute;
  bottom: 0;
  right: -2px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.6);
}

.classmate-status-dot.online {
  background: #4A90D9;
}

.classmate-status-dot.offline {
  background: #8AA4C0;
}

.classmate-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.classmate-name {
  font-size: 0.875rem;
  font-weight: 500;
}

.classmate-type {
  font-size: 0.625rem;
  color: #8AA4C0;
}

.classmate-action {
  font-size: 0.75rem;
}

.answering-indicator {
  color: var(--warning);
  animation: blink 1s infinite;
}

.last-action {
  color: #8AA4C0;
}

/* 学伴互动按钮 */
.companion-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
}

.action-btn {
  padding: 0.5rem;
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(74, 144, 217, 0.12);
  border-radius: var(--radius);
  color: #2C4A6E;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.action-btn:hover {
  border-color: #4A90D9;
  background: rgba(74, 144, 217, 0.1);
}

/* Quick Tools */
.quick-tools {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.5rem;
}

.tool-btn {
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid rgba(74, 144, 217, 0.12);
  border-radius: var(--radius);
  color: #2C4A6E;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.tool-btn:hover {
  border-color: #4A90D9;
  background: rgba(74, 144, 217, 0.1);
}

/* Modals */
.egg-modal {
  position: fixed;
  inset: 0;
  background: rgba(44, 74, 110, 0.3); backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}

.egg-content {
  background: linear-gradient(135deg, #A8D0F0, #4A90D9);
  padding: 2rem;
  border-radius: var(--radius-lg);
  text-align: center;
  max-width: 400px;
  animation: eggBounce 0.5s ease;
}

@keyframes eggBounce {
  0% { transform: scale(0); }
  50% { transform: scale(1.1); }
  100% { transform: scale(1); }
}

.egg-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.egg-text {
  color: #2C4A6E;
  line-height: 1.6;
  margin-bottom: 1rem;
}

.egg-xp {
  font-size: 1.5rem;
  font-weight: 700;
}

/* 抢答弹窗 */
.rush-modal {
  position: fixed;
  inset: 0;
  background: rgba(44, 74, 110, 0.3); backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
  backdrop-filter: blur(4px);
}

.rush-content {
  position: relative;
  width: 90%;
  max-width: 420px;
  background: rgba(255, 255, 255, 0.92); backdrop-filter: blur(12px);
  border-radius: 24px;
  padding: 2rem;
  text-align: center;
  border: 3px solid #4A90D9;
  box-shadow: 
    0 0 40px rgba(74, 144, 217, 0.3),
    0 0 80px rgba(74, 144, 217, 0.1),
    inset 0 1px 0 rgba(74, 144, 217, 0.05);
  overflow: hidden;
}

.rush-content::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #4A90D9, #A8D0F0, #4A90D9, #4A90D9);
  background-size: 200% 100%;
  animation: shimmer 2s linear infinite;
}

.rush-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.rush-badge {
  background: linear-gradient(135deg, #4A90D9, #3A7BC8);
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 700;
}

.rush-countdown {
  font-size: 1.5rem;
  font-weight: 700;
  color: #4A90D9;
  font-variant-numeric: tabular-nums;
}

.rush-countdown.urgent {
  color: #ff4d4f;
  animation: urgentPulse 0.5s ease-in-out infinite;
}

@keyframes urgentPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.2); }
}

.rush-question {
  font-size: 1.25rem;
  color: #2C4A6E;
  margin-bottom: 2rem;
  line-height: 1.6;
}

.rush-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 1rem 3rem;
  background: linear-gradient(135deg, #4A90D9 0%, #7CB8E4 50%, #4A90D9 100%);
  border: none;
  border-radius: 9999px;
  font-size: 1.25rem;
  font-weight: 700;
  color: white;
  cursor: pointer;
  overflow: hidden;
  transition: all 0.3s ease;
  box-shadow: 
    0 4px 15px rgba(74, 144, 217, 0.4),
    0 2px 4px rgba(74, 144, 217, 0.06),
    inset 0 2px 0 rgba(255,255,255,0.2),
    inset 0 -2px 0 rgba(74, 144, 217, 0.1);
}

.rush-btn:hover:not(:disabled) {
  transform: translateY(-2px) scale(1.05);
  box-shadow: 
    0 8px 25px rgba(74, 144, 217, 0.5),
    0 4px 8px rgba(74, 144, 217, 0.1),
    inset 0 2px 0 rgba(255,255,255,0.2),
    inset 0 -2px 0 rgba(74, 144, 217, 0.1);
}

.rush-btn:active:not(:disabled) {
  transform: translateY(1px) scale(0.98);
  box-shadow: 
    0 2px 8px rgba(74, 144, 217, 0.3),
    0 1px 2px rgba(74, 144, 217, 0.06),
    inset 0 2px 4px rgba(74, 144, 217, 0.08);
}

.rush-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.rush-btn-text {
  position: relative;
  z-index: 1;
}

.rush-btn-particles {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
  transform: translateX(-100%);
}

.rush-btn:hover .rush-btn-particles {
  animation: btnShine 0.8s ease forwards;
}

@keyframes btnShine {
  to { transform: translateX(100%); }
}

/* 抢答结果 */
.rush-result-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
  animation: resultBounce 0.5s ease;
}

@keyframes resultBounce {
  0% { transform: scale(0) rotate(-20deg); }
  50% { transform: scale(1.2) rotate(10deg); }
  100% { transform: scale(1) rotate(0); }
}

.rush-result-text {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.rush-xp-gain {
  font-size: 2rem;
  font-weight: 700;
  color: #A8D0F0;
  text-shadow: 0 0 20px rgba(255, 215, 0, 0.5);
  animation: xpGain 0.5s ease;
}

@keyframes xpGain {
  0% { transform: scale(0); opacity: 0; }
  50% { transform: scale(1.3); }
  100% { transform: scale(1); opacity: 1; }
}

.rush-result-hint {
  color: #6B8AAD;
  font-size: 0.875rem;
}

.rush-particles {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.particle {
  position: absolute;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  animation: particleFly 1s ease-out forwards;
}

.particle:nth-child(odd) { background: #A8D0F0; }
.particle:nth-child(even) { background: #4A90D9; }
.particle:nth-child(1) { left: 50%; top: 50%; animation-delay: 0s; --tx: -60px; --ty: -80px; }
.particle:nth-child(2) { left: 50%; top: 50%; animation-delay: 0.05s; --tx: 60px; --ty: -80px; }
.particle:nth-child(3) { left: 50%; top: 50%; animation-delay: 0.1s; --tx: -80px; --ty: 0px; }
.particle:nth-child(4) { left: 50%; top: 50%; animation-delay: 0.15s; --tx: 80px; --ty: 0px; }
.particle:nth-child(5) { left: 50%; top: 50%; animation-delay: 0.2s; --tx: -60px; --ty: 80px; }
.particle:nth-child(6) { left: 50%; top: 50%; animation-delay: 0.25s; --tx: 60px; --ty: 80px; }
.particle:nth-child(7) { left: 50%; top: 50%; animation-delay: 0.08s; --tx: -40px; --ty: -60px; }
.particle:nth-child(8) { left: 50%; top: 50%; animation-delay: 0.12s; --tx: 40px; --ty: -60px; }
.particle:nth-child(9) { left: 50%; top: 50%; animation-delay: 0.18s; --tx: -70px; --ty: 40px; }
.particle:nth-child(10) { left: 50%; top: 50%; animation-delay: 0.22s; --tx: 70px; --ty: 40px; }
.particle:nth-child(11) { left: 50%; top: 50%; animation-delay: 0.03s; --tx: 0px; --ty: -90px; }
.particle:nth-child(12) { left: 50%; top: 50%; animation-delay: 0.16s; --tx: 0px; --ty: 90px; }

@keyframes particleFly {
  0% { transform: translate(0, 0) scale(1); opacity: 1; }
  100% { transform: translate(var(--tx), var(--ty)) scale(0); opacity: 0; }
}

/* 成功/失败/超时状态样式 */
.rush-content.success {
  border-color: #4A90D9;
  box-shadow: 
    0 0 60px rgba(74, 144, 217, 0.5),
    0 0 100px rgba(74, 144, 217, 0.2);
}

.rush-content.success .rush-result-text {
  color: #4A90D9;
}

.rush-content.fail {
  border-color: #ff4d4f;
}

.rush-content.fail .rush-result-text {
  color: #ff4d4f;
}

.rush-content.timeout {
  border-color: #faad14;
}

.rush-content.timeout .rush-result-text {
  color: #faad14;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* 弹窗动画 */
.rush-modal-anim-enter-active {
  animation: modalIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.rush-modal-anim-leave-active {
  animation: modalOut 0.3s ease-in;
}

@keyframes modalIn {
  0% { opacity: 0; }
  100% { opacity: 1; }
}

@keyframes modalOut {
  0% { opacity: 1; }
  100% { opacity: 0; }
}

/* Transitions */
.egg-enter-active,
.egg-leave-active {
  transition: all 0.3s ease;
}

.egg-enter-from,
.egg-leave-to {
  opacity: 0;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 1024px) {
  .classroom-main {
    grid-template-columns: 1fr;
  }
  
  .module-sidebar {
    display: none;
  }
  
  .tools-section {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.75rem;
  }
  
  .avatar-widget {
    grid-column: span 2;
  }
}
</style>
