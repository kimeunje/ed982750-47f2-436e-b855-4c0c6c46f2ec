// router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// 컴포넌트 import - 레이지 로딩 적용
const LoginPage = () => import('@/modules/auth/views/LoginPage.vue')

// Security Audit 관련 페이지들
const SecurityAuditPage = () => import('@/modules/security-audit/views/SecurityAuditPage.vue')
const SecurityAuditResultsPage = () =>
  import('@/modules/security-audit/views/SecurityAuditResultsPage.vue')
const SecurityAuditSolutionsPage = () =>
  import('@/modules/security-audit/views/SecurityAuditSolutionsPage.vue')
const ContactPage = () => import('@/modules/contact/views/ContactPage.vue')

// Solutions 하위 페이지들
const ScreenSaverSolutionPage = () =>
  import('@/modules/security-audit/views/solutions/ScreenSaverSolutionPage.vue')
const PasswordPolicySolutionPage = () =>
  import('@/modules/security-audit/views/solutions/PasswordPolicySolutionPage.vue')
const SharedFolderSolutionPage = () =>
  import('@/modules/security-audit/views/solutions/SharedFolderSolutionPage.vue')
const RemoteDesktopSolutionPage = () =>
  import('@/modules/security-audit/views/solutions/RemoteDesktopSolutionPage.vue')

const SecurityEducationPage = () =>
  import('@/modules/security-education/views/SecurityEducationPage.vue')
const PhishingTrainingPage = () =>
  import('@/modules/phishing-training/views/PhishingTrainingPage.vue')
const SecurityScorePage = () => import('@/modules/total-score/views/TotalScorePage.vue')

const AdminExceptionManagement = () => import('@/modules/admin/views/AdminExceptionManagement.vue')
const AdminPhishingTrainingManagement = () =>
  import('@/modules/admin/views/AdminPhishingTrainingManagement.vue')

const ManualCheckManagement = () => import('@/modules/admin/views/ManualCheckManagement.vue')

// 1. 먼저 관리자 대시보드 컴포넌트 import 추가
const AdminDashboard = () => import('@/modules/admin/views/AdminDashboard.vue')
const AdminUserManagement = () => import('@/modules/admin/views/AdminUserManagement.vue')
const AdminUserDetail = () => import('@/modules/admin/views/AdminUserDetail.vue')

// 관리자 교육 관리 컴포넌트 import 추가
const AdminSecurityEducationManagement = () =>
  import('@/modules/admin/views/AdminSecurityEducationManagement.vue')

