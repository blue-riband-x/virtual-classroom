<template>
  <div class="leaderboard-page">
    <Navbar />
    
    <div class="leaderboard-container">
      <!-- 头部筛选 -->
      <header class="leaderboard-header">
        <h1>🏆 排行榜</h1>
        <div class="filter-group">
          <button 
            v-for="type in rankTypes" 
            :key="type.value"
            class="filter-btn"
            :class="{ active: currentType === type.value }"
            @click="currentType = type.value"
          >
            {{ type.label }}
          </button>
        </div>
      </header>

      <!-- 冠军展示 -->
      <div class="champions">
        <div class="champion-card second" v-if="sortedList[1]">
          <div class="champion-avatar">{{ sortedList[1].avatar }}</div>
          <div class="champion-crown">🥈</div>
          <div class="champion-name">{{ sortedList[1].nickname }}</div>
          <div class="champion-level">Lv.{{ sortedList[1].level }}</div>
          <div class="champion-xp">{{ sortedList[1].xp.toLocaleString() }} XP</div>
        </div>
        
        <div class="champion-card first" v-if="sortedList[0]">
          <div class="champion-avatar">{{ sortedList[0].avatar }}</div>
          <div class="champion-crown">👑</div>
          <div class="champion-name">{{ sortedList[0].nickname }}</div>
          <div class="champion-level">Lv.{{ sortedList[0].level }}</div>
          <div class="champion-xp">{{ sortedList[0].xp.toLocaleString() }} XP</div>
        </div>
        
        <div class="champion-card third" v-if="sortedList[2]">
          <div class="champion-avatar">{{ sortedList[2].avatar }}</div>
          <div class="champion-crown">🥉</div>
          <div class="champion-name">{{ sortedList[2].nickname }}</div>
          <div class="champion-level">Lv.{{ sortedList[2].level }}</div>
          <div class="champion-xp">{{ sortedList[2].xp.toLocaleString() }} XP</div>
        </div>
      </div>

      <!-- 范围切换 -->
      <div class="scope-tabs">
        <button 
          v-for="scope in scopes" 
          :key="scope.value"
          class="scope-btn"
          :class="{ active: currentScope === scope.value }"
          @click="currentScope = scope.value"
        >
          {{ scope.label }}
        </button>
      </div>

      <!-- 排行榜列表 -->
      <div class="rank-list">
        <div class="rank-item" v-for="item in displayList" :key="item.rank">
          <div class="rank-number" :class="getRankClass(item.rank)">
            {{ item.rank <= 3 ? getRankEmoji(item.rank) : item.rank }}
          </div>
          <div class="rank-avatar">{{ item.avatar }}</div>
          <div class="rank-info">
            <div class="rank-name">
              {{ item.nickname }}
              <span class="is-me" v-if="item.nickname === '学海无涯'">（我）</span>
            </div>
            <div class="rank-meta">
              <span class="level-badge">Lv.{{ item.level }}</span>
              <span class="streak" v-if="item.streak > 0">🔥 {{ item.streak }}天</span>
            </div>
          </div>
          <div class="rank-xp">
            <span class="xp-value">{{ item.xp.toLocaleString() }}</span>
            <span class="xp-label">XP</span>
          </div>
          <div class="rank-change" :class="getChangeClass(item.change)">
            <span v-if="item.change > 0">↑ {{ item.change }}</span>
            <span v-else-if="item.change < 0">↓ {{ Math.abs(item.change) }}</span>
            <span v-else>—</span>
          </div>
        </div>
      </div>

      <!-- 自己的排名 -->
      <div class="my-rank" v-if="myRank">
        <div class="my-rank-label">我的排名</div>
        <div class="my-rank-content">
          <div class="my-rank-number">{{ myRank.rank }}</div>
          <div class="my-rank-avatar">{{ myRank.avatar }}</div>
          <div class="my-rank-info">
            <div class="my-rank-name">{{ myRank.nickname }}</div>
            <div class="my-rank-meta">
              <span class="level-badge">Lv.{{ myRank.level }}</span>
              <span class="xp-value">{{ myRank.xp.toLocaleString() }} XP</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 上周之星 -->
      <div class="weekly-star">
        <div class="star-header">
          <span class="star-icon">⭐</span>
          <span class="star-title">上周之星</span>
        </div>
        <div class="star-winners">
          <div class="star-winner" v-for="(winner, i) in weeklyWinners" :key="i">
            <div class="winner-avatar">{{ winner.avatar }}</div>
            <div class="winner-name">{{ winner.nickname }}</div>
            <div class="winner-reward">{{ winner.reward }}</div>
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

