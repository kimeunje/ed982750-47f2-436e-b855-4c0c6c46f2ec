<!-- views/SecurityEducationPage.vue -->
<template>
  <main>
    <div class="education-page">
      <!-- 연도 선택기 -->
      <div class="page-header">
        <h1 class="page-title">정보보호 교육 현황</h1>
        <div class="year-selector">
          <label for="year">연도:</label>
          <select id="year" v-model="selectedYear" @change="fetchEducationStatus">
            <option v-for="year in availableYears" :key="year" :value="year">{{ year }}년</option>
          </select>
        </div>
      </div>

      <!-- 로딩 상태 -->
      <div v-if="loading" class="loading-container">
        <div class="loading-spinner"></div>
        <p>교육 현황을 불러오는 중...</p>
      </div>

      <!-- 에러 상태 -->
      <div v-else-if="error" class="error-container">
        <div class="error-icon">⚠️</div>
        <h3>데이터 로드 실패</h3>
        <p>{{ error }}</p>
        <button @click="fetchEducationStatus" class="retry-button">다시 시도</button>
      </div>

      <!-- 빈 데이터 -->
      <div v-else-if="isEmptyData" class="error-container">
        <div class="no-data-icon">📚</div>
        <h3>{{ selectedYear }}년 교육 데이터 없음</h3>
        <p>해당 연도에 등록된 교육 과정이 없습니다.</p>
        <div class="no-data-actions">
          <button @click="fetchEducationStatus" class="retry-button">다시 조회</button>
        </div>
      </div>

      <!-- 교육 현황 데이터 -->
      <div v-else-if="educationData" class="education-content">

        <!-- 교육 상태 대시보드 -->
        <div class="section">
          <div class="dashboard-grid">
            <div class="dashboard-card education-check" :class="getEducationCardClass()">
              <div class="card-header">
                <div class="card-icon education" :class="getEducationIconClass()">
                  <svg width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M8.211 2.047a.5.5 0 0 0-.422 0l-7.5 3.5a.5.5 0 0 0 .025.917l7.5 3a.5.5 0 0 0 .372 0L14.5 7.14V13a1 1 0 0 0-1 1v2h3v-2a1 1 0 0 0-1-1V6.739l.686-.275a.5.5 0 0 0 .025-.917l-7.5-3.5ZM8 8.46 1.758 5.965 8 3.052l6.242 2.913L8 8.46Z" />
                    <path d="M4.176 9.032a.5.5 0 0 0-.656.327l-.5 1.7a.5.5 0 0 0 .294.605l4.5 1.8a.5.5 0 0 0 .372 0l4.5-1.8a.5.5 0 0 0 .294-.605l-.5-1.7a.5.5 0 0 0-.656-.327L8 10.466 4.176 9.032Z" />
                  </svg>
                </div>
                <h3>정보보호 교육</h3>
                <span class="card-frequency">{{ selectedYear }}년 온/오프라인 교육</span>
              </div>

              <div class="card-stats">
                <div class="stat-row">
                  <span class="stat-label">총 과정수</span>
                  <span class="stat-value">{{ educationData.summary.total_courses }}</span>
                </div>
                <div class="stat-row">
                  <span class="stat-label">수료완료</span>
                  <span class="stat-value success">{{ educationData.summary.completed }}</span>
                </div>
                <div class="stat-row">
                  <span class="stat-label">미수료</span>
                  <span class="stat-value danger">{{ educationData.summary.incomplete }}</span>
                </div>
              </div>

              <div class="card-progress">
                <div class="progress-bar">
                  <div
                    class="progress-fill education"
                    :style="{ width: `${educationData.summary.completion_rate}%` }"
                    :class="getProgressClass(educationData.summary.completion_rate)"
                  ></div>
                </div>
                <span
                  class="progress-text"
                  :class="educationData.summary.completion_rate >= 100 ? 'text-excellent' : 'text-poor'"
                >수료율 {{ educationData.summary.completion_rate }}%</span>
              </div>

              <div v-if="educationData.summary.excluded_count > 0" class="card-notice">
                <div class="notice-icon">ℹ️</div>
                <span>{{ educationData.summary.excluded_count }}건 점수 제외</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 온라인/오프라인별 상세 현황 -->
        <div class="section">
          <h2 class="section-title">온라인/오프라인별 교육 현황</h2>
          <div class="periods-grid">
            <div
              v-for="education in educationData.education_status"
              :key="education.course_name || education.type"
              class="period-card"
              :class="getPeriodCardClass(education)"
            >
              <!-- 카드 헤더: 기간명 + 상태 뱃지 -->
              <div class="period-header">
                <h3>{{ education.period_name || education.course_name || education.type_name }}</h3>
                <div class="status-badge" :class="getStatusBadgeClass(education)">
                  {{ getStatusText(education) }}
                </div>
              </div>

              <!-- 서브텍스트: 일정 -->
              <div class="period-sub">
                <span v-if="education.start_date && education.end_date">
                  {{ formatDate(education.start_date) }} ~ {{ formatDate(education.end_date) }}
                </span>
                <span v-else-if="education.education_date">
                  {{ formatDate(education.education_date) }}
                </span>
              </div>

              <!-- 통계 인라인 -->
              <div class="period-stats">
                <div class="period-stat-item">
                  <span class="period-stat-num success">{{ education.completed_count || education.completed_courses || 0 }}</span>
                  <span class="period-stat-label">수료</span>
                </div>
                <span class="period-stat-sep">/</span>
                <div class="period-stat-item">
                  <span class="period-stat-num danger">{{ education.incomplete_count || education.incomplete_courses || 0 }}</span>
                  <span class="period-stat-label">미수료</span>
                </div>
                <span class="period-stat-sep">/</span>
                <div class="period-stat-item">
                  <span class="period-stat-num">{{ education.total_courses || 0 }}</span>
                  <span class="period-stat-label">총 과정</span>
                </div>
              </div>

              <!-- 프로그레스 바 -->
              <div class="period-progress">
                <div class="period-progress-bar">
                  <div
                    class="period-progress-fill"
                    :class="getProgressClass(education.completion_rate || 0)"
                    :style="{ width: `${education.completion_rate || 0}%` }"
                  ></div>
                </div>
                <span
                  class="period-progress-text"
                  :class="(education.completion_rate || 0) >= 100 ? 'text-excellent' : 'text-poor'"
                >{{ education.completion_rate || 0 }}%</span>
              </div>

              <!-- 하단 알림 메시지 -->
              <div class="period-message" :class="getIndividualNoticeClass(education)">
                {{ getIndividualNoticeMessage(education) }}
              </div>
            </div>
          </div>
        </div>

        <!-- 교육 안내 -->
        <div class="section">
          <h2 class="section-title">정보보호 교육 안내</h2>
          <div class="info-grid">
            <div class="info-card">
              <div class="info-icon">💻</div>
              <h3>온라인 교육</h3>
              <ul>
                <li>온라인 수강 형태(상시)</li>
                <li>필수 수료 과정</li>
              </ul>
            </div>
            <div class="info-card">
              <div class="info-icon">🏢</div>
              <h3>오프라인 교육</h3>
              <ul>
                <li>집합 교육 형태</li>
                <li>필수 참석 과정</li>
              </ul>
            </div>
            <div class="info-card">
              <div class="info-icon">🎯</div>
              <h3>평가 기준</h3>
              <ul>
                <li>수료: 100% 완료</li>
                <li>미수료: 100% 외 모든 상태</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

