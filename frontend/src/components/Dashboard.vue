<template>
  <div class="dashboard">
    <!-- 상단 컨트롤 -->
    <div class="controls">
      <label class="control-label">
        라인 선택:
        <select v-model="selectedLine" @change="loadData" class="control-select">
          <option value="LINE_01">LINE 01</option>
          <option value="LINE_02">LINE 02</option>
          <option value="LINE_03">LINE 03</option>
        </select>
      </label>
      <button @click="toggleRealtime" :class="['realtime-btn', { active: isRealtime }]">
        {{ isRealtime ? '실시간' : '새로고침' }}
      </button>
    </div>

    <!-- 상태 카드 그리드 -->
    <div class="stats-grid">
      <div class="stat-card" :class="getCardClass()">
        <div class="stat-label">고장 확률</div>
        <div class="stat-value">{{ getDisplayProbability() }}%</div>
        <div class="stat-status">{{ getRiskLevel() }}</div>
      </div>

      <div class="stat-card">
        <div class="stat-label">온도</div>
        <div class="stat-value">{{ formatValue(realtimeData.temperature) }}°C</div>
      </div>

      <div class="stat-card">
        <div class="stat-label">진동 (mm/s)</div>
        <div class="stat-value">{{ formatValue(realtimeData.vibration) }}</div>
      </div>

      <div class="stat-card">
        <div class="stat-label">전류</div>
        <div class="stat-value">{{ formatValue(realtimeData.current) }}A</div>
      </div>

      <div class="stat-card">
        <div class="stat-label">생산량 (개/h)</div>
        <div class="stat-value">{{ realtimeData.production_count || 0 }}</div>
      </div>

      <div class="stat-card">
        <div class="stat-label">불량 수</div>
        <div class="stat-value">{{ realtimeData.defect_count || 0 }}</div>
      </div>
    </div>

    <!-- 시계열 차트 -->
    <div class="chart-section">
      <div class="chart-header">
        <h3>시계열 추이</h3>
        <span class="realtime-indicator" v-if="isRealtime">● LIVE</span>
      </div>
      <div class="chart-container">
        <canvas ref="chartCanvas"></canvas>
      </div>
    </div>

    <!-- 하단 통계 -->
    <div class="stats-summary">
      <div class="summary-card">
        <div class="summary-label">총 데이터:</div>
        <div class="summary-value">{{ stats.total_records }} 건</div>
      </div>
      <div class="summary-card">
        <div class="summary-label">고장 발생:</div>
        <div class="summary-value">{{ stats.total_failures }} 건</div>
      </div>
      <div class="summary-card">
        <div class="summary-label">고장률:</div>
        <div class="summary-value">{{ stats.failure_rate }}%</div>
      </div>
      <div class="summary-card">
        <div class="summary-label">최근 24시간:</div>
        <div class="summary-value">{{ stats.recent_24h }} 건</div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
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
    const isRealtime = ref(true)
    let chart = null
    let interval = null
    let chartData = {
      timestamps: [],
      temperature: [],
      vibration: [],
      probability: []
    }
    const maxDataPoints = 50

    const loadData = async () => {
      try {
        const realtimeRes = await axios.get(`/api/monitor/realtime?line_id=${selectedLine.value}`)
        
        // 실시간 랜덤 변동 추가 (±2%)
        const variation = () => 1 + (Math.random() - 0.5) * 0.04
        realtimeData.value = {
          ...realtimeRes.data,
          temperature: (realtimeRes.data.temperature || 240) * variation(),
          vibration: (realtimeRes.data.vibration || 1.1) * variation(),
          current: (realtimeRes.data.current || 31) * variation(),
          failure_probability: (realtimeRes.data.failure_probability || 0.15) * variation()
        }

        const statsRes = await axios.get('/api/data/stats')
        stats.value = statsRes.data

        if (isRealtime.value && chart) {
          addRealtimeData(realtimeData.value)
        }
      } catch (error) {
        console.error('데이터 로드 실패:', error)
      }
    }

    const toggleRealtime = () => {
      isRealtime.value = !isRealtime.value
      if (!isRealtime.value) {
        loadData()
      }
    }

    const addRealtimeData = (data) => {
      const now = new Date()
      const timeLabel = `${now.getHours().toString().padStart(2,'0')}:${now.getMinutes().toString().padStart(2,'0')}:${now.getSeconds().toString().padStart(2,'0')}`
      
      chartData.timestamps.push(timeLabel)
      chartData.temperature.push(data.temperature || 240)
      chartData.vibration.push(data.vibration || 1.1)
      chartData.probability.push((data.failure_probability || 0.15) * 100)

      if (chartData.timestamps.length > maxDataPoints) {
        chartData.timestamps.shift()
        chartData.temperature.shift()
        chartData.vibration.shift()
        chartData.probability.shift()
      }

      updateChart()
    }

    const updateChart = () => {
      if (!chart) return

      chart.data.labels = chartData.timestamps
      chart.data.datasets[0].data = chartData.temperature
      chart.data.datasets[1].data = chartData.vibration
      chart.data.datasets[2].data = chartData.probability
      
      chart.update('none')
    }

    const initChart = () => {
      if (!chartCanvas.value) return

      const ctx = chartCanvas.value.getContext('2d')
      
      chart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: chartData.timestamps,
          datasets: [
            {
              label: '온도 (°C)',
              data: chartData.temperature,
              borderColor: '#ff6384',
              backgroundColor: 'rgba(255, 99, 132, 0.1)',
              yAxisID: 'y-temp',
              tension: 0.4,
              borderWidth: 2,
              pointRadius: 0
            },
            {
              label: '진동 (mm/s)',
              data: chartData.vibration,
              borderColor: '#36a2eb',
              backgroundColor: 'rgba(54, 162, 235, 0.1)',
              yAxisID: 'y-vib',
              tension: 0.4,
              borderWidth: 2,
              pointRadius: 0
            },
            {
              label: '고장 확률 (%)',
              data: chartData.probability,
              borderColor: '#ffcd56',
              backgroundColor: 'rgba(255, 205, 86, 0.1)',
              yAxisID: 'y-prob',
              tension: 0.4,
              borderWidth: 2,
              pointRadius: 0
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: {
            duration: 0
          },
          interaction: {
            mode: 'index',
            intersect: false
          },
          plugins: {
            legend: {
              position: 'top',
              labels: { 
                color: '#e0e0e0', 
                font: { size: 16, family: 'Noto Sans KR', weight: '500' },
                padding: 15
              }
            },
            tooltip: {
              backgroundColor: 'rgba(15, 40, 73, 0.95)',
              titleColor: '#00d4ff',
              bodyColor: '#e0e0e0',
              borderColor: '#00d4ff',
              borderWidth: 1,
              padding: 12,
              titleFont: { size: 14, family: 'Noto Sans KR', weight: '700' },
              bodyFont: { size: 13, family: 'Noto Sans KR' }
            }
          },
          scales: {
            x: {
              ticks: { 
                color: '#a0a0a0',
                font: { size: 11, family: 'Noto Sans KR' },
                maxRotation: 45,
                minRotation: 45
              },
              grid: { color: 'rgba(255,255,255,0.05)' }
            },
            'y-temp': {
              type: 'linear',
              position: 'left',
              ticks: { 
                color: '#ff6384',
                font: { size: 12, family: 'Noto Sans KR', weight: '500' }
              },
              grid: { color: 'rgba(255, 99, 132, 0.1)' },
              title: { 
                display: true, 
                text: '온도 (°C)', 
                color: '#ff6384',
                font: { size: 14, family: 'Noto Sans KR', weight: '700' }
              }
            },
            'y-vib': {
              type: 'linear',
              position: 'right',
              ticks: { 
                color: '#36a2eb',
                font: { size: 12, family: 'Noto Sans KR', weight: '500' }
              },
              grid: { display: false },
              title: { 
                display: true, 
                text: '진동 (mm/s)', 
                color: '#36a2eb',
                font: { size: 14, family: 'Noto Sans KR', weight: '700' }
              }
            },
            'y-prob': {
              type: 'linear',
              position: 'right',
              ticks: { 
                color: '#ffcd56',
                font: { size: 12, family: 'Noto Sans KR', weight: '500' }
              },
              grid: { display: false },
              title: { 
                display: true, 
                text: '고장 확률 (%)', 
                color: '#ffcd56',
                font: { size: 14, family: 'Noto Sans KR', weight: '700' }
              }
            }
          }
        }
      })
    }

    const formatValue = (value) => {
      return value ? Number(value).toFixed(1) : '0.0'
    }

    const getRiskLevel = () => {
      const prob = getActualProbability()
      if (prob < 0.3) return '정상'
      if (prob < 0.6) return '주의'
      return '위험'
    }

    const getCardClass = () => {
      const prob = getActualProbability()
      if (prob >= 0.6) return 'danger'
      if (prob >= 0.3) return 'warning'
      return 'safe'
    }

    const getActualProbability = () => {
      if (realtimeData.value.failure_probability > 0) {
        return realtimeData.value.failure_probability
      }
      return stats.value.failure_rate / 100 || 0
    }

    const getDisplayProbability = () => {
      return (getActualProbability() * 100).toFixed(1)
    }

    onMounted(() => {
      initChart()
      loadData()
      interval = setInterval(loadData, 2000) // 2초마다 실시간 업데이트
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
      isRealtime,
      loadData,
      toggleRealtime,
      formatValue,
      getRiskLevel,
      getCardClass,
      getDisplayProbability
    }
  }
}
</script>

