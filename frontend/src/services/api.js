/**
 * API服务 - HTTP客户端
 * 统一处理 Java ApiResponse 信封：{ code, message, data }
 */
const BASE_URL = '/api/v1'

class ApiClient {
  constructor() {
    this.token = localStorage.getItem('token') || ''
  }

  /** 401 时跳转登录页 */
  _handleUnauthorized() {
    this.token = ''
    localStorage.removeItem('token')
    // 避免重复跳转
    if (window.location.pathname !== '/login') {
      window.location.href = '/login'
    }
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

    let response
    try {
      response = await fetch(`${BASE_URL}${url}`, config)
    } catch (err) {
      throw new Error('网络连接失败，请检查网络')
    }

    // HTTP 层面错误
    if (!response.ok) {
      if (response.status === 401) {
        this._handleUnauthorized()
      }
      // 尝试解析后端返回的错误消息
      var errMsg = ''
      try {
        var errData = await response.json()
        errMsg = errData.message || errData.detail || ''
      } catch (e) { /* ignore parse error */ }
      throw new Error(errMsg || '请求失败(' + response.status + ')')
    }

    // 解析 JSON 响应体
    var body
    try {
      body = await response.json()
    } catch (e) {
      throw new Error('服务器返回数据格式异常')
    }

    // 兼容 ApiResponse 信封：{ code, message, data }
    if (typeof body.code === 'number' && 'data' in body) {
      if (body.code !== 200) {
        throw new Error(body.message || '操作失败')
      }
      return body.data
    }

    // 直返格式
    return body
  }

  get(url, params) {
    const query = params ? '?' + new URLSearchParams(params).toString() : ''
    return this.request(`${url}${query}`)
  }

  post(url, body) {
    return this.request(url, { method: 'POST', body: JSON.stringify(body) })
  }

  put(url, body) {
    return this.request(url, { method: 'PUT', body: JSON.stringify(body) })
  }

  delete(url) {
    return this.request(url, { method: 'DELETE' })
  }
}

export const api = new ApiClient()

// ========== 认证API ==========
export const authAPI = {
  async login(username, password) {
    const data = await api.post('/auth/login', { username, password })
    if (!data || !data.access_token) {
      throw new Error('登录返回数据异常')
    }
    api.setToken(data.access_token)
    return data
  },

  async register(form) {
    const data = await api.post('/auth/register', form)
    if (!data || !data.access_token) {
      throw new Error('注册返回数据异常')
    }
    api.setToken(data.access_token)
    return data
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
  async getProfile() { return await api.get('/users/profile') },
  async getHistory() { return await api.get('/users/history') },
  async getAchievements() { return await api.get('/users/achievements') },
  async incrementLearningCount() { return await api.post('/users/learning-count') },
  async addXP(amount) { return await api.post('/users/add-xp', { amount }) }
}

// ========== AI交互API ==========
export const aiAPI = {
  async startSession(message, agentType = null, teacherStyle = null) {
    const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    const body = { message, session_id: sessionId }
    if (agentType) body.agent_type = agentType
    if (teacherStyle) body.teacher_style = teacherStyle
    return await api.post(`/ai/tutor/${sessionId}`, body)
  },
  async listAgents() { return await api.get('/ai/agents') },
  async startPipeline(message, agentSequence) {
    const sessionId = `pipeline_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    return await api.post(`/ai/pipeline/${sessionId}`, { message, agent_sequence: agentSequence, session_id: sessionId })
  },
  async switchAgent(sessionId, agentType) {
    return await api.post(`/ai/switch/${sessionId}`, { session_id: sessionId, agent_type: agentType })
  }
}

export default api
