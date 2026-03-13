<template>
  <div class="admin-training">
    <!-- ===== 관리 헤더 ===== -->
    <div class="admin-header">
      <h1>정보보호 교육 관리</h1>
      <div class="admin-nav">
        <RouterLink to="/admin/training" class="nav-item">모의훈련 관리</RouterLink>
        <RouterLink to="/admin/education" class="nav-item active">교육 관리</RouterLink>
        <RouterLink to="/admin/manual-check" class="nav-item">수시 점검 관리</RouterLink>
        <RouterLink to="/admin/exceptions" class="nav-item">제외 설정</RouterLink>
      </div>
    </div>

    <div class="management-content">
      <!-- ===== 교육 기간 관리 섹션 ===== -->
      <div class="period-management-section">
        <div class="section-header">
          <h3>🗓️ 교육 기간 관리</h3>
          <button @click="openPeriodModal" class="primary-button">
            <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
              <path
                d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4z"
              />
            </svg>
            기간 추가
          </button>
        </div>

        <!-- 교육 기간 카드들 (기존 구조에 통계 정보 추가) -->
        <div
          class="period-cards"
          v-if="
            periodStatus.education_types && Object.keys(periodStatus.education_types).length > 0
          "
        >
          <div
            v-for="(typeData, educationType) in periodStatus.education_types"
            :key="educationType"
            class="education-type-group"
          >
            <!-- 교육 유형 헤더에 통계 정보 추가 -->
            <div class="type-header-with-stats">
              <div class="type-title-section">
                <h4 class="type-header">{{ educationType }} 교육</h4>
              </div>
            </div>

            <div class="type-periods">
              <div
                v-for="period in typeData.periods"
                :key="period.period_id"
                class="period-card"
                :class="[`status-${period.status}`, { completed: period.is_completed }]"
              >
                <!-- 기존 카드 헤더 -->
                <div class="card-header">
                  <h5>{{ period.period_name }}</h5>
                  <div class="status-badge" :class="getCardHeaderStatusClass(period)">
                    {{ getCardHeaderStatusText(period) }}
                  </div>
                </div>

                <!-- 통계 섹션 추가 -->
                <div class="period-statistics" v-if="period.statistics">
                  <div class="stats-title">📈 교육 통계</div>
                  <div class="stats-grid-compact">
                    <div class="stat-compact">
                      <span class="stat-number">{{
                        period.statistics.total_participants || 0
                      }}</span>
                      <span class="stat-text">참가자</span>
                    </div>
                    <div class="stat-compact success">
                      <span class="stat-number">{{
                        period.statistics.success_user_count || 0
                      }}</span>
                      <span class="stat-text">수료자</span>
                    </div>
                    <div class="stat-compact failure">
                      <span class="stat-number">{{
                        period.statistics.failure_user_count || 0
                      }}</span>
                      <span class="stat-text">미수료자</span>
                    </div>
                    <div
                      class="stat-compact rate"
                      :class="getSuccessRateClass(period.statistics.success_rate)"
                    >
                      <span class="stat-number">{{
                        formatSuccessRate(period.statistics.success_rate)
                      }}</span>
                      <span class="stat-text">수료율</span>
                    </div>
                  </div>

                  <!-- 프로그레스 바 -->
                  <div class="progress-bar" v-if="period.statistics.total_participants > 0">
                    <div
                      class="progress-fill"
                      :style="`width: ${period.statistics.success_rate}%`"
                      :class="getSuccessRateClass(period.statistics.success_rate)"
                    ></div>
                  </div>
                  <div class="no-data" v-else>아직 교육 데이터가 없습니다.</div>
                </div>

                <!-- 기존 카드 바디 -->
                <div class="card-body">
                  <div class="period-info">
                    <span class="info-item">
                      📅 {{ formatDate(period.start_date) }} ~ {{ formatDate(period.end_date) }}
                    </span>
                    <span
                      class="info-item"
                      v-if="period.statistics && period.statistics.total_participants > 0"
                    >
                      👥 {{ period.statistics.total_participants }}명 참여
                    </span>
                  </div>
                  <div class="card-actions">
                    <!-- 수정 버튼: 완료된 상태에서는 비활성화 -->
                    <button
                      @click="editPeriod(period)"
                      class="edit-button"
                      :disabled="period.is_completed"
                    >
                      <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
                        <path
                          d="M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708L14.5 5.207l-3-3L12.146.146zM11.207 1.5L1.5 11.207V14.5h3.293L14.5 4.707l-3-3L11.207 1.5z"
                        />
                      </svg>
                      수정
                    </button>

                    <!-- 완료 처리 버튼: 완료되지 않은 경우에만 활성화 -->
                    <button
                      @click="completePeriod(period)"
                      class="complete-button"
                      :disabled="period.is_completed"
                    >
                      <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
                        <path
                          d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"
                        />
                      </svg>
                      완료 처리
                    </button>

                    <!-- 재개 버튼: 완료된 경우에만 활성화 -->
                    <button
                      @click="reopenPeriod(period)"
                      class="reopen-button"
                      :disabled="!period.is_completed"
                    >
                      <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
                        <path d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2v1z" />
                        <path
                          d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466z"
                        />
                      </svg>
                      재개
                    </button>

                    <!-- 삭제 버튼: 완료된 상태에서는 비활성화 -->
                    <button
                      @click="deletePeriod(period)"
                      class="delete-button"
                      :disabled="period.is_completed"
                    >
                      <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
                        <path
                          d="M6.5 1h3a.5.5 0 0 1 .5.5v1H6v-1a.5.5 0 0 1 .5-.5ZM11 2.5v-1A1.5 1.5 0 0 0 9.5 0h-3A1.5 1.5 0 0 0 5 1.5v1H2.5a.5.5 0 0 0 0 1h.538l.853 10.66A2 2 0 0 0 5.883 16h4.234a2 2 0 0 0 1.992-1.84l.853-10.66h.538a.5.5 0 0 0 0-1H11z"
                        />
                      </svg>
                      삭제
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 상세 통계 모달 -->
        <div v-if="showDetailStatsModal" class="modal-overlay" @click="closeDetailStatsModal">
          <div class="modal-content stats-modal" @click.stop>
            <div class="modal-header">
              <h3>📊 상세 교육 통계</h3>
              <button @click="closeDetailStatsModal" class="close-button">&times;</button>
            </div>

            <div class="modal-body" v-if="selectedPeriodStats">
              <!-- 기간 정보 -->
              <div class="period-info-section">
                <h4>{{ selectedPeriodStats.period_info.period_name }}</h4>
                <p>
                  {{ selectedPeriodStats.period_info.education_type }} |
                  {{ formatDate(selectedPeriodStats.period_info.start_date) }} ~
                  {{ formatDate(selectedPeriodStats.period_info.end_date) }}
                </p>
              </div>

              <!-- 전체 통계 -->
              <div class="summary-stats">
                <div class="summary-grid">
                  <div class="summary-item">
                    <div class="summary-value">
                      {{ selectedPeriodStats.summary.total_participants }}
                    </div>
                    <div class="summary-label">총 참가자</div>
                  </div>
                  <div class="summary-item">
                    <div class="summary-value success">
                      {{ selectedPeriodStats.summary.success_users }}
                    </div>
                    <div class="summary-label">수료자 수</div>
                  </div>
                  <div class="summary-item">
                    <div class="summary-value failure">
                      {{ selectedPeriodStats.summary.failure_users }}
                    </div>
                    <div class="summary-label">미수료자 수</div>
                  </div>
                </div>
              </div>

              <!-- 부서별 통계 -->
              <div class="department-stats" v-if="selectedPeriodStats.department_statistics">
                <h5>부서별 통계</h5>
                <div class="department-table">
                  <table>
                    <thead>
                      <tr>
                        <th>부서</th>
                        <th>참가자</th>
                        <th>수료자</th>
                        <th>미수료자</th>
                        <th>수료율</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr
                        v-for="dept in selectedPeriodStats.department_statistics"
                        :key="dept.department"
                      >
                        <td>{{ dept.department }}</td>
                        <td>{{ dept.participants }}</td>
                        <td class="success">{{ dept.success_users }}</td>
                        <td class="failure">{{ dept.failure_users }}</td>
                        <td :class="getSuccessRateClass(dept.success_rate)">
                          {{ formatSuccessRate(dept.success_rate) }}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <!-- 개별 참가자 상세 (필요시 토글) -->
              <div class="participant-details" v-if="selectedPeriodStats.participant_details">
                <h5>개별 참가자 상세 ({{ selectedPeriodStats.participant_details.length }}명)</h5>
                <div class="participant-table" style="max-height: 300px; overflow-y: auto">
                  <table>
                    <thead>
                      <tr>
                        <th>이름</th>
                        <th>부서</th>
                        <th>수료</th>
                        <th>미수료</th>
                        <th>수료율</th>
                        <th>상태</th>
                        <th>제외여부</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr
                        v-for="participant in selectedPeriodStats.participant_details"
                        :key="participant.username"
                      >
                        <td>{{ participant.username }}</td>
                        <td>{{ participant.department }}</td>
                        <td class="success">{{ participant.completed_count || 0 }}</td>
                        <td class="failure">{{ participant.incomplete_count || 0 }}</td>
                        <td :class="getRateClass(participant.completion_rate)">
                          {{
                            participant.completion_rate
                              ? participant.completion_rate.toFixed(1) + '%'
                              : '0%'
                          }}
                        </td>
                        <td>
                          <span v-if="participant.user_status === 'success'" class="success-badge"
                            >수료</span
                          >
                          <span v-else class="failure-badge">미수료</span>
                        </td>
                        <td>
                          <span v-if="participant.exclude_from_scoring" class="excluded-badge"
                            >제외</span
                          >
                          <span v-else class="included-badge">포함</span>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            <div class="modal-footer">
              <button @click="closeDetailStatsModal" class="secondary-button">닫기</button>
            </div>
          </div>
        </div>
      </div>
      <!-- ===== 교육 기록 관리 섹션 ===== -->
      <div class="table-section">
        <!-- 액션 버튼들 -->
        <div class="section-header">
          <h3>📋 교육 기록 관리 ({{ filteredRecords.length }}건)</h3>
          <div class="section-actions">
            <button @click="downloadTemplate" class="outline-button">
              <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                <path
                  d="M14 14V4.5L9.5 0H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2zM9.5 3A1.5 1.5 0 0 0 11 4.5h2V14a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1h5.5v2z"
                />
              </svg>
              📄 템플릿 다운로드
            </button>
            <button @click="showBulkUploadModal = true" class="primary-button">
              <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                <path
                  d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"
                />
                <path
                  d="M7.646 1.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1-.708.708L8.5 2.707V11.5a.5.5 0 0 1-1 0V2.707L5.354 4.854a.5.5 0 1 1-.708-.708l3-3z"
                />
              </svg>
              📤 일괄 등록
            </button>
          </div>
        </div>

        <!-- 필터 섹션 -->
        <div class="filter-section">
          <div class="filter-group">
            <label>연도:</label>
            <select v-model="selectedYear" @change="loadEducationData">
              <option v-for="year in availableYears" :key="year" :value="year">{{ year }}년</option>
            </select>
          </div>

          <div class="filter-group">
            <label>교육유형:</label>
            <select v-model="selectedEducationType" @change="loadEducationData">
              <option value="">전체</option>
              <option value="오프라인">오프라인</option>
              <option value="온라인">온라인</option>
            </select>
          </div>

          <div class="filter-group">
            <label>상태:</label>
            <select v-model="selectedStatus" @change="loadEducationData">
              <option value="">전체</option>
              <option value="1">수료</option>
              <option value="0">미수료</option>
            </select>
          </div>

          <div class="search-group">
            <label>검색:</label>
            <input
              type="text"
              v-model="searchQuery"
              @input="searchEducationData"
              placeholder="사용자명 또는 부서 검색..."
              class="search-input"
            />
          </div>
        </div>

        <!-- 일괄 작업 -->
        <div class="bulk-actions" v-if="selectedRecords.length > 0">
          <div class="select-all">
            <input type="checkbox" v-model="selectAll" @change="toggleSelectAll" />
            <span>{{ selectedRecords.length }}개 선택됨</span>
          </div>
          <button @click="bulkToggleException" class="bulk-action-button">일괄 제외 설정</button>
          <span class="selected-count">총 {{ filteredRecords.length }}건</span>
        </div>

        <!-- 교육 기록 테이블 -->
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th style="width: 40px">
                  <input
                    type="checkbox"
                    v-model="selectAll"
                    @change="toggleSelectAll"
                    :indeterminate="
                      selectedRecords.length > 0 && selectedRecords.length < paginatedRecords.length
                    "
                  />
                </th>
                <th>사용자</th>
                <th>부서</th>
                <th>과정명</th>
                <th>교육유형</th>
                <th>수료횟수</th>
                <th>미수료횟수</th>
                <th>수료율</th>
                <th>상태</th>
                <th>교육일</th>
                <th>기간</th>
                <th>감점</th>
                <th>제외</th>
                <th>작업</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="record in paginatedRecords"
                :key="record.education_id"
                :class="{
                  selected: selectedRecords.includes(record),
                  excluded: record.exclude_from_scoring,
                  'data-legacy': record.data_mode === 'legacy',
                }"
              >
                <!-- 체크박스 -->
                <td class="checkbox-col">
                  <input
                    type="checkbox"
                    :value="record"
                    v-model="selectedRecords"
                    @change="updateSelectAll"
                  />
                </td>

                <!-- 사용자 정보 -->
                <td class="user-info">
                  <div class="user-name">{{ record.username }}</div>
                  <div class="user-id">{{ record.mail }}</div>
                </td>

                <!-- 부서 -->
                <td class="department">{{ record.department }}</td>

                <!-- 과정명 -->
                <td class="course-name">
                  <div class="course-main">{{ record.course_name || record.education_type }}</div>
                  <div v-if="record.total_courses > 1" class="course-meta">
                    총 {{ record.total_courses }}과정
                  </div>
                </td>

                <!-- 교육유형 -->
                <td class="education-type">
                  <span class="type-badge" :class="getTypeClass(record.education_type)">
                    {{ record.education_type }}
                  </span>
                </td>

                <!-- 수료횟수 -->
                <td class="completed-count">
                  <span class="count-value success">{{ record.completed_count || 0 }}</span>
                </td>

                <!-- 미수료횟수 -->
                <td class="incomplete-count">
                  <span class="count-value danger">{{ record.incomplete_count || 0 }}</span>
                </td>

                <!-- 수료율 -->
                <td class="completion-rate">
                  <div class="rate-container">
                    <div class="rate-bar">
                      <div
                        class="rate-fill"
                        :style="{ width: `${record.completion_rate || 0}%` }"
                        :class="getRateClass(record.completion_rate)"
                      ></div>
                    </div>
                    <span class="rate-text" :class="getRateTextClass(record.completion_rate)">
                      {{ (record.completion_rate || 0).toFixed(0) }}%
                    </span>
                  </div>
                </td>

                <!-- 상태 -->
                <td class="status">
                  <span class="status-badge" :class="getStatusClass(record)">
                    {{ record.status_text || getStatusText(record) }}
                  </span>
                  <div v-if="record.data_mode === 'legacy'" class="legacy-indicator">레거시</div>
                </td>

                <!-- 교육일 -->
                <td class="education-date">{{ formatDate(record.education_date) }}</td>

                <!-- 기간 정보 -->
                <td class="period-info">
                  <div v-if="record.period_name" class="period-name">{{ record.period_name }}</div>
                  <div
                    v-if="record.period_start_date && record.period_end_date"
                    class="period-dates"
                  >
                    {{ formatDateShort(record.period_start_date) }} ~
                    {{ formatDateShort(record.period_end_date) }}
                  </div>
                  <div v-if="record.period_completed" class="period-status completed">완료됨</div>
                </td>

                <!-- 감점 -->
                <td class="penalty">
                  <span v-if="record.exclude_from_scoring" class="penalty-excluded">제외</span>
                  <span
                    v-else
                    class="penalty-value"
                    :class="{ 'penalty-active': record.penalty_applied > 0 }"
                  >
                    -{{ (record.penalty_applied || 0).toFixed(1) }}점
                  </span>
                </td>

                <!-- 제외 상태 -->
                <td class="exclude-status">
                  <button
                    @click="toggleExceptionStatus(record)"
                    class="exclude-toggle"
                    :class="{ active: record.exclude_from_scoring }"
                    :title="record.exclude_from_scoring ? '제외 해제' : '점수 제외'"
                  >
                    <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                      <path
                        v-if="record.exclude_from_scoring"
                        d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM5.354 4.646a.5.5 0 1 0-.708.708L7.293 8l-2.647 2.646a.5.5 0 0 0 .708.708L8 8.707l2.646 2.647a.5.5 0 0 0 .708-.708L8.707 8l2.647-2.646a.5.5 0 0 0-.708-.708L8 7.293 5.354 4.646z"
                      />
                      <path
                        v-else
                        d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zm-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.061L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z"
                      />
                    </svg>
                  </button>
                  <div
                    v-if="record.exclude_from_scoring && record.exclude_reason"
                    class="exclude-reason"
                  >
                    {{ record.exclude_reason }}
                  </div>
                </td>

                <!-- 작업 버튼 -->
                <td class="actions">
                  <div class="action-buttons">
                    <button @click="editRecord(record)" class="action-btn edit" title="수정">
                      <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
                        <path
                          d="M15.502 1.94a.5.5 0 0 1 0 .706L14.459 3.69l-2-2L13.502.646a.5.5 0 0 1 .707 0l1.293 1.293zm-1.75 2.456-2-2L4.939 9.21a.5.5 0 0 0-.121.196l-.805 2.414a.25.25 0 0 0 .316.316l2.414-.805a.5.5 0 0 0 .196-.12l6.813-6.814z"
                        />
                        <path
                          fill-rule="evenodd"
                          d="M1 13.5A1.5 1.5 0 0 0 2.5 15h11a1.5 1.5 0 0 0 1.5-1.5v-6a.5.5 0 0 0-1 0v6a.5.5 0 0 1-.5.5h-11a.5.5 0 0 1-.5-.5v-11a.5.5 0 0 1 .5-.5H9a.5.5 0 0 0 0-1H2.5A1.5 1.5 0 0 0 1 2.5v11z"
                        />
                      </svg>
                    </button>
                    <button @click="deleteRecord(record)" class="action-btn delete" title="삭제">
                      <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
                        <path
                          d="M2.5 1a1 1 0 0 0-1 1v1a1 1 0 0 0 1 1H3v9a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2V4h.5a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1H10a1 1 0 0 0-1-1H7a1 1 0 0 0-1 1H2.5zm3 4a.5.5 0 0 1 .5.5v7a.5.5 0 0 1-1 0v-7a.5.5 0 0 1 .5-.5zM8 5a.5.5 0 0 1 .5.5v7a.5.5 0 0 1-1 0v-7A.5.5 0 0 1 8 5zm3 .5v7a.5.5 0 0 1-1 0v-7a.5.5 0 0 1 1 0z"
                        />
                      </svg>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>

          <!-- 페이지네이션 -->
          <div class="pagination">
            <button @click="currentPage--" :disabled="currentPage <= 1" class="pagination-button">
              이전
            </button>
            <span class="pagination-info"
              >{{ currentPage }} / {{ totalPages }} 페이지 (총 {{ filteredRecords.length }}건)</span
            >
            <button
              @click="currentPage++"
              :disabled="currentPage >= totalPages"
              class="pagination-button"
            >
              다음
            </button>
          </div>
        </div>

        <!-- 데이터가 없는 경우 -->
        <div v-if="filteredRecords.length === 0" class="no-data">
          <div class="no-data-icon">📚</div>
          <h3>교육 기록이 없습니다</h3>
          <p>필터 조건을 변경하거나 새로운 교육 데이터를 업로드해보세요.</p>
        </div>
      </div>
    </div>

    <!-- ===== 모달들 ===== -->

    <!-- 기간 설정 모달 -->
    <div v-if="showPeriodModal" class="modal-overlay" @click="closePeriodModal">
      <div class="modal-content period-modal" @click.stop>
        <div class="modal-header">
          <h3>{{ editingPeriod ? '기간 수정' : '기간 추가' }}</h3>
          <button @click="closePeriodModal" class="close-button">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>연도:</label>
            <input
              type="number"
              v-model="periodForm.education_year"
              :min="2020"
              :max="2030"
              class="form-input"
            />
          </div>
          <div class="form-group">
            <label>기간명:</label>
            <input
              type="text"
              v-model="periodForm.period_name"
              placeholder="예: 1차 오프라인 교육, 상반기 온라인 교육"
              class="form-input"
            />
          </div>
          <div class="form-group">
            <label>교육유형:</label>
            <select v-model="periodForm.education_type" class="form-input">
              <option value="오프라인">오프라인</option>
              <option value="온라인">온라인</option>
            </select>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>시작일:</label>
              <input type="date" v-model="periodForm.start_date" class="form-input" />
            </div>
            <div class="form-group">
              <label>종료일:</label>
              <input type="date" v-model="periodForm.end_date" class="form-input" />
            </div>
          </div>
          <div class="form-group">
            <label>설명:</label>
            <textarea
              v-model="periodForm.description"
              rows="3"
              placeholder="교육에 대한 설명을 입력하세요"
              class="form-input"
            ></textarea>
          </div>
          <div class="form-group">
            <label class="checkbox-label">
              <input type="checkbox" v-model="periodForm.auto_pass_setting" />
              완료 시 자동 통과 처리
            </label>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="closePeriodModal" class="cancel-button">취소</button>
          <button @click="savePeriod" class="save-button" :disabled="!isValidPeriodForm">
            {{ editingPeriod ? '수정' : '추가' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 일괄 업로드 모달 -->
    <div v-if="showBulkUploadModal" class="modal-overlay" @click="closeBulkUploadModal">
      <div class="modal-content bulk-upload-modal" @click.stop>
        <div class="modal-header">
          <h3>교육 결과 일괄 업로드</h3>
          <button @click="closeBulkUploadModal" class="close-button">&times;</button>
        </div>

        <div class="modal-body">
          <!-- 1단계: 교육 기간 선택 -->
          <div class="upload-step">
            <h4>1단계: 교육 기간 선택 (필수)</h4>
            <div class="period-selection">
              <select v-model="selectedUploadPeriod" @change="onPeriodChange" class="period-select">
                <option value="">교육 기간을 선택하세요</option>
                <optgroup
                  v-for="(typeData, eduType) in availablePeriodsForUpload"
                  :key="eduType"
                  :label="`${eduType} 교육`"
                >
                  <option
                    v-for="period in typeData.periods"
                    :key="period.period_id"
                    :value="period.period_id"
                  >
                    {{ period.period_name }} ({{
                      formatDateRange(period.start_date, period.end_date)
                    }}) - {{ getPeriodStatusText(period) }}
                  </option>
                </optgroup>
              </select>
            </div>

            <!-- 선택된 기간 정보 표시 -->
            <div v-if="selectedPeriodInfo" class="selected-period-info">
              <div class="info-card">
                <h5>선택된 교육 기간</h5>
                <p><strong>기간명:</strong> {{ selectedPeriodInfo.period_name }}</p>
                <p><strong>교육유형:</strong> {{ selectedPeriodInfo.education_type }}</p>
                <p>
                  <strong>기간:</strong>
                  {{ formatDateRange(selectedPeriodInfo.start_date, selectedPeriodInfo.end_date) }}
                </p>
                <p>
                  <strong>상태:</strong>
                  <span :class="getPeriodStatusClass(selectedPeriodInfo)">{{
                    getPeriodStatusText(selectedPeriodInfo)
                  }}</span>
                </p>
              </div>
            </div>
          </div>

          <!-- 2단계: 파일 업로드 -->
          <div class="upload-step" :class="{ disabled: !selectedUploadPeriod }">
            <h4>2단계: CSV/Excel 파일 업로드</h4>

            <!-- 기간 미선택 시 안내 메시지 -->
            <div v-if="!selectedUploadPeriod" class="warning-message">
              <p>⚠️ 먼저 교육 기간을 선택해주세요.</p>
            </div>

            <div v-else class="file-upload-area">
              <div
                class="dropzone"
                :class="{ active: isDragOver }"
                @dragover.prevent="isDragOver = true"
                @dragleave="isDragOver = false"
                @drop.prevent="handleFileDrop"
                @click="triggerFileSelect"
              >
                <div v-if="!selectedFile" class="upload-placeholder">
                  <div class="upload-icon">📁</div>
                  <p>CSV 또는 Excel 파일을 드래그하거나 클릭하여 선택하세요</p>
                  <small>지원 형식: .csv, .xlsx, .xls</small>
                </div>

                <div v-else class="file-info">
                  <div class="file-icon">📄</div>
                  <div class="file-details">
                    <p>
                      <strong>{{ selectedFile.name }}</strong>
                    </p>
                    <small>{{ formatFileSize(selectedFile.size) }}</small>
                  </div>
                  <button @click.stop="removeSelectedFile" class="remove-file-btn">✕</button>
                </div>
              </div>

              <input
                ref="fileInput"
                type="file"
                accept=".csv,.xlsx,.xls"
                @change="handleFileSelect"
                style="display: none"
              />
            </div>
          </div>

          <!-- 3단계: 데이터 미리보기 및 검증 -->
          <div v-if="uploadPreview.length > 0" class="upload-step">
            <h4>3단계: 데이터 미리보기 및 검증</h4>

            <!-- 검증 결과 요약 -->
            <div class="validation-summary">
              <div class="summary-stats">
                <div class="stat-item">
                  <span class="stat-label">총 레코드:</span>
                  <span class="stat-value">{{ uploadPreview.length }}건</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">예상 수료:</span>
                  <span class="stat-value success">{{ getTotalCompletedCount() }}건</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">예상 미수료:</span>
                  <span class="stat-value warning">{{ getTotalIncompleteCount() }}건</span>
                </div>
              </div>
            </div>

            <!-- 데이터 검증 경고 -->
            <div v-if="validationWarnings.length > 0" class="validation-warnings">
              <h5>⚠️ 검증 경고사항</h5>
              <ul>
                <li v-for="warning in validationWarnings" :key="warning">{{ warning }}</li>
              </ul>
            </div>

            <!-- 데이터 테이블 미리보기 -->
            <div class="preview-table-container">
              <table class="preview-table">
                <thead>
                  <tr>
                    <th>이름</th>
                    <th>부서</th>
                    <th>수강과정</th>
                    <th>수료횟수</th>
                    <th>미수료횟수</th>
                    <th>전체</th>
                    <th>수료율</th>
                    <th>상태</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(record, index) in uploadPreview.slice(0, 10)" :key="index">
                    <td>{{ record.username }}</td>
                    <td>{{ record.department }}</td>
                    <td>{{ record.education_type }}</td>
                    <td class="number-cell">{{ record.completed_count }}</td>
                    <td class="number-cell">{{ record.incomplete_count }}</td>
                    <td class="number-cell">
                      {{ record.completed_count + record.incomplete_count }}
                    </td>
                    <td class="percentage-cell">
                      {{
                        record.completed_count + record.incomplete_count > 0
                          ? Math.round(
                              (record.completed_count /
                                (record.completed_count + record.incomplete_count)) *
                                100,
                            )
                          : 0
                      }}%
                    </td>
                    <td>
                      <!-- 🔄 단순화된 상태 표시 -->
                      <span
                        :class="{
                          'status-completed':
                            record.completed_count + record.incomplete_count > 0 &&
                            record.completed_count /
                              (record.completed_count + record.incomplete_count) >=
                              1.0,
                          'status-incomplete':
                            record.completed_count + record.incomplete_count === 0 ||
                            record.completed_count /
                              (record.completed_count + record.incomplete_count) <
                              1.0,
                        }"
                      >
                        {{
                          record.completed_count + record.incomplete_count === 0
                            ? '데이터없음'
                            : record.completed_count /
                                  (record.completed_count + record.incomplete_count) >=
                                1.0
                              ? '수료'
                              : '미수료'
                        }}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>

              <!-- 더 많은 데이터가 있는 경우 안내 -->
              <p v-if="uploadPreview.length > 10" class="preview-note">
                총 {{ uploadPreview.length }}건 중 10건만 미리보기로 표시됩니다.
              </p>
            </div>
          </div>
        </div>

        <!-- 업로드 버튼 -->
        <div class="modal-footer">
          <button @click="closeBulkUploadModal" class="cancel-button">취소</button>
          <button
            @click="executeUpload"
            :disabled="!canUpload"
            class="upload-button"
            :class="{ loading: uploading }"
          >
            <span v-if="uploading" class="loading-spinner"></span>
            <span v-if="uploading">{{ selectedPeriodInfo?.period_name }}에 업로드 중...</span>
            <span v-else-if="!selectedUploadPeriod">교육 기간을 선택하세요</span>
            <span v-else-if="uploadPreview.length === 0">파일을 선택하세요</span>
            <span v-else
              >{{ selectedPeriodInfo?.period_name }}에 {{ uploadPreview.length }}건 업로드</span
            >
          </button>
        </div>
      </div>
    </div>

    <!-- 편집 모달 -->
    <div v-if="showEditModal" class="modal-overlay" @click="closeEditModal">
      <div class="modal-content edit-modal" @click.stop>
        <div class="modal-header">
          <h3>교육 기록 수정</h3>
          <button @click="closeEditModal" class="close-button">&times;</button>
        </div>

        <div class="modal-body">
          <form @submit.prevent="saveRecord" class="edit-form">
            <!-- 기본 정보 (읽기 전용) -->
            <div class="form-row">
              <div class="form-group">
                <label>사용자명</label>
                <input type="text" v-model="editingRecord.username" class="form-input" disabled />
              </div>
              <div class="form-group">
                <label>부서</label>
                <input type="text" v-model="editingRecord.department" class="form-input" disabled />
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>교육 연도</label>
                <input
                  type="number"
                  v-model="editingRecord.education_year"
                  class="form-input"
                  disabled
                />
              </div>
              <div class="form-group">
                <label>교육 유형</label>
                <input
                  type="text"
                  v-model="editingRecord.education_type"
                  class="form-input"
                  disabled
                />
              </div>
            </div>

            <!-- 수정 가능한 필드들 -->
            <div class="form-group">
              <label>과정명</label>
              <input
                type="text"
                v-model="editingRecord.course_name"
                class="form-input"
                placeholder="교육 과정명"
              />
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>수료 횟수</label>
                <input
                  type="number"
                  v-model.number="editingRecord.completed_count"
                  class="form-input"
                  min="0"
                  placeholder="0"
                />
              </div>
              <div class="form-group">
                <label>미수료 횟수</label>
                <input
                  type="number"
                  v-model.number="editingRecord.incomplete_count"
                  class="form-input"
                  min="0"
                  placeholder="0"
                />
              </div>
            </div>

            <div class="form-group">
              <label>교육일</label>
              <input type="date" v-model="editingRecord.education_date" class="form-input" />
            </div>

            <!-- 예외 처리 -->
            <div class="form-group">
              <label class="checkbox-label">
                <input type="checkbox" v-model="editingRecord.exclude_from_scoring" />
                점수 산정에서 제외
              </label>
            </div>

            <div v-if="editingRecord.exclude_from_scoring" class="form-group">
              <label>제외 사유</label>
              <input
                type="text"
                v-model="editingRecord.exclude_reason"
                class="form-input"
                placeholder="제외 사유를 입력하세요"
              />
            </div>

            <div class="form-group">
              <label>비고</label>
              <textarea
                v-model="editingRecord.notes"
                class="form-input"
                rows="3"
                placeholder="추가 정보나 비고사항"
              ></textarea>
            </div>

            <!-- 버튼 -->
            <div class="modal-footer">
              <button type="button" @click="closeEditModal" class="cancel-button">취소</button>
              <button type="submit" class="save-button" :disabled="saving">
                {{ saving ? '저장 중...' : '저장' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- 토스트 메시지 -->
    <div v-if="showToast" class="toast" :class="toastType">{{ toastMessage }}</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { RouterLink } from 'vue-router'

// ===== 상태 관리 =====

// 기본 상태
const loading = ref(false)
const saving = ref(false)

// 필터 및 검색 상태
const selectedYear = ref(new Date().getFullYear())
const selectedEducationType = ref('')
const selectedStatus = ref('')
const searchQuery = ref('')

// 교육 기간 관리 상태
const periodStatus = ref({ education_types: {} })
const showPeriodModal = ref(false)
const editingPeriod = ref(null)
const periodForm = ref({
  education_year: new Date().getFullYear(),
  period_name: '',
  education_type: '오프라인',
  start_date: '',
  end_date: '',
  description: '',
  auto_pass_setting: true,
})

// 교육 데이터 상태
const educationData = ref([])
const filteredRecords = ref([])
const currentPage = ref(1)
const pageSize = ref(20)

// 선택 및 일괄 작업 상태
const selectedRecords = ref([])
const selectAll = ref(false)

// 업로드 관련 상태
const showBulkUploadModal = ref(false)
const selectedFile = ref(null)
const uploadPreview = ref([])
const uploading = ref(false)
const isDragOver = ref(false)
const selectedUploadPeriod = ref('')
const availablePeriodsForUpload = ref({})
const validationWarnings = ref([])

// 편집 관련 상태
const showEditModal = ref(false)
const editingRecord = ref({})

// 토스트 상태
const showToast = ref(false)
const toastMessage = ref('')
const toastType = ref('success')

// 기존 반응형 데이터에 추가
const showDetailStatsModal = ref(false)
const selectedPeriodStats = ref(null)
const loadingStats = ref(false)

// ===== 계산된 속성 =====

// 연도 옵션 계산
const availableYears = computed(() => {
  const currentYear = new Date().getFullYear()
  return [currentYear - 1, currentYear, currentYear + 1]
})

// 페이지네이션 계산
const paginatedRecords = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredRecords.value.slice(start, end)
})

const totalPages = computed(() => {
  return Math.ceil(filteredRecords.value.length / pageSize.value)
})

// 폼 유효성 검사
const isValidPeriodForm = computed(() => {
  return (
    periodForm.value.period_name &&
    periodForm.value.education_type &&
    periodForm.value.start_date &&
    periodForm.value.end_date
  )
})

// 선택된 기간 정보
const selectedPeriodInfo = computed(() => {
  if (!selectedUploadPeriod.value) return null

  for (const typeData of Object.values(availablePeriodsForUpload.value)) {
    const period = typeData.periods.find((p) => p.period_id == selectedUploadPeriod.value)
    if (period) return period
  }
  return null
})

// 업로드 가능 여부
const canUpload = computed(() => {
  return (
    selectedUploadPeriod.value &&
    uploadPreview.value.length > 0 &&
    !uploading.value &&
    validationWarnings.value.filter((w) => w.includes('오류')).length === 0
  )
})

// ===== 라이프사이클 =====

onMounted(() => {
  loadPeriodStatus()
  loadEducationData()
  loadAvailablePeriodsForUpload()
})

// ===== 데이터 로딩 메서드 =====

/**
 * 교육 기간 현황 조회
 */
const loadPeriodStatus = async () => {
  try {
    console.log('[DEBUG] 기간 현황 조회 시작:', selectedYear.value)

    // 통계가 포함된 API 호출
    const response = await fetch(
      `/api/security-education/periods/statistics?year=${selectedYear.value}`,
      {
        credentials: 'include',
      },
    )

    if (!response.ok) {
      throw new Error('기간 현황 조회 실패')
    }

    const data = await response.json()
    console.log('[DEBUG] 서버 응답 데이터 (통계 포함):', data)

    periodStatus.value = data

    // 기간 개수 로그
    if (data.education_types) {
      let totalPeriods = 0
      Object.values(data.education_types).forEach((typeData) => {
        totalPeriods += typeData.periods ? typeData.periods.length : 0
      })
      console.log('[DEBUG] 총 기간 개수:', totalPeriods)
    }
  } catch (err) {
    console.error('기간 현황 조회 오류:', err)
    displayToast('기간 현황을 불러오는데 실패했습니다.', 'error')
  }
}

/**
 * 특정 교육 기간의 상세 통계 조회
 */
const viewDetailedStatistics = async (period) => {
  loadingStats.value = true
  try {
    const response = await fetch(`/api/security-education/periods/${period.period_id}/statistics`, {
      credentials: 'include',
    })

    if (!response.ok) {
      throw new Error('상세 통계 조회 실패')
    }

    const data = await response.json()
    selectedPeriodStats.value = {
      ...data,
      period_info: period,
    }
    showDetailStatsModal.value = true
  } catch (err) {
    console.error('상세 통계 조회 오류:', err)
    displayToast('상세 통계를 불러오는데 실패했습니다.', 'error')
  } finally {
    loadingStats.value = false
  }
}

/**
 * 상세 통계 모달 닫기
 */
const closeDetailStatsModal = () => {
  showDetailStatsModal.value = false
  selectedPeriodStats.value = null
}

// ===== 유틸리티 메서드 추가 =====

/**
 * 성공률 포맷팅
 */
const formatSuccessRate = (rate) => {
  if (rate === null || rate === undefined) return '0%'
  return `${Math.round(rate * 10) / 10}%`
}

/**
 * 🔄 단순화된 성공률별 CSS 클래스 반환
 */
const getSuccessRateClass = (rate) => {
  if (rate >= 100) return 'rate-excellent'  // 🔄 100%만 excellent
  return 'rate-poor'  // 🔄 100% 외는 모두 poor
}

/**
 * 교육 데이터 조회
 */
const loadEducationData = async () => {
  loading.value = true
  try {
    const params = new URLSearchParams({
      year: selectedYear.value,
      education_type: selectedEducationType.value,
      status: selectedStatus.value,
    })

    const response = await fetch(`/api/security-education/records?${params}`, {
      credentials: 'include',
    })

    if (!response.ok) {
      throw new Error('교육 데이터 조회 실패')
    }

    educationData.value = await response.json()
    applyFilters()
  } catch (err) {
    console.error('교육 데이터 조회 오류:', err)
    displayToast('교육 데이터를 불러오는데 실패했습니다.', 'error')
  } finally {
    loading.value = false
  }
}

/**
 * 업로드 가능한 교육 기간 목록 로드
 */
const loadAvailablePeriodsForUpload = async () => {
  try {
    const response = await fetch('/api/security-education/periods/status', {
      credentials: 'include',
    })

    if (!response.ok) {
      throw new Error('교육 기간 목록 로드 실패')
    }

    const result = await response.json()
    availablePeriodsForUpload.value = result.education_types || {}

    console.log('[DEBUG] 업로드 가능한 교육 기간:', availablePeriodsForUpload.value)
  } catch (err) {
    console.error('교육 기간 로드 오류:', err)
    displayToast('교육 기간 목록을 불러오는데 실패했습니다.', 'error')
  }
}

// ===== 필터링 및 검색 =====

/**
 * 검색 실행
 */
const searchEducationData = () => {
  applyFilters()
}

/**
 * 필터 적용
 */
const applyFilters = () => {
  let filtered = [...educationData.value]

  // 검색어 필터
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase().trim()
    filtered = filtered.filter((record) => {
      return (
        record.username?.toLowerCase().includes(query) ||
        record.department?.toLowerCase().includes(query) ||
        record.course_name?.toLowerCase().includes(query) ||
        record.education_type?.toLowerCase().includes(query)
      )
    })
  }

  filteredRecords.value = filtered
  currentPage.value = 1
}

