<template>
  <div class="report-page">
    <Navbar />
    
    <div class="report-container">
      <!-- 报告头部 -->
      <header class="report-header">
        <div class="report-celebration">
          <span class="celebration-icon">🎉</span>
          <span class="celebration-text">课堂完成！</span>
        </div>
        <h1>学习报告</h1>
        <p class="report-date">{{ report.date }}</p>
      </header>

      <!-- 概览卡片 -->
      <div class="overview-cards">
        <div class="overview-card">
          <div class="card-icon">📚</div>
          <div class="card-info">
            <span class="card-value">{{ report.duration }}</span>
            <span class="card-label">学习时长(分钟)</span>
          </div>
        </div>
        <div class="overview-card">
          <div class="card-icon">🏆</div>
          <div class="card-info">
            <span class="card-value">{{ report.score }}</span>
            <span class="card-label">综合得分</span>
          </div>
        </div>
        <div class="overview-card highlight">
          <div class="card-icon">⚡</div>
          <div class="card-info">
            <span class="card-value">+{{ report.xpEarned }}</span>
            <span class="card-label">获得XP</span>
          </div>
        </div>
        <div class="overview-card">
          <div class="card-icon">✅</div>
          <div class="card-info">
            <span class="card-value">{{ report.correctRate }}%</span>
            <span class="card-label">正确率</span>
          </div>
        </div>
      </div>

      <!-- 知识雷达图 -->
      <div class="section">
        <h2 class="section-title">📊 知识点掌握情况</h2>
        <div class="radar-chart-container">
          <div ref="radarChart" class="radar-chart"></div>
          <div class="radar-legend">
            <div class="legend-item" v-for="(label, i) in report.knowledgeRadar.labels" :key="i">
              <span class="legend-dot" :style="{ background: legendColors[i] }"></span>
              <span class="legend-text">{{ label }}</span>
              <span class="legend-value">{{ report.knowledgeRadar.data[i] }}%</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 答题详情 -->
      <div class="section">
        <h2 class="section-title">📝 答题统计</h2>
        <div class="stats-row">
          <div class="stat-item">
            <span class="stat-num">{{ report.questionsAnswered }}</span>
            <span class="stat-lbl">答题数</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-num correct">{{ report.correctRate }}%</span>
            <span class="stat-lbl">正确率</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-num">{{ report.questionsCount - Math.round(report.questionsCount * report.correctRate / 100) }}</span>
            <span class="stat-lbl">错误数</span>
          </div>
        </div>
        <div class="accuracy-bar">
          <div class="accuracy-fill" :style="{ width: report.correctRate + '%' }"></div>
        </div>
      </div>

      <!-- 优劣势分析 -->
      <div class="section analysis-section">
        <h2 class="section-title">🔍 学习分析</h2>
        <div class="analysis-grid">
          <div class="analysis-card strengths">
            <div class="analysis-header">
              <span class="analysis-icon">💪</span>
              <span class="analysis-title">优势领域</span>
            </div>
            <ul class="analysis-list">
              <li v-for="(s, i) in report.strengths" :key="i">{{ s }}</li>
            </ul>
          </div>
          <div class="analysis-card weaknesses">
            <div class="analysis-header">
              <span class="analysis-icon">📈</span>
              <span class="analysis-title">待提升</span>
            </div>
            <ul class="analysis-list">
              <li v-for="(w, i) in report.weaknesses" :key="i">{{ w }}</li>
            </ul>
          </div>
        </div>
      </div>

      <!-- AI点评 -->
      <div class="section ai-comment">
        <div class="ai-avatar">🤖</div>
        <div class="ai-content">
          <span class="ai-label">AI助教点评</span>
          <p class="ai-text">{{ report.aiComments }}</p>
        </div>
      </div>

      <!-- 学习建议 -->
      <div class="section suggestions">
        <h2 class="section-title">💡 学习建议</h2>
        <div class="suggestion-list">
          <div v-for="(s, i) in report.suggestions" :key="i" class="suggestion-item">
            <span class="suggestion-num">{{ i + 1 }}</span>
            <span class="suggestion-text">{{ s }}</span>
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="actions">
        <button class="btn btn-secondary" @click="downloadPDF">
          <span>📄</span> 下载PDF报告
        </button>
        <button class="btn btn-primary btn-lg" @click="continueLearning">
          <span>🚀</span> 继续学习
        </button>
      </div>
    </div>

    <BottomNav />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Navbar from '../../components/layout/Navbar.vue'
