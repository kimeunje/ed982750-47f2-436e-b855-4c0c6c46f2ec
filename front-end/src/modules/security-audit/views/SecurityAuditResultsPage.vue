<!-- SecurityAuditResultsPage.vue Template - 제외 설정 반영 버전 -->
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
          <p>보안 감사 결과를 확인하려면 로그인이 필요합니다.</p>
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
          <h1 class="page-title">보안 감사 결과 현황</h1>
        </div>

        <!-- 로딩 상태 -->
        <div v-if="loading" class="loading-container">
          <div class="loading-spinner"></div>
          <p>데이터를 불러오는 중...</p>
        </div>

        <!-- 에러 상태 -->
        <div v-else-if="error" class="error-container">
          <div class="error-icon">⚠️</div>
          <h3>데이터 로드 미흡</h3>
          <p>{{ error }}</p>
          <button @click="fetchData" class="retry-button">다시 시도</button>
        </div>

        <!-- 데이터 표시 -->
        <div v-else>
          <!-- 점검 유형 탭 -->
          <div class="section">
            <div class="tabs-container">
              <div class="tabs-header">
                <button
                  @click="activeTab = 'daily'"
                  class="tab-button"
                  :class="{ active: activeTab === 'daily' }"
                >
                  <svg width="20" height="20" fill="currentColor" viewBox="0 0 16 16">
                    <path
                      d="M8 3.5a.5.5 0 0 0-1 0V9a.5.5 0 0 0 .252.434l3.5 2a.5.5 0 0 0 .496-.868L8 8.71V3.5z"
                    />
                    <path
                      d="M8 16A8 8 0 1 0 8 0a8 8 0 0 0 0 16zm7-8A7 7 0 1 1 1 8a7 7 0 0 1 14 0z"
                    />
                  </svg>
                  정기 점검
                  <span class="tab-count">{{ stats.daily?.totalChecks || 0 }}개 항목</span>
                </button>

                <button
                  @click="activeTab = 'manual'"
                  class="tab-button"
                  :class="{ active: activeTab === 'manual' }"
                >
                  <svg width="20" height="20" fill="currentColor" viewBox="0 0 16 16">
                    <path
                      d="M9.405 1.05c-.413-1.4-2.397-1.4-2.81 0l-.1.34a1.464 1.464 0 0 1-2.105.872l-.31-.17c-1.283-.698-2.686.705-1.987 1.987l.169.311c.446.82.023 1.841-.872 2.105l-.34.1c-1.4.413-1.4 2.397 0 2.81l.34.1a1.464 1.464 0 0 1 .872 2.105l-.17.31c-.698 1.283.705 2.686 1.987 1.987l.311-.169a1.464 1.464 0 0 1 2.105.872l.1.34c.413 1.4 2.397 1.4 2.81 0l.1-.34a1.464 1.464 0 0 1 2.105-.872l.31.17c1.283.698 2.686-.705 1.987-1.987l-.169-.311a1.464 1.464 0 0 1 .872-2.105l.34-.1c1.4-.413 1.4-2.397 0-2.81l-.34-.1a1.464 1.464 0 0 1-.872-2.105l.17-.31c.698-1.283-.705-2.686-1.987-1.987l-.311.169a1.464 1.464 0 0 1-2.105-.872l-.1-.34zM8 10.93a2.929 2.929 0 1 1 0-5.86 2.929 2.929 0 0 1 0 5.858z"
                    />
                  </svg>
                  수시 점검
                  <span class="tab-count">{{ stats.manual?.totalChecks || 0 }}개 항목</span>
                </button>
              </div>
            </div>
          </div>

          <!-- 요약 통계 카드 (제외 항목 정보 추가) -->
          <div class="section">
            <h2 class="section-title">
              {{ getTabTitle() }} 요약
              <span v-if="activeTab !== 'all'" class="tab-indicator">{{ getTabSubtitle() }}</span>
            </h2>
            <div class="stats-grid">
              <StatsCard
                title="총 점검 항목"
                :value="currentStats.totalChecks"
                :subtitle="`전체 항목 (제외: ${currentStats.excludedItems || 0}개)`"
              />

              <!-- 활성 점검 항목 표시 -->
              <StatsCard
                title="활성 점검 항목"
                :value="getActiveChecks()"
                :subtitle="`실제 점검 대상 항목`"
                value-color="blue"
              />

              <StatsCard
                title="양호"
                :value="currentStats.completedChecks"
                :subtitle="`양호 항목 (${getPassRate()}%)`"
                value-color="green"
              />

              <StatsCard
                title="미흡"
                :value="currentStats.criticalIssues"
                :subtitle="`미흡 항목 (${getFailRate()}%)`"
                value-color="red"
              />
            </div>
          </div>

          <!-- 일별 감점 시각화 (페이지네이션 추가) -->
          <div class="section" v-if="currentDailyStats.length > 0">
            <div class="section-header">
              <h2 class="section-title">{{ getTabTitle() }} 일별 현황</h2>
              <div class="chart-controls">
                <div class="date-range-info">
                  {{ getCurrentDateRange() }}
                </div>
                <div class="pagination-controls">
                  <button 
                    @click="previousPage" 
                    :disabled="currentChartPage === 0"
                    class="nav-button prev"
                  >
                    ← 최신
                  </button>
                  <span class="page-info">
                    {{ currentChartPage + 1 }} / {{ totalChartPages }}
                  </span>
                  <button 
                    @click="nextPage" 
                    :disabled="currentChartPage >= totalChartPages - 1"
                    class="nav-button next"
                  >
                    과거 →
                  </button>
                </div>
              </div>
            </div>
            
            <div class="daily-stats-container">
              <!-- 차트 영역 -->
              <div class="chart-container">
                <div class="chart-area">
                  <div class="chart-bars">
                    <div
                      v-for="(day, index) in paginatedDailyStats"
                      :key="index"
                      class="chart-bar-group"
                    >
                      <div class="chart-bars-container">
                        <div
                          class="chart-bar passed"
                          :style="{ height: `${(day.passed / getMaxValue()) * 100}%` }"
                        ></div>
                        <div
                          class="chart-bar failed"
                          :style="{ height: `${(day.failed / getMaxValue()) * 100}%` }"
                        ></div>
                      </div>
                      <div class="chart-label">{{ formatChartDate(day.date) }}</div>
                      <div class="chart-penalty">-{{ day.penalty }}점</div>
                    </div>
                  </div>
                </div>

                <!-- 범례 -->
                <div class="chart-legend">
                  <div class="legend-item">
                    <div class="legend-color passed"></div>
                    <span>양호</span>
                  </div>
                  <div class="legend-item">
                    <div class="legend-color failed"></div>
                    <span>미흡</span>
                  </div>
                </div>
              </div>

              <!-- 일별 통계 테이블 (페이지네이션 적용) -->
              <div class="daily-stats-table">
                <table>
                  <thead>
                    <tr>
                      <th>날짜</th>
                      <th>양호</th>
                      <th>미흡</th>
                      <th>양호율</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(day, index) in paginatedDailyStats" :key="index">
                      <td>{{ day.date }}</td>
                      <td class="passed-count">{{ day.passed }}</td>
                      <td class="failed-count">{{ day.failed }}</td>
                      <td>{{ day.passRate }}%</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <!-- 데이터 없음 상태 (일별 통계) -->
          <div v-else class="section">
            <h2 class="section-title">{{ getTabTitle() }} 일별 현황</h2>
            <div class="no-data">
              <p>{{ getTabTitle() }} 검사 결과 데이터가 없습니다.</p>
            </div>
          </div>

          <!-- 항목별 상세 결과 테이블 개선 -->
          <div class="section">
            <h2 class="section-title">{{ getTabTitle() }} 항목별 검사 결과</h2>
            <div v-if="currentItemStats.length > 0" class="items-container">
              <!-- 테이블 헤더 -->
              <div class="items-header">
                <div class="header-cell">ID</div>
                <div class="header-cell">항목명</div>
                <div class="header-cell">카테고리</div>
                <div class="header-cell">점검 유형</div>
                <div class="header-cell">양호</div>
                <div class="header-cell">미흡</div>
                <div class="header-cell">양호율</div>
                <div class="header-cell">상세</div>
              </div>

              <div v-for="item in currentItemStats" :key="item.id" class="item-row-container">
                <!-- 기존 항목 정보 행 -->
                <div class="item-row" :class="{ expanded: selectedItemId === item.id, excluded: item.isExcluded }">
                  <div class="item-cell item-id">{{ item.id }}</div>
                  <div class="item-cell item-name">{{ item.name }}</div>
                  <div class="item-cell item-category">{{ item.category }}</div>
                  <div class="item-cell">
                    <span class="check-type-badge" :class="item.checkType">
                      {{ item.checkType === 'daily' ? '정기' : '수시' }}
                    </span>
                  </div>
                  <div class="item-cell passed-count">{{ item.passed }}</div>
                  <div class="item-cell failed-count">{{ item.failed }}</div>
                  <div class="item-cell">
                    <div class="progress-container">
                      <div class="progress-bar">
                        <div
                          class="progress-fill"
                          :style="{ width: `${item.passRate}%` }"
                          :class="getPenaltyClass(item.penalty)"
                        ></div>
                      </div>
                      <span class="progress-text">{{ item.passRate }}%</span>
                    </div>
                  </div>
                  <div class="item-cell">
                    <button
                      @click="toggleItemDetail(item.id)"
                      class="detail-button"
                      :class="{ active: selectedItemId === item.id }"
                    >
                      {{ selectedItemId === item.id ? '닫기' : '상세보기' }}
                    </button>
                  </div>
                </div>

                <!-- 개선된 상세보기 -->
                <div v-if="selectedItemId === item.id" class="item-detail-container">
                  <!-- 미흡 건 요약 -->
                  <div v-if="getFailedLogsForItem(item.id).length > 0" class="critical-summary">
                    <div class="summary-header">
                      <h4>🚨 미흡 건 요약</h4>
                      <span class="summary-count">{{ getFailedLogsForItem(item.id).length }}건</span>
                    </div>
                    <div class="summary-content">
                      <div class="summary-stats">
                        <span class="stat-item">
                          <strong>최근 미흡:</strong> 
                          {{ formatDate(getLatestFailedLog(item.id)?.checked_at) }}
                        </span>
                        <span class="stat-item">
                          <strong>미흡률:</strong> 
                          {{ Math.round((getFailedLogsForItem(item.id).length / getItemLogs(item.id).length) * 100) }}%
                        </span>
                      </div>
                    </div>
                  </div>

                  <div class="detail-header-inline">
                    <div class="detail-info">
                      <h3 class="detail-title">{{ item.name }} 상세 정보</h3>
                      <p class="detail-description">{{ item.description }}</p>
                      <div class="detail-meta">
                        <span class="meta-item">
                          <strong>점검 유형:</strong>
                          {{
                            item.checkType === 'daily'
                              ? '정기 점검 (매일 자동)'
                              : '수시 점검 (수동 실행)'
                          }}
                        </span>
                        <span class="meta-item">
                          <strong>카테고리:</strong> {{ item.category }}
                        </span>

                        <!-- 제외 설정 정보 -->
                        <span v-if="item.isExcluded" class="meta-item exclusion-info">
                          <strong>제외 설정:</strong> {{ item.excludeReason }}
                          <span class="exclusion-type"
                            >({{ getExclusionTypeText(item.exclusionType) }})</span
                          >
                        </span>
                      </div>
                    </div>
                  </div>

                  <!-- 필터 및 페이지네이션 컨트롤 -->
                  <div class="detail-controls">
                    <div class="filter-tabs">
                      <button 
                        @click="setDetailFilter(item.id, 'all')" 
                        class="filter-tab" 
                        :class="{ active: getDetailFilter(item.id) === 'all' }"
                      >
                        전체 ({{ getItemLogs(item.id).length }})
                      </button>
                      <button 
                        @click="setDetailFilter(item.id, 'failed')" 
                        class="filter-tab failed" 
                        :class="{ active: getDetailFilter(item.id) === 'failed' }"
                      >
                        미흡만 ({{ getFailedLogsForItem(item.id).length }})
                      </button>
                      <button 
                        @click="setDetailFilter(item.id, 'passed')" 
                        class="filter-tab passed" 
                        :class="{ active: getDetailFilter(item.id) === 'passed' }"
                      >
                        양호만 ({{ getPassedLogsForItem(item.id).length }})
                      </button>
                    </div>

                    <div class="pagination-info">
                      {{ getCurrentPageInfo(item.id) }}
                    </div>
                  </div>

                  <!-- 페이지네이션된 로그 테이블 -->
                  <div v-if="getPaginatedLogs(item.id).length > 0" class="logs-table-container-inline">
                    <table class="logs-table">
                      <thead>
                        <tr>
                          <th>검사 일시</th>
                          <th>결과</th>
                          <th v-if="activeTab !== 'manual'">실제 값</th>
                          <th>제외</th>
                          <th>메모</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr
                          v-for="log in getPaginatedLogs(item.id)"
                          :key="log.log_id"
                          :class="{ 
                            'excluded-row': log.is_excluded,
                            'failed-row': log.passed === 0 && !log.is_excluded,
                            'recent-failed': isRecentFailure(log)
                          }"
                        >
                          <td>
                            <div class="datetime-cell">
                              {{ formatDate(log.checked_at) }}
                              <span v-if="isRecentFailure(log)" class="recent-badge">최근</span>
                            </div>
                          </td>
                          <td>
                            <span class="result-badge" :class="log.passed === 1 ? 'passed' : 'failed'">
                              {{ log.passed === 1 ? '통과' : '실패' }}
                            </span>
                          </td>
                          <td v-if="activeTab !== 'manual'" class="actual-value">
                            {{ formatActualValue(log.actual_value) }}
                          </td>
                          <td>
                            <span v-if="log.is_excluded" class="exclusion-badge">제외</span>
                          </td>
                          <td class="notes">{{ log.notes }}</td>
                        </tr>
                      </tbody>
                    </table>

                    <!-- 페이지네이션 컨트롤 -->
                    <div class="detail-pagination">
                      <button 
                        @click="previousDetailPage(item.id)" 
                        :disabled="getDetailPage(item.id) === 0"
                        class="nav-button"
                      >
                        ← 이전
                      </button>
                      <span class="page-info">
                        {{ getDetailPage(item.id) + 1 }} / {{ getTotalDetailPages(item.id) }}
                      </span>
                      <button 
                        @click="nextDetailPage(item.id)" 
                        :disabled="getDetailPage(item.id) >= getTotalDetailPages(item.id) - 1"
                        class="nav-button"
                      >
                        다음 →
                      </button>
                    </div>
                  </div>
                  <div v-else class="no-data-inline">
                    <p>선택한 조건에 해당하는 데이터가 없습니다.</p>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="no-data">
              <p>{{ getTabTitle() }} 검사 결과 데이터가 없습니다.</p>
            </div>
          </div>
        </div>

        <!-- 페이지 네비게이션 -->
        <PageNavigation current-path="/security-audit/results" />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Sidebar from '@/components/Sidebar.vue'
