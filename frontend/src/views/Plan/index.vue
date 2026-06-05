<template>
  <div class="plan-page">
    <Navbar />
    
    <div class="plan-container">
      <!-- 左侧：对话区域 -->
      <div class="chat-area">
        <div class="chat-header">
          <div class="ai-avatar-lg">🤖</div>
          <div class="ai-info">
            <h2>大纲规划助手</h2>
            <p v-if="generationMode === 'chat'">告诉我你想学什么，我来帮你规划学习大纲</p>
            <p v-else>上传 PDF 电子书或资料，自动生成学习大纲</p>
          </div>
        </div>

        <!-- 模式切换 -->
        <div class="mode-toggle" v-if="!outlineGenerated">
          <button
            class="mode-btn"
            :class="{ active: generationMode === 'chat' }"
            @click="generationMode = 'chat'"
          >对话生成</button>
          <button
            class="mode-btn"
            :class="{ active: generationMode === 'pdf' }"
            @click="generationMode = 'pdf'"
          >根据资料生成</button>
        </div>

        <!-- PDF 上传模式 -->
        <div class="pdf-upload-area" v-if="generationMode === 'pdf' && !outlineGenerated">
          <div class="upload-zone" @click="triggerFileInput" @dragover.prevent @drop.prevent="handleDrop">
            <input
              ref="fileInput"
              type="file"
              accept=".pdf"
              style="display:none"
              @change="handleFileSelect"
            />
            <div v-if="!uploadedFile" class="upload-prompt">
              <div class="upload-icon">📄</div>
              <p>点击或拖拽上传 PDF 文件</p>
              <span class="upload-hint">支持 PDF 格式的电子书、教材、文档</span>
            </div>
            <div v-else class="uploaded-info">
              <div class="file-icon">📑</div>
              <div class="file-detail">
                <span class="file-name">{{ uploadedFile.name }}</span>
                <span class="file-size">{{ formatSize(uploadedFile.size) }}</span>
              </div>
              <button class="remove-file" @click.stop="clearFile">✕</button>
            </div>
          </div>
          <div class="pdf-actions" v-if="!uploading">
            <div class="topic-input">
              <label>主题（可选，默认用文件名）</label>
              <input v-model="pdfTopic" type="text" placeholder="如：Python编程" />
            </div>
            <div class="level-select">
              <label>程度</label>
              <select v-model="pdfLevel">
                <option value="beginner">初级（零基础）</option>
                <option value="intermediate">中级</option>
                <option value="advanced">高级</option>
              </select>
            </div>
          </div>
          <button
            class="btn btn-primary upload-submit"
            :disabled="!uploadedFile || uploading"
            @click="handlePdfGenerate"
          >
            <span v-if="!uploading">生成大纲</span>
            <span v-else class="spinning">⏳ 解析PDF并生成大纲...</span>
          </button>
        </div>

        <!-- 对话模式的原有内容 -->
        <template v-if="generationMode === 'chat'">
        <div class="chat-messages" ref="chatContainer">
          <div 
            v-for="msg in messages" 
            :key="msg.id"
            class="chat-message"
            :class="msg.type"
          >
            <div class="msg-avatar" v-if="msg.type === 'ai'">{{ msg.avatar }}</div>
            <div class="msg-content">
              <div class="msg-bubble">{{ msg.content }}</div>
              <!-- 选项按钮：当 AI 消息附带 options 时渲染 -->
              <div v-if="msg.options && msg.options.length && !msg.optionSelected" class="options-row">
                <button
                  v-for="opt in msg.options"
                  :key="opt.value"
                  class="option-btn"
                  @click="selectOption(opt.value, msg)"
                >
                  <span class="option-label">{{ opt.label }}</span>
                  <span class="option-desc">{{ opt.desc }}</span>
                </button>
              </div>
              <div class="msg-time" v-if="msg.time">{{ msg.time }}</div>
            </div>
          </div>
          
          <!-- 正在输入指示器 -->
          <div v-if="isTyping && !hasStreamingMessage" class="chat-message ai">
            <div class="msg-avatar">🤖</div>
            <div class="msg-content">
              <div class="typing">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 快捷问题 — 仅初始状态显示 -->
        <div class="quick-questions" v-if="messages.length <= 2 && !sessionId">
          <span class="quick-label">试试这些：</span>
          <button 
            v-for="q in quickQuestions" 
            :key="q"
            class="quick-btn"
            @click="handleQuick(q)"
          >
            {{ q }}
          </button>
        </div>
        
        <!-- 输入区域 — 大纲已生成后隐藏 -->
        <div class="input-area" v-if="!outlineGenerated">
          <input 
            v-model="userInput"
            type="text"
            placeholder="输入你想学习的内容..."
            class="chat-input"
            @keyup.enter="handleSend"
            :disabled="isTyping"
          />
          <button class="send-btn" @click="handleSend" :disabled="!userInput.trim() || isTyping">
            <span>➤</span>
          </button>
        </div>
        </template>
      </div>
      
      <!-- 右侧：预览区域 -->
      <div class="preview-area">
        <div class="preview-header">
          <h3>大纲预览</h3>
          <span class="preview-status" :class="{ active: outlineGenerated }">
            {{ outlineGenerated ? '已生成' : '待生成' }}
          </span>
        </div>
        
        <!-- 未生成大纲时 -->
        <div class="preview-empty" v-if="!outlineGenerated">
          <div class="empty-icon">📋</div>
          <p>回答3个简单问题后，这里将显示你的学习大纲</p>
          <div class="step-indicators">
            <div class="step-dot" :class="{ done: currentStep >= 1 }">1</div>
            <div class="step-line" :class="{ done: currentStep >= 2 }"></div>
            <div class="step-dot" :class="{ done: currentStep >= 2 }">2</div>
            <div class="step-line" :class="{ done: currentStep >= 3 }"></div>
            <div class="step-dot" :class="{ done: currentStep >= 3 }">3</div>
          </div>
          <div class="step-labels">
            <span :class="{ active: currentStep === 1 }">想学什么</span>
            <span :class="{ active: currentStep === 2 }">程度选择</span>
            <span :class="{ active: currentStep === 3 }">时间投入</span>
          </div>
        </div>
        
        <!-- 大纲卡片 -->
        <div class="outline-preview" v-else>
          <div class="outline-topic">
            <h2>{{ outline.title }}</h2>
            <div class="outline-tags">
              <span class="tag">{{ outline.subject || outline.topic }}</span>
              <span class="tag">{{ outline.level }}</span>
              <span class="tag">⏱️ {{ outline.duration || outline.total_duration }}分钟</span>
            </div>
          </div>
          
          <div class="outline-modules">
            <h4>学习模块</h4>
            <div 
              v-for="(mod, index) in outline.modules" 
              :key="mod.id"
              class="module-card"
              :class="{ current: index === currentModuleIndex }"
            >
              <div class="module-number">{{ index + 1 }}</div>
              <div class="module-info">
                <h5>{{ mod.name }}</h5>
                <div class="module-meta">
                  <span>{{ mod.duration }}分钟</span>
                  <span class="difficulty" :class="mod.difficulty">
                    {{ difficultyText[mod.difficulty] }}
                  </span>
                </div>
                <div class="module-points">
                  <span v-for="point in mod.keyPoints" :key="point" class="point-tag">
                    {{ point }}
                  </span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 开始学习按钮 -->
          <button class="btn btn-primary btn-lg start-class-btn" @click="startClass">
            <span>🚀</span>
            开始学习
          </button>
        </div>
      </div>
    </div>
    
    <BottomNav />
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import Navbar from '../../components/layout/Navbar.vue'
import BottomNav from '../../components/layout/BottomNav.vue'

