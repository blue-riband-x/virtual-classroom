import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login/index.vue'),
    meta: { title: '登录 - AI虚拟课堂', guest: true }
  },
  {
    path: '/home',
    name: 'Home',
    component: () => import('../views/Home/index.vue'),
    meta: { title: 'AI虚拟课堂', requiresAuth: true }
  },
  {
    path: '/plan',
    name: 'Plan',
    component: () => import('../views/Plan/index.vue'),
    meta: { title: '学习规划', requiresAuth: true }
  },
  {
    path: '/classroom',
    name: 'Classroom',
    component: () => import('../views/Classroom/index.vue'),
    meta: { title: '虚拟课堂', requiresAuth: true }
  },
  {
    path: '/report',
    name: 'Report',
    component: () => import('../views/Report/index.vue'),
    meta: { title: '学习报告', requiresAuth: true }
  },
  {
    path: '/game',
    name: 'Game',
    component: () => import('../views/Game/index.vue'),
    meta: { title: '游戏中心', requiresAuth: true }
  },
  {
    path: '/leaderboard',
    name: 'Leaderboard',
    component: () => import('../views/Leaderboard/index.vue'),
    meta: { title: '排行榜', requiresAuth: true }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('../views/Profile/index.vue'),
    meta: { title: '个人中心', requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
  scrollBehavior() {
    return { top: 0, behavior: 'smooth' }
  }
})

router.beforeEach((to, from, next) => {
  document.title = to.meta.title || 'AI虚拟课堂'
  
  const token = localStorage.getItem('token')
  const requiresAuth = to.meta.requiresAuth
  const isGuest = to.meta.guest
  
  if (requiresAuth && !token) {
    // 未登录，重定向到登录页
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else if (isGuest && token) {
    // 已登录，访问登录页则跳转到首页
    next({ name: 'Home' })
  } else {
    next()
  }
})

export default router
