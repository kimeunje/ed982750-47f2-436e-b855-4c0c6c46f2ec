<!-- Navigation.vue - 관리자 메뉴 포함 -->
<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

// 모바일 메뉴 상태
const isMobileMenuOpen = ref(false)
const adminMenuExpanded = ref(false)

// 관리자 권한 확인
const isAdmin = computed(() => {
  const role = authStore.user?.role
  console.log('Navigation - 사용자 권한 확인:', {
    username: authStore.user?.username,
    role: role,
    isAdmin: role === 'admin',
  })
  return role === 'admin'
})

// 현재 라우트가 관리자 페이지인지 확인
const isAdminRoute = computed(() => {
  return route.path.startsWith('/admin')
})

// 네비게이션 메뉴 아이템들
const menuItems = computed(() => {
  const baseItems = [
    {
      name: 'SecurityScore',
      path: '/security-score',
      title: '종합 보안 점수',
    },
    {
      name: 'SecurityAudit',
      path: '/security-audit',
      title: '정보보안 감사',
    },
    {
      name: 'SecurityEducation',
      path: '/security-education',
      title: '정보보호 교육',
    },
    {
      name: 'PhishingTraining',
      path: '/phishing-training',
      title: '악성메일 모의훈련',
    },
    {
      name: 'Contact',
      path: '/contact',
      title: '문의사항',
    },
  ]

  return baseItems
})

// 관리자 메뉴 아이템들
const adminMenuItems = computed(() => {
  if (!isAdmin.value) return []

  return [
    { name: 'AdminDashboard', path: '/admin/dashboard', title: '대시보드' },
    { name: 'AdminUserManagement', path: '/admin/users', title: '사용자 관리' },
    { name: 'AdminPhishingTrainingManagement', path: '/admin/training', title: '모의훈련 관리' },
    { name: 'AdminSecurityEducationManagement', path: '/admin/education', title: '교육 관리' }, // 추가
    { name: 'ManualCheckManagement', path: '/admin/manual-check', title: '수시 점검 관리' },
    { name: 'AdminExceptionManagement', path: '/admin/exceptions', title: '제외 설정' },
  ]
})

// 현재 라우트 확인
const isCurrentRoute = (routeName) => {
  return route.name === routeName
}

// 모바일 메뉴 토글
const toggleMobileMenu = () => {
  isMobileMenuOpen.value = !isMobileMenuOpen.value
}

// 관리자 메뉴 토글
const toggleAdminMenu = () => {
  adminMenuExpanded.value = !adminMenuExpanded.value
}

// 관리자 메뉴 닫기
const closeAdminMenu = () => {
  adminMenuExpanded.value = false
}

// 메뉴 클릭 시 모바일 메뉴 닫기
const handleMenuClick = () => {
  isMobileMenuOpen.value = false
}

// 관리자 메뉴 클릭 시 메뉴 닫기
const handleAdminMenuClick = () => {
  adminMenuExpanded.value = false
}

// 관리자 페이지 접근 시 자동으로 관리자 메뉴 확장
watch(
  isAdminRoute,
  (newValue) => {
    if (newValue && isAdmin.value) {
      adminMenuExpanded.value = true
    }
  },
  { immediate: true },
)

// 라우트 변경 시 모바일 메뉴 닫기
watch(route, () => {
  isMobileMenuOpen.value = false
})

// 문서 클릭 이벤트로 관리자 메뉴 닫기
onMounted(() => {
  const handleClickOutside = (event) => {
    // 관리자 메뉴가 열려있을 때만 처리
    if (!adminMenuExpanded.value) return

    // 클릭된 요소가 관리자 메뉴 컨테이너 내부가 아닌 경우 메뉴 닫기
    const adminMenuContainer = event.target.closest('.admin-menu-container')
    if (!adminMenuContainer) {
      adminMenuExpanded.value = false
    }
  }

  // 이벤트 리스너 등록
  document.addEventListener('click', handleClickOutside)

  // 컴포넌트 언마운트 시 이벤트 리스너 제거
  onUnmounted(() => {
    document.removeEventListener('click', handleClickOutside)
  })
})
</script>

