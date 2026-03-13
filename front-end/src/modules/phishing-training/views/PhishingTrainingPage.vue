<!-- views/PhishingTrainingPage.vue -->
<template>
  <main class="">
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
        <h3>데이터 로드 실패</h3>
        <p>{{ error }}</p>
        <button @click="fetchTrainingStatus" class="retry-button">다시 시도</button>
      </div>

      <!-- 모의훈련 현황 데이터 -->
      <div v-else-if="trainingData" class="training-content">
        <!-- 훈련 상태 대시보드 -->
        <div class="section">
          <div class="dashboard-grid">
            <!-- 모의훈련 카드 -->
            <div class="dashboard-card phishing-training">
              <div class="card-header">
                <div class="card-icon phishing">
                  <svg width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
                    <path
                      d="M8 1a2.5 2.5 0 0 1 2.5 2.5V4h-5v-.5A2.5 2.5 0 0 1 8 1zm3.5 3v-.5a3.5 3.5 0 1 0-7 0V4H1v10a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V4h-3.5zM2 5h12v9a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V5z"
                    />
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
                <div class="stat-row">
                  <span class="stat-label">미실시</span>
                  <span class="stat-value warning">{{
                    trainingData.summary.not_started || 0
                  }}</span>
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
                <span class="progress-text">통과율 {{ trainingData.summary.pass_rate }}%</span>
              </div>

              <!-- 제외된 기록이 있을 경우 표시 -->
              <div v-if="trainingData.summary.excluded_count > 0" class="card-notice">
                <div class="notice-icon">ℹ️</div>
                <span>{{ trainingData.summary.excluded_count }}건 점수 제외</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 상반기/하반기별 상세 현황 -->
        <div class="section">
          <h2 class="section-title">상반기/하반기별 모의훈련 결과</h2>
          <div class="periods-grid">
            <div
              v-for="period in trainingData.period_status"
              :key="period.period"
              class="period-card"
              :class="getPeriodCardClass(period)"
            >
              <div class="period-header">
                <h3>{{ period.period_name }}</h3>
                <div class="status-badge" :class="getStatusBadgeClass(period.result)">
                  {{ getResultText(period.result) }}
                </div>
                <div v-if="period.exclude_from_scoring" class="excluded-badge">점수 제외</div>
              </div>

              <div class="period-details">
                <div class="detail-row" v-if="period.action_time">
                  <span class="label">수행시간:</span>
                  <span class="value">{{ period.action_time }}</span>
                </div>
                <div class="detail-row" v-if="period.log_type">
                  <span class="label">로그유형:</span>
                  <span class="value danger-text">{{ period.log_type }}</span>
                </div>
                <div class="detail-row" v-if="period.mail_type">
                  <span class="label">메일유형:</span>
                  <span class="value">{{ period.mail_type }}</span>
                </div>
                <div class="detail-row" v-if="period.user_email">
                  <span class="label">이메일:</span>
                  <span class="value">{{ period.user_email }}</span>
                </div>
                <div class="detail-row" v-if="period.ip_address">
                  <span class="label">IP주소:</span>
                  <span class="value">{{ period.ip_address }}</span>
                </div>

                <div class="detail-row">
                  <span class="label">비고:</span>
                  <span class="value notes">{{ period.notes || '-' }}</span>
                </div>
              </div>

              <!-- 결과별 알림 -->
              <div v-if="period.result === 'fail'" class="result-notice fail">
                <div class="notice-icon">⚠️</div>
                <p>모의훈련에서 {{ period.log_type || '피싱 활동' }}을 했습니다.</p>
                <small v-if="!period.exclude_from_scoring">감점: -0.5점</small>
                <small v-else>점수 계산에서 제외됨</small>
              </div>

              <div v-else-if="period.result === 'pass'" class="result-notice pass">
                <div class="notice-icon">✅</div>
                <p>모의훈련을 성공적으로 통과했습니다.</p>
                <small v-if="period.response_time_minutes">
                  {{ period.response_time_minutes }}분 경과 후 액션 없음
                </small>
              </div>

              <div v-else="period.result === 'pending'" class="result-notice pending">
                <div class="notice-icon">⏳</div>
                <p>이 기간 모의훈련이 아직 실시되지 않았습니다.</p>
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
// PhishingTrainingPage.vue의 완전한 <script setup> 섹션
// 상반기/하반기별 상세 모의훈련 결과 포함