// 排行榜数据（后续可接入后端API）
const leaderboardData = [
  { rank: 1, nickname: '编程小王子', avatar: '👨‍💻', level: 28, xp: 15680, streak: 45, change: 0 },
  { rank: 2, nickname: 'AI学习狂人', avatar: '🤖', level: 25, xp: 14250, streak: 32, change: 2 },
  { rank: 3, nickname: '数据分析师', avatar: '📊', level: 24, xp: 13800, streak: 28, change: -1 },
  { rank: 4, nickname: '前端开发者', avatar: '🎨', level: 23, xp: 12500, streak: 21, change: 1 },
  { rank: 5, nickname: '算法爱好者', avatar: '🧮', level: 22, xp: 11900, streak: 18, change: -2 },
  { rank: 6, nickname: '后端新手', avatar: '⚙️', level: 21, xp: 11200, streak: 15, change: 0 },
  { rank: 7, nickname: '全栈梦想家', avatar: '🚀', level: 20, xp: 10500, streak: 12, change: 3 },
]

const rankTypes = [
  { label: '总XP', value: 'total' },
  { label: '本周XP', value: 'weekly' },
  { label: '连续天数', value: 'streak' },
  { label: '知识掌握', value: 'knowledge' }
]

const scopes = [
  { label: '全校', value: 'school' },
  { label: '全年级', value: 'grade' },
  { label: '同专业', value: 'major' }
]

const currentType = ref('total')
const currentScope = ref('school')

const sortedList = computed(() => {
  let list = [...leaderboardData]
  
  if (currentType.value === 'streak') {
    list.sort((a, b) => b.streak - a.streak)
  }
  
  return list.map((item, i) => ({
    ...item,
    rank: i + 1
  }))
})

const displayList = computed(() => {
  return sortedList.value.slice(3) // 去掉前3名
})

const myRank = computed(() => {
  const me = leaderboardData.find(item => item.nickname === '学海无涯')
  if (!me) return null
  return {
    ...me,
    rank: leaderboardData.findIndex(item => item.nickname === '学海无涯') + 1
  }
})

const weeklyWinners = [
  { avatar: '🏆', nickname: '编程小王子', reward: '专属头像框' },
  { avatar: '🥈', nickname: 'AI学习狂人', reward: '7天称号' },
  { avatar: '🥉', nickname: '数据分析师', reward: '7天称号' }
]

const getRankClass = (rank) => {
  if (rank === 1) return 'gold'
  if (rank === 2) return 'silver'
  if (rank === 3) return 'bronze'
  return ''
}

const getRankEmoji = (rank) => {
  if (rank === 1) return '🥇'
  if (rank === 2) return '🥈'
  if (rank === 3) return '🥉'
  return rank
}

const getChangeClass = (change) => {
  if (change > 0) return 'up'
  if (change < 0) return 'down'
  return ''
}
</script>

<style scoped>
.leaderboard-page {
  min-height: 100vh;
  padding-top: 64px;
  padding-bottom: 80px;
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
}

.leaderboard-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 1.5rem;
}

/* Header */
.leaderboard-header {
  text-align: center;
  margin-bottom: 2rem;
}

.leaderboard-header h1 {
  font-size: 2rem;
  margin-bottom: 1.5rem;
}

.filter-group {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.filter-btn {
  padding: 0.5rem 1.25rem;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 9999px;
  color: var(--text-secondary);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.filter-btn.active {
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  border-color: transparent;
  color: white;
}

/* Champions */
.champions {
  display: flex;
  justify-content: center;
  align-items: flex-end;
  gap: 1rem;
  margin-bottom: 2rem;
  padding: 1rem 0;
}

.champion-card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 1.5rem 1rem;
  text-align: center;
  border: 2px solid var(--border);
  position: relative;
  animation: championFloat 3s ease-in-out infinite;
}

.champion-card.first {
  order: 2;
  border-color: #ffd700;
  padding: 2rem 1.5rem;
  box-shadow: 0 0 30px rgba(255, 215, 0, 0.3);
  animation-delay: 0s;
}

.champion-card.second {
  order: 1;
  animation-delay: 0.5s;
}

.champion-card.third {
  order: 3;
  animation-delay: 1s;
}

@keyframes championFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

.champion-card.first {
  animation: championFloatFirst 3s ease-in-out infinite;
}

@keyframes championFloatFirst {
  0%, 100% { transform: translateY(0) scale(1); }
  50% { transform: translateY(-12px) scale(1.02); }
}

.champion-avatar {
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-secondary);
  border-radius: 50%;
  margin: 0 auto 0.75rem;
  font-size: 2rem;
}

