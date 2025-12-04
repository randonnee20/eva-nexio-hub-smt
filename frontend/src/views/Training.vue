<template>
  <div class="training">
    <h2>🤖 AI 모델 학습</h2>

    <!-- 모델 정보 -->
    <section class="section">
      <h3>📊 현재 모델 상태</h3>
      <div v-if="modelInfo.trained" class="model-status trained">
        <div class="status-badge">✅ 학습 완료</div>
        <div class="info-grid">
          <div class="info-item">
            <strong>마지막 학습:</strong>
            <span>{{ formatDate(modelInfo.last_training) }}</span>
          </div>
          <div class="info-item">
            <strong>학습 데이터:</strong>
            <span>{{ modelInfo.training_samples }} 건</span>
          </div>
          <div class="info-item">
            <strong>정확도:</strong>
            <span class="metric">{{ (modelInfo.accuracy * 100).toFixed(2) }}%</span>
          </div>
          <div class="info-item">
            <strong>정밀도:</strong>
            <span class="metric">{{ (modelInfo.precision * 100).toFixed(2) }}%</span>
          </div>
          <div class="info-item">
            <strong>재현율:</strong>
            <span class="metric">{{ (modelInfo.recall * 100).toFixed(2) }}%</span>
          </div>
          <div class="info-item">
            <strong>F1 Score:</strong>
            <span class="metric">{{ (modelInfo.f1_score * 100).toFixed(2) }}%</span>
          </div>
        </div>

        <div v-if="modelInfo.feature_importance" class="feature-importance">
          <h4>📈 특성 중요도</h4>
          <div class="importance-bars">
            <div 
              v-for="(value, feature) in modelInfo.feature_importance" 
              :key="feature"
              class="importance-item"
            >
              <span class="feature-name">{{ getFeatureName(feature) }}</span>
              <div class="bar-container">
                <div class="bar" :style="{width: (value * 100) + '%'}"></div>
              </div>
              <span class="feature-value">{{ (value * 100).toFixed(1) }}%</span>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="model-status untrained">
        <div class="status-badge">⚠️ 미학습</div>
        <p>모델이 아직 학습되지 않았습니다. 아래에서 학습을 진행하세요.</p>
      </div>
    </section>

    <!-- 학습 실행 -->
    <section class="section">
      <h3>🎓 모델 학습 실행</h3>
      <div class="training-form">
        <div class="form-group">
          <label>최소 학습 데이터 수:</label>
          <input v-model.number="minSamples" type="number" min="100" step="100">
          <p class="hint">💡 최소 100개 이상의 데이터가 필요합니다.</p>
        </div>

        <button 
          @click="trainModel" 
          :disabled="training"
          class="btn-train"
        >
          {{ training ? '학습 중...' : '🚀 학습 시작' }}
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
            <div class="metric-value">{{ (trainingResult.accuracy * 100).toFixed(2) }}%</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">정밀도</div>
            <div class="metric-value">{{ (trainingResult.precision * 100).toFixed(2) }}%</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">재현율</div>
            <div class="metric-value">{{ (trainingResult.recall * 100).toFixed(2) }}%</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">F1 Score</div>
            <div class="metric-value">{{ (trainingResult.f1_score * 100).toFixed(2) }}%</div>
          </div>
        </div>
      </div>
    </section>

    <!-- 학습 가이드 -->
    <section class="section guide">
      <h3>📖 학습 가이드</h3>
      <div class="guide-content">
        <div class="guide-item">
          <strong>1️⃣ 데이터 수집</strong>
          <p>먼저 "데이터 관리" 탭에서 충분한 양의 학습 데이터를 준비하세요.</p>
        </div>
        <div class="guide-item">
          <strong>2️⃣ 모델 학습</strong>
          <p>최소 100개 이상의 데이터로 AI 모델을 학습시킵니다.</p>
        </div>
        <div class="guide-item">
          <strong>3️⃣ 성능 확인</strong>
          <p>학습 완료 후 정확도, 정밀도 등의 지표를 확인하세요.</p>
        </div>
        <div class="guide-item">
          <strong>4️⃣ 재학습</strong>
          <p>새로운 데이터가 추가되면 주기적으로 재학습하여 성능을 개선하세요.</p>
        </div>
      </div>

      <div class="metrics-explanation">
        <h4>📊 성능 지표 설명</h4>
        <ul>
          <li><strong>정확도 (Accuracy):</strong> 전체 예측 중 올바른 예측의 비율</li>
          <li><strong>정밀도 (Precision):</strong> 고장으로 예측한 것 중 실제 고장의 비율</li>
          <li><strong>재현율 (Recall):</strong> 실제 고장 중 정확히 예측한 비율</li>
          <li><strong>F1 Score:</strong> 정밀도와 재현율의 조화 평균</li>
        </ul>
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
    const modelInfo = ref({
      trained: false
    })
    const minSamples = ref(100)
    const training = ref(false)
    const trainingResult = ref(null)

    const featureNames = {
      temperature: '온도',
      vibration: '진동',
      current: '전류',
      production_count: '생산량',
      defect_count: '불량수',
      cycle_time: '사이클타임',
      pressure: '압력',
      humidity: '습도'
    }

    const loadModelInfo = async () => {
      try {
        const res = await axios.get('/api/model/info')
        modelInfo.value = res.data
      } catch (error) {
        console.error('모델 정보 로드 실패:', error)
      }
    }

    const trainModel = async () => {
      if (!confirm('모델 학습을 시작하시겠습니까? (수 분 소요될 수 있습니다)')) return

      training.value = true
      trainingResult.value = null

      try {
        const res = await axios.post('/api/model/train', {
          min_samples: minSamples.value
        })
        
        trainingResult.value = res.data
        
        if (res.data.success) {
          alert('✅ 모델 학습 완료!')
          await loadModelInfo()
        } else {
          alert('❌ 학습 실패: ' + res.data.message)
        }
      } catch (error) {
        alert('학습 중 오류 발생: ' + error.message)
        trainingResult.value = {
          success: false,
          message: error.message
        }
      } finally {
        training.value = false
      }
    }

    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleString('ko-KR')
    }

    const getFeatureName = (feature) => {
      return featureNames[feature] || feature
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
      formatDate,
      getFeatureName
    }
  }
}
</script>