// ===== 기간 관리 메서드 =====

/**
 * 기간 추가 모달 열기
 */
const openPeriodModal = () => {
  editingPeriod.value = null
  periodForm.value = {
    education_year: selectedYear.value,
    period_name: '',
    education_type: '오프라인',
    start_date: '',
    end_date: '',
    description: '',
    auto_pass_setting: true,
  }
  showPeriodModal.value = true
}

/**
 * 기간 편집 모달 열기
 */
const editPeriod = (period) => {
  console.log('[DEBUG] 수정할 기간 데이터:', period)

  // 수정 모드로 설정
  editingPeriod.value = period

  // 기존 값들을 폼에 설정
  periodForm.value = {
    education_year: period.education_year,
    period_name: period.period_name,
    education_type: period.education_type,
    start_date: period.start_date,
    end_date: period.end_date,
    description: period.description || '',
    auto_pass_setting: period.auto_pass_setting === 1 || period.auto_pass_setting === true,
  }

  console.log('[DEBUG] 폼에 설정된 값들:', periodForm.value)

  // 모달 열기
  showPeriodModal.value = true
}

/**
 * 기간 저장 (추가/수정)
 */
const savePeriod = async () => {
  if (!isValidPeriodForm.value) {
    displayToast('필수 필드를 모두 입력해주세요.', 'error')
    return
  }

  // 날짜 유효성 검사
  if (new Date(periodForm.value.start_date) >= new Date(periodForm.value.end_date)) {
    displayToast('종료일은 시작일보다 늦어야 합니다.', 'error')
    return
  }

  try {
    console.log('[DEBUG] 기간 저장 요청:', periodForm.value)

    const method = editingPeriod.value ? 'PUT' : 'POST'
    const url = editingPeriod.value
      ? `/api/security-education/periods/${editingPeriod.value.period_id}`
      : '/api/security-education/periods'

    const response = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(periodForm.value),
    })

    const result = await response.json()
    console.log('[DEBUG] 서버 응답:', result)

    if (!response.ok) {
      // ✅ 완료된 기간 수정 시 특별 처리
      if (result.message && result.message.includes('완료된 교육 기간은 수정할 수 없습니다')) {
        const confirmReopen = confirm(
          `이 기간은 완료 상태입니다.\n\n완료 상태를 해제하고 수정하시겠습니까?\n\n` +
            `※ 완료 상태 해제 시 자동 통과 처리된 데이터가 삭제될 수 있습니다.`,
        )

        if (confirmReopen) {
          await reopenAndEdit()
          return
        } else {
          displayToast('수정이 취소되었습니다.', 'info')
          return
        }
      }

      // 기타 오류 처리
      let errorMessage = result.error || result.message || '기간 저장 실패'

      // 겹치는 기간이 있는 경우 상세 정보 표시
      if (result.overlapping_periods && result.overlapping_periods.length > 0) {
        const overlapDetails = result.overlapping_periods
          .map((p) => `${p.year}년 ${p.period_name} (${p.start_date} ~ ${p.end_date})`)
          .join(', ')
        errorMessage += `\n\n겹치는 기간: ${overlapDetails}`
      }

      throw new Error(errorMessage)
    }

    displayToast(result.message || '기간이 저장되었습니다.', 'success')
    closePeriodModal()
    await loadPeriodStatus()
  } catch (err) {
    console.error('기간 저장 오류:', err)
    // 여러 줄 메시지 처리
    const message = err.message.split('\n')[0] // 첫 번째 줄만 토스트에 표시
    displayToast(message, 'error')

    // 전체 에러 메시지는 콘솔에 출력
    if (err.message.includes('\n')) {
      console.warn('전체 에러 메시지:', err.message)
    }
  }
}