// 라우터 설정
const routes = [
  // 홈 페이지
  {
    path: '/',
    name: 'Home',
    component: SecurityScorePage,
    meta: {
      title: '정보보안 감사 시스템',
      description: '정보보안 감사 시스템',
    },
  },

  {
    path: '/admin/manual-check',
    name: 'AdminManualCheck',
    component: ManualCheckManagement,
    meta: {
      title: '수시 점검 관리',
      requiresAuth: true,
      requiresAdmin: true,
    },
  },

  // 관리자 대시보드 메인
  {
    path: '/admin/dashboard',
    name: 'AdminDashboard',
    component: AdminDashboard,
    meta: {
      title: '관리자 대시보드',
      requiresAuth: true,
      requiresAdmin: true,
    },
  },

  {
    path: '/admin/education',
    name: 'AdminSecurityEducationManagement',
    component: AdminSecurityEducationManagement,
    meta: {
      title: '정보보호 교육 관리',
      requiresAuth: true,
      requiresAdmin: true,
    },
  },
  // 관리자 사용자 관리 (전체 목록)
  {
    path: '/admin/users',
    name: 'AdminUserManagement',
    component: AdminUserManagement,
    meta: {
      title: '사용자 관리',
      requiresAuth: true,
      requiresAdmin: true,
    },
  },

  // 사용자 상세 페이지
  {
    path: '/admin/users/:userId/detail',
    name: 'AdminUserDetail',
    component: AdminUserDetail,
    props: true,
    meta: {
      title: '사용자 상세 정보',
      requiresAuth: true,
      requiresAdmin: true,
    },
  },

  // 기존 admin 라우트 수정 (대시보드로 리다이렉트)
  {
    path: '/admin',
    name: 'Admin',
    redirect: '/admin/dashboard',
    meta: {
      requiresAuth: true,
      requiresAdmin: true,
    },
  },

  {
    path: '/admin/exceptions',
    name: 'AdminExceptionManagement',
    component: AdminExceptionManagement,
    meta: { requiresAuth: true, requiresAdmin: true },
  },

  // 로그인 페이지
  {
    path: '/login',
    name: 'Login',
    component: LoginPage,
    meta: {
      title: '로그인 - 정보보안 감사 시스템',
      requiresGuest: true, // 이미 로그인한 사용자는 접근 제한
    },
  },

  // 정보보안 감사 관련 라우트
  {
    path: '/security-audit',
    name: 'SecurityAudit',
    component: SecurityAuditPage,
    meta: {
      title: '정보보안 감사 현황',
      requiresAuth: true,
    },
  },

  // 검사결과 페이지
  {
    path: '/security-audit/results',
    name: 'SecurityAuditResults',
    component: SecurityAuditResultsPage,
    meta: {
      title: '보안 감사 결과',
      requiresAuth: true,
    },
  },

  // 조치방법 메인 페이지
  {
    path: '/security-audit/solutions',
    name: 'SecurityAuditSolutions',
    component: SecurityAuditSolutionsPage,
    meta: {
      title: '보안 감사 조치방법',
      requiresAuth: true,
    },
  },

  // 조치방법 세부 페이지들
  {
    path: '/security-audit/solutions/screen-saver',
    name: 'ScreenSaverSolution',
    component: ScreenSaverSolutionPage,
    meta: {
      title: '화면보호기 사용 확인',
      requiresAuth: true,
    },
  },

  {
    path: '/security-education',
    name: 'SecurityEducation',
    component: SecurityEducationPage,
    meta: {
      title: '정보보호 교육 현황',
      requiresAuth: true,
    },
  },

  // 악성메일 모의훈련 현황 페이지
  {
    path: '/phishing-training',
    name: 'PhishingTraining',
    component: PhishingTrainingPage,
    meta: {
      title: '악성메일 모의훈련 현황',
      requiresAuth: true,
    },
  },

  // 종합 보안 점수 페이지
  {
    path: '/security-score',
    name: 'SecurityScore',
    component: SecurityScorePage,
    meta: {
      title: '종합 보안 점수',
      requiresAuth: true,
    },
  },

  // 모의훈련 관리
  {
    path: '/admin/training',
    name: 'AdminPhishingTrainingManagement',
    component: AdminPhishingTrainingManagement,
    meta: {
      title: '모의훈련 관리',
      requiresAuth: true,
      requiresAdmin: true,
    },
  },

  {
    path: '/security-audit/solutions/password-policy',
    name: 'PasswordPolicySolution',
    component: PasswordPolicySolutionPage,
    meta: {
      title: '패스워드 정책 점검',
      requiresAuth: true,
    },
  },

  {
    path: '/security-audit/solutions/shared-folder',
    name: 'SharedFolderSolution',
    component: SharedFolderSolutionPage,
    meta: {
      title: '공유폴더 확인',
      requiresAuth: true,
    },
  },
  {
    path: '/security-audit/solutions/remote-desktop',
    name: 'RemoteDesktopSolution',
    component: RemoteDesktopSolutionPage,
    meta: {
      title: '원격데스크톱 제한',
      requiresAuth: true,
    },
  },

  // 문의사항 페이지
  {
    path: '/contact',
    name: 'Contact',
    component: ContactPage,
    meta: {
      title: '문의사항 - 정보보안 감사 시스템',
      requiresAuth: true,
    },
  },

  // // 404 페이지 - 마지막에 위치해야 함
  // {
  //   path: '/:pathMatch(.*)*',
  //   name: 'NotFound',
  //   component: NotFoundPage,
  //   meta: {
  //     title: '페이지를 찾을 수 없습니다',
  //   },
  // },
]

// 라우터 인스턴스 생성
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior(to, from, savedPosition) {
    // 브라우저 뒤로가기/앞으로가기 시 스크롤 위치 복원
    if (savedPosition) {
      return savedPosition
    }
    // 해시가 있으면 해당 요소로 스크롤
    if (to.hash) {
      return {
        el: to.hash,
        behavior: 'smooth',
      }
    }
    // 기본적으로 페이지 상단으로 스크롤
    return { top: 0 }
  },
})

