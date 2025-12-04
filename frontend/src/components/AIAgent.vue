<template>
  <div class="ai-agent">
    <div class="agent-grid">
      <!-- 왼쪽: 매뉴얼 검색 -->
      <section class="section query-section">
        <h3>매뉴얼 검색</h3>
        
        <div class="query-form">
          <textarea 
            v-model="query" 
            placeholder="SMT 장비에 대해 질문하세요..."
            rows="4"
          ></textarea>
          
          <button 
            @click="submitQuery" 
            :disabled="!query.trim() || querying"
            class="btn-primary"
          >
            {{ querying ? '검색 중...' : '질문하기' }}
          </button>
        </div>

        <div v-if="querying" class="loading">
          <div class="spinner"></div>
          <p>AI가 매뉴얼을 검색 중입니다...</p>
        </div>

        <div v-if="answer" class="answer-box">
          <h4>AI 답변</h4>
          <div class="answer-content">{{ answer.answer }}</div>
          
          <div v-if="answer.sources && answer.sources.length > 0" class="sources">
            <strong>출처:</strong>
            <span v-for="(source, idx) in answer.sources" :key="idx" class="source-tag">
              {{ source }}
            </span>
          </div>
        </div>

        <!-- 문서 업로드 -->
        <div class="upload-section">
          <h4>매뉴얼 업로드 (최대 10개)</h4>
          
          <div 
            class="dropzone"
            :class="{'dragover': isDragging}"
            @drop.prevent="handleDrop"
            @dragover.prevent="isDragging = true"
            @dragleave.prevent="isDragging = false"
          >
            <div class="dropzone-content">
              <span class="dropzone-icon">📁</span>
              <p>파일을 드래그하거나 클릭하여 선택</p>
              <input 
                type="file" 
                ref="fileInput"
                @change="handleFileSelect"
                accept=".txt"
                multiple
                style="display: none;"
              >
              <button @click="$refs.fileInput.click()" class="btn-select">파일 선택</button>
            </div>
          </div>

          <div v-if="selectedFiles.length > 0" class="file-list">
            <div v-for="(file, idx) in selectedFiles" :key="idx" class="file-item">
              <span>{{ file.name }}</span>
              <button @click="removeFile(idx)" class="btn-remove">✖</button>
            </div>
          </div>

          <div class="upload-actions" v-if="selectedFiles.length > 0">
            <button 
              @click="uploadAllDocuments" 
              :disabled="uploading"
              class="btn-primary"
            >
              {{ uploading ? '업로드 중...' : `${selectedFiles.length}개 파일 업로드` }}
            </button>
          </div>
        </div>
      </section>

      <!-- 오른쪽: 보고서 작성 -->
      <section class="section report-section">
        <h3>보고서 작성</h3>
        
        <div class="report-controls">
          <button @click="generateReport" :disabled="generating" class="btn-generate">
            {{ generating ? '생성 중...' : '보고서 생성' }}
          </button>
          <button 
            @click="downloadPDF" 
            :disabled="!reportData"
            class="btn-download"
          >
            PDF 저장
          </button>
        </div>

        <div v-if="generating" class="loading">
          <div class="spinner"></div>
          <p>보고서를 생성하는 중...</p>
        </div>

        <div v-if="reportData" class="report-preview" ref="reportPreview">
          <div class="report-header">
            <h2>장비 고장 보고서</h2>
            <p class="report-date">{{ reportData.date }}</p>
          </div>

          <div class="report-section-item">
            <h3>1. 전체 현황</h3>
            <table class="report-table">
              <tr>
                <th>총 데이터</th>
                <td>{{ reportData.stats.total_records }} 건</td>
              </tr>
              <tr>
                <th>고장 발생</th>
                <td>{{ reportData.stats.total_failures }} 건</td>
              </tr>
              <tr>
                <th>고장률</th>
                <td>{{ reportData.stats.failure_rate }}%</td>
              </tr>
            </table>
          </div>

          <div class="report-section-item">
            <h3>2. 라인별 분석</h3>
            <table class="report-table">
              <thead>
                <tr>
                  <th>라인</th>
                  <th>총 데이터</th>
                  <th>고장 건수</th>
                  <th>고장률</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(line, key) in reportData.lines" :key="key">
                  <td>{{ key }}</td>
                  <td>{{ line.total }}</td>
                  <td>{{ line.failures }}</td>
                  <td>{{ ((line.failures / line.total) * 100).toFixed(1) }}%</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="report-section-item">
            <h3>3. 모델 성능</h3>
            <table class="report-table" v-if="reportData.model">
              <tr>
                <th>정확도</th>
                <td>{{ (reportData.model.accuracy * 100).toFixed(1) }}%</td>
              </tr>
              <tr>
                <th>정밀도</th>
                <td>{{ (reportData.model.precision * 100).toFixed(1) }}%</td>
              </tr>
              <tr>
                <th>재현율</th>
                <td>{{ (reportData.model.recall * 100).toFixed(1) }}%</td>
              </tr>
              <tr>
                <th>F1 Score</th>
                <td>{{ (reportData.model.f1_score * 100).toFixed(1) }}%</td>
              </tr>
            </table>
            <p v-else>모델이 학습되지 않았습니다.</p>
          </div>

          <div class="report-footer">
            <p>보고서 생성일: {{ reportData.date }}</p>
            <p>시스템: NEXIO.HUB</p>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import axios from 'axios'