.first .champion-avatar {
  width: 80px;
  height: 80px;
  font-size: 2.5rem;
}

.champion-crown {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
}

.champion-name {
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.champion-level {
  font-size: 0.75rem;
  color: var(--primary);
  margin-bottom: 0.25rem;
}

.champion-xp {
  font-size: 0.875rem;
  color: var(--warning);
  font-weight: 600;
}

/* Scope Tabs */
.scope-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  padding: 0.25rem;
  background: var(--bg-card);
  border-radius: var(--radius);
}

.scope-btn {
  flex: 1;
  padding: 0.75rem;
  background: transparent;
  border: none;
  border-radius: var(--radius);
  color: var(--text-secondary);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.scope-btn.active {
  background: var(--primary);
  color: white;
}

/* Rank List */
.rank-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.rank-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: var(--bg-card);
  border-radius: var(--radius);
  border: 1px solid var(--border);
  transition: all 0.3s ease;
}

.rank-item:hover {
  border-color: var(--primary);
  transform: translateX(4px);
}

.rank-number {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.875rem;
}

.rank-number.gold { color: #ffd700; }
.rank-number.silver { color: #c0c0c0; }
.rank-number.bronze { color: #cd7f32; }

.rank-avatar {
  font-size: 1.5rem;
}

.rank-info {
  flex: 1;
}

.rank-name {
  font-weight: 500;
  margin-bottom: 0.25rem;
}

.is-me {
  color: var(--primary);
  font-size: 0.75rem;
}

.rank-meta {
  display: flex;
  gap: 0.5rem;
  font-size: 0.75rem;
}

.level-badge {
  padding: 0.125rem 0.5rem;
  background: var(--bg-secondary);
  border-radius: 4px;
  color: var(--primary);
}

.streak {
  color: #f97316;
}

.rank-xp {
  text-align: right;
}

.xp-value {
  font-weight: 700;
  color: var(--warning);
}

.xp-label {
  font-size: 0.625rem;
  color: var(--text-muted);
}

.rank-change {
  width: 40px;
  text-align: center;
  font-size: 0.75rem;
}

.rank-change.up { color: var(--success); }
.rank-change.down { color: var(--danger); }

/* My Rank */
.my-rank {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.2), rgba(118, 75, 162, 0.2));
  border: 2px solid var(--primary);
  border-radius: var(--radius-lg);
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.my-rank-label {
  font-size: 0.75rem;
  color: var(--primary);
  margin-bottom: 1rem;
}

.my-rank-content {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.my-rank-number {
  font-size: 2rem;
  font-weight: 700;
  color: var(--primary);
}

.my-rank-avatar {
  font-size: 2rem;
}

.my-rank-name {
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.my-rank-meta {
  display: flex;
  gap: 0.75rem;
  font-size: 0.75rem;
}

/* Weekly Star */
.weekly-star {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 1.5rem;
  border: 1px solid rgba(255, 215, 0, 0.3);
}

.star-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.star-icon {
  font-size: 1.5rem;
}

.star-title {
  font-size: 1.125rem;
  font-weight: 600;
  background: linear-gradient(135deg, #ffd700, #ffa500);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.star-winners {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}

.star-winner {
  text-align: center;
  padding: 1rem;
  background: var(--bg-secondary);
  border-radius: var(--radius);
}

.winner-avatar {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.winner-name {
  font-size: 0.875rem;
  font-weight: 500;
  margin-bottom: 0.25rem;
}

.winner-reward {
  font-size: 0.625rem;
  color: var(--warning);
}

@media (max-width: 768px) {
  .champions {
    gap: 0.5rem;
  }
  
  .champion-card {
    padding: 1rem 0.5rem;
  }
  
  .champion-avatar {
    width: 48px;
    height: 48px;
    font-size: 1.5rem;
  }
  
  .first .champion-avatar {
    width: 60px;
    height: 60px;
    font-size: 2rem;
  }
  
  .champion-name {
    font-size: 0.75rem;
  }
  
  .star-winners {
    grid-template-columns: 1fr;
  }
}
</style>