import BottomNav from '../../components/layout/BottomNav.vue'
import * as echarts from 'echarts'

const router = useRouter()

// 报告数据（后续可接入后端API生成）
const report = ref({
  date: new Date().toISOString().split('T')[0],
  duration: 45,
  score: 88,
  xpEarned: 68,
  knowledgeRadar: {
    labels: ['变量类型', '条件判断', '循环结构', '函数调用', '列表操作'],
    data: [95, 82, 75, 88, 65]
  },
  questionsAnswered: 12,
  correctRate: 83,
  strengths: ['对变量类型的理解比较扎实', '条件语句的逻辑清晰'],
  weaknesses: ['循环嵌套的运用还需加强', '列表操作不够熟练'],
  suggestions: ['建议加强循环结构的练习', '可以尝试做一些算法题目提升能力'],
  aiComments: '今天的课堂表现很棒！继续保持！'
})
const radarChart = ref(null)

const legendColors = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6']

onMounted(() => {
  initRadarChart()
})

const initRadarChart = () => {
  if (!radarChart.value) return
  
  const chart = echarts.init(radarChart.value)
  
  const option = {
    radar: {
      indicator: report.value.knowledgeRadar.labels.map((name, i) => ({
        name,
        max: 100,
        color: legendColors[i]
      })),
      shape: 'polygon',
      splitNumber: 4,
      axisName: {
        color: '#94a3b8',
        fontSize: 12
      },
      splitLine: {
        lineStyle: {
          color: 'rgba(255, 255, 255, 0.1)'
        }
      },
      splitArea: {
        show: true,
        areaStyle: {
          color: ['rgba(102, 126, 234, 0.05)', 'rgba(102, 126, 234, 0.1)', 'rgba(102, 126, 234, 0.15)', 'rgba(102, 126, 234, 0.2)']
        }
      },
      axisLine: {
        lineStyle: {
          color: 'rgba(255, 255, 255, 0.1)'
        }
      }
    },
    series: [{
      type: 'radar',
      data: [{
        value: report.value.knowledgeRadar.data,
        name: '掌握度',
        areaStyle: {
          color: new echarts.graphic.RadialGradient(0.5, 0.5, 1, [
            { offset: 0, color: 'rgba(102, 126, 234, 0.8)' },
            { offset: 1, color: 'rgba(118, 75, 162, 0.3)' }
          ])
        },
        lineStyle: {
          color: '#667eea',
          width: 2
        },
        itemStyle: {
          color: '#667eea'
        }
      }]
    }]
  }
  
  chart.setOption(option)
  
  window.addEventListener('resize', () => {
    chart.resize()
  })
}

const downloadPDF = () => {
  alert('📄 PDF报告正在生成中，稍后可在"我的文件"中查看下载。')
}

const continueLearning = () => {
  router.push('/plan')
}
</script>

<style scoped>
.report-page {
  min-height: 100vh;
  padding-top: 64px;
  padding-bottom: 80px;
  background: linear-gradient(180deg, var(--bg-primary) 0%, #1a1a2e 100%);
}

.report-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 1.5rem;
}

/* Header */
.report-header {
  text-align: center;
  padding: 2rem 0;
}

.report-celebration {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1.5rem;
  background: linear-gradient(135deg, rgba(255, 215, 0, 0.2), rgba(255, 107, 107, 0.2));
  border: 1px solid rgba(255, 215, 0, 0.3);
  border-radius: 9999px;
  margin-bottom: 1rem;
  animation: celebrate 0.5s ease;
}

@keyframes celebrate {
  0% { transform: scale(0); }
  50% { transform: scale(1.1); }
  100% { transform: scale(1); }
}

.celebration-icon {
  font-size: 1.5rem;
  animation: bounce 1s infinite;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-5px); }
}