/**
 * 기간 재개 후 수정
 */
const reopenAndEdit = async () => {
  try {
    console.log('[DEBUG] 기간 재개 후 수정 시작:', editingPeriod.value.period_id)

    // 1. 기간 재개
    const reopenResponse = await fetch(
      `/api/security-education/periods/${editingPeriod.value.period_id}/reopen`,
      {
        method: 'POST',
        credentials: 'include',
      },
    )

    const reopenResult = await reopenResponse.json()

    if (!reopenResponse.ok) {
      throw new Error(reopenResult.error || '재개 실패')
    }

    displayToast('기간이 재개되었습니다. 수정을 진행합니다.', 'success')

    // 2. 수정 재시도
    const updateResponse = await fetch(
      `/api/security-education/periods/${editingPeriod.value.period_id}`,
      {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(periodForm.value),
      },
    )

    const updateResult = await updateResponse.json()

    if (!updateResponse.ok) {
      throw new Error(updateResult.error || '수정 실패')
    }

    displayToast(updateResult.message || '기간이 수정되었습니다.', 'success')
    closePeriodModal()
    await loadPeriodStatus()
    await loadEducationData()
  } catch (err) {
    console.error('재개 후 수정 오류:', err)
    displayToast(err.message, 'error')
  }
}

/**
 * 기간 완료 처리
 */
