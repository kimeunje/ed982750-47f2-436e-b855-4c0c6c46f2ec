<template>
  <div class="admin-dashboard">
    <!-- 헤더 -->
    <div class="admin-header">
      <h1>관리자 대시보드</h1>
      <p>전체 사용자 보안 현황 및 통계를 확인하고 관리하세요</p>

      <!-- 년도 선택 및 컨트롤 -->
      <div class="header-controls">
        <div class="year-selector">
          <label>평가 년도:</label>
          <select v-model="selectedYear" @change="loadDashboardData">
            <option v-for="year in availableYears" :key="year" :value="year">{{ year }}년</option>
          </select>
        </div>
        <div class="action-buttons">
          <button @click="refreshData" class="refresh-btn" :disabled="loading">
            <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
              <path
                d="M11.534 7h3.932a.25.25 0 0 1 .192.41l-1.966 2.36a.25.25 0 0 1-.384 0l-1.966-2.36a.25.25 0 0 1 .192-.41zm-11 2h3.932a.25.25 0 0 0 .192-.41L2.692 6.23a.25.25 0 0 0-.384 0L.342 8.59A.25.25 0 0 0 .534 9z"
              />
              <path
                d="M8 3c-1.552 0-2.94.707-3.857 1.818a.5.5 0 1 1-.771-.636A6.002 6.002 0 0 1 13.917 7H12.9A5.002 5.002 0 0 0 8 3zM3.1 9a5.002 5.002 0 0 0 8.757 2.182.5.5 0 1 1 .771.636A6.002 6.002 0 0 1 2.083 9H3.1z"
              />
            </svg>
            새로고침
          </button>
          <button @click="exportItemDetails" :disabled="loading" class="export-btn item-detail">
            <span>📋 항목별 내보내기</span>
          </button>
          <!-- ✅ 새로 추가: 정규화 내보내기 버튼 -->
          <button @click="exportItemNormalized" :disabled="loading" class="export-btn normalized">
            <span class="btn-icon">✓</span>
            <span>정규화 내보내기</span>
          </button>
          <button @click="exportSummary" class="export-btn" :disabled="loading">
            <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
              <path
                d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"
              />
              <path
                d="M7.646 1.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1-.708.708L8.5 2.707V11.5a.5.5 0 0 1-1 0V2.707L5.354 4.854a.5.5 0 1 1-.708-.708l3-3z"
              />
            </svg>
            데이터 내보내기
          </button>
        </div>
      </div>
    </div>

    <!-- 로딩 상태 -->
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>데이터를 불러오는 중...</p>
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
      <button @click="loadDashboardData" class="retry-btn">다시 시도</button>
    </div>

    <!-- 대시보드 콘텐츠 -->
    <div v-else-if="dashboardData" class="dashboard-content">
      <!-- 1. 전체 통계 카드 -->
      <div class="stats-grid">
        <div class="stat-card total-users">
          <div class="stat-icon">
            <svg width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
              <path
                d="M15 14s1 0 1-1-1-4-5-4-5 3-5 4 1 1 1 1h8Zm-7.978-1A.261.261 0 0 1 7 12.996c.001-.264.167-1.03.76-1.72C8.312 10.629 9.282 10 11 10c1.717 0 2.687.63 3.24 1.276.593.69.758 1.457.76 1.72l-.008.002A.274.274 0 0 1 15 13H7ZM11 7a2 2 0 1 0 0-4 2 2 0 0 0 0 4Zm3-2a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z"
              />
            </svg>
          </div>
          <div class="stat-content">
            <h3>전체 사용자</h3>
            <div class="stat-value">
              {{ formatNumber(dashboardData.user_stats?.total_users || 0) }}
            </div>
            <div class="stat-detail">
              평가완료: {{ formatNumber(dashboardData.user_stats?.evaluated_users || 0) }}명
            </div>
          </div>
        </div>

        <div class="stat-card excellent-users">
          <div class="stat-icon">
            <svg width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
              <path
                d="M3.612 15.443c-.386.198-.824-.149-.746-.592l.83-4.73L.173 6.765c-.329-.314-.158-.888.283-.95l4.898-.696L7.538.792c.197-.39.73-.39.927 0l2.184 4.327 4.898.696c.441.062.612.636.282.95l-3.522 3.356.83 4.73c.078.443-.36.79-.746.592L8 13.187l-4.389 2.256z"
              />
            </svg>
          </div>
          <div class="stat-content">
            <h3>우수 사용자</h3>
            <div class="stat-value excellent">
              {{ formatNumber(dashboardData.user_stats?.excellent_users || 0) }}
            </div>
            <div class="stat-detail">
              {{
                calculatePercentage(
                  dashboardData.user_stats?.excellent_users,
                  dashboardData.user_stats?.total_users,
                )
              }}%
            </div>
          </div>
        </div>

        <div class="stat-card warning-users">
          <div class="stat-icon">
            <svg width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
              <path
                d="M8.982 1.566a1.13 1.13 0 0 0-1.96 0L.165 13.233c-.457.778.091 1.767.98 1.767h13.713c.889 0 1.438-.99.98-1.767L8.982 1.566zM8 5c.535 0 .954.462.9.995l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 5.995A.905.905 0 0 1 8 5zm.002 6a1 1 0 1 1 0 2 1 1 0 0 1 0-2z"
              />
            </svg>
          </div>
          <div class="stat-content">
            <h3>주의 사용자</h3>
            <div class="stat-value warning">
              {{ formatNumber(dashboardData.user_stats?.warning_users || 0) }}
            </div>
            <div class="stat-detail">
              {{
                calculatePercentage(
                  dashboardData.user_stats?.warning_users,
                  dashboardData.user_stats?.total_users,
                )
              }}%
            </div>
          </div>
        </div>

        <div class="stat-card critical-users">
          <div class="stat-icon">
            <svg width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
              <path
                d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM5.354 4.646a.5.5 0 1 0-.708.708L7.293 8l-2.647 2.646a.5.5 0 0 0 .708.708L8 8.707l2.646 2.647a.5.5 0 0 0 .708-.708L8.707 8l2.647-2.646a.5.5 0 0 0-.708-.708L8 7.293 5.354 4.646z"
              />
            </svg>
          </div>
          <div class="stat-content">
            <h3>위험 사용자</h3>
            <div class="stat-value critical">
              {{ formatNumber(dashboardData.user_stats?.critical_users || 0) }}
            </div>
            <div class="stat-detail">
              {{
                calculatePercentage(
                  dashboardData.user_stats?.critical_users,
                  dashboardData.user_stats?.total_users,
                )
              }}%
            </div>
          </div>
        </div>

        <div class="stat-card avg-penalty">
          <div class="stat-icon">
            <svg width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
              <path
                d="M1 2.828c.885-.37 2.154-.769 3.388-.893 1.33-.134 2.458.063 3.112.752v9.746c-.935-.53-2.12-.603-3.213-.493-1.18.12-2.37.461-3.287.811V2.828zm7.5-.141c.654-.689 1.782-.886 3.112-.752 1.234.124 2.503.523 3.388.893v9.923c-.918-.35-2.107-.692-3.287-.81-1.094-.111-2.278-.039-3.213.492V2.687zM8 1.783C7.015.936 5.587.81 4.287.94c-1.514.153-3.042.672-3.994 1.105A.5.5 0 0 0 0 2.5v11a.5.5 0 0 0 .707.455c.882-.4 2.303-.881 3.68-1.02 1.409-.142 2.59.087 3.223.877a.5.5 0 0 0 .78 0c.633-.79 1.814-1.019 3.222-.877 1.378.139 2.8.62 3.681 1.02A.5.5 0 0 0 16 13.5v-11a.5.5 0 0 0-.293-.455c-.952-.433-2.48-.952-3.994-1.105C10.413.809 8.985.936 8 1.783z"
              />
            </svg>
          </div>
          <div class="stat-content">
            <h3>평균 감점</h3>
            <div class="stat-value">
              {{ formatDecimal(dashboardData.user_stats?.avg_penalty || 0) }}
            </div>
            <div class="stat-detail">
              최대: {{ formatDecimal(dashboardData.user_stats?.max_penalty || 0) }}점
            </div>
          </div>
        </div>
      </div>

      <!-- 2. 차트 및 분석 섹션 -->
      <div class="charts-row">
        <!-- 보안 점수 분포 차트 -->
        <div class="chart-section">
          <div class="section-header">
            <h3>보안 점수 분포</h3>
            <div class="chart-controls">
              <button @click="toggleChartType" class="chart-type-btn">
                {{ chartType === 'pie' ? '막대차트' : '원형차트' }}
              </button>
            </div>
          </div>
          <div class="chart-container">
            <div class="score-distribution-chart">
              <!-- 점수 분포 데이터 표시 -->
              <div v-if="dashboardData.score_distribution?.length" class="distribution-grid">
                <div
                  v-for="item in dashboardData.score_distribution"
                  :key="item.score_range"
                  class="distribution-item"
                  :class="item.score_range"
                >
                  <div class="range-label">{{ getRangeLabel(item.score_range) }}</div>
                  <div class="range-count">{{ item.user_count }}명</div>
                  <div class="range-percentage">{{ formatDecimal(item.percentage) }}%</div>
                </div>
              </div>
              <div v-else class="no-data">데이터가 없습니다.</div>
            </div>
          </div>
        </div>

        <!-- 월별 트렌드 -->
        <div class="trend-section">
          <div class="section-header">
            <h3>월별 트렌드</h3>
            <select v-model="trendMetric" @change="updateTrendChart" class="trend-select">
              <option value="failure_rate">실패율</option>
              <option value="active_users">활성 사용자</option>
              <option value="total_checks">전체 점검</option>
            </select>
          </div>
          <div class="trend-chart">
            <div v-if="dashboardData.monthly_trends?.length" class="trend-data">
              <div
                v-for="trend in dashboardData.monthly_trends"
                :key="trend.month"
                class="trend-month"
              >
                <div class="month-label">{{ trend.month }}월</div>
                <div class="trend-value">
                  <span v-if="trendMetric === 'failure_rate'"
                    >{{ formatDecimal(trend.failure_rate) }}%</span
                  >
                  <span v-else-if="trendMetric === 'active_users'">{{ trend.active_users }}명</span>
                  <span v-else>{{ trend.total_checks }}건</span>
                </div>
              </div>
            </div>
            <div v-else class="no-data">트렌드 데이터가 없습니다.</div>
          </div>
        </div>
      </div>

      <!-- 3. 부서별/직급별 현황 -->
      <div class="overview-sections">
        <!-- 부서별 현황 -->
        <div class="department-section">
          <div class="section-header">
            <h3>부서별 현황</h3>
            <button @click="exportDepartmentData" class="export-btn">
              <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                <path
                  d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"
                />
                <path
                  d="M7.646 1.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1-.708.708L8.5 2.707V11.5a.5.5 0 0 1-1 0V2.707L5.354 4.854a.5.5 0 1 1-.708-.708l3-3z"
                />
              </svg>
              내보내기
            </button>
          </div>
          <div class="department-grid">
            <div
              v-for="dept in dashboardData.department_overview"
              :key="dept.department"
              class="department-card"
            >
              <div class="dept-header">
                <h4>{{ dept.department }}</h4>
                <span class="user-count">{{ formatNumber(dept.total_users) }}명</span>
              </div>
              <div class="dept-stats">
                <div class="stat-row">
                  <span class="label">평균 감점:</span>
                  <span class="value" :class="getPenaltyClass(dept.avg_penalty)">
                    {{ formatDecimal(dept.avg_penalty) }}점
                  </span>
                </div>
                <div class="dept-distribution">
                  <div class="dist-item excellent">
                    <span class="count">{{ dept.excellent_count }}</span>
                    <span class="label">우수</span>
                  </div>
                  <div class="dist-item warning">
                    <span class="count">{{ dept.warning_count }}</span>
                    <span class="label">주의</span>
                  </div>
                  <div class="dist-item critical">
                    <span class="count">{{ dept.critical_count }}</span>
                    <span class="label">위험</span>
                  </div>
                </div>
                <div class="excellent-rate">우수율: {{ formatDecimal(dept.excellent_rate) }}%</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 직급별 현황 -->
        <div class="position-section">
          <div class="section-header">
            <h3>직급별 현황</h3>
          </div>
          <div class="position-table">
            <table>
              <thead>
                <tr>
                  <th>직급</th>
                  <th>인원</th>
                  <th>평균 감점</th>
                  <th>우수율</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="pos in dashboardData.position_overview" :key="pos.position">
                  <td class="position-name">{{ pos.position }}</td>
                  <td>{{ formatNumber(pos.total_users) }}</td>
                  <td :class="getPenaltyClass(pos.avg_penalty)">
                    {{ formatDecimal(pos.avg_penalty) }}점
                  </td>
                  <td>{{ calculatePercentage(pos.excellent_count, pos.total_users) }}%</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- 4. 위험 사용자 및 최근 활동 -->
      <div class="activity-sections">
        <!-- 위험 사용자 -->
        <div class="risk-users-section">
          <div class="section-header">
            <h3>위험 사용자 목록</h3>
            <RouterLink to="/admin/users?risk_level=high" class="view-all-btn">
              전체 보기
            </RouterLink>
          </div>
          <div class="risk-users-list">
            <div
              v-for="user in dashboardData.risk_users"
              :key="user.uid"
              class="risk-user-card"
              @click="viewUserDetail(user.uid)"
            >
              <div class="user-info">
                <div class="user-name">{{ user.name }}</div>
                <div class="user-details">{{ user.department }} · {{ user.position }}</div>
              </div>
              <div class="user-risk">
                <div class="risk-level" :class="user.risk_level">
                  {{ getRiskLevelLabel(user.risk_level) }}
                </div>
                <div class="penalty-score">{{ formatDecimal(user.total_penalty) }}점</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 최근 활동 -->
        <div class="recent-activities-section">
          <div class="section-header">
            <h3>최근 활동</h3>
            <select v-model="activityFilter" @change="filterActivities" class="activity-filter">
              <option value="all">전체</option>
              <option value="success">성공</option>
              <option value="failure">실패</option>
              <option value="pending">대기</option>
            </select>
          </div>
          <div class="activities-list">
            <div
              v-for="activity in filteredActivities"
              :key="`${activity.activity_type}-${activity.activity_time}`"
              class="activity-item"
            >
              <div class="activity-icon" :class="activity.status">
                <svg
                  v-if="activity.status === 'success'"
                  width="16"
                  height="16"
                  fill="currentColor"
                  viewBox="0 0 16 16"
                >
                  <path
                    d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"
                  />
                </svg>
                <svg
                  v-else-if="activity.status === 'failure'"
                  width="16"
                  height="16"
                  fill="currentColor"
                  viewBox="0 0 16 16"
                >
                  <path
                    d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM5.354 4.646a.5.5 0 1 0-.708.708L7.293 8l-2.647 2.646a.5.5 0 0 0 .708.708L8 8.707l2.646 2.647a.5.5 0 0 0 .708-.708L8.707 8l2.647-2.646a.5.5 0 0 0-.708-.708L8 7.293 5.354 4.646z"
                  />
                </svg>
                <svg v-else width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                  <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z" />
                </svg>
              </div>
              <div class="activity-content">
                <div class="activity-description">
                  <strong>{{ activity.user_name }}</strong> · {{ activity.department }}
                  <br />
                  {{ activity.activity_description }}
                </div>
                <div class="activity-time">
                  {{ formatDateTime(activity.activity_time) }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 5. 빠른 액션 버튼들 -->
      <div class="quick-actions">
        <div class="section-header">
          <h3>빠른 작업</h3>
        </div>
        <div class="action-buttons-grid">
          <RouterLink to="/admin/users" class="action-button">
            <svg width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
              <path
                d="M15 14s1 0 1-1-1-4-5-4-5 3-5 4 1 1 1 1h8Zm-7.978-1A.261.261 0 0 1 7 12.996c.001-.264.167-1.03.76-1.72C8.312 10.629 9.282 10 11 10c1.717 0 2.687.63 3.24 1.276.593.69.758 1.457.76 1.72l-.008.002A.274.274 0 0 1 15 13H7Z"
              />
            </svg>
            <span>사용자 관리</span>
          </RouterLink>

          <RouterLink to="/admin/training" class="action-button">
            <svg width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
              <path
                d="M8.5 5a.5.5 0 0 0-1 0v1.5H6a.5.5 0 0 0 0 1h1.5V9a.5.5 0 0 0 1 0V7.5H10a.5.5 0 0 0 0-1H8.5V5z"
              />
              <path
                d="M2 2a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v13.5a.5.5 0 0 1-.777.416L8 13.101l-5.223 2.815A.5.5 0 0 1 2 15.5V2zm2-1a1 1 0 0 0-1 1v12.566l4.723-2.482a.5.5 0 0 1 .554 0L13 14.566V2a1 1 0 0 0-1-1H4z"
              />
            </svg>
            <span>모의훈련 관리</span>
          </RouterLink>

          <RouterLink to="/admin/exceptions" class="action-button">
            <svg width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
              <path
                d="M9.405 1.05c-.413-1.4-2.397-1.4-2.81 0l-.1.34a1.464 1.464 0 0 1-2.105.872l-.31-.17c-1.283-.698-2.686.705-1.987 1.987l.169.311c.446.82.023 1.841-.872 2.105l-.34.1c-1.4.413-1.4 2.397 0 2.81l.34.1a1.464 1.464 0 0 1 .872 2.105l-.17.31c-.698 1.283.705 2.686 1.987 1.987l.311-.169a1.464 1.464 0 0 1 2.105.872l.1.34c.413 1.4 2.397 1.4 2.81 0l.1-.34a1.464 1.464 0 0 1 2.105-.872l.31.17c1.283.698 2.686-.705 1.987-1.987l-.169-.311a1.464 1.464 0 0 1 .872-2.105l.34-.1c1.4-.413 1.4-2.397 0-2.81l-.34-.1a1.464 1.464 0 0 1-.872-2.105l.17-.31c.698-1.283-.705-2.686-1.987-1.987l-.311.169a1.464 1.464 0 0 1-2.105-.872l-.1-.34zM8 10.93a2.929 2.929 0 1 1 0-5.86 2.929 2.929 0 0 1 0 5.858z"
              />
            </svg>
            <span>예외 관리</span>
          </RouterLink>

          <button @click="exportDetailed" class="action-button">
            <svg width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
              <path
                d="M14 14V4.5L9.5 0H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2zM9.5 3A1.5 1.5 0 0 0 11 4.5h2V14a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1h5.5v2z"
              />
            </svg>
            <span>상세 보고서</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// 상태 관리
const loading = ref(false)
const error = ref('')
const selectedYear = ref(new Date().getFullYear())
const chartType = ref('pie')
const trendMetric = ref('failure_rate')
const activityFilter = ref('all')
const dashboardData = ref(null)

// 스토어
const authStore = useAuthStore()
const router = useRouter()

// 사용 가능한 년도 목록
const availableYears = computed(() => {
  const currentYear = new Date().getFullYear()
  const years = []
  for (let i = currentYear; i >= currentYear - 5; i--) {
    years.push(i)
  }
  return years
})

// 필터링된 활동 목록
const filteredActivities = computed(() => {
  if (!dashboardData.value?.recent_activities) return []

  if (activityFilter.value === 'all') {
    return dashboardData.value.recent_activities
  }

  return dashboardData.value.recent_activities.filter(
    (activity) => activity.status === activityFilter.value,
  )
})
// API 객체에 새로운 함수들 추가
const adminAPI = {
  async getDashboardOverview(year, autoCalculate = true) {
    const response = await fetch(
      `/api/admin/dashboard/overview?year=${year}&auto_calculate=${autoCalculate}`,
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

  async getCalculationStatus(year) {
    const response = await fetch(`/api/admin/dashboard/calculation-status?year=${year}`, {
      headers: {
        Authorization: `Bearer ${authStore.token}`,
      },
    })

    if (!response.ok) {
      throw new Error(`상태 조회 실패: ${response.status}`)
    }

    return await response.json()
  },

  async triggerFullCalculation(year, forceRecalculate = false) {
    const response = await fetch('/api/admin/dashboard/trigger-calculation', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${authStore.token}`,
      },
      body: JSON.stringify({
        year: year,
        force_recalculate: forceRecalculate,
      }),
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.error || `계산 실행 실패: ${response.status}`)
    }

    return await response.json()
  },

  // 기존 exportData 함수는 그대로 유지
  async exportData(exportType, format = 'csv') {
    const response = await fetch(
      `/api/admin/dashboard/export?year=${selectedYear.value}&type=${exportType}&format=${format}`,
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

// 대시보드 로드 함수 수정 - 자동 계산 비활성화
async function loadDashboardData() {
  if (!authStore.isAuthenticated || !isAdmin()) {
    router.push('/login')
    return
  }

  loading.value = true
  error.value = ''

  try {
    console.log(`관리자 대시보드 데이터 로드: ${selectedYear.value}년`)

    // 자동 계산 비활성화 - 수동으로만 계산하도록 변경
    const data = await adminAPI.getDashboardOverview(selectedYear.value, false) // auto_calculate=false

    dashboardData.value = data
    console.log('대시보드 데이터 로드 완료:', data)
  } catch (err) {
    console.error('대시보드 데이터 로드 실패:', err)
    error.value = err.message || '데이터를 불러오는데 실패했습니다.'
  } finally {
    loading.value = false

    // 로딩 메시지 제거
    const loader = document.querySelector('.refresh-loader')
    if (loader) {
      loader.remove()
    }
  }
}

// 새로고침 함수 수정 - 옵션 제공
async function refreshData() {
  loading.value = true
  error.value = ''

  try {
    console.log('데이터 새로고침 시작...')

    // 사용자에게 새로고침 방식 선택 옵션 제공
    const choice = await showRefreshOptions()

    if (choice === 'cancel') {
      return // 사용자가 취소한 경우
    }

    if (choice === 'force_all') {
      // 모든 사용자 강제 재계산
      await forceRecalculateAll()
    } else {
      // 기본 새로고침 (미계산 사용자만)
      await refreshDataOnly()
    }

    // 대시보드 데이터 새로고침
    await loadDashboardData()

    showSuccess('데이터 새로고침이 완료되었습니다.')
  } catch (err) {
    console.error('새로고침 중 오류:', err)
    error.value = err.message || '새로고침 중 오류가 발생했습니다.'
  } finally {
    loading.value = false
  }
}

// 모든 사용자 강제 재계산
async function forceRecalculateAll() {
  try {
    showLoadingMessage('모든 사용자의 점수를 재계산하고 있습니다...')

    // 서버에 강제 재계산 요청
    const response = await adminAPI.triggerFullCalculation(selectedYear.value, true) // force_recalculate=true

    console.log('전체 재계산 완료:', response)

    if (response.calculated_count) {
      showSuccess(`${response.calculated_count}명의 사용자 점수가 재계산되었습니다.`)
    }
  } catch (err) {
    console.error('전체 재계산 실패:', err)
    throw new Error(`전체 재계산 실패: ${err.message}`)
  }
}

// 로딩 메시지 표시
function showLoadingMessage(message) {
  // 기존 로딩 메시지 제거
  const existingLoader = document.querySelector('.refresh-loader')
  if (existingLoader) {
    existingLoader.remove()
  }

  const loader = document.createElement('div')
  loader.className = 'refresh-loader'
  loader.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background: #3b82f6;
    color: white;
    padding: 12px 20px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    z-index: 1000;
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 14px;
    max-width: 350px;
  `

  loader.innerHTML = `
    <div style="
      width: 20px;
      height: 20px;
      border: 2px solid rgba(255,255,255,0.3);
      border-top: 2px solid white;
      border-radius: 50%;
      animation: spin 1s linear infinite;
    "></div>
    <span>${message}</span>
  `

  // 스피너 애니메이션 CSS 추가
  if (!document.querySelector('#spinner-style')) {
    const style = document.createElement('style')
    style.id = 'spinner-style'
    style.textContent = `
      @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
      }
    `
    document.head.appendChild(style)
  }

  document.body.appendChild(loader)

  // 30초 후 자동 제거
  setTimeout(() => {
    if (loader.parentNode) {
      loader.parentNode.removeChild(loader)
    }
  }, 30000)
}

// 데이터만 새로고침 (기존 로직)
async function refreshDataOnly() {
  try {
    showLoadingMessage('데이터를 새로고침하고 있습니다...')

    // 계산 상태 확인
    const statusResponse = await adminAPI.getCalculationStatus(selectedYear.value)
    console.log('계산 상태:', statusResponse)

    // 미계산 사용자가 있으면 자동 계산
    if (statusResponse.missing_users > 0) {
      console.log(`${statusResponse.missing_users}명의 미계산 사용자 자동 계산`)
      await adminAPI.triggerFullCalculation(selectedYear.value, false) // 미계산만
    }
  } catch (err) {
    console.error('데이터 새로고침 실패:', err)
    throw new Error(`데이터 새로고침 실패: ${err.message}`)
  }
}

// 새로고침 옵션 선택 대화상자
function showRefreshOptions() {
  return new Promise((resolve) => {
    // 커스텀 대화상자 HTML 생성
    const modal = document.createElement('div')
    modal.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.5);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 10000;
    `

    const dialog = document.createElement('div')
    dialog.style.cssText = `
      background: white;
      padding: 30px;
      border-radius: 12px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
      max-width: 500px;
      width: 90%;
    `

    dialog.innerHTML = `
      <h3 style="margin: 0 0 20px 0; color: #1f2937; font-size: 20px;">새로고침 방식 선택</h3>
      <p style="margin: 0 0 25px 0; color: #6b7280; line-height: 1.5;">
        데이터를 어떻게 새로고침하시겠습니까?
      </p>

      <div style="display: flex; flex-direction: column; gap: 15px; margin-bottom: 25px;">
        <button id="refreshOnly" style="
          padding: 12px 16px;
          border: 2px solid #e5e7eb;
          border-radius: 8px;
          background: white;
          cursor: pointer;
          text-align: left;
          transition: all 0.2s;
        ">
          <div style="font-weight: 600; color: #1f2937; margin-bottom: 4px;">📊 데이터만 새로고침</div>
          <div style="font-size: 14px; color: #6b7280;">기존 점수는 유지하고 대시보드 데이터만 갱신</div>
        </button>

        <button id="forceAll" style="
          padding: 12px 16px;
          border: 2px solid #fbbf24;
          border-radius: 8px;
          background: #fffbeb;
          cursor: pointer;
          text-align: left;
          transition: all 0.2s;
        ">
          <div style="font-weight: 600; color: #92400e; margin-bottom: 4px;">🔄 모든 사용자 점수 재계산</div>
          <div style="font-size: 14px; color: #92400e;">모든 사용자의 점수를 처음부터 다시 계산 (시간 소요)</div>
        </button>
      </div>

      <div style="display: flex; gap: 10px; justify-content: flex-end;">
        <button id="cancel" style="
          padding: 8px 16px;
          border: 1px solid #d1d5db;
          border-radius: 6px;
          background: white;
          cursor: pointer;
          color: #6b7280;
        ">취소</button>
      </div>
    `

    modal.appendChild(dialog)
    document.body.appendChild(modal)

    // 버튼 이벤트 등록
    dialog.querySelector('#refreshOnly').onclick = () => {
      document.body.removeChild(modal)
      resolve('refresh_only')
    }

    dialog.querySelector('#forceAll').onclick = () => {
      document.body.removeChild(modal)
      resolve('force_all')
    }

    dialog.querySelector('#cancel').onclick = () => {
      document.body.removeChild(modal)
      resolve('cancel')
    }

    // 호버 효과
    const buttons = dialog.querySelectorAll('button')
    buttons.forEach((btn) => {
      if (btn.id === 'refreshOnly' || btn.id === 'forceAll') {
        btn.onmouseenter = () => {
          btn.style.transform = 'translateY(-2px)'
          btn.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.1)'
        }
        btn.onmouseleave = () => {
          btn.style.transform = 'translateY(0)'
          btn.style.boxShadow = 'none'
        }
      }
    })
  })
}

// 배치 작업 완료 대기 함수 (새로 추가)
async function waitForBatchCompletion() {
  const maxWaitTime = 30000 // 30초
  const checkInterval = 2000 // 2초마다 확인
  const startTime = Date.now()

  while (Date.now() - startTime < maxWaitTime) {
    try {
      const statusResponse = await fetch('/api/admin/batch/status', {
        headers: {
          Authorization: `Bearer ${authStore.token}`,
        },
      })

      if (statusResponse.ok) {
        const status = await statusResponse.json()

        if (!status.is_running) {
          console.log(
            `배치 작업 완료: 성공 ${status.success_count}명, 실패 ${status.error_count}명`,
          )
          break
        }
      }

      // 2초 대기
      await new Promise((resolve) => setTimeout(resolve, checkInterval))
    } catch (err) {
      console.error('배치 상태 확인 중 오류:', err)
      break
    }
  }
}

function toggleChartType() {
  chartType.value = chartType.value === 'pie' ? 'bar' : 'pie'
}

function updateTrendChart() {
  // 트렌드 차트 업데이트 로직
  console.log('트렌드 메트릭 변경:', trendMetric.value)
}

function filterActivities() {
  // 활동 필터링은 computed로 자동 처리됨
  console.log('활동 필터 변경:', activityFilter.value)
}

// 유틸리티 함수들
function formatNumber(num) {
  return new Intl.NumberFormat('ko-KR').format(num || 0)
}

function formatDecimal(num, decimals = 1) {
  return parseFloat(num || 0).toFixed(decimals)
}

function calculatePercentage(value, total) {
  if (!total || total === 0) return '0.0'
  return ((value / total) * 100).toFixed(1)
}

function formatDateTime(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('ko-KR', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// 위험도 및 감점 관련 함수들
function getRiskLevelColor(level) {
  const colors = {
    low: '#10b981',
    medium: '#f59e0b',
    high: '#ef4444',
    critical: '#dc2626',
    not_evaluated: '#6b7280',
  }
  return colors[level] || '#6b7280'
}

function getRiskLevelLabel(level) {
  const labels = {
    low: '낮음',
    medium: '보통',
    high: '높음',
    critical: '매우 높음',
    not_evaluated: '미평가',
  }
  return labels[level] || '알 수 없음'
}

function getPenaltyClass(penalty) {
  const penaltyNum = parseFloat(penalty || 0)
  if (penaltyNum <= 0.5) return 'penalty-low'
  if (penaltyNum <= 2.0) return 'penalty-medium'
  return 'penalty-high'
}

function getRangeLabel(range) {
  const labels = {
    perfect: '완벽 (0점)',
    excellent: '우수 (0.5점 이하)',
    good: '양호 (1.0점 이하)',
    warning: '주의 (2.0점 이하)',
    danger: '위험 (3.0점 이하)',
    critical: '매우 위험 (3.0점 초과)',
    not_evaluated: '미평가',
  }
  return labels[range] || range
}

// 사용자 관련 함수들
async function viewUserDetail(userId) {
  router.push(`/admin/users/${userId}/detail`)
}

function isAdmin() {
  const userRole = authStore.user?.role || 'user'
  return userRole === 'admin' || authStore.user?.username === 'admin'
}

async function exportSummary() {
  try {
    loading.value = true
    
    console.log('전체 사용자 데이터 내보내기 시작...');
    
    // 전체 사용자 데이터 내보내기 API 호출
    const params = new URLSearchParams({
      year: selectedYear.value,
      format: 'csv'
    });

    const response = await fetch(`/api/admin/dashboard/export?${params}`, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${authStore.token}`,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
    }

    // 파일 다운로드 처리
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    
    // 파일명: 종합보안점수_전체사용자_2025년_20250122.csv
    const today = new Date().toISOString().split('T')[0].replace(/-/g, '');
    a.download = `종합보안점수_전체사용자_${selectedYear.value}년_${today}.csv`
    
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
    
    console.log('데이터 내보내기 완료');
    showSuccess(`${selectedYear.value}년 전체 사용자 데이터가 성공적으로 내보내졌습니다.`)
  } catch (err) {
    console.error('요약 데이터 내보내기 실패:', err)
    error.value = `데이터 내보내기에 실패했습니다: ${err.message}`
  } finally {
    loading.value = false
  }
}

// 2. 항목별 상세 내보내기 (신규)
async function exportItemDetails() {
  try {
    loading.value = true
    const params = new URLSearchParams({
      year: selectedYear.value,
      format: 'csv',
      mode: 'item_count'  // 핵심!
    });

    const response = await fetch(`/api/admin/dashboard/export?${params}`, {
      method: 'GET',
      headers: { Authorization: `Bearer ${authStore.token}` }
    });

    if (!response.ok) throw new Error('내보내기 실패');

    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `사용자_보안현황_항목별_${selectedYear.value}년.csv`
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
    
    showSuccess('항목별 상세 보고서가 성공적으로 내보내졌습니다.')
  } catch (err) {
    error.value = `항목별 데이터 내보내기에 실패했습니다: ${err.message}`
  } finally {
    loading.value = false
  }
}

async function exportItemNormalized() {
  try {
    loading.value = true
    
    console.log('항목별 정규화 데이터 내보내기 시작...');
    
    // mode=normalized 파라미터 추가
    const params = new URLSearchParams({
      year: selectedYear.value,
      format: 'csv',
      mode: 'normalized'  // 정규화 모드
    });

    // 현재 적용된 필터가 있다면 추가
    if (dashboardData.value?.filters) {
      const filters = dashboardData.value.filters;
      if (filters.department) params.append('department', filters.department);
      if (filters.risk_level) params.append('risk_level', filters.risk_level);
      if (filters.search) params.append('search', filters.search);
    }

    const response = await fetch(`/api/admin/dashboard/export?${params}`, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${authStore.token}`,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
    }

    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    
    const today = new Date().toISOString().split('T')[0].replace(/-/g, '');
    a.download = `사용자_보안현황_정규화_${selectedYear.value}년_${today}.csv`
    
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
    
    console.log('항목별 정규화 데이터 내보내기 완료');
    showSuccess('정규화 보고서가 성공적으로 내보내졌습니다. (결함 있으면 1건으로 표시)')
  } catch (err) {
    console.error('정규화 데이터 내보내기 실패:', err)
    error.value = `정규화 데이터 내보내기에 실패했습니다: ${err.message}`
  } finally {
    loading.value = false
  }
}


async function exportDetailed() {
  try {
    loading.value = true
    
    console.log('상세 데이터 내보내기 시작...');
    
    // type=detailed 파라미터 추가
    const params = new URLSearchParams({
      year: selectedYear.value,
      format: 'csv',
      type: 'detailed'  // 상세 보고서 모드
    });

    // 현재 적용된 필터가 있다면 추가
    if (dashboardData.value?.filters) {
      const filters = dashboardData.value.filters;
      if (filters.department) params.append('department', filters.department);
      if (filters.risk_level) params.append('risk_level', filters.risk_level);
      if (filters.search) params.append('search', filters.search);
    }

    const response = await fetch(`/api/admin/dashboard/export?${params}`, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${authStore.token}`,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
    }

    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `상세보고서_전체사용자_${selectedYear.value}년_${new Date().toISOString().split('T')[0].replace(/-/g, '')}.csv`
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
    
    console.log('상세 데이터 내보내기 완료');
    showSuccess('상세 보고서가 성공적으로 내보내졌습니다.')
  } catch (err) {
    console.error('상세 데이터 내보내기 실패:', err)
    error.value = `상세 데이터 내보내기에 실패했습니다: ${err.message}`
  } finally {
    loading.value = false
  }
}

async function exportDepartmentData() {
  try {
    loading.value = true
    
    console.log('부서별 데이터 내보내기 시작...');
    
    // 부서별 집계 데이터 내보내기
    const params = new URLSearchParams({
      year: selectedYear.value,
      format: 'csv',
      type: 'department'
    });

    const response = await fetch(`/api/admin/dashboard/export?${params}`, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${authStore.token}`,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
    }

    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `부서별_현황_${selectedYear.value}년.csv`
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
    
    console.log('부서별 데이터 내보내기 완료');
    showSuccess('부서별 데이터가 성공적으로 내보내졌습니다.')
  } catch (err) {
    console.error('부서별 데이터 내보내기 실패:', err)
    error.value = `부서별 데이터 내보내기에 실패했습니다: ${err.message}`
  } finally {
    loading.value = false
  }
}

// 선택된 사용자만 내보내기 (필요시 추가)
async function exportSelectedUsers(userIds) {
  try {
    loading.value = true
    
    console.log('선택된 사용자 데이터 내보내기 시작...');
    
    const params = new URLSearchParams({
      year: selectedYear.value,
      format: 'csv',
      user_ids: userIds.join(',')
    });

    const response = await fetch(`/api/admin/dashboard/export?${params}`, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${authStore.token}`,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
    }

    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `선택된_사용자_${userIds.length}명_${selectedYear.value}년.csv`
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
    
    console.log('선택된 사용자 데이터 내보내기 완료');
    showSuccess(`${userIds.length}명의 사용자 데이터가 성공적으로 내보내졌습니다.`)
  } catch (err) {
    console.error('선택된 사용자 데이터 내보내기 실패:', err)
    error.value = `선택된 사용자 데이터 내보내기에 실패했습니다: ${err.message}`
  } finally {
    loading.value = false
  }
}


// 디바운스 함수
function debounce(func, wait) {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

// 반응형 데이터 감시
watch(selectedYear, () => {
  loadDashboardData()
})

// 권한 체크
watch(
  () => authStore.user,
  (newUser) => {
    if (!newUser || !isAdmin()) {
      router.push('/login')
    }
  },
  { immediate: true },
)

// 페이지 로드 시 자동으로 계산 상태 확인하는 훅 추가
onMounted(async () => {
  if (authStore.isAuthenticated && isAdmin()) {
    // 계산 상태 먼저 확인
    try {
      const status = await adminAPI.getCalculationStatus(selectedYear.value)
      if (status.missing_users > 0) {
        console.log(`알림: ${status.missing_users}명의 미계산 사용자가 있습니다.`)
      }
    } catch (err) {
      console.warn('계산 상태 확인 실패:', err)
    }

    // 대시보드 데이터 로드 (자동 계산 포함)
    loadDashboardData()
  }
})
// 에러 처리
function handleError(error, context) {
  console.error(`${context} 오류:`, error)
  error.value = `${context} 중 오류가 발생했습니다: ${error.message}`
}

// 성공 메시지 표시 함수 개선
function showSuccess(message) {
  // 간단한 알림 (실제 프로젝트에서는 toast 라이브러리 사용 권장)
  const notification = document.createElement('div')
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background: #10b981;
    color: white;
    padding: 12px 20px;
    border-radius: 6px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    z-index: 1000;
    font-size: 14px;
    max-width: 400px;
  `
  notification.textContent = message

  document.body.appendChild(notification)

  // 3초 후 자동 제거
  setTimeout(() => {
    if (notification.parentNode) {
      notification.parentNode.removeChild(notification)
    }
  }, 3000)
}

// 확인 대화상자
function confirmAction(message) {
  return confirm(message)
}

// 데이터 유효성 검사
function validateData(data) {
  if (!data) return false
  if (!data.user_stats) return false
  return true
}

// 통계 계산 헬퍼
function calculateTotalUsers() {
  if (!dashboardData.value?.user_stats) return 0
  return dashboardData.value.user_stats.total_users || 0
}

function calculateComplianceRate() {
  if (!dashboardData.value?.user_stats) return 0
  const stats = dashboardData.value.user_stats
  const total = stats.total_users || 0
  const excellent = stats.excellent_users || 0

  if (total === 0) return 0
  return ((excellent / total) * 100).toFixed(1)
}

// 내보내기
defineExpose({
  loadDashboardData,
  refreshData,
  exportSummary,
  exportDetailed,
  exportDepartmentData,
})
</script>

<style scoped>
@import '../styles/AdminDashboard.css';
</style>