.celebration-text {
  font-weight: 600;
  background: linear-gradient(135deg, #ffd700, #ff6b6b);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.report-header h1 {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.report-date {
  color: var(--text-muted);
}

/* Overview Cards */
.overview-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  margin-bottom: 2rem;
}

.overview-card {
  background: var(--bg-card);
  border-radius: var(--radius);
  padding: 1.25rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  border: 1px solid var(--border);
}

.overview-card.highlight {
  background: linear-gradient(135deg, rgba(255, 215, 0, 0.15), rgba(255, 165, 0, 0.15));
  border-color: rgba(255, 215, 0, 0.3);
}

.card-icon {
  font-size: 1.5rem;
}

.card-info {
  display: flex;
  flex-direction: column;
}

.card-value {
  font-size: 1.25rem;
  font-weight: 700;
}

.overview-card.highlight .card-value {
  background: linear-gradient(135deg, #ffd700, #ffa500);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.card-label {
  font-size: 0.625rem;
  color: var(--text-muted);
}

/* Section */
.section {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  border: 1px solid var(--border);
}

.section-title {
  font-size: 1.125rem;
  margin-bottom: 1.25rem;
}

/* Radar Chart */
.radar-chart-container {
  display: grid;
  grid-template-columns: 1fr 200px;
  gap: 1.5rem;
  align-items: center;
}

.radar-chart {
  height: 280px;
}

.radar-legend {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.legend-text {
  flex: 1;
  font-size: 0.875rem;
}

.legend-value {
  font-weight: 600;
  font-size: 0.875rem;
}

/* Stats Row */
.stats-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2rem;
  padding: 1rem 0;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-num {
  font-size: 2rem;
  font-weight: 700;
}

.stat-num.correct {
  color: var(--success);
}

.stat-lbl {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.stat-divider {
  width: 1px;
  height: 40px;
  background: var(--border);
}

.accuracy-bar {
  height: 12px;
  background: var(--bg-secondary);
  border-radius: 6px;
  overflow: hidden;
  margin-top: 1rem;
}

.accuracy-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--success), #34d399);
  border-radius: 6px;
  transition: width 1s ease;
}

/* Analysis */
.analysis-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.analysis-card {
  padding: 1rem;
  border-radius: var(--radius);
}

.analysis-card.strengths {
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.analysis-card.weaknesses {
  background: rgba(245, 158, 11, 0.1);
  border: 1px solid rgba(245, 158, 11, 0.2);
}

.analysis-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.analysis-icon {
  font-size: 1.25rem;
}

.analysis-title {
  font-weight: 600;
  font-size: 0.875rem;
}

.analysis-list {
  list-style: none;
  padding: 0;
}

.analysis-list li {
  font-size: 0.875rem;
  color: var(--text-secondary);
  padding: 0.375rem 0;
  padding-left: 1rem;
  position: relative;
}

.analysis-list li::before {
  content: '•';
  position: absolute;
  left: 0;
  color: var(--text-muted);
}

/* AI Comment */
.ai-comment {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
  border-color: var(--primary);
}

.ai-avatar {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-secondary);
  border-radius: 50%;
  font-size: 1.5rem;
  flex-shrink: 0;
}

.ai-content {
  flex: 1;
}

.ai-label {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  background: var(--primary);
  border-radius: 9999px;
  font-size: 0.75rem;
  margin-bottom: 0.75rem;
}

.ai-text {
  line-height: 1.6;
  color: var(--text-secondary);
}

/* Suggestions */
.suggestion-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.suggestion-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: var(--bg-secondary);
  border-radius: var(--radius);
}

.suggestion-num {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--primary);
  border-radius: 50%;
  font-size: 0.75rem;
  font-weight: 600;
}

.suggestion-text {
  flex: 1;
  font-size: 0.9375rem;
}

/* Actions */
.actions {
  display: flex;
  gap: 1rem;
  padding-top: 1rem;
}

.actions .btn {
  flex: 1;
}

@media (max-width: 768px) {
  .overview-cards {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .radar-chart-container {
    grid-template-columns: 1fr;
  }
  
  .analysis-grid {
    grid-template-columns: 1fr;
  }
  
  .actions {
    flex-direction: column;
  }
}
</style>
