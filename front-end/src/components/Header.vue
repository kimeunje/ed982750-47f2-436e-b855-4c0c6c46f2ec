<!-- components/Header.vue -->
<template>
  <header class="header" id="header">
    <RouterLink :to="getLinkPath()" class="logo-container scale-hover">
      <!-- 스크롤하지 않았을 때: CI 이미지 표시 -->
      <!-- <img v-if="!scrolled" src="/logo.png" alt="로고" class="logo-image" /> -->
      <img src="/logo.png" alt="로고" class="logo-image" />
      <!-- 스크롤했을 때: 현재 경로 텍스트 표시 -->
      <!-- <div v-if="scrolled" class="route-title">
        {{ getRouteTitle() }}
      </div> -->
    </RouterLink>

    <div class="user-controls">
      <div class="user-menu" v-if="user">
        <div class="user-info">
          <div class="user-name">{{ user.name }}</div>
          <div class="user-role">{{ getUserRoleText(user.role) }}</div>
        </div>
        <div class="user-actions">
          <button @click="handleLogout" class="logout-button">
            <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
              <path
                d="M6 12.5a.5.5 0 0 0 .5.5h4a.5.5 0 0 0 .5-.5v-9a.5.5 0 0 0-.5-.5h-4a.5.5 0 0 0-.5.5V4a.5.5 0 0 1-1 0V3.5A1.5 1.5 0 0 1 6.5 2h4A1.5 1.5 0 0 1 12 3.5v9a1.5 1.5 0 0 1-1.5 1.5h-4A1.5 1.5 0 0 1 5 12.5V12a.5.5 0 0 1 1 .5z"
              />
              <path
                d="M.146 8.354a.5.5 0 0 1 0-.708l3-3a.5.5 0 1 1 .708.708L1.707 7.5H10.5a.5.5 0 0 1 0 1H1.707l2.147 2.146a.5.5 0 0 1-.708.708l-3-3z"
              />
            </svg>
            로그아웃
          </button>
        </div>
      </div>
      <div v-else>
        <RouterLink to="/login" class="login-link">
          <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
            <path d="M3 14s-1 0-1-1 1-4 6-4 6 3 6 4-1 1-1 1H3zm5-6a3 3 0 1 0 0-6 3 3 0 0 0 0 6z" />
          </svg>
          로그인
        </RouterLink>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'

// Props와 Emits 정의
defineProps({
  user: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['logout'])

// 반응형 데이터
const scrolled = ref(false)
const route = useRoute()

// 라우트 제목 가져오기
const getRouteTitle = () => {
  const titleMap = {
    '/': '',
    '/dashboard': '대시보드',
    '/security-audit': '정보보안 감사',
    '/security-audit/results': '검사결과',
    '/security-audit/solutions': '조치방법',
    '/security-audit/solutions/screen-saver': '화면보호기 점검',
    '/security-audit/solutions/antivirus': '백신 상태 점검',
    '/security-audit/solutions/password-policy': '패스워드 정책 점검',
    '/security-audit/solutions/shared-folder': '공유폴더 점검',
    '/security-audit/solutions/remote-desktop': '원격 데스크톱 점검',
    '/security-score': '종합 보안 점수',
    '/security-education': '정보보호 교육',
    '/phishing-training': '악성메일 모의훈련',
    '/contact': '문의사항',
    '/admin': '관리자',
    '/admin/dashboard': '관리자 대시보드',
    '/admin/users': '사용자 관리',
    '/admin/training': '모의훈련 관리',
    '/profile': '프로필',
    '/login': '로그인',
  }

  // 현재 경로와 정확히 일치하는 제목이 있으면 반환
  if (titleMap[route.path]) {
    return titleMap[route.path]
  }

  // 부분 일치 검사 (하위 경로 처리)
  for (const [path, title] of Object.entries(titleMap)) {
    if (route.path.startsWith(path) && path !== '/') {
      return title
    }
  }

  // 메타 정보에서 제목 가져오기
  if (route.meta?.title) {
    return route.meta.title.replace(' - 정보보안 감사 시스템', '')
  }

  return ''
}

// 현재 경로에 따른 링크 경로 결정
const getLinkPath = () => {
  if (!scrolled.value || route.path === '/') {
    return '/'
  }
  return route.path
}

// 사용자 역할 텍스트 변환
const getUserRoleText = (role) => {
  const roleMap = {
    admin: '관리자',
    user: '사용자',
    manager: '관리자',
    employee: '직원',
  }
  return roleMap[role] || '사용자'
}

// 스크롤 이벤트 처리
const handleScroll = () => {
  scrolled.value = window.scrollY > 50
}

// 로그아웃 처리 함수
const handleLogout = (e) => {
  e.preventDefault()
  emit('logout')
}

// 라이프사이클 훅
onMounted(() => {
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})
</script>

<!-- CSS는 외부 파일에서 import -->
<style scoped>
@import './styles/Header.css';
</style>
