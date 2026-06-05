/**
 * AI虚拟课堂 - SSE流式通信服务
 * 对接FastAPI后端的SSE端点（通过Vue CLI代理）
 */
import { ref, onUnmounted } from 'vue'

const API_BASE = '/api/v1/ai'
let _token = null

export function setSSEToken(token) { _token = token }
export function clearSSEToken() { _token = null; localStorage.removeItem('token') }
export function getSSEToken() {
  if (_token) return _token
  return localStorage.getItem('token') || ''
}

/**
 * 启动AI导师会话（POST /api/v1/ai/tutor/{session_id}）
 */
export async function startTutorSession(message, agentType = null, teacherStyle = null) {
  const sessionId = `sse_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`
  const token = getSSEToken()

  const body = { message, session_id: sessionId }
  if (agentType) body.agent_type = agentType
  if (teacherStyle) body.teacher_style = teacherStyle

  const res = await fetch(`${API_BASE}/tutor/${sessionId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify(body)
  })

  if (!res.ok) {
    throw new Error(`启动会话失败: ${res.status}`)
  }

  const data = await res.json()
  return { sessionId, ...data }
}

/**
 * 启动多Agent流水线
 */
export async function startPipeline(message, agentSequence) {
  const sessionId = `pipe_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`
  const token = getSSEToken()

  const res = await fetch(`${API_BASE}/pipeline/${sessionId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify({
      message,
      agent_sequence: agentSequence,
      session_id: sessionId
    })
  })

  if (!res.ok) {
    throw new Error(`启动流水线失败: ${res.status}`)
  }

  const data = await res.json()
  return { sessionId, ...data }
}

/**
 * 监听SSE流式输出
 * 
 * @param {string} sessionId - 会话ID
 * @param {Object} callbacks - 回调函数
 * @returns {EventSource} - SSE连接对象
 */
export function subscribeSSE(sessionId, callbacks = {}) {
  const {
    onConnected,
    onToken,
    onDone,
    onError,
    onHeartbeat,
    onAgentSwitched,
    onPipelineStarted,
    onPipelineCompleted
  } = callbacks

  // 带token的SSE URL
  const url = `${API_BASE}/tutor/stream/${sessionId}?token=${encodeURIComponent(getSSEToken())}`
  const es = new EventSource(url)

  es.addEventListener('connected', (e) => {
    try {
      const data = JSON.parse(e.data)
      onConnected?.(data)
    } catch { }
  })

  es.addEventListener('token', (e) => {
    try {
      const data = JSON.parse(e.data)
      onToken?.(data.token, data.progress || 0)
    } catch { }
  })

  es.addEventListener('done', (e) => {
    try {
      const data = JSON.parse(e.data)
      onDone?.(data.full_text)
    } catch { }
    es.close()
  })

  es.addEventListener('error', (e) => {
    try {
      const data = JSON.parse(e.data)
      onError?.(data.message)
    } catch {
      onError?.('连接异常')
    }
    es.close()
  })

  es.addEventListener('heartbeat', () => {
    onHeartbeat?.()
  })

  es.addEventListener('agent_switched', (e) => {
    try {
      const data = JSON.parse(e.data)
      onAgentSwitched?.(data.new_agent)
    } catch { }
  })

  es.addEventListener('pipeline_started', (e) => {
    try {
      const data = JSON.parse(e.data)
      onPipelineStarted?.(data.agent_sequence)
    } catch { }
  })

  es.addEventListener('pipeline_completed', (e) => {
    try {
      const data = JSON.parse(e.data)
      onPipelineCompleted?.(data.final_output)
    } catch { }
    es.close()
  })

  return es
}

/**
 * 切换Agent
 */
export async function switchAgentAPI(sessionId, agentType) {
  const token = getSSEToken()
  const res = await fetch(`${API_BASE}/switch/${sessionId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify({
      session_id: sessionId,
      agent_type: agentType
    })
  })
  if (!res.ok) throw new Error(`切换Agent失败: ${res.status}`)
  return await res.json()
}

/**
 * Vue 3 组合式函数 - useAITutor
 * 在Vue组件中使用AI导师功能
 */
export function useAITutor() {
  const sessionId = ref(null)
  const isLoading = ref(false)
  const aiOutput = ref('')
  const error = ref(null)
  const currentAgent = ref('tutor')

  let eventSource = null

  const sendMessage = async (message, agentType = null, teacherStyle = null) => {
    if (!message.trim()) return
    isLoading.value = true
    error.value = null
    aiOutput.value = ''

    try {
      const { sessionId: sid } = await startTutorSession(message, agentType, teacherStyle)
      sessionId.value = sid
      currentAgent.value = agentType || 'tutor'

      eventSource = subscribeSSE(sid, {
        onConnected: (d) => console.log('✅ SSE:', d),
        onToken: (token) => { aiOutput.value += token },
        onDone: () => { isLoading.value = false },
        onError: (msg) => { error.value = msg; isLoading.value = false },
        onAgentSwitched: (agent) => { currentAgent.value = agent }
      })
    } catch (err) {
      error.value = err.message
      isLoading.value = false
    }
  }

  const startAgentPipeline = async (message, agentSequence) => {
    isLoading.value = true
    error.value = null
    aiOutput.value = ''

    try {
      const { sessionId: sid } = await startPipeline(message, agentSequence)
      sessionId.value = sid

      eventSource = subscribeSSE(sid, {
        onToken: (token) => { aiOutput.value += token },
        onPipelineCompleted: () => { isLoading.value = false },
        onError: (msg) => { error.value = msg; isLoading.value = false }
      })
    } catch (err) {
      error.value = err.message
      isLoading.value = false
    }
  }

  const switchAgent = async (agentType) => {
    if (!sessionId.value) return
    try {
      await switchAgentAPI(sessionId.value, agentType)
      currentAgent.value = agentType
    } catch (err) {
      error.value = err.message
    }
  }

  const stopSession = () => {
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }
    isLoading.value = false
  }

  onUnmounted(() => stopSession())

  return {
    sessionId, isLoading, aiOutput, error, currentAgent,
    sendMessage, switchAgent, startAgentPipeline, stopSession
  }
}
