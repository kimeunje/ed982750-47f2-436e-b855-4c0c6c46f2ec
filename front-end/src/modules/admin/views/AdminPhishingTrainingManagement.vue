<template>
  <div class="admin-training">
    <!-- ===== 관리 헤더 ===== -->
    <div class="admin-header">
      <h1>악성메일 모의훈련 관리</h1>
      <div class="admin-nav">
        <RouterLink to="/admin/training" class="nav-item active">모의훈련 관리</RouterLink>
        <RouterLink to="/admin/education" class="nav-item">교육 관리</RouterLink>
        <RouterLink to="/admin/manual-check" class="nav-item">수시 점검 관리</RouterLink>
        <RouterLink to="/admin/exceptions" class="nav-item">제외 설정</RouterLink>
      </div>
    </div>

    <div class="management-content">
      <!-- ===== 훈련 기간 관리 섹션 ===== -->
      <div class="period-management-section">
        <div class="section-header">
          <h3>🗓️ 훈련 기간 관리</h3>
          <button @click="openPeriodModal" class="primary-button">
            <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
              <path
                d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4z"
              />
            </svg>
            기간 추가
          </button>
        </div>

        <!-- 훈련 기간 카드들 -->
        <div
          class="period-cards"
          v-if="periodStatus.training_types && Object.keys(periodStatus.training_types).length > 0"
        >
          <div
            v-for="(typeData, trainingType) in periodStatus.training_types"
            :key="trainingType"
            class="training-type-group"
          >
            <!-- 훈련 유형 헤더에 통계 정보 추가 -->
            <div class="type-header-with-stats">
              <div class="type-title-section">
                <h4 class="type-header">{{ trainingType }} 훈련</h4>
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

                <!-- 카드 메타 정보 -->
                <div class="card-meta">
                  <div class="meta-item">
                    <span class="meta-label">기간:</span>
                    <span class="meta-value">{{
                      formatDateRange(period.start_date, period.end_date)
                    }}</span>
                  </div>
                  <div class="meta-item">
                    <span class="meta-label">유형:</span>
                    <span class="meta-value">{{ period.training_type }}</span>
                  </div>
                  <div v-if="period.description" class="meta-item">
                    <span class="meta-label">설명:</span>
                    <span class="meta-value">{{ period.description }}</span>
                  </div>
                </div>

                <!-- 통계 정보 -->
                <div class="stats-section" v-if="period.stats">
                  <div class="stats-row">
                    <div class="stat-item success">
                      <span class="stat-label">성공</span>
                      <span class="stat-value">{{ period.stats.success_count || 0 }}</span>
                    </div>
                    <div class="stat-item fail">
                      <span class="stat-label">실패</span>
                      <span class="stat-value">{{ period.stats.fail_count || 0 }}</span>
                    </div>
                    <div class="stat-item no-response">
                      <span class="stat-label">무응답</span>
                      <span class="stat-value">{{ period.stats.no_response_count || 0 }}</span>
                    </div>
                    <div class="stat-item total">
                      <span class="stat-label">전체</span>
                      <span class="stat-value">{{ period.stats.total_targets || 0 }}</span>
                    </div>
                  </div>
                  <div class="success-rate" :class="getRateClass(period.stats.success_rate || 0)">
                    성공률: {{ (period.stats.success_rate || 0).toFixed(1) }}%
                  </div>
                </div>

                <!-- 액션 버튼들 -->
                <div class="card-actions">
                  <button
                    @click="editPeriod(period)"
                    class="action-button edit"
                    :disabled="period.is_completed && !canEdit"
                  >
                    <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
                      <path
                        d="M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708L8.5 11.207l-3 1a.5.5 0 0 1-.65-.65l1-3L12.146.146zM11.207 1.5L13.5 3.793 12.793 4.5 10.5 2.207 11.207 1.5z"
                      />
                    </svg>
                    수정
                  </button>

                  <button
                    @click="viewStats(period)"
                    class="action-button stats"
                    v-if="period.stats && period.stats.total_targets > 0"
                  >
                    <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
                      <path
                        d="M4 11H2v3h2v-3zm5-4H7v7h2V7zm5-5v12h-2V2h2zm-2-1a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1h-2zM6 7a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v7a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V7zM1 11a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1H2a1 1 0 0 1-1-1v-3z"
                      />
                    </svg>
                    상세 통계
                  </button>

                  <button
                    v-if="!period.is_completed"
                    @click="completePeriod(period)"
                    class="action-button complete"
                  >
                    <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
                      <path
                        d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"
                      />
                    </svg>
                    완료 처리
                  </button>

                  <button
                    v-if="period.is_completed"
                    @click="reopenPeriod(period)"
                    class="action-button reopen"
                  >
                    <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
                      <path d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2v1z" />
                      <path
                        d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466z"
                      />
                    </svg>
                    재개
                  </button>

                  <button @click="deletePeriod(period)" class="action-button delete">
                    <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
                      <path
                        d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"
                      />
                      <path
                        fill-rule="evenodd"
                        d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"
                      />
                    </svg>
                    삭제
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 기간이 없을 때 표시 -->
        <div v-else class="empty-periods">
          <div class="empty-content">
            <svg width="48" height="48" fill="currentColor" viewBox="0 0 16 16">
              <path
                d="M3.5 0a.5.5 0 0 1 .5.5V1h8V.5a.5.5 0 0 1 1 0V1h1a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V3a2 2 0 0 1 2-2h1V.5a.5.5 0 0 1 .5-.5zM1 4v10a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V4H1z"
              />
            </svg>
            <h4>등록된 훈련 기간이 없습니다</h4>
            <p>새로운 훈련 기간을 추가해주세요.</p>
          </div>
        </div>
      </div>

      <!-- ===== 데이터 관리 섹션 ===== -->
      <div class="data-management-section">
        <div class="section-header">
          <h3>📊 데이터 관리</h3>
          <div class="header-actions">
            <button @click="openUploadModal" class="secondary-button">
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
            <select v-model="selectedYear" @change="loadTrainingData">
              <option v-for="year in availableYears" :key="year" :value="year">{{ year }}년</option>
            </select>
          </div>

          <div class="filter-group">
            <label>훈련유형:</label>
            <select v-model="selectedTrainingType" @change="loadTrainingData">
              <option value="">전체</option>
              <option value="이메일 피싱">이메일 피싱</option>
              <option value="SMS 피싱">SMS 피싱</option>
              <option value="전화 피싱">전화 피싱</option>
            </select>
          </div>

          <div class="filter-group">
            <label>결과:</label>
            <select v-model="selectedResult" @change="loadTrainingData">
              <option value="">전체</option>
              <option value="success">성공</option>
              <option value="fail">실패</option>
              <option value="no_response">무응답</option>
            </select>
          </div>

          <div class="search-group">
            <label>검색:</label>
            <input
              type="text"
              v-model="searchQuery"
              @input="searchTrainingData"
              placeholder="사용자명 또는 부서 검색..."
              class="search-input"
            />
          </div>
        </div>

        <!-- 훈련 기록 테이블 -->
        <div class="records-table-section">
          <div class="table-header">
            <h4>훈련 기록 ({{ filteredRecords.length }}건)</h4>
            <div class="table-actions">
              <select v-model="recordsPerPage" @change="currentPage = 1" class="records-per-page">
                <option :value="10">10개씩</option>
                <option :value="20">20개씩</option>
                <option :value="50">50개씩</option>
                <option :value="100">100개씩</option>
              </select>
            </div>
          </div>

          <div class="table-container" v-if="filteredRecords.length > 0">
            <table class="records-table">
              <thead>
                <tr>
                  <th>사용자</th>
                  <th>부서</th>
                  <th>훈련기간</th>
                  <th>이메일</th>
                  <th>메일유형</th>
                  <th>로그유형</th>
                  <th>발송시각</th>
                  <th>수행시각</th>
                  <th>응답시간</th>
                  <th>결과</th>
                  <th>제외여부</th>
                  <th>작업</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="record in paginatedRecords"
                  :key="record.training_id"
                  :class="{ excluded: record.exclude_from_scoring }"
                >
                  <td class="user-cell">
                    <div class="user-info">
                      <span class="username">{{ record.username }}</span>
                    </div>
                  </td>
                  <td>{{ record.department }}</td>
                  <td class="period-cell">
                    <div class="period-info">
                      <span class="period-name">{{ record.period_name }}</span>
                      <span class="training-type">{{ record.training_type }}</span>
                    </div>
                  </td>
                  <td class="email-cell">{{ record.target_email }}</td>
                  <td>{{ record.mail_type }}</td>
                  <td>{{ record.log_type }}</td>
                  <td class="time-cell">{{ formatDateTime(record.email_sent_time) }}</td>
                  <td class="time-cell">{{ formatDateTime(record.action_time) }}</td>
                  <td class="response-time-cell">
                    <span v-if="record.response_time_minutes">
                      {{ formatResponseTime(record.response_time_minutes) }}
                    </span>
                    <span v-else class="no-response">-</span>
                  </td>
                  <td class="result-cell">
                    <span class="result-badge" :class="getResultClass(record.training_result)">
                      {{ getResultText(record.training_result) }}
                    </span>
                  </td>
                  <td class="exclude-cell">
                    <span v-if="record.exclude_from_scoring" class="exclude-badge"> 제외 </span>
                    <span v-else class="include-badge"> 포함 </span>
                  </td>
                  <td class="actions-cell">
                    <div class="record-actions">
                      <button @click="editRecord(record)" class="action-btn edit-btn" title="수정">
                        <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
                          <path
                            d="M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708L8.5 11.207l-3 1a.5.5 0 0 1-.65-.65l1-3L12.146.146zM11.207 1.5L13.5 3.793 12.793 4.5 10.5 2.207 11.207 1.5z"
                          />
                        </svg>
                      </button>
                      <button
                        @click="toggleExclude(record)"
                        class="action-btn exclude-btn"
                        :class="{ active: record.exclude_from_scoring }"
                        :title="record.exclude_from_scoring ? '포함' : '제외'"
                      >
                        <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
                          <path
                            d="M2.146 2.854a.5.5 0 1 1 .708-.708L8 7.293l5.146-5.147a.5.5 0 0 1 .708.708L8.707 8l5.147 5.146a.5.5 0 0 1-.708.708L8 8.707l-5.146 5.147a.5.5 0 0 1-.708-.708L7.293 8 2.146 2.854Z"
                          />
                        </svg>
                      </button>
                      <button
                        @click="deleteRecord(record)"
                        class="action-btn delete-btn"
                        title="삭제"
                      >
                        <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
                          <path
                            d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"
                          />
                          <path
                            fill-rule="evenodd"
                            d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"
                          />
                        </svg>
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 빈 상태 -->
          <div v-else class="empty-records">
            <div class="empty-content">
              <svg width="48" height="48" fill="currentColor" viewBox="0 0 16 16">
                <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z" />
                <path
                  d="M7.002 11a1 1 0 1 1 2 0 1 1 0 0 1-2 0zM7.1 4.995a.905.905 0 1 1 1.8 0l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 4.995z"
                />
              </svg>
              <h4>훈련 기록이 없습니다</h4>
              <p>선택한 조건에 맞는 훈련 기록이 없습니다.</p>
            </div>
          </div>

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
      </div>
    </div>

    <!-- ===== 기간 생성/수정 모달 ===== -->
    <div v-if="showPeriodModal" class="modal-overlay" @click="closePeriodModal">
      <div class="modal-content period-modal" @click.stop>
        <div class="modal-header">
          <h3>
            {{ editingPeriod ? '훈련 기간 수정' : '새 훈련 기간 추가' }}
          </h3>
          <button @click="closePeriodModal" class="close-button">
            <svg width="20" height="20" fill="currentColor" viewBox="0 0 16 16">
              <path
                d="M2.146 2.146a.5.5 0 0 1 .708 0L8 7.293l5.146-5.147a.5.5 0 0 1 .708.708L8.707 8l5.147 5.146a.5.5 0 0 1-.708.708L8 8.707l-5.146 5.147a.5.5 0 0 1-.708-.708L7.293 8 2.146 2.854a.5.5 0 0 1 0-.708z"
              />
            </svg>
          </button>
        </div>

        <div class="modal-body">
          <form @submit.prevent="savePeriod">
            <div class="form-row">
              <div class="form-group">
                <label for="training_year">훈련 연도 *</label>
                <select
                  id="training_year"
                  v-model="periodForm.training_year"
                  required
                  class="form-input"
                >
                  <option v-for="year in availableYears" :key="year" :value="year">
                    {{ year }}년
                  </option>
                </select>
              </div>

              <div class="form-group">
                <label for="period_name">기간명 *</label>
                <input
                  type="text"
                  id="period_name"
                  v-model="periodForm.period_name"
                  placeholder="예: 1차 피싱 훈련"
                  required
                  class="form-input"
                />
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label for="training_type">훈련 유형 *</label>
                <select
                  id="training_type"
                  v-model="periodForm.training_type"
                  required
                  class="form-input"
                >
                  <option value="이메일 피싱">이메일 피싱</option>
                  <option value="SMS 피싱">SMS 피싱</option>
                  <option value="전화 피싱">전화 피싱</option>
                </select>
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label for="start_date">시작일 *</label>
                <input
                  type="date"
                  id="start_date"
                  v-model="periodForm.start_date"
                  required
                  class="form-input"
                />
              </div>

              <div class="form-group">
                <label for="end_date">종료일 *</label>
                <input
                  type="date"
                  id="end_date"
                  v-model="periodForm.end_date"
                  required
                  class="form-input"
                />
              </div>
            </div>

            <div class="form-group">
              <label for="description">설명</label>
              <textarea
                id="description"
                v-model="periodForm.description"
                placeholder="훈련에 대한 상세 설명을 입력하세요."
                class="form-input"
                rows="3"
              ></textarea>
            </div>

            <div class="form-group">
              <div class="checkbox-wrapper">
                <label class="checkbox-label">
                  <input
                    type="checkbox"
                    v-model="periodForm.auto_pass_setting"
                    class="checkbox-input"
                  />
                  <span class="checkbox-custom">
                    <span class="checkbox-checkmark">
                      <svg width="12" height="12" fill="currentColor" viewBox="0 0 16 16">
                        <path
                          d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"
                        />
                      </svg>
                    </span>
                    <span class="checkbox-text"> 자동 통과 처리 설정 </span>
                  </span>
                </label>
              </div>
              <small class="form-hint">
                체크하면 훈련 기간 완료 시 무응답한 사용자들을 자동으로 성공 처리합니다.
              </small>
            </div>

            <!-- 중복 체크 안내 -->
            <div v-if="duplicateWarning" class="warning-section">
              <div class="warning-message">
                <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                  <path
                    d="M8.982 1.566a1.13 1.13 0 0 0-1.96 0L.165 13.233c-.457.778.091 1.767.98 1.767h13.713c.889 0 1.438-.99.98-1.767L8.982 1.566zM8 5c.535 0 .954.462.9.995l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 5.995A.905.905 0 0 1 8 5zm.002 6a1 1 0 1 1 0 2 1 1 0 0 1 0-2z"
                  />
                </svg>
                {{ duplicateWarning }}
              </div>
            </div>

            <!-- 기존 기간 수정 시 추가 안내 -->
            <div v-if="editingPeriod && editingPeriod.is_completed" class="info-section">
              <div class="info-message">
                <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                  <path
                    d="m8.93 6.588-2.29.287-.082.38.45.083c.294.07.352.176.288.469l-.738 3.468c-.194.897.105 1.319.808 1.319.545 0 1.178-.252 1.465-.598l.088-.416c-.2.176-.492.246-.686.246-.275 0-.375-.193-.304-.533L8.93 6.588zM9 4.5a1 1 0 1 1-2 0 1 1 0 0 1 2 0z"
                  />
                  <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z" />
                </svg>
                완료된 훈련 기간입니다. 수정하려면 먼저 기간을 재개해야 합니다.
              </div>
            </div>
          </form>
        </div>

        <div class="modal-footer">
          <button @click="closePeriodModal" class="secondary-button">취소</button>
          <button @click="savePeriod" class="primary-button" :disabled="!isValidPeriodForm">
            {{ editingPeriod ? '수정' : '저장' }}
          </button>
        </div>
      </div>
    </div>

    <!-- ===== 업로드 모달 ===== -->
    <div v-if="showUploadModal" class="modal-overlay" @click="closeUploadModal">
      <div class="modal-content upload-modal" @click.stop>
        <div class="modal-header">
          <h3>훈련 결과 일괄 등록</h3>
          <button @click="closeUploadModal" class="close-button">
            <svg width="20" height="20" fill="currentColor" viewBox="0 0 16 16">
              <path
                d="M2.146 2.146a.5.5 0 0 1 .708 0L8 7.293l5.146-5.147a.5.5 0 0 1 .708.708L8.707 8l5.147 5.146a.5.5 0 0 1-.708.708L8 8.707l-5.146 5.147a.5.5 0 0 1-.708-.708L7.293 8 2.146 2.854a.5.5 0 0 1 0-.708z"
              />
            </svg>
          </button>
        </div>

        <div class="modal-body">
          <!-- 기간 선택 -->
          <div class="form-group">
            <label for="upload_period">훈련 기간 선택 *</label>
            <select id="upload_period" v-model="uploadForm.period_id" required class="form-input">
              <option value="">기간을 선택하세요</option>
              <option
                v-for="period in availablePeriods"
                :key="period.period_id"
                :value="period.period_id"
              >
                {{ period.training_year }}년 - {{ period.period_name }} ({{ period.training_type }})
              </option>
            </select>
          </div>

          <!-- 파일 업로드 -->
          <div class="form-group">
            <label for="excel_file">엑셀 파일 *</label>
            <div
              class="file-upload-area"
              :class="{ dragover: isDragover }"
              @drop="handleFileDrop"
              @dragover.prevent
              @dragenter.prevent
              @dragleave="isDragover = false"
            >
              <input
                type="file"
                id="excel_file"
                ref="fileInput"
                @change="handleFileSelect"
                accept=".xlsx,.xls"
                class="file-input"
              />
              <div class="file-upload-content">
                <svg width="48" height="48" fill="currentColor" viewBox="0 0 16 16">
                  <path
                    d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"
                  />
                  <path
                    d="M7.646 1.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1-.708.708L8.5 2.707V11.5a.5.5 0 0 1-1 0V2.707L5.354 4.854a.5.5 0 1 1-.708-.708l3-3z"
                  />
                </svg>
                <p v-if="!uploadForm.file">
                  <strong>클릭하여 파일 선택</strong> 또는 파일을 여기로 드래그하세요
                </p>
                <p v-else class="selected-file">선택된 파일: {{ uploadForm.file.name }}</p>
                <small>Excel 파일만 업로드 가능합니다 (.xlsx, .xls)</small>
              </div>
            </div>
          </div>

          <!-- 업로드 진행률 -->
          <div v-if="uploadProgress > 0" class="progress-section">
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
            </div>
            <p class="progress-text">업로드 중... {{ uploadProgress }}%</p>
          </div>

          <!-- 결과 미리보기 -->
          <div v-if="uploadPreview.length > 0" class="preview-section">
            <h4>업로드 결과 미리보기 ({{ uploadPreview.length }}건)</h4>
            <div class="preview-table">
              <table>
                <thead>
                  <tr>
                    <th>이메일</th>
                    <th>메일유형</th>
                    <th>로그유형</th>
                    <th>발송시각</th>
                    <th>수행시각</th>
                    <th>훈련결과</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(item, index) in uploadPreview.slice(0, 5)" :key="index">
                    <td>{{ item.target_email }}</td>
                    <td>{{ item.mail_type }}</td>
                    <td>{{ item.log_type }}</td>
                    <td>{{ formatDate(item.email_sent_time) }}</td>
                    <td>{{ formatDate(item.action_time) }}</td>
                    <td>
                      <span class="result-badge" :class="getResultClass(item.training_result)">
                        {{ getResultText(item.training_result) }}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
              <p v-if="uploadPreview.length > 5" class="preview-more">
                ... 외 {{ uploadPreview.length - 5 }}건
              </p>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button @click="closeUploadModal" class="secondary-button">취소</button>
          <button
            @click="processUpload"
            class="primary-button"
            :disabled="!uploadForm.period_id || !uploadForm.file || isUploading"
          >
            {{ isUploading ? '업로드 중...' : '업로드' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 훈련 기록 수정 모달 -->
    <div v-if="showEditModal" class="modal-overlay" @click="closeEditModal">
      <div class="modal-content large" @click.stop>
        <div class="modal-header">
          <h3>훈련 기록 수정</h3>
          <button @click="closeEditModal" class="close-button">
            <svg width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
              <path
                d="m8.93 6.588-2.29.287-.082.38.45.083c.294.07.352.176.288.469l-.738 3.468c-.194.897.105 1.319.808 1.319.545 0 1.178-.252 1.465-.598l.088-.416c-.2.176-.492.246-.686.246-.275 0-.375-.193-.304-.533L8.93 6.588zM9 4.5a1 1 0 1 1-2 0 1 1 0 0 1 2 0z"
              />
            </svg>
          </button>
        </div>

        <div class="modal-body">
          <form @submit.prevent="saveRecord" class="edit-form">
            <!-- 기본 정보 (읽기 전용) -->
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">사용자명</label>
                <input v-model="editingRecord.username" type="text" class="form-input" readonly />
              </div>
              <div class="form-group">
                <label class="form-label">부서</label>
                <input v-model="editingRecord.department" type="text" class="form-input" readonly />
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label class="form-label">이메일</label>
                <input
                  v-model="editingRecord.target_email"
                  type="email"
                  class="form-input"
                  readonly
                />
              </div>
              <div class="form-group">
                <label class="form-label">메일 유형</label>
                <input v-model="editingRecord.mail_type" type="text" class="form-input" readonly />
              </div>
            </div>

            <!-- 수정 가능한 필드들 -->
            <div class="form-group">
              <label class="form-label">훈련 결과 *</label>
              <select v-model="editingRecord.training_result" class="form-input" required>
                <option value="">선택하세요</option>
                <option value="success">성공</option>
                <option value="fail">실패</option>
                <option value="no_response">무응답</option>
              </select>
            </div>

            <div class="form-group">
              <label class="form-label">메모</label>
              <textarea
                v-model="editingRecord.notes"
                class="form-input"
                rows="3"
                placeholder="기록에 대한 추가 메모를 입력하세요"
              ></textarea>
            </div>

            <!-- 제외 설정 -->
            <div class="form-group">
              <div class="checkbox-wrapper">
                <label class="checkbox-label">
                  <input
                    type="checkbox"
                    v-model="editingRecord.exclude_from_scoring"
                    class="checkbox-input"
                  />
                  <span class="checkbox-custom">
                    <span class="checkbox-checkmark">
                      <svg width="12" height="12" fill="currentColor" viewBox="0 0 16 16">
                        <path
                          d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"
                        />
                      </svg>
                    </span>
                    <span class="checkbox-text">점수 계산에서 제외</span>
                  </span>
                </label>
              </div>
            </div>

            <div v-if="editingRecord.exclude_from_scoring" class="form-group">
              <label class="form-label">제외 사유</label>
              <input
                v-model="editingRecord.exclude_reason"
                type="text"
                class="form-input"
                placeholder="제외 사유를 입력하세요"
              />
            </div>
          </form>
        </div>

        <div class="modal-footer">
          <button @click="closeEditModal" class="secondary-button" :disabled="saving">취소</button>
          <button @click="saveRecord" class="primary-button" :disabled="saving">
            <span v-if="saving">저장 중...</span>
            <span v-else>저장</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 토스트 메시지 -->
    <div v-if="toast.show" class="toast" :class="toast.type">
      <div class="toast-content">
        <svg
          v-if="toast.type === 'success'"
          width="20"
          height="20"
          fill="currentColor"
          viewBox="0 0 16 16"
        >
          <path
            d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"
          />
        </svg>
        <svg
          v-else-if="toast.type === 'error'"
          width="20"
          height="20"
          fill="currentColor"
          viewBox="0 0 16 16"
        >
          <path
            d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM5.354 4.646a.5.5 0 1 0-.708.708L7.293 8l-2.647 2.646a.5.5 0 0 0 .708.708L8 8.707l2.646 2.647a.5.5 0 0 0 .708-.708L8.707 8l2.647-2.646a.5.5 0 0 0-.708-.708L8 7.293 5.354 4.646z"
          />
        </svg>
        <span>{{ toast.message }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { RouterLink } from 'vue-router'

// ===== 반응형 데이터 =====
const loading = ref(false)
const toast = ref({ show: false, message: '', type: 'success' })

// 기간 관리 관련
const periodStatus = ref({ training_types: {} })
const showPeriodModal = ref(false)
const editingPeriod = ref(null)
const periodForm = ref({
  training_year: new Date().getFullYear(),
  period_name: '',
  training_type: '이메일 피싱',
  start_date: '',
  end_date: '',
  description: '',
  auto_pass_setting: true,
})
const duplicateWarning = ref('')

// 업로드 관련
const showUploadModal = ref(false)
const uploadForm = ref({
  period_id: '',
  file: null,
})
const uploadProgress = ref(0)
const uploadPreview = ref([])
const isUploading = ref(false)
const isDragover = ref(false)
const fileInput = ref(null)

// 필터링 관련
const selectedYear = ref(new Date().getFullYear())
const selectedTrainingType = ref('')
const selectedResult = ref('')
const searchQuery = ref('')

// 기존 필터링 관련 뒤에 추가
// 훈련 기록 관련
const trainingRecords = ref([])
const filteredRecords = ref([])
const currentPage = ref(1)
const recordsPerPage = ref(20)

// ==== 1. 반응형 데이터에 추가 ====
const showEditModal = ref(false) // 수정 모달 표시 여부
const editingRecord = ref({}) // 수정 중인 기록
const saving = ref(false) // 저장 중 상태

// ===== Computed =====
const availableYears = computed(() => {
  const currentYear = new Date().getFullYear()
  return Array.from({ length: 5 }, (_, i) => currentYear - i)
})

// 페이지네이션 계산
const paginatedRecords = computed(() => {
  const start = (currentPage.value - 1) * recordsPerPage.value
  const end = start + recordsPerPage.value
  return filteredRecords.value.slice(start, end)
})

const totalPages = computed(() => {
  return Math.ceil(filteredRecords.value.length / recordsPerPage.value)
})

const availablePeriods = computed(() => {
  const periods = []
  Object.values(periodStatus.value.training_types || {}).forEach((typeData) => {
    periods.push(...typeData.periods)
  })
  return periods.filter((period) => !period.is_completed)
})

const isValidPeriodForm = computed(() => {
  return (
    periodForm.value.training_year &&
    periodForm.value.period_name.trim() &&
    periodForm.value.training_type &&
    periodForm.value.start_date &&
    periodForm.value.end_date
  )
})

const canEdit = computed(() => true) // 관리자는 항상 편집 가능

// ===== MOCK 데이터 생성 =====
// const createMockData = () => {
//   periodStatus.value = {
//     training_types: {
//       '이메일 피싱': {
//         periods: [
//           {
//             period_id: 1,
//             training_year: 2025,
//             period_name: '1차 피싱 훈련',
//             training_type: '이메일 피싱',
//             start_date: '2025-06-01',
//             end_date: '2025-06-30',
//             is_completed: false,
//             description: '2025년 1차 이메일 피싱 모의훈련',
//             auto_pass_setting: true,
//             status: 'active',
//             stats: {
//               total_targets: 150,
//               success_count: 120,
//               fail_count: 25,
//               no_response_count: 5,
//               success_rate: 80.0,
//               fail_rate: 16.7,
//             },
//           },
//           {
//             period_id: 2,
//             training_year: 2025,
//             period_name: '2차 피싱 훈련',
//             training_type: '이메일 피싱',
//             start_date: '2025-09-01',
//             end_date: '2025-09-30',
//             is_completed: true,
//             description: '2025년 2차 이메일 피싱 모의훈련',
//             auto_pass_setting: true,
//             status: 'completed',
//             stats: {
//               total_targets: 145,
//               success_count: 110,
//               fail_count: 30,
//               no_response_count: 5,
//               success_rate: 75.9,
//               fail_rate: 20.7,
//             },
//           },
//         ],
//       },
//       'SMS 피싱': {
//         periods: [
//           {
//             period_id: 3,
//             training_year: 2025,
//             period_name: '1차 SMS 훈련',
//             training_type: 'SMS 피싱',
//             start_date: '2025-03-01',
//             end_date: '2025-03-31',
//             is_completed: false,
//             description: '2025년 1차 SMS 피싱 모의훈련',
//             auto_pass_setting: true,
//             status: 'pending',
//             stats: {
//               total_targets: 0,
//               success_count: 0,
//               fail_count: 0,
//               no_response_count: 0,
//               success_rate: 0,
//               fail_rate: 0,
//             },
//           },
//         ],
//       },
//     },
//   }
//   trainingRecords.value = [
//     {
//       training_id: 1,
//       user_id: 1,
//       username: '홍길동',
//       department: 'IT팀',
//       period_id: 1,
//       period_name: '1차 피싱 훈련',
//       training_type: '이메일 피싱',
//       target_email: 'hong@test.com',
//       mail_type: '퇴직연금 운용',
//       log_type: '이메일 열람',
//       email_sent_time: '2025-06-02 09:30:00',
//       action_time: '2025-06-02 14:20:00',
//       training_result: 'success',
//       response_time_minutes: 290,
//       exclude_from_scoring: false,
//       notes: null,
//     },
//     {
//       training_id: 1,
//       user_id: 1,
//       username: '홍길동',
//       department: 'IT팀',
//       period_id: 1,
//       period_name: '1차 피싱 훈련',
//       training_type: '이메일 피싱',
//       target_email: 'hong@test.com',
//       mail_type: '퇴직연금 운용',
//       log_type: '이메일 열람',
//       email_sent_time: '2025-06-02 09:30:00',
//       action_time: '2025-06-02 14:20:00',
//       training_result: 'success',
//       response_time_minutes: 290,
//       exclude_from_scoring: false,
//       notes: null,
//     },
//     // ... 더 많은 기록들 (총 8개)
//   ]
//   filteredRecords.value = [...trainingRecords.value]
// }

// ===== 라이프사이클 =====
onMounted(() => {
  loadPeriodStatus()
  loadTrainingData()
})

// ===== 메서드 =====

/**
 * 토스트 메시지 표시
 */
const displayToast = (message, type = 'success') => {
  toast.value = { show: true, message, type }
  setTimeout(() => {
    toast.value.show = false
  }, 3000)
}

/**
 * 기간 현황 로드 (실제 API 호출)
 */
const loadPeriodStatus = async () => {
  try {
    loading.value = true
    const response = await fetch(
      `/api/phishing-training/periods/status?year=${selectedYear.value}`,
      {
        credentials: 'include',
      },
    )

    if (!response.ok) {
      throw new Error('기간 현황 조회 실패')
    }

    const result = await response.json()
    periodStatus.value = result

    console.log('기간 현황 로드됨:', result)
  } catch (error) {
    console.error('기간 현황 로드 실패:', error)
    displayToast('기간 현황을 불러오는데 실패했습니다.', 'error')
  } finally {
    loading.value = false
  }
}
/**
 * 훈련 데이터 로드 (모든 데이터를 가져와서 클라이언트에서 페이지네이션)
 */
const loadTrainingData = async () => {
  try {
    loading.value = true

    // 모든 데이터를 가져오기 위해 per_page를 크게 설정
    const params = new URLSearchParams({
      year: selectedYear.value,
      per_page: 10000, // 충분히 큰 값으로 설정하여 모든 데이터 가져오기
      page: 1,
    })

    // 서버 사이드 필터는 기본적인 것만 적용 (년도는 데이터량 때문에 서버에서 처리)
    // 나머지는 클라이언트에서 처리

    const response = await fetch(`/api/phishing-training/records?${params}`, {
      credentials: 'include',
    })

    if (!response.ok) {
      throw new Error('훈련 데이터 조회 실패')
    }

    const result = await response.json()

    // 모든 데이터를 trainingRecords에 저장
    trainingRecords.value = result.records || []

    // 초기 필터 적용
    applyFilters()

    console.log(`훈련 데이터 로드됨: 총 ${trainingRecords.value.length}건`)
  } catch (error) {
    console.error('훈련 데이터 로드 실패:', error)
    displayToast('훈련 데이터를 불러오는데 실패했습니다.', 'error')
    trainingRecords.value = []
    filteredRecords.value = []
  } finally {
    loading.value = false
  }
}

/**
 * 검색 실행
 */
// 기존 searchTrainingData 함수를 다음으로 교체
const searchTrainingData = () => {
  applyFilters()
}

// applyFilters 함수 추가
const applyFilters = () => {
  let filtered = [...trainingRecords.value]

  // 연도 필터
  if (selectedYear.value) {
    filtered = filtered.filter((record) => {
      const year = new Date(record.email_sent_time).getFullYear()
      return year === selectedYear.value
    })
  }

  // 훈련 유형 필터
  if (selectedTrainingType.value) {
    filtered = filtered.filter((record) => record.training_type === selectedTrainingType.value)
  }

  // 결과 필터
  if (selectedResult.value) {
    filtered = filtered.filter((record) => record.training_result === selectedResult.value)
  }

  // 검색어 필터
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase().trim()
    filtered = filtered.filter(
      (record) =>
        record.username?.toLowerCase().includes(query) ||
        record.department?.toLowerCase().includes(query) ||
        record.target_email?.toLowerCase().includes(query) ||
        record.mail_type?.toLowerCase().includes(query),
    )
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
    training_year: selectedYear.value,
    period_name: '',
    training_type: '이메일 피싱',
    start_date: '',
    end_date: '',
    description: '',
    auto_pass_setting: true,
  }
  duplicateWarning.value = ''
  showPeriodModal.value = true
}

/**
 * 기간 편집 모달 열기
 */
const editPeriod = (period) => {
  editingPeriod.value = period
  periodForm.value = {
    training_year: period.training_year,
    period_name: period.period_name,
    training_type: period.training_type,
    start_date: period.start_date,
    end_date: period.end_date,
    description: period.description || '',
    auto_pass_setting: period.auto_pass_setting === 1 || period.auto_pass_setting === true,
  }
  duplicateWarning.value = ''
  showPeriodModal.value = true
}

/**
 * 기간 모달 닫기
 */
const closePeriodModal = () => {
  showPeriodModal.value = false
  editingPeriod.value = null
  duplicateWarning.value = ''
}

/**
 * 기간 저장 (실제 API 호출)
 */
const savePeriod = async () => {
  if (!isValidPeriodForm.value) {
    displayToast('필수 필드를 모두 입력해주세요.', 'error')
    return
  }

  if (new Date(periodForm.value.start_date) >= new Date(periodForm.value.end_date)) {
    displayToast('종료일은 시작일보다 늦어야 합니다.', 'error')
    return
  }

  try {
    const method = editingPeriod.value ? 'PUT' : 'POST'
    const url = editingPeriod.value
      ? `/api/phishing-training/periods/${editingPeriod.value.period_id}`
      : '/api/phishing-training/periods'

    const response = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(periodForm.value),
    })

    const result = await response.json()

    if (!response.ok) {
      // 완료된 기간 수정 시 특별 처리
      if (result.message && result.message.includes('완료된 훈련 기간은 수정할 수 없습니다')) {
        const confirmReopen = confirm(
          `이 기간은 완료 상태입니다.\n\n완료 상태를 해제하고 수정하시겠습니까?\n\n` +
            `※ 완료 상태 해제 시 자동 통과 처리된 데이터가 변경될 수 있습니다.`,
        )

        if (confirmReopen) {
          await reopenAndEdit()
          return
        } else {
          displayToast('수정이 취소되었습니다.', 'info')
          return
        }
      }

      throw new Error(result.error || '저장 실패')
    }

    displayToast(result.message || '저장되었습니다.', 'success')
    closePeriodModal()
    await loadPeriodStatus()
  } catch (error) {
    console.error('기간 저장 실패:', error)
    displayToast(error.message, 'error')
  }
}