import { ref, onMounted, computed, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'

// Pinia Store
const authStore = useAuthStore()

// 반응형 데이터
const loading = ref(false)
const error = ref(null)
const trainingData = ref(null)
const selectedYear = ref(new Date().getFullYear())

// 계산된 속성
const availableYears = computed(() => {
  const currentYear = new Date().getFullYear()
  return [currentYear - 2, currentYear - 1, currentYear, currentYear + 1]
})

// ===== MOCK 데이터 생성 함수들 =====

/**
 * 메인 MOCK 데이터 생성 함수
 */
const generateMockTrainingData = (year) => {
  const currentDate = new Date()
  const currentYear = currentDate.getFullYear()
  const currentMonth = currentDate.getMonth()

  // 기본 통계 데이터
  const summary = {
    conducted: 0,
    passed: 0,
    failed: 0,
    pending: 0,
    not_started: 0,
    overall_score: 0,
    pass_rate: 0,
    penalty_score: 0,
    excluded_count: 0,
  }

  // 상반기/하반기별 상태 데이터
  const period_status = []

  // 상반기 훈련 데이터 (3-6월)
  const firstHalfPeriod = createPeriodData(year, 'first_half', {
    period_name: `${year}년 상반기 피싱 훈련`,
    start_date: `${year}-03-01`,
    end_date: `${year}-06-30`,
    mail_sent_date: `${year}-04-15`,
    training_themes: ['퇴직연금 안내', '보험 상품 안내', '건강검진 결과'],
    currentYear,
    currentMonth,
  })

  // 하반기 훈련 데이터 (9-12월)
  const secondHalfPeriod = createPeriodData(year, 'second_half', {
    period_name: `${year}년 하반기 피싱 훈련`,
    start_date: `${year}-09-01`,
    end_date: `${year}-12-31`,
    mail_sent_date: `${year}-10-20`,
    training_themes: ['세금계산서', '배송 알림', '카카오톡 메시지'],
    currentYear,
    currentMonth,
  })

  period_status.push(firstHalfPeriod, secondHalfPeriod)

  // 통계 계산
  period_status.forEach((period) => {
    if (period.result === 'pass') {
      summary.passed++
      summary.conducted++
    } else if (period.result === 'fail') {
      summary.failed++
      summary.conducted++
      if (!period.exclude_from_scoring) {
        summary.penalty_score += 0.5
        summary.overall_score -= 0.5
      }
    } else {
      summary.pending++
      summary.not_started++
    }

    if (period.exclude_from_scoring) {
      summary.excluded_count++
    }
  })

  // 통과율 계산
  const totalConducted = summary.passed + summary.failed
  if (totalConducted > 0) {
    summary.pass_rate = Math.round((summary.passed / totalConducted) * 100)
  }

  return {
    summary,
    period_status,
    periods: period_status, // 기존 템플릿 호환성을 위해 추가
    user_info: {
      username: authStore.user?.username || '홍길동',
      email: authStore.user?.email || 'hong@company.com',
      department: authStore.user?.department || '개발팀',
      position: authStore.user?.position || '선임연구원',
    },
    year_stats: {
      year: year,
      total_periods: 2,
      completed_periods: summary.conducted,
      pending_periods: summary.pending,
      average_response_time: calculateAverageResponseTime(period_status),
      improvement_trend: calculateImprovementTrend(year, summary.pass_rate),
    },
  }
}

/**
 * 기간별 상세 데이터 생성 함수
 */
const createPeriodData = (year, period, config) => {
  const {
    period_name,
    start_date,
    end_date,
    mail_sent_date,
    training_themes,
    currentYear,
    currentMonth,
  } = config

  const baseData = {
    period_id: `${year}_${period}`,
    period: period,
    period_name: period_name,
    training_type: '이메일 피싱',
    year: year,
    quarter: period === 'first_half' ? '상반기' : '하반기',
    start_date: start_date,
    end_date: end_date,
    conducted_date: `${mail_sent_date}T09:00:00.000Z`,
    result: 'pending',
    exclude_from_scoring: false,
    log_type: null,
    mail_type: null,
    email_sent_time: null,
    action_time: null,
    response_time_minutes: null,
    score_impact: 0,
    notes: null,
    // 추가 상세 정보
    training_details: {
      target_count: 1,
      completion_rate: 0,
      phishing_url: null,
      attachment_name: null,
      sender_email: null,
      mail_subject: null,
    },
  }

  // 연도별 결과 설정
  if (year < currentYear) {
    // 과거 년도 - 완료된 훈련
    return generateCompletedTraining(baseData, period, training_themes, year)
  } else if (year === currentYear) {
    // 현재 년도 - 진행 상황에 따라
    return generateCurrentYearTraining(baseData, period, training_themes, currentMonth, year)
  } else {
    // 미래 년도 - 미실시
    return generateFutureTraining(baseData)
  }
}

/**
 * 완료된 훈련 데이터 생성 (과거 년도)
 */
const generateCompletedTraining = (baseData, period, training_themes, year) => {
  const trainingScenarios = [
    // 통과 시나리오들
    {
      result: 'pass',
      log_type: '이메일 열람',
      action_time: null,
      response_time_minutes: 0,
      notes: '의심스러운 메일로 판단하여 액션 없음',
      score_impact: 0,
    },
    {
      result: 'pass',
      log_type: '이메일 삭제',
      action_time: null,
      response_time_minutes: 0,
      notes: '피싱 메일로 인식하고 즉시 삭제',
      score_impact: 0,
    },
    // 실패 시나리오들
    {
      result: 'fail',
      log_type: '스크립트 첨부파일 열람',
      response_time_minutes: 15,
      notes: '첨부파일을 다운로드하여 실행함',
      score_impact: -0.5,
    },
    {
      result: 'fail',
      log_type: '링크 클릭',
      response_time_minutes: 5,
      notes: '의심스러운 링크를 클릭함',
      score_impact: -0.5,
    },
    {
      result: 'fail',
      log_type: '개인정보 입력',
      response_time_minutes: 8,
      notes: '피싱 사이트에 개인정보 입력',
      score_impact: -0.5,
    },
  ]

  // 상반기는 주로 통과, 하반기는 실패하는 경향으로 설정
  const scenario =
    period === 'first_half'
      ? trainingScenarios[Math.floor(Math.random() * 2)] // 통과 시나리오
      : trainingScenarios[2 + Math.floor(Math.random() * 3)] // 실패 시나리오

  const mailType = training_themes[Math.floor(Math.random() * training_themes.length)]

  return {
    ...baseData,
    result: scenario.result,
    log_type: scenario.log_type,
    mail_type: mailType,
    email_sent_time: `${year}-${period === 'first_half' ? '04-15' : '10-20'}T09:00:00.000Z`,
    action_time:
      scenario.response_time_minutes > 0
        ? `${year}-${period === 'first_half' ? '04-15' : '10-20'}T${9 + Math.floor(scenario.response_time_minutes / 60)}:${String(scenario.response_time_minutes % 60).padStart(2, '0')}:00.000Z`
        : null,
    response_time_minutes: scenario.response_time_minutes,
    score_impact: scenario.score_impact,
    notes: scenario.notes,
    training_details: {
      target_count: 1,
      completion_rate: 100,
      phishing_url: scenario.log_type.includes('링크') ? 'https://fake-banking-site.com' : null,
      attachment_name: scenario.log_type.includes('첨부파일') ? `${mailType}_안내.pdf` : null,
      sender_email: generateFakeSenderEmail(mailType),
      mail_subject: generateMailSubject(mailType),
    },
  }
}

/**
 * 현재 년도 훈련 데이터 생성
 */
const generateCurrentYearTraining = (baseData, period, training_themes, currentMonth, year) => {
  const isFirstHalf = period === 'first_half'
  const shouldBeCompleted = isFirstHalf ? currentMonth >= 6 : currentMonth >= 10

  if (!shouldBeCompleted) {
    return generateFutureTraining(baseData)
  }

  // 현재 년도는 최신 훈련이므로 더 현실적인 결과
  const currentYearScenarios = [
    {
      result: 'pass',
      log_type: '이메일 열람2',
      response_time_minutes: 0,
      notes: '피싱 메일로 인식하고 즉시 신고함',
      score_impact: 0,
    },
    {
      result: 'fail',
      log_type: '링크 클릭',
      response_time_minutes: 2,
      notes: '의심스러운 링크를 클릭함',
      score_impact: -0.5,
    },
  ]

  const scenario = isFirstHalf ? currentYearScenarios[0] : currentYearScenarios[1]
  const mailType = training_themes[0] // 첫 번째 테마 사용

  return {
    ...baseData,
    result: scenario.result,
    log_type: scenario.log_type,
    mail_type: mailType,
    email_sent_time: `${year}-${isFirstHalf ? '04-15' : '10-20'}T09:00:00.000Z`,
    action_time:
      scenario.response_time_minutes > 0
        ? `${year}-${isFirstHalf ? '04-15' : '10-20'}T09:0${scenario.response_time_minutes}:00.000Z`
        : null,
    response_time_minutes: scenario.response_time_minutes,
    score_impact: scenario.score_impact,
    notes: scenario.notes,
    training_details: {
      target_count: 1,
      completion_rate: 100,
      phishing_url: scenario.log_type.includes('링크')
        ? 'https://fake-delivery-notification.com'
        : null,
      attachment_name: null,
      sender_email: generateFakeSenderEmail(mailType),
      mail_subject: generateMailSubject(mailType),
    },
  }
}

/**
 * 미래 훈련 데이터 생성
 */
const generateFutureTraining = (baseData) => {
  return {
    ...baseData,
    result: 'pending',
    training_details: {
      target_count: 1,
      completion_rate: 0,
      phishing_url: null,
      attachment_name: null,
      sender_email: null,
      mail_subject: null,
    },
  }
}

/**
 * 가짜 발신자 이메일 생성
 */
const generateFakeSenderEmail = (mailType) => {
  const emailMap = {
    '퇴직연금 안내': 'pension@korea-retire.com',
    '보험 상품 안내': 'insurance@best-insure.co.kr',
    '건강검진 결과': 'health@medical-center.or.kr',
    세금계산서: 'tax@hometax-service.go.kr',
    '배송 알림': 'delivery@express-ship.com',
    '카카오톡 메시지': 'notify@kakao-talk.com',
  }
  return emailMap[mailType] || 'noreply@suspicious-site.com'
}

/**
 * 메일 제목 생성
 */
const generateMailSubject = (mailType) => {
  const subjectMap = {
    '퇴직연금 안내': '[긴급] 퇴직연금 운용 변경 안내',
    '보험 상품 안내': '[필수확인] 새로운 보험상품 가입 혜택',
    '건강검진 결과': '[중요] 건강검진 결과 확인 요청',
    세금계산서: '[국세청] 세금계산서 발급 완료 안내',
    '배송 알림': '[택배] 배송 지연 안내 - 확인 필요',
    '카카오톡 메시지': '[카카오톡] 새로운 메시지가 도착했습니다',
  }
  return subjectMap[mailType] || '[중요] 긴급 확인 요청'
}

// ===== 헬퍼 함수들 =====

const calculateAverageResponseTime = (periods) => {
  const completedPeriods = periods.filter((p) => p.result === 'fail' && p.response_time_minutes)
  if (completedPeriods.length === 0) return 0

  const totalTime = completedPeriods.reduce((sum, p) => sum + p.response_time_minutes, 0)
  return Math.round(totalTime / completedPeriods.length)
}

const calculateImprovementTrend = (year, passRate) => {
  const currentYear = new Date().getFullYear()

  if (year >= currentYear) return 'stable'
  if (passRate >= 75) return 'excellent'
  if (passRate >= 50) return 'good'
  if (passRate >= 25) return 'warning'
  return 'poor'
}

// ===== 메인 메서드 =====

const fetchTrainingStatus = async () => {
  loading.value = true
  error.value = null

  try {
    const response = await fetch(`/api/phishing-training/status?year=${selectedYear.value}`, {
      method: 'GET',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()
    console.log(data)
    trainingData.value = data
  } catch (err) {
    console.error('모의훈련 현황 조회 실패:', err)
    error.value = err.message || '모의훈련 현황을 불러올 수 없습니다.'
  } finally {
    loading.value = false
  }
}

// ===== 템플릿에서 사용하는 기존 메서드들 =====

const getProgressClass = (rate) => {
  if (rate >= 75) return 'excellent'
  if (rate >= 50) return 'good'
  if (rate >= 25) return 'warning'
  return 'poor'
}

const getPeriodCardClass = (period) => {
  if (period.exclude_from_scoring) return 'excluded'
  if (period.result === 'pass') return 'passed'
  if (period.result === 'fail') return 'failed'
  return 'pending'
}

const getStatusBadgeClass = (result) => {
  if (result === 'pass') return 'success'
  if (result === 'fail') return 'danger'
  return 'warning'
}

const getResultText = (result) => {
  const texts = {
    pass: '양호',
    fail: '미흡',
  }
  return texts[result] || '알 수 없음'
}

// ===== 추가 포맷팅 함수들 =====

const formatResponseTime = (minutes) => {
  if (!minutes || minutes === 0) return '즉시'

  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60

  if (hours > 0) {
    return `${hours}시간 ${mins}분`
  }
  return `${mins}분`
}

const formatDateTime = (dateTimeString) => {
  if (!dateTimeString) return '-'

  try {
    return new Date(dateTimeString).toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return dateTimeString
  }
}

const formatScoreImpact = (impact) => {
  if (!impact || impact === 0) return ''
  return impact > 0 ? `+${impact}점` : `${impact}점`
}

// 훈련 상태 텍스트 반환
const getTrainingStatusText = (period) => {
  if (period.result === 'pass') return '훈련 통과'
  if (period.result === 'fail') return '훈련 실패'
  return '훈련 미실시'
}

// 위험도 레벨 계산
const getRiskLevel = (period) => {
  if (period.result === 'fail') {
    if (period.log_type?.includes('개인정보')) return 'high'
    if (period.log_type?.includes('첨부파일')) return 'medium'
    if (period.log_type?.includes('링크')) return 'medium'
  }
  return 'low'
}

// 위험도 텍스트
const getRiskLevelText = (riskLevel) => {
  const riskMap = {
    high: '높음',
    medium: '보통',
    low: '낮음',
  }
  return riskMap[riskLevel] || '알 수 없음'
}

// 훈련 완료율 계산
const getCompletionRate = (periods) => {
  const total = periods.length
  const completed = periods.filter((p) => p.result !== 'pending').length
  return total > 0 ? Math.round((completed / total) * 100) : 0
}

// ===== 감시자 및 라이프사이클 =====

watch(selectedYear, () => {
  fetchTrainingStatus()
})

onMounted(() => {
  if (authStore.user) {
    fetchTrainingStatus()
  }
})
</script>

<!-- CSS는 외부 파일에서 import -->
<style scoped>
@import '../styles/PhishingTrainingPage.css';
</style>
