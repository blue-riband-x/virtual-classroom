/**
 * API服务 - HTTP客户端
 * 统一管理所有后端API请求
 */
import { useUserStore } from '@/stores/index'

const BASE_URL = '/api/v1'

// 请求拦截器
class ApiClient {
  constructor() {
    this.token = localStorage.getItem('token') || ''
  }

  setToken(token) {
    this.token = token
    localStorage.setItem('token', token)
  }

  clearToken() {
    this.token = ''
    localStorage.removeItem('token')
  }

  async request(url, options = {}) {
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...(this.token ? { 'Authorization': `Bearer ${this.token}` } : {})
      },
      ...options
    }

    const response = await fetch(`${BASE_URL}${url}`, config)

    if (!response.ok) {
      if (response.status === 401) {
        this.clearToken()
        throw new Error('认证过期，请重新登录')
      }
      const error = await response.json().catch(() => ({ message: `请求失败: ${response.status}` }))
      throw new Error(error.message || error.detail || '请求失败')
    }

    const data = await response.json()
    return data
  }

  get(url, params) {
    const query = params ? '?' + new URLSearchParams(params).toString() : ''
    return this.request(`${url}${query}`)
  }

  post(url, body) {
    return this.request(url, {
      method: 'POST',
      body: JSON.stringify(body)
    })
  }

  put(url, body) {
    return this.request(url, {
      method: 'PUT',
      body: JSON.stringify(body)
    })
  }

  delete(url) {
    return this.request(url, { method: 'DELETE' })
  }
}

export const api = new ApiClient()

// ========== 认证API ==========
export const authAPI = {
  async login(username, password) {
    const res = await api.post('/auth/login', { username, password })
    if (res.data?.access_token) {
      api.setToken(res.data.access_token)
    }
    return res.data
  },

  async register(data) {
    return await api.post('/auth/register', data)
  },

  async getMe() {
    return await api.get('/auth/me')
  },

  logout() {
    api.clearToken()
  }
}

// ========== 用户API ==========
export const userAPI = {
  async getProfile() {
    const res = await api.get('/users/profile')
    return res.data
  },

  async getHistory() {
    const res = await api.get('/users/history')
    return res.data
  },

  async getAchievements() {
    const res = await api.get('/users/achievements')
    return res.data
  }
}

// ========== AI交互API ==========
export const aiAPI = {
  async startSession(message, agentType = null, teacherStyle = null) {
    const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    const body = { message, session_id: sessionId }
    if (agentType) body.agent_type = agentType
    if (teacherStyle) body.teacher_style = teacherStyle
    const res = await api.post(`/ai/tutor/${sessionId}`, body)
    return res.data || res
  },

  async listAgents() {
    const res = await api.get('/ai/agents')
    return res.data || res
  },

  async startPipeline(message, agentSequence) {
    const sessionId = `pipeline_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    const res = await api.post(`/ai/pipeline/${sessionId}`, {
      message,
      agent_sequence: agentSequence,
      session_id: sessionId
    })
    return res.data || res
  },

  async switchAgent(sessionId, agentType) {
    const res = await api.post(`/ai/switch/${sessionId}`, {
      session_id: sessionId,
      agent_type: agentType
    })
    return res.data || res
  }
}

export default api
