<template>
  <div class="data-management">
    <h2>💾 데이터 관리</h2>

    <!-- 샘플 데이터 생성 -->
    <section class="section">
      <h3>🎲 샘플 데이터 생성</h3>
      <div class="form-group">
        <label>생성할 데이터 수:</label>
        <input v-model.number="sampleCount" type="number" min="100" max="10000" step="100">
        <button @click="generateData" :disabled="generating" class="btn-primary">
          {{ generating ? '생성 중...' : '데이터 생성' }}
        </button>
      </div>
      <p class="hint">💡 AI 학습을 위한 임의의 SMT 장비 데이터를 생성합니다.</p>
    </section>

    <!-- 수동 데이터 입력 -->
    <section class="section">
      <h3>✍️ 실시간 데이터 입력</h3>
      <div class="form-grid">
        <div class="form-group">
          <label>라인 ID:</label>
          <select v-model="formData.line_id">
            <option value="LINE_01">LINE 01</option>
            <option value="LINE_02">LINE 02</option>
            <option value="LINE_03">LINE 03</option>
          </select>
        </div>

        <div class="form-group">
          <label>온도 (°C):</label>
          <input v-model.number="formData.temperature" type="number" step="0.1">
        </div>

        <div class="form-group">
          <label>진동 (mm/s):</label>
          <input v-model.number="formData.vibration" type="number" step="0.01">
        </div>

        <div class="form-group">
          <label>전류 (A):</label>
          <input v-model.number="formData.current" type="number" step="0.1">
        </div>

        <div class="form-group">
          <label>생산량 (개/h):</label>
          <input v-model.number="formData.production_count" type="number">
        </div>

        <div class="form-group">
          <label>불량 수:</label>
          <input v-model.number="formData.defect_count" type="number">
        </div>

        <div class="form-group">
          <label>사이클 타임 (초):</label>
          <input v-model.number="formData.cycle_time" type="number" step="0.1">
        </div>

        <div class="form-group">
          <label>압력 (MPa):</label>
          <input v-model.number="formData.pressure" type="number" step="0.01">
        </div>

        <div class="form-group">
          <label>습도 (%):</label>
          <input v-model.number="formData.humidity" type="number" step="1">
        </div>

        <div class="form-group checkbox-group">
          <label>
            <input v-model="formData.failure_occurred" type="checkbox">
            고장 발생
          </label>
        </div>
      </div>

      <div class="form-actions">
        <button @click="submitData" :disabled="submitting" class="btn-primary">
          {{ submitting ? '저장 중...' : '데이터 저장' }}
        </button>
        <button @click="resetForm" class="btn-secondary">초기화</button>
      </div>

      <div v-if="prediction" class="prediction-result">
        <h4>🤖 AI 예측 결과</h4>
        <div class="result-grid">
          <div class="result-item">
            <strong>고장 예측:</strong>
            <span :class="{'text-danger': prediction.predicted_failure}">
              {{ prediction.predicted_failure ? '고장 위험' : '정상' }}
            </span>
          </div>
          <div class="result-item">
            <strong>고장 확률:</strong>
            <span>{{ (prediction.failure_probability * 100).toFixed(1) }}%</span>
          </div>
          <div class="result-item">
            <strong>위험도:</strong>
            <span :class="getRiskClass(prediction.risk_level)">
              {{ prediction.risk_level }}
            </span>
          </div>
        </div>
        <div v-if="prediction.recommendations" class="recommendations">
          <strong>권장사항:</strong>
          <ul>
            <li v-for="(rec, idx) in prediction.recommendations" :key="idx">{{ rec }}</li>
          </ul>
        </div>
      </div>
    </section>

    <!-- 데이터 조회 -->
    <section class="section">
      <h3>📊 저장된 데이터 조회</h3>
      <div class="table-controls">
        <button @click="loadDataList" class="btn-secondary">🔄 새로고침</button>
        <div>총 {{ dataList.length }}건</div>
      </div>
      
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>시간</th>
              <th>라인</th>
              <th>온도</th>
              <th>진동</th>
              <th>전류</th>
              <th>생산량</th>
              <th>불량</th>
              <th>고장여부</th>
              <th>예측</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in dataList" :key="item.id" :class="{'danger-row': item.failure_occurred}">
              <td>{{ formatDate(item.timestamp) }}</td>
              <td>{{ item.line_id }}</td>
              <td>{{ item.temperature.toFixed(1) }}</td>
              <td>{{ item.vibration.toFixed(2) }}</td>
              <td>{{ item.current.toFixed(1) }}</td>
              <td>{{ item.production_count }}</td>
              <td>{{ item.defect_count }}</td>
              <td>
                <span :class="item.failure_occurred ? 'badge-danger' : 'badge-safe'">
                  {{ item.failure_occurred ? '고장' : '정상' }}
                </span>
              </td>
              <td>{{ (item.failure_probability * 100).toFixed(1) }}%</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import axios from '@/api'