import StatsCard from '@/components/StatsCard.vue'
import PageNavigation from '@/components/PageNavigation.vue'

// Pinia Store
const authStore = useAuthStore()

// 반응형 데이터
const loading = ref(false)
const error = ref(null)
const activeTab = ref('daily') // 'daily', 'manual', 'all'

// 통계 데이터 (제외 설정 정보 포함)
const stats = ref({
  daily: null,
  manual: null,
  all: null,
})

// 보안 점검 항목 데이터 (탭별)
const checklistItems = ref({
  daily: [],
  manual: [],
  all: [],
})

// 로그 데이터 (탭별, 제외 설정 정보 포함)
const auditLogs = ref({
  daily: [],
  manual: [],
  all: [],
})

// 선택된 항목 ID
const selectedItemId = ref(null)

// 시간별로 그룹화된 로그 (최근 7일) - 탭별
const dailyStats = ref({
  daily: [],
  manual: [],
  all: [],
})

// 항목별 양호/미흡 통계 - 탭별 (제외 설정 정보 포함)
const itemStats = ref({
  daily: [],
  manual: [],
  all: [],
})

// Sidebar ref
const sidebarRef = ref(null)

// 차트 페이지네이션 관련 상태
const currentChartPage = ref(0)
const chartItemsPerPage = 10

