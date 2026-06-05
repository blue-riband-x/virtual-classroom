<template>
  <div class="xp-progress">
    <div class="xp-info">
      <span class="xp-label">⭐ {{ current }}</span>
      <span class="xp-total">/ {{ total }}</span>
    </div>
    <div class="progress-track">
      <div class="progress-fill" :style="{ width: percentage + '%' }">
        <div class="fill-shine"></div>
      </div>
      <div class="progress-star" v-if="percentage > 5" :style="{ left: Math.min(percentage, 98) + '%' }">
        ⭐
      </div>
    </div>
    <div class="level-info" v-if="showNext">
      <div class="level-badge">
        <span>Lv.{{ level }}</span>
      </div>
      <span class="next-hint">距 Lv.{{ level + 1 }} 还差 {{ total - current }} XP</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  current: {
    type: Number,
    default: 0
  },
  total: {
    type: Number,
    default: 100
  },
  level: {
    type: Number,
    default: 1
  },
  showNext: {
    type: Boolean,
    default: true
  }
})

const percentage = computed(() => {
  return Math.min((props.current / props.total) * 100, 100)
})
</script>

<style scoped>
.xp-progress {
  width: 100%;
}

.xp-info {
  display: flex;
  align-items: baseline;
  gap: 0.25rem;
  margin-bottom: 0.375rem;
}

.xp-label {
  font-size: 0.875rem;
  font-weight: 700;
  background: linear-gradient(135deg, #ffd33d, #fa8c16);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.xp-total {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.progress-track {
  position: relative;
  height: 10px;
  background: linear-gradient(180deg, #e8f5e9, #c8e6c9);
  border-radius: var(--radius-full);
  overflow: visible;
  border: 1px solid #a5d6a7;
  box-shadow: inset 0 1px 3px rgba(0,0,0,0.1);
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #ffe058, #ffd33d, #fa8c16);
  border-radius: var(--radius-full);
  transition: width 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
  position: relative;
  overflow: hidden;
  min-width: 4px;
}

.fill-shine {
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.5), transparent);
  animation: fillShimmer 2s linear infinite;
}

@keyframes fillShimmer {
  to { left: 100%; }
}

.progress-star {
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
  font-size: 0.875rem;
  filter: drop-shadow(0 0 4px rgba(255, 208, 88, 0.8));
  animation: starPulse 1s ease-in-out infinite;
  z-index: 1;
  pointer-events: none;
}

@keyframes starPulse {
  0%, 100% { transform: translate(-50%, -50%) scale(1); }
  50% { transform: translate(-50%, -50%) scale(1.3); }
}

.level-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 0.375rem;
}

.level-badge {
  background: linear-gradient(135deg, #D6E8FF, #A8C8F0);
  color: var(--primary-dark);
  padding: 0.125rem 0.5rem;
  border-radius: var(--radius-full);
  font-size: 0.625rem;
  font-weight: 700;
}

.next-hint {
  font-size: 0.6875rem;
  color: var(--text-muted);
}
</style>
