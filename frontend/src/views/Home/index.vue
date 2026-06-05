<template>
  <div class="home-page">
    <Navbar />

    <!-- 渐变背景包裹整个主内容 -->
    <div class="home-main">
      <!-- 3D人物 + 问候 -->
      <section class="hero-section">
        <div class="hero-avatar-wrap">
          <ThreeAvatar />
        </div>

        <div class="hero-greeting">
          <span class="greeting-text">{{ timeGreeting }}</span>
          <span class="greeting-name">{{ userStore.userInfo.nickname }}</span>
        </div>

        <div class="hero-level" @click.stop="showLevelInfo">
          <span class="level-text">LV.{{ userStore.userInfo.level }}</span>
        </div>
      </section>

      <!-- 顶部状态条 -->
      <section class="top-stats">
        <div class="top-stat-item">
          <span class="ts-icon">🔥</span>
          <div class="ts-info">
            <span class="ts-value">{{ userStore.userInfo.streak }} 天</span>
            <span class="ts-label">连续学习</span>
          </div>
        </div>
        <div class="top-stat-divider"></div>
        <div class="top-stat-item">
          <span class="ts-icon">⚡</span>
          <div class="ts-info">
            <span class="ts-value">{{ userStore.userInfo.xp }}</span>
            <span class="ts-label">经验值</span>
          </div>
        </div>
      </section>

      <!-- 功能入口 -->
      <section class="nav-icons">
        <div class="nav-icon-item" @click="$router.push('/plan')">
          <div class="ni-circle">
            <span class="ni-emoji">📖</span>
          </div>
          <span class="ni-label">开始学习</span>
        </div>
        <div class="nav-icon-item" @click="$router.push('/report')">
          <div class="ni-circle">
            <span class="ni-emoji">📊</span>
          </div>
          <span class="ni-label">学习报告</span>
        </div>
        <div class="nav-icon-item" @click="$router.push('/game')">
          <div class="ni-circle">
            <span class="ni-emoji">🎮</span>
          </div>
          <span class="ni-label">成就中心</span>
        </div>
        <div class="nav-icon-item" @click="$router.push('/leaderboard')">
          <div class="ni-circle">
            <span class="ni-emoji">🏆</span>
          </div>
          <span class="ni-label">排行榜</span>
        </div>
      </section>

      <!-- 收集进度 -->
      <section class="collect-bar" @click="$router.push('/game')">
        <div class="collect-left">
          <span class="collect-icon">🐾</span>
          <span class="collect-text">收集进度</span>
        </div>
        <div class="collect-right">
          <span class="collect-count">1/2</span>
          <span class="collect-arrow">›</span>
        </div>
      </section>

      <!-- 学习进度卡片 -->
      <section class="progress-card">
        <div class="pc-header">
          <div class="pc-title-row">
            <span class="pc-emoji">📚</span>
            <span class="pc-title">学习进度</span>
          </div>
          <span class="pc-arrow" @click="$router.push('/plan')">详情 ›</span>
        </div>

        <div class="pc-stats">
          <div class="pc-stat">
            <span class="pc-value">{{ userStore.userInfo.xp }}</span>
            <span class="pc-label">已掌握</span>
          </div>
          <div class="pc-divider"></div>
          <div class="pc-stat">
            <span class="pc-value">{{ userStore.userInfo.totalLearningHours }}</span>
            <span class="pc-label">已学习(h)</span>
          </div>
          <div class="pc-divider"></div>
          <div class="pc-stat">
            <span class="pc-value">LV.{{ userStore.userInfo.level }}</span>
            <span class="pc-label">当前等级</span>
          </div>
        </div>

        <XPProgress
          :current="userStore.userInfo.xp"
          :total="userStore.userInfo.xpToNextLevel"
          :level="userStore.userInfo.level"
          :showNext="false"
          class="pc-progress"
        />
      </section>

      <!-- 底部双按钮 -->
      <section class="bottom-actions">
        <button class="ba-primary" @click="$router.push('/plan')">
          <span class="ba-icon">📖</span>
          <div class="ba-text">
            <span class="ba-title">开始学习</span>
            <span class="ba-sub">新学内容</span>
          </div>
          <span class="ba-arrow">›</span>
        </button>

        <button class="ba-secondary" @click="$router.push('/plan')">
          <span class="ba-icon">🔄</span>
          <div class="ba-text">
            <span class="ba-title">继续学习</span>
            <span class="ba-sub">复习巩固</span>
          </div>
          <span class="ba-arrow">›</span>
        </button>
      </section>

      <!-- 最近记录 -->
      <section v-if="recentHistory.length" class="history-section">
        <div class="hs-header">
          <span class="hs-title">最近记录</span>
        </div>
        <div class="hs-list">
          <div
            v-for="item in recentHistory"
            :key="item.id"
            class="hs-item"
          >
            <span class="hs-emoji">{{ getSubjectIcon(item.topic) }}</span>
            <div class="hs-info">
              <span class="hs-topic">{{ item.topic }}</span>
              <span class="hs-meta">{{ item.date }} · {{ item.duration }}分钟</span>
            </div>
            <span class="hs-score">+{{ item.xp }}</span>
          </div>
        </div>
      </section>
    </div>

    <BottomNav />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import Navbar from '../../components/layout/Navbar.vue'