// 상세보기 페이지네이션 관련 상태
const detailPageSettings = ref({}) // { itemId: { page: 0, filter: 'failed' } }
const detailItemsPerPage = 5

// 계산된 속성
const isAuthenticated = computed(() => !!authStore.user)

const currentStats = computed(() => {
  return (
    stats.value[activeTab.value] || {
      totalChecks: 0,
      activeChecks: 0, // 실제 점검 대상 항목 수
      completedChecks: 0, // 양호 항목
      criticalIssues: 0, // 미흡 항목 (감점 대상)
      lastCheckedAt: '',
      totalPenalty: 0, // 총 감점
      excludedItems: 0, // 제외된 항목 수
    }
  )
})

const currentDailyStats = computed(() => {
  return dailyStats.value[activeTab.value] || []
})

const currentItemStats = computed(() => {
  const items = itemStats.value[activeTab.value] || []

  // item.id 순서대로 오름차순 정렬
  return items.sort((a, b) => {
    return a.id - b.id // 1, 2, 3, 4... 순서로 정렬
  })
})

// 차트 페이지네이션 계산된 속성들
const totalChartPages = computed(() => {
  return Math.ceil(currentDailyStats.value.length / chartItemsPerPage)
})

const paginatedDailyStats = computed(() => {
  const start = currentChartPage.value * chartItemsPerPage
  const end = start + chartItemsPerPage
  return currentDailyStats.value.slice(start, end)
})

