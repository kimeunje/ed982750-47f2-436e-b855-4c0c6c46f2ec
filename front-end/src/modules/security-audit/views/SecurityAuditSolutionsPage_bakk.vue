<!-- views/SecurityAuditSolutionsPage.vue - Template -->
<template>
  <div class="security-audit-layout">
    <!-- 모바일 메뉴 토글 버튼 -->
    <button
      v-if="sidebarRef?.isMobile"
      @click="sidebarRef?.toggleSidebar()"
      class="mobile-menu-toggle"
    >
      <svg width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
        <path
          fill-rule="evenodd"
          d="M2.5 12a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5zm0-4a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5zm0-4a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5z"
        />
      </svg>
    </button>

    <!-- 사이드바 -->
    <Sidebar ref="sidebarRef" />

    <!-- 메인 콘텐츠 -->
    <main class="main-content">
      <div>
        <div class="page-header">
          <h1 class="page-title">보안 감사 조치방법</h1>
        </div>
        <!-- 조치방법 개요 -->
        <div class="section">
          <h2 class="section-title">조치방법 개요</h2>
          <div class="overview-card">
            <div class="overview-content">
              <p>
                이 페이지에서는 정보보안 감사에서 확인해야 할 주요 항목에 대한 조치방법을
                안내합니다. 모든 가이드는 조직의 보안 정책을 준수하기 위한 기본적인 설정 방법과 점검
                사항을 제공합니다.
              </p>
            </div>
          </div>
        </div>

        <!-- 항목별 상세 가이드 -->
        <div class="section">
          <h2 class="section-title">항목별 상세 가이드</h2>
          <div class="solutions-grid">
            <RouterLink
              v-for="(item, index) in solutionItems"
              :key="index"
              :to="item.path"
              class="solution-card-link"
            >
              <div class="solution-card">
                <div class="solution-content">
                  <h3 class="solution-title">{{ item.title }}</h3>
                  <p class="solution-description">{{ item.description }}</p>
                  <div class="solution-meta">
                    <span class="solution-category">{{ item.category }}</span>
                  </div>
                </div>
                <div class="solution-arrow">
                  <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                    <path
                      fill-rule="evenodd"
                      d="M4.646 1.646a.5.5 0 0 1 .708 0l6 6a.5.5 0 0 1 0 .708l-6 6a.5.5 0 0 1-.708-.708L10.293 8 4.646 2.354a.5.5 0 0 1 0-.708z"
                    />
                  </svg>
                </div>
              </div>
            </RouterLink>
          </div>
        </div>

        <!-- 페이지 네비게이션 -->
        <PageNavigation :current-path="route.path" />
      </div>
    </main>
  </div>
</template>

<!-- views/SecurityAuditSolutionsPage.vue - script -->
<script setup>
import { ref } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import Sidebar from '@/components/Sidebar.vue'
import PageNavigation from '@/components/PageNavigation.vue'

const route = useRoute()
const sidebarRef = ref(null)

// 솔루션 항목 데이터
const solutionItems = [
  {
    id: 'screen-saver',
    title: '화면보호기 사용',
    path: '/security-audit/solutions/screen-saver',
    description: '화면보호기 10분 이내 설정 및 암호화 적용',
    category: '시스템 보안',
    difficulty: '쉬움',
  },
  {
    id: 'password-policy',
    title: '패스워드 길이 및 복잡도',
    path: '/security-audit/solutions/password-policy',
    description: '8자 이상 강력한 패스워드 정책 적용 및 정기적 변경',
    category: '인증 보안',
    difficulty: '보통',
  },
  {
    id: 'shared-folder',
    title: '공유폴더 확인',
    path: '/security-audit/solutions/shared-folder',
    description: '불필요한 공유폴더 제거 및 접근 권한 관리',
    category: '접근 통제',
    difficulty: '어려움',
  },
  {
    id: 'remote-desktop',
    title: '원격데스크톱 제한',
    path: '/security-audit/solutions/remote-desktop',
    description: '원격 접속 비활성화 또는 승인된 사용자로 제한',
    category: '네트워크 보안',
    difficulty: '보통',
  },
]
</script>

<!-- CSS는 외부 파일에서 import -->
<style scoped>
@import '../styles/SecurityAuditSolutionsPage.css';
</style>