// 전역 네비게이션 가드
router.beforeEach(async (to, from, next) => {
  // 페이지 타이틀 설정
  if (to.meta.title) {
    document.title = to.meta.title
  }

  // 인증 상태 확인
  const authStore = useAuthStore()

  // 로딩이 완료되지 않았다면 대기
  if (authStore.loading) {
    await authStore.initialize()
  }

  const isAuthenticated = authStore.isAuthenticated
  const requiresAuth = to.meta.requiresAuth
  const requiresGuest = to.meta.requiresGuest
  const requiresAdmin = to.meta.requiresAdmin

  // 인증이 필요한 페이지에 미인증 사용자가 접근하는 경우
  if (requiresAuth && !isAuthenticated) {
    console.log('인증이 필요한 페이지에 미인증 사용자 접근:', to.path)
    next({
      name: 'Login',
      query: { redirect: to.fullPath },
    })
    return
  }
  // 게스트 전용 페이지에 인증된 사용자가 접근하는 경우 (예: 로그인 페이지)
  if (requiresGuest && isAuthenticated) {
    console.log('⚠️ 로그인한 사용자가 게스트 전용 페이지 접근:', to.path)
    const redirectPath = to.query.redirect || '/'
    next(redirectPath)
    return
  }

  // 관리자 권한이 필요한 페이지 체크
  if (requiresAdmin && isAuthenticated) {
    // 사용자 역할 체크
    const userRole = authStore.user?.role || 'user'
    const isAdmin = userRole === 'admin'

    // 관리자 권한 디버깅
    console.group('👑 관리자 권한 체크')
    console.log('userRole:', userRole)
    console.log('isAdmin:', isAdmin)
    console.log('authStore.user?.role:', authStore.user?.role)
    console.groupEnd()

    if (!isAdmin) {
      console.log('❌ 관리자 권한이 없는 사용자의 관리자 페이지 접근:', to.path)
      next({
        name: 'Home',
        query: { error: 'unauthorized' },
      })
      return
    }
  }

  // 정상적인 경우 계속 진행
  console.log('✅ 라우터 가드 통과')
  next()
})

// 전역 후처리 가드
router.afterEach((to, from) => {
  // 페이지 변경 완료 후 처리
  console.log(`페이지 이동 완료: ${from.path} → ${to.path}`)

  // Google Analytics 등 추적 코드 실행 위치
  // if (window.gtag) {
  //   window.gtag('config', 'GA_MEASUREMENT_ID', {
  //     page_path: to.path
  //   })
  // }
})

// 라우터 에러 핸들링
router.onError((error, to, from) => {
  console.error('라우터 에러 발생:', error)
  console.error('이동하려던 경로:', to.path)
  console.error('이전 경로:', from.path)

  // 에러 발생 시 홈페이지로 리디렉션
  if (to.path !== '/') {
    router.push('/')
  }
})

export default router

// 라우터 유틸리티 함수들
export const routerUtils = {
  // 현재 라우트가 특정 경로와 일치하는지 확인
  isCurrentRoute(routeName) {
    return router.currentRoute.value.name === routeName
  },

  // 현재 라우트가 특정 경로의 하위인지 확인
  isChildRoute(parentPath) {
    const currentPath = router.currentRoute.value.path
    return currentPath.startsWith(parentPath)
  },

  // 인증이 필요한 라우트인지 확인
  isProtectedRoute(path) {
    return PROTECTED_ROUTES.some((route) => path.startsWith(route))
  },

  // 브레드크럼 생성
  generateBreadcrumbs() {
    const route = router.currentRoute.value
    const pathArray = route.path.split('/').filter((segment) => segment)
    const breadcrumbs = []

    let currentPath = ''
    for (const segment of pathArray) {
      currentPath += `/${segment}`
      const matchedRoute = router.getRoutes().find((r) => r.path === currentPath)

      if (matchedRoute && matchedRoute.meta.title) {
        breadcrumbs.push({
          name: matchedRoute.meta.title,
          path: currentPath,
          active: currentPath === route.path,
        })
      }
    }

    return breadcrumbs
  },

  // 안전한 네비게이션 (에러 처리 포함)
  async safeNavigate(to, options = {}) {
    try {
      await router.push(to)
    } catch (error) {
      console.error('네비게이션 에러:', error)
      if (options.fallback) {
        await router.push(options.fallback)
      }
    }
  },
}
