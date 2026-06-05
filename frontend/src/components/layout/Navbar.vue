<template>
  <header class="navbar">
    <div class="navbar-content">
      <!-- Logo -->
      <div class="navbar-left">
        <router-link to="/" class="logo">
          <div class="logo-icon-wrap">
            <span class="logo-icon">📘</span>
          </div>
          <span class="logo-text">AI虚拟课堂</span>
        </router-link>
      </div>
      
      <!-- 导航 -->
      <nav class="navbar-nav">
        <router-link to="/" class="nav-link" :class="{ active: $route.path === '/' }">
          <span class="nav-icon">🏠</span>
          <span class="nav-label">首页</span>
        </router-link>
        <router-link to="/plan" class="nav-link" :class="{ active: $route.path === '/plan' }">
          <span class="nav-icon">📖</span>
          <span class="nav-label">学习</span>
        </router-link>
        <router-link to="/game" class="nav-link" :class="{ active: $route.path === '/game' }">
          <span class="nav-icon">🏅</span>
          <span class="nav-label">成就</span>
        </router-link>
        <router-link to="/leaderboard" class="nav-link" :class="{ active: $route.path === '/leaderboard' }">
          <span class="nav-icon">👑</span>
          <span class="nav-label">排行</span>
        </router-link>
      </nav>
      
      <!-- 用户信息 -->
      <div class="navbar-right">
        <div class="user-info" @click="$router.push('/profile')">
          <div class="user-avatar-wrap">
            <span class="user-avatar">{{ userStore.userInfo.avatar }}</span>
          </div>
          <div class="user-stats">
            <div class="user-level-row">
              <span class="user-level">Lv.{{ userStore.userInfo.level }}</span>
              <span class="user-name">{{ userStore.userInfo.nickname }}</span>
            </div>
            <div class="user-xp-bar">
              <div class="user-xp-fill" :style="{ width: userStore.xpProgress + '%' }">
                <div class="xp-fill-shine"></div>
              </div>
            </div>
          </div>
          <div class="streak-badge" v-if="userStore.userInfo.streak > 0">
            <span class="streak-flame-icon">🔥</span>
            <span>{{ userStore.userInfo.streak }}</span>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { useUserStore } from '../../stores'

const userStore = useUserStore()
</script>

<style scoped>
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 64px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(74, 144, 217, 0.12);
  z-index: 100;
  box-shadow: 0 2px 16px rgba(74, 144, 217, 0.08);
}

.navbar-content {
  max-width: 1400px;
  margin: 0 auto;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 2rem;
}

/* Logo */
.navbar-left {
  display: flex;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  color: var(--text-primary);
  transition: transform 0.3s ease;
}

.logo:hover {
  transform: scale(1.05);
}

.logo-icon-wrap {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, var(--primary-light), var(--primary));
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  box-shadow: 0 2px 0 rgba(58, 123, 200, 0.4);
}

.logo-icon {
  font-size: 1.25rem;
}

.logo-text {
  font-size: 1.125rem;
  font-weight: 800;
  color: var(--text-primary);
  letter-spacing: 0.05em;
}

/* Nav */
.navbar-nav {
  display: flex;
  gap: 0.25rem;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 9999px;
  text-decoration: none;
  color: var(--text-secondary);
  font-weight: 500;
  font-size: 0.875rem;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  position: relative;
}

.nav-link::after {
  content: '';
  position: absolute;
  bottom: 4px;
  left: 50%;
  transform: translateX(-50%) scaleX(0);
  width: 20px;
  height: 3px;
  background: linear-gradient(90deg, var(--primary-light), var(--primary));
  border-radius: 2px;
  transition: transform 0.3s ease;
}

.nav-link:hover {
  color: var(--primary-dark);
  background: rgba(74, 144, 217, 0.08);
}

.nav-link:hover .nav-icon {
  transform: scale(1.2);
}

.nav-link.active {
  color: var(--primary-dark);
  background: rgba(74, 144, 217, 0.12);
  font-weight: 700;
}

.nav-link.active::after {
  transform: translateX(-50%) scaleX(1);
}

.nav-icon {
  font-size: 1.125rem;
  transition: transform 0.3s ease;
}

.nav-label {
  font-weight: 600;
}

/* User */
.user-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.375rem 0.875rem 0.375rem 0.375rem;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 9999px;
  cursor: pointer;
  border: 1.5px solid rgba(74, 144, 217, 0.15);
  box-shadow: 0 1px 4px rgba(74, 144, 217, 0.06);
  transition: all 0.3s ease;
}

.user-info:hover {
  border-color: rgba(74, 144, 217, 0.35);
  box-shadow: 0 2px 8px rgba(74, 144, 217, 0.12);
  transform: translateY(-1px);
}

.user-avatar-wrap {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #E3F0FA, #D0E4F8);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid rgba(74, 144, 217, 0.2);
  flex-shrink: 0;
}

.user-avatar {
  font-size: 1.25rem;
}

.user-stats {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  min-width: 80px;
}

.user-level-row {
  display: flex;
  align-items: baseline;
  gap: 0.375rem;
}

.user-level {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--primary-dark);
  background: rgba(74, 144, 217, 0.1);
  padding: 0.125rem 0.5rem;
  border-radius: 9999px;
  border: 1px solid rgba(74, 144, 217, 0.15);
}

.user-name {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 60px;
}

.user-xp-bar {
  width: 80px;
  height: 6px;
  background: rgba(74, 144, 217, 0.08);
  border-radius: 9999px;
  overflow: hidden;
  border: 1px solid rgba(74, 144, 217, 0.1);
}

.user-xp-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary-light), var(--primary));
  border-radius: 9999px;
  transition: width 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
  position: relative;
  overflow: hidden;
}

.xp-fill-shine {
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.5), transparent);
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  to { left: 100%; }
}

.streak-badge {
  display: flex;
  align-items: center;
  gap: 0.125rem;
  background: linear-gradient(135deg, #fff7e6, #ffe7ba);
  border-radius: 9999px;
  padding: 0.25rem 0.625rem;
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--accent);
  border: 1px solid rgba(250, 140, 22, 0.2);
}

.streak-flame-icon {
  font-size: 0.875rem;
}

@media (max-width: 768px) {
  .navbar-nav {
    display: none;
  }
  
  .logo-text,
  .user-name {
    display: none;
  }
  
  .user-xp-bar {
    width: 50px;
  }
  
  .navbar-content {
    padding: 0 1rem;
  }
}
</style>
