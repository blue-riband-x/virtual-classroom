<template>
  <div class="app-container">
    <router-view v-slot="{ Component }">
      <transition name="page" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
    
    <!-- ✨ XP弹窗 -->
    <transition name="xp-popup-anim">
      <div v-if="showXPPopup" class="xp-popup" role="alert">
        <span class="xp-icon">⭐</span>
        <span>+{{ popupXP }} XP</span>
      </div>
    </transition>
    
    <!-- 🎉 升级动画 -->
    <transition name="level-up-anim">
      <div v-if="showLevelUp" class="level-up-overlay" role="dialog" aria-label="升级提示">
        <div class="level-up-content">
          <!-- 装饰星星 -->
          <div class="level-stars">
            <span v-for="i in 12" :key="i" class="level-star" :style="getStarStyle(i)">✨</span>
          </div>
          
          <div class="level-up-badge">
            <span class="level-badge-icon">🌟</span>
          </div>
          
          <h1 class="level-up-title">LEVEL UP!</h1>
          
          <div class="level-up-number">
            <span class="level-prefix">Lv.</span>
            <span class="level-value">{{ newLevel }}</span>
          </div>
          
          <p class="level-up-message">🎊 恭喜达到新等级！</p>
          <p class="level-up-reward">🎁 解锁新成就资格，快去探索吧！</p>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, provide } from 'vue'
import { useUserStore } from './stores'

const userStore = useUserStore()

// XP弹窗
const showXPPopup = ref(false)
const popupXP = ref(0)

// 升级动画
const showLevelUp = ref(false)
const newLevel = ref(0)

// 星星位置样式
const getStarStyle = (i) => {
  const angle = (i / 12) * 360
  const radius = 150
  const x = Math.cos((angle * Math.PI) / 180) * radius
  const y = Math.sin((angle * Math.PI) / 180) * radius
  const delay = i * 0.1
  
  return {
    position: 'absolute',
    left: `calc(50% + ${x}px)`,
    top: `calc(50% + ${y}px)`,
    transform: 'translate(-50%, -50%)',
    fontSize: `${12 + Math.random() * 12}px`,
    animationDelay: `${delay}s`,
    opacity: 0.8
  }
}

// 提供全局方法
const showXP = (amount) => {
  popupXP.value = amount
  showXPPopup.value = true
  setTimeout(() => {
    showXPPopup.value = false
  }, 1500)
}

const triggerLevelUp = (level) => {
  newLevel.value = level
  showLevelUp.value = true
  setTimeout(() => {
    showLevelUp.value = false
  }, 2800)
}

provide('showXP', showXP)
provide('triggerLevelUp', triggerLevelUp)
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  position: relative;
}

/* 页面切换动画 */
.page-enter-active,
.page-leave-active {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.page-enter-from {
  opacity: 0;
  transform: translateX(30px);
}

.page-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}

/* XP弹窗动画 */
.xp-popup-anim-enter-active {
  animation: xpPopup 1.5s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}

.xp-popup-anim-leave-active {
  animation: xpFadeOut 0.3s ease forwards;
}

@keyframes xpFadeOut {
  to { opacity: 0; transform: translate(-50%, -100%) scale(0.8); }
}

