<template>
  <div class="dashboard">
    <h2>📊 실시간 모니터링</h2>
    
    <div class="controls">
      <label>
        라인 선택:
        <select v-model="selectedLine" @change="loadData">
          <option value="LINE_01">LINE 01</option>
          <option value="LINE_02">LINE 02</option>
          <option value="LINE_03">LINE 03</option>
        </select>
      </label>
      <button @click="loadData" class="refresh-btn">🔄 새로고침</button>
    </div>

    <div class="stats-grid">
      <div class="stat-card" :class="{'danger': realtimeData.predicted_failure}">
        <div class="stat-icon">🚨</div>
        <div class="stat-content">
          <div class="stat-value">{{ (realtimeData.failure_probability * 100).toFixed(1) }}%</div>
          <div class="stat-label">고장 확률</div>
          <div class="stat-status" :class="getRiskClass()">{{ getRiskLevel() }}</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">🌡️</div>
        <div class="stat-content">
          <div class="stat-value">{{ realtimeData.temperature?.toFixed(1) || 0 }}°C</div>
          <div class="stat-label">온도</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">📳</div>
        <div class="stat-content">
          <div class="stat-value">{{ realtimeData.vibration?.toFixed(2) || 0 }}</div>
          <div class="stat-label">진동 (mm/s)</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">⚡</div>
        <div class="stat-content">
          <div class="stat-value">{{ realtimeData.current?.toFixed(1) || 0 }}A</div>
          <div class="stat-label">전류</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">📦</div>
        <div class="stat-content">
          <div class="stat-value">{{ realtimeData.production_count || 0 }}</div>
          <div class="stat-label">생산량 (개/h)</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">❌</div>
        <div class="stat-content">
          <div class="stat-value">{{ realtimeData.defect_count || 0 }}</div>
          <div class="stat-label">불량 수</div>
        </div>
      </div>
    </div>

    <div class="chart-container">
      <h3>📈 시계열 추이 (최근 24시간)</h3>
      <canvas ref="chartCanvas"></canvas>
    </div>

    <div class="stats-summary">
      <h3>📋 전체 통계</h3>
      <div class="summary-grid">
        <div class="summary-item">
          <strong>총 데이터:</strong> {{ stats.total_records }} 건
        </div>
        <div class="summary-item">
          <strong>고장 발생:</strong> {{ stats.total_failures }} 건
        </div>
        <div class="summary-item">
          <strong>고장률:</strong> {{ stats.failure_rate }}%
        </div>
        <div class="summary-item">
          <strong>최근 24시간:</strong> {{ stats.recent_24h }} 건
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import axios from '@/api'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

export default {
  name: 'Dashboard',
  setup() {
    const selectedLine = ref('LINE_01')
    const realtimeData = ref({})
    const stats = ref({
      total_records: 0,
      total_failures: 0,
      failure_rate: 0,
      recent_24h: 0
    })
    const chartCanvas = ref(null)
    let chart = null
    let interval = null

    const loadData = async () => {
      try {
        // 실시간 데이터
        const realtimeRes = await axios.get(`/api/monitor/realtime?line_id=${selectedLine.value}`)
        realtimeData.value = realtimeRes.data

        // 통계
        const statsRes = await axios.get('/api/data/stats')
        stats.value = statsRes.data

        // 차트 데이터
        const chartRes = await axios.get(`/api/monitor/chart?line_id=${selectedLine.value}&hours=24`)
        updateChart(chartRes.data)
      } catch (error) {
        console.error('데이터 로드 실패:', error)
      }
    }

    const updateChart = (data) => {
      if (!chartCanvas.value) return

      if (chart) {
        chart.destroy()
      }

      const ctx = chartCanvas.value.getContext('2d')
      chart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: data.timestamps.map(t => new Date(t).toLocaleTimeString('ko-KR', {hour: '2-digit', minute: '2-digit'})),
          datasets: [
            {
              label: '온도 (°C)',
              data: data.temperature,
              borderColor: 'rgb(255, 99, 132)',
              backgroundColor: 'rgba(255, 99, 132, 0.1)',
              yAxisID: 'y'
            },
            {
              label: '진동 (mm/s)',
              data: data.vibration.map(v => v * 100),
              borderColor: 'rgb(54, 162, 235)',
              backgroundColor: 'rgba(54, 162, 235, 0.1)',
              yAxisID: 'y'
            },
            {
              label: '고장 확률 (%)',
              data: data.failure_probability.map(p => p * 100),
              borderColor: 'rgb(255, 206, 86)',
              backgroundColor: 'rgba(255, 206, 86, 0.1)',
              yAxisID: 'y1'
            }
          ]
        },
        options: {
          responsive: true,
          interaction: {
            mode: 'index',
            intersect: false
          },
          scales: {
            y: {
              type: 'linear',
              display: true,
              position: 'left'
            },
            y1: {
              type: 'linear',
              display: true,
              position: 'right',
              grid: {
                drawOnChartArea: false
              }
            }
          }
        }
      })
    }

    const getRiskLevel = () => {
      const prob = realtimeData.value.failure_probability || 0
      if (prob < 0.3) return '정상'
      if (prob < 0.6) return '주의'
      return '위험'
    }

    const getRiskClass = () => {
      const prob = realtimeData.value.failure_probability || 0
      if (prob < 0.3) return 'safe'
      if (prob < 0.6) return 'warning'
      return 'danger'
    }

    onMounted(() => {
      loadData()
      interval = setInterval(loadData, 10000) // 10초마다 갱신
    })

    onUnmounted(() => {
      if (interval) clearInterval(interval)
      if (chart) chart.destroy()
    })

    return {
      selectedLine,
      realtimeData,
      stats,
      chartCanvas,
      loadData,
      getRiskLevel,
      getRiskClass
    }
  }
}
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

h2 {
  font-size: 2em;
  color: #333;
  margin-bottom: 20px;
}

.controls {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
  align-items: center;
}

.controls label {
  font-weight: 600;
}

.controls select {
  padding: 8px 15px;
  border: 2px solid #667eea;
  border-radius: 8px;
  font-size: 1em;
  margin-left: 10px;
}

.refresh-btn {
  padding: 10px 20px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1em;
  font-weight: 600;
}

.refresh-btn:hover {
  background: #5568d3;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
  border-radius: 12px;
  color: white;
  display: flex;
  align-items: center;
  gap: 15px;
  box-shadow: 0 5px 15px rgba(0,0,0,0.1);
}

.stat-card.danger {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.02); }
}

.stat-icon {
  font-size: 2.5em;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 2em;
  font-weight: bold;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 0.9em;
  opacity: 0.9;
}

.stat-status {
  margin-top: 5px;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 0.85em;
  font-weight: 600;
  display: inline-block;
}

.stat-status.safe {
  background: #4caf50;
}

.stat-status.warning {
  background: #ff9800;
}

.stat-status.danger {
  background: #f44336;
}

.chart-container {
  background: #f5f5f5;
  padding: 20px;
  border-radius: 12px;
  margin-bottom: 30px;
}

.chart-container h3 {
  margin-bottom: 15px;
  color: #333;
}

.stats-summary {
  background: #f5f5f5;
  padding: 20px;
  border-radius: 12px;
}

.stats-summary h3 {
  margin-bottom: 15px;
  color: #333;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
}

.summary-item {
  background: white;
  padding: 15px;
  border-radius: 8px;
  font-size: 1.1em;
}

.summary-item strong {
  color: #667eea;
}
</style>