const completePeriod = async (period) => {
  if (!confirm(`${period.period_name} 기간을 완료 처리하시겠습니까?`)) return

  try {
    const response = await fetch(`/api/security-education/periods/${period.period_id}/complete`, {
      method: 'POST',
      credentials: 'include',
    })

    const result = await response.json()

    if (!response.ok) {
      throw new Error(result.error || '완료 처리 실패')
    }

    displayToast(result.message, 'success')
    await loadPeriodStatus()
    await loadEducationData()
  } catch (err) {
    console.error('완료 처리 오류:', err)
    displayToast(err.message, 'error')
  }
}

/**
 * 기간 재개 처리
 */
const reopenPeriod = async (period) => {
  if (!confirm(`${period.period_name} 기간을 재개하시겠습니까?`)) return

  try {
    const response = await fetch(`/api/security-education/periods/${period.period_id}/reopen`, {
      method: 'POST',
      credentials: 'include',
    })

    const result = await response.json()

    if (!response.ok) {
      throw new Error(result.error || '재개 처리 실패')
    }

    displayToast(result.message, 'success')
    await loadPeriodStatus()
    await loadEducationData()
  } catch (err) {
    console.error('재개 처리 오류:', err)
    displayToast(err.message, 'error')
  }
}

/**
 * 기간 삭제
 */
