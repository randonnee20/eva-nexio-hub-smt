<template>
  <div class="rag-query">
    <h2>📚 매뉴얼 검색 (RAG)</h2>

    <!-- RAG 통계 -->
    <section class="section stats">
      <div class="stat-item">
        <span class="stat-icon">📄</span>
        <div>
          <div class="stat-value">{{ ragStats.document_count }}</div>
          <div class="stat-label">저장된 문서</div>
        </div>
      </div>
      <div class="stat-item">
        <span class="stat-icon">🤖</span>
        <div>
          <div class="stat-value">{{ ragStats.llm_model }}</div>
          <div class="stat-label">LLM 모델</div>
        </div>
      </div>
      <div class="stat-item">
        <span class="stat-icon">🔍</span>
        <div>
          <div class="stat-value">{{ ragStats.embedding_model }}</div>
          <div class="stat-label">임베딩 모델</div>
        </div>
      </div>
    </section>

    <!-- 질의응답 -->
    <section class="section">
      <h3>💬 질문하기</h3>
      <div class="query-form">
        <textarea 
          v-model="query" 
          placeholder="SMT 장비에 대해 궁금한 점을 질문하세요...&#10;예) 온도가 230도 이상일 때 조치 방법은?&#10;예) 진동이 심할 때 어떻게 해야 하나요?"
          rows="4"
        ></textarea>
        
        <button 
          @click="submitQuery" 
          :disabled="!query.trim() || querying"
          class="btn-query"
        >
          {{ querying ? '검색 중...' : '🔍 질문하기' }}
        </button>
      </div>

      <div v-if="querying" class="loading">
        <div class="spinner"></div>
        <p>AI가 매뉴얼을 검색하고 답변을 생성 중입니다...</p>
      </div>

      <div v-if="answer" class="answer-box">
        <h4>🤖 AI 답변</h4>
        <div class="answer-content">{{ answer.answer }}</div>
        
        <div v-if="answer.sources && answer.sources.length > 0" class="sources">
          <strong>📌 출처:</strong>
          <span v-for="(source, idx) in answer.sources" :key="idx" class="source-tag">
            {{ source }}
          </span>
        </div>
      </div>
    </section>

    <!-- 빠른 질문 -->
    <section class="section">
      <h3>⚡ 빠른 질문</h3>
      <div class="quick-questions">
        <button 
          v-for="(q, idx) in quickQuestions" 
          :key="idx"
          @click="query = q; submitQuery()"
          class="quick-btn"
        >
          {{ q }}
        </button>
      </div>
    </section>

    <!-- 문서 업로드 -->
    <section class="section">
      <h3>📤 매뉴얼 업로드</h3>
      <div class="upload-form">
        <input 
          type="file" 
          ref="fileInput"
          @change="handleFileSelect"
          accept=".txt"
        >
        <button 
          @click="uploadDocument" 
          :disabled="!selectedFile || uploading"
          class="btn-upload"
        >
          {{ uploading ? '업로드 중...' : '📤 업로드' }}
        </button>
      </div>
      <p class="hint">💡 .txt 형식의 텍스트 파일만 지원됩니다.</p>
      
      <div v-if="uploadResult" class="upload-result">
        {{ uploadResult.success ? '✅' : '❌' }} {{ uploadResult.message }}
      </div>
    </section>

    <!-- 사용 가이드 -->
    <section class="section guide">
      <h3>📖 RAG 시스템 가이드</h3>
      <div class="guide-content">
        <div class="guide-item">
          <strong>1️⃣ RAG란?</strong>
          <p>Retrieval-Augmented Generation의 약자로, 저장된 문서를 검색하여 AI가 정확한 답변을 생성하는 기술입니다.</p>
        </div>
        <div class="guide-item">
          <strong>2️⃣ 사용 방법</strong>
          <p>SMT 장비 관련 질문을 입력하면, AI가 매뉴얼을 검색하여 답변합니다.</p>
        </div>
        <div class="guide-item">
          <strong>3️⃣ 문서 추가</strong>
          <p>새로운 매뉴얼이나 문서를 업로드하여 지식을 확장할 수 있습니다.</p>
        </div>
        <div class="guide-item">
          <strong>4️⃣ 장점</strong>
          <p>실시간 고장 상황에서 빠르게 대응 방법을 찾을 수 있습니다.</p>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import axios from 'axios'