// 통계 계산 함수들 (제외 항목 반영)
const getActiveChecks = () => {
  return (
    currentStats.value.activeChecks ||
    currentStats.value.totalChecks - (currentStats.value.excludedItems || 0)
  )
}

const getPassedCount = () => {
  return currentStats.value.completedChecks || 0
}

const getFailedCount = () => {
  return currentStats.value.criticalIssues || 0
}

const getPassRate = () => {
  const activeChecks = getActiveChecks()
  const passedCount = getPassedCount()
  if (activeChecks === 0) return 0
  return Math.round((passedCount / activeChecks) * 100)
}

const getFailRate = () => {
  const activeChecks = getActiveChecks()
  const failedCount = getFailedCount()
  if (activeChecks === 0) return 0
  return Math.round((failedCount / activeChecks) * 100)
}

const getTotalPenalty = () => {
  return (currentStats.value.totalPenalty || 0).toFixed(1)
}

const getMaxValue = () => {
  if (paginatedDailyStats.value.length === 0) return 1
  return Math.max(...paginatedDailyStats.value.map((day) => Math.max(day.passed, day.failed)))
}

// 차트 페이지네이션 메서드들
const getCurrentDateRange = () => {
  if (paginatedDailyStats.value.length === 0) return ''
  
  const firstDate = paginatedDailyStats.value[0].date
  const lastDate = paginatedDailyStats.value[paginatedDailyStats.value.length - 1].date
  
  if (firstDate === lastDate) {
    return firstDate
  }
  
  return `${firstDate} ~ ${lastDate}`
}