<style scoped>
.dashboard {
  height: calc(100vh - 150px);
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 10px;
}

/* 컨트롤 */
.controls {
  display: flex;
  gap: 20px;
  align-items: center;
}

.control-label {
  font-size: 18px;
  color: #e0e0e0;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 10px;
}

.control-select {
  padding: 10px 20px;
  background: #0f2849;
  color: #00d4ff;
  border: 2px solid #00d4ff;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  font-family: 'Noto Sans KR', sans-serif;
}

.realtime-btn {
  padding: 10px 25px;
  background: #0f2849;
  color: #00d4ff;
  border: 2px solid #00d4ff;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  font-family: 'Noto Sans KR', sans-serif;
}

.realtime-btn.active {
  background: #00d4ff;
  color: #0a1628;
}

/* 상태 카드 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 15px;
}

.stat-card {
  background: linear-gradient(135deg, #0f2849 0%, #1a3a5c 100%);
  border: 2px solid #00d4ff;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  transition: all 0.3s;
}

.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(0, 212, 255, 0.3);
}

.stat-card.safe {
  border-color: #4caf50;
}

.stat-card.warning {
  border-color: #ff9800;
}

.stat-card.danger {
  border-color: #f44336;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.85; }
}

.stat-label {
  font-size: 18px;
  color: #a0a0a0;
  margin-bottom: 12px;
  font-weight: 500;
  letter-spacing: 0.5px;
}

.stat-value {
  font-size: 40px;
  color: #00d4ff;
  font-weight: 700;
  margin-bottom: 8px;
  letter-spacing: 1px;
}

.stat-status {
  font-size: 18px;
  color: #e0e0e0;
  font-weight: 600;
  letter-spacing: 0.5px;
}

/* 차트 섹션 */
.chart-section {
  flex: 1;
  background: linear-gradient(135deg, #0f2849 0%, #1a3a5c 100%);
  border: 2px solid #00d4ff;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  flex-direction: column;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.chart-header h3 {
  font-size: 24px;
  color: #00d4ff;
  font-weight: 700;
  letter-spacing: 1px;
}

.realtime-indicator {
  color: #4caf50;
  font-size: 18px;
  font-weight: 700;
  animation: blink 1.5s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.chart-container {
  flex: 1;
  position: relative;
  min-height: 0;
}

.chart-container canvas {
  width: 100% !important;
  height: 100% !important;
}

/* 하단 통계 */
.stats-summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 15px;
}

.summary-card {
  background: linear-gradient(135deg, #0f2849 0%, #1a3a5c 100%);
  border: 2px solid #00d4ff;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.summary-label {
  font-size: 18px;
  color: #a0a0a0;
  font-weight: 500;
  letter-spacing: 0.5px;
}

.summary-value {
  font-size: 28px;
  color: #00d4ff;
  font-weight: 700;
  letter-spacing: 1px;
}
</style>