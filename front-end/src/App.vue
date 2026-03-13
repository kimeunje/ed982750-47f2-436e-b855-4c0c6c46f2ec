<!-- App.vue -->
<template>
  <div id="app">
    <!-- 헤더 컴포넌트 -->
    <Header :user="authStore.user" :loading="authStore.loading" @logout="handleLogout" />

    <!-- 네비게이션 컴포넌트 -->
    <Navigation />

    <!-- 메인 콘텐츠 영역 -->
    <main class="main-container">
      <!-- 로딩 상태 표시 -->
      <div v-if="authStore.loading && isInitialLoad" class="loading-overlay">
        <div class="loading-spinner"></div>
        <p>인증 상태를 확인하는 중...</p>
      </div>

      <!-- 라우터 뷰 -->
      <RouterView v-else :user="authStore.user" />
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, RouterView } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Header from '@/components/Header.vue'
import Navigation from '@/components/Navigation.vue'

// Vue Router
const router = useRouter()

// Pinia Store
const authStore = useAuthStore()

// 반응형 데이터
const isInitialLoad = ref(true)

// 로그아웃 처리
const handleLogout = async () => {
  try {
    await authStore.logout(false) // 리디렉션 없이 로그아웃

    // Vue Router를 사용하여 로그인 페이지로 이동
    router.push('/login')
  } catch (error) {
    console.error('로그아웃 중 오류:', error)
  }
}

// 라이프사이클 훅
onMounted(async () => {
  try {
    // 인증 상태 초기화
    await authStore.initialize()
  } catch (error) {
    console.error('앱 초기화 중 오류:', error)
  } finally {
    isInitialLoad.value = false
  }
})
</script>

<style>
/* Noto Sans KR TTF 폰트 정의 */
@font-face {
  font-family: 'Noto Sans KR';
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url('/fonts/NotoSansKR-Regular.ttf') format('truetype');
}

@font-face {
  font-family: 'Noto Sans KR';
  font-style: normal;
  font-weight: 500;
  font-display: swap;
  src: url('/fonts/NotoSansKR-Medium.ttf') format('truetype');
}

@font-face {
  font-family: 'Noto Sans KR';
  font-style: normal;
  font-weight: 600;
  font-display: swap;
  src: url('/fonts/NotoSansKR-SemiBold.ttf') format('truetype');
}

@font-face {
  font-family: 'Noto Sans KR';
  font-style: normal;
  font-weight: 700;
  font-display: swap;
  src: url('/fonts/NotoSansKR-Bold.ttf') format('truetype');
}

/* 전역 CSS 변수 */
:root {
  --primary-color: #4056b7;
  --light-blue: #e8eaf6;
  --dark-blue: #3949ab;
  --bright-bg: #f5f7fa;
  --content-bg: #ffffff;
  --subtle-blue: #eef1fd;
  --white: #ffffff;
  --light-gray: #f5f5f5;
  --gray: #9e9e9e;
  --dark-gray: #616161;
  --text-color: #333333;
}

/* 전역 스타일 리셋 */
* {
  box-sizing: border-box;
  padding: 0;
  margin: 0;
}

html,
body {
  max-width: 100vw;
  font-family:
    'Noto Sans KR',
    'Malgun Gothic',
    '맑은 고딕',
    -apple-system,
    BlinkMacSystemFont,
    'Apple SD Gothic Neo',
    'Segoe UI',
    Roboto,
    'Helvetica Neue',
    Arial,
    sans-serif;
  color: var(--text-color);
  background-color: var(--bright-bg);
}

/* 링크 기본 스타일 */
a {
  color: inherit;
  text-decoration: none;
}

/* 메인 컨테이너 */
.main-container {
  width: 100%;
  background-color: var(--bright-bg);
  min-height: calc(100vh - 114px); /* 헤더와 네비게이션 높이 제외 */
}

/* 공통 페이지 요소들 */
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: var(--dark-blue);
  margin: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 15px;
  border-bottom: 2px solid #e5e7eb;
}

.section {
  margin-bottom: 40px;
}

.section-title {
  font-size: 20px;
  margin-bottom: 15px;
  border-left: 4px solid var(--primary-color);
  padding-left: 10px;
  color: var(--dark-blue);
}

/* 페이지네이션 공통 스타일 */
.pagination {
  display: flex;
  justify-content: space-between;
  margin-top: 40px;
  padding-top: 20px;
  border-top: 1px solid var(--light-blue);
}

.pagination button {
  background-color: var(--primary-color);
  color: var(--white);
  border: none;
  padding: 8px 15px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.pagination button:hover {
  background-color: var(--dark-blue);
}

.pagination button:disabled {
  background-color: var(--gray);
  cursor: not-allowed;
}

/* 로딩 애니메이션 */
@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.loading-spinner {
  border: 2px solid #f3f3f3;
  border-top: 2px solid var(--primary-color);
  border-radius: 50%;
  width: 20px;
  height: 20px;
  animation: spin 1s linear infinite;
  display: inline-block;
  margin-right: 8px;
}

/* 유틸리티 클래스 */
.text-center {
  text-align: center;
}

.text-left {
  text-align: left;
}

.text-right {
  text-align: right;
}

.mt-10 {
  margin-top: 10px;
}

.mt-20 {
  margin-top: 20px;
}

.mb-10 {
  margin-bottom: 10px;
}

.mb-20 {
  margin-bottom: 20px;
}

.p-10 {
  padding: 10px;
}

.p-20 {
  padding: 20px;
}

/* 반응형 기본 설정 */
@media (max-width: 768px) {
  .main-container {
    padding: 10px;
  }

  .container {
    padding: 0 10px;
  }

  .page-title {
    font-size: 20px;
  }

  .section-title {
    font-size: 18px;
  }
}

@media (max-width: 480px) {
  .pagination {
    flex-direction: column;
    gap: 10px;
  }

  .pagination button {
    width: 100%;
  }
}

/* 스크롤바 커스터마이징 */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
}

::-webkit-scrollbar-thumb {
  background: var(--gray);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--dark-gray);
}
</style>