// 반응형 데이터
const loading = ref(false)
const error = ref(null)
const educationData = ref(null)
const selectedYear = ref(new Date().getFullYear())

// 연도 목록
const availableYears = computed(() => {
  const currentYear = new Date().getFullYear()
  return [currentYear - 1, currentYear, currentYear + 1]
})

// 빈 데이터 여부
const isEmptyData = computed(() => {
  return (
    educationData.value &&
    educationData.value.summary &&
    educationData.value.summary.total_courses === 0 &&
    educationData.value.education_status.length === 0
  )
})

// ===== API 호출 =====
const fetchEducationStatus = async () => {
  loading.value = true
  error.value = null

  try {
    const response = await fetch(
      `/api/security-education/user-summary?year=${selectedYear.value}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${authStore.token}`,
        },
      },
    )

    if (!response.ok) {
      if (response.status === 401) {
        authStore.logout()
        throw new Error('로그인이 만료되었습니다.')
      }
      try {
        const errorData = await response.json()
        throw new Error(errorData.error || `HTTP ${response.status}: 데이터를 불러올 수 없습니다.`)
      } catch {
        throw new Error(`HTTP ${response.status}: 데이터를 불러올 수 없습니다.`)
      }
    }

    const responseData = await response.json()

    if (!responseData || typeof responseData !== 'object') {
      throw new Error('서버에서 올바르지 않은 응답을 받았습니다.')
    }

    educationData.value = {
      year: responseData.year || selectedYear.value,
      education_status: responseData.education_status || [],
      summary: {
        total_courses: responseData.summary?.total_courses || 0,
        completed: responseData.summary?.completed || 0,
        incomplete: responseData.summary?.incomplete || 0,
        not_started: responseData.summary?.not_started || 0,
        completion_rate: responseData.summary?.completion_rate || 0,
        penalty_score: responseData.summary?.penalty_score || 0.0,
        excluded_count: responseData.summary?.excluded_count || 0,
        unique_courses: responseData.summary?.unique_courses || 0,
        avg_completion_rate: responseData.summary?.avg_completion_rate || 0.0,
      },
    }
  } catch (err) {
    error.value = err.message || '교육 현황을 불러오는 중 오류가 발생했습니다.'
    educationData.value = {
      year: selectedYear.value,
      education_status: [],
      summary: {
        total_courses: 0, completed: 0, incomplete: 0, not_started: 0,
        completion_rate: 0, penalty_score: 0.0, excluded_count: 0,
        unique_courses: 0, avg_completion_rate: 0.0,
      },
    }
  } finally {
    loading.value = false
  }
}