<style scoped>
.training {
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

.model-status {
  padding: 25px;
  border-radius: 12px;
}

.model-status.trained {
  background: #e8f5e9;
  border-left: 5px solid #4caf50;
}

.model-status.untrained {
  background: #fff3e0;
  border-left: 5px solid #ff9800;
}

.status-badge {
  display: inline-block;
  padding: 8px 20px;
  border-radius: 20px;
  font-weight: 600;
  font-size: 1.1em;
  margin-bottom: 20px;
  background: white;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
  margin-bottom: 25px;
}

.info-item {
  background: white;
  padding: 15px;
  border-radius: 8px;
}

.info-item strong {
  display: block;
  color: #666;
  margin-bottom: 5px;
  font-size: 0.9em;
}

.info-item span {
  font-size: 1.1em;
  color: #333;
}

.info-item .metric {
  color: #667eea;
  font-weight: bold;
  font-size: 1.3em;
}

.feature-importance {
  background: white;
  padding: 20px;
  border-radius: 8px;
  margin-top: 20px;
}

.feature-importance h4 {
  margin-bottom: 15px;
  color: #667eea;
}

.importance-bars {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.importance-item {
  display: grid;
  grid-template-columns: 120px 1fr 60px;
  align-items: center;
  gap: 10px;
}

.feature-name {
  font-weight: 600;
  color: #333;
}

.bar-container {
  height: 20px;
  background: #e0e0e0;
  border-radius: 10px;
  overflow: hidden;
}

.bar {
  height: 100%;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  transition: width 0.5s;
}

.feature-value {
  text-align: right;
  font-weight: 600;
  color: #667eea;
}

.training-form {
  background: white;
  padding: 25px;
  border-radius: 12px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-weight: 600;
  margin-bottom: 8px;
  color: #333;
}

.form-group input {
  width: 100%;
  max-width: 300px;
  padding: 10px;
  border: 2px solid #ddd;
  border-radius: 8px;
  font-size: 1em;
}

.hint {
  margin-top: 8px;
  color: #666;
  font-size: 0.9em;
}

.btn-train {
  padding: 15px 40px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 1.2em;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-train:hover:not(:disabled) {
  transform: translateY(-3px);
  box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4);
}

.btn-train:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.training-progress {
  margin-top: 25px;
  text-align: center;
  padding: 30px;
  background: #f5f5f5;
  border-radius: 12px;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 5px solid #f3f3f3;
  border-top: 5px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 15px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.training-result {
  margin-top: 25px;
  padding: 25px;
  background: white;
  border-radius: 12px;
  border-left: 5px solid #667eea;
}

.training-result h4 {
  margin-bottom: 15px;
  font-size: 1.3em;
  color: #667eea;
}

.result-message {
  font-size: 1.1em;
  margin-bottom: 20px;
  color: #333;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 15px;
}

.metric-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
  border-radius: 12px;
  color: white;
  text-align: center;
}

.metric-label {
  font-size: 0.9em;
  opacity: 0.9;
  margin-bottom: 10px;
}

.metric-value {
  font-size: 2em;
  font-weight: bold;
}

.guide {
  background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
}

.guide-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 25px;
}

.guide-item {
  background: white;
  padding: 20px;
  border-radius: 12px;
  border-left: 4px solid #667eea;
}

.guide-item strong {
  display: block;
  font-size: 1.1em;
  color: #667eea;
  margin-bottom: 10px;
}

.guide-item p {
  color: #666;
  line-height: 1.6;
}

.metrics-explanation {
  background: white;
  padding: 20px;
  border-radius: 12px;
}

.metrics-explanation h4 {
  margin-bottom: 15px;
  color: #667eea;
}

.metrics-explanation ul {
  list-style: none;
  padding: 0;
}

.metrics-explanation li {
  padding: 10px 0;
  border-bottom: 1px solid #eee;
  color: #333;
  line-height: 1.6;
}

.metrics-explanation li:last-child {
  border-bottom: none;
}

.metrics-explanation strong {
  color: #667eea;
}
</style>