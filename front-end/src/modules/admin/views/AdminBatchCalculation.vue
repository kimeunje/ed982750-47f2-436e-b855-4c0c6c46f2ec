<!-- AdminBatchCalculation.vue -->
<template>
  <div class="batch-calculation-container">
    <!-- 헤더 -->
    <div class="batch-header">
      <h2>전체 사용자 점수 일괄 계산</h2>
      <p class="batch-description">
        모든 사용자의 보안 점수를 일괄적으로 계산합니다. 로그인하지 않은 사용자의 점수도 자동으로
        계산됩니다.
      </p>
    </div>

    <!-- 통계 카드 -->
    <div class="statistics-cards">
      <div class="stat-card">
        <div class="stat-icon">👥</div>
        <div class="stat-content">
          <h3>전체 사용자</h3>
          <div class="stat-value">{{ statistics.total_users || 0 }}명</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">✅</div>
        <div class="stat-content">
          <h3>계산 완료</h3>
          <div class="stat-value">{{ statistics.calculated_users || 0 }}명</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">⏳</div>
        <div class="stat-content">
          <h3>미계산</h3>
          <div class="stat-value">{{ statistics.uncalculated_users || 0 }}명</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">📊</div>
        <div class="stat-content">
          <h3>계산률</h3>
          <div class="stat-value">{{ statistics.calculation_percentage || 0 }}%</div>
        </div>
      </div>
    </div>

    <!-- 계산 옵션 -->
    <div class="calculation-options">
      <div class="option-group">
        <label for="year-select">계산 연도:</label>
        <select id="year-select" v-model="selectedYear" @change="loadStatistics">
          <option v-for="year in availableYears" :key="year" :value="year">{{ year }}년</option>
        </select>
      </div>

      <div class="option-group">
        <label>
          <input type="checkbox" v-model="forceRecalculate" :disabled="batchStatus.is_running" />
          기존 데이터도 다시 계산 (모든 사용자)
        </label>
      </div>
    </div>

    <!-- 배치 작업 상태 -->
    <div v-if="batchStatus.is_running || batchStatus.end_time" class="batch-status">
      <h3>배치 작업 상태</h3>

      <div class="status-info">
        <div class="status-row">
          <span class="status-label">상태:</span>
          <span class="status-value" :class="getStatusClass()">
            {{ getStatusText() }}
          </span>
        </div>

        <div v-if="batchStatus.current_task" class="status-row">
          <span class="status-label">현재 작업:</span>
          <span class="status-value">{{ batchStatus.current_task }}</span>
        </div>
      </div>

      <!-- 진행률 바 -->
      <div v-if="batchStatus.total > 0" class="progress-section">
        <div class="progress-info">
          <span>{{ batchStatus.progress }} / {{ batchStatus.total }}</span>
          <span>{{ batchStatus.progress_percentage }}%</span>
        </div>
        <div class="progress-bar">
          <div
            class="progress-fill"
            :style="{ width: batchStatus.progress_percentage + '%' }"
          ></div>
        </div>
      </div>

      <!-- 결과 통계 -->
      <div v-if="batchStatus.success_count > 0 || batchStatus.error_count > 0" class="result-stats">
        <div class="result-item success">
          <span class="result-icon">✅</span>
          <span>성공: {{ batchStatus.success_count }}명</span>
        </div>
        <div class="result-item error">
          <span class="result-icon">❌</span>
          <span>실패: {{ batchStatus.error_count }}명</span>
        </div>
      </div>

      <!-- 예상 완료 시간 -->
      <div v-if="batchStatus.estimated_completion && batchStatus.is_running" class="estimated-time">
        예상 완료: {{ formatDateTime(batchStatus.estimated_completion) }}
      </div>

      <!-- 최근 에러 -->
      <div
        v-if="batchStatus.recent_errors && batchStatus.recent_errors.length > 0"
        class="recent-errors"
      >
        <h4>최근 오류</h4>
        <div class="error-list">
          <div v-for="error in batchStatus.recent_errors" :key="error.timestamp" class="error-item">
            <span class="error-user">{{ error.user_id }} ({{ error.username }})</span>
            <span class="error-message">{{ error.error }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 액션 버튼 -->
    <div class="action-buttons">
      <button
        class="btn btn-primary"
        @click="startBatchCalculation"
        :disabled="batchStatus.is_running || loading"
      >
        <span v-if="loading">계산 시작 중...</span>
        <span v-else-if="forceRecalculate">전체 재계산 시작</span>
        <span v-else>미계산 사용자 계산</span>
      </button>

      <button
        v-if="batchStatus.is_running"
        class="btn btn-secondary"
        @click="cancelBatchCalculation"
      >
        작업 취소
      </button>

      <button class="btn btn-outline" @click="refreshStatus" :disabled="loading">
        상태 새로고침
      </button>
    </div>

    <!-- 에러 메시지 -->
    <div v-if="error" class="error-message">
      {{ error }}
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'

// 반응형 상태
const loading = ref(false)
const error = ref(null)
const selectedYear = ref(new Date().getFullYear())
const forceRecalculate = ref(false)

const statistics = reactive({
  total_users: 0,
  calculated_users: 0,
  uncalculated_users: 0,
  calculation_percentage: 0,
  last_calculation_time: null,
})

const batchStatus = reactive({
  is_running: false,
  current_task: null,
  progress: 0,
  total: 0,
  progress_percentage: 0,
  start_time: null,
  end_time: null,
  estimated_completion: null,
  success_count: 0,
  error_count: 0,
  recent_errors: [],
})

// 사용 가능한 연도 목록
const availableYears = ref([])
for (let year = new Date().getFullYear(); year >= 2020; year--) {
  availableYears.value.push(year)
}

// 상태 폴링 인터벌
let statusInterval = null

// API 호출 함수들
const loadStatistics = async () => {
  try {
    const response = await fetch(`/api/admin/batch/statistics?year=${selectedYear.value}`, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('token')}`,
      },
    })

    if (!response.ok) throw new Error('통계 조회 실패')

    const data = await response.json()
    Object.assign(statistics, data)
  } catch (err) {
    console.error('통계 조회 오류:', err)
    error.value = err.message
  }
}

const loadBatchStatus = async () => {
  try {
    const response = await fetch('/api/admin/batch/status', {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('token')}`,
      },
    })

    if (!response.ok) throw new Error('상태 조회 실패')

    const data = await response.json()
    Object.assign(batchStatus, data)

    // 작업이 완료되면 통계 새로고침
    if (!data.is_running && data.end_time && statusInterval) {
      setTimeout(() => {
        loadStatistics()
      }, 1000)
    }
  } catch (err) {
    console.error('상태 조회 오류:', err)
  }
}