// AdminSecurityEducationManagement.vue - 수정된 deletePeriod 함수

const deletePeriod = async (period) => {
  if (!confirm(`${period.period_name} 기간을 삭제하시겠습니까?`)) return

  try {
    console.log('[DEBUG] 교육 기간 삭제 요청:', period.period_id)

    // 1차 삭제 시도 (일반 삭제)
    const response = await fetch(`/api/security-education/periods/${period.period_id}`, {
      method: 'DELETE',
      credentials: 'include',
    })

    const result = await response.json()
    console.log('[DEBUG] 삭제 응답:', response.status, result)

    // ✅ 성공한 경우
    if (response.ok) {
      displayToast(result.message, 'success')
      await loadPeriodStatus()
      return
    }

    // ✅ 400 오류이고 확인이 필요한 경우
    if (response.status === 400 && result.requires_confirmation) {
      console.log('[DEBUG] 확인 필요:', result.education_count, '건의 교육 기록')

      // 강제 삭제 확인
      const forceDelete = confirm(
        `${result.error}\n\n모든 관련 데이터를 포함하여 완전히 삭제하시겠습니까?\n\n※ 이 작업은 되돌릴 수 없습니다.`,
      )

      if (forceDelete) {
        await forceDeletePeriod(period.period_id)
      } else {
        displayToast('삭제가 취소되었습니다.', 'info')
      }
      return
    }

    // ✅ 기타 오류인 경우
    throw new Error(result.error || result.message || '삭제 실패')
  } catch (err) {
    console.error('기간 삭제 오류:', err)
    displayToast(err.message, 'error')
  }
}