import html2canvas from 'html2canvas'
import jsPDF from 'jspdf'

export default {
  name: 'AIAgent',
  setup() {
    const query = ref('')
    const querying = ref(false)
    const answer = ref(null)
    
    const fileInput = ref(null)
    const selectedFiles = ref([])
    const uploading = ref(false)
    const isDragging = ref(false)
    
    const reportData = ref(null)
    const generating = ref(false)
    const reportPreview = ref(null)

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
      const files = Array.from(event.target.files)
      if (files.length + selectedFiles.value.length > 10) {
        alert('최대 10개 파일까지 업로드 가능합니다.')
        return
      }
      selectedFiles.value = [...selectedFiles.value, ...files]
    }

    const handleDrop = (event) => {
      isDragging.value = false
      const files = Array.from(event.dataTransfer.files).filter(f => f.name.endsWith('.txt'))
      
      if (files.length + selectedFiles.value.length > 10) {
        alert('최대 10개 파일까지 업로드 가능합니다.')
        return
      }
      
      selectedFiles.value = [...selectedFiles.value, ...files]
    }

    const removeFile = (index) => {
      selectedFiles.value.splice(index, 1)
    }

    const uploadAllDocuments = async () => {
      if (selectedFiles.value.length === 0) return

      uploading.value = true

      for (const file of selectedFiles.value) {
        try {
          const formData = new FormData()
          formData.append('file', file)

          await axios.post('/api/rag/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
          })
        } catch (error) {
          console.error('업로드 실패:', file.name, error)
        }
      }

      uploading.value = false
      selectedFiles.value = []
      if (fileInput.value) fileInput.value.value = ''
      
      alert('업로드 완료!')
    }

    const generateReport = async () => {
      generating.value = true

      try {
        const statsRes = await axios.get('/api/data/stats')
        const modelRes = await axios.get('/api/model/info')

        reportData.value = {
          date: new Date().toLocaleString('ko-KR'),
          stats: statsRes.data,
          lines: statsRes.data.lines || {},
          model: modelRes.data.trained ? {
            accuracy: modelRes.data.accuracy,
            precision: modelRes.data.precision,
            recall: modelRes.data.recall,
            f1_score: modelRes.data.f1_score
          } : null
        }
      } catch (error) {
        alert('보고서 생성 실패: ' + error.message)
      } finally {
        generating.value = false
      }
    }

    const downloadPDF = async () => {
      if (!reportPreview.value) return

      try {
        // 스크롤 위치 저장
        const originalScrollTop = reportPreview.value.scrollTop
        const originalMaxHeight = reportPreview.value.style.maxHeight
        const originalOverflow = reportPreview.value.style.overflow
        
        // 전체 내용을 캡처하기 위해 높이 제한 해제
        reportPreview.value.style.maxHeight = 'none'
        reportPreview.value.style.overflow = 'visible'
        reportPreview.value.scrollTop = 0

        // 캔버스 생성 (전체 높이)
        const canvas = await html2canvas(reportPreview.value, {
          scale: 2,
          backgroundColor: '#ffffff',
          useCORS: true,
          allowTaint: true,
          scrollY: 0,
          scrollX: 0,
          windowHeight: reportPreview.value.scrollHeight
        })

        // 원래 스타일 복원
        reportPreview.value.style.maxHeight = originalMaxHeight
        reportPreview.value.style.overflow = originalOverflow
        reportPreview.value.scrollTop = originalScrollTop

        // PDF 생성 (A4 크기)
        const imgData = canvas.toDataURL('image/png')
        const pdf = new jsPDF('p', 'mm', 'a4')
        
        const pdfWidth = 210 // A4 width in mm
        const pdfHeight = 297 // A4 height in mm
        const imgWidth = pdfWidth
        const imgHeight = (canvas.height * pdfWidth) / canvas.width
        
        let heightLeft = imgHeight
        let position = 0

        // 첫 페이지 추가
        pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight)
        heightLeft -= pdfHeight

        // 여러 페이지가 필요한 경우 페이지 추가
        while (heightLeft > 0) {
          position = heightLeft - imgHeight
          pdf.addPage()
          pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight)
          heightLeft -= pdfHeight
        }
        
        const filename = `장비_고장_보고서_${new Date().toISOString().slice(0,10)}.pdf`
        pdf.save(filename)
        
        alert(`PDF 저장 완료!\n파일명: ${filename}`)
      } catch (error) {
        alert('PDF 저장 실패: ' + error.message)
      }
    }

    return {
      query,
      querying,
      answer,
      submitQuery,
      fileInput,
      selectedFiles,
      uploading,
      isDragging,
      handleFileSelect,
      handleDrop,
      removeFile,
      uploadAllDocuments,
      reportData,
      generating,
      reportPreview,
      generateReport,
      downloadPDF
    }
  }
}
</script>

