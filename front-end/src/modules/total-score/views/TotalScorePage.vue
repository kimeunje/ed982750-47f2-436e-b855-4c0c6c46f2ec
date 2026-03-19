<template>
  <div class="score-page">

    <!-- 로딩 상태 -->
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>보안 점수를 계산하는 중...</p>
    </div>

    <!-- 에러 상태 -->
    <div v-else-if="error" class="error-container">
      <div class="error-icon">⚠️</div>
      <h3>점수 계산 실패</h3>
      <p>{{ error }}</p>
      <button @click="fetchSecurityScore" class="retry-button">다시 계산</button>
    </div>

    <!-- 보안 점수 데이터 -->
    <div v-else-if="scoreData" class="score-content">
      <!-- 종합 점수 카드 -->
      <div class="overall-score-card" :class="getRiskLevel()">
        <!-- 연도 선택기 (카드 우측 상단) -->
        <div class="card-year-selector">
          <select v-model="selectedYear" @change="fetchSecurityScore">
            <option v-for="year in availableYears" :key="year" :value="year">{{ year }}년</option>
          </select>
        </div>

        <div class="score-circle">
          <div class="circle-chart" :class="getRiskLevel()">
            <div class="circle-score">
              <span class="score-number">{{ getTotalCount() }}</span>
              <span class="score-unit">건</span>
            </div>
            <div class="circle-grade">총 미흡 건수</div>
          </div>
        </div>

        <div class="score-summary">
          <h2>{{ selectedYear }}년 보안 미흡 현황</h2>
          <p class="score-description">
            <template v-if="getTotalCount() === 0">
              보안 미흡 사항이 없습니다.
            </template>
            <template v-else>
              총 <strong>{{ getTotalCount() }}건</strong>의 보안 미흡 사항이 있습니다.
            </template>
          </p>

          <div v-if="getTotalCount() > 0" class="score-details">
            <div class="detail-item">
              <span class="detail-label">정보보안 감사</span>
              <span class="detail-value" :class="{ 'penalty-active': getAuditTotalCount() > 0 }">
                {{ getAuditTotalCount() }}건
              </span>
            </div>
            <div class="detail-item">
              <span class="detail-label">정보보호 교육</span>
              <span class="detail-value" :class="{ 'penalty-active': getEducationFailCount() > 0 }">
                {{ getEducationFailCount() }}건
              </span>
            </div>
            <div class="detail-item">
              <span class="detail-label">악성메일 모의훈련</span>
              <span class="detail-value" :class="{ 'penalty-active': (scoreData.training_stats?.failed_count || 0) > 0 }">
                {{ scoreData.training_stats?.failed_count || 0 }}건
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 3. 감점 상세 내역 -->
      <div class="score-breakdown">
        <h2>감점 상세 내역</h2>

        <div class="breakdown-grid">
          <!-- ========== 정보보안 감사 (기존 유지) ========== -->
          <div class="breakdown-card audit">
            <div class="card-header">
              <div class="card-icon audit">
                <svg width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
                  <path d="M8 1a2 2 0 0 1 2 2v4H6V3a2 2 0 0 1 2-2zm3 6V3a3 3 0 0 0-6 0v4a2 2 0 0 0-2 2v5a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2z"/>
                </svg>
              </div>
              <h3>정보보안 감사</h3>
            </div>

            <div class="card-content">
              <div class="main-score penalty">{{ getAuditTotalCount() }}건</div>
              <div class="score-detail">
                <p>정기 점검 미흡: {{ scoreData.audit_stats?.failed_count || 0 }}건</p>
                <p>수시 점검 미흡: {{ scoreData.manual_check_stats?.failed_count || 0 }}건</p>
              </div>

              <!-- 상시 감사 항목 -->
              <div v-if="scoreData.audit_stats && scoreData.audit_stats.items?.length > 0" class="penalty-items">
                <h4>📋 정기 점검 항목</h4>
                <div class="penalty-list">
                  <div
                    v-for="item in scoreData.audit_stats.items"
                    :key="item.item_name"
                    class="penalty-item"
                    :class="item.result === 'pass' ? 'pass' : 'fail'"
                  >
                    <div class="item-info">
                      <div class="item-name">{{ item.item_name }}</div>
                      <div class="item-status">
                        {{ item.result === 'pass' ? '✓ 양호' : '✗ 미흡' }}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- items가 없고 failed_items만 있는 경우 (하위 호환성) -->
              <div v-else-if="scoreData.audit_stats?.failed_items?.length > 0" class="penalty-items">
                <h4>📋 미흡 항목</h4>
                <div class="penalty-list">
                  <div
                    v-for="item in scoreData.audit_stats.failed_items"
                    :key="item.item_name"
                    class="penalty-item fail"
                  >
                    <div class="item-info">
                      <div class="item-name">{{ item.item_name }}</div>
                      <div class="item-status">✗ 미흡</div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 수시 점검 항목 -->
              <div v-if="scoreData.manual_check_stats?.items?.length > 0" class="penalty-items">
                <h4>🔍 수시 점검 항목</h4>
                <div class="penalty-list">
                  <div
                    v-for="(item, index) in scoreData.manual_check_stats.items"
                    :key="index"
                    class="penalty-item"
                    :class="item.result"
                  >
                    <div class="item-info">
                      <div class="item-name">{{ item.check_type }}</div>
                      <div class="item-status">{{ item.result === 'pass' ? '✓ 양호' : '✗ 미흡' }}</div>
                    </div>
                  </div>
                </div>
              </div>

            </div>

            <div class="card-footer">
              <router-link to="/security-audit/results" class="detail-link">
                정기 점검 상세 보기 →
              </router-link>
              <router-link 
                v-if="scoreData.manual_check_stats" 
                to="/security-audit/results" 
                class="detail-link"
                style="margin-left: 1rem;"
              >
                수시 점검 상세 보기 →
              </router-link>
            </div>
          </div>

          <!-- ========== 정보보호 교육 (상세 항목 카드 추가) ========== -->
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
              <div class="main-score penalty">
                {{ getEducationFailCount() }}건
              </div>
              <div class="score-detail">
                <p>교육 미수료: {{ getEducationFailCount() }}건</p>
                <p>총 교육 과정: {{ scoreData.education_stats?.total_count || scoreData.education_stats?.total_educations || 0 }}건</p>
              </div>

              <!-- ★ 신규: 과정별 상세 항목 카드 (course_summary 기반) -->
              <div v-if="getEducationCourseList().length > 0" class="penalty-items">
                <h4>📚 교육 과정별 현황</h4>
                <div class="penalty-list">
                  <div
                    v-for="(course, index) in getEducationCourseList()"
                    :key="index"
                    class="penalty-item"
                    :class="course.isPass ? 'pass' : 'fail'"
                  >
                    <div class="item-info">
                      <div class="item-name">{{ course.name }}</div>
                      <div class="item-status">
                        {{ course.isPass ? '✓ 수료' : '✗ 미수료' }}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 레거시: incomplete_periods 문자열 배열 기반 (하위 호환) -->
              <div v-else-if="scoreData.education_stats?.incomplete_periods?.length > 0" class="penalty-items">
                <h4>미완료 교육 목록</h4>
                <div class="penalty-list">
                  <div
                    v-for="(period, index) in scoreData.education_stats.incomplete_periods"
                    :key="index"
                    class="penalty-item fail"
                  >
                    <div class="item-info">
                      <div class="item-name">{{ period }}</div>
                      <div class="item-status">✗ 미완료</div>
                    </div>
                  </div>
                </div>
              </div>

            </div>

            <div class="card-footer">
              <router-link to="/security-education" class="detail-link">
                상세 보기 →
              </router-link>
            </div>
          </div>

          <!-- ========== 악성메일 모의훈련 (상세 항목 카드 추가) ========== -->
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
              <div class="main-score penalty">
                {{ scoreData.training_stats?.failed_count || 0 }}건
              </div>
              <div class="score-detail">
                <p>훈련 미흡: {{ scoreData.training_stats?.failed_count || 0 }}건</p>
                <p>총 훈련: {{ scoreData.training_stats?.total_count || 0 }}건</p>
              </div>

              <!-- ★ 신규: 훈련별 상세 항목 카드 (items 기반) -->
              <div v-if="getTrainingItemList().length > 0" class="penalty-items">
                <h4>🎯 훈련별 현황</h4>
                <div class="penalty-list">
                  <div
                    v-for="(item, index) in getTrainingItemList()"
                    :key="index"
                    class="penalty-item"
                    :class="item.isPass ? 'pass' : 'fail'"
                  >
                    <div class="item-info">
                      <div class="item-name">{{ item.name }}</div>
                      <div class="item-status">
                        {{ item.isPass ? '✓ 양호' : '✗ 미흡' }}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 레거시: failed_periods 문자열 배열 기반 (하위 호환) -->
              <div v-else-if="scoreData.training_stats?.failed_periods?.length > 0" class="penalty-items">
                <h4>미흡 훈련 목록</h4>
                <div class="penalty-list">
                  <div
                    v-for="(period, index) in scoreData.training_stats.failed_periods"
                    :key="index"
                    class="penalty-item fail"
                  >
                    <div class="item-info">
                      <div class="item-name">{{ period }}</div>
                      <div class="item-status">✗ 미흡</div>
                    </div>
                  </div>
                </div>
              </div>

            </div>

            <div class="card-footer">
              <router-link to="/phishing-training" class="detail-link">
                상세 보기 →
              </router-link>
            </div>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// Router와 Store 사용
