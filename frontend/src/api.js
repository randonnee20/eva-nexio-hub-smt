import axios from 'axios'

// 환경 변수에서 API URL 가져오기
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// axios 인스턴스 생성
const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

export default apiClient