<!-- SecurityAuditPage.vue - KPI 감점 시스템으로 수정 -->
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
      <div v-if="!authStore.user" class="not-authenticated">
        <div class="auth-warning">
          <div class="warning-icon">
            <svg width="48" height="48" fill="currentColor" viewBox="0 0 16 16">
              <path
                d="M8.982 1.566a1.13 1.13 0 0 0-1.96 0L.165 13.233c-.457.778.091 1.767.98 1.767h13.713c.889 0 1.438-.99.98-1.767L8.982 1.566zM8 5c.535 0 .954.462.9.995l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 5.995A.905.905 0 0 1 8 5zm.002 6a1 1 0 1 1 0 2 1 1 0 0 1 0-2z"
              />
            </svg>
          </div>
          <h2>인증이 필요합니다</h2>
          <p>정보보안 감사 시스템에 접근하려면 로그인이 필요합니다.</p>
          <div class="auth-actions">
            <RouterLink to="/login" class="login-button">
              <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                <path
                  fill-rule="evenodd"
                  d="M6 12.5a.5.5 0 0 0 .5.5h8a.5.5 0 0 0 .5-.5v-9a.5.5 0 0 0-.5-.5h-8a.5.5 0 0 0-.5.5v2a.5.5 0 0 1-1 0v-2A1.5 1.5 0 0 1 6.5 2h8A1.5 1.5 0 0 1 16 3.5v9a1.5 1.5 0 0 1-1.5 1.5h-8A1.5 1.5 0 0 1 5 12.5v-2a.5.5 0 0 1 1 0v2z"
                />
                <path
                  fill-rule="evenodd"
                  d="M.146 8.354a.5.5 0 0 1 0-.708l3-3a.5.5 0 1 1 .708.708L1.707 7.5H10.5a.5.5 0 0 1 0 1H1.707l2.147 2.146a.5.5 0 0 1-.708.708l-3-3z"
                />
              </svg>
              로그인하기
            </RouterLink>
          </div>
        </div>
      </div>

      <!-- 인증된 사용자용 콘텐츠 -->
      <div v-else>
        <div class="page-header">
          <h1 class="page-title">정보보안 감사 현황</h1>
        </div>

        <!-- 로딩 상태 -->
        <div v-if="loading" class="loading-container">
          <div class="loading-spinner"></div>
          <p>데이터를 불러오는 중...</p>
        </div>

        <!-- KPI 감점 상태 대시보드 -->
        <!-- 수정: 점검 상태 -> KPI 감점 상태 -->
        <div class="section" v-if="dashboardStats">
          <div class="dashboard-grid">
            <!-- 정기 점검 카드 -->
            <div class="dashboard-card daily-check">
              <div class="card-header">
                <div class="card-icon daily">
                  <svg width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
                    <path
                      d="M8 3.5a.5.5 0 0 0-1 0V9a.5.5 0 0 0 .252.434l3.5 2a.5.5 0 0 0 .496-.868L8 8.71V3.5z"
                    />
                    <path
                      d="M8 16A8 8 0 1 0 8 0a8 8 0 0 0 0 16zm7-8A7 7 0 1 1 1 8a7 7 0 0 1 14 0z"
                    />
                  </svg>
                </div>
                <h3>정기 점검</h3>
                <span class="card-frequency">매일 자동 실행</span>
              </div>
              <div class="card-stats">
                <div class="stat-row">
                  <span class="stat-label">전체 항목</span>
                  <span class="stat-value">{{ dashboardStats.daily.totalChecks }}</span>
                </div>
                <div class="stat-row">
                  <span class="stat-label">양호</span>
                  <span class="stat-value success">{{ dashboardStats.daily.completedChecks }}</span>
                </div>
                <div class="stat-row">
                  <span class="stat-label">미흡</span>
                  <span class="stat-value danger">{{ dashboardStats.daily.criticalIssues }}</span>
                </div>

                <div class="stat-row">
                  <span class="stat-label">최근 점검</span>
                  <span class="stat-value">{{
                    formatDate(dashboardStats.daily.lastAuditDate)
                  }}</span>
                </div>
              </div>
              <!-- 수정: 진행률 바를 감점 표시로 변경 -->
              <div class="card-progress">
                <div class="penalty-display">
                  <span class="penalty-label">미흡 건수:</span>
                  <span class="penalty-value">{{ dashboardStats.daily.criticalIssues }}점</span>
                </div>
              </div>
            </div>

            <!-- 수시 점검 카드 -->
            <div class="dashboard-card manual-check">
              <div class="card-header">
                <div class="card-icon manual">
                  <svg width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
                    <path
                      d="M9.405 1.05c-.413-1.4-2.397-1.4-2.81 0l-.1.34a1.464 1.464 0 0 1-2.105.872l-.31-.17c-1.283-.698-2.686.705-1.987 1.987l.169.311c.446.82.023 1.841-.872 2.105l-.34.1c-1.4.413-1.4 2.397 0 2.81l.34.1a1.464 1.464 0 0 1 .872 2.105l-.17.31c-.698 1.283.705 2.686 1.987 1.987l.311-.169a1.464 1.464 0 0 1 2.105.872l.1.34c.413 1.4 2.397 1.4 2.81 0l.1-.34a1.464 1.464 0 0 1 2.105-.872l.31.17c1.283.698 2.686-.705 1.987-1.987l-.169-.311a1.464 1.464 0 0 1 .872-2.105l.34-.1c1.4-.413 1.4-2.397 0-2.81l-.34-.1a1.464 1.464 0 0 1-.872-2.105l.17-.31c.698-1.283-.705-2.686-1.987-1.987l-.311.169a1.464 1.464 0 0 1-2.105-.872l-.1-.34zM8 10.93a2.929 2.929 0 1 1 0-5.86 2.929 2.929 0 0 1 0 5.858z"
                    />
                  </svg>
                </div>
                <h3>수시 점검</h3>
                <span class="card-frequency">관리자 수동 실행</span>
              </div>
              <div class="card-stats">
                <div class="stat-row">
                  <span class="stat-label">전체 항목</span>
                  <span class="stat-value">{{ dashboardStats.manual.totalChecks }}</span>
                </div>
                <div class="stat-row">
                  <span class="stat-label">양호</span>
                  <span class="stat-value success">{{
                    dashboardStats.manual.completedChecks
                  }}</span>
                </div>
                <div class="stat-row">
                  <span class="stat-label">미흡</span>
                  <span class="stat-value danger">{{ dashboardStats.manual.criticalIssues }}</span>
                </div>

                <div class="stat-row">
                  <span class="stat-label">최근 점검</span>
                  <span class="stat-value">{{
                    formatDate(dashboardStats.manual.lastAuditDate)
                  }}</span>
                </div>
              </div>
              <!-- 수정: 진행률 바를 감점 표시로 변경 -->
              <div class="card-progress">
                <div class="penalty-display">
                  <span class="penalty-label">미흡 건수:</span>
                  <span class="penalty-value">{{ dashboardStats.manual.criticalIssues }}건</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 총 감점 요약 -->
        <!-- 수정: 새로운 섹션 추가 -->
        <!-- <div class="section" v-if="dashboardStats">
          <div class="total-penalty-summary">
            <h2 class="section-title">감사 항목 총 감점</h2>
            <div class="total-penalty-card">
              <div class="penalty-icon">⚠️</div>
              <div class="penalty-content">
                <div class="penalty-number">-{{ getTotalAuditPenalty() }}점</div>
                <div class="penalty-description">
                  정기점검 {{ getDailyPenalty() }}점 + 수시점검 {{ getManualPenalty() }}점
                </div>
              </div>
              <div class="penalty-status" :class="getPenaltyStatusClass()">
                {{ getPenaltyStatusText() }}
              </div>
            </div>
          </div>
        </div> -->

        <!-- 주요 기능 소개 -->
        <div class="section">
          <h2 class="section-title">주요 기능</h2>
          <div class="features-grid">
            <div class="feature-card">
              <div class="feature-icon results">
                <svg width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
                  <path
                    d="M1.5 1.5A.5.5 0 0 1 2 1h12a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-.128.334L10 8.692V13.5a.5.5 0 0 1-.342.474l-3 1A.5.5 0 0 1 6 14.5V8.692L1.628 3.834A.5.5 0 0 1 1.5 3.5v-2z"
                  />
                </svg>
              </div>
              <div class="feature-content">
                <h3>검사결과</h3>
                <p>실시간 보안 감사 결과와 감점 현황을 확인하고 분석할 수 있습니다.</p>
                <!-- 수정 -->
                <RouterLink to="/security-audit/results" class="feature-link">
                  결과 보기
                  <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
                    <path
                      fill-rule="evenodd"
                      d="M4.646 1.646a.5.5 0 0 1 .708 0l6 6a.5.5 0 0 1 0 .708l-6 6a.5.5 0 0 1-.708-.708L10.293 8 4.646 2.354a.5.5 0 0 1 0-.708z"
                    />
                  </svg>
                </RouterLink>
              </div>
            </div>

            <div class="feature-card">
              <div class="feature-icon solutions">
                <svg width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
                  <path
                    d="M8 4.754a3.246 3.246 0 1 0 0 6.492 3.246 3.246 0 0 0 0-6.492zM5.754 8a2.246 2.246 0 1 1 4.492 0 2.246 2.246 0 0 1-4.492 0z"
                  />
                  <path
                    d="M9.796 1.343c-.527-1.79-3.065-1.79-3.592 0l-.094.319a.873.873 0 0 1-1.255.52l-.292-.16c-1.64-.892-3.433.902-2.54 2.541l.159.292a.873.873 0 0 1-.52 1.255l-.319.094c-1.79.527-1.79 3.065 0 3.592l.319.094a.873.873 0 0 1 .52 1.255l-.16.292c-.892 1.64.901 3.434 2.541 2.54l.292-.159a.873.873 0 0 1 1.255.52l.094.319c.527 1.79 3.065 1.79 3.592 0l.094-.319a.873.873 0 0 1 1.255-.52l.292.16c1.64.893 3.434-.902 2.54-2.541l-.159-.292a.873.873 0 0 1 .52-1.255l.319-.094c1.79-.527 1.79-3.065 0-3.592l-.319-.094a.873.873 0 0 1-.52-1.255l.16-.292c.893-1.64-.902-3.433-2.541-2.54l-.292.159a.873.873 0 0 1-1.255-.52l-.094-.319z"
                  />
                </svg>
              </div>
              <div class="feature-content">
                <h3>조치방법</h3>
                <p>보안 문제에 대한 상세한 해결 방법과 감점 해소 가이드를 제공합니다.</p>
                <!-- 수정 -->
                <RouterLink to="/security-audit/solutions" class="feature-link">
                  조치방법 보기
                  <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
                    <path
                      fill-rule="evenodd"
                      d="M4.646 1.646a.5.5 0 0 1 .708 0l6 6a.5.5 0 0 1 0 .708l-6 6a.5.5 0 0 1-.708-.708L10.293 8 4.646 2.354a.5.5 0 0 1 0-.708z"
                    />
                  </svg>
                </RouterLink>
              </div>
            </div>
          </div>
        </div>

        <!-- 수시 점검 모달 -->
        <ManualCheckModal
          v-if="showManualCheckModal"
          @close="showManualCheckModal = false"
          @check-completed="handleManualCheckCompleted"
        />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Sidebar from '@/components/Sidebar.vue'
