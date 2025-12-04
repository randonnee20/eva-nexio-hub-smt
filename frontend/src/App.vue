<template>
  <div class="app">
    <!-- 상단 헤더 -->
    <header class="header">
      <div class="logo-container">
        <!-- 이미지로 변경된 로고 -->
        <img :src="logoImage" alt="EVA NEXIO.HUB" class="logo-image">
      </div>
      <div class="subtitle-container">
        <span class="subtitle">SMT AX Factory</span>
        <span class="tagline">장비 고장 예측 시스템</span>
      </div>
    </header>

    <div class="content-wrapper">
      <!-- 좌측 세로 메뉴 -->
      <aside class="sidebar">
        <nav class="nav">
          <button 
            v-for="tab in tabs" 
            :key="tab.id"
            :class="['nav-btn', { active: currentTab === tab.id }]"
            @click="currentTab = tab.id"
          >
            {{ tab.name }}
          </button>
        </nav>
      </aside>

      <!-- 메인 컨텐츠 -->
      <main class="main">
        <component :is="currentComponent" />
      </main>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import Dashboard from './components/Dashboard.vue'
import DataManagement from './components/DataManagement.vue'
import Training from './components/Training.vue'
import AIAgent from './components/AIAgent.vue'
import logoImage from './assets/logo-title.png'

export default {
  name: 'App',
  components: {
    Dashboard,
    DataManagement,
    Training,
    AIAgent
  },
  setup() {
    const currentTab = ref('dashboard')
    
    const tabs = [
      { id: 'dashboard', name: '대시보드' },
      { id: 'data', name: '데이터관리' },
      { id: 'training', name: 'AI 학습' },
      { id: 'agent', name: 'AI 에이전트' }
    ]

    const currentComponent = computed(() => {
      const components = {
        dashboard: 'Dashboard',
        data: 'DataManagement',
        training: 'Training',
        agent: 'AIAgent'
      }
      return components[currentTab.value]
    })

    return { currentTab, tabs, currentComponent, logoImage }
  }
}
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Noto Sans KR', sans-serif;
  background: #0a1628;
  color: #e0e0e0;
  overflow: hidden;
}

.app {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
}

/* 상단 헤더 */
.header {
  background: linear-gradient(90deg, #0f2849 0%, #1a3a5c 100%);
  padding: 15px 40px 15px 10px; /* 좌측 패딩 줄임 */
  display: flex;
  align-items: center;
  gap: 40px;
  border-bottom: 2px solid #00d4ff;
  box-shadow: 0 2px 10px rgba(0, 212, 255, 0.3);
  height: 100px;
}

.logo-container {
  display: flex;
  align-items: center;
  padding-left: 10px; /* 대시보드와 정렬 */
}

/* 로고 이미지 스타일 - 50% 확대 */
.logo-image {
  height: 105px; /* 70px의 150% */
  width: auto;
  object-fit: contain;
  filter: drop-shadow(0 0 10px rgba(0, 212, 255, 0.5));
}

.subtitle-container {
  display: flex;
  flex-direction: row; /* 세로 → 가로 배치로 변경 */
  align-items: center; /* 수직 중앙 정렬 */
  gap: 20px; /* 두 텍스트 사이 간격 */
}

/* SMT AX Factory - 20% 축소, 시인성 개선 */
.subtitle {
  font-size: 22.4px; /* 28px의 80% */
  font-weight: 600;
  color: #00e5ff; /* 더 밝고 선명한 시안 색상 */
  letter-spacing: 1.5px;
  text-shadow: 0 0 8px rgba(0, 229, 255, 0.6);
}

/* 장비 고장 예측 시스템 - 20% 확대, 시인성 개선 */
.tagline {
  font-size: 19.2px; /* 16px의 120% */
  color: #e0f7ff; /* 밝고 선명한 밝은 시안 */
  font-weight: 400;
  letter-spacing: 0.8px;
  text-shadow: 0 0 6px rgba(224, 247, 255, 0.5);
}

/* 컨텐츠 래퍼 */
.content-wrapper {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* 좌측 세로 메뉴 */
.sidebar {
  width: 220px;
  background: linear-gradient(180deg, #0f2849 0%, #1a3a5c 100%);
  border-right: 2px solid #00d4ff;
  padding: 20px 0;
  box-shadow: 2px 0 10px rgba(0, 212, 255, 0.2);
}

.nav {
  display: flex;
  flex-direction: column;
  gap: 5px;
  padding: 10px;
}

.nav-btn {
  padding: 20px 25px;
  font-size: 20px;
  font-weight: 500;
  border: none;
  background: transparent;
  color: #a0a0a0;
  cursor: pointer;
  transition: all 0.3s;
  border-radius: 8px;
  text-align: left;
  border-left: 4px solid transparent;
  font-family: 'Noto Sans KR', sans-serif;
  letter-spacing: 1px;
}

.nav-btn:hover {
  color: #00d4ff;
  background: rgba(0, 212, 255, 0.1);
  border-left-color: #00d4ff;
}

.nav-btn.active {
  color: #ffffff;
  background: linear-gradient(90deg, rgba(0, 212, 255, 0.3) 0%, transparent 100%);
  border-left-color: #00d4ff;
  font-weight: 700;
}

/* 메인 컨텐츠 */
.main {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  background: #0a1628;
  padding: 25px;
}

.main::-webkit-scrollbar {
  width: 10px;
}

.main::-webkit-scrollbar-track {
  background: #0f2849;
}

.main::-webkit-scrollbar-thumb {
  background: #00d4ff;
  border-radius: 5px;
}

.main::-webkit-scrollbar-thumb:hover {
  background: #00b8d4;
}
</style>