/* XP弹窗样式 */
.xp-popup {
  position: fixed;
  top: 40%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: linear-gradient(135deg, #ffe058, #fa8c16, #ffd33d);
  color: #7c4a03;
  padding: 1rem 2.5rem;
  border-radius: var(--radius-xl);
  font-size: 1.75rem;
  font-weight: 800;
  z-index: 2000;
  box-shadow: 
    0 6px 0 rgba(218, 120, 0, 0.5),
    0 0 40px rgba(250, 140, 22, 0.5),
    inset 0 2px 4px rgba(255,255,255,0.5);
  border: 3px solid rgba(255,255,255,0.6);
}

.xp-icon {
  font-size: 1.5em;
  animation: xpStarSpin 1s ease infinite;
}

@keyframes xpStarSpin {
  0% { transform: rotate(0deg) scale(1); }
  50% { transform: rotate(180deg) scale(1.3); }
  100% { transform: rotate(360deg) scale(1); }
}

/* 升级动画 */
.level-up-anim-enter-active {
  animation: levelUpIn 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}

.level-up-anim-leave-active {
  animation: levelUpOut 0.5s ease forwards;
}

@keyframes levelUpIn {
  from {
    opacity: 0;
    clip-path: circle(0% at 50% 50%);
  }
  to {
    opacity: 1;
    clip-path: circle(100% at 50% 50%);
  }
}

@keyframes levelUpOut {
  to {
    opacity: 0;
    transform: scale(1.2);
  }
}

.level-up-overlay {
  position: fixed;
  inset: 0;
  background: linear-gradient(135deg, #0D2250 0%, #162D5A 50%, #1A3A6E 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 3000;
  overflow: hidden;
}

/* 蓝色科技背景光效 */
.level-up-overlay::before {
  content: '';
  position: absolute;
  inset: 0;
  background: 
    radial-gradient(ellipse at 30% 20%, rgba(74, 144, 217, 0.3) 0%, transparent 60%),
    radial-gradient(ellipse at 70% 80%, rgba(91, 141, 239, 0.2) 0%, transparent 50%),
    radial-gradient(ellipse at 50% 50%, rgba(124, 184, 228, 0.15) 0%, transparent 70%);
  animation: bgPulse 2s ease-in-out infinite alternate;
}

@keyframes bgPulse {
  from { opacity: 0.7; transform: scale(1); }
  to { opacity: 1; transform: scale(1.05); }
}

.level-stars {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.level-star {
  position: absolute;
  animation: starTwinkle 1.5s ease-in-out infinite;
  color: #ffd33d;
  text-shadow: 0 0 10px #ffd33d;
}

@keyframes starTwinkle {
  0%, 100% { opacity: 0.4; transform: translate(-50%, -50%) scale(0.8); }
  50% { opacity: 1; transform: translate(-50%, -50%) scale(1.2); }
}

.level-up-content {
  text-align: center;
  z-index: 1;
  animation: levelContentBounce 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) 0.2s backwards;
}

@keyframes levelContentBounce {
  from { opacity: 0; transform: scale(0.5); }
  to { opacity: 1; transform: scale(1); }
}

.level-up-badge {
  margin-bottom: 1rem;
  animation: badgeFloat 2s ease-in-out infinite;
}

@keyframes badgeFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.level-badge-icon {
  font-size: 5rem;
  display: block;
  filter: drop-shadow(0 0 20px rgba(255, 208, 88, 0.8));
}

.level-up-title {
  font-size: 4rem;
  background: linear-gradient(135deg, #ffd33d, #ff9f43, #ff6b6b, #ffd33d);
  background-size: 300% auto;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: rainbowShine 2s linear infinite;
  text-shadow: none;
  letter-spacing: 0.05em;
  margin-bottom: 1rem;
}

@keyframes rainbowShine {
  to { background-position: 300% center; }
}

.level-up-number {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 0.25rem;
  margin-bottom: 1.5rem;
}

.level-prefix {
  font-size: 2.5rem;
  color: rgba(255, 255, 255, 0.7);
  font-weight: 600;
}

.level-value {
  font-size: 6rem;
  font-weight: 800;
  color: white;
  text-shadow: 0 0 30px rgba(255, 208, 88, 0.8), 0 4px 0 rgba(0,0,0,0.2);
  animation: levelNumPop 0.8s cubic-bezier(0.34, 1.56, 0.64, 1) 0.4s backwards;
}

@keyframes levelNumPop {
  from { opacity: 0; transform: scale(0.3) rotate(-10deg); }
  60% { transform: scale(1.2) rotate(5deg); }
  to { opacity: 1; transform: scale(1) rotate(0); }
}

.level-up-message {
  font-size: 1.75rem;
  color: white;
  margin-bottom: 0.5rem;
  animation: msgSlide 0.5s ease 0.6s backwards;
}

.level-up-reward {
  font-size: 1.125rem;
  color: rgba(255, 255, 255, 0.7);
  animation: msgSlide 0.5s ease 0.8s backwards;
}

@keyframes msgSlide {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