/**
 * 기간 강제 삭제 (교육 기록 포함)
 */
const forceDeletePeriod = async (periodId) => {
  try {
    console.log('[DEBUG] 교육 기간 강제 삭제 요청:', periodId)

    const response = await fetch(`/api/security-education/periods/${periodId}/force-delete`, {
      method: 'DELETE',
      credentials: 'include',
    })

    const result = await response.json()

    if (!response.ok) {
      throw new Error(result.error || '강제 삭제 실패')
    }

    displayToast(result.message, 'success')
    await loadPeriodStatus()
    await loadEducationData() // 교육 데이터도 새로고침
  } catch (err) {
    console.error('강제 삭제 오류:', err)
    displayToast(err.message, 'error')
  }
}

/**
 * 기간 모달 닫기
 */
const closePeriodModal = () => {
  showPeriodModal.value = false
  editingPeriod.value = null
  periodForm.value = {
    education_year: selectedYear.value,
    period_name: '',
    education_type: '오프라인',
    start_date: '',
    end_date: '',
    description: '',
    auto_pass_setting: true,
  }
}

// ===== 파일 업로드 메서드 =====

/**
 * 파일 선택 처리
 */
const handleFileSelect = (event) => {
  if (!selectedUploadPeriod.value) {
    displayToast('먼저 교육 기간을 선택해주세요.', 'warning')
    return
  }

  const file = event.target.files[0]
  if (file) {
    selectedFile.value = file
    parseFile(file)
  }
}

/**
 * 파일 드래그 앤 드롭 처리
 */
const handleFileDrop = (event) => {
  event.preventDefault()
  isDragOver.value = false

  if (!selectedUploadPeriod.value) {
    displayToast('먼저 교육 기간을 선택해주세요.', 'warning')
    return
  }

  const file = event.dataTransfer.files[0]
  if (file) {
    selectedFile.value = file
    parseFile(file)
  }
}

/**
 * 파일 선택 트리거
 */
const triggerFileSelect = () => {
  if (!selectedUploadPeriod.value) {
    displayToast('먼저 교육 기간을 선택해주세요.', 'warning')
    return
  }
  const fileInput = document.querySelector('input[type="file"]')
  fileInput?.click()
}

/**
 * 선택된 파일 제거
 */
const removeSelectedFile = () => {
  selectedFile.value = null
  uploadPreview.value = []
}

/**
 * 교육 기간 변경 처리
 */
const onPeriodChange = () => {
  if (selectedFile.value) {
    // 기간 변경 시 파일 초기화하고 재검증 필요 알림
    selectedFile.value = null
    uploadPreview.value = []
    validationWarnings.value = []
    displayToast('교육 기간이 변경되어 파일을 다시 선택해주세요.', 'info')
  }
}

/**
 * 파일 파싱 (CSV/Excel 처리)
 */
