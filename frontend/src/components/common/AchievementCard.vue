<template>
  <div class="achievement-card" :class="{ locked: !achievement.unlocked, tier: achievement.tier }">
    <div class="achievement-icon-wrap">
      <div class="achievement-icon" :class="{ locked: !achievement.unlocked }">
        {{ achievement.unlocked ? achievement.icon : '🔒' }}
      </div>
      <div class="achievement-glow" v-if="achievement.unlocked"></div>
    </div>
    <div class="achievement-info">
      <h4 class="achievement-name">{{ achievement.name }}</h4>
      <p class="achievement-desc">{{ achievement.desc }}</p>
      <div class="achievement-tier">
        <span class="tier-badge" :class="achievement.tier">
          {{ tierText }}
        </span>
      </div>
    </div>
    <div class="achievement-progress" v-if="!achievement.unlocked">
      <div class="progress-text">{{ achievement.progress }}%</div>
      <div class="progress-track">
        <div class="progress-fill" :style="{ width: achievement.progress + '%' }"></div>
      </div>
    </div>
    <div class="achievement-unlocked" v-else>
      <span class="check-icon">✓</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  achievement: {
    type: Object,
    required: true
  }
})

const tierText = computed(() => {
  const map = {
    bronze: '🥉 铜牌',
    silver: '🥈 银牌',
    gold: '🥇 金牌'
  }
  return map[props.achievement.tier] || '🥉 铜牌'
})
</script>

<style scoped>
.achievement-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.25rem;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  border: 2px solid var(--border);
  box-shadow: var(--shadow-sm);
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  position: relative;
  overflow: hidden;
}

.achievement-card:not(.locked):hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}

.achievement-card.locked {
  opacity: 0.55;
  filter: grayscale(30%);
}

.achievement-card.locked:hover {
  opacity: 0.7;
}

.achievement-card.tier-bronze:not(.locked) {
  border-color: #ffa940;
}

.achievement-card.tier-silver:not(.locked) {
  border-color: #8c8c8c;
}

.achievement-card.tier-gold:not(.locked) {
  border-color: #ffd33d;
}

.achievement-icon-wrap {
  position: relative;
  flex-shrink: 0;
}

.achievement-icon {
  font-size: 2.5rem;
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f0fdf4, #dcfce7);
  border-radius: var(--radius);
  border: 2px solid var(--border);
  position: relative;
  z-index: 1;
}

.achievement-icon.locked {
  background: var(--bg-secondary);
}

.tier-bronze:not(.locked) .achievement-icon { border-color: #ffa940; }
.tier-silver:not(.locked) .achievement-icon { border-color: #8c8c8c; }
.tier-gold:not(.locked) .achievement-icon { border-color: #ffd33d; }

.achievement-glow {
  position: absolute;
  inset: -4px;
  border-radius: var(--radius);
  background: radial-gradient(circle, rgba(255, 208, 88, 0.3), transparent 70%);
  animation: glowPulse 2s ease-in-out infinite;
}

@keyframes glowPulse {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}

.achievement-info {
  flex: 1;
  min-width: 0;
}

.achievement-name {
  font-size: 0.9375rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 0.25rem;
}

.achievement-desc {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-bottom: 0.375rem;
}

.achievement-tier {
  display: flex;
}

.tier-badge {
  padding: 0.125rem 0.5rem;
  border-radius: var(--radius-full);
  font-size: 0.6875rem;
  font-weight: 700;
}

.tier-badge.bronze {
  background: linear-gradient(135deg, #ffe0b2, #ffa940);
  color: #8b4500;
  border: 1px solid #ffb74d;
}

.tier-badge.silver {
  background: linear-gradient(135deg, #e8e8e8, #bfbfbf);
  color: #525252;
  border: 1px solid #d9d9d9;
}

.tier-badge.gold {
  background: linear-gradient(135deg, #fff1b8, #ffe058);
  color: #8b6914;
  border: 1px solid #ffd33d;
  box-shadow: 0 0 6px rgba(255, 208, 88, 0.4);
}

.achievement-progress {
  width: 70px;
  flex-shrink: 0;
  text-align: right;
}

.progress-text {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--primary-dark);
  margin-bottom: 0.25rem;
}

.progress-track {
  height: 8px;
  background: var(--bg-secondary);
  border-radius: var(--radius-full);
  overflow: hidden;
  border: 1px solid var(--border);
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary-light), var(--primary));
  border-radius: var(--radius-full);
  transition: width 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.achievement-unlocked {
  flex-shrink: 0;
}

.check-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: linear-gradient(135deg, #7CB8E4, #4A90D9);
  color: white;
  border-radius: 50%;
  font-size: 0.875rem;
  font-weight: bold;
  box-shadow: 0 2px 6px rgba(74, 144, 217, 0.4);
}
</style>