<style scoped>
.ai-agent {
  max-width: 1840px;
  margin: 0 auto;
}

.agent-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 30px;
}

.section {
  background: linear-gradient(135deg, #0f3460 0%, #16213e 100%);
  padding: 30px;
  border-radius: 12px;
  border: 2px solid #00d4ff;
  height: fit-content;
}

.section h3 {
  font-size: 20px;
  color: #00d4ff;
  margin-bottom: 20px;
  font-weight: 600;
}

.query-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-bottom: 20px;
}

.query-form textarea {
  width: 100%;
  padding: 15px;
  background: #1a1a2e;
  color: #e0e0e0;
  border: 2px solid #00d4ff;
  border-radius: 8px;
  font-size: 16px;
  font-family: 'Noto Sans KR', sans-serif;
  resize: vertical;
}

.btn-primary {
  padding: 12px 30px;
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

.loading {
  text-align: center;
  padding: 30px;
  background: rgba(0, 212, 255, 0.1);
  border-radius: 8px;
  margin: 20px 0;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(0, 212, 255, 0.3);
  border-top: 4px solid #00d4ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 15px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.answer-box {
  background: rgba(0, 212, 255, 0.1);
  padding: 20px;
  border-radius: 8px;
  border-left: 4px solid #00d4ff;
  margin: 20px 0;
}

.answer-box h4 {
  color: #00d4ff;
  margin-bottom: 15px;
}

.answer-content {
  color: #e0e0e0;
  line-height: 1.8;
  white-space: pre-wrap;
}

.sources {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid rgba(0, 212, 255, 0.3);
}

.source-tag {
  display: inline-block;
  background: rgba(0, 212, 255, 0.2);
  color: #00d4ff;
  padding: 5px 15px;
  border-radius: 15px;
  font-size: 14px;
  margin-right: 8px;
  margin-top: 5px;
}

.upload-section {
  margin-top: 30px;
  padding-top: 30px;
  border-top: 2px solid rgba(0, 212, 255, 0.3);
}

.upload-section h4 {
  color: #00d4ff;
  margin-bottom: 15px;
  font-size: 18px;
}

.dropzone {
  border: 3px dashed #00d4ff;
  border-radius: 12px;
  padding: 30px;
  text-align: center;
  background: rgba(0, 212, 255, 0.05);
  cursor: pointer;
  transition: all 0.3s;
  margin-bottom: 15px;
}

.dropzone.dragover {
  background: rgba(0, 212, 255, 0.15);
  border-color: #00b8d4;
}

.dropzone-icon {
  font-size: 3em;
  display: block;
  margin-bottom: 10px;
}

.btn-select {
  margin-top: 15px;
  padding: 10px 25px;
  background: #16213e;
  color: #00d4ff;
  border: 2px solid #00d4ff;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
}

.file-list {
  margin-bottom: 15px;
}

.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background: rgba(0, 212, 255, 0.1);
  border-radius: 8px;
  margin-bottom: 8px;
  color: #e0e0e0;
}

.btn-remove {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
}

.report-controls {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
}

.btn-generate {
  padding: 12px 30px;
  background: linear-gradient(135deg, #00d4ff 0%, #00b8d4 100%);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-download {
  padding: 12px 30px;
  background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-download:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.report-preview {
  background: #fff;
  color: #000;
  padding: 25px 30px; /* 40px → 25px로 축소 */
  border-radius: 8px;
  max-height: 800px;
  overflow-y: auto;
}

.report-header {
  text-align: center;
  margin-bottom: 20px; /* 30px → 20px */
  padding-bottom: 12px; /* 20px → 12px */
  border-bottom: 3px solid #00d4ff;
}

.report-header h2 {
  font-size: 24px; /* 28px → 24px */
  color: #0f3460;
  margin-bottom: 6px; /* 10px → 6px */
}

.report-date {
  color: #666;
  font-size: 13px; /* 14px → 13px */
}

.report-section-item {
  margin-bottom: 18px; /* 30px → 18px */
}

.report-section-item h3 {
  font-size: 18px; /* 20px → 18px */
  color: #0f3460;
  margin-bottom: 10px; /* 15px → 10px */
  border-left: 4px solid #00d4ff;
  padding-left: 12px; /* 15px → 12px */
}

.report-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 12px; /* 20px → 12px */
}

.report-table th,
.report-table td {
  padding: 8px 10px; /* 12px → 8px */
  border: 1px solid #ddd;
  text-align: left;
  font-size: 13px; /* 기본 크기에서 축소 */
}

.report-table th {
  background: #0f3460;
  color: #fff;
  font-weight: 600;
}

.report-table tbody tr:nth-child(even) {
  background: #f9f9f9;
}

.report-footer {
  margin-top: 20px; /* 40px → 20px */
  padding-top: 12px; /* 20px → 12px */
  border-top: 2px solid #00d4ff;
  text-align: center;
  color: #666;
  font-size: 12px; /* 14px → 12px */
}
</style>