const router = useRouter()
const authStore = useAuthStore()

// 반응형 데이터
const loading = ref(false)
const error = ref(null)
const scoreData = ref(null)
const selectedYear = ref(new Date().getFullYear())

// 계산된 속성
const availableYears = computed(() => {
  const currentYear = new Date().getFullYear()
  return [currentYear - 1, currentYear, currentYear + 1]
})

// ===== 점수 계산 함수들 =====

const getTotalCount = () => {
  const auditCount = getAuditTotalCount()
  const educationCount = getEducationFailCount()
  const trainingCount = scoreData.value?.training_stats?.failed_count || 0
  return auditCount + educationCount + trainingCount
}

const getAuditTotalCount = () => {
  const auditFailed = scoreData.value?.audit_stats?.failed_count || 0
  const manualFailed = scoreData.value?.manual_check_stats?.failed_count || 0
  return auditFailed + manualFailed
}

const getEducationFailCount = () => {
  return scoreData.value?.education_stats?.periods_with_incomplete ||
         scoreData.value?.education_stats?.incomplete_count || 0
}

const getRiskLevel = () => {
  const totalCount = getTotalCount()
  if (totalCount === 0) return 'low'   // 0건: 우수
  return 'high'                         // 1건+: 위험 (KPI 감점 발생)
}