const startBatchCalculation = async () => {
  loading.value = true
  error.value = null

  try {
    const response = await fetch('/api/admin/batch/calculate-all-scores', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${localStorage.getItem('token')}`,
      },
      body: JSON.stringify({
        year: selectedYear.value,
        force_recalculate: forceRecalculate.value,
      }),
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.error || '계산 시작 실패')
    }

    const data = await response.json()
    console.log('배치 계산 시작:', data)

    // 상태 폴링 시작
    startStatusPolling()

    // 즉시 상태 업데이트
    setTimeout(loadBatchStatus, 500)
  } catch (err) {
    console.error('배치 계산 시작 오류:', err)
    error.value = err.message
  } finally {
    loading.value = false
  }
}

const cancelBatchCalculation = async () => {
  try {
    const response = await fetch('/api/admin/batch/cancel', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${localStorage.getItem('token')}`,
      },
    })

    if (!response.ok) throw new Error('취소 요청 실패')

    const data = await response.json()
    console.log('배치 작업 취소:', data.message)
  } catch (err) {
    console.error('작업 취소 오류:', err)
    error.value = err.message
  }
}

const refreshStatus = async () => {
  loading.value = true
  try {
    await Promise.all([loadStatistics(), loadBatchStatus()])
  } finally {
    loading.value = false
  }
}

// 상태 폴링 관리
const startStatusPolling = () => {
  if (statusInterval) clearInterval(statusInterval)
  statusInterval = setInterval(loadBatchStatus, 2000) // 2초마다 상태 확인
}

