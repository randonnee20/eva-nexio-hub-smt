<template>
  <div class="training">
    <section class="section">
      <h3>현재 모델 상태</h3>
      <div v-if="modelInfo.trained" class="model-status trained">
        <div class="status-badge">학습 완료</div>
        <div class="info-grid">
          <div class="info-item">
            <span class="info-label">마지막 학습</span>
            <span class="info-value">{{ formatDate(modelInfo.last_training) }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">학습 데이터</span>
            <span class="info-value">{{ modelInfo.training_samples }} 건</span>
          </div>
          <div class="info-item">
            <span class="info-label">정확도</span>
            <span class="info-value">{{ (modelInfo.accuracy * 100).toFixed(1) }}%</span>
          </div>
          <div class="info-item">
            <span class="info-label">정밀도</span>
            <span class="info-value">{{ (modelInfo.precision * 100).toFixed(1) }}%</span>
          </div>
          <div class="info-item">
            <span class="info-label">재현율</span>
            <span class="info-value">{{ (modelInfo.recall * 100).toFixed(1) }}%</span>
          </div>
          <div class="info-item">
            <span class="info-label">F1 Score</span>
            <span class="info-value">{{ (modelInfo.f1_score * 100).toFixed(1) }}%</span>
          </div>
        </div>
      </div>

      <div v-else class="model-status untrained">
        <div class="status-badge">미학습</div>
        <p>모델이 아직 학습되지 않았습니다. 아래에서 학습을 진행하세요.</p>
      </div>
    </section>

    <section class="section">
      <h3>모델 학습 실행</h3>
      <div class="training-form">
        <div class="form-group">
          <label>최소 학습 데이터 수:</label>
          <input v-model.number="minSamples" type="number" min="100" step="100">
        </div>

        <button 
          @click="trainModel" 
          :disabled="training"
          class="btn-train"
        >
          {{ training ? '학습 중...' : '학습 시작' }}
        </button>

        <div v-if="training" class="training-progress">
          <div class="spinner"></div>
          <p>AI 모델 학습 중입니다. 잠시만 기다려주세요...</p>
        </div>
      </div>

      <div v-if="trainingResult" class="training-result">
        <h4>{{ trainingResult.success ? '✅' : '❌' }} 학습 결과</h4>
        <p class="result-message">{{ trainingResult.message }}</p>
        
        <div v-if="trainingResult.success" class="metrics-grid">
          <div class="metric-card">
            <div class="metric-label">정확도</div>
            <div class="metric-value">{{ (trainingResult.accuracy * 100).toFixed(1) }}%</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">정밀도</div>
            <div class="metric-value">{{ (trainingResult.precision * 100).toFixed(1) }}%</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">재현율</div>
            <div class="metric-value">{{ (trainingResult.recall * 100).toFixed(1) }}%</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">F1 Score</div>
            <div class="metric-value">{{ (trainingResult.f1_score * 100).toFixed(1) }}%</div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import axios from 'axios'

export default {
  name: 'Training',
  setup() {
    const modelInfo = ref({ trained: false })
    const minSamples = ref(100)
    const training = ref(false)
    const trainingResult = ref(null)

    const loadModelInfo = async () => {
      try {
        const res = await axios.get('/api/model/info')
        modelInfo.value = res.data
      } catch (error) {
        console.error('모델 정보 로드 실패:', error)
      }
    }

    const trainModel = async () => {
      if (!confirm('모델 학습을 시작하시겠습니까?')) return

      training.value = true
      trainingResult.value = null

      try {
        const res = await axios.post('/api/model/train', {
          min_samples: minSamples.value
        })
        
        trainingResult.value = res.data
        
        if (res.data.success) {
          alert('모델 학습 완료!')
          await loadModelInfo()
        } else {
          alert('학습 실패: ' + res.data.message)
        }
      } catch (error) {
        alert('학습 중 오류 발생: ' + error.message)
      } finally {
        training.value = false
      }
    }

    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleString('ko-KR')
    }

    onMounted(() => {
      loadModelInfo()
    })

    return {
      modelInfo,
      minSamples,
      training,
      trainingResult,
      trainModel,
      formatDate
    }
  }
}
</script>

<style scoped>
.training {
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

.model-status {
  padding: 30px;
  border-radius: 12px;
}

.model-status.trained {
  background: rgba(76, 175, 80, 0.1);
  border: 2px solid #4caf50;
}

.model-status.untrained {
  background: rgba(255, 152, 0, 0.1);
  border: 2px solid #ff9800;
}

.status-badge {
  display: inline-block;
  padding: 10px 25px;
  background: linear-gradient(135deg, #00d4ff 0%, #00b8d4 100%);
  color: #fff;
  border-radius: 20px;
  font-weight: 600;
  font-size: 16px;
  margin-bottom: 20px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 20px;
  background: rgba(0, 212, 255, 0.1);
  border-radius: 8px;
}

.info-label {
  font-size: 18px;
  color: #00d4ff;
  font-weight: 600;
}

.info-value {
  font-size: 32px;
  color: #00d4ff;
  font-weight: 700;
}

.training-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  align-items: center;
  gap: 15px;
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

.btn-train {
  padding: 15px 40px;
  background: linear-gradient(135deg, #00d4ff 0%, #00b8d4 100%);
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 18px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  align-self: flex-start;
}

.btn-train:hover:not(:disabled) {
  transform: translateY(-3px);
  box-shadow: 0 10px 25px rgba(0, 212, 255, 0.4);
}

.btn-train:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.training-progress {
  text-align: center;
  padding: 30px;
  background: rgba(0, 212, 255, 0.1);
  border-radius: 12px;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 5px solid rgba(0, 212, 255, 0.3);
  border-top: 5px solid #00d4ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 15px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.training-result {
  margin-top: 30px;
  padding: 30px;
  background: rgba(0, 212, 255, 0.1);
  border-radius: 12px;
  border-left: 5px solid #00d4ff;
}

.training-result h4 {
  margin-bottom: 15px;
  font-size: 20px;
  color: #00d4ff;
}

.result-message {
  font-size: 16px;
  margin-bottom: 20px;
  color: #e0e0e0;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.metric-card {
  background: linear-gradient(135deg, #00d4ff 0%, #00b8d4 100%);
  padding: 25px;
  border-radius: 12px;
  text-align: center;
}

.metric-label {
  font-size: 18px;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 10px;
  font-weight: 600;
}

.metric-value {
  font-size: 40px;
  color: #fff;
  font-weight: 700;
}
</style>