// ===== 프로그레스 바 =====
const getProgressClass = (rate) => {
  if (rate >= 100) return 'excellent'
  return 'poor'
}

// ===== 수료율 색상 =====
const getCompletionRateClass = (rate) => {
  if (rate === undefined || rate === null) return 'completion-rate-poor'
  if (rate >= 100) return 'completion-rate-excellent'
  return 'completion-rate-poor'
}

// ===== 날짜 포맷 =====
const formatDate = (dateString) => {
  if (!dateString) return '-'
  try {
    return new Date(dateString).toLocaleDateString('ko-KR')
  } catch {
    return dateString
  }
}

// ===== 기간 카드 클래스 =====
const getPeriodCardClass = (education) => {
  if (!education) return 'pending'
  if (education.exclude_from_scoring) return 'excluded'

  if (education.status) {
    switch (education.status) {
      case 'completed': return 'passed'
      case 'in_progress': return 'in-progress'
      case 'incomplete': return 'failed'
      case 'not_started': return 'pending'
      case 'expired': return 'failed'
      default: return 'pending'
    }
  }

  if (education.completion_rate !== undefined) {
    return education.completion_rate >= 100 ? 'passed' : 'failed'
  }

  return 'pending'
}

// ===== 상태 뱃지 =====
const getStatusBadgeClass = (education) => {
  if (education.exclude_from_scoring) return 'excluded'

  if (education.status) {
    switch (education.status) {
      case 'completed': return 'success'
      case 'in_progress': return 'warning'
      case 'incomplete': return 'danger'
      case 'not_started': return 'info'
      case 'expired': return 'danger'
      default: return 'unknown'
    }
  }

  if (education.completion_rate !== undefined) {
    return education.completion_rate >= 100 ? 'success' : 'danger'
  }

  return 'unknown'
}