const previousPage = () => {
  if (currentChartPage.value > 0) {
    currentChartPage.value--
  }
}

const nextPage = () => {
  if (currentChartPage.value < totalChartPages.value - 1) {
    currentChartPage.value++
  }
}

// 상세보기 필터 및 페이지 관리
const initDetailSettings = (itemId) => {
  if (!detailPageSettings.value[itemId]) {
    detailPageSettings.value[itemId] = {
      page: 0,
      filter: 'failed' // 기본적으로 미흡 건부터 표시
    }
  }
}

const getDetailFilter = (itemId) => {
  initDetailSettings(itemId)
  return detailPageSettings.value[itemId].filter
}

const setDetailFilter = (itemId, filter) => {
  initDetailSettings(itemId)
  detailPageSettings.value[itemId].filter = filter
  detailPageSettings.value[itemId].page = 0 // 필터 변경시 첫 페이지로
}

const getDetailPage = (itemId) => {
  initDetailSettings(itemId)
  return detailPageSettings.value[itemId].page
}

// 항목별 로그 필터링 및 정렬
const getFilteredLogs = (itemId) => {
  const allLogs = getItemLogs(itemId)
  const filter = getDetailFilter(itemId)
  
  let filtered = []
  if (filter === 'failed') {
    filtered = allLogs.filter(log => log.passed === 0)
  } else if (filter === 'passed') {
    filtered = allLogs.filter(log => log.passed === 1)
  } else {
    filtered = [...allLogs]
  }
  
  // 미흡 건을 우선으로 정렬 (최신순)
  return filtered.sort((a, b) => {
    // 먼저 실패 여부로 정렬 (실패가 먼저)
    if (a.passed !== b.passed) {
      return a.passed - b.passed // 0(실패)이 1(성공)보다 먼저
    }
    // 같은 상태라면 최신순으로 정렬
    return new Date(b.checked_at) - new Date(a.checked_at)
  })
}

const getPaginatedLogs = (itemId) => {
  const filteredLogs = getFilteredLogs(itemId)
  const page = getDetailPage(itemId)
  const start = page * detailItemsPerPage
  const end = start + detailItemsPerPage
  return filteredLogs.slice(start, end)
}

const getTotalDetailPages = (itemId) => {
  const filteredLogs = getFilteredLogs(itemId)
  return Math.ceil(filteredLogs.length / detailItemsPerPage)
}