const router = useRouter()
const API_BASE = '/api/v1/outline'

// ─── 生成模式 ───
const generationMode = ref('chat')  // 'chat' | 'pdf'

// ─── 对话模式 ───
const messages = ref([])
const userInput = ref('')
const isTyping = ref(false)
const outlineGenerated = ref(false)
const currentModuleIndex = ref(-1)
const outline = ref(null)
const sessionId = ref('')       // 当前会话ID，用于续接对话
const currentStep = ref(1)      // 当前步骤：1=问知识, 2=选程度, 3=问时间, 4=生成

// ─── PDF 上传模式 ───
const fileInput = ref(null)
const uploadedFile = ref(null)
const uploading = ref(false)
const pdfTopic = ref('')
const pdfLevel = ref('beginner')

const triggerFileInput = () => {
  fileInput.value?.click()
}

const handleFileSelect = (e) => {
  const file = e.target.files?.[0]
  if (file && file.name.endsWith('.pdf')) {
    uploadedFile.value = file
    if (!pdfTopic.value) {
      pdfTopic.value = file.name.replace('.pdf', '')
    }
  }
}

const handleDrop = (e) => {
  const file = e.dataTransfer?.files?.[0]
  if (file && file.name.endsWith('.pdf')) {
    uploadedFile.value = file
    if (!pdfTopic.value) {
      pdfTopic.value = file.name.replace('.pdf', '')
    }
  }
}

