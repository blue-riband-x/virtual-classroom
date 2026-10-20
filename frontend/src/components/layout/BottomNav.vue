<template>
  <nav class="bottom-nav">
    <router-link to="/home" class="nav-item" :class="{ active: $route.path === '/home' }">
      <span class="nav-icon">🏠</span>
      <span class="nav-text">首页</span>
      <span class="nav-dot"></span>
    </router-link>
    <router-link to="/plan" class="nav-item" :class="{ active: $route.path === '/plan' }">
      <span class="nav-icon">📖</span>
      <span class="nav-text">学习</span>
      <span class="nav-dot"></span>
    </router-link>
    <a class="nav-item nav-item-main" :class="{ active: $route.path === '/classroom' }" @click="openSelector">
      <div class="main-btn">
        <span class="nav-icon-main">▶</span>
        <div class="main-glow"></div>
      </div>
    </a>
    <router-link to="/game" class="nav-item" :class="{ active: $route.path === '/game' }">
      <span class="nav-icon">🏅</span>
      <span class="nav-text">成就</span>
      <span class="nav-dot"></span>
    </router-link>
    <router-link to="/profile" class="nav-item" :class="{ active: $route.path === '/profile' }">
      <span class="nav-icon">👤</span>
      <span class="nav-text">我的</span>
      <span class="nav-dot"></span>
    </router-link>
  </nav>

  <!-- 选择大纲弹窗 -->
  <transition name="fade">
    <div v-if="showSelector" class="selector-overlay" @click.self="showSelector = false">
      <div class="selector-modal">
        <h3 class="sel-title">选择学习大纲</h3>
        <p class="sel-subtitle">请先选择一份大纲开始AI课堂</p>

        <div class="sel-loading" v-if="loading">加载中...</div>

        <div class="sel-list" v-if="!loading && outlines.length">
          <div
            v-for="o in outlines"
            :key="o.id"
            class="sel-item"
            :class="{ selected: selectedId === o.id }"
            @click="selectedId = o.id"
          >
            <div class="sel-item-header">
              <span class="sel-topic">{{ o.title }}</span>
              <span class="sel-level">{{ levelMap[o.level] || o.level }}</span>
            </div>
            <div class="sel-meta">
              <span>{{ o.module_count }} 模块</span>
              <span>{{ o.total_duration }} 分钟</span>
            </div>
          </div>
        </div>

        <div class="sel-empty" v-if="!loading && !outlines.length">
          <p>还没有大纲</p>
          <button class="sel-goto" @click="goCreateOutline">去创建大纲</button>
        </div>

        <div class="sel-actions">
          <button class="sel-cancel" @click="showSelector = false">取消</button>
          <button class="sel-confirm" :disabled="!selectedId" @click="startClassroom">
            开始AI课堂
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const showSelector = ref(false)
const loading = ref(false)
const outlines = ref([])
const selectedId = ref(null)
const levelMap = { beginner: '入门', intermediate: '中级', advanced: '高级' }

const openSelector = async () => {
  showSelector.value = true
  selectedId.value = null
  loading.value = true
  try {
    const token = localStorage.getItem('token') || ''
    const res = await fetch('/api/v1/outline/my', {
      headers: { Authorization: `Bearer ${token}` }
    })
    if (res.ok) {
      const json = await res.json()
      // Java 后端返回 ApiResponse 格式: {code, data, message}
      const rawList = Array.isArray(json) ? json : (json.data || [])
      // modulesData 可能是 JSON 字符串，需要解析；字段名统一
      outlines.value = rawList.map(o => ({
        ...o,
        modules_data: typeof o.modulesData === 'string' ? JSON.parse(o.modulesData) : (o.modulesData || o.modules_data || []),
        // 同时提供 snake_case 别名，供模板使用
        module_count: o.moduleCount || o.module_count || 0,
        total_duration: o.totalDuration || o.total_duration || 0
      }))
    }
  } catch (e) {
    outlines.value = []
  }
  loading.value = false
}

const startClassroom = () => {
  if (!selectedId.value) return
  showSelector.value = false
  router.push(`/classroom?outline_id=${selectedId.value}`)
}

const goCreateOutline = () => {
  showSelector.value = false
  router.push('/plan')
}
</script>

<style scoped>
.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 72px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(12px);
  border-top: 2px solid var(--border);
  display: flex;
  justify-content: space-around;
  align-items: flex-end;
  z-index: 100;
  padding: 0 0.5rem;
  padding-bottom: env(safe-area-inset-bottom);
  box-shadow: 0 -4px 16px rgba(74, 144, 217, 0.08);
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
  padding: 0.5rem 1rem 0.375rem;
  text-decoration: none;
  color: var(--text-muted);
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  position: relative;
  flex: 1;
  cursor: pointer;
}

