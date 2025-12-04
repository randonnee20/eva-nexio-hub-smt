<template>
  <div class="data-management">
    <section class="section">
      <h3>샘플 데이터 생성</h3>
      <div class="form-group">
        <label>생성할 데이터 수:</label>
        <input v-model.number="sampleCount" type="number" min="100" max="10000" step="100">
        <button @click="generateData" :disabled="generating" class="btn-primary">
          {{ generating ? '생성 중...' : '데이터 생성' }}
        </button>
      </div>
    </section>

    <section class="section">
      <h3>CSV 파일 불러오기</h3>
      <div class="upload-area">
        <input 
          type="file" 
          ref="csvInput"
          @change="handleCSVSelect"
          accept=".csv"
          style="display: none;"
        >
        <button @click="$refs.csvInput.click()" class="btn-secondary">
          CSV 파일 선택
        </button>
        <span v-if="selectedCSV" class="file-name">{{ selectedCSV.name }}</span>
        <button 
          v-if="selectedCSV"
          @click="uploadCSV" 
          :disabled="uploading"
          class="btn-primary"
        >
          {{ uploading ? '업로드 중...' : '업로드' }}
        </button>
      </div>
      <p class="hint">CSV 형식: line_id, temperature, vibration, current, production_count, defect_count, cycle_time, pressure, humidity, failure_occurred</p>
    </section>

    <section class="section table-section">
      <div class="table-header">
        <h3>저장된 데이터 조회</h3>
        <button @click="loadDataList" class="btn-refresh" :disabled="refreshing">
          {{ refreshing ? '새로고침 중...' : '🔄 새로고침' }}
        </button>
      </div>
      
      <div v-if="dataList.length === 0" class="no-data">
        <p>저장된 데이터가 없습니다. 위에서 샘플 데이터를 생성하거나 CSV를 업로드하세요.</p>
      </div>

      <div v-else class="table-container">
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
              <th>예측확률</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in dataList" :key="item.id" :class="{'danger-row': item.failure_occurred}">
              <td>{{ formatDate(item.timestamp) }}</td>
              <td><span class="line-badge">{{ item.line_id }}</span></td>
              <td>{{ item.temperature.toFixed(1) }}°C</td>
              <td>{{ item.vibration.toFixed(2) }}</td>
              <td>{{ item.current.toFixed(1) }}A</td>
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
import axios from 'axios'

export default {
  name: 'DataManagement',
  setup() {
    const sampleCount = ref(1000)
    const generating = ref(false)
    const dataList = ref([])
    const csvInput = ref(null)
    const selectedCSV = ref(null)
    const uploading = ref(false)
    const refreshing = ref(false)

    const generateData = async () => {
      if (!confirm(`${sampleCount.value}개의 샘플 데이터를 생성하시겠습니까?`)) return

      generating.value = true
      try {
        const res = await axios.post(`/api/data/generate?samples=${sampleCount.value}`)
        
        let message = res.data.message
        if (res.data.csv_saved) {
          message += `\n\nCSV 저장 완료!\n파일: ${res.data.csv_filename}\n경로: ${res.data.csv_path}`
        }
        
        alert(message)
        await loadDataList()
      } catch (error) {
        alert('데이터 생성 실패: ' + error.message)
      } finally {
        generating.value = false
      }
    }

    const handleCSVSelect = (event) => {
      selectedCSV.value = event.target.files[0]
    }

    const uploadCSV = async () => {
      if (!selectedCSV.value) return

      uploading.value = true
      try {
        const formData = new FormData()
        formData.append('file', selectedCSV.value)

        const res = await axios.post('/api/data/upload-csv', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })

        alert(`${res.data.count}개 데이터 업로드 완료!`)
        selectedCSV.value = null
        if (csvInput.value) csvInput.value.value = ''
        await loadDataList()
      } catch (error) {
        alert('CSV 업로드 실패: ' + error.message)
      } finally {
        uploading.value = false
      }
    }

    const loadDataList = async () => {
      refreshing.value = true
      try {
        const timestamp = new Date().getTime()
        const res = await axios.get(`/api/data/list?limit=100&_=${timestamp}`)
        dataList.value = res.data
      } catch (error) {
        console.error('데이터 로드 실패:', error)
        alert('데이터 조회 실패: ' + error.message)
      } finally {
        refreshing.value = false
      }
    }

    const formatDate = (dateString) => {
      const date = new Date(dateString)
      
      // 유효한 날짜인지 확인
      if (isNaN(date.getTime())) {
        return '날짜 오류'
      }
      
      return date.toLocaleString('ko-KR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
      })
    }

    onMounted(() => {
      loadDataList()
    })

    return {
      sampleCount,
      generating,
      dataList,
      csvInput,
      selectedCSV,
      uploading,
      refreshing,
      generateData,
      handleCSVSelect,
      uploadCSV,
      loadDataList,
      formatDate
    }
  }
}
</script>

