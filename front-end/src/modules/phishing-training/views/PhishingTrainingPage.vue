<!-- views/PhishingTrainingPage.vue -->
<template>
  <main>
    <div class="training-page">
      <!-- 연도 선택기 -->
      <div class="page-header">
        <h1 class="page-title">악성메일 모의훈련 현황</h1>
        <div class="year-selector">
          <label for="year">연도:</label>
          <select id="year" v-model="selectedYear" @change="fetchTrainingStatus">
            <option v-for="year in availableYears" :key="year" :value="year">{{ year }}년</option>
          </select>
        </div>
      </div>

      <!-- 로딩 상태 -->
      <div v-if="loading" class="loading-container">
        <div class="loading-spinner"></div>
        <p>모의훈련 현황을 불러오는 중...</p>
      </div>

      <!-- 에러 상태 -->
      <div v-else-if="error" class="error-container">
        <div class="error-icon">⚠️</div>
        <h3>데이터 로드 오류</h3>
        <p>{{ error }}</p>
        <button @click="fetchTrainingStatus" class="retry-button">다시 시도</button>
      </div>

      <!-- 모의훈련 현황 데이터 -->
      <div v-else-if="trainingData" class="training-content">

        <!-- 훈련 상태 대시보드 -->
        <div class="section">
          <div class="dashboard-grid">
            <div class="dashboard-card phishing-training">
              <div class="card-header">
                <div class="card-icon phishing">
                  <svg width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M0 4a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V4Zm2-1a1 1 0 0 0-1 1v.217l7 4.2 7-4.2V4a1 1 0 0 0-1-1H2Zm13 2.383-4.708 2.825L15 11.105V5.383Zm-.034 6.876-5.64-3.471L8 9.583l-1.326-.795-5.64 3.47A1 1 0 0 0 2 13h12a1 1 0 0 0 .966-.741ZM1 11.105l4.708-2.897L1 5.383v5.722Z" />
                  </svg>
                </div>
                <h3>악성메일 모의훈련</h3>
                <span class="card-frequency">{{ selectedYear }}년 실시</span>
              </div>

              <div class="card-stats">
                <div class="stat-row">
                  <span class="stat-label">실시 횟수</span>
                  <span class="stat-value">{{ trainingData.summary.conducted }}</span>
                </div>
                <div class="stat-row">
                  <span class="stat-label">양호</span>
                  <span class="stat-value success">{{ trainingData.summary.passed }}</span>
                </div>
                <div class="stat-row">
                  <span class="stat-label">미흡</span>
                  <span class="stat-value danger">{{ trainingData.summary.failed }}</span>
                </div>
              </div>

              <div class="card-progress">
                <div class="progress-bar">
                  <div
                    class="progress-fill phishing"
                    :style="{ width: `${trainingData.summary.pass_rate}%` }"
                    :class="getProgressClass(trainingData.summary.pass_rate)"
                  ></div>
                </div>
                <span
                  class="progress-text"
                  :class="trainingData.summary.pass_rate >= 100 ? 'text-excellent' : 'text-poor'"
                >양호율 {{ trainingData.summary.pass_rate }}%</span>
              </div>

              <div v-if="trainingData.summary.excluded_count > 0" class="card-notice">
                <span>ℹ️ {{ trainingData.summary.excluded_count }}건 점수 제외</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 상반기/하반기별 상세 현황 -->
        <div class="section">
          <h2 class="section-title">상반기/하반기별 모의훈련 결과</h2>

          <!-- 일정이 없는 경우 -->
          <div v-if="!trainingData.period_status || trainingData.period_status.length === 0" class="no-schedule-notice">
            <div class="no-schedule-icon">📅</div>
            <p>{{ selectedYear }}년에 등록된 모의훈련 일정이 없습니다.</p>
          </div>

          <!-- 일정이 있는 경우 -->
          <div v-else class="periods-grid">
            <div
              v-for="period in trainingData.period_status"
              :key="period.period"
              class="period-card"
              :class="getPeriodCardClass(period)"
            >
              <!-- 카드 헤더: 기간명 + 상태 뱃지 -->
              <div class="period-header">
                <h3>{{ period.period_name }}</h3>
                <div class="status-badge" :class="getStatusBadgeClass(period)">
                  {{ getResultText(period) }}
                </div>
              </div>

              <!-- 서브텍스트: 일정 -->
              <div class="period-sub">
                <span v-if="period.start_date && period.end_date">
                  {{ formatDate(period.start_date) }} ~ {{ formatDate(period.end_date) }}
                </span>
              </div>

              <!-- 통계 인라인 -->
              <div class="period-stats">
                <div class="period-stat-item">
                  <span class="period-stat-num" :class="{ success: period.result === 'pass' }">{{ period.result === 'pass' ? 1 : 0 }}</span>
                  <span class="period-stat-label">양호</span>
                </div>
                <span class="period-stat-sep">/</span>
                <div class="period-stat-item">
                  <span class="period-stat-num" :class="{ danger: period.result === 'fail' }">{{ period.result === 'fail' ? 1 : 0 }}</span>
                  <span class="period-stat-label">미흡</span>
                </div>
                <span class="period-stat-sep">/</span>
                <div class="period-stat-item">
                  <span class="period-stat-num">{{ period.result === 'pending' ? 0 : 1 }}</span>
                  <span class="period-stat-label">총 훈련</span>
                </div>
              </div>

              <!-- 프로그레스 바 -->
              <div class="period-progress">
                <div class="period-progress-bar">
                  <div
                    class="period-progress-fill"
                    :class="period.result === 'pass' ? 'excellent' : 'poor'"
                    :style="{ width: period.result === 'pass' ? '100%' : '0%' }"
                  ></div>
                </div>
                <span
                  class="period-progress-text"
                  :class="period.result === 'pass' ? 'text-excellent' : 'text-poor'"
                >{{ period.result === 'pass' ? '100%' : '0%' }}</span>
              </div>

              <!-- 하단 알림 메시지 -->
              <div class="period-message" :class="getMessageClass(period)">
                {{ getMessageText(period) }}
              </div>
            </div>
          </div>
        </div>

        <!-- 훈련 안내 -->
        <div class="section">
          <h2 class="section-title">악성메일 모의훈련 안내</h2>
          <div class="info-grid">
            <div class="info-card">
              <div class="info-icon">📧</div>
              <h3>훈련 방식</h3>
              <ul>
                <li>상반기/하반기 각 1회 실시</li>
                <li>무작위 시점에 발송</li>
                <li>클릭/열람 여부 및 시간 추적</li>
              </ul>
            </div>
            <div class="info-card">
              <div class="info-icon">🎯</div>
              <h3>평가 기준</h3>
              <ul>
                <li>첨부파일 열람/링크 클릭: 미흡</li>
              </ul>
            </div>
            <div class="info-card">
              <div class="info-icon">🛡️</div>
              <h3>대응 방법</h3>
              <ul>
                <li>의심스러운 메일은 즉시 신고</li>
                <li>첨부파일 다운로드 주의</li>
                <li>링크 클릭 전 URL 확인</li>
                <li>발신자 정보 검증</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