// 특정 타입 로그 조회
const getFailedLogsForItem = (itemId) => {
  return getItemLogs(itemId).filter(log => log.passed === 0)
}

const getPassedLogsForItem = (itemId) => {
  return getItemLogs(itemId).filter(log => log.passed === 1)
}

const getLatestFailedLog = (itemId) => {
  const failedLogs = getFailedLogsForItem(itemId)
  return failedLogs.sort((a, b) => new Date(b.checked_at) - new Date(a.checked_at))[0]
}

// 최근 실패 여부 체크 (7일 이내)
const isRecentFailure = (log) => {
  if (log.passed === 1) return false
  const logDate = new Date(log.checked_at)
  const sevenDaysAgo = new Date()
  sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7)
  return logDate > sevenDaysAgo
}

// 페이지네이션 메서드
const previousDetailPage = (itemId) => {
  initDetailSettings(itemId)
  if (detailPageSettings.value[itemId].page > 0) {
    detailPageSettings.value[itemId].page--
  }
}

const nextDetailPage = (itemId) => {
  initDetailSettings(itemId)
  const totalPages = getTotalDetailPages(itemId)
  if (detailPageSettings.value[itemId].page < totalPages - 1) {
    detailPageSettings.value[itemId].page++
  }
}

// 페이지 정보 표시
const getCurrentPageInfo = (itemId) => {
  const filteredLogs = getFilteredLogs(itemId)
  const page = getDetailPage(itemId)
  const start = page * detailItemsPerPage + 1
  const end = Math.min((page + 1) * detailItemsPerPage, filteredLogs.length)
  
  if (filteredLogs.length === 0) return '데이터 없음'
  
  return `${start}-${end} / ${filteredLogs.length}건`
}

// 탭 관련 메서드
const getTabTitle = () => {
  switch (activeTab.value) {
    case 'daily':
      return '정기 점검'
    case 'manual':
      return '수시 점검'
    case 'all':
      return '전체'
    default:
      return '정기 점검'
  }
}

const getTabSubtitle = () => {
  switch (activeTab.value) {
    case 'daily':
      return '매일 자동 실행'
    case 'manual':
      return '관리자 수동 실행'
    default:
      return ''
  }
}