const parseFile = async (file) => {
  try {
    const fileName = file.name.toLowerCase()
    let records = []

    if (fileName.endsWith('.csv')) {
      // CSV 파일 처리
      const text = await file.text()
      const lines = text.split('\n')
      const headers = lines[0].split(',').map((h) => h.trim().replace(/"/g, ''))

      for (let i = 1; i < lines.length; i++) {
        if (lines[i].trim()) {
          const values = lines[i].split(',').map((v) => v.trim().replace(/"/g, ''))
          const record = {}
          headers.forEach((header, index) => {
            record[header] = values[index] || ''
          })
          records.push(record)
        }
      }
    } else if (fileName.endsWith('.xlsx') || fileName.endsWith('.xls')) {
      // Excel 파일 처리
      const arrayBuffer = await file.arrayBuffer()
      const XLSX = window.XLSX || (await import('xlsx'))

      const workbook = XLSX.read(arrayBuffer, { type: 'array' })
      const sheetName = workbook.SheetNames[0]
      const worksheet = workbook.Sheets[sheetName]

      records = XLSX.utils.sheet_to_json(worksheet, {
        raw: false,
        dateNF: 'yyyy-mm-dd hh:mm:ss',
      })
    } else {
      throw new Error('지원하지 않는 파일 형식입니다. CSV 또는 Excel 파일을 선택해주세요.')
    }

    // 필드 매핑 및 정규화
    const processedRecords = normalizeFieldNames(records)

    // 클라이언트 사이드 기본 검증
    const validation = validateUploadData(processedRecords)

    uploadPreview.value = processedRecords
    validationWarnings.value = validation.warnings

    if (validation.errors.length > 0) {
      displayToast(`파일 검증 실패: ${validation.errors[0]}`, 'error')
      uploadPreview.value = []
      return
    }

    displayToast(`${processedRecords.length}개의 레코드가 준비되었습니다.`, 'success')
  } catch (err) {
    console.error('파일 파싱 실패:', err)
    displayToast(`파일 파싱에 실패했습니다: ${err.message}`, 'error')
    uploadPreview.value = []
    validationWarnings.value = []
  }
}

/**
 * 필드명 정규화 (한글 → 영문)
 */
const normalizeFieldNames = (records) => {
  const fieldMapping = {
    // 새로운 CSV 형식 필드 매핑
    이름: 'username',
    사용자명: 'username',
    사용자이름: 'username',
    부서: 'department',
    소속: 'department',
    소속부서: 'department',
    수강과정: 'education_type',
    교육과정: 'education_type',
    과정명: 'education_type',
    과정: 'education_type',
    수료: 'completed_count',
    수료횟수: 'completed_count',
    완료: 'completed_count',
    완료횟수: 'completed_count',
    미수료: 'incomplete_count',
    미완료: 'incomplete_count',
    미이수: 'incomplete_count',
    실패: 'incomplete_count',
    실패횟수: 'incomplete_count',

    // 영문 헤더도 지원
    username: 'username',
    department: 'department',
    education_type: 'education_type',
    completed_count: 'completed_count',
    incomplete_count: 'incomplete_count',
  }

  return records
    .map((record) => {
      const processedRecord = {}

      // 필드명 매핑
      Object.keys(record).forEach((key) => {
        const normalizedKey = key.trim().replace(/\s+/g, '')
        const mappedKey = fieldMapping[normalizedKey] || fieldMapping[key] || key
        processedRecord[mappedKey] = record[key]
      })

      // 타입 변환 및 기본값 설정
      processedRecord.completed_count = Math.max(0, parseInt(processedRecord.completed_count) || 0)
      processedRecord.incomplete_count = Math.max(
        0,
        parseInt(processedRecord.incomplete_count) || 0,
      )

      // 문자열 필드 정리
      if (processedRecord.username)
        processedRecord.username = processedRecord.username.toString().trim()
      if (processedRecord.department)
        processedRecord.department = processedRecord.department.toString().trim()
      if (processedRecord.education_type)
        processedRecord.education_type = processedRecord.education_type.toString().trim()

      return processedRecord
    })
    .filter((record) => record.username && record.department && record.education_type)
}

/**
 * 업로드 데이터 검증
 */
const validateUploadData = (records) => {
  const warnings = []
  const errors = []

  if (records.length === 0) {
    errors.push('유효한 데이터가 없습니다.')
    return { warnings, errors }
  }

  // 필수 필드 검증
  const requiredFields = [
    'username',
    'department',
    'education_type',
    'completed_count',
    'incomplete_count',
  ]

  for (let i = 0; i < records.length; i++) {
    const record = records[i]
    const missingFields = requiredFields.filter((field) => !record[field] && record[field] !== 0)

    if (missingFields.length > 0) {
      errors.push(`행 ${i + 1}: 필수 필드 누락 (${missingFields.join(', ')})`)
      continue
    }

    // 수료/미수료 횟수 유효성
    const completed = parseInt(record.completed_count) || 0
    const incomplete = parseInt(record.incomplete_count) || 0

    if (completed < 0 || incomplete < 0) {
      errors.push(`행 ${i + 1}: 수료/미수료 횟수는 0 이상이어야 합니다`)
    }

    if (completed + incomplete === 0) {
      warnings.push(`행 ${i + 1} (${record.username}): 수료와 미수료가 모두 0입니다`)
    }

    // 기존 검증도 유지
    if (!record.username?.trim()) {
      errors.push(`행 ${i + 1}: 사용자명이 비어있습니다`)
    }

    if (!record.department?.trim()) {
      errors.push(`행 ${i + 1}: 부서명이 비어있습니다`)
    }

    if (!record.education_type?.trim()) {
      errors.push(`행 ${i + 1}: 수강과정이 비어있습니다`)
    }
  }

  return { warnings, errors }
}

/**
 * 업로드 실행
 */
const executeUpload = async () => {
  if (!selectedUploadPeriod.value) {
    displayToast('교육 기간을 선택해주세요.', 'warning')
    return
  }

  if (uploadPreview.value.length === 0) {
    displayToast('업로드할 파일을 선택해주세요.', 'warning')
    return
  }

  uploading.value = true

  try {
    // 새로운 필드명으로 데이터 전송
    const uploadData = {
      period_id: selectedUploadPeriod.value,
      records: uploadPreview.value.map((record) => ({
        // 새로운 API가 기대하는 필드명으로 매핑
        이름: record.username,
        부서: record.department,
        수강과정: record.education_type,
        수료: record.completed_count,
        미수료: record.incomplete_count,
      })),
    }

    console.log('[DEBUG] 업로드 데이터 전송:', {
      period_id: uploadData.period_id,
      record_count: uploadData.records.length,
      sample_record: uploadData.records[0],
    })

    const response = await fetch('/api/security-education/bulk-upload', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(uploadData),
    })

    const result = await response.json()

    if (!response.ok) {
      throw new Error(result.error || '업로드 실패')
    }

    // 성공 처리
    const successMsg =
      `${selectedPeriodInfo.value.period_name}에 업로드 완료!\n` +
      `✅ 성공: ${result.success_count}건\n` +
      (result.update_count > 0 ? `🔄 업데이트: ${result.update_count}건\n` : '') +
      (result.error_count > 0 ? `❌ 오류: ${result.error_count}건` : '')

    displayToast(successMsg, 'success')

    // 오류 상세 정보 표시
    if (result.error_count > 0 && result.errors) {
      console.warn('업로드 오류 상세:', result.errors)
      setTimeout(() => {
        displayToast(`오류 상세: ${result.errors.slice(0, 3).join(', ')}`, 'warning')
      }, 2000)
    }

    closeBulkUploadModal()
    await loadEducationData()
  } catch (err) {
    console.error('업로드 오류:', err)
    displayToast(`업로드 실패: ${err.message}`, 'error')
  } finally {
    uploading.value = false
  }
}

/**
 * 업로드 모달 닫기
 */
const closeBulkUploadModal = () => {
  showBulkUploadModal.value = false
  selectedFile.value = null
  uploadPreview.value = []
  selectedUploadPeriod.value = ''
  validationWarnings.value = []
}

// ===== 교육 기록 관리 메서드 =====

/**
 * 교육 기록 수정 모달 열기
 */
const editRecord = (record) => {
  // 새로운 스키마 데이터를 기존 형식으로 변환
  editingRecord.value = {
    education_id: record.education_id,
    user_id: record.user_id,
    username: record.username,
    department: record.department,
    education_year: record.education_year,
    education_type: record.education_type,
    education_date: record.education_date,
    // 새로운 필드들
    course_name: record.course_name,
    completed_count: record.completed_count || 0,
    incomplete_count: record.incomplete_count || 0,
    total_courses: record.total_courses || 1,
    completion_rate: record.completion_rate || 0,
    // 기존 필드들
    completion_status: record.completion_status,
    exclude_from_scoring: record.exclude_from_scoring,
    exclude_reason: record.exclude_reason,
    notes: record.notes,
    period_id: record.period_id,
  }
  showEditModal.value = true
}

/**
 * 교육 기록 저장
 */
const saveRecord = async () => {
  if (saving.value) return

  saving.value = true

  try {
    // 필수 필드 검증
    if (!editingRecord.value.education_id) {
      throw new Error('교육 ID가 없습니다.')
    }

    // 수정할 데이터 준비
    const updateData = {
      education_id: editingRecord.value.education_id,
      user_id: editingRecord.value.user_id,
      education_year: editingRecord.value.education_year,
      education_type: editingRecord.value.education_type,
      education_date: editingRecord.value.education_date,
      // 새로운 스키마 필드들
      course_name: editingRecord.value.course_name,
      completed_count: parseInt(editingRecord.value.completed_count) || 0,
      incomplete_count: parseInt(editingRecord.value.incomplete_count) || 0,
      // 기존 필드들
      exclude_from_scoring: editingRecord.value.exclude_from_scoring || false,
      exclude_reason: editingRecord.value.exclude_reason || '',
      notes: editingRecord.value.notes || '',
      period_id: editingRecord.value.period_id,
    }

    console.log('[DEBUG] 교육 기록 수정 요청:', updateData)

    const response = await fetch('/api/security-education/update', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify(updateData),
    })

    const result = await response.json()

    if (!response.ok) {
      throw new Error(result.error || '수정 실패')
    }

    displayToast(result.message || '교육 기록이 성공적으로 수정되었습니다.', 'success')
    closeEditModal()
    await loadEducationData() // 데이터 새로고침
  } catch (err) {
    console.error('교육 기록 수정 오류:', err)
    displayToast(err.message, 'error')
  } finally {
    saving.value = false
  }
}

/**
 * 교육 기록 삭제
 */
const deleteRecord = async (record) => {
  if (!confirm('이 교육 기록을 삭제하시겠습니까?')) return

  try {
    const response = await fetch('/api/security-education/delete', {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        user_id: record.user_id,
        period_id: record.period_id,
        education_type: record.education_type,
      }),
    })

    const result = await response.json()

    if (!response.ok) {
      throw new Error(result.error || '삭제 실패')
    }

    displayToast(result.message, 'success')
    await loadEducationData()
  } catch (err) {
    console.error('기록 삭제 오류:', err)
    displayToast(err.message, 'error')
  }
}

/**
 * 편집 모달 닫기
 */
const closeEditModal = () => {
  showEditModal.value = false
  editingRecord.value = {}
}

// ===== 선택 및 일괄 작업 =====

/**
 * 전체 선택/해제 토글
 */
const toggleSelectAll = () => {
  if (selectAll.value) {
    selectedRecords.value = [...paginatedRecords.value]
  } else {
    selectedRecords.value = []
  }
}