import ManualCheckModal from '@/modules/security-audit/components/modal/ManualCheckModal.vue'

// Pinia Store
const authStore = useAuthStore()

// 반응형 데이터
const dashboardStats = ref(null)
const loading = ref(false)
const showManualCheckModal = ref(false)

// Sidebar ref
const sidebarRef = ref(null)

// 계산된 속성
const isAuthenticated = computed(() => !!authStore.user)

// 수정: 감점 계산 함수들 (통과율 제거)
const getDailyPenalty = () => {
  if (!dashboardStats.value?.daily) return 0
  const stats = dashboardStats.value.daily
  // 미흡 수 × 0.5점
  return ((stats.criticalIssues || 0) * 0.5).toFixed(1)
}

const getManualPenalty = () => {
  if (!dashboardStats.value?.manual) return 0
  const stats = dashboardStats.value.manual
  // 미흡 수 × 0.5점
  return ((stats.criticalIssues || 0) * 0.5).toFixed(1)
}

// 수정: 총 감점 계산
const getTotalAuditPenalty = () => {
  const dailyPenalty = parseFloat(getDailyPenalty())
  const manualPenalty = parseFloat(getManualPenalty())
  return (dailyPenalty + manualPenalty).toFixed(1)
}

// 수정: 감점 상태 클래스
const getPenaltyStatusClass = () => {
  const totalPenalty = parseFloat(getTotalAuditPenalty())
  if (totalPenalty === 0) return 'no-penalty'
  if (totalPenalty <= 1.0) return 'low-penalty'
  if (totalPenalty <= 2.5) return 'medium-penalty'
  return 'high-penalty'
}

