<template>
  <div class="game-page">
    <Navbar />
    
    <div class="game-container">
      <!-- 用户状态卡片 -->
      <div class="user-status-card">
        <div class="avatar-section">
          <div class="user-avatar">{{ userStore.userInfo.avatar }}</div>
          <div class="avatar-level-badge">Lv.{{ userStore.userInfo.level }}</div>
        </div>
        <div class="user-info">
          <h2>{{ userStore.userInfo.nickname }}</h2>
          <div class="user-stats-row">
            <div class="stat-item">
              <span class="stat-icon">🔥</span>
              <span class="stat-value">{{ userStore.userInfo.streak }}</span>
              <span class="stat-label">天连胜</span>
            </div>
            <div class="stat-item">
              <span class="stat-icon">🏆</span>
              <span class="stat-value">{{ userStore.unlockedAchievements.length }}</span>
              <span class="stat-label">成就数</span>
            </div>
            <div class="stat-item">
              <span class="stat-icon">⏱️</span>
              <span class="stat-value">{{ userStore.userInfo.totalLearningHours }}h</span>
              <span class="stat-label">学习时长</span>
            </div>
          </div>
        </div>
        <XPProgress 
          :current="userStore.userInfo.xp" 
          :total="userStore.userInfo.xpToNextLevel"
          :level="userStore.userInfo.level"
          class="xp-progress-section"
        />
      </div>

      <!-- Streak 火焰展示 -->
      <div class="streak-showcase">
        <div class="streak-visual" :class="{ active: userStore.userInfo.streak > 0 }">
          <div class="flame-container">
            <span class="flame" v-for="i in 3" :key="i" :style="{ animationDelay: i * 0.2 + 's' }">
              🔥
            </span>
          </div>
          <div class="streak-count">{{ userStore.userInfo.streak }} 天</div>
          <div class="streak-label">连续学习</div>
        </div>
        <div class="streak-rewards">
          <div class="reward-item" :class="{ unlocked: userStore.userInfo.streak >= 3 }">
            <span class="reward-icon">3天 +10%</span>
            <span class="reward-xp">XP</span>
          </div>
          <div class="reward-item" :class="{ unlocked: userStore.userInfo.streak >= 7 }">
            <span class="reward-icon">7天 +25%</span>
            <span class="reward-xp">XP</span>
          </div>
          <div class="reward-item" :class="{ unlocked: userStore.userInfo.streak >= 30 }">
            <span class="reward-icon">30天 +50%</span>
            <span class="reward-xp">XP</span>
          </div>
        </div>
      </div>

      <!-- 成就墙 -->
      <div class="achievements-section">
        <div class="section-header">
          <h2>🏅 成就徽章</h2>
          <div class="filter-tabs">
            <button 
              class="tab" 
              :class="{ active: filter === 'all' }"
              @click="filter = 'all'"
            >全部</button>
            <button 
              class="tab" 
              :class="{ active: filter === 'unlocked' }"
              @click="filter = 'unlocked'"
            >已解锁</button>
            <button 
              class="tab" 
              :class="{ active: filter === 'locked' }"
              @click="filter = 'locked'"
            >进行中</button>
          </div>
        </div>
        
        <div class="achievements-grid">
          <AchievementCard 
            v-for="ach in filteredAchievements" 
            :key="ach.id"
            :achievement="ach"
            class="achievement-item"
          />
        </div>
      </div>

      <!-- 虚拟形象 -->
      <div class="avatar-section-full">
        <h2>🎭 我的虚拟形象</h2>
        <div class="avatar-customize">
          <div class="avatar-preview">
            <div class="avatar-display">
              <span class="avatar-base">{{ userStore.userInfo.avatar }}</span>
              <span class="avatar-accessory">🎧</span>
            </div>
            <div class="expression-selector">
              <button 
                v-for="(expr, key) in expressions" 
                :key="key"
                class="expr-btn"
                :class="{ active: userStore.avatar.expression === key }"
                @click="setExpression(key)"
              >
                {{ expr }}
              </button>
            </div>
          </div>
          <div class="avatar-items">
            <h4>已解锁物品</h4>
            <div class="items-grid">
              <div class="item unlocked">
                <span>👓</span>
                <span class="item-name">眼镜</span>
              </div>
              <div class="item unlocked">
                <span>🎧</span>
                <span class="item-name">耳机</span>
              </div>
              <div class="item locked">
                <span>🎩</span>
                <span class="item-name">礼帽</span>
                <span class="item-lock">🔒</span>
              </div>
              <div class="item locked">
                <span>👑</span>
                <span class="item-name">王冠</span>
                <span class="item-lock">🔒</span>
              </div>
              <div class="item locked">
                <span>🕶️</span>
                <span class="item-name">墨镜</span>
                <span class="item-lock">🔒</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- XP明细 -->
      <div class="xp-details-section">
        <h2>📊 XP获取明细</h2>
        <div class="xp-summary">
          <div class="summary-item">
            <span class="summary-icon">📚</span>
            <span class="summary-label">课堂学习</span>
            <span class="summary-value">+320</span>
          </div>
          <div class="summary-item">
            <span class="summary-icon">✅</span>
            <span class="summary-label">答题正确</span>
            <span class="summary-value">+156</span>
          </div>
          <div class="summary-item">
            <span class="summary-icon">❓</span>
            <span class="summary-label">提问奖励</span>
            <span class="summary-value">+45</span>
          </div>
          <div class="summary-item">
            <span class="summary-icon">🥚</span>
            <span class="summary-label">知识彩蛋</span>
            <span class="summary-value">+25</span>
          </div>
          <div class="summary-item">
            <span class="summary-icon">🔥</span>
            <span class="summary-label">连胜加成</span>
            <span class="summary-value">+80</span>
          </div>
        </div>
        <div class="weekly-chart">
          <h4>本周XP趋势</h4>
          <div class="chart-container">
            <div class="bar-chart">
              <div class="bar-item" v-for="(val, day) in weeklyXP" :key="day">
                <div class="bar" :style="{ height: (val / maxXP * 100) + '%' }">
                  <span class="bar-value">{{ val }}</span>
                </div>
                <span class="bar-label">{{ day }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <BottomNav />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import Navbar from '../../components/layout/Navbar.vue'
import BottomNav from '../../components/layout/BottomNav.vue'
import AchievementCard from '../../components/common/AchievementCard.vue'
import XPProgress from '../../components/common/XPProgress.vue'
import { useUserStore } from '../../stores'

const userStore = useUserStore()

const filter = ref('all')

const expressions = {
  focus: '🧐',
  happy: '😄',
  confused: '🤔',
  tired: '😪'
}

const weeklyXP = {
  '周一': 120,
  '周二': 85,
  '周三': 156,
  '周四': 92,
  '周五': 145,
  '周六': 68,
  '周日': 110
}

const maxXP = computed(() => Math.max(...Object.values(weeklyXP)))

const filteredAchievements = computed(() => {
  if (filter.value === 'unlocked') return userStore.achievements.filter(a => a.unlocked)
  if (filter.value === 'locked') return userStore.achievements.filter(a => !a.unlocked)
  return userStore.achievements
})

const setExpression = (expr) => {
  userStore.updateExpression(expr)
}
</script>

<style scoped>
.game-page {
  min-height: 100vh;
  padding-top: 64px;
  padding-bottom: 80px;
  background: linear-gradient(180deg, var(--bg-primary) 0%, #1a1a2e 100%);
}

.game-container {
  max-width: 900px;
  margin: 0 auto;
  padding: 1.5rem;
}

/* User Status Card */
.user-status-card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  border: 1px solid var(--border);
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 1.5rem;
  align-items: center;
}

.avatar-section {
  position: relative;
}

.user-avatar {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  border-radius: 50%;
  font-size: 2.5rem;
}

.avatar-level-badge {
  position: absolute;
  bottom: -4px;
  right: -4px;
  padding: 0.25rem 0.5rem;
  background: linear-gradient(135deg, #ffd700, #ffa500);
  color: #1a1a2e;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 700;
}

.user-info h2 {
  font-size: 1.25rem;
  margin-bottom: 0.75rem;
}

.user-stats-row {
  display: flex;
  gap: 1.5rem;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.stat-icon {
  font-size: 1rem;
}

.stat-value {
  font-weight: 700;
}

.stat-label {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.xp-progress-section {
  min-width: 200px;
}

/* Streak Showcase */
.streak-showcase {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  border: 1px solid var(--border);
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 2rem;
  align-items: center;
}

.streak-visual {
  text-align: center;
}

.flame-container {
  display: flex;
  justify-content: center;
  gap: 0.25rem;
  margin-bottom: 0.5rem;
  height: 48px;
}

.flame {
  font-size: 2rem;
  opacity: 0.3;
  transition: all 0.3s ease;
}

.streak-visual.active .flame {
  opacity: 1;
  animation: flameDance 0.5s ease-in-out infinite alternate;
}

@keyframes flameDance {
  from { transform: scale(1) translateY(0); }
  to { transform: scale(1.1) translateY(-4px); }
}

.streak-count {
  font-size: 1.5rem;
  font-weight: 700;
  color: #f97316;
}

.streak-label {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.streak-rewards {
  display: flex;
  gap: 1rem;
}

.reward-item {
  padding: 0.75rem 1rem;
  background: var(--bg-secondary);
  border-radius: var(--radius);
  text-align: center;
  opacity: 0.5;
  border: 1px dashed var(--border);
  transition: all 0.3s ease;
}

.reward-item.unlocked {
  opacity: 1;
  border-style: solid;
  border-color: var(--warning);
  background: rgba(245, 158, 11, 0.1);
}

.reward-icon {
  font-size: 0.875rem;
  font-weight: 600;
  display: block;
}

.reward-xp {
  font-size: 0.625rem;
  color: var(--warning);
}

/* Achievements */
.achievements-section {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  border: 1px solid var(--border);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.section-header h2 {
  font-size: 1.25rem;
}

.filter-tabs {
  display: flex;
  gap: 0.5rem;
}

.tab {
  padding: 0.5rem 1rem;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 9999px;
  color: var(--text-secondary);
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.tab.active {
  background: var(--primary);
  border-color: var(--primary);
  color: white;
}

.achievements-grid {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

/* Avatar Section */
.avatar-section-full {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  border: 1px solid var(--border);
}

.avatar-section-full h2 {
  font-size: 1.25rem;
  margin-bottom: 1.5rem;
}

.avatar-customize {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 2rem;
}

.avatar-preview {
  text-align: center;
}

.avatar-display {
  width: 120px;
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  border-radius: 50%;
  margin: 0 auto 1rem;
  position: relative;
}

.avatar-base {
  font-size: 4rem;
}

.avatar-accessory {
  position: absolute;
  top: 0;
  right: 0;
  font-size: 1.5rem;
}

.expression-selector {
  display: flex;
  gap: 0.5rem;
  justify-content: center;
}

.expr-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-secondary);
  border: 2px solid var(--border);
  border-radius: 50%;
  font-size: 1.25rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.expr-btn.active {
  border-color: var(--primary);
  background: rgba(102, 126, 234, 0.2);
}

.avatar-items h4 {
  font-size: 0.875rem;
  color: var(--text-muted);
  margin-bottom: 1rem;
}

.items-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 0.75rem;
}

.item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.75rem;
  background: var(--bg-secondary);
  border-radius: var(--radius);
  font-size: 1.5rem;
  position: relative;
  opacity: 0.5;
}

.item.unlocked {
  opacity: 1;
  border: 1px solid var(--border);
}

.item-name {
  font-size: 0.625rem;
  margin-top: 0.25rem;
  color: var(--text-secondary);
}

.item-lock {
  position: absolute;
  top: 0;
  right: 0;
  font-size: 0.75rem;
}

/* XP Details */
.xp-details-section {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 1.5rem;
  border: 1px solid var(--border);
}

.xp-details-section h2 {
  font-size: 1.25rem;
  margin-bottom: 1.5rem;
}

.xp-summary {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.summary-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1rem;
  background: var(--bg-secondary);
  border-radius: var(--radius);
  text-align: center;
}

.summary-icon {
  font-size: 1.25rem;
  margin-bottom: 0.25rem;
}

.summary-label {
  font-size: 0.625rem;
  color: var(--text-muted);
  margin-bottom: 0.25rem;
}

.summary-value {
  font-size: 1rem;
  font-weight: 700;
  color: var(--warning);
}

.weekly-chart h4 {
  font-size: 0.875rem;
  color: var(--text-muted);
  margin-bottom: 1rem;
}

.chart-container {
  height: 150px;
}

.bar-chart {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  height: 100%;
  padding: 0 1rem;
}

.bar-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
}

.bar {
  width: 24px;
  background: linear-gradient(to top, var(--primary), var(--secondary));
  border-radius: 4px 4px 0 0;
  min-height: 4px;
  position: relative;
  transition: height 0.5s ease;
}

.bar-value {
  position: absolute;
  top: -20px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 0.625rem;
  font-weight: 600;
  color: var(--text-secondary);
}

.bar-label {
  font-size: 0.625rem;
  color: var(--text-muted);
  margin-top: 0.5rem;
}

@media (max-width: 768px) {
  .user-status-card {
    grid-template-columns: 1fr;
    text-align: center;
  }
  
  .avatar-section {
    margin: 0 auto;
  }
  
  .user-stats-row {
    justify-content: center;
  }
  
  .xp-progress-section {
    min-width: auto;
  }
  
  .streak-showcase {
    grid-template-columns: 1fr;
    text-align: center;
  }
  
  .streak-rewards {
    justify-content: center;
  }
  
  .avatar-customize {
    grid-template-columns: 1fr;
  }
  
  .xp-summary {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>
