import { defineStore } from 'pinia'
import { userAPI, authAPI } from '@/services/api'

export const useUserStore = defineStore('user', {
  state: () => ({
    // 用户信息
    userInfo: {
      id: 0,
      nickname: '加载中...',
      avatar: '👨‍🎓',
      phone: '',
      grade: '',
      subjects: [],
      level: 0,
      xp: 0,
      xpToNextLevel: 0,
      streak: 0,
      totalLearningHours: 0,
      totalLearningCount: 0
    },
    // 学习历史
    learningHistory: [],
    // 成就列表
    achievements: [],
    // 加载状态
    loading: false,
    error: null,
    // Token
    token: localStorage.getItem('token') || '',
    // 3D形象
    avatar: {
      base: 1,
      hair: 3,
      clothes: 2,
      accessories: 1,
      expression: 'focus'
    },
    // 设置
    settings: {
      voiceType: 'female',
      voiceSpeed: 'medium',
      fontSize: 'medium',
      notifications: true,
      teacherStyle: localStorage.getItem('teacherStyle') || 'default',
      studyCompanions: JSON.parse(localStorage.getItem('studyCompanions') || '[]')
    }
  }),
  getters: {
    xpProgress: (state) => state.userInfo.xpToNextLevel > 0
      ? (state.userInfo.xp / state.userInfo.xpToNextLevel * 100).toFixed(1)
      : 0,
    unlockedAchievements: (state) => state.achievements.filter(a => a.unlocked),
    lockedAchievements: (state) => state.achievements.filter(a => !a.unlocked),
    isLoggedIn: (state) => !!state.token
  },
  actions: {
    /** 从后端加载用户数据 */
    async fetchProfile() {
      this.loading = true
      this.error = null
      try {
        const data = await userAPI.getProfile()
        this.userInfo = { ...this.userInfo, ...data }
      } catch (err) {
        console.warn('获取用户资料失败，使用本地数据:', err.message)
        this.userInfo = { ...this.userInfo, nickname: '离线模式' }
      } finally {
        this.loading = false
      }
    },

    /** 加载学习历史 */
    async fetchHistory() {
      try {
        const data = await userAPI.getHistory()
        if (Array.isArray(data)) {
          this.learningHistory = data
        }
      } catch (err) {
        console.warn('获取历史失败:', err.message)
      }
    },

    /** 加载成就列表 */
    async fetchAchievements() {
      try {
        const data = await userAPI.getAchievements()
        if (Array.isArray(data)) {
          this.achievements = data
        }
      } catch (err) {
        console.warn('获取成就失败:', err.message)
      }
    },

    /** 登录 */
    async login(username, password) {
      try {
        const data = await authAPI.login(username, password)
        if (!data) throw new Error('登录失败：无返回数据')
        this.token = data.access_token
        localStorage.setItem('token', data.access_token)
        // 从登录响应中直接获取基本信息
        this.userInfo = {
          ...this.userInfo,
          id: data.user_id || 0,
          nickname: data.nickname || data.username || '用户',
          username: data.username || '',
          level: data.level || 1,
          xp: data.xp || 0,
          streak: data.streak || 0,
          totalLearningHours: data.totalLearningHours || 0,
          totalLearningCount: data.totalLearningCount || 0,
          xpToNextLevel: data.xpToNextLevel || 100
        }
        // 异步拉取完整用户数据（不阻塞跳转）
        this.fetchProfile().catch(() => {})
        return true
      } catch (err) {
        this.error = err.message || '登录失败'
        return false
      }
    },

    /** 退出登录 */
    logout() {
      authAPI.logout()
      this.token = ''
      localStorage.removeItem('token')
      this.userInfo = {
        id: 0, nickname: '未登录', avatar: '👨‍🎓', phone: '', grade: '',
        subjects: [], level: 0, xp: 0, xpToNextLevel: 0, streak: 0, totalLearningHours: 0, totalLearningCount: 0
      }
      this.learningHistory = []
      this.achievements = []
      this.error = null
    },

    /** 初始化 - 加载所有数据 */
    async init() {
      this.loading = true
      await Promise.allSettled([
        this.fetchProfile(),
        this.fetchHistory(),
        this.fetchAchievements()
      ])
      this.loading = false
    },

    addXP(amount) {
      this.userInfo.xp += amount
      if (this.userInfo.xp >= this.userInfo.xpToNextLevel) {
        this.userInfo.level++
        this.userInfo.xp -= this.userInfo.xpToNextLevel
        this.userInfo.xpToNextLevel = Math.floor(this.userInfo.xpToNextLevel * 1.2)
      }
      // 异步持久化到后端，失败时静默处理
      userAPI.addXP(amount).then(data => {
        if (data) {
          // 用后端返回的真实值覆盖，避免前后端升级计算不一致
          this.userInfo.xp = data.xp ?? this.userInfo.xp
          this.userInfo.level = data.level ?? this.userInfo.level
          this.userInfo.xpToNextLevel = data.xpToNextLevel ?? this.userInfo.xpToNextLevel
        }
      }).catch(err => {
        console.warn('经验值同步失败:', err.message)
      })
    },

    async incrementLearningCount() {
      try {
        const data = await userAPI.incrementLearningCount()
        if (data?.totalLearningCount !== undefined) {
          this.userInfo.totalLearningCount = data.totalLearningCount
        } else {
          this.userInfo.totalLearningCount = (this.userInfo.totalLearningCount || 0) + 1
        }
      } catch (err) {
        console.warn('递增学习次数失败:', err.message)
        this.userInfo.totalLearningCount = (this.userInfo.totalLearningCount || 0) + 1
      }
    },

    updateExpression(expr) {
      this.avatar.expression = expr
    }
  }
})

export const useClassStore = defineStore('classroom', {
  state: () => ({
    currentOutline: null,
    currentModuleIndex: 0,
    chatMessages: [],
    answers: [],
    knowledgePoints: {
      labels: ['理解', '应用', '分析', '记忆', '创新'],
      data: [85, 72, 65, 90, 45]
    },
    status: 'idle',
    currentAgent: 'tutor',
    streamingContent: ''
  }),
  actions: {
    setOutline(outline) {
      this.currentOutline = outline
    },
    addMessage(msg) {
      this.chatMessages.push({
        ...msg,
        id: Date.now(),
        timestamp: new Date().toLocaleTimeString()
      })
    },
    appendStreaming(token) {
      this.streamingContent += token
    },
    finishStreaming() {
      if (this.streamingContent) {
        this.addMessage({
          role: 'assistant',
          content: this.streamingContent
        })
        this.streamingContent = ''
      }
    },
    addAnswer(answer) {
      this.answers.push(answer)
    },
    switchAgent(agentType) {
      this.currentAgent = agentType
    }
  }
})