<template>
  <nav class="navigation">
    <!-- 데스크톱 네비게이션 -->
    <ul class="desktop-nav">
      <!-- 일반 메뉴 -->
      <li v-for="item in menuItems" :key="item.name">
        <RouterLink :to="item.path" :class="{ 'router-link-active': isCurrentRoute(item.name) }">
          {{ item.title }}
        </RouterLink>
      </li>

      <!-- 관리자 메뉴 (관리자인 경우만 표시) -->
      <li v-if="isAdmin" class="admin-menu-container">
        <div
          class="admin-menu-toggle"
          :class="{ active: isAdminRoute || adminMenuExpanded }"
          @click="toggleAdminMenu"
        >
          관리자 메뉴
          <span class="dropdown-arrow" :class="{ expanded: adminMenuExpanded }">▼</span>
        </div>

        <!-- 관리자 드롭다운 메뉴 -->
        <ul v-if="adminMenuExpanded" class="admin-dropdown">
          <li v-for="adminItem in adminMenuItems" :key="adminItem.name">
            <RouterLink
              :to="adminItem.path"
              :class="{ 'router-link-active': isCurrentRoute(adminItem.name) }"
              @click="handleAdminMenuClick"
            >
              {{ adminItem.title }}
            </RouterLink>
          </li>
        </ul>
      </li>
    </ul>

    <!-- 모바일 햄버거 버튼 -->
    <button
      class="mobile-menu-toggle"
      @click="toggleMobileMenu"
      :class="{ active: isMobileMenuOpen }"
    >
      <span class="hamburger-line" :class="{ active: isMobileMenuOpen }"></span>
      <span class="hamburger-line" :class="{ active: isMobileMenuOpen }"></span>
      <span class="hamburger-line" :class="{ active: isMobileMenuOpen }"></span>
    </button>

    <!-- 모바일 메뉴 오버레이 -->
    <div v-if="isMobileMenuOpen" class="mobile-menu-overlay" @click="toggleMobileMenu"></div>

    <!-- 모바일 메뉴 -->
    <div class="mobile-menu" :class="{ open: isMobileMenuOpen }">
      <ul class="mobile-nav-links">
        <!-- 일반 메뉴 -->
        <li v-for="item in menuItems" :key="item.name">
          <RouterLink
            :to="item.path"
            :class="{ 'router-link-active': isCurrentRoute(item.name) }"
            @click="handleMenuClick"
          >
            {{ item.title }}
          </RouterLink>
        </li>

        <!-- 관리자 메뉴 (관리자인 경우만 표시) -->
        <template v-if="isAdmin">
          <li class="mobile-admin-divider">
            <div class="divider-line"></div>
            <span class="divider-text">관리자 메뉴</span>
            <div class="divider-line"></div>
          </li>

          <li v-for="adminItem in adminMenuItems" :key="adminItem.name">
            <RouterLink
              :to="adminItem.path"
              :class="{ 'router-link-active': isCurrentRoute(adminItem.name) }"
              @click="handleMenuClick"
              class="admin-link"
            >
              {{ adminItem.title }}
            </RouterLink>
          </li>
        </template>
      </ul>
    </div>
  </nav>
</template>

<style scoped>
/* 기본 네비게이션 스타일 (기존 유지) */
.navigation {
  background-color: #4355b9;
  padding: 0 40px;
  z-index: 999;
  flex-shrink: 0;
  position: sticky;
  top: 65px;
  transition: all 0.5s cubic-bezier(0.215, 0.61, 0.355, 1);
  height: 49px;
  overflow: visible; /* 드롭다운을 위해 변경 */
  opacity: 1;
  width: 100%;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
}

/* 데스크톱 네비게이션 */
.desktop-nav {
  display: flex;
  list-style: none;
  margin: 0;
  padding: 0;
  align-items: center;
}

.desktop-nav li a {
  color: white;
  text-decoration: none;
  padding: 15px 20px;
  display: block;
  transition: background-color 0.3s ease;
}

.desktop-nav li a:hover,
.desktop-nav li a.router-link-active {
  background-color: rgba(255, 255, 255, 0.1);
}