const stopStatusPolling = () => {
  if (statusInterval) {
    clearInterval(statusInterval)
    statusInterval = null
  }
}

// 유틸리티 함수들
const getStatusClass = () => {
  if (batchStatus.is_running) return 'status-running'
  if (batchStatus.end_time) return 'status-completed'
  return 'status-idle'
}

const getStatusText = () => {
  if (batchStatus.is_running) return '실행 중'
  if (batchStatus.end_time) return '완료'
  return '대기'
}

const formatDateTime = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('ko-KR')
}

// 라이프사이클
onMounted(async () => {
  await loadStatistics()
  await loadBatchStatus()

  // 실행 중인 작업이 있으면 폴링 시작
  if (batchStatus.is_running) {
    startStatusPolling()
  }
})

onUnmounted(() => {
  stopStatusPolling()
})
</script>

<style scoped>
.batch-calculation-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.batch-header {
  margin-bottom: 30px;
}

.batch-header h2 {
  color: #333;
  margin-bottom: 10px;
}

.batch-description {
  color: #666;
  font-size: 14px;
}

.statistics-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 15px;
}

.stat-icon {
  font-size: 24px;
}

.stat-content h3 {
  margin: 0 0 5px 0;
  font-size: 14px;
  color: #666;
}

.stat-value {
  font-size: 20px;
  font-weight: bold;
  color: #333;
}

.calculation-options {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 30px;
  display: flex;
  gap: 30px;
  align-items: center;
}

.option-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.option-group label {
  font-weight: 500;
  color: #333;
}

.option-group select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
}

.option-group input[type='checkbox'] {
  margin-right: 8px;
}

.batch-status {
  background: white;
  border: 1px solid #e1e5e9;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 30px;
}

.batch-status h3 {
  margin: 0 0 15px 0;
  color: #333;
}

.status-info {
  margin-bottom: 15px;
}

.status-row {
  display: flex;
  margin-bottom: 8px;
}

.status-label {
  width: 100px;
  font-weight: 500;
  color: #666;
}

.status-value {
  color: #333;
}

.status-value.status-running {
  color: #007bff;
  font-weight: 500;
}

.status-value.status-completed {
  color: #28a745;
  font-weight: 500;
}

.status-value.status-idle {
  color: #6c757d;
}

.progress-section {
  margin: 15px 0;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
  color: #666;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background-color: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background-color: #007bff;
  transition: width 0.3s ease;
}

.result-stats {
  display: flex;
  gap: 20px;
  margin: 15px 0;
}

.result-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 14px;
}

.result-item.success {
  color: #28a745;
}

.result-item.error {
  color: #dc3545;
}

.result-icon {
  font-size: 16px;
}

.estimated-time {
  margin: 10px 0;
  padding: 10px;
  background: #e7f3ff;
  border-left: 4px solid #007bff;
  font-size: 14px;
  color: #004085;
}

.recent-errors {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #e1e5e9;
}

.recent-errors h4 {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: #dc3545;
}

.error-list {
  max-height: 150px;
  overflow-y: auto;
}

.error-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 8px;
  background: #fff5f5;
  border: 1px solid #fed7d7;
  border-radius: 4px;
  margin-bottom: 5px;
  font-size: 12px;
}

.error-user {
  font-weight: 500;
  color: #742a2a;
}

.error-message {
  color: #e53e3e;
}

.action-buttons {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
}

.btn {
  padding: 12px 24px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: #007bff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #0056b3;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background: #545b62;
}

.btn-outline {
  background: transparent;
  color: #007bff;
  border: 1px solid #007bff;
}

.btn-outline:hover:not(:disabled) {
  background: #007bff;
  color: white;
}

.error-message {
  background: #f8d7da;
  color: #721c24;
  padding: 12px;
  border: 1px solid #f5c6cb;
  border-radius: 4px;
  margin-top: 10px;
}

@media (max-width: 768px) {
  .statistics-cards {
    grid-template-columns: repeat(2, 1fr);
  }

  .calculation-options {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }

  .action-buttons {
    flex-direction: column;
  }

  .result-stats {
    flex-direction: column;
    gap: 10px;
  }
}
</style>