// ===== ★ 교육 과정 목록 생성 함수 =====
const getEducationCourseList = () => {
  const stats = scoreData.value?.education_stats
  if (!stats) return []

  // 1순위: course_summary 배열 (personal-dashboard API)
  if (stats.course_summary && stats.course_summary.length > 0) {
    return stats.course_summary.map(course => ({
      name: course.course_name || course.education_name || '교육 과정',
      detail: course.completion_rate !== undefined
        ? `수료율 ${course.completion_rate}% (수료 ${course.completed || 0} / 미수료 ${course.incomplete || 0})`
        : null,
      isPass: course.status === '완료' || course.incomplete === 0 || course.incomplete_count === 0
    }))
  }

  // 2순위: incomplete_items 배열 (admin-user-detail API)
  if (stats.incomplete_items && stats.incomplete_items.length > 0) {
    // incomplete_items는 미완료 항목만 포함하므로, 전체 목록을 구성하기 위해
    // passed_educations 수와 합쳐서 표현
    const items = []

    // 미완료 항목 추가
    for (const item of stats.incomplete_items) {
      items.push({
        name: item.course_name || item.education_name || '교육 과정',
        detail: item.completion_rate !== undefined
          ? `수료율 ${item.completion_rate}% (수료 ${item.completed_count || 0} / 미수료 ${item.incomplete_count || 0})`
          : null,
        isPass: false
      })
    }

    return items
  }

  return []
}

// ===== ★ 모의훈련 항목 목록 생성 함수 =====
const getTrainingItemList = () => {
  const stats = scoreData.value?.training_stats
  if (!stats) return []

  // items 배열 (personal-dashboard API)
  if (stats.items && stats.items.length > 0) {
    return stats.items.map(item => ({
      name: item.period || item.period_name || '모의훈련',
      detail: item.training_type || null,
      isPass: item.result === 'success' || item.result === 'pass'
    }))
  }

  return []
}

// ===== API 호출 =====

const callSecurityScoreAPI = async (year) => {
  const response = await fetch(`/api/personal-dashboard/summary?year=${year}`, {
    method: 'GET',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    if (response.status === 401) {
      router.push('/login')
      throw new Error('인증이 필요합니다. 로그인 페이지로 이동합니다.')
    }
    const errorData = await response.json()
    throw new Error(errorData.error || '보안 점수 조회 중 오류가 발생했습니다.')
  }

  return await response.json()
}

// 데이터 로드
const fetchSecurityScore = async () => {
  loading.value = true
  error.value = null

  try {
    const data = await callSecurityScoreAPI(selectedYear.value)
    scoreData.value = data
  } catch (err) {
    console.error('보안 점수 로드 실패:', err)
    error.value = err.message
  } finally {
    loading.value = false
  }
}

// 라이프사이클
onMounted(() => {
  fetchSecurityScore()
})
</script>

<style scoped>
@import '../styles/TotalScorePage.css';

/* 종합 점수 카드 내 연도 선택기 */
.overall-score-card {
  position: relative;
}

.card-year-selector {
  position: absolute;
  top: 1.25rem;
  right: 1.25rem;
  z-index: 1;
}

.card-year-selector select {
  padding: 0.4rem 0.75rem;
  border: 1px solid rgba(255, 255, 255, 0.4);
  border-radius: 6px;
  font-size: 0.85rem;
  background-color: rgba(255, 255, 255, 0.15);
  color: white;
  cursor: pointer;
  transition: all 0.2s ease;
  appearance: none;
  -webkit-appearance: none;
  padding-right: 1.75rem;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' fill='white' viewBox='0 0 16 16'%3E%3Cpath d='M7.247 11.14 2.451 5.658C1.885 5.013 2.345 4 3.204 4h9.592a1 1 0 0 1 .753 1.659l-4.796 5.48a1 1 0 0 1-1.506 0z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 0.5rem center;
}

.card-year-selector select:hover {
  background-color: rgba(255, 255, 255, 0.25);
  border-color: rgba(255, 255, 255, 0.6);
}

.card-year-selector select:focus {
  outline: none;
  background-color: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.8);
}

.card-year-selector select option {
  background-color: #374151;
  color: white;
}
</style>