/**
 * 재개 후 수정 처리
 */
const reopenAndEdit = async () => {
  try {
    displayToast('기간을 재개하고 수정을 진행합니다.', 'success')

    // 1. 기간 재개
    const reopenResponse = await fetch(
      `/api/phishing-training/periods/${editingPeriod.value.period_id}/reopen`,
      {
        method: 'POST',
        credentials: 'include',
      },
    )

    const reopenResult = await reopenResponse.json()

    if (!reopenResponse.ok) {
      throw new Error(reopenResult.error || '재개 실패')
    }

    // 2. 수정 재시도
    const updateResponse = await fetch(
      `/api/phishing-training/periods/${editingPeriod.value.period_id}`,
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
    await loadTrainingData()
  } catch (err) {
    console.error('재개 후 수정 오류:', err)
    displayToast(err.message, 'error')
  }
}

/**
 * 기간 완료 처리 (실제 API 호출)
 */
const completePeriod = async (period) => {
  if (!confirm(`${period.period_name} 기간을 완료 처리하시겠습니까?`)) return

  try {
    const response = await fetch(`/api/phishing-training/periods/${period.period_id}/complete`, {
      method: 'POST',
      credentials: 'include',
    })

    const result = await response.json()

    if (!response.ok) {
      throw new Error(result.error || '완료 처리 실패')
    }

    displayToast(result.message, 'success')
    await loadPeriodStatus()
    await loadTrainingData()
  } catch (err) {
    console.error('완료 처리 오류:', err)
    displayToast(err.message, 'error')
  }
}

/**
 * 기간 재개 처리 (실제 API 호출)
 */
const reopenPeriod = async (period) => {
  if (!confirm(`${period.period_name} 기간을 재개하시겠습니까?`)) return

  try {
    const response = await fetch(`/api/phishing-training/periods/${period.period_id}/reopen`, {
      method: 'POST',
      credentials: 'include',
    })

    const result = await response.json()

    if (!response.ok) {
      throw new Error(result.error || '재개 처리 실패')
    }

    displayToast(result.message, 'success')
    await loadPeriodStatus()
    await loadTrainingData()
  } catch (err) {
    console.error('재개 처리 오류:', err)
    displayToast(err.message, 'error')
  }
}

/**
 * 기간 삭제 (실제 API 호출)
 */
const deletePeriod = async (period) => {
  if (!confirm(`${period.period_name} 기간을 삭제하시겠습니까?`)) return

  try {
    console.log('[DEBUG] 훈련 기간 삭제 요청:', period.period_id)

    const response = await fetch(`/api/phishing-training/periods/${period.period_id}`, {
      method: 'DELETE',
      credentials: 'include',
    })

    const result = await response.json()
    console.log('[DEBUG] 삭제 응답:', response.status, result)

    // 성공한 경우
    if (response.ok) {
      displayToast(result.message, 'success')
      await loadPeriodStatus()
      await loadTrainingData()
      return
    }

    // 400 오류이고 확인이 필요한 경우
    if (response.status === 400 && result.requires_confirmation) {
      console.log('[DEBUG] 확인 필요:', result.training_count, '건의 훈련 기록')

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

    throw new Error(result.error || '삭제 실패')
  } catch (err) {
    console.error('기간 삭제 오류:', err)
    displayToast(err.message, 'error')
  }
}

/**
 * 기간 강제 삭제 (실제 API 호출)
 */
const forceDeletePeriod = async (periodId) => {
  try {
    const response = await fetch(`/api/phishing-training/periods/${periodId}/force-delete`, {
      method: 'DELETE',
      credentials: 'include',
    })

    const result = await response.json()

    if (!response.ok) {
      throw new Error(result.error || '강제 삭제 실패')
    }

    displayToast(result.message, 'success')
    await loadPeriodStatus()
    await loadTrainingData()
  } catch (err) {
    console.error('강제 삭제 오류:', err)
    displayToast(err.message, 'error')
  }
}

/**
 * 상세 통계 보기
 */
const viewStats = (period) => {
  console.log('상세 통계 보기:', period)
  // 다음 단계에서 구현
}

// ===== 업로드 관련 메서드 =====

/**
 * 업로드 모달 열기
 */
const openUploadModal = () => {
  uploadForm.value = {
    period_id: '',
    file: null,
  }
  uploadProgress.value = 0
  uploadPreview.value = []
  isUploading.value = false
  showUploadModal.value = true
}

/**
 * 업로드 모달 닫기
 */
const closeUploadModal = () => {
  showUploadModal.value = false
  uploadForm.value = { period_id: '', file: null }
  uploadProgress.value = 0
  uploadPreview.value = []
  isUploading.value = false
}

/**
 * 파일 선택 처리
 */
const handleFileSelect = (event) => {
  const file = event.target.files[0]
  if (file) {
    uploadForm.value.file = file
    parseExcelFile(file)
  }
}

/**
 * 드래그 앤 드롭 처리
 */
const handleFileDrop = (event) => {
  event.preventDefault()
  isDragover.value = false

  const files = event.dataTransfer.files
  if (files.length > 0) {
    uploadForm.value.file = files[0]
    parseExcelFile(files[0])
  }
}

/**
 * 엑셀 파일 파싱
 */
// const parseExcelFile = async (file) => {
//   try {
//     // MOCK 데이터 생성
//     uploadPreview.value = [
//       {
//         target_email: 'penguin@test.com',
//         mail_type: '퇴직연금 운용',
//         log_type: '스크립트 첨부파일 열람',
//         email_sent_time: '2025-06-02T23:59:17.999Z',
//         action_time: '2025-06-03T01:32:30.000Z',
//         training_result: 'fail',
//       },
//       {
//         target_email: 'eunjekim8@test.com',
//         mail_type: '세금계산서',
//         log_type: '스크립트 첨부파일 열람',
//         email_sent_time: '2025-06-02T23:59:17.999Z',
//         action_time: '2025-06-03T01:32:30.000Z',
//         training_result: 'fail',
//       },
//       {
//         target_email: 'admin@test.com',
//         mail_type: '카카오톡',
//         log_type: '이메일 열람2',
//         email_sent_time: '2025-06-02T23:59:17.999Z',
//         action_time: '2025-06-03T01:32:30.000Z',
//         training_result: 'success',
//       },
//     ]
//   } catch (error) {
//     console.error('파일 파싱 실패:', error)
//     displayToast('파일을 읽는데 실패했습니다.', 'error')
//   }
// }

/**
 * 엑셀 파일 파싱 - 실제 구현
 */
const parseExcelFile = async (file) => {
  try {
    // 파일 유효성 검증
    if (!file) {
      throw new Error('파일이 선택되지 않았습니다.')
    }

    const fileName = file.name.toLowerCase()
    if (!fileName.endsWith('.xlsx') && !fileName.endsWith('.xls')) {
      throw new Error('엑셀 파일(.xlsx, .xls)만 업로드 가능합니다.')
    }

    // 파일 크기 제한 (10MB)
    const maxSize = 10 * 1024 * 1024
    if (file.size > maxSize) {
      throw new Error('파일 크기는 10MB 이하여야 합니다.')
    }

    // SheetJS 사용 (Vue 프로젝트에 이미 설치되어 있음)
    const XLSX = await import('xlsx')

    // 파일을 ArrayBuffer로 읽기
    const arrayBuffer = await file.arrayBuffer()

    // 워크북 읽기
    const workbook = XLSX.read(arrayBuffer, {
      type: 'array',
      cellDates: true,
      dateNF: 'yyyy-mm-dd hh:mm:ss',
    })

    // 첫 번째 시트 선택
    const sheetName = workbook.SheetNames[0]
    if (!sheetName) {
      throw new Error('엑셀 파일에 시트가 없습니다.')
    }

    const worksheet = workbook.Sheets[sheetName]

    // JSON 형태로 변환
    const rawData = XLSX.utils.sheet_to_json(worksheet, {
      raw: false,
      dateNF: 'yyyy-mm-dd"T"hh:mm:ss.000"Z"',
      defval: '', // 빈 셀은 빈 문자열로 처리
    })

    if (rawData.length === 0) {
      throw new Error('엑셀 파일에 데이터가 없습니다.')
    }

    // 컬럼 매핑 정의
    const columnMapping = {
      email_sent_time: ['메일발송시각', '발송시각', '메일발송일시', '발송일시'],
      action_time: ['수행시각', '액션시각', '클릭시각', '응답시각'],
      log_type: ['로그유형', '액션유형', '행동유형', '로그타입'],
      mail_type: ['메일유형', '메일타입', '훈련유형', '메일종류'],
      target_email: ['이메일', '대상이메일', '사용자이메일', '수신자'],
    }

    // 실제 컬럼명 찾기
    const actualColumns = Object.keys(rawData[0])
    const mappedColumns = findColumnMapping(actualColumns, columnMapping)

    // 필수 컬럼 체크
    const requiredFields = ['target_email', 'log_type']
    const missingFields = requiredFields.filter((field) => !mappedColumns[field])

    if (missingFields.length > 0) {
      throw new Error(`필수 컬럼이 누락되었습니다: ${missingFields.join(', ')}`)
    }

    // 데이터 처리 및 검증
    const processedData = []
    const validationErrors = []

    for (let i = 0; i < rawData.length; i++) {
      const row = rawData[i]
      const rowNum = i + 2 // 엑셀 행 번호 (헤더 + 1)

      try {
        // 빈 행 스킵
        if (isEmptyRow(row, mappedColumns)) {
          continue
        }

        // 각 필드 추출 및 검증
        const processedRow = {
          target_email: extractAndValidateEmail(row[mappedColumns.target_email], rowNum),
          mail_type: extractString(row[mappedColumns.mail_type]) || '기타',
          log_type: extractString(row[mappedColumns.log_type]),
          email_sent_time: extractDateTime(row[mappedColumns.email_sent_time]),
          action_time: extractDateTime(row[mappedColumns.action_time]),
          training_result: determineTrainingResult(extractString(row[mappedColumns.log_type])),
          row_number: rowNum,
        }

        // 추가 검증
        if (!processedRow.log_type) {
          validationErrors.push(`${rowNum}행: 로그유형이 비어있습니다.`)
          continue
        }

        processedData.push(processedRow)
      } catch (error) {
        validationErrors.push(`${rowNum}행: ${error.message}`)
      }
    }

    // 처리 결과 검증
    if (processedData.length === 0) {
      throw new Error('처리 가능한 유효한 데이터가 없습니다.')
    }

    // 중복 데이터 체크
    const duplicates = findDuplicateRecords(processedData)
    if (duplicates.length > 0) {
      validationErrors.push(`중복된 기록이 있습니다: ${duplicates.join(', ')}행`)
    }

    // 미리보기 데이터 설정
    uploadPreview.value = processedData

    // 검증 경고가 있으면 표시
    if (validationErrors.length > 0) {
      displayToast(`파일 파싱 완료, 경고 ${validationErrors.length}개`, 'warning')
      console.warn('데이터 검증 경고:', validationErrors)
    } else {
      displayToast(`${processedData.length}건의 데이터를 성공적으로 로드했습니다.`, 'success')
    }

    return {
      success: true,
      data: processedData,
      warnings: validationErrors,
      summary: {
        total_rows: rawData.length,
        processed_rows: processedData.length,
        warning_count: validationErrors.length,
      },
    }
  } catch (error) {
    console.error('파일 파싱 실패:', error)
    uploadPreview.value = []
    displayToast(`파일 파싱 실패: ${error.message}`, 'error')

    return {
      success: false,
      error: error.message,
    }
  }
}

// ===== 헬퍼 함수들 (Vue 컴포넌트 내부에 추가) =====

/**
 * 컬럼 매핑 찾기
 */
const findColumnMapping = (actualColumns, columnMapping) => {
  const result = {}

  for (const [key, candidates] of Object.entries(columnMapping)) {
    result[key] = null

    // 정확한 매칭 우선
    for (const candidate of candidates) {
      const found = actualColumns.find((col) => col === candidate)
      if (found) {
        result[key] = found
        break
      }
    }

    // 부분 매칭 시도
    if (!result[key]) {
      for (const candidate of candidates) {
        const found = actualColumns.find(
          (col) => col.includes(candidate) || candidate.includes(col),
        )
        if (found) {
          result[key] = found
          break
        }
      }
    }
  }

  return result
}

/**
 * 빈 행 체크
 */
const isEmptyRow = (row, mappedColumns) => {
  const importantFields = ['target_email', 'log_type']
  return importantFields.every((field) => {
    const columnName = mappedColumns[field]
    return !columnName || !row[columnName] || String(row[columnName]).trim() === ''
  })
}

/**
 * 이메일 추출 및 검증
 */
const extractAndValidateEmail = (value, rowNum) => {
  const email = extractString(value)
  if (!email) {
    throw new Error('이메일이 비어있습니다.')
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(email)) {
    throw new Error(`유효하지 않은 이메일 형식: ${email}`)
  }

  return email.toLowerCase()
}

/**
 * 문자열 추출
 */
const extractString = (value) => {
  if (value === null || value === undefined) return ''
  return String(value).trim()
}

/**
 * 날짜시간 추출
 */
const extractDateTime = (value) => {
  if (!value) return null

  try {
    // 이미 Date 객체인 경우
    if (value instanceof Date) {
      return value.toISOString()
    }

    // 문자열인 경우 파싱 시도
    const dateValue = new Date(value)
    if (isNaN(dateValue.getTime())) {
      return null
    }

    return dateValue.toISOString()
  } catch {
    return null
  }
}

/**
 * 훈련 결과 판정
 */
const determineTrainingResult = (logType) => {
  if (!logType) return 'unknown'

  const logTypeLower = logType.toLowerCase()

  // 실패 케이스 (피싱에 걸린 경우)
  const failPatterns = [
    '첨부파일 열람',
    '첨부파일 실행',
    '링크 클릭',
    '스크립트 실행',
    '매크로 실행',
    '다운로드',
    'attachment',
    'click',
    'download',
    'execute',
  ]

  if (failPatterns.some((pattern) => logTypeLower.includes(pattern))) {
    return 'fail'
  }

  // 성공 케이스 (단순 열람만)
  const successPatterns = ['이메일 열람', '메일 읽기', '열람만', 'view', 'read']

  if (successPatterns.some((pattern) => logTypeLower.includes(pattern))) {
    return 'success'
  }

  // 기본적으로는 실패로 간주 (보수적 접근)
  return 'fail'
}

/**
 * 중복 기록 찾기
 */
const findDuplicateRecords = (data) => {
  const seen = new Set()
  const duplicates = []

  data.forEach((record, index) => {
    const key = `${record.target_email}_${record.email_sent_time}_${record.log_type}`
    if (seen.has(key)) {
      duplicates.push(record.row_number)
    } else {
      seen.add(key)
    }
  })

  return duplicates
}

/**
 * 업로드 처리 (실제 API 호출)
 */
const processUpload = async () => {
  if (!uploadForm.value.period_id || !uploadForm.value.file) {
    displayToast('기간과 파일을 모두 선택해주세요.', 'error')
    return
  }

  try {
    isUploading.value = true

    const formData = new FormData()
    formData.append('file', uploadForm.value.file)
    formData.append('period_id', uploadForm.value.period_id)

    const response = await fetch('/api/phishing-training/bulk-upload', {
      method: 'POST',
      credentials: 'include',
      body: formData,
    })

    const result = await response.json()

    if (!response.ok) {
      throw new Error(result.error || '업로드 실패')
    }

    displayToast(result.message, 'success')
    closeUploadModal()
    await loadPeriodStatus()
    await loadTrainingData()
  } catch (error) {
    console.error('업로드 실패:', error)
    displayToast(error.message, 'error')
  } finally {
    isUploading.value = false
    uploadProgress.value = 0
  }
}

// ===== 유틸리티 메서드 =====

/**
 * 카드 헤더 상태 클래스
 */
const getCardHeaderStatusClass = (period) => {
  if (period.is_completed) return 'completed'
  return period.status || 'pending'
}

/**
 * 카드 헤더 상태 텍스트
 */
const getCardHeaderStatusText = (period) => {
  if (period.is_completed) return '완료'
  switch (period.status) {
    case 'active':
      return '진행중'
    case 'pending':
      return '대기'
    default:
      return '대기'
  }
}

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
 * 날짜 범위 포맷팅
 */
const formatDateRange = (startDate, endDate) => {
  const start = new Date(startDate).toLocaleDateString('ko-KR')
  const end = new Date(endDate).toLocaleDateString('ko-KR')
  return `${start} ~ ${end}`
}

/**
 * 수료율별 CSS 클래스
 */
const getRateClass = (rate) => {
  if (rate >= 80) return 'rate-excellent'
  if (rate >= 60) return 'rate-good'
  if (rate >= 40) return 'rate-warning'
  return 'rate-poor'
}

/**
 * 결과별 CSS 클래스
 */
const getResultClass = (result) => {
  switch (result) {
    case 'success':
      return 'result-success'
    case 'fail':
      return 'result-fail'
    case 'no_response':
      return 'result-no-response'
    default:
      return 'result-unknown'
  }
}

/**
 * 결과 텍스트
 */
const getResultText = (result) => {
  switch (result) {
    case 'success':
      return '성공'
    case 'fail':
      return '실패'
    case 'no_response':
      return '무응답'
    default:
      return '알 수 없음'
  }
}

// getResultText 함수 뒤에 추가
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

const formatResponseTime = (minutes) => {
  if (!minutes || minutes === 0) return '즉시'

  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60

  if (hours > 0) {
    return `${hours}시간 ${mins}분`
  }
  return `${mins}분`
}

/**
 * 훈련 기록 수정 모달 열기
 */
const editRecord = (record) => {
  editingRecord.value = {
    training_id: record.training_id,
    user_id: record.user_id,
    username: record.username,
    department: record.department,
    target_email: record.target_email,
    mail_type: record.mail_type,
    log_type: record.log_type,
    training_result: record.training_result,
    notes: record.notes || '',
    exclude_from_scoring: record.exclude_from_scoring,
    exclude_reason: record.exclude_reason || '',
    // 읽기 전용으로 표시할 추가 정보
    email_sent_time: record.email_sent_time,
    action_time: record.action_time,
    response_time_minutes: record.response_time_minutes,
  }
  showEditModal.value = true
}

/**
 * 훈련 기록 저장 (실제 API 호출)
 */
const saveRecord = async () => {
  if (saving.value) return

  // 필수 필드 검증
  if (!editingRecord.value.training_result) {
    displayToast('훈련 결과를 선택해주세요.', 'error')
    return
  }

  // 제외 사유 검증
  if (editingRecord.value.exclude_from_scoring && !editingRecord.value.exclude_reason) {
    displayToast('제외 사유를 입력해주세요.', 'error')
    return
  }

  saving.value = true

  try {
    const response = await fetch(
      `/api/phishing-training/records/${editingRecord.value.training_id}`,
      {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          training_result: editingRecord.value.training_result,
          notes: editingRecord.value.notes,
          exclude_from_scoring: editingRecord.value.exclude_from_scoring,
          exclude_reason: editingRecord.value.exclude_from_scoring
            ? editingRecord.value.exclude_reason
            : null,
        }),
      },
    )

    const result = await response.json()

    if (!response.ok) {
      throw new Error(result.error || '수정 실패')
    }

    // 로컬 상태 업데이트
    const index = trainingRecords.value.findIndex(
      (r) => r.training_id === editingRecord.value.training_id,
    )
    if (index !== -1) {
      trainingRecords.value[index] = {
        ...trainingRecords.value[index],
        training_result: editingRecord.value.training_result,
        notes: editingRecord.value.notes,
        exclude_from_scoring: editingRecord.value.exclude_from_scoring,
        exclude_reason: editingRecord.value.exclude_reason,
      }
      applyFilters() // 필터 재적용
    }

    displayToast(result.message || '훈련 기록이 수정되었습니다.', 'success')
    closeEditModal()
  } catch (error) {
    console.error('기록 수정 실패:', error)
    displayToast(error.message, 'error')
  } finally {
    saving.value = false
  }
}