export default {
  name: 'RAGQuery',
  setup() {
    const query = ref('')
    const querying = ref(false)
    const answer = ref(null)
    const ragStats = ref({
      document_count: 0,
      llm_model: '',
      embedding_model: ''
    })
    
    const fileInput = ref(null)
    const selectedFile = ref(null)
    const uploading = ref(false)
    const uploadResult = ref(null)

    const quickQuestions = [
      '온도가 230도 이상일 때 조치 방법은?',
      '진동이 0.7mm/s 이상일 때 어떻게 해야 하나요?',
      '불량률이 5% 이상일 때 확인할 사항은?',
      '예방 정비 주기는 어떻게 되나요?',
      '긴급 정지 시 조치 절차는?'
    ]

    const loadStats = async () => {
      try {
        const res = await axios.get('/api/rag/stats')
        ragStats.value = res.data
      } catch (error) {
        console.error('RAG 통계 로드 실패:', error)
      }
    }

    const submitQuery = async () => {
      if (!query.value.trim()) return

      querying.value = true
      answer.value = null

      try {
        const res = await axios.post('/api/rag/query', {
          query: query.value,
          top_k: 3
        })
        answer.value = res.data
      } catch (error) {
        alert('질문 처리 실패: ' + error.message)
      } finally {
        querying.value = false
      }
    }

    const handleFileSelect = (event) => {
      selectedFile.value = event.target.files[0]
      uploadResult.value = null
    }

    const uploadDocument = async () => {
      if (!selectedFile.value) return

      uploading.value = true
      uploadResult.value = null

      try {
        const formData = new FormData()
        formData.append('file', selectedFile.value)

        const res = await axios.post('/api/rag/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        
        uploadResult.value = res.data
        selectedFile.value = null
        if (fileInput.value) fileInput.value.value = ''
        
        await loadStats()
      } catch (error) {
        uploadResult.value = {
          success: false,
          message: '업로드 실패: ' + error.message
        }
      } finally {
        uploading.value = false
      }
    }

    onMounted(() => {
      loadStats()
    })

    return {
      query,
      querying,
      answer,
      ragStats,
      quickQuestions,
      fileInput,
      selectedFile,
      uploading,
      uploadResult,
      submitQuery,
      handleFileSelect,
      uploadDocument
    }
  }
}
</script>

<style scoped>
.rag-query {
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

.stats {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.stat-item {
  flex: 1;
  min-width: 200px;
  display: flex;
  align-items: center;
  gap: 15px;
  background: rgba(255,255,255,0.1);
  padding: 20px;
  border-radius: 12px;
}

.stat-icon {
  font-size: 2.5em;
}

.stat-value {
  font-size: 1.5em;
  font-weight: bold;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 0.9em;
  opacity: 0.9;
}

.query-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.query-form textarea {
  width: 100%;
  padding: 15px;
  border: 2px solid #ddd;
  border-radius: 12px;
  font-size: 1em;
  font-family: inherit;
  resize: vertical;
}

.query-form textarea:focus {
  outline: none;
  border-color: #667eea;
}

.btn-query {
  align-self: flex-start;
  padding: 15px 40px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 1.1em;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-query:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
}

.btn-query:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading {
  text-align: center;
  padding: 30px;
  background: white;
  border-radius: 12px;
  margin-top: 20px;
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

.answer-box {
  margin-top: 20px;
  background: white;
  padding: 25px;
  border-radius: 12px;
  border-left: 5px solid #667eea;
}

.answer-box h4 {
  margin-bottom: 15px;
  color: #667eea;
  font-size: 1.3em;
}

.answer-content {
  line-height: 1.8;
  color: #333;
  font-size: 1.05em;
  margin-bottom: 20px;
  white-space: pre-wrap;
}

.sources {
  padding-top: 15px;
  border-top: 1px solid #eee;
}

.sources strong {
  color: #666;
  margin-right: 10px;
}

.source-tag {
  display: inline-block;
  background: #e3f2fd;
  color: #1976d2;
  padding: 5px 15px;
  border-radius: 15px;
  font-size: 0.9em;
  margin-right: 8px;
  margin-top: 5px;
}

.quick-questions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.quick-btn {
  padding: 12px 20px;
  background: white;
  border: 2px solid #667eea;
  border-radius: 20px;
  color: #667eea;
  font-size: 0.95em;
  cursor: pointer;
  transition: all 0.3s;
}

.quick-btn:hover {
  background: #667eea;
  color: white;
  transform: translateY(-2px);
}

.upload-form {
  display: flex;
  gap: 15px;
  align-items: center;
  margin-bottom: 10px;
}

.upload-form input[type="file"] {
  flex: 1;
  padding: 10px;
  border: 2px solid #ddd;
  border-radius: 8px;
}

.btn-upload {
  padding: 12px 30px;
  background: #4caf50;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-upload:hover:not(:disabled) {
  background: #45a049;
  transform: translateY(-2px);
}

.btn-upload:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.hint {
  color: #666;
  font-size: 0.9em;
  margin-top: 5px;
}

.upload-result {
  margin-top: 15px;
  padding: 15px;
  background: white;
  border-radius: 8px;
  border-left: 4px solid #4caf50;
}

.guide {
  background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
}

.guide-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
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
</style>