export default {
  name: 'DataManagement',
  setup() {
    const sampleCount = ref(1000)
    const generating = ref(false)
    const submitting = ref(false)
    const dataList = ref([])
    const prediction = ref(null)

    const formData = ref({
      line_id: 'LINE_01',
      temperature: 200,
      vibration: 0.3,
      current: 20,
      production_count: 100,
      defect_count: 2,
      cycle_time: 3.0,
      pressure: 0.5,
      humidity: 50,
      failure_occurred: false
    })

    const generateData = async () => {
      if (!confirm(`${sampleCount.value}개의 샘플 데이터를 생성하시겠습니까?`)) return

      generating.value = true
      try {
        const res = await axios.post(`/api/data/generate?samples=${sampleCount.value}`)
        alert(res.data.message)
        await loadDataList()
      } catch (error) {
        alert('데이터 생성 실패: ' + error.message)
      } finally {
        generating.value = false
      }
    }

    const submitData = async () => {
      submitting.value = true
      prediction.value = null
      
      try {
        const res = await axios.post('/api/data/add', formData.value)
        prediction.value = {
          predicted_failure: res.data.predicted_failure,
          failure_probability: res.data.failure_probability,
          risk_level: getRiskLevelText(res.data.failure_probability),
          recommendations: getRecommendations(res.data)
        }
        alert('데이터 저장 완료!')
        await loadDataList()
      } catch (error) {
        alert('데이터 저장 실패: ' + error.message)
      } finally {
        submitting.value = false
      }
    }

    const resetForm = () => {
      formData.value = {
        line_id: 'LINE_01',
        temperature: 200,
        vibration: 0.3,
        current: 20,
        production_count: 100,
        defect_count: 2,
        cycle_time: 3.0,
        pressure: 0.5,
        humidity: 50,
        failure_occurred: false
      }
      prediction.value = null
    }

    const loadDataList = async () => {
      try {
        const res = await axios.get('/api/data/list?limit=50')
        dataList.value = res.data
      } catch (error) {
        console.error('데이터 로드 실패:', error)
      }
    }

    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleString('ko-KR')
    }

    const getRiskLevelText = (prob) => {
      if (prob < 0.3) return 'LOW'
      if (prob < 0.6) return 'MEDIUM'
      return 'HIGH'
    }

    const getRiskClass = (level) => {
      if (level === 'LOW') return 'text-safe'
      if (level === 'MEDIUM') return 'text-warning'
      return 'text-danger'
    }

    const getRecommendations = (data) => {
      const recs = []
      if (data.failure_probability < 0.3) {
        recs.push('✅ 정상 동작 중입니다.')
      } else if (data.failure_probability < 0.6) {
        recs.push('⚠️ 주의: 일부 센서 값이 정상 범위를 벗어났습니다.')
        recs.push('📋 정기 점검을 권장합니다.')
      } else {
        recs.push('🚨 경고: 고장 가능성이 높습니다.')
        recs.push('🔧 즉시 설비 점검이 필요합니다.')
      }
      return recs
    }

    onMounted(() => {
      loadDataList()
    })

    return {
      sampleCount,
      generating,
      submitting,
      formData,
      prediction,
      dataList,
      generateData,
      submitData,
      resetForm,
      loadDataList,
      formatDate,
      getRiskClass
    }
  }
}
</script>

<style scoped>
.data-management {
  padding: 20px;
}

h2 {
  font-size: 2em;
  color: #333;
  margin-bottom: 30px;
}

.section {
  background: #f9f9f9;
  padding: 25px;
  border-radius: 12px;
  margin-bottom: 30px;
}

.section h3 {
  font-size: 1.5em;
  color: #667eea;
  margin-bottom: 20px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  font-weight: 600;
  margin-bottom: 5px;
  color: #333;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 10px;
  border: 2px solid #ddd;
  border-radius: 8px;
  font-size: 1em;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #667eea;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
  margin-bottom: 20px;
}

.checkbox-group {
  display: flex;
  align-items: center;
}

.checkbox-group label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.checkbox-group input[type="checkbox"] {
  width: auto;
  cursor: pointer;
}

.form-actions {
  display: flex;
  gap: 10px;
}

.btn-primary,
.btn-secondary {
  padding: 12px 25px;
  border: none;
  border-radius: 8px;
  font-size: 1em;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: #e0e0e0;
  color: #333;
}

.btn-secondary:hover {
  background: #d0d0d0;
}

.hint {
  margin-top: 10px;
  color: #666;
  font-size: 0.9em;
}

.prediction-result {
  margin-top: 20px;
  padding: 20px;
  background: white;
  border-radius: 8px;
  border-left: 4px solid #667eea;
}

.prediction-result h4 {
  margin-bottom: 15px;
  color: #667eea;
}

.result-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 15px;
  margin-bottom: 15px;
}

.result-item strong {
  display: block;
  margin-bottom: 5px;
  color: #666;
}

.text-safe { color: #4caf50; font-weight: bold; }
.text-warning { color: #ff9800; font-weight: bold; }
.text-danger { color: #f44336; font-weight: bold; }

.recommendations {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #eee;
}

.recommendations ul {
  list-style: none;
  padding: 0;
  margin-top: 10px;
}

.recommendations li {
  padding: 8px 0;
  color: #333;
}

.table-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

thead {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

th, td {
  padding: 12px;
  text-align: left;
}

tbody tr:nth-child(even) {
  background: #f9f9f9;
}

tbody tr:hover {
  background: #f0f0f0;
}

.danger-row {
  background: #fff5f5 !important;
}

.badge-safe,
.badge-danger {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 0.85em;
  font-weight: 600;
}

.badge-safe {
  background: #e8f5e9;
  color: #4caf50;
}

.badge-danger {
  background: #ffebee;
  color: #f44336;
}
</style>