<style scoped>
.data-management {
  max-width: 1840px;
  margin: 0 auto;
}

.section {
  background: linear-gradient(135deg, #0f3460 0%, #16213e 100%);
  padding: 30px;
  border-radius: 12px;
  border: 2px solid #00d4ff;
  margin-bottom: 30px;
}

.section h3 {
  font-size: 20px;
  color: #00d4ff;
  margin-bottom: 20px;
  font-weight: 600;
}

.form-group {
  display: flex;
  gap: 15px;
  align-items: center;
}

.form-group label {
  color: #e0e0e0;
  font-weight: 500;
}

.form-group input {
  padding: 10px 15px;
  background: #1a1a2e;
  color: #e0e0e0;
  border: 2px solid #00d4ff;
  border-radius: 8px;
  font-size: 16px;
  width: 150px;
}

.btn-primary {
  padding: 10px 30px;
  background: linear-gradient(135deg, #00d4ff 0%, #00b8d4 100%);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0, 212, 255, 0.4);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  padding: 10px 30px;
  background: #16213e;
  color: #00d4ff;
  border: 2px solid #00d4ff;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-secondary:hover {
  background: rgba(0, 212, 255, 0.1);
}

.upload-area {
  display: flex;
  gap: 15px;
  align-items: center;
}

.file-name {
  color: #00d4ff;
  font-weight: 500;
}

.hint {
  margin-top: 10px;
  color: #a0a0a0;
  font-size: 14px;
}

.table-section {
  max-height: 700px;
  overflow: visible;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.btn-refresh {
  padding: 10px 25px;
  background: linear-gradient(135deg, #00d4ff 0%, #00b8d4 100%);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-refresh:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0, 212, 255, 0.4);
}

.btn-refresh:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.no-data {
  text-align: center;
  padding: 40px;
  background: rgba(0, 212, 255, 0.1);
  border-radius: 8px;
  color: #a0a0a0;
  font-size: 16px;
}

.table-container {
  overflow-x: auto;
  max-height: 500px;
  overflow-y: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: #0f3460;
  position: sticky;
  top: 0;
  z-index: 10;
}

th {
  padding: 15px;
  text-align: left;
  color: #00d4ff;
  font-weight: 600;
  border-bottom: 2px solid #00d4ff;
}

td {
  padding: 12px 15px;
  color: #e0e0e0;
  border-bottom: 1px solid rgba(0, 212, 255, 0.2);
}

tbody tr:hover {
  background: rgba(0, 212, 255, 0.1);
}

.danger-row {
  background: rgba(244, 67, 54, 0.1);
}

.line-badge {
  display: inline-block;
  padding: 4px 12px;
  background: #00d4ff;
  color: #1a1a2e;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 700;
}

.badge-safe {
  padding: 4px 12px;
  background: #4caf50;
  color: #fff;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.badge-danger {
  padding: 4px 12px;
  background: #f44336;
  color: #fff;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}
</style>