const getStatusText = (education) => {
  if (education.exclude_from_scoring) return '교육 제외'

  if (education.status) {
    switch (education.status) {
      case 'completed': return '수료'
      case 'in_progress': return '진행중'
      case 'incomplete': return '미수료'
      case 'not_started': return '시작전'
      case 'expired': return '기간만료'
      default: return '알 수 없음'
    }
  }

  if (education.completion_rate !== undefined) {
    return education.completion_rate >= 100 ? '수료' : '미수료'
  }

  return '알 수 없음'
}

// ===== 개별 교육 알림 =====
const getIndividualNoticeClass = (education) => {
  if (education.exclude_from_scoring) return 'excluded'

  if (education.status) {
    switch (education.status) {
      case 'completed': return 'pass'
      case 'in_progress': return 'pending'
      case 'incomplete': return 'fail'
      case 'not_started': return 'pending'
      case 'expired': return 'fail'
      default: return 'pending'
    }
  }

  if (education.completion_rate !== undefined) {
    return education.completion_rate >= 100 ? 'pass' : 'fail'
  }

  return 'pending'
}

const getIndividualNoticeIcon = (education) => {
  if (education.exclude_from_scoring) return '🚫'

  if (education.status) {
    switch (education.status) {
      case 'completed': return '✅'
      case 'in_progress': return '🔄'
      case 'incomplete': return '⚠️'
      case 'not_started': return '📅'
      case 'expired': return '❌'
      default: return '⚠️'
    }
  }

  if (education.completion_rate !== undefined) {
    return education.completion_rate >= 100 ? '✅' : '⚠️'
  }

  return '⚠️'
}

const getIndividualNoticeMessage = (education) => {
  const typeName = education.course_name || education.type_name || education.type || '교육'

  if (education.exclude_from_scoring) {
    return `${typeName}이 점수 계산에서 제외되었습니다.`
  }

  if (education.status) {
    switch (education.status) {
      case 'completed': return `${typeName}을 수료했습니다.`
      case 'in_progress': return `${typeName}이 진행 중입니다.`
      case 'incomplete': return `${typeName}이 미수료 상태입니다.`
      case 'not_started': return `${typeName}이 아직 시작되지 않았습니다.`
      case 'expired': return `${typeName}의 교육 기간이 만료되었습니다.`
      default: return `${typeName} 상태를 확인해주세요.`
    }
  }

  if (education.completion_rate !== undefined) {
    return education.completion_rate >= 100
      ? `${typeName}을 수료했습니다.`
      : `${typeName}이 미수료 상태입니다.`
  }

  return `${typeName} 상태를 확인해주세요.`
}

const getIndividualPenalty = (education) => {
  if (education.exclude_from_scoring) return 0

  if (education.status) {
    switch (education.status) {
      case 'completed': return 0
      case 'in_progress': return 0
      case 'incomplete': return 0.5
      case 'not_started': return 0
      case 'expired': return 0.5
      default: return 0
    }
  }

  if (education.completion_rate !== undefined) {
    return education.completion_rate >= 100 ? 0 : 0.5
  }

  return 0
}

// ===== 대시보드 카드/아이콘 클래스 =====
const getEducationCardClass = () => {
  const summary = educationData.value?.summary
  const educations = educationData.value?.education_status || []

  if (!summary) return ''

  if (educations.some(edu => edu.status === 'in_progress')) return 'education-in-progress'
  if ((summary.completion_rate || 0) >= 100) return 'education-completed'

  return 'education-incomplete'
}

const getEducationIconClass = () => {
  const summary = educationData.value?.summary
  const educations = educationData.value?.education_status || []

  if (!summary) return ''

  if (educations.some(edu => edu.status === 'in_progress')) return 'icon-warning'
  if ((summary.completion_rate || 0) >= 100) return 'icon-success'

  return 'icon-danger'
}

// ===== 초기화 =====
onMounted(() => {
  if (authStore.user) {
    fetchEducationStatus()
  }
})
</script>

<style scoped>
@import '../styles/SecurityEducationPage.css';
</style>