const clearFile = () => {
  uploadedFile.value = null
  if (fileInput.value) fileInput.value.value = ''
}

const formatSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const handlePdfGenerate = async () => {
  if (!uploadedFile.value || uploading.value) return
  uploading.value = true

  const token = localStorage.getItem('token') || ''
  const formData = new FormData()
  formData.append('file', uploadedFile.value)
  formData.append('topic', pdfTopic.value || uploadedFile.value.name.replace('.pdf', ''))
  formData.append('level', pdfLevel.value)

  try {
    const res = await fetch(`${API_BASE}/pdf-generate`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: formData
    })
    if (!res.ok) {
      const err = await res.json()
      alert(err.detail || '生成失败')
      return
    }
    const data = await res.json()

    // 显示生成的大纲
    outline.value = {
      id: data.outline_id,
      title: data.title,
      topic: data.topic,
      level: data.level,
      duration: data.total_duration,
      total_duration: data.total_duration,
      module_count: data.module_count,
      modules: data.modules,
      subject: data.topic
    }
    outlineGenerated.value = true
  } catch (err) {
    console.error('[Plan] PDF upload error:', err)
    alert('网络错误，请重试')
  } finally {
    uploading.value = false
  }
}

// 是否存在正在流式输出的 AI 消息
const hasStreamingMessage = computed(() => {
  return messages.value.some(m => m.type === 'ai' && m.streaming)
})

const quickQuestions = [
  '我想学习Python基础',
  '教我数据结构与算法',
  '帮我规划机器学习入门'
]

const difficultyText = {
  easy: '简单', medium: '中等', hard: '困难',
  beginner: '入门', intermediate: '中级', advanced: '高级'
}

const handleQuick = (q) => sendMessage(q)

const handleSend = () => {
  const text = userInput.value?.trim()
  if (text && !isTyping.value) {
    userInput.value = ''
    sendMessage(text)
  }
}

/**
 * 点击选项按钮（如程度选择）
 */
const selectOption = (value, msg) => {
  if (isTyping.value) return
  msg.optionSelected = true

  // 选项对应的显示文本
  const labels = {
    beginner: '初级（零基础入门）',
    intermediate: '中级（有一定基础）',
    advanced: '高级（深入精通）'
  }
  const displayText = labels[value] || value

  // 添加用户"点击"消息
  messages.value.push({
    id: Date.now(),
    type: 'user',
    content: displayText,
    time: new Date().toLocaleTimeString(),
    isOption: true
  })

  // 发送
  sendMessage(value)
}