/**
 * 전체 선택 상태 업데이트
 */
const updateSelectAll = () => {
  selectAll.value =
    paginatedRecords.value.length > 0 &&
    selectedRecords.value.length === paginatedRecords.value.length
}

/**
 * 개별 제외 상태 토글
 */
const toggleExceptionStatus = async (record) => {
  if (!confirm(`${record.username}의 교육 제외 상태를 변경하시겠습니까?`)) return

  try {
    const newExcludeStatus = !record.exclude_from_scoring

    const response = await fetch('/api/security-education/toggle-exception', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        user_id: record.user_id,
        period_id: record.period_id,
        education_type: record.education_type,
        exclude: newExcludeStatus,
        exclude_reason: newExcludeStatus ? '관리자 설정' : '',
      }),
    })

    const result = await response.json()

    if (!response.ok) {
      throw new Error(result.error || '제외 상태 변경 실패')
    }

    record.exclude_from_scoring = newExcludeStatus
    record.exclude_reason = newExcludeStatus ? '관리자 설정' : ''

    displayToast(result.message || '제외 상태가 변경되었습니다.', 'success')
    await loadEducationData()
  } catch (err) {
    console.error('제외 상태 변경 오류:', err)
    displayToast(err.message, 'error')
  }
}

/**
 * 일괄 제외 상태 토글
 */
const bulkToggleException = async () => {
  if (selectedRecords.value.length === 0) return

  try {
    const response = await fetch('/api/security-education/bulk-toggle-exception', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        records: selectedRecords.value.map((r) => ({
          user_id: r.user_id,
          period_id: r.period_id,
          education_type: r.education_type,
        })),
      }),
    })

    const result = await response.json()

    if (!response.ok) {
      throw new Error(result.error || '일괄 제외 상태 변경 실패')
    }

    displayToast(result.message, 'success')
    selectedRecords.value = []
    await loadEducationData()
  } catch (err) {
    console.error('일괄 제외 상태 변경 오류:', err)
    displayToast(err.message, 'error')
  }
}

// ===== 데이터 내보내기 =====

/**
 * 템플릿 다운로드
 */
const downloadTemplate = async () => {
  try {
    const response = await fetch('/api/security-education/template/download', {
      credentials: 'include',
    })

    if (!response.ok) throw new Error('템플릿 다운로드 실패')

    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = '정보보호교육_업로드_템플릿.csv'
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
  } catch (err) {
    console.error('템플릿 다운로드 오류:', err)
    displayToast('템플릿 다운로드에 실패했습니다.', 'error')
  }
}

// ===== 유틸리티 메서드 =====

/**
 * 날짜 포맷팅
 */
const formatDate = (dateString) => {
  if (!dateString) return '-'
  try {
    return new Date(dateString).toLocaleDateString('ko-KR')
  } catch {
    return dateString
  }
}

/**
 * 짧은 날짜 포맷팅
 */
const formatDateShort = (dateString) => {
  if (!dateString) return '-'
  try {
    return new Date(dateString).toLocaleDateString('ko-KR', {
      month: '2-digit',
      day: '2-digit',
    })
  } catch {
    return dateString
  }
}

/**
 * 날짜 범위 포맷팅
 */
const formatDateRange = (startDate, endDate) => {
  const start = new Date(startDate).toLocaleDateString('ko-KR')
  const end = new Date(endDate).toLocaleDateString('ko-KR')
  return `${start} ~ ${end}`
}

/**
 * 파일 크기 포맷팅
 */
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * 교육 유형별 CSS 클래스 반환
 */
const getTypeClass = (educationType) => {
  const typeMap = {
    온라인: 'type-online',
    오프라인: 'type-offline',
    기본교육: 'type-basic',
  }
  return typeMap[educationType] || 'type-default'
}

/**
 * 🔄 단순화된 수료율별 CSS 클래스 반환
 */
const getRateClass = (rate) => {
  if (rate >= 100) return 'rate-excellent'  // 🔄 100%만 excellent
  return 'rate-poor'  // 🔄 100% 외는 모두 poor
}

/**
 * 🔄 단순화된 수료율 텍스트 CSS 클래스 반환
 */
const getRateTextClass = (rate) => {
  if (rate >= 100) return 'text-excellent'  // 🔄 100%만 excellent
  return 'text-danger'  // 🔄 100% 외는 모두 danger
}

/**
 * 🔄 단순화된 상태별 CSS 클래스 반환
 */
const getStatusClass = (record) => {
  if (record.exclude_from_scoring) return 'status-excluded'

  // 새로운 스키마 기반 - 단순화
  if (record.completion_rate !== undefined) {
    if (record.completion_rate >= 100) return 'status-completed'  // 🔄 100%만 완료
    return 'status-incomplete'  // 🔄 100% 외는 모두 미완료
  }

  // 레거시 스키마 기반
  if (record.completion_status === 1) return 'status-completed'
  return 'status-incomplete'
}

/**
 * 🔄 단순화된 상태 텍스트 반환
 */
const getStatusText = (record) => {
  if (record.status_text) {
    // 🔄 서버에서 제공된 상태 텍스트도 단순화
    if (record.status_text.includes('완료') || record.status_text.includes('수료')) {
      return '수료'
    }
    if (record.status_text.includes('제외')) {
      return '제외'
    }
    return '미수료'
  }

  if (record.exclude_from_scoring) return '제외'

  // 새로운 스키마 기반 - 단순화
  if (record.completion_rate !== undefined) {
    if (record.completion_rate >= 100) return '수료'  // 🔄 100%만 수료
    return '미수료'  // 🔄 100% 외는 모두 미수료
  }

  // 레거시 기반
  return record.completion_status === 1 ? '수료' : '미수료'
}

/**
 * 기간 상태 텍스트 반환
 */
const getPeriodStatusText = (period) => {
  if (period.is_completed) return '완료됨'

  const now = new Date()
  const startDate = new Date(period.start_date)
  const endDate = new Date(period.end_date)

  if (now < startDate) return '예정'
  if (now > endDate) return '종료됨'
  return '진행중'
}

/**
 * 기간 상태 CSS 클래스 반환
 */
const getPeriodStatusClass = (period) => {
  if (period.is_completed) return 'status-completed'

  const now = new Date()
  const startDate = new Date(period.start_date)
  const endDate = new Date(period.end_date)

  if (now < startDate) return 'status-upcoming'
  if (now > endDate) return 'status-ended'
  return 'status-active'
}

/**
 * 카드 헤더 전용: 기간 상태 텍스트 변환
 * determine_period_status 함수에서 반환되는 값들을 변환
 * @param {Object} record - 기간 레코드 객체 (record.status 포함)
 * @returns {string} 변환된 상태 텍스트
 */
const getCardHeaderStatusText = (record) => {
  const status = record.status

  switch (status) {
    case 'completed':
      return '완료됨'
    case 'not_started':
      return '시작전'
    case 'in_progress':
      return '진행중'
    case 'expired':
      return '기간만료'
    case 'unknown':
      return '알 수 없음'
    default:
      return status || '미정'
  }
}

/**
 * 카드 헤더 전용: 기간 상태 CSS 클래스 반환
 * @param {Object} record - 기간 레코드 객체
 * @returns {string} CSS 클래스명
 */
const getCardHeaderStatusClass = (record) => {
  const status = record.status

  switch (status) {
    case 'completed':
      return 'card-status-completed'
    case 'not_started':
      return 'card-status-not-started'
    case 'in_progress':
      return 'card-status-in-progress'
    case 'expired':
      return 'card-status-expired'
    case 'unknown':
      return 'card-status-unknown'
    default:
      return 'card-status-default'
  }
}

/**
 * 업로드 미리보기 통계 계산
 */
const getTotalCompletedCount = () => {
  return uploadPreview.value.reduce(
    (sum, record) => sum + (parseInt(record.completed_count) || 0),
    0,
  )
}

const getTotalIncompleteCount = () => {
  return uploadPreview.value.reduce(
    (sum, record) => sum + (parseInt(record.incomplete_count) || 0),
    0,
  )
}

/**
 * 토스트 메시지 표시
 */
const displayToast = (message, type = 'success') => {
  toastMessage.value = message
  toastType.value = type
  showToast.value = true

  setTimeout(() => {
    showToast.value = false
  }, 3000)
}

// ===== 감시자 (Watchers) =====

// 연도 변경 시 데이터 새로고침
watch(selectedYear, () => {
  loadPeriodStatus()
  loadEducationData()
  loadAvailablePeriodsForUpload()
})

// 업로드 기간 선택 변경 시 파일 초기화
watch(selectedUploadPeriod, (newValue, oldValue) => {
  if (newValue !== oldValue && selectedFile.value) {
    selectedFile.value = null
    uploadPreview.value = []
    displayToast('교육 기간이 변경되어 파일 선택을 초기화했습니다.', 'info')
  }
})
</script>

<style scoped>
@import '../styles/AdminSecurityEducationManagement.css';
</style>