import BottomNav from '../../components/layout/BottomNav.vue'
import XPProgress from '../../components/common/XPProgress.vue'
import ThreeAvatar from '../../components/ThreeAvatar.vue'
import { useUserStore } from '../../stores'

const userStore = useUserStore()

const timeGreeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 6) return '夜深了'
  if (hour < 9) return '早上好'
  if (hour < 12) return '上午好'
  if (hour < 14) return '中午好'
  if (hour < 18) return '下午好'
  if (hour < 21) return '傍晚好'
  return '晚上好'
})

const showLevelInfo = () => {
  const xpNeeded = userStore.userInfo.xpToNextLevel - userStore.userInfo.xp
  alert(`距离下一级还需 ${xpNeeded} XP`)
}

const recentHistory = computed(() => userStore.learningHistory.slice(0, 3))

const getSubjectIcon = (topic) => {
  if (topic.includes('Python')) return '🐍'
  if (topic.includes('JavaScript')) return '💛'
  if (topic.includes('Vue')) return '💚'
  if (topic.includes('数据结构')) return '📊'
  if (topic.includes('算法')) return '🧮'
  return '📚'
}
</script>

<style scoped>
/* ============================================
   整体 - 浅蓝清新风格
   ============================================ */
.home-page {
  min-height: 100vh;
  padding-top: 64px;
  padding-bottom: 80px;
  background: linear-gradient(180deg, #E3F0FA 0%, #C5DFF5 30%, #D4E8F7 60%, #E8F1F9 100%);
}

.home-main {
  max-width: 480px;
  margin: 0 auto;
  padding: 0 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

/* ============================================
   Hero - 3D人物 + 问候
   ============================================ */
.hero-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 12px;
  gap: 6px;
}

.hero-avatar-wrap {
  width: 340px;
  height: 340px;
  border-radius: 0;
  overflow: visible;
  background: transparent;
  backdrop-filter: none;
  border: none;
  margin: 0 auto;
}

.hero-greeting {
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.greeting-text {
  font-size: 14px;
  color: #6B8AAD;
  font-weight: 500;
}

.greeting-name {
  font-size: 22px;
  font-weight: 700;
  color: #2C4A6E;
  letter-spacing: 0.5px;
}

.hero-level {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(6px);
  border: 1px solid rgba(74, 144, 217, 0.2);
  border-radius: 20px;
  padding: 4px 16px;
  cursor: pointer;
  transition: transform 0.2s;
}

.hero-level:hover {
  transform: scale(1.05);
}

.level-text {
  font-size: 13px;
  font-weight: 700;
  color: #4A90D9;
}

/* ============================================
   顶部状态条
   ============================================ */
.top-stats {
  display: flex;
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(8px);
  border-radius: 16px;
  padding: 14px 0;
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: 0 2px 12px rgba(74, 144, 217, 0.08);
}

.top-stat-item {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.ts-icon {
  font-size: 22px;
}

.ts-info {
  display: flex;
  flex-direction: column;
}

.ts-value {
  font-size: 16px;
  font-weight: 700;
  color: #2C4A6E;
}

.ts-label {
  font-size: 11px;
  color: #8BA4C0;
}

.top-stat-divider {
  width: 1px;
  background: rgba(74, 144, 217, 0.15);
  margin: 4px 0;
}

/* ============================================
   功能入口
   ============================================ */
.nav-icons {
  display: flex;
  justify-content: space-between;
  padding: 4px 0;
}

.nav-icon-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  transition: transform 0.2s;
}

.nav-icon-item:hover {
  transform: translateY(-3px);
}

.ni-circle {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 10px rgba(74, 144, 217, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.7);
}

.ni-emoji {
  font-size: 22px;
}

.ni-label {
  font-size: 11px;
  color: #5A7A9A;
  font-weight: 500;
}

/* ============================================
   收集进度条
   ============================================ */
.collect-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(8px);
  border-radius: 14px;
  padding: 14px 18px;
  cursor: pointer;
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: 0 2px 10px rgba(74, 144, 217, 0.06);
  transition: transform 0.2s;
}

.collect-bar:hover {
  transform: translateY(-2px);
}

.collect-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.collect-icon {
  font-size: 20px;
}

.collect-text {
  font-size: 14px;
  font-weight: 600;
  color: #2C4A6E;
}

.collect-right {
  display: flex;
  align-items: center;
  gap: 4px;
}

.collect-count {
  font-size: 14px;
  font-weight: 700;
  color: #4A90D9;
}

.collect-arrow {
  font-size: 18px;
  color: #A0B8D0;
}

/* ============================================
   学习进度卡片
   ============================================ */
.progress-card {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(8px);
  border-radius: 18px;
  padding: 18px 20px;
  border: 1px solid rgba(255, 255, 255, 0.7);
  box-shadow: 0 4px 16px rgba(74, 144, 217, 0.08);
}

.pc-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.pc-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pc-emoji {
  font-size: 18px;
}

.pc-title {
  font-size: 15px;
  font-weight: 700;
  color: #2C4A6E;
}

.pc-arrow {
  font-size: 13px;
  color: #4A90D9;
  font-weight: 500;
  cursor: pointer;
}

.pc-stats {
  display: flex;
  align-items: center;
  margin-bottom: 14px;
}

.pc-stat {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.pc-value {
  font-size: 22px;
  font-weight: 800;
  color: #2C4A6E;
}

.pc-label {
  font-size: 11px;
  color: #8BA4C0;
}

.pc-divider {
  width: 1px;
  height: 36px;
  background: rgba(74, 144, 217, 0.12);
}

.pc-progress {
  margin-top: 4px;
}

/* ============================================
   底部双按钮
   ============================================ */
.bottom-actions {
  display: flex;
  gap: 12px;
}

.ba-primary {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  background: linear-gradient(135deg, #4A90D9, #357ABD);
  color: white;
  border: none;
  border-radius: 18px;
  padding: 16px 18px;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(74, 144, 217, 0.3);
  transition: all 0.25s;
}

.ba-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(74, 144, 217, 0.4);
}

.ba-secondary {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(74, 144, 217, 0.2);
  border-radius: 18px;
  padding: 16px 18px;
  cursor: pointer;
  color: #4A90D9;
  transition: all 0.25s;
  box-shadow: 0 2px 10px rgba(74, 144, 217, 0.08);
  backdrop-filter: blur(8px);
}

.ba-secondary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(74, 144, 217, 0.15);
}

.ba-icon {
  font-size: 22px;
  flex-shrink: 0;
}

.ba-text {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.ba-title {
  font-size: 15px;
  font-weight: 700;
}

.ba-sub {
  font-size: 11px;
  opacity: 0.7;
}

.ba-arrow {
  font-size: 18px;
  flex-shrink: 0;
}

.ba-secondary .ba-arrow {
  color: #A0B8D0;
}

/* ============================================
   最近记录
   ============================================ */
.history-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.hs-header {
  padding: 0 4px;
}

.hs-title {
  font-size: 13px;
  font-weight: 600;
  color: #6B8AAD;
}

.hs-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.hs-item {
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(6px);
  border-radius: 14px;
  padding: 12px 16px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  transition: all 0.2s;
}

.hs-item:hover {
  background: rgba(255, 255, 255, 0.9);
  transform: translateX(3px);
}

.hs-emoji {
  font-size: 20px;
  flex-shrink: 0;
}

.hs-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.hs-topic {
  font-size: 13px;
  font-weight: 600;
  color: #2C4A6E;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.hs-meta {
  font-size: 11px;
  color: #8BA4C0;
}

.hs-score {
  font-size: 13px;
  font-weight: 700;
  color: #4A90D9;
  flex-shrink: 0;
}

/* ============================================
   Responsive
   ============================================ */
@media (min-width: 769px) {
  .home-main {
    max-width: 500px;
  }

  .hero-avatar-wrap {
    width: 300px;
    height: 300px;
  }

  .greeting-name {
    font-size: 24px;
  }
}
</style>