// 반응형 데이터
const loading = ref(false)
const error = ref(null)
const trainingData = ref(null)
const selectedYear = ref(new Date().getFullYear())

// 연도 목록
const availableYears = computed(() => {
  const currentYear = new Date().getFullYear()
  return [currentYear - 2, currentYear - 1, currentYear, currentYear + 1]
})

// 빈 데이터 여부
const isEmptyData = computed(() => {
  return (
    trainingData.value &&
    trainingData.value.summary &&
    trainingData.value.summary.total_trainings === 0 &&
    (!trainingData.value.period_status || trainingData.value.period_status.length === 0)
  )
})

// ===== API 호출 =====
const fetchTrainingStatus = async () => {
  loading.value = true
  error.value = null

  try {
    const response = await fetch(`/api/phishing-training/status?year=${selectedYear.value}`, {
      method: 'GET',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()
    trainingData.value = data
  } catch (err) {
    error.value = err.message || '모의훈련 현황을 불러올 수 없습니다.'
  } finally {
    loading.value = false
  }
}

// ===== 대시보드 프로그레스 바 =====
const getProgressClass = (rate) => {
  if (rate >= 100) return 'excellent'
  return 'poor'
}

// ===== 기간 카드 클래스 =====
const getPeriodCardClass = (period) => {
  if (period.exclude_from_scoring) return 'excluded'
  if (period.result === 'pass') return 'passed'
  if (period.result === 'fail') return 'failed'
  return 'pending'
}

// ===== 상태 뱃지 =====
const getStatusBadgeClass = (period) => {
  if (period.exclude_from_scoring) return 'excluded'
  if (period.result === 'pass') return 'success'
  if (period.result === 'fail') return 'danger'
  return 'warning'
}

const getResultText = (period) => {
  if (period.exclude_from_scoring) return '훈련 제외'
  if (period.result === 'pass') return '양호'
  if (period.result === 'fail') return '미흡'
  return '미실시'
}

// ===== 하단 메시지 =====
const getMessageClass = (period) => {
  if (period.exclude_from_scoring) return 'excluded'
  if (period.result === 'pass') return 'pass'
  if (period.result === 'fail') return 'fail'
  return 'pending'
}

const getMessageText = (period) => {
  if (period.exclude_from_scoring) return '모의훈련이 점수 계산에서 제외되었습니다.'
  if (period.result === 'pass') return '모의훈련 결과가 양호합니다.'
  if (period.result === 'fail') {
    return `모의훈련에서 ${period.log_type || '피싱 활동'}을 했습니다.`
  }
  return '이 기간 모의훈련이 아직 실시되지 않았습니다.'
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

// ===== 감시자 및 초기화 =====
watch(selectedYear, () => {
  fetchTrainingStatus()
})

onMounted(() => {
  if (authStore.user) {
    fetchTrainingStatus()
  }
})
</script>

<style scoped>
@import '../styles/PhishingTrainingPage.css';

.no-schedule-notice {
  text-align: center;
  padding: 3rem 2rem;
  background-color: #f9fafb;
  border: 1px dashed #d1d5db;
  border-radius: 12px;
  color: #6b7280;
}

.no-schedule-icon {
  font-size: 2.5rem;
  margin-bottom: 0.75rem;
}

.no-schedule-notice p {
  margin: 0;
  font-size: 1rem;
}
</style>