// 수정: 감점 상태 텍스트
const getPenaltyStatusText = () => {
  const totalPenalty = parseFloat(getTotalAuditPenalty())
  if (totalPenalty === 0) return '우수'
  if (totalPenalty <= 1.0) return '양호'
  if (totalPenalty <= 2.5) return '주의'
  return '개선필요'
}

// 메서드
const fetchDashboardStats = async () => {
  if (!authStore.user) return

  loading.value = true
  try {
    const response = await fetch('/api/security-audit/dashboard-stats', {
      credentials: 'include',
    })

    if (response.ok) {
      const data = await response.json()
      dashboardStats.value = data
    } else {
      console.error('대시보드 데이터 로드 실패:', response.status)
    }
  } catch (error) {
    console.error('대시보드 데이터 로드 실패:', error)
  } finally {
    loading.value = false
  }
}

const handleManualCheckCompleted = () => {
  // 수시 점검 완료 후 데이터 새로고침
  fetchDashboardStats()
}

const formatDate = (dateStr) => {
  if (!dateStr) return '아직 없음'

  const date = new Date(dateStr)
  return date.toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

// 라이프사이클 훅
onMounted(() => {
  if (authStore.user) {
    fetchDashboardStats()
  }
})
</script>
<!-- CSS는 외부 파일에서 import -->
<style scoped>
@import '../styles/SecurityAuditPage.css';
</style>
