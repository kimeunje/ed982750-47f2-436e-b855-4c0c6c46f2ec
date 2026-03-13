<template>
  <div class="admin-user-detail">
    <!-- 헤더 -->
    <div class="detail-header">
      <div class="header-content">
        <div class="back-navigation">
          <button @click="goBack" class="back-btn">
            <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
              <path
                d="M11.354 1.646a.5.5 0 0 1 0 .708L5.707 8l5.647 5.646a.5.5 0 0 1-.708.708l-6-6a.5.5 0 0 1 0-.708l6-6a.5.5 0 0 1 .708 0z"
              />
            </svg>
            사용자 목록으로 돌아가기
          </button>
        </div>

        <div class="title-section">
          <h1 v-if="userDetail">{{ userDetail.user_info?.name || userDetail.user_info?.username }} 상세 정보</h1>
          <h1 v-else>사용자 상세 정보</h1>
          <p>보안 점수 및 상세 감점 내역을 확인합니다</p>
        </div>

        <div class="header-actions">
          <div class="year-selector">
            <label>평가 년도:</label>
            <select v-model="selectedYear" @change="loadUserDetail">
              <option v-for="year in availableYears" :key="year" :value="year">{{ year }}년</option>
            </select>
          </div>

          <button @click="exportUserDetail" class="export-btn" :disabled="loading">
            <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
              <path
                d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"
              />
              <path
                d="M7.646 1.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1-.708.708L8.5 2.707V11.5a.5.5 0 0 1-1 0V2.707L5.354 4.854a.5.5 0 1 1-.708-.708l3-3z"
              />
            </svg>
            상세 보고서 내보내기
          </button>
        </div>
      </div>
    </div>

    <!-- 로딩 상태 -->
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>사용자 상세 정보를 불러오는 중...</p>
    </div>

    <!-- 에러 상태 -->
    <div v-else-if="error" class="error-container">
      <div class="error-icon">
        <svg width="48" height="48" fill="currentColor" viewBox="0 0 16 16">
          <path
            d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM5.354 4.646a.5.5 0 1 0-.708.708L7.293 8l-2.647 2.646a.5.5 0 0 0 .708.708L8 8.707l2.646 2.647a.5.5 0 0 0 .708-.708L8.707 8l2.647-2.646a.5.5 0 0 0-.708-.708L8 7.293 5.354 4.646z"
          />
        </svg>
      </div>
      <h3>데이터 로드 실패</h3>
      <p>{{ error }}</p>
      <button @click="loadUserDetail" class="retry-btn">다시 시도</button>
    </div>

    <!-- 사용자 상세 정보 -->
    <div v-else-if="userDetail" class="detail-content">
      <!-- 1. 사용자 기본 정보 카드 -->
      <div class="user-info-card">
        <div class="card-header">
          <h2>기본 정보</h2>
          <div class="risk-indicator" :class="getRiskLevel()">
            <span class="risk-dot"></span>
            {{ getRiskLevelLabel() }}
          </div>
        </div>

        <div class="user-basic-info">
          <div class="info-grid">
            <div class="info-item">
              <label>이름</label>
              <span class="value">{{ userDetail.user_info?.name || userDetail.user_info?.username }}</span>
            </div>
            <div class="info-item">
              <label>사번</label>
              <span class="value employee-id">{{ userDetail.user_info?.employee_id || userDetail.user_info?.user_id }}</span>
            </div>
            <div class="info-item">
              <label>부서</label>
              <span class="value">{{ userDetail.user_info?.department || '-' }}</span>
            </div>
            <div class="info-item">
              <label>직급</label>
              <span class="value">{{ userDetail.user_info?.position || '-' }}</span>
            </div>
            <div class="info-item">
              <label>이메일</label>
              <span class="value email">{{ userDetail.user_info?.email || userDetail.user_info?.mail }}</span>
            </div>
            <div class="info-item">
              <label>마지막 업데이트</label>
              <span class="value">{{ formatDateTime(userDetail.last_updated) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 2. 종합 점수 카드 -->
      <div class="overall-score-card">
        <div class="score-circle">
          <div class="circle-chart" :class="getRiskLevel()">
            <div class="circle-score">
              <span class="score-number">{{ getTotalPenalty() }}</span>
              <span class="score-unit">점</span>
            </div>
            <div class="circle-grade">{{ getRiskLevelLabel() }}</div>
          </div>
        </div>

        <div class="score-summary">
          <h2>총 감점</h2>
          <p class="score-description">
            KPI 기준 최대 5점 감점 중 <strong>{{ getTotalPenalty() }}점</strong>이 감점되었습니다.
          </p>

          <div class="score-details">
            <div class="detail-item">
              <span class="detail-label">보안 감사</span>
              <span class="detail-value penalty">-{{ getAuditPenalty() }}점</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">정보보호 교육</span>
              <span class="detail-value penalty">-{{ getEducationPenalty() }}점</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">모의훈련</span>
              <span class="detail-value penalty">-{{ getTrainingPenalty() }}점</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 3. 감점 상세 내역 -->
      <div class="score-breakdown">
        <h2>감점 상세 내역</h2>

        <div class="breakdown-grid">
          <!-- 보안 감사 감점 -->
          <div class="breakdown-card audit">
            <div class="card-header">
              <div class="card-icon audit">
                <svg width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
                  <path d="M8 1a2 2 0 0 1 2 2v4H6V3a2 2 0 0 1 2-2zm3 6V3a3 3 0 0 0-6 0v4a2 2 0 0 0-2 2v5a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2z"/>
                </svg>
              </div>
              <h3>보안 감사</h3>
            </div>

            <div class="card-content">
              <div class="main-score penalty">-{{ getAuditPenalty() }}점</div>
              <div class="score-detail">
                <p>실패 항목: {{ getAuditStats().failed_count }}개</p>
                <p>총 점검: {{ getAuditStats().total_count }}개</p>
              </div>

              <div v-if="getAuditStats().failed_items?.length > 0" class="penalty-items">
                <h4>실패 항목 목록</h4>
                <div class="penalty-list">
                  <div
                    v-for="item in getAuditStats().failed_items"
                    :key="item.item_name"
                    class="penalty-item audit"
                  >
                    <div class="item-info">
                      <div class="item-name">{{ item.item_name }}</div>
                      <div class="item-date">{{ formatDate(item.checked_at) }}</div>
                    </div>
                    <div class="item-penalty">-{{ item.penalty || '0.5' }}점</div>
                  </div>
                </div>
              </div>

              <div v-else class="no-penalty-items">
                <span v-if="getAuditPenalty() === '0.0'">모든 감사 항목을 통과했습니다</span>
                <span v-else>상세 정보가 없습니다</span>
              </div>
            </div>

            <div class="card-footer">
              <router-link to="/security-audit" class="detail-link">
                감사 현황 보기
              </router-link>
            </div>
          </div>

          <!-- 정보보호 교육 감점 -->
          <div class="breakdown-card education">
            <div class="card-header">
              <div class="card-icon education">
                <svg width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
                  <path d="M8.211 2.047a.5.5 0 0 0-.422 0l-7.5 3.5a.5.5 0 0 0 .025.917l7.5 3a.5.5 0 0 0 .372 0L14.5 7.14V13a1 1 0 0 0-1 1v2h3v-2a1 1 0 0 0-1-1V6.739l.686-.275a.5.5 0 0 0 .025-.917l-7.5-3.5Z"/>
                </svg>
              </div>
              <h3>정보보호 교육</h3>
            </div>

            <div class="card-content">
              <div class="main-score penalty">-{{ getEducationPenalty() }}점</div>
              <div class="score-detail">
                <p>미완료 기간: {{ getEducationStats().incomplete_count }}개</p>
                <p>총 교육 기간: {{ getEducationStats().total_count }}개</p>
              </div>

              <div v-if="getEducationStats().incomplete_items?.length > 0" class="penalty-items">
                <h4>미완료 교육 목록</h4>
                <div class="penalty-list">
                  <div
                    v-for="item in getEducationStats().incomplete_items"
                    :key="item.period_name"
                    class="penalty-item education"
                  >
                    <div class="item-info">
                      <div class="item-name">{{ item.period_name }}</div>
                      <div class="item-date">{{ formatDateRange(item.start_date, item.end_date) }}</div>
                    </div>
                    <div class="item-penalty">-{{ item.penalty || '0.5' }}점</div>
                  </div>
                </div>
              </div>

              <div v-else class="no-penalty-items">
                <span v-if="getEducationPenalty() === '0.0'">모든 교육을 완료했습니다</span>
                <span v-else>상세 정보가 없습니다</span>
              </div>
            </div>

            <div class="card-footer">
              <router-link to="/security-education" class="detail-link">
                교육 현황 보기
              </router-link>
            </div>
          </div>

          <!-- 모의훈련 감점 -->
          <div class="breakdown-card training">
            <div class="card-header">
              <div class="card-icon training">
                <svg width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
                  <path d="M0 4a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V4Zm2-1a1 1 0 0 0-1 1v.217l7 4.2 7-4.2V4a1 1 0 0 0-1-1H2Zm13 2.383-4.708 2.825L15 11.105V5.383Zm-.034 6.876-5.64-3.471L8 9.583l-1.326-.795-5.64 3.47A1 1 0 0 0 2 13h12a1 1 0 0 0 .966-.741ZM1 11.105l4.708-2.897L1 5.383v5.722Z"/>
                </svg>
              </div>
              <h3>악성메일 모의훈련</h3>
            </div>

            <div class="card-content">
              <div class="main-score penalty">-{{ getTrainingPenalty() }}점</div>
              <div class="score-detail">
                <p>실패 횟수: {{ getTrainingStats().failed_count }}회</p>
                <p>총 훈련: {{ getTrainingStats().total_count }}회</p>
              </div>

              <div v-if="getTrainingStats().failed_items?.length > 0" class="penalty-items">
                <h4>실패 훈련 목록</h4>
                <div class="penalty-list">
                  <div
                    v-for="item in getTrainingStats().failed_items"
                    :key="item.period_name"
                    class="penalty-item training"
                  >
                    <div class="item-info">
                      <div class="item-name">{{ item.period_name }}</div>
                      <div class="item-date">{{ formatDateRange(item.start_date, item.end_date) }}</div>
                    </div>
                    <div class="item-penalty">-{{ item.penalty || '0.5' }}점</div>
                  </div>
                </div>
              </div>

              <div v-else class="no-penalty-items">
                <span v-if="getTrainingPenalty() === '0.0'">모든 훈련을 성공했습니다</span>
                <span v-else>상세 정보가 없습니다</span>
              </div>
            </div>

            <div class="card-footer">
              <router-link to="/phishing-training" class="detail-link">
                훈련 현황 보기
              </router-link>
            </div>
          </div>
        </div>
      </div>

      <!-- 4. 개선 권고사항 -->
      <div v-if="getTotalPenalty() !== '0.0'" class="recommendations">
        <h2>개선 권고사항</h2>

        <div class="recommendation-list">
          <div v-if="getAuditPenalty() !== '0.0'" class="recommendation-card high">
            <div class="recommendation-header">
              <div class="priority-badge high">높음</div>
              <h3>보안 감사 항목 개선</h3>
            </div>
            <p>실패한 보안 감사 항목을 점검하여 보안 정책을 준수해주세요.</p>
            <div class="recommendation-action">
              <router-link to="/security-audit/solutions" class="action-button">
                조치방법 보기 →
              </router-link>
            </div>
          </div>

          <div v-if="getEducationPenalty() !== '0.0'" class="recommendation-card medium">
            <div class="recommendation-header">
              <div class="priority-badge medium">중간</div>
              <h3>정보보호 교육 이수</h3>
            </div>
            <p>미완료된 정보보호 교육을 모두 이수하여 보안 인식을 높여주세요.</p>
            <div class="recommendation-action">
              <router-link to="/security-education" class="action-button">
                교육 이수하기 →
              </router-link>
            </div>
          </div>

          <div v-if="getTrainingPenalty() !== '0.0'" class="recommendation-card medium">
            <div class="recommendation-header">
              <div class="priority-badge medium">중간</div>
              <h3>악성메일 대응 역량 강화</h3>
            </div>
            <p>모의훈련 실패를 통해 악성메일 식별 능력을 향상시켜주세요.</p>
            <div class="recommendation-action">
              <router-link to="/phishing-training" class="action-button">
                훈련 현황 보기 →
              </router-link>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="no-recommendations">
        <div class="success-icon">
          <svg width="48" height="48" fill="currentColor" viewBox="0 0 16 16">
            <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
            <path d="M10.97 4.97a.235.235 0 0 0-.02.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.061L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-1.071-1.05z"/>
          </svg>
        </div>
        <h3>우수한 보안 관리 상태입니다!</h3>
        <p>모든 보안 요구사항을 잘 준수하고 있습니다. 계속해서 보안 수준을 유지해주세요.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// Props
const props = defineProps({
  userId: {
    type: String,
    required: true
  }
})

// Router and Store
const router = useRouter()
const authStore = useAuthStore()

// Reactive Data
const userDetail = ref(null)
const loading = ref(false)
const error = ref('')
const selectedYear = ref(new Date().getFullYear())

// Available years (recent 5 years)
const availableYears = computed(() => {
  const currentYear = new Date().getFullYear()
  return Array.from({ length: 5 }, (_, i) => currentYear - i)
})

// Admin check
const isAdmin = () => {
  return authStore.user?.role === 'admin'
}

// API Functions
const adminAPI = {
  async getUserDetail(userId, year) {
    const response = await fetch(
      `/api/admin/dashboard/users/${userId}/detail?year=${year}`,
      {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${authStore.token}`,
          'Content-Type': 'application/json',
        },
      },
    )

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    return await response.json()
  },

  async exportUserDetail(userId, year) {
    const response = await fetch(
      `/api/admin/dashboard/users/${userId}/export?year=${year}`,
      {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${authStore.token}`,
        },
      },
    )

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    return response
  },
}

// Main Functions
async function loadUserDetail() {
  if (!authStore.isAuthenticated || !isAdmin()) {
    router.push('/login')
    return
  }

  if (!props.userId) {
    error.value = '사용자 ID가 유효하지 않습니다.'
    return
  }

  loading.value = true
  error.value = ''

  try {
    console.log(`사용자 상세 정보 로드: userId=${props.userId}, year=${selectedYear.value}`)

    const detailData = await adminAPI.getUserDetail(props.userId, selectedYear.value)
    userDetail.value = detailData

    console.log('사용자 상세 정보 로드 완료:', detailData)
  } catch (err) {
    console.error('사용자 상세 정보 로드 실패:', err)
    error.value = err.message || '사용자 상세 정보를 불러오는데 실패했습니다.'
  } finally {
    loading.value = false
  }
}

// Export function
async function exportUserDetail() {
  if (!userDetail.value) return

  try {
    loading.value = true
    const response = await adminAPI.exportUserDetail(props.userId, selectedYear.value)

    const userName = userDetail.value.user_info?.name || userDetail.value.user_info?.username || '사용자'

    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${userName}_상세보고서_${selectedYear.value}.csv`
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)

    alert(`${userName}의 상세 보고서를 내보냈습니다.`)
  } catch (err) {
    console.error('상세 보고서 내보내기 실패:', err)
    alert('상세 보고서 내보내기에 실패했습니다.')
  } finally {
    loading.value = false
  }
}

// Navigation
function goBack() {
  router.push('/admin/users')
}

// Computed Properties for Score Data
const getTotalPenalty = () => {
  return (userDetail.value?.score_detail?.total_penalty || 0).toFixed(1)
}

const getAuditPenalty = () => {
  return (userDetail.value?.score_detail?.audit_penalty || 0).toFixed(1)
}

const getEducationPenalty = () => {
  return (userDetail.value?.score_detail?.education_penalty || 0).toFixed(1)
}

const getTrainingPenalty = () => {
  return (userDetail.value?.score_detail?.training_penalty || 0).toFixed(1)
}

const getAuditStats = () => {
  return userDetail.value?.score_detail?.audit_stats || {
    failed_count: 0,
    total_count: 0,
    failed_items: []
  }
}

const getEducationStats = () => {
  return userDetail.value?.score_detail?.education_stats || {
    incomplete_count: 0,
    total_count: 0,
    incomplete_items: []
  }
}

const getTrainingStats = () => {
  return userDetail.value?.score_detail?.training_stats || {
    failed_count: 0,
    total_count: 0,
    failed_items: []
  }
}

const getRiskLevel = () => {
  const totalPenalty = parseFloat(getTotalPenalty())
  if (totalPenalty === 0) return 'low'
  if (totalPenalty <= 1.0) return 'medium'
  if (totalPenalty <= 2.0) return 'high'
  return 'critical'
}

const getRiskLevelLabel = () => {
  const level = getRiskLevel()
  const labels = {
    low: '우수',
    medium: '주의',
    high: '위험',
    critical: '매우 위험'
  }
  return labels[level] || '미평가'
}

// Utility Functions
const formatDateTime = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  if (isNaN(date.getTime())) return '-'
  return date.toLocaleString('ko-KR')
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  if (isNaN(date.getTime())) return '-'
  return date.toLocaleDateString('ko-KR')
}

const formatDateRange = (startDate, endDate) => {
  const start = formatDate(startDate)
  const end = formatDate(endDate)
  if (start === '-' && end === '-') return '-'
  return `${start} ~ ${end}`
}

// Lifecycle
onMounted(() => {
  loadUserDetail()
})
</script>

<style scoped>
@import '../styles/AdminUserDetail.css';
</style>