/* 관리자 메뉴 컨테이너 */
.admin-menu-container {
  position: relative;
}

.admin-menu-toggle {
  color: white;
  padding: 15px 20px;
  cursor: pointer;
  transition: background-color 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.admin-menu-toggle:hover,
.admin-menu-toggle.active {
  background-color: rgba(255, 255, 255, 0.1);
}

.dropdown-arrow {
  font-size: 12px;
  transition: transform 0.3s ease;
}

.dropdown-arrow.expanded {
  transform: rotate(180deg);
}

/* 관리자 드롭다운 메뉴 */
.admin-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  min-width: 220px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  overflow: hidden;
  z-index: 1001;
  list-style: none;
  margin: 0;
  padding: 8px 0;
  border: 1px solid #e5e7eb;
}

.admin-dropdown li a {
  color: #374151;
  padding: 12px 20px;
  display: block;
  transition: all 0.2s ease;
  font-weight: 500;
}

.admin-dropdown li a:hover {
  background-color: #f3f4f6;
  color: #4355b9;
}

.admin-dropdown li a.router-link-active {
  background-color: #eff6ff;
  color: #4355b9;
  border-left: 3px solid #4355b9;
}

/* 모바일 햄버거 버튼 */
.mobile-menu-toggle {
  display: none;
  flex-direction: column;
  justify-content: space-around;
  width: 24px;
  height: 24px;
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 0;
}

.hamburger-line {
  width: 24px;
  height: 3px;
  background-color: white;
  border-radius: 2px;
  transition: all 0.3s ease;
  transform-origin: center;
}

.hamburger-line.active:nth-child(1) {
  transform: rotate(45deg) translate(5px, 5px);
}

.hamburger-line.active:nth-child(2) {
  opacity: 0;
}

.hamburger-line.active:nth-child(3) {
  transform: rotate(-45deg) translate(7px, -6px);
}

/* 모바일 메뉴 */
.mobile-menu {
  position: fixed;
  top: 114px; /* 헤더 + 네비게이션 높이 */
  right: -300px;
  width: 300px;
  height: calc(100vh - 114px);
  background-color: #4355b9;
  transition: right 0.3s ease;
  z-index: 999;
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.1);
  overflow-y: auto;
}

.mobile-menu.open {
  right: 0;
}

.mobile-nav-links {
  list-style: none;
  margin: 0;
  padding: 20px 0;
}

.mobile-nav-links li {
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.mobile-nav-links li a {
  color: white;
  text-decoration: none;
  padding: 15px 20px;
  display: block;
  transition: background-color 0.3s ease;
}

.mobile-nav-links li a:hover,
.mobile-nav-links li a.router-link-active {
  background-color: rgba(255, 255, 255, 0.1);
}

/* 모바일 관리자 메뉴 구분선 */
.mobile-admin-divider {
  display: flex;
  align-items: center;
  padding: 20px 20px 10px;
  border-bottom: none !important;
}

.divider-line {
  flex: 1;
  height: 1px;
  background-color: rgba(255, 255, 255, 0.3);
}

.divider-text {
  color: rgba(255, 255, 255, 0.8);
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin: 0 15px;
}

/* 모바일 관리자 링크 스타일 */
.admin-link {
  background-color: rgba(255, 255, 255, 0.05) !important;
  border-left: 3px solid rgba(255, 255, 255, 0.3) !important;
}

.admin-link:hover,
.admin-link.router-link-active {
  background-color: rgba(255, 255, 255, 0.15) !important;
  border-left-color: white !important;
}

/* 모바일 메뉴 오버레이 */
.mobile-menu-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 998;
}

/* 반응형 디자인 */
@media (max-width: 768px) {
  .navigation {
    padding: 0 20px;
  }

  /* 데스크톱 네비게이션 숨기기 */
  .desktop-nav {
    display: none;
  }

  /* 모바일 햄버거 버튼 보이기 */
  .mobile-menu-toggle {
    display: flex;
  }
}

@media (max-width: 480px) {
  .navigation {
    padding: 0 15px;
  }

  .mobile-menu {
    width: 280px;
  }
}
</style>