.nav-item:hover .nav-icon { transform: translateY(-2px); }

.nav-item.active .nav-icon { transform: translateY(-4px) scale(1.15); }
.nav-item.active .nav-text { color: var(--primary-dark); font-weight: 700; }
.nav-item.active .nav-dot { transform: scaleX(1); background: var(--primary); }

.nav-icon { font-size: 1.5rem; transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1); }
.nav-text { font-size: 0.6875rem; font-weight: 600; color: var(--text-muted); transition: all 0.3s ease; }

.nav-dot {
  position: absolute; top: 0; left: 50%; transform: translateX(-50%) scaleX(0);
  width: 4px; height: 4px; border-radius: 2px; background: var(--primary); transition: all 0.3s ease;
}

.nav-item-main { padding: 0; flex: none; width: 60px; }

.main-btn {
  position: relative; width: 56px; height: 56px; margin-top: -16px;
  background: linear-gradient(135deg, #7CB8E4, #4A90D9); border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 4px 0 rgba(58, 123, 200, 0.5), 0 8px 20px rgba(74, 144, 217, 0.3);
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1); border: 3px solid white;
}
.main-btn:active { transform: translateY(2px); box-shadow: 0 2px 0 rgba(58, 123, 200, 0.5); }
.nav-item-main.active .main-btn { background: linear-gradient(135deg, #5B9BD5, #3A7BC8); box-shadow: 0 4px 0 rgba(58, 123, 200, 0.5), 0 8px 24px rgba(74, 144, 217, 0.5); }
.nav-icon-main { font-size: 1.25rem; color: white; position: relative; z-index: 1; }

.main-glow {
  position: absolute; inset: -4px; border-radius: 50%;
  background: linear-gradient(135deg, rgba(74, 144, 217, 0.3), transparent);
  animation: mainPulse 2s ease-in-out infinite;
}
@keyframes mainPulse {
  0%, 100% { transform: scale(1); opacity: 0.5; }
  50% { transform: scale(1.2); opacity: 0; }
}

/* Selector Modal */
.selector-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.45); z-index: 200;
  display: flex; align-items: center; justify-content: center; padding: 20px;
}
.selector-modal {
  background: white; border-radius: 20px; padding: 24px; width: 100%; max-width: 400px;
  max-height: 80vh; display: flex; flex-direction: column; gap: 16px;
}
.sel-title { font-size: 18px; font-weight: 700; color: #1a1a2e; text-align: center; }
.sel-subtitle { font-size: 13px; color: #999; text-align: center; margin: -8px 0 0; }
.sel-loading { text-align: center; color: #999; padding: 20px; }

.sel-list { display: flex; flex-direction: column; gap: 8px; overflow-y: auto; max-height: 50vh; }
.sel-item {
  padding: 14px 16px; border-radius: 14px; border: 2px solid #eee; cursor: pointer;
  transition: all 0.2s; display: flex; flex-direction: column; gap: 4px;
}
.sel-item:hover { border-color: #7CB8E4; background: #F0F6FF; }
.sel-item.selected { border-color: #4A90D9; background: linear-gradient(135deg, #F0F6FF, #E3F0FA); }
.sel-item-header { display: flex; justify-content: space-between; align-items: center; }
.sel-topic { font-size: 14px; font-weight: 600; color: #1a1a2e; }
.sel-level { font-size: 11px; padding: 2px 8px; border-radius: 8px; background: rgba(74,144,217,0.1); color: #4A90D9; }
.sel-meta { display: flex; gap: 12px; font-size: 11px; color: #bbb; }

.sel-empty { text-align: center; padding: 20px; color: #999; }
.sel-goto { margin-top: 8px; padding: 8px 20px; border: 1px solid #4A90D9; border-radius: 8px; background: white; color: #4A90D9; cursor: pointer; }

.sel-actions { display: flex; gap: 10px; }
.sel-cancel { flex: 1; padding: 12px; border: 1px solid #eee; border-radius: 12px; background: #f5f5f5; color: #666; font-size: 14px; cursor: pointer; }
.sel-confirm {
  flex: 2; padding: 12px; border: none; border-radius: 12px;
  background: linear-gradient(135deg, #7CB8E4, #4A90D9); color: white; font-size: 14px; font-weight: 600; cursor: pointer;
}
.sel-confirm:disabled { opacity: 0.4; cursor: not-allowed; }

.fade-enter-active, .fade-leave-active { transition: opacity 0.25s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