/**
 * 수정 모달 닫기
 */
const closeEditModal = () => {
  showEditModal.value = false
  editingRecord.value = {}
  saving.value = false
}

/**
 * 제외/포함 토글 (실제 API 호출)
 */
const toggleExclude = async (record) => {
  const action = record.exclude_from_scoring ? '포함' : '제외'
  if (!confirm(`${record.username}의 훈련 기록을 점수 계산에서 ${action}하시겠습니까?`)) return

  try {
    const response = await fetch(`/api/phishing-training/records/${record.training_id}/exclude`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        exclude: !record.exclude_from_scoring,
        reason: !record.exclude_from_scoring ? '관리자가 제외 처리' : '',
      }),
    })

    const result = await response.json()

    if (!response.ok) {
      throw new Error(result.error || '처리 실패')
    }

    // 로컬 상태 업데이트
    record.exclude_from_scoring = !record.exclude_from_scoring
    displayToast(result.message, 'success')
  } catch (error) {
    console.error('제외/포함 처리 실패:', error)
    displayToast(error.message, 'error')
  }
}

/**
 * 기록 삭제 (실제 API 호출)
 */
const deleteRecord = async (record) => {
  if (
    !confirm(
      `${record.username}의 훈련 기록을 삭제하시겠습니까?\n\n※ 이 작업은 되돌릴 수 없습니다.`,
    )
  )
    return

  try {
    const response = await fetch(`/api/phishing-training/records/${record.training_id}`, {
      method: 'DELETE',
      credentials: 'include',
    })

    const result = await response.json()

    if (!response.ok) {
      throw new Error(result.error || '삭제 실패')
    }

    // 로컬 상태에서 제거
    const index = trainingRecords.value.findIndex((r) => r.training_id === record.training_id)
    if (index !== -1) {
      trainingRecords.value.splice(index, 1)
      applyFilters() // 필터 재적용
    }

    displayToast(result.message, 'success')
  } catch (error) {
    console.error('기록 삭제 실패:', error)
    displayToast(error.message, 'error')
  }
}

// ===== Watchers =====
// 기존 watch를 다음으로 교체
watch(selectedYear, () => {
  loadPeriodStatus()
  loadTrainingData()
  applyFilters()
})

watch(selectedTrainingType, applyFilters)
watch(selectedResult, applyFilters)
</script>

<style scoped>
@import '../styles/AdminPhishingTrainingManagement.css';
</style>