// 메서드
const fetchData = async () => {
  if (!authStore.user) return

  loading.value = true
  error.value = null

  try {
    // 모든 탭의 데이터를 병렬로 가져오기
    const [
      dailyLogsResponse,
      manualLogsResponse,
      allLogsResponse,
      dailyChecklistResponse,
      manualChecklistResponse,
      allChecklistResponse,
    ] = await Promise.all([
      fetch('/api/security-audit/logs?type=daily', { credentials: 'include' }),
      fetch('/api/security-audit/logs?type=manual', { credentials: 'include' }),
      fetch('/api/security-audit/logs', { credentials: 'include' }),
      fetch('/api/security-audit/checklist-items?type=daily', { credentials: 'include' }),
      fetch('/api/security-audit/checklist-items?type=manual', { credentials: 'include' }),
      fetch('/api/security-audit/checklist-items', { credentials: 'include' }),
    ])

    // 응답 확인
    const responses = [
      dailyLogsResponse,
      manualLogsResponse,
      allLogsResponse,
      dailyChecklistResponse,
      manualChecklistResponse,
      allChecklistResponse,
    ]
    for (const response of responses) {
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`)
      }
    }

    // 데이터 파싱
    const [
      dailyLogsData,
      manualLogsData,
      allLogsData,
      dailyChecklistData,
      manualChecklistData,
      allChecklistData,
    ] = await Promise.all(responses.map((res) => res.json()))

    // 로그 데이터 설정 (제외 설정 정보 포함)
    auditLogs.value = {
      daily: dailyLogsData,
      manual: manualLogsData,
      all: allLogsData,
    }

    // 체크리스트 데이터 변환 및 설정
    checklistItems.value = {
      daily: formatChecklistItems(dailyChecklistData),
      manual: formatChecklistItems(manualChecklistData),
      all: formatChecklistItems(allChecklistData),
    }

    // 각 탭별 통계 계산 (제외 설정 반영)
    calculateAllStats()
    prepareAllDailyStats()
    prepareAllItemStats()

    console.log('모든 데이터 로드 완료')
  } catch (err) {
    console.error('Failed to fetch data:', err)
    error.value = '데이터를 불러오는 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.'
  } finally {
    loading.value = false
  }
}

const formatChecklistItems = (checklistData) => {
  return checklistData.map((item) => ({
    id: item.item_id,
    name: item.name || item.item_name,
    category: item.category,
    description: item.description,
    checkType: item.check_type,
    checkFrequency: item.check_frequency,
    penaltyWeight: item.penalty_weight || 0.5, // 감점 가중치
  }))
}

// 통계 계산 (제외 설정 반영)
const calculateAllStats = () => {
  ;['daily', 'manual', 'all'].forEach((tabType) => {
    const logs = auditLogs.value[tabType]
    const totalChecks = logs.length

    // 제외 설정을 반영한 양호/미흡 계산
    const passedChecks = logs.filter((log) => log.passed === 1 && !log.is_excluded).length
    const failedChecks = logs.filter((log) => log.passed === 0 && !log.is_excluded).length
    const excludedChecks = logs.filter((log) => log.is_excluded).length
    const activeChecks = passedChecks + failedChecks // 제외되지 않은 실제 점검 항목

    // 가장 최근 검사 날짜
    const sortedLogs = [...logs].sort((a, b) => new Date(b.checked_at) - new Date(a.checked_at))
    const lastCheckedAt = sortedLogs.length > 0 ? sortedLogs[0].checked_at : ''

    // 감점 계산 (제외된 항목은 감점에서 제외)
    let totalPenalty = 0
    logs.forEach((log) => {
      if (log.passed === 0 && !log.is_excluded) {
        totalPenalty += log.penalty_applied || log.penalty_weight || 0.5
      }
    })

    stats.value[tabType] = {
      totalChecks,
      activeChecks, // 실제 점검 대상 항목 수
      completedChecks: passedChecks,
      criticalIssues: failedChecks, // 제외된 항목 제외
      lastCheckedAt,
      totalPenalty: totalPenalty,
      excludedItems: excludedChecks, // 제외된 항목 수
    }
  })
}

const prepareAllDailyStats = () => {
  ;['daily', 'manual', 'all'].forEach((tabType) => {
    const logs = auditLogs.value[tabType]

    // 날짜별로 로그를 그룹화
    const groupedByDate = {}

    logs.forEach((log) => {
      const dateOnly = log.checked_at.split(' ')[0]
      if (!groupedByDate[dateOnly]) {
        groupedByDate[dateOnly] = {
          date: dateOnly,
          passed: 0,
          failed: 0,
          penalty: 0, // 감점 추가
        }
      }

      if (log.passed === 1 && !log.is_excluded) {
        groupedByDate[dateOnly].passed += 1
      } else if (log.passed === 0 && !log.is_excluded) {
        // 제외된 항목은 미흡로 카운트하지 않음
        groupedByDate[dateOnly].failed += 1
        // 감점 누적 (제외된 항목은 감점에서 제외)
        groupedByDate[dateOnly].penalty += log.penalty_applied || log.penalty_weight || 0.5
      }
    })

    // 날짜순으로 정렬 (내림차순)
    const sortedDates = Object.values(groupedByDate).sort(
      (a, b) => new Date(b.date) - new Date(a.date),
    )

    // 차트에서 사용하기 쉽게 데이터 구조 조정
    const chartData = sortedDates.map((day) => {
      const total = day.passed + day.failed
      const passRate = total > 0 ? Math.round((day.passed / total) * 100) : 0

      return {
        ...day,
        passRate,
        total,
        penalty: Math.round(day.penalty * 10) / 10, // 감점 반올림
      }
    })

    dailyStats.value[tabType] = chartData
  })
}

const prepareAllItemStats = () => {
  ;['daily', 'manual', 'all'].forEach((tabType) => {
    const items = checklistItems.value[tabType]
    const logs = auditLogs.value[tabType]

    const itemStatsData = items.map((item) => {
      const itemLogs = logs.filter((log) => log.item_id === item.id)
      const passedCount = itemLogs.filter((log) => log.passed === 1).length
      const failedCount = itemLogs.filter((log) => log.passed === 0).length
      const totalCount = passedCount + failedCount
      const passRate = totalCount > 0 ? (passedCount / totalCount) * 100 : 0

      // 제외 설정 정보 확인 (최근 로그 기준)
      const latestLog = itemLogs.sort((a, b) => new Date(b.checked_at) - new Date(a.checked_at))[0]
      const isExcluded = latestLog ? latestLog.is_excluded : false
      const excludeReason = latestLog ? latestLog.exclude_reason : null
      const exclusionType = latestLog ? latestLog.exception_type : null

      // 감점 계산 (제외된 항목은 감점에서 제외)
      const actualFailedCount = itemLogs.filter(
        (log) => log.passed === 0 && !log.is_excluded,
      ).length
      const penalty = actualFailedCount * (item.penaltyWeight || 0.5)

      return {
        id: item.id,
        name: item.name,
        category: item.category,
        description: item.description,
        checkType: item.checkType,
        penaltyWeight: item.penaltyWeight,
        total: totalCount,
        passed: passedCount,
        failed: failedCount,
        passRate: Math.round(passRate),
        penalty: Math.round(penalty * 10) / 10,
        isExcluded: isExcluded, // 제외 설정 여부
        excludeReason: excludeReason, // 제외 사유
        exclusionType: exclusionType, // 제외 유형
      }
    })

    itemStats.value[tabType] = itemStatsData
  })
}

const toggleItemDetail = (itemId) => {
  if (selectedItemId.value === itemId) {
    selectedItemId.value = null
  } else {
    selectedItemId.value = itemId
    initDetailSettings(itemId)
  }
}

const getItemLogs = (itemId) => {
  const logs = auditLogs.value[activeTab.value]
  return logs
    .filter((log) => log.item_id === itemId)
    .sort((a, b) => new Date(b.checked_at) - new Date(a.checked_at))
}

// 진행률 클래스를 감점 클래스로 변경
const getPenaltyClass = (penalty) => {
  if (penalty === 0) return 'no-penalty'
  if (penalty <= 1.0) return 'low-penalty'
  if (penalty <= 2.5) return 'medium-penalty'
  return 'high-penalty'
}

const formatDate = (dateStr) => {
  if (!dateStr) return '데이터 없음'

  const date = new Date(dateStr)
  return date.toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const formatChartDate = (dateStr) => {
  if (!dateStr) return ''

  const date = new Date(dateStr)
  return `${date.getMonth() + 1}/${date.getDate()}`
}

// formatActualValue 함수 수정
const formatActualValue = (actualValue) => {
  // 수시 점검인 경우 실제 값을 표시하지 않음
  if (activeTab.value === 'manual') {
    return '-'
  }

  // 기존 로직
  if (!actualValue) return '-'

  if (typeof actualValue === 'object') {
    try {
      const obj = typeof actualValue === 'string' ? JSON.parse(actualValue) : actualValue

      // 객체에서 주요 정보만 추출
      if (obj.status) return obj.status
      if (obj.result) return obj.result
      if (obj.value !== undefined) return obj.value
      if (obj.count !== undefined) return obj.count
      if (obj.version) return obj.version

      return '확인됨'
    } catch {
      return actualValue.toString()
    }
  }

  return actualValue.toString()
}

// 제외 유형 텍스트 변환
const getExclusionTypeText = (exclusionType) => {
  switch (exclusionType) {
    case 'user':
      return '사용자별 제외'
    case 'user_extended':
      return '사용자별 확장 제외'
    case 'department':
      return '부서별 제외'
    case 'department_extended':
      return '부서별 확장 제외'
    default:
      return '제외 설정'
  }
}

// 탭 변경시 페이지 초기화
watch(activeTab, () => {
  currentChartPage.value = 0
  selectedItemId.value = null
})

// 라이프사이클 훅
onMounted(() => {
  if (authStore.user) {
    fetchData()
  }
})

// 인증 상태 변경 감지
watch(
  () => authStore.user,
  (newUser) => {
    if (newUser) {
      fetchData()
    } else {
      // 로그아웃 시 데이터 초기화
      stats.value = {
        daily: null,
        manual: null,
        all: null,
      }
      checklistItems.value = {
        daily: [],
        manual: [],
        all: [],
      }
      auditLogs.value = {
        daily: [],
        manual: [],
        all: [],
      }
      dailyStats.value = {
        daily: [],
        manual: [],
        all: [],
      }
      itemStats.value = {
        daily: [],
        manual: [],
        all: [],
      }
      selectedItemId.value = null
      currentChartPage.value = 0
      detailPageSettings.value = {}
    }
  },
)
</script>

<!-- CSS는 외부 파일에서 import -->
<style scoped>
@import '../styles/SecurityAuditResultsPage.css';
</style>