const sendMessage = async (text) => {
  if (!text || isTyping.value) return
  
  // 用户输入的消息，添加到聊天列表（选项点击由 selectOption 添加）
  const lastMsg = messages.value[messages.value.length - 1]
  if (!lastMsg || !lastMsg.isOption || lastMsg.content !== text) {
    messages.value.push({
      id: Date.now(),
      type: 'user',
      content: text,
      time: new Date().toLocaleTimeString()
    })
  }
  
  isTyping.value = true
  await scrollToBottom()

  // 添加 AI 占位消息
  const aiMsgId = Date.now() + 1
  messages.value.push({
    id: aiMsgId,
    type: 'ai',
    content: '',
    avatar: '🤖',
    time: new Date().toLocaleTimeString(),
    streaming: true,
    options: [],       // 可能附带选项
    optionSelected: false
  })
  await scrollToBottom()

  const token = localStorage.getItem('token') || ''

  try {
    const res = await fetch(`${API_BASE}/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ 
        message: text,
        topic: text,
        level: 'beginner',
        session_id: sessionId.value
      })
    })
    const data = await res.json()

    if (data.session_id) {
      sessionId.value = data.session_id
    }

    if (data.stream_url) {
      connectSSE(data.stream_url, aiMsgId)
    } else {
      updateAiMessage(aiMsgId, '大纲生成启动失败')
      isTyping.value = false
    }
  } catch (err) {
    console.error('[Plan] fetch error:', err)
    updateAiMessage(aiMsgId, '网络错误，请重试')
    isTyping.value = false
  }
}

const connectSSE = async (streamUrl, aiMsgId) => {
  const token = localStorage.getItem('token') || ''
  // 直连后端（SSE 流无法通过 webpack 代理，会被缓冲）
  const url = `http://127.0.0.1:8000${streamUrl}?token=${encodeURIComponent(token)}`

  let fullText = ''

  try {
    const response = await fetch(url, {
      headers: {
        'Accept': 'text/event-stream',
        'Authorization': token ? `Bearer ${token}` : ''
      }
    })

    if (!response.ok) {
      updateAiMessage(aiMsgId, `连接失败: ${response.status}`)
      isTyping.value = false
      return
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    let done = false
    while (!done) {
      const result = await reader.read()
      done = result.done
      if (done) break

      buffer += decoder.decode(result.value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      let eventType = ''
      for (const line of lines) {
        if (line.startsWith('event: ')) {
          eventType = line.slice(7).trim()
        } else if (line.startsWith('data: ')) {
          const dataStr = line.slice(6)

          try {
            const d = JSON.parse(dataStr)

            if (eventType === 'token') {
              // 流式 token
              fullText += d.token
              updateAiMessage(aiMsgId, fullText)
              scrollToBottom()
            } else if (eventType === 'options') {
              // 选项事件：将选项附加到当前 AI 消息
              fullText += '\n'  // 确保选项在文本后
              updateAiMessage(aiMsgId, fullText, true)
              attachOptions(aiMsgId, d.options || [])
            } else if (eventType === 'step') {
              // 步骤更新
              currentStep.value = d.step
            } else if (eventType === 'step_update') {
              // 步骤更新（对话阶段结束时的汇总）
              currentStep.value = d.step
              if (d.has_options && d.options) {
                attachOptions(aiMsgId, d.options)
              }
            } else if (eventType === 'outline_completed') {
              // 大纲生成完成
              fullText = d.full_text || fullText
              updateAiMessage(aiMsgId, fullText, false)
              isTyping.value = false
              currentStep.value = 4

              if (d.modules?.length) {
                outline.value = {
                  id: d.outline_id,
                  title: d.title,
                  topic: d.topic,
                  level: d.level,
                  duration: d.total_duration,
                  total_duration: d.total_duration,
                  module_count: d.module_count,
                  modules: d.modules
                }
                outlineGenerated.value = true
              }
            } else if (eventType === 'done') {
              // 流结束
              if (!outlineGenerated.value) {
                updateAiMessage(aiMsgId, fullText, false)
                isTyping.value = false
              }
            } else if (eventType === 'error') {
              updateAiMessage(aiMsgId, d.message || '生成失败')
              isTyping.value = false
            }
          } catch (e) {
            // JSON parse 失败，忽略
          }
        }
      }
    }
  } catch (err) {
    console.error('[SSE-fetch] error:', err)
    updateAiMessage(aiMsgId, `网络错误: ${err.message}`)
    isTyping.value = false
  }
}

const updateAiMessage = (id, content, streaming = true) => {
  const idx = messages.value.findIndex(m => m.id === id)
  if (idx >= 0) {
    messages.value[idx].content = content
    messages.value[idx].streaming = streaming
  }
}

const attachOptions = (id, options) => {
  const idx = messages.value.findIndex(m => m.id === id)
  if (idx >= 0) {
    messages.value[idx].options = options
    messages.value[idx].optionSelected = false
  }
}

const scrollToBottom = async () => {
  await nextTick()
  const container = document.querySelector('.chat-messages')
  if (container) container.scrollTop = container.scrollHeight
}

const startClass = () => {
  router.push({ path: '/classroom', query: { outline_id: outline.value?.id } })
}

onMounted(() => {
  setTimeout(() => {
    messages.value.push({
      id: 1,
      type: 'ai',
      content: `你好！我是大纲规划助手 🎯

只需回答3个简单问题，我就能为你生成一份专属学习大纲：

1️⃣ **你想学什么？** — 告诉我具体的学习主题
2️⃣ **你的程度？** — 初级/中级/高级（点击选择）
3️⃣ **时间投入？** — 每天或每周能学多久

来吧，先告诉我你想学什么～`,
      avatar: '🤖',
      time: new Date().toLocaleTimeString()
    })
  }, 500)
})

onUnmounted(() => {
  // 清理
})
</script>

<style scoped>
/* ============================================
   整体 - 浅蓝清新风格（与首页统一）
   ============================================ */
.plan-page {
  min-height: 100vh;
  padding-top: 80px;
  padding-bottom: 80px;
  background: linear-gradient(180deg, #E3F0FA 0%, #C5DFF5 30%, #D4E8F7 60%, #E8F1F9 100%);
}

.plan-container {
  max-width: 1100px;
  margin: 0 auto;
  padding: 0 20px;
  display: grid;
  grid-template-columns: 1fr 360px;
  gap: 16px;
  min-height: calc(100vh - 64px - 80px - 3rem);
}

/* ====== Chat Area ====== */
.chat-area {
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(8px);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: 0 2px 12px rgba(74, 144, 217, 0.08);
  overflow: hidden;
}

.chat-header {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(74, 144, 217, 0.12);
  background: rgba(255, 255, 255, 0.5);
}

.ai-avatar-lg {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #DCE8F4, #C5DFF5);
  border-radius: 50%;
  font-size: 1.5rem;
  box-shadow: 0 2px 6px rgba(74, 144, 217, 0.15);
  flex-shrink: 0;
}

.ai-info h2 {
  font-size: 1.05rem;
  font-weight: 700;
  color: #2C4A6E;
  margin-bottom: 2px;
}

.ai-info p {
  font-size: 0.78rem;
  color: #6B8AAD;
}

/* Messages */
.chat-messages {
  flex: 1;
  padding: 16px 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  background: rgba(232, 241, 249, 0.3);
}

.chat-message {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
  animation: msgIn 0.3s ease;
}

@keyframes msgIn {
  from { opacity: 0; transform: translateY(8px); }
}

.chat-message.user { flex-direction: row-reverse; }

.msg-avatar {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #DCE8F4, #C5DFF5);
  border-radius: 50%;
  font-size: 1.05rem;
  flex-shrink: 0;
  box-shadow: 0 1px 4px rgba(74, 144, 217, 0.1);
}

.msg-content { max-width: 70%; }

.msg-bubble {
  padding: 10px 14px;
  border-radius: 14px;
  line-height: 1.55;
  white-space: pre-wrap;
  font-size: 0.88rem;
}

.chat-message.ai .msg-bubble {
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid rgba(74, 144, 217, 0.1);
  border-bottom-left-radius: 4px;
  color: #2C4A6E;
}

.chat-message.user .msg-bubble {
  background: linear-gradient(135deg, #4A90D9, #3A7BC8);
  color: white;
  border-bottom-right-radius: 4px;
  box-shadow: 0 2px 8px rgba(74, 144, 217, 0.25);
}

.msg-time {
  font-size: 0.6rem;
  color: #8AA4C0;
  margin-top: 3px;
  padding: 0 6px;
}

/* ─── 选项按钮 ─── */
.options-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 10px;
}

.option-btn {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.9);
  border: 2px solid rgba(74, 144, 217, 0.2);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
  width: 100%;
}

.option-btn:hover {
  border-color: #4A90D9;
  background: rgba(74, 144, 217, 0.06);
  transform: translateX(4px);
  box-shadow: 0 2px 10px rgba(74, 144, 217, 0.12);
}

.option-btn:active {
  transform: scale(0.98);
}

.option-label {
  font-size: 0.9rem;
  font-weight: 700;
  color: #2C4A6E;
}

.option-desc {
  font-size: 0.72rem;
  color: #8AA4C0;
}

/* Typing indicator */
.typing {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid rgba(74, 144, 217, 0.1);
  border-radius: 14px;
  border-bottom-left-radius: 4px;
}

.typing span {
  width: 7px;
  height: 7px;
  background: #7CB8E4;
  border-radius: 50%;
  animation: typingBounce 1.4s infinite;
}

.typing span:nth-child(2) { animation-delay: 0.2s; }
.typing span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typingBounce {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.35; }
  30% { transform: translateY(-5px); opacity: 1; }
}

/* Quick questions */
.quick-questions {
  padding: 0 20px 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.quick-label {
  font-size: 0.72rem;
  color: #8AA4C0;
}

.quick-btn {
  padding: 6px 14px;
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(74, 144, 217, 0.15);
  border-radius: 9999px;
  color: #4A90D9;
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.quick-btn:hover {
  background: #4A90D9;
  color: white;
  border-color: #4A90D9;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(74, 144, 217, 0.25);
}

/* Input area */
.input-area {
  display: flex;
  gap: 10px;
  padding: 14px 20px;
  border-top: 1px solid rgba(74, 144, 217, 0.12);
  background: rgba(255, 255, 255, 0.6);
}

.chat-input {
  flex: 1;
  padding: 10px 16px;
  background: rgba(255, 255, 255, 0.8);
  border: 1.5px solid rgba(74, 144, 217, 0.15);
  border-radius: 12px;
  color: #2C4A6E;
  font-size: 0.88rem;
  outline: none;
  transition: border-color 0.3s ease, box-shadow 0.3s ease;
}

.chat-input:focus {
  border-color: #4A90D9;
  box-shadow: 0 0 0 3px rgba(74, 144, 217, 0.08);
}

.chat-input::placeholder { color: #AAC0D8; }
.chat-input:disabled { opacity: 0.5; cursor: not-allowed; }

.send-btn {
  width: 42px;
  height: 42px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #4A90D9, #3A7BC8);
  border: none;
  border-radius: 12px;
  color: white;
  font-size: 1.1rem;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 6px rgba(74, 144, 217, 0.2);
}

.send-btn:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 4px 14px rgba(74, 144, 217, 0.3);
}

.send-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
  box-shadow: none;
}

/* ====== Preview Area ====== */
.preview-area {
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(8px);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: 0 2px 12px rgba(74, 144, 217, 0.08);
  padding: 18px;
  display: flex;
  flex-direction: column;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(74, 144, 217, 0.12);
}

.preview-header h3 {
  font-size: 1rem;
  font-weight: 700;
  color: #2C4A6E;
}

.preview-status {
  padding: 3px 12px;
  background: rgba(74, 144, 217, 0.08);
  border-radius: 9999px;
  font-size: 0.7rem;
  font-weight: 600;
  color: #8AA4C0;
}

.preview-status.active {
  background: rgba(74, 144, 217, 0.15);
  color: #4A90D9;
}

.preview-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: #8AA4C0;
  gap: 10px;
}

.empty-icon {
  font-size: 3rem;
  opacity: 0.3;
}

.preview-empty p {
  font-size: 0.82rem;
}

/* ─── 步骤指示器 ─── */
.step-indicators {
  display: flex;
  align-items: center;
  gap: 0;
  margin-top: 8px;
}

.step-dot {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(74, 144, 217, 0.1);
  border: 2px solid rgba(74, 144, 217, 0.2);
  border-radius: 50%;
  font-size: 0.7rem;
  font-weight: 700;
  color: #8AA4C0;
  transition: all 0.3s ease;
}

.step-dot.done {
  background: #4A90D9;
  border-color: #4A90D9;
  color: white;
}

.step-line {
  width: 30px;
  height: 2px;
  background: rgba(74, 144, 217, 0.15);
  transition: all 0.3s ease;
}

.step-line.done {
  background: #4A90D9;
}

.step-labels {
  display: flex;
  justify-content: space-between;
  width: 100%;
  max-width: 180px;
  margin-top: 6px;
  font-size: 0.6rem;
  color: #AAC0D8;
}

.step-labels span.active {
  color: #4A90D9;
  font-weight: 700;
}

/* Outline cards */
.outline-preview {
  flex: 1;
  display: flex;
  flex-direction: column;
  animation: fadeIn 0.5s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
}

.outline-topic {
  margin-bottom: 14px;
}

.outline-topic h2 {
  font-size: 1.15rem;
  font-weight: 700;
  margin-bottom: 8px;
  color: #2C4A6E;
}

.outline-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag {
  padding: 4px 10px;
  background: rgba(74, 144, 217, 0.08);
  border-radius: 9999px;
  font-size: 0.68rem;
  font-weight: 500;
  color: #4A90D9;
  border: 1px solid rgba(74, 144, 217, 0.12);
}

.outline-modules h4 {
  font-size: 0.78rem;
  color: #8AA4C0;
  margin-bottom: 10px;
  font-weight: 600;
}

.module-card {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 12px;
  margin-bottom: 8px;
  border: 1px solid rgba(74, 144, 217, 0.1);
  transition: all 0.25s ease;
}

.module-card:hover {
  border-color: rgba(74, 144, 217, 0.25);
  box-shadow: 0 2px 8px rgba(74, 144, 217, 0.08);
}

.module-card.current {
  border-color: #4A90D9;
  background: rgba(74, 144, 217, 0.06);
  box-shadow: 0 2px 10px rgba(74, 144, 217, 0.12);
}

.module-number {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #4A90D9, #3A7BC8);
  border-radius: 50%;
  color: white;
  font-weight: 700;
  font-size: 0.75rem;
  flex-shrink: 0;
  box-shadow: 0 2px 5px rgba(74, 144, 217, 0.2);
}

.module-info { flex: 1; }

.module-info h5 {
  font-size: 0.82rem;
  font-weight: 600;
  margin-bottom: 3px;
  color: #2C4A6E;
}

.module-meta {
  display: flex;
  gap: 10px;
  font-size: 0.68rem;
  color: #8AA4C0;
  margin-bottom: 5px;
}

.difficulty {
  padding: 1px 8px;
  border-radius: 9999px;
  font-weight: 600;
}

.difficulty.easy, .difficulty.beginner {
  background: rgba(74, 144, 217, 0.1);
  color: #4A90D9;
}

.difficulty.medium, .difficulty.intermediate {
  background: rgba(250, 173, 20, 0.12);
  color: #D48806;
}

.difficulty.hard, .difficulty.advanced {
  background: rgba(239, 68, 68, 0.1);
  color: #D94A4A;
}

.module-points {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.point-tag {
  padding: 2px 7px;
  background: rgba(74, 144, 217, 0.05);
  border-radius: 4px;
  font-size: 0.6rem;
  color: #6B8AAD;
  border: 1px solid rgba(74, 144, 217, 0.08);
}

.start-class-btn {
  margin-top: auto;
  width: 100%;
  padding: 12px;
  background: linear-gradient(135deg, #4A90D9, #3A7BC8);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 0.95rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 3px 0 rgba(41, 102, 165, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.start-class-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 0 rgba(41, 102, 165, 0.5), 0 4px 14px rgba(74, 144, 217, 0.3);
}

.start-class-btn:active {
  transform: translateY(2px);
  box-shadow: 0 1px 0 rgba(41, 102, 165, 0.5);
}

@media (max-width: 1024px) {
  .plan-container {
    grid-template-columns: 1fr;
  }
  .preview-area {
    order: -1;
  }
}

/* ====== 模式切换 ====== */
.mode-toggle {
  display: flex;
  gap: 8px;
  padding: 0 14px 14px;
}

.mode-btn {
  flex: 1;
  padding: 10px 0;
  border: 2px solid rgba(74, 144, 217, 0.15);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.4);
  color: #6B8AAA;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.mode-btn:hover {
  border-color: rgba(74, 144, 217, 0.3);
  color: #4A90D9;
}

.mode-btn.active {
  background: linear-gradient(135deg, #4A90D9, #357ABD);
  border-color: #4A90D9;
  color: #fff;
}

/* ====== PDF Upload ====== */
.pdf-upload-area {
  padding: 0 14px 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.upload-zone {
  border: 2px dashed rgba(74, 144, 217, 0.25);
  border-radius: 14px;
  padding: 30px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  background: rgba(255, 255, 255, 0.3);
}

.upload-zone:hover {
  border-color: #4A90D9;
  background: rgba(74, 144, 217, 0.05);
}

.upload-prompt {
  pointer-events: none;
}

.upload-icon {
  font-size: 2.5rem;
  margin-bottom: 8px;
}

.upload-prompt p {
  font-size: 0.9rem;
  color: #4A6B8A;
  margin: 0 0 4px;
  font-weight: 600;
}

.upload-hint {
  font-size: 0.75rem;
  color: #94AFC5;
}

.uploaded-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
}

.file-icon {
  font-size: 2rem;
}

.file-detail {
  flex: 1;
  text-align: left;
  display: flex;
  flex-direction: column;
}

.file-name {
  font-size: 0.85rem;
  font-weight: 600;
  color: #2C4A6E;
  word-break: break-all;
}

.file-size {
  font-size: 0.7rem;
  color: #94AFC5;
}

.remove-file {
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 50%;
  background: rgba(231, 76, 60, 0.1);
  color: #E74C3C;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s;
}

.remove-file:hover {
  background: rgba(231, 76, 60, 0.2);
}

.pdf-actions {
  display: flex;
  gap: 10px;
}

.topic-input, .level-select {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.topic-input label, .level-select label {
  font-size: 0.7rem;
  font-weight: 600;
  color: #6B8AAA;
}

.topic-input input, .level-select select {
  padding: 8px 12px;
  border: 1px solid rgba(74, 144, 217, 0.15);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.6);
  color: #2C4A6E;
  font-size: 0.85rem;
  outline: none;
  transition: border-color 0.2s;
}

.topic-input input:focus, .level-select select:focus {
  border-color: #4A90D9;
}

.upload-submit {
  width: 100%;
  padding: 12px;
  font-size: 0.95rem;
}

.upload-submit:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.spinning {
  animation: spin 1.2s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
