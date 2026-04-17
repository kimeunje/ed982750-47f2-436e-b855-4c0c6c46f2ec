<template>
  <div class="admin-education-management">
    <!-- ===== 페이지 헤더 (사용자 관리와 동일) ===== -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">정보보호 교육 관리</h1>
        <p class="page-subtitle">교육 기간 설정 및 교육 기록 관리</p>
      </div>
      <div class="header-right">
        <select v-model="selectedYear" class="header-year-select">
          <option v-for="year in availableYears" :key="year" :value="year">{{ year }}년</option>
        </select>
      </div>
    </div>

    <!-- ===== 교육 기간 관리 섹션 ===== -->
    <div class="period-management-section">
      <div class="section-header">
        <h3>
          <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M3.5 0a.5.5 0 0 1 .5.5V1h8V.5a.5.5 0 0 1 1 0V1h1a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V3a2 2 0 0 1 2-2h1V.5a.5.5 0 0 1 .5-.5zM1 4v10a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V4H1z"/></svg>
          교육 기간 관리
        </h3>
        <button @click="openPeriodModal" class="btn-action btn-add">
          <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16"><path d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4z"/></svg>
          기간 추가
        </button>
      </div>

      <!-- 교육 기간 테이블형 리스트 -->
      <div
        class="period-list"
        v-if="periodStatus.education_types && Object.keys(periodStatus.education_types).length > 0"
      >
        <div
          v-for="(typeData, educationType) in periodStatus.education_types"
          :key="educationType"
          class="education-type-group"
        >
          <div class="type-group-header">
            <span class="type-group-label">{{ educationType }} 교육</span>
            <span class="type-group-count">{{ typeData.periods?.length || 0 }}개 기간</span>
          </div>

          <div class="period-table-container">
            <table class="period-table">
              <thead>
                <tr>
                  <th class="pt-col-name">기간명</th>
                  <th class="pt-col-date">기간</th>
                  <th class="pt-col-status">상태</th>
                  <th class="pt-col-stats">대상자</th>
                  <th class="pt-col-stats">수료</th>
                  <th class="pt-col-stats">미수료</th>
                  <th class="pt-col-rate">수료율</th>
                  <th class="pt-col-actions">관리</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="period in typeData.periods"
                  :key="period.period_id"
                  class="period-row"
                  :class="{ 'row-completed': period.is_completed }"
                >
                  <td class="pt-col-name">
                    <div class="period-name-cell">
                      <span class="period-name">{{ period.period_name }}</span>
                      <span class="period-desc" v-if="period.description">{{ period.description }}</span>
                    </div>
                  </td>
                  <td class="pt-col-date">
                    <span class="date-range">{{ formatDate(period.start_date) }} ~ {{ formatDate(period.end_date) }}</span>
                  </td>
                  <td class="pt-col-status">
                    <span class="card-status-badge" :class="getCardHeaderStatusClass(period)">
                      {{ getCardHeaderStatusText(period) }}
                    </span>
                  </td>
                  <td class="pt-col-stats">
                    <span class="stat-cell">{{ period.statistics?.total_participants || 0 }}</span>
                  </td>
                  <td class="pt-col-stats">
                    <span class="stat-cell success">{{ period.statistics?.success_count || period.statistics?.success_user_count || 0 }}</span>
                  </td>
                  <td class="pt-col-stats">
                    <span class="stat-cell failure">{{ period.statistics?.failure_count || period.statistics?.failure_user_count || 0 }}</span>
                  </td>
                  <td class="pt-col-rate">
                    <div class="rate-inline" v-if="period.statistics">
                      <div class="rate-bar-mini">
                        <div
                          class="rate-fill-mini"
                          :class="period.statistics.success_rate >= 100 ? 'fill-pass' : 'fill-fail'"
                          :style="{ width: Math.min(period.statistics.success_rate || 0, 100) + '%' }"
                        ></div>
                      </div>
                      <span class="rate-pct" :class="period.statistics.success_rate >= 100 ? 'pct-pass' : 'pct-fail'">
                        {{ formatSuccessRate(period.statistics.success_rate) }}
                      </span>
                    </div>
                    <span v-else class="stat-cell muted">-</span>
                  </td>
                  <td class="pt-col-actions">
                    <div class="action-buttons">
                      <button class="action-btn" @click="editPeriod(period)" title="수정">
                        <svg width="15" height="15" viewBox="0 0 16 16" fill="currentColor"><path d="M15.502 1.94a.5.5 0 0 1 0 .706L14.459 3.69l-2-2L13.502.646a.5.5 0 0 1 .707 0l1.293 1.293zm-1.75 2.456-2-2L4.939 9.21a.5.5 0 0 0-.121.196l-.805 2.414a.25.25 0 0 0 .316.316l2.414-.805a.5.5 0 0 0 .196-.12l6.813-6.814z"/><path fill-rule="evenodd" d="M1 13.5A1.5 1.5 0 0 0 2.5 15h11a1.5 1.5 0 0 0 1.5-1.5v-6a.5.5 0 0 0-1 0v6a.5.5 0 0 1-.5.5h-11a.5.5 0 0 1-.5-.5v-11a.5.5 0 0 1 .5-.5H9a.5.5 0 0 0 0-1H2.5A1.5 1.5 0 0 0 1 2.5v11z"/></svg>
                      </button>
                      <!-- 완료/재개 토글 버튼 -->
                      <button
                        v-if="!period.is_completed"
                        class="action-btn complete"
                        @click="completePeriod(period)"
                        title="완료 처리"
                      >
                        <svg width="15" height="15" viewBox="0 0 16 16" fill="currentColor"><path d="M10.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425a.267.267 0 0 1 .02-.022z"/></svg>
                      </button>
                      <button
                        v-else
                        class="action-btn reopen"
                        @click="reopenPeriod(period)"
                        title="재개"
                      >
                        <svg width="15" height="15" viewBox="0 0 16 16" fill="currentColor"><path fill-rule="evenodd" d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2v1z"/><path d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466z"/></svg>
                      </button>
                      <button class="action-btn danger" @click="deletePeriod(period)" title="삭제">
                        <svg width="15" height="15" viewBox="0 0 16 16" fill="currentColor"><path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/><path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/></svg>
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div v-else class="no-periods">
        교육 기간이 등록되지 않았습니다. '기간 추가' 버튼으로 교육 기간을 설정해주세요.
      </div>
    </div>

    <!-- ===== 교육 기록 관리 (헤더 + 툴바 + 테이블 통합) ===== -->
    <div class="table-section">
      <!-- 섹션 헤더 -->
      <div class="table-section-header">
        <h3>교육 기록 ({{ filteredRecords.length }}건)</h3>
      </div>

      <!-- 툴바: 연도 + 교육유형 + 검색 + 액션 -->
      <div class="table-toolbar">
        <div class="toolbar-left">
          <div class="search-wrapper">
            <span class="search-icon">
              <svg width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
            </span>
            <input
              type="text"
              v-model="searchQuery"
              @input="searchEducationData"
              placeholder="사용자명 또는 부서 검색..."
              class="search-input"
            />
            <button v-if="searchQuery" class="search-clear" @click="searchQuery = ''; searchEducationData()">
              <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16"><path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/></svg>
            </button>
          </div>
        </div>
        <div class="toolbar-actions">
          <button @click="openAddRecordModal" class="btn-action btn-add">
            <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16"><path d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4z"/></svg>
            단일 등록
          </button>
          <button @click="showBulkUploadModal = true" class="btn-action btn-upload">
            <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16"><path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/><path d="M7.646 1.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1-.708.708L8.5 2.707V11.5a.5.5 0 0 1-1 0V2.707L5.354 4.854a.5.5 0 1 1-.708-.708l3-3z"/></svg>
            일괄 등록
          </button>
          <button @click="exportData" class="btn-action btn-export" :disabled="exporting">
            <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16"><path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/><path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"/></svg>
            {{ exporting ? '내보내는 중...' : '내보내기' }}
          </button>
          <button @click="loadEducationData" class="btn-action btn-refresh" :disabled="loading">
            <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2v1z"/><path d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466z"/></svg>
            {{ loading ? '로딩...' : '새로고침' }}
          </button>
        </div>
      </div>

      <!-- 활성 필터 태그 -->
      <div v-if="hasActiveColumnFilters" class="active-filters">
        <span class="filter-label">필터:</span>
        <span v-if="filterDepartment" class="filter-tag" @click="clearColumnFilter('department')">부서: {{ filterDepartment }} ✕</span>
        <span v-if="filterCourse" class="filter-tag" @click="clearColumnFilter('course')">과정: {{ filterCourse }} ✕</span>
        <span v-if="selectedEducationType" class="filter-tag" @click="clearColumnFilter('educationType')">유형: {{ selectedEducationType }} ✕</span>
        <span v-if="selectedStatus" class="filter-tag" @click="clearColumnFilter('status')">수료현황: {{ selectedStatus === '1' ? '수료' : '미수료' }} ✕</span>
        <span v-if="filterExclude" class="filter-tag" @click="clearColumnFilter('exclude')">제외: {{ filterExclude === 'excluded' ? '제외만' : '포함만' }} ✕</span>
        <button class="filter-clear-all" @click="resetColumnFilters">모두 해제</button>
      </div>

      <!-- 일괄 작업 바 (모의훈련과 동일 구조) -->
      <div v-if="selectedRecords.length > 0" class="bulk-actions-bar">
        <span class="bulk-selected-count">✓ {{ selectedRecords.length }}건 선택됨</span>
        <div class="bulk-actions-buttons">
          <button class="bulk-btn" @click="bulkToggleException(true)">
            🚫 일괄 제외
          </button>
          <button class="bulk-btn" @click="bulkToggleException(false)">
            ↩️ 일괄 포함
          </button>
          <button class="bulk-btn bulk-btn-danger" @click="bulkDeleteRecords">
            🗑️ 일괄 삭제
          </button>
          <button class="bulk-btn-clear" @click="clearSelection">
            ✕ 선택 해제
          </button>
        </div>
      </div>

      <!-- 로딩 -->
      <div v-if="loading" class="loading-container">
        <div class="loading-spinner"></div>
        <p>교육 데이터를 불러오는 중...</p>
      </div>

      <!-- 데이터 테이블 -->
      <div v-else-if="paginatedRecords.length > 0 || filteredRecords.length > 0">
        <!-- 테이블 정보 바 (사용자 관리와 동일) -->
        <div class="table-info">
          <span class="table-count">
            총 {{ filteredRecords.length }}건 중 {{ paginatedRecords.length }}건 표시
          </span>
          <select v-model="pageSize" @change="currentPage = 1" class="per-page-select">
            <option :value="10">10개씩</option>
            <option :value="20">20개씩</option>
            <option :value="50">50개씩</option>
            <option :value="100">100개씩</option>
          </select>
        </div>
        <div class="data-table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th class="checkbox-col">
                  <input type="checkbox" v-model="selectAll" @change="toggleSelectAll" />
                </th>
                <th class="col-user" @click="toggleSort('username')">
                  <span class="th-sortable">사용자 <span v-if="sortField === 'username'" class="sort-arrow">{{ sortOrder === 'asc' ? '↑' : '↓' }}</span></span>
                </th>
                <th class="col-dept">
                  <div class="th-filterable" @click.stop="toggleColumnFilter('department', $event)">
                    <span>부서</span>
                    <svg :class="['filter-icon', { active: filterDepartment }]" width="12" height="12" viewBox="0 0 16 16" fill="currentColor"><path d="M1.5 1.5A.5.5 0 0 1 2 1h12a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-.128.334L10 8.692V13.5a.5.5 0 0 1-.342.474l-3 1A.5.5 0 0 1 6 14.5V8.692L1.628 3.834A.5.5 0 0 1 1.5 3.5v-2z"/></svg>
                  </div>
                </th>
                <th class="col-course">
                  <div class="th-filterable" @click.stop="toggleColumnFilter('course', $event)">
                    <span>교육과정</span>
                    <svg :class="['filter-icon', { active: filterCourse }]" width="12" height="12" viewBox="0 0 16 16" fill="currentColor"><path d="M1.5 1.5A.5.5 0 0 1 2 1h12a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-.128.334L10 8.692V13.5a.5.5 0 0 1-.342.474l-3 1A.5.5 0 0 1 6 14.5V8.692L1.628 3.834A.5.5 0 0 1 1.5 3.5v-2z"/></svg>
                  </div>
                </th>
                <th class="col-type">
                  <div class="th-filterable" @click.stop="toggleColumnFilter('educationType', $event)">
                    <span>유형</span>
                    <svg :class="['filter-icon', { active: selectedEducationType }]" width="12" height="12" viewBox="0 0 16 16" fill="currentColor"><path d="M1.5 1.5A.5.5 0 0 1 2 1h12a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-.128.334L10 8.692V13.5a.5.5 0 0 1-.342.474l-3 1A.5.5 0 0 1 6 14.5V8.692L1.628 3.834A.5.5 0 0 1 1.5 3.5v-2z"/></svg>
                  </div>
                </th>
                <th class="col-completion">
                  <div class="th-filterable" @click.stop="toggleColumnFilter('status', $event)">
                    <span>수료 현황</span>
                    <svg :class="['filter-icon', { active: selectedStatus }]" width="12" height="12" viewBox="0 0 16 16" fill="currentColor"><path d="M1.5 1.5A.5.5 0 0 1 2 1h12a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-.128.334L10 8.692V13.5a.5.5 0 0 1-.342.474l-3 1A.5.5 0 0 1 6 14.5V8.692L1.628 3.834A.5.5 0 0 1 1.5 3.5v-2z"/></svg>
                  </div>
                </th>
                <th class="col-exclude">
                  <div class="th-filterable" @click.stop="toggleColumnFilter('exclude', $event)">
                    <span>제외</span>
                    <svg :class="['filter-icon', { active: filterExclude }]" width="12" height="12" viewBox="0 0 16 16" fill="currentColor"><path d="M1.5 1.5A.5.5 0 0 1 2 1h12a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-.128.334L10 8.692V13.5a.5.5 0 0 1-.342.474l-3 1A.5.5 0 0 1 6 14.5V8.692L1.628 3.834A.5.5 0 0 1 1.5 3.5v-2z"/></svg>
                  </div>
                </th>
                <th class="col-actions">관리</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="record in paginatedRecords"
                :key="record.education_id"
                :class="{
                  'row-excluded': record.exclude_from_scoring,
                  'row-selected': selectedRecords.includes(record),
                  'row-legacy': record.is_legacy,
                }"
              >
                <td class="checkbox-col">
                  <input
                    type="checkbox"
                    :checked="selectedRecords.includes(record)"
                    @change="toggleRecordSelection(record)"
                  />
                </td>
                <td class="col-user">
                  <div class="user-name-cell">
                    <span class="user-name">{{ record.username }}</span>
                    <span class="user-email">{{ record.mail || record.email || record.user_id }}</span>
                  </div>
                </td>
                <td class="col-dept">{{ record.department }}</td>
                <td class="col-course">
                  <div class="course-main">{{ record.course_name || '-' }}</div>
                  <div class="course-meta" v-if="record.education_date">{{ record.education_date }}</div>
                </td>
                <td class="col-type">
                  <span class="type-badge" :class="'type-' + (record.education_type || 'default').toLowerCase()">
                    {{ record.education_type || '-' }}
                  </span>
                </td>
                <td class="col-completion">
                  <div class="completion-cell">
                    <div class="completion-top">
                      <span class="status-badge" :class="getStatusFromRate(record.completion_rate).class">
                        {{ getStatusFromRate(record.completion_rate).text }}
                      </span>
                      <span class="completion-counts">
                        수료 <strong>{{ record.completed_count || 0 }}</strong> · 미수료 <strong>{{ record.incomplete_count || 0 }}</strong>
                      </span>
                    </div>
                    <div class="completion-bar">
                      <div class="bar-track">
                        <div
                          class="bar-fill"
                          :class="record.completion_rate >= 100 ? 'fill-pass' : 'fill-fail'"
                          :style="{ width: Math.min(record.completion_rate || 0, 100) + '%' }"
                        ></div>
                      </div>
                      <span class="bar-pct" :class="record.completion_rate >= 100 ? 'pct-pass' : 'pct-fail'">
                        {{ record.completion_rate ? record.completion_rate.toFixed(0) : '0' }}%
                      </span>
                    </div>
                  </div>
                </td>
                <td class="col-exclude">
                  <button
                    @click="toggleExceptionStatus(record)"
                    :class="['exclude-toggle', record.exclude_from_scoring ? 'excluded' : 'included']"
                  >
                    <span class="toggle-dot"></span>
                    {{ record.exclude_from_scoring ? '제외' : '포함' }}
                  </button>
                </td>
                <td class="col-actions">
                  <div class="action-buttons">
                    <button class="action-btn" @click="editRecord(record)" title="수정">
                      <svg width="15" height="15" viewBox="0 0 16 16" fill="currentColor"><path d="M15.502 1.94a.5.5 0 0 1 0 .706L14.459 3.69l-2-2L13.502.646a.5.5 0 0 1 .707 0l1.293 1.293zm-1.75 2.456-2-2L4.939 9.21a.5.5 0 0 0-.121.196l-.805 2.414a.25.25 0 0 0 .316.316l2.414-.805a.5.5 0 0 0 .196-.12l6.813-6.814z"/><path fill-rule="evenodd" d="M1 13.5A1.5 1.5 0 0 0 2.5 15h11a1.5 1.5 0 0 0 1.5-1.5v-6a.5.5 0 0 0-1 0v6a.5.5 0 0 1-.5.5h-11a.5.5 0 0 1-.5-.5v-11a.5.5 0 0 1 .5-.5H9a.5.5 0 0 0 0-1H2.5A1.5 1.5 0 0 0 1 2.5v11z"/></svg>
                    </button>
                    <button class="action-btn danger" @click="deleteRecord(record)" title="삭제">
                      <svg width="15" height="15" viewBox="0 0 16 16" fill="currentColor"><path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/><path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/></svg>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 페이지네이션 (모의훈련과 동일) -->
        <div v-if="totalPages > 1" class="pagination">
          <button class="page-btn" :disabled="currentPage <= 1" @click="currentPage = 1">« 처음</button>
          <button class="page-btn" :disabled="currentPage <= 1" @click="currentPage--">‹ 이전</button>
          <template v-for="page in paginationPages" :key="page">
            <span v-if="page === '...'" class="page-ellipsis">…</span>
            <button v-else class="page-btn" :class="{ active: currentPage === page }" @click="currentPage = page">
              {{ page }}
            </button>
          </template>
          <button class="page-btn" :disabled="currentPage >= totalPages" @click="currentPage++">다음 ›</button>
          <button class="page-btn" :disabled="currentPage >= totalPages" @click="currentPage = totalPages">마지막 »</button>
        </div>
      </div>

      <!-- 빈 상태 -->
      <div v-else class="empty-state">
        교육 기록이 없습니다.
      </div>
    </div>

    <!-- ===== 기간 추가/수정 모달 ===== -->
    <div v-if="showPeriodModal" class="modal-overlay" @click.self="closePeriodModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>{{ editingPeriod ? '교육 기간 수정' : '교육 기간 추가' }}</h3>
          <button class="modal-close" @click="closePeriodModal">✕</button>
        </div>
        <form @submit.prevent="savePeriod">
          <div class="modal-body">
            <div class="form-row">
              <div class="form-group">
                <label>교육 연도</label>
                <input type="number" v-model.number="periodForm.education_year" class="form-input" min="2020" max="2030" />
              </div>
              <div class="form-group">
                <label>교육 유형</label>
                <select v-model="periodForm.education_type" class="form-input">
                  <option value="오프라인">오프라인</option>
                  <option value="온라인">온라인</option>
                </select>
              </div>
            </div>
            <div class="form-group">
              <label>기간명</label>
              <input type="text" v-model="periodForm.period_name" class="form-input" placeholder="예: 상반기, 1분기" />
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>시작일</label>
                <input type="date" v-model="periodForm.start_date" class="form-input" />
              </div>
              <div class="form-group">
                <label>종료일</label>
                <input type="date" v-model="periodForm.end_date" class="form-input" />
              </div>
            </div>
            <div class="form-group">
              <label>설명</label>
              <textarea v-model="periodForm.description" class="form-input" rows="2" placeholder="교육 기간에 대한 설명"></textarea>
            </div>
            <div class="form-group">
              <label class="checkbox-label">
                <input type="checkbox" v-model="periodForm.auto_pass_setting" />
                자동 통과 처리 활성화
              </label>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="cancel-button" @click="closePeriodModal">취소</button>
            <button type="submit" class="save-button" :disabled="saving">
              {{ saving ? '저장 중...' : (editingPeriod ? '수정' : '추가') }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- ===== 일괄 업로드 모달 ===== -->
    <div v-if="showBulkUploadModal" class="modal-overlay" @click.self="closeBulkUploadModal">
      <div class="modal-content wide">
        <div class="modal-header">
          <h3>📤 교육 기록 일괄 등록</h3>
          <button class="modal-close" @click="closeBulkUploadModal">✕</button>
        </div>
        <div class="modal-body">
          <!-- 기간 선택 -->
          <div class="period-select-container">
            <label class="period-select-label">교육 기간 선택</label>
            <select v-model="selectedUploadPeriod" class="period-select">
              <option value="">기간을 선택하세요</option>
              <template v-for="(typeData, typeName) in availablePeriodsForUpload" :key="typeName">
                <optgroup :label="typeName + ' 교육'">
                  <option
                    v-for="period in typeData.periods"
                    :key="period.period_id"
                    :value="period.period_id"
                  >
                    {{ period.period_name }} ({{ period.start_date }} ~ {{ period.end_date }})
                  </option>
                </optgroup>
              </template>
            </select>
          </div>

          <!-- 필드 안내 (모의훈련과 동일 구조) -->
          <div class="field-guide">
            <div class="field-guide-header">
              <div class="field-guide-title">📋 CSV 필드 안내</div>
              <button type="button" class="template-download-btn" @click="downloadTemplate">
                <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16"><path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/><path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"/></svg>
                템플릿 다운로드
              </button>
            </div>
            <div class="field-guide-content">
              <div class="field-row">
                <span class="field-badge required">필수</span>
                <span class="field-names">이름, 부서, 수료, 미수료</span>
              </div>
              <div class="field-row">
                <span class="field-badge optional">선택</span>
                <span class="field-names">수강과정, 교육일</span>
              </div>
              <div class="field-guide-note">
                💡 수료/미수료는 숫자로 입력하세요. (예: 수료 1, 미수료 0)
              </div>
              <div class="field-guide-note">
                💡 수강과정에는 교육 과목명을 입력합니다. (예: <strong>정보보호 기본교육</strong>, <strong>개인정보보호 교육</strong>)
              </div>
            </div>
          </div>

          <!-- 파일 업로드 영역 -->
          <div class="upload-section">
            <div
              class="upload-area"
              :class="{ 'has-file': selectedFile }"
              @click="$refs.fileInput.click()"
              @dragover.prevent
              @drop.prevent="handleFileDrop"
            >
              <input
                type="file"
                ref="fileInput"
                accept=".xlsx,.xls,.csv"
                @change="handleFileChange"
                style="display: none"
              />
              <div v-if="!selectedFile">
                <div class="upload-icon">📁</div>
                <div class="upload-text">파일을 드래그하거나 클릭하여 선택</div>
                <div class="upload-hint">지원 형식: .xlsx, .xls, .csv</div>
              </div>
              <div v-else>
                <div class="upload-icon">✅</div>
                <div class="upload-text">{{ selectedFile.name }}</div>
              </div>
            </div>
            <div v-if="selectedFile" class="file-info">
              <span class="file-name">{{ selectedFile.name }} ({{ (selectedFile.size / 1024).toFixed(1) }}KB)</span>
              <button class="file-remove" @click="selectedFile = null; uploadPreview = []">삭제</button>
            </div>
          </div>

          <!-- 검증 경고 -->
          <div v-if="validationWarnings.length > 0" class="validation-warnings">
            <div v-for="(warning, idx) in validationWarnings" :key="idx" class="warning-item">
              ⚠️ {{ warning }}
            </div>
          </div>

          <!-- 미리보기 -->
          <div v-if="uploadPreview.length > 0">
            <div class="summary-stats">
              <div class="summary-stat">
                <div class="stat-value">{{ uploadPreview.length }}</div>
                <div class="stat-label">총 건수</div>
              </div>
              <div class="summary-stat">
                <div class="stat-value">{{ getTotalCompletedCount() }}</div>
                <div class="stat-label">수료 합계</div>
              </div>
              <div class="summary-stat">
                <div class="stat-value">{{ getTotalIncompleteCount() }}</div>
                <div class="stat-label">미수료 합계</div>
              </div>
            </div>

            <div class="preview-table-container">
              <table class="preview-table">
                <thead>
                  <tr>
                    <th>이름</th>
                    <th>부서</th>
                    <th>과정명</th>
                    <th>수료</th>
                    <th>미수료</th>
                    <th>교육일</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, idx) in uploadPreview.slice(0, 10)" :key="idx">
                    <td>{{ row.username || row.name }}</td>
                    <td>{{ row.department }}</td>
                    <td>{{ row.course_name }}</td>
                    <td>{{ row.completed_count || 0 }}</td>
                    <td>{{ row.incomplete_count || 0 }}</td>
                    <td>{{ row.education_date }}</td>
                  </tr>
                </tbody>
              </table>
              <div v-if="uploadPreview.length > 10" class="preview-note">
                외 {{ uploadPreview.length - 10 }}건 더 있음
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="cancel-button" @click="closeBulkUploadModal">취소</button>
          <button
            class="upload-button"
            @click="uploadBulkData"
            :disabled="!selectedFile || !selectedUploadPeriod || uploading"
          >
            <span v-if="uploading"><div class="inline-spinner"></div> 업로드 중...</span>
            <span v-else>📤 일괄 등록</span>
          </button>
        </div>
      </div>
    </div>

    <!-- ===== 단일 교육 기록 추가 모달 ===== -->
    <div v-if="showAddRecordModal" class="modal-overlay" @click.self="closeAddRecordModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>교육 기록 추가</h3>
          <button class="modal-close" @click="closeAddRecordModal">✕</button>
        </div>
        <form @submit.prevent="saveNewRecord">
          <div class="modal-body">
            <!-- 빈 상태: 기간 없음 -->
            <div v-if="!hasAvailablePeriods" class="empty-periods-notice">
              <div class="empty-periods-icon">📅</div>
              <div class="empty-periods-title">등록 가능한 교육 기간이 없습니다</div>
              <div class="empty-periods-desc">먼저 교육 기간을 생성해주세요.</div>
              <button type="button" class="empty-periods-btn" @click="goToCreatePeriod">
                + 교육 기간 추가
              </button>
            </div>

            <template v-else>
            <!-- 교육 기간 선택 -->
            <div class="form-group">
              <label>교육 기간 <span class="required">*</span></label>
              <select v-model="newRecordForm.period_id" class="form-input" required>
                <option value="">기간을 선택하세요</option>
                <template v-for="(typeData, typeName) in availablePeriodsForUpload" :key="typeName">
                  <optgroup :label="typeName + ' 교육'">
                    <option
                      v-for="period in typeData.periods"
                      :key="period.period_id"
                      :value="period.period_id"
                    >
                      {{ period.period_name }} ({{ period.start_date }} ~ {{ period.end_date }})
                    </option>
                  </optgroup>
                </template>
              </select>
            </div>

            <!-- 사용자 검색 -->
            <div class="form-group">
              <label>사용자 <span class="required">*</span></label>
              <div class="user-search-container">
                <!-- 선택된 사용자가 없을 때: 검색 입력 표시 -->
                <template v-if="!newRecordForm.user_id">
                  <div class="search-input-wrap">
                    <input
                      type="text"
                      v-model="userSearchQuery"
                      @input="searchUsers"
                      @focus="onUserSearchFocus"
                      @blur="onUserSearchBlur"
                      class="form-input"
                      placeholder="사용자명 또는 부서로 검색 후 선택하세요"
                      autocomplete="off"
                    />
                    <span v-if="userSearchLoading" class="search-status-icon">
                      <div class="inline-spinner"></div>
                    </span>
                  </div>
                  <!-- 검색 결과 드롭다운 -->
                  <div v-if="showUserDropdown" class="user-search-dropdown" @mousedown.prevent>
                    <div
                      v-for="user in userSearchResults"
                      :key="user.uid"
                      class="user-search-item"
                      @click="selectUser(user)"
                    >
                      <span class="user-search-name">{{ user.username }}</span>
                      <span class="user-search-dept">{{ user.department }}</span>
                    </div>
                    <div v-if="userSearchResults.length === 0 && !userSearchLoading && userSearchQuery.length >= 1" class="user-search-empty">
                      검색 결과가 없습니다.
                    </div>
                    <div v-if="userSearchLoading" class="user-search-empty">
                      <div class="inline-spinner"></div> 검색 중...
                    </div>
                  </div>
                  <div v-if="userSearchQuery && !showUserDropdown" class="field-hint hint-warning">
                    목록에서 사용자를 선택해주세요.
                  </div>
                </template>
                <!-- 선택된 사용자 표시 -->
                <template v-else>
                  <div class="selected-user-tag">
                    <span>{{ newRecordForm.username }} ({{ newRecordForm.department }})</span>
                    <button type="button" class="tag-remove" @click="clearSelectedUser">✕</button>
                  </div>
                </template>
              </div>
            </div>

            <!-- 교육과정명 -->
            <div class="form-group">
              <label>교육과정명</label>
              <input type="text" v-model="newRecordForm.course_name" class="form-input" placeholder="교육과정명 입력" />
            </div>

            <!-- 수료/미수료 건수 -->
            <div class="form-row">
              <div class="form-group">
                <label>수료 건수 <span class="required">*</span></label>
                <input type="number" v-model.number="newRecordForm.completed_count" class="form-input" min="0" placeholder="0" />
              </div>
              <div class="form-group">
                <label>미수료 건수 <span class="required">*</span></label>
                <input type="number" v-model.number="newRecordForm.incomplete_count" class="form-input" min="0" placeholder="0" />
              </div>
            </div>

            <!-- 교육일 -->
            <div class="form-group">
              <label>교육일</label>
              <input type="date" v-model="newRecordForm.education_date" class="form-input" />
            </div>

            <!-- 비고 -->
            <div class="form-group">
              <label>비고</label>
              <textarea v-model="newRecordForm.notes" class="form-input" rows="2" placeholder="추가 정보나 비고사항"></textarea>
            </div>
            </template>
          </div>
          <div class="modal-footer">
            <button type="button" class="cancel-button" @click="closeAddRecordModal">취소</button>
            <button
              type="submit"
              class="save-button"
              :disabled="saving || !hasAvailablePeriods || !newRecordForm.period_id || !newRecordForm.user_id"
            >
              {{ saving ? '저장 중...' : '추가' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- ===== 교육 기록 수정 모달 ===== -->
    <div v-if="showEditModal" class="modal-overlay" @click.self="closeEditModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>교육 기록 수정</h3>
          <button class="modal-close" @click="closeEditModal">✕</button>
        </div>
        <form @submit.prevent="saveRecord">
          <div class="modal-body">
            <!-- 완료된 기간 경고 배너 -->
            <div v-if="editingRecord.period_is_completed" class="period-completed-warning">
              <div class="warning-icon">⚠️</div>
              <div class="warning-content">
                <div class="warning-title">이 교육 기간은 완료 처리되었습니다</div>
                <div class="warning-desc">수정 사항이 점수 산정에 영향을 줄 수 있으니 신중하게 진행해주세요.</div>
              </div>
            </div>

            <!-- 참고 정보 (readonly) -->
            <div class="readonly-section">
              <div class="readonly-section-title">📄 기록 정보</div>
              <div class="form-row">
                <div class="form-group">
                  <label>사용자</label>
                  <input type="text" :value="editingRecord.username" class="form-input" readonly />
                </div>
                <div class="form-group">
                  <label>부서</label>
                  <input type="text" :value="editingRecord.department" class="form-input" readonly />
                </div>
              </div>
              <div class="form-group">
                <label>교육 기간</label>
                <input
                  type="text"
                  :value="`${editingRecord.period_name || ''}${editingRecord.education_type ? ' (' + editingRecord.education_type + ')' : ''}`"
                  class="form-input"
                  readonly
                />
              </div>
            </div>

            <!-- 편집 가능 필드 -->
            <div class="editable-section">
              <div class="editable-section-title">✏️ 상세 정보</div>

              <div class="form-group">
                <label>교육과정</label>
                <input type="text" v-model="editingRecord.course_name" class="form-input" placeholder="교육과정명" />
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label>수료 건수 <span class="required">*</span></label>
                  <input type="number" v-model.number="editingRecord.completed_count" class="form-input" min="0" placeholder="0" />
                </div>
                <div class="form-group">
                  <label>미수료 건수 <span class="required">*</span></label>
                  <input type="number" v-model.number="editingRecord.incomplete_count" class="form-input" min="0" placeholder="0" />
                </div>
              </div>

              <div class="form-group">
                <label>교육일</label>
                <input type="date" v-model="editingRecord.education_date" class="form-input" />
              </div>
            </div>

            <!-- 점수 관리 -->
            <div class="editable-section">
              <div class="editable-section-title">⚙️ 점수 관리</div>
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
                  rows="2"
                  placeholder="메모를 입력하세요"
                ></textarea>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="cancel-button" @click="closeEditModal">취소</button>
            <button type="submit" class="save-button" :disabled="saving">
              {{ saving ? '저장 중...' : '저장' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- ===== 상세 통계 모달 ===== -->
    <div v-if="showDetailStatsModal" class="modal-overlay" @click.self="closeDetailStatsModal">
      <div class="modal-content extra-wide">
        <div class="modal-header">
          <h3>📊 {{ selectedPeriodStats?.period_info?.period_name }} - 상세 통계</h3>
          <button class="modal-close" @click="closeDetailStatsModal">✕</button>
        </div>
        <div class="modal-body" v-if="selectedPeriodStats">
          <!-- 통계 개요 -->
          <div class="stats-overview">
            <div class="stat-card info">
              <div class="stat-value">{{ selectedPeriodStats.total_participants || 0 }}</div>
              <div class="stat-label">전체 대상자</div>
            </div>
            <div class="stat-card success">
              <div class="stat-value">{{ selectedPeriodStats.success_count || 0 }}</div>
              <div class="stat-label">수료</div>
            </div>
            <div class="stat-card danger">
              <div class="stat-value">{{ selectedPeriodStats.failure_count || 0 }}</div>
              <div class="stat-label">미수료</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ formatSuccessRate(selectedPeriodStats.success_rate) }}</div>
              <div class="stat-label">수료율</div>
            </div>
          </div>

          <!-- 참가자 테이블 -->
          <div v-if="selectedPeriodStats.participants && selectedPeriodStats.participants.length > 0">
            <h4 style="margin: 0 0 12px; font-size: 14px; font-weight: 600; color: #374151;">참가자 목록</h4>
            <div class="participants-table-container">
              <table class="participants-table">
                <thead>
                  <tr>
                    <th>이름</th>
                    <th>부서</th>
                    <th>수료</th>
                    <th>미수료</th>
                    <th>수료율</th>
                    <th>상태</th>
                    <th>제외</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="participant in selectedPeriodStats.participants" :key="participant.user_id">
                    <td>{{ participant.username }}</td>
                    <td>{{ participant.department }}</td>
                    <td>{{ participant.completed_count || 0 }}</td>
                    <td>{{ participant.incomplete_count || 0 }}</td>
                    <td>
                      {{
                        participant.completion_rate
                          ? participant.completion_rate.toFixed(1) + '%'
                          : '0%'
                      }}
                    </td>
                    <td>
                      <span v-if="participant.user_status === 'success'" class="success-badge">수료</span>
                      <span v-else class="failure-badge">미수료</span>
                    </td>
                    <td>
                      <span v-if="participant.exclude_from_scoring" class="excluded-badge">제외</span>
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

    <!-- 컬럼 필터 드롭다운 (Teleport) -->
    <Teleport to="body">
      <div v-if="openFilter" class="cfd-overlay" @click="closeColumnFilter">
        <!-- 부서 필터 -->
        <div v-if="openFilter === 'department'" class="cfd-floating" :style="dropdownPosition" @click.stop>
          <div class="cfd-item" :class="{ selected: !filterDepartment }" @click="setColumnFilter('department', '')">전체 부서</div>
          <div v-for="dept in departmentOptions" :key="dept" class="cfd-item" :class="{ selected: filterDepartment === dept }" @click="setColumnFilter('department', dept)">{{ dept }}</div>
        </div>
        <!-- 교육유형 필터 -->
        <div v-if="openFilter === 'educationType'" class="cfd-floating" :style="dropdownPosition" @click.stop>
          <div class="cfd-item" :class="{ selected: !selectedEducationType }" @click="setColumnFilter('educationType', '')">전체 유형</div>
          <div class="cfd-item" :class="{ selected: selectedEducationType === '오프라인' }" @click="setColumnFilter('educationType', '오프라인')">오프라인</div>
          <div class="cfd-item" :class="{ selected: selectedEducationType === '온라인' }" @click="setColumnFilter('educationType', '온라인')">온라인</div>
        </div>
        <!-- 상태 필터 -->
        <div v-if="openFilter === 'status'" class="cfd-floating" :style="dropdownPosition" @click.stop>
          <div class="cfd-item" :class="{ selected: !selectedStatus }" @click="setColumnFilter('status', '')">전체</div>
          <div class="cfd-item" :class="{ selected: selectedStatus === '1' }" @click="setColumnFilter('status', '1')">수료</div>
          <div class="cfd-item" :class="{ selected: selectedStatus === '0' }" @click="setColumnFilter('status', '0')">미수료</div>
        </div>
        <!-- 교육과정 필터 -->
        <div v-if="openFilter === 'course'" class="cfd-floating" :style="dropdownPosition" @click.stop>
          <div class="cfd-item" :class="{ selected: !filterCourse }" @click="setColumnFilter('course', '')">전체 과정</div>
          <div v-for="course in courseOptions" :key="course" class="cfd-item" :class="{ selected: filterCourse === course }" @click="setColumnFilter('course', course)">{{ course }}</div>
        </div>
        <!-- 제외 필터 -->
        <div v-if="openFilter === 'exclude'" class="cfd-floating" :style="dropdownPosition" @click.stop>
          <div class="cfd-item" :class="{ selected: !filterExclude }" @click="setColumnFilter('exclude', '')">전체</div>
          <div class="cfd-item" :class="{ selected: filterExclude === 'included' }" @click="setColumnFilter('exclude', 'included')">포함만</div>
          <div class="cfd-item" :class="{ selected: filterExclude === 'excluded' }" @click="setColumnFilter('exclude', 'excluded')">제외만</div>
        </div>
      </div>
    </Teleport>

    <!-- 토스트 메시지 -->
    <div v-if="showToast" class="toast" :class="toastType">{{ toastMessage }}</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import Papa from 'papaparse'

// ===== 상태 관리 =====

// 기본 상태
const loading = ref(false)
const saving = ref(false)
const loadingStats = ref(false)

// 필터 및 검색 상태
const selectedYear = ref(new Date().getFullYear())
const selectedEducationType = ref('')
const selectedStatus = ref('')
const searchQuery = ref('')
const filterDepartment = ref('')
const filterCourse = ref('')
const filterExclude = ref('')

// 정렬 상태
const sortField = ref('')
const sortOrder = ref('desc')

// 컬럼 필터 드롭다운 상태
const openFilter = ref(null)
const dropdownPosition = ref({})

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
const exporting = ref(false)
const selectedUploadPeriod = ref('')
const availablePeriodsForUpload = ref({})
const validationWarnings = ref([])

// 수정 모달 상태
const showEditModal = ref(false)
const editingRecord = ref({})

// 단일 추가 모달 상태
const showAddRecordModal = ref(false)
const userSearchQuery = ref('')
const userSearchResults = ref([])
const showUserDropdown = ref(false)
const userSearchTimeout = ref(null)
const userSearchLoading = ref(false)
const newRecordForm = ref({
  period_id: '',
  user_id: null,
  username: '',
  department: '',
  course_name: '',
  completed_count: 0,
  incomplete_count: 0,
  education_date: '',
  notes: '',
})

// 상세 통계 모달
const showDetailStatsModal = ref(false)
const selectedPeriodStats = ref(null)

// 토스트 상태
const showToast = ref(false)
const toastMessage = ref('')
const toastType = ref('success')

// ===== Computed =====

const availableYears = computed(() => {
  const currentYear = new Date().getFullYear()
  const years = []
  for (let y = currentYear + 1; y >= currentYear - 3; y--) {
    years.push(y)
  }
  return years
})

const paginatedRecords = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredRecords.value.slice(start, start + pageSize.value)
})

const totalPages = computed(() => {
  return Math.max(1, Math.ceil(filteredRecords.value.length / pageSize.value))
})

const paginationPages = computed(() => {
  const total = totalPages.value
  const current = currentPage.value
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)
  const pages = []
  pages.push(1)
  if (current > 3) pages.push('...')
  for (let i = Math.max(2, current - 1); i <= Math.min(total - 1, current + 1); i++) {
    pages.push(i)
  }
  if (current < total - 2) pages.push('...')
  pages.push(total)
  return pages
})

const completedCount = computed(() => {
  return filteredRecords.value.filter(r => parseFloat(r.completion_rate || 0) >= 100).length
})

const incompleteCount = computed(() => {
  return filteredRecords.value.filter(r => parseFloat(r.completion_rate || 0) < 100).length
})

const overallCompletionRate = computed(() => {
  if (filteredRecords.value.length === 0) return 0
  return ((completedCount.value / filteredRecords.value.length) * 100).toFixed(1)
})

const hasAvailablePeriods = computed(() => {
  if (!periodStatus.value.education_types) return false
  return Object.values(periodStatus.value.education_types).some(
    (td) => td.periods && td.periods.some((p) => !p.is_completed)
  )
})

const departmentOptions = computed(() => {
  const depts = [...new Set(educationData.value.map(r => r.department).filter(Boolean))]
  return depts.sort()
})

const courseOptions = computed(() => {
  const courses = [...new Set(educationData.value.map(r => r.course_name).filter(Boolean))]
  return courses.sort()
})

const hasActiveColumnFilters = computed(() => {
  return filterDepartment.value || selectedEducationType.value || selectedStatus.value || filterCourse.value || filterExclude.value
})

// ===== 초기화 =====

onMounted(async () => {
  await loadPeriodStatus()
  await loadEducationData()
  await loadAvailablePeriodsForUpload()
})

// ===== 교육 기간 관리 메서드 =====

const loadPeriodStatus = async () => {
  try {
    const response = await fetch(`/api/security-education/periods/statistics?year=${selectedYear.value}`, {
      credentials: 'include',
    })

    if (!response.ok) throw new Error('기간 현황 조회 실패')

    const data = await response.json()
    periodStatus.value = data

    // 디버깅
    const totalPeriods = Object.values(data.education_types || {}).reduce((sum, typeData) => {
      return sum + (typeData.periods ? typeData.periods.length : 0)
    }, 0)
    console.log('[DEBUG] 총 기간 개수:', totalPeriods)
  } catch (err) {
    console.error('기간 현황 조회 오류:', err)
    displayToast('기간 현황을 불러오는데 실패했습니다.', 'error')
  }
}

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

const closePeriodModal = () => {
  showPeriodModal.value = false
  editingPeriod.value = null
}

const editPeriod = (period) => {
  editingPeriod.value = period
  periodForm.value = {
    education_year: period.education_year || selectedYear.value,
    period_name: period.period_name,
    education_type: period.education_type || '오프라인',
    start_date: period.start_date,
    end_date: period.end_date,
    description: period.description || '',
    auto_pass_setting: period.auto_pass_setting !== false,
  }
  showPeriodModal.value = true
}

const savePeriod = async () => {
  if (saving.value) return

  // 유효성 검사
  if (!periodForm.value.period_name || !periodForm.value.education_type ||
      !periodForm.value.start_date || !periodForm.value.end_date) {
    displayToast('필수 필드를 모두 입력해주세요.', 'error')
    return
  }

  if (new Date(periodForm.value.start_date) >= new Date(periodForm.value.end_date)) {
    displayToast('종료일은 시작일보다 늦어야 합니다.', 'error')
    return
  }

  saving.value = true

  try {
    const url = editingPeriod.value
      ? `/api/security-education/periods/${editingPeriod.value.period_id}`
      : '/api/security-education/periods'

    const method = editingPeriod.value ? 'PUT' : 'POST'

    const response = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(periodForm.value),
    })

    const result = await response.json()

    if (!response.ok) {
      throw new Error(result.error || result.message || '기간 저장 실패')
    }

    displayToast(result.message || '저장되었습니다.', 'success')
    closePeriodModal()
    await loadPeriodStatus()
    await loadEducationData()
  } catch (err) {
    console.error('기간 저장 오류:', err)
    displayToast(err.message, 'error')
  } finally {
    saving.value = false
  }
}

const deletePeriod = async (period) => {
  if (!confirm(`"${period.period_name}" 교육 기간을 삭제하시겠습니까?`)) return

  try {
    const response = await fetch(`/api/security-education/periods/${period.period_id}`, {
      method: 'DELETE',
      credentials: 'include',
    })

    const result = await response.json()

    // 성공
    if (response.ok) {
      displayToast(result.message || '삭제되었습니다.', 'success')
      await loadPeriodStatus()
      await loadEducationData()
      return
    }

    // 교육 기록이 있어서 확인이 필요한 경우
    if (response.status === 400 && result.requires_confirmation) {
      const forceDelete = confirm(
        `${result.error || result.message}\n\n` +
        `관련 교육 기록 ${result.education_count}건을 포함하여 완전히 삭제하시겠습니까?\n\n` +
        `※ 이 작업은 되돌릴 수 없습니다.`
      )
      if (forceDelete) {
        await forceDeletePeriod(period.period_id)
      } else {
        displayToast('삭제가 취소되었습니다.', 'info')
      }
      return
    }

    // 기타 에러
    throw new Error(result.error || result.message || '삭제 실패')
  } catch (err) {
    displayToast(err.message, 'error')
  }
}

/**
 * 교육 기간 강제 삭제 (관련 교육 기록 포함)
 */
const forceDeletePeriod = async (periodId) => {
  try {
    const response = await fetch(`/api/security-education/periods/${periodId}/force-delete`, {
      method: 'DELETE',
      credentials: 'include',
    })

    const result = await response.json()
    if (!response.ok) throw new Error(result.error || result.message || '강제 삭제 실패')

    displayToast(result.message || '삭제되었습니다.', 'success')
    await loadPeriodStatus()
    await loadEducationData()
  } catch (err) {
    console.error('강제 삭제 오류:', err)
    displayToast(err.message, 'error')
  }
}

const completePeriod = async (period) => {
  if (!confirm(
    `"${period.period_name}" 교육 기간을 완료 처리하시겠습니까?\n\n` +
    `⚠️ 교육 기록이 없는 사용자는 자동으로 미수료 처리됩니다.`
  )) return

  try {
    const response = await fetch(`/api/security-education/periods/${period.period_id}/complete`, {
      method: 'POST',
      credentials: 'include',
    })

    const result = await response.json()
    if (!response.ok) throw new Error(result.error || result.message || '완료 처리 실패')

    displayToast(result.message || '완료 처리되었습니다.', 'success')
    await loadPeriodStatus()
    await loadEducationData()
  } catch (err) {
    displayToast(err.message, 'error')
  }
}

const reopenPeriod = async (period) => {
  if (!confirm(
    `"${period.period_name}" 교육 기간을 재개하시겠습니까?\n\n` +
    `⚠️ 수정하지 않은 자동 미수료 기록만 삭제됩니다.\n수료로 변경한 기록은 유지됩니다.`
  )) return

  try {
    const response = await fetch(`/api/security-education/periods/${period.period_id}/reopen`, {
      method: 'POST',
      credentials: 'include',
    })

    const result = await response.json()
    if (!response.ok) throw new Error(result.error || result.message || '재개 실패')

    displayToast(result.message || '재개되었습니다.', 'success')
    await loadPeriodStatus()
    await loadEducationData()
  } catch (err) {
    displayToast(err.message, 'error')
  }
}

const viewDetailedStatistics = async (period) => {
  loadingStats.value = true
  try {
    const response = await fetch(`/api/security-education/periods/${period.period_id}/statistics`, {
      credentials: 'include',
    })

    if (!response.ok) throw new Error('상세 통계 조회 실패')

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

const closeDetailStatsModal = () => {
  showDetailStatsModal.value = false
  selectedPeriodStats.value = null
}

// ===== 교육 데이터 메서드 =====

const loadEducationData = async () => {
  loading.value = true
  try {
    const params = new URLSearchParams({
      year: selectedYear.value,
      education_type: selectedEducationType.value,
    })

    const response = await fetch(`/api/security-education/records?${params}`, {
      credentials: 'include',
    })

    if (!response.ok) throw new Error('교육 데이터 조회 실패')

    educationData.value = await response.json()
    applyFilters()
  } catch (err) {
    console.error('교육 데이터 조회 오류:', err)
    displayToast('교육 데이터를 불러오는데 실패했습니다.', 'error')
  } finally {
    loading.value = false
  }
}

const loadAvailablePeriodsForUpload = async () => {
  try {
    const response = await fetch('/api/security-education/periods/status', {
      credentials: 'include',
    })

    if (!response.ok) throw new Error('교육 기간 목록 로드 실패')

    const result = await response.json()
    availablePeriodsForUpload.value = result.education_types || {}
  } catch (err) {
    console.error('교육 기간 로드 오류:', err)
    displayToast('교육 기간 목록을 불러오는데 실패했습니다.', 'error')
  }
}

const applyFilters = () => {
  let records = [...educationData.value]

  // 부서 필터
  if (filterDepartment.value) {
    records = records.filter(r => r.department === filterDepartment.value)
  }

  // 교육과정 필터
  if (filterCourse.value) {
    records = records.filter(r => r.course_name === filterCourse.value)
  }

  // 제외 필터
  if (filterExclude.value) {
    if (filterExclude.value === 'included') {
      records = records.filter(r => !r.exclude_from_scoring)
    } else if (filterExclude.value === 'excluded') {
      records = records.filter(r => r.exclude_from_scoring)
    }
  }

  // 수료 현황 필터 (completion_rate >= 100 = 수료, 그 외 = 미수료)
  if (selectedStatus.value) {
    if (selectedStatus.value === '1') {
      records = records.filter(r => parseFloat(r.completion_rate || 0) >= 100)
    } else if (selectedStatus.value === '0') {
      records = records.filter(r => parseFloat(r.completion_rate || 0) < 100)
      // 미수료 필터 시 수료 건수 많은 순으로 정렬
      records.sort((a, b) => (b.completed_count || 0) - (a.completed_count || 0))
    }
  }

  // 검색어 필터
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    records = records.filter(
      (r) =>
        (r.username && r.username.toLowerCase().includes(query)) ||
        (r.department && r.department.toLowerCase().includes(query)) ||
        (r.email && r.email.toLowerCase().includes(query))
    )
  }

  // 정렬
  if (sortField.value) {
    records.sort((a, b) => {
      let va = a[sortField.value]
      let vb = b[sortField.value]
      // 숫자 비교
      if (typeof va === 'number' || !isNaN(parseFloat(va))) {
        va = parseFloat(va) || 0
        vb = parseFloat(vb) || 0
      } else {
        // 문자열 비교
        va = (va || '').toString().toLowerCase()
        vb = (vb || '').toString().toLowerCase()
      }
      if (va < vb) return sortOrder.value === 'asc' ? -1 : 1
      if (va > vb) return sortOrder.value === 'asc' ? 1 : -1
      return 0
    })
  }

  filteredRecords.value = records
  currentPage.value = 1
  selectedRecords.value = []
  selectAll.value = false
}

const searchEducationData = () => {
  applyFilters()
}

// ===== 컬럼 정렬 (사용자 관리와 동일) =====

const toggleSort = (field) => {
  if (sortField.value === field) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortField.value = field
    sortOrder.value = field === 'username' ? 'asc' : 'desc'
  }
  applyFilters()
}

// ===== 컬럼 필터 드롭다운 (사용자 관리와 동일) =====

const toggleColumnFilter = (col, event) => {
  if (openFilter.value === col) { openFilter.value = null; return }
  const rect = event.currentTarget.getBoundingClientRect()
  dropdownPosition.value = { position: 'fixed', top: `${rect.bottom + 4}px`, left: `${rect.left}px` }
  openFilter.value = col
}

const closeColumnFilter = () => {
  openFilter.value = null
}

const setColumnFilter = (key, val) => {
  if (key === 'department') filterDepartment.value = val
  else if (key === 'educationType') selectedEducationType.value = val
  else if (key === 'status') selectedStatus.value = val
  else if (key === 'course') filterCourse.value = val
  else if (key === 'exclude') filterExclude.value = val
  openFilter.value = null

  // 교육유형은 백엔드 필터이므로 서버 재조회, 나머지는 프론트 필터만 적용
  if (key === 'educationType') {
    loadEducationData()
  } else {
    applyFilters()
  }
}

const clearColumnFilter = (key) => {
  if (key === 'department') filterDepartment.value = ''
  else if (key === 'educationType') selectedEducationType.value = ''
  else if (key === 'status') selectedStatus.value = ''
  else if (key === 'course') filterCourse.value = ''
  else if (key === 'exclude') filterExclude.value = ''

  if (key === 'educationType') {
    loadEducationData()
  } else {
    applyFilters()
  }
}

const resetColumnFilters = () => {
  filterDepartment.value = ''
  selectedEducationType.value = ''
  selectedStatus.value = ''
  filterCourse.value = ''
  filterExclude.value = ''
  sortField.value = ''
  loadEducationData()
}

// ===== 파일 업로드 메서드 =====

const handleFileChange = (e) => {
  const file = e.target.files?.[0]
  if (file) {
    selectedFile.value = file
    previewFile(file)
  }
}

const handleFileDrop = (e) => {
  const file = e.dataTransfer.files?.[0]
  if (file) {
    selectedFile.value = file
    previewFile(file)
  }
}

/**
 * 파일 파싱 (사용자 관리와 동일한 방식: PapaParse + SheetJS)
 * CSV는 인코딩 자동 감지 (UTF-8 / EUC-KR) 지원
 */
const previewFile = async (file) => {
  uploadPreview.value = []
  validationWarnings.value = []

  const ext = file.name.split('.').pop().toLowerCase()

  if (ext === 'csv') {
    // CSV: 인코딩 감지 후 PapaParse로 파싱
    try {
      const csvText = await readFileWithAutoEncoding(file)

      Papa.parse(csvText, {
        header: true,
        skipEmptyLines: true,
        complete: (results) => {
          try {
            const processedRecords = normalizeFieldNames(results.data)
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
            console.error('CSV 데이터 처리 실패:', err)
            displayToast(`데이터 처리 실패: ${err.message}`, 'error')
            uploadPreview.value = []
          }
        },
        error: (err) => {
          console.error('CSV 파싱 실패:', err)
          displayToast('CSV 파일 파싱에 실패했습니다.', 'error')
          selectedFile.value = null
        },
      })
    } catch (err) {
      console.error('파일 읽기 실패:', err)
      displayToast(`파일 읽기 실패: ${err.message}`, 'error')
    }
  } else if (ext === 'xlsx' || ext === 'xls') {
    // Excel: SheetJS 사용
    const reader = new FileReader()
    reader.onload = async (e) => {
      try {
        const XLSX = await import('xlsx')
        const wb = XLSX.read(e.target.result, { type: 'array' })
        const ws = wb.Sheets[wb.SheetNames[0]]
        const rawData = XLSX.utils.sheet_to_json(ws, { raw: false, defval: '' })

        const processedRecords = normalizeFieldNames(rawData)
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
        console.error('엑셀 파싱 실패:', err)
        displayToast('엑셀 파일 파싱에 실패했습니다.', 'error')
        selectedFile.value = null
      }
    }
    reader.readAsArrayBuffer(file)
  } else {
    displayToast('CSV 또는 Excel 파일을 선택해주세요.', 'error')
  }
}

/**
 * CSV 파일 인코딩 자동 감지 (UTF-8 → EUC-KR)
 * 한국어 Excel에서 CSV 저장 시 EUC-KR이 기본이므로 자동 대응
 */
const readFileWithAutoEncoding = async (file) => {
  const buffer = await file.arrayBuffer()

  // 1차: UTF-8 시도 (BOM 있는 경우 포함)
  try {
    const text = new TextDecoder('utf-8', { fatal: true }).decode(buffer)
    return text.replace(/^\uFEFF/, '')
  } catch {
    // UTF-8 디코딩 실패
  }

  // 2차: EUC-KR (한국어 Excel 기본 인코딩)
  try {
    const text = new TextDecoder('euc-kr').decode(buffer)
    console.log('[DEBUG] CSV를 EUC-KR로 읽기 성공')
    return text
  } catch {
    // fallback
  }

  // 3차: latin-1 (최후의 수단)
  return new TextDecoder('latin1').decode(buffer)
}

/**
 * 필드명 정규화 (한글 → 영문)
 */
const normalizeFieldNames = (records) => {
  const fieldMapping = {
    이름: 'username', 사용자명: 'username', 사용자이름: 'username',
    부서: 'department', 소속: 'department', 소속부서: 'department',
    수강과정: 'education_type', 교육과정: 'education_type', 과정명: 'education_type', 과정: 'education_type',
    수료: 'completed_count', 수료횟수: 'completed_count', 완료: 'completed_count', 완료횟수: 'completed_count',
    미수료: 'incomplete_count', 미완료: 'incomplete_count', 미이수: 'incomplete_count', 실패: 'incomplete_count', 실패횟수: 'incomplete_count',
    username: 'username', department: 'department', education_type: 'education_type',
    completed_count: 'completed_count', incomplete_count: 'incomplete_count',
  }

  return records
    .map((record) => {
      const processed = {}
      Object.keys(record).forEach((key) => {
        const normalizedKey = key.trim().replace(/\s+/g, '')
        const mappedKey = fieldMapping[normalizedKey] || fieldMapping[key] || key
        processed[mappedKey] = record[key]
      })
      processed.completed_count = Math.max(0, parseInt(processed.completed_count) || 0)
      processed.incomplete_count = Math.max(0, parseInt(processed.incomplete_count) || 0)
      if (processed.username) processed.username = processed.username.toString().trim()
      if (processed.department) processed.department = processed.department.toString().trim()
      if (processed.education_type) processed.education_type = processed.education_type.toString().trim()
      return processed
    })
    .filter((r) => r.username && r.department)
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

  const requiredFields = ['username', 'department', 'completed_count', 'incomplete_count']

  for (let i = 0; i < records.length; i++) {
    const record = records[i]
    const missingFields = requiredFields.filter((f) => !record[f] && record[f] !== 0)

    if (missingFields.length > 0) {
      errors.push(`행 ${i + 1}: 필수 필드 누락 (${missingFields.join(', ')})`)
      continue
    }

    const completed = parseInt(record.completed_count) || 0
    const incomplete = parseInt(record.incomplete_count) || 0

    if (completed < 0 || incomplete < 0) {
      errors.push(`행 ${i + 1}: 수료/미수료 횟수는 0 이상이어야 합니다`)
    }

    if (completed + incomplete === 0) {
      warnings.push(`행 ${i + 1} (${record.username}): 수료와 미수료가 모두 0입니다`)
    }
  }

  return { warnings, errors }
}

/**
 * 템플릿 다운로드 (BOM 포함하여 한글 깨짐 방지)
 */
const downloadTemplate = async () => {
  try {
    const response = await fetch('/api/security-education/template/download', {
      credentials: 'include',
    })

    if (!response.ok) throw new Error('템플릿 다운로드 실패')

    // UTF-8 텍스트로 읽은 후 BOM을 추가하여 Excel에서 한글 정상 표시
    const text = await response.text()
    const bom = '\uFEFF'
    const blob = new Blob([bom + text], { type: 'text/csv;charset=utf-8;' })

    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = '정보보호교육_업로드_템플릿.csv'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)

    displayToast('템플릿이 다운로드되었습니다.', 'success')
  } catch (err) {
    displayToast(err.message, 'error')
  }
}

// ===== 내보내기 =====

/**
 * 교육 데이터 CSV 내보내기 (현재 선택된 연도 전체)
 */
const exportData = async () => {
  if (exporting.value) return
  exporting.value = true

  try {
    const url = `/api/security-education/export?year=${selectedYear.value}&format=csv`
    const response = await fetch(url, { credentials: 'include' })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: '내보내기 실패' }))
      throw new Error(errorData.error || '내보내기 실패')
    }

    const blob = await response.blob()
    const downloadUrl = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = downloadUrl
    a.download = `정보보호교육_${selectedYear.value}년.csv`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(downloadUrl)

    displayToast(`${selectedYear.value}년 교육 데이터가 다운로드되었습니다.`, 'success')
  } catch (err) {
    console.error('내보내기 오류:', err)
    displayToast(err.message || '내보내기 실패', 'error')
  } finally {
    exporting.value = false
  }
}

// ===== 선택 해제 =====

const clearSelection = () => {
  selectedRecords.value = []
  selectAll.value = false
}

/**
 * 일괄 업로드 실행 (클라이언트 파싱 → JSON 전송)
 */
const uploadBulkData = async () => {
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
    // 클라이언트에서 파싱한 데이터를 JSON으로 전송
    const uploadData = {
      period_id: selectedUploadPeriod.value,
      records: uploadPreview.value.map((record) => ({
        이름: record.username,
        부서: record.department,
        수강과정: record.education_type || '',
        수료: record.completed_count,
        미수료: record.incomplete_count,
      })),
    }

    console.log('[DEBUG] 업로드 데이터 전송:', {
      period_id: uploadData.period_id,
      record_count: uploadData.records.length,
      sample: uploadData.records[0],
    })

    const response = await fetch('/api/security-education/bulk-upload', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(uploadData),
    })

    const result = await response.json()
    if (!response.ok) throw new Error(result.error || result.message || '업로드 실패')

    const successMsg =
      `업로드 완료!\n` +
      (result.success_count > 0 ? `✅ 등록: ${result.success_count}건\n` : '') +
      (result.update_count > 0 ? `🔄 업데이트: ${result.update_count}건\n` : '') +
      (result.error_count > 0 ? `❌ 오류: ${result.error_count}건` : '')

    displayToast(successMsg, 'success')

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

const closeBulkUploadModal = () => {
  showBulkUploadModal.value = false
  selectedFile.value = null
  uploadPreview.value = []
  selectedUploadPeriod.value = ''
  validationWarnings.value = []
}

// ===== 교육 기록 관리 =====

const editRecord = (record) => {
  editingRecord.value = {
    ...record,
    // null이면 빈 문자열로
    course_name: record.course_name || '',
    completed_count: record.completed_count || 0,
    incomplete_count: record.incomplete_count || 0,
    education_date: record.education_date || '',
    exclude_reason: record.exclude_reason || '',
    notes: record.notes || '',
    exclude_from_scoring: !!record.exclude_from_scoring,
    period_is_completed: !!record.period_completed,
    period_name: record.period_name || '',
    education_type: record.education_type || '',
  }
  showEditModal.value = true
}

const saveRecord = async () => {
  if (saving.value) return
  saving.value = true

  try {
    if (!editingRecord.value.education_id) throw new Error('교육 ID가 없습니다.')

    const response = await fetch('/api/security-education/update', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(editingRecord.value),
    })

    const result = await response.json()
    if (!response.ok) throw new Error(result.error || result.message || '수정 실패')

    displayToast(result.message || '수정되었습니다.', 'success')
    closeEditModal()
    await loadEducationData()
  } catch (err) {
    console.error('교육 기록 수정 오류:', err)
    displayToast(err.message, 'error')
  } finally {
    saving.value = false
  }
}

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
    if (!response.ok) throw new Error(result.error || result.message || '삭제 실패')

    displayToast(result.message, 'success')
    await loadEducationData()
  } catch (err) {
    console.error('기록 삭제 오류:', err)
    displayToast(err.message, 'error')
  }
}

const closeEditModal = () => {
  showEditModal.value = false
  editingRecord.value = {}
}

// ===== 단일 교육 기록 추가 =====

const openAddRecordModal = () => {
  newRecordForm.value = {
    period_id: '',
    user_id: null,
    username: '',
    department: '',
    course_name: '',
    completed_count: 0,
    incomplete_count: 0,
    education_date: '',
    notes: '',
  }
  userSearchQuery.value = ''
  userSearchResults.value = []
  showUserDropdown.value = false
  showAddRecordModal.value = true
}

const closeAddRecordModal = () => {
  showAddRecordModal.value = false
  userSearchQuery.value = ''
  userSearchResults.value = []
  showUserDropdown.value = false
  userSearchLoading.value = false
}

const goToCreatePeriod = () => {
  showAddRecordModal.value = false
  showBulkUploadModal.value = false
  openPeriodModal()
}

const searchUsers = () => {
  if (userSearchTimeout.value) clearTimeout(userSearchTimeout.value)

  const query = userSearchQuery.value.trim()
  if (query.length < 1) {
    userSearchResults.value = []
    showUserDropdown.value = false
    userSearchLoading.value = false
    return
  }

  userSearchLoading.value = true
  showUserDropdown.value = true

  userSearchTimeout.value = setTimeout(async () => {
    try {
      const response = await fetch(`/api/security-education/search-users?q=${encodeURIComponent(query)}`, {
        credentials: 'include',
      })

      if (!response.ok) throw new Error('사용자 검색 실패')

      const data = await response.json()
      userSearchResults.value = data.users || []
      showUserDropdown.value = true
    } catch (err) {
      console.error('사용자 검색 오류:', err)
      userSearchResults.value = []
    } finally {
      userSearchLoading.value = false
    }
  }, 300)
}

const onUserSearchFocus = () => {
  if (userSearchQuery.value.trim().length >= 1) {
    showUserDropdown.value = true
    if (userSearchResults.value.length === 0 && !userSearchLoading.value) {
      searchUsers()
    }
  }
}

const onUserSearchBlur = () => {
  // 드롭다운 클릭이 먼저 처리되도록 지연 닫힘
  setTimeout(() => {
    showUserDropdown.value = false
  }, 200)
}

const selectUser = (user) => {
  newRecordForm.value.user_id = user.uid
  newRecordForm.value.username = user.username
  newRecordForm.value.department = user.department
  userSearchQuery.value = ''
  userSearchResults.value = []
  showUserDropdown.value = false
}

const clearSelectedUser = () => {
  newRecordForm.value.user_id = null
  newRecordForm.value.username = ''
  newRecordForm.value.department = ''
}

const saveNewRecord = async () => {
  if (saving.value) return

  // 유효성 검사
  if (!newRecordForm.value.period_id) {
    displayToast('교육 기간을 선택해주세요.', 'error')
    return
  }
  if (!newRecordForm.value.user_id) {
    displayToast('사용자를 선택해주세요.', 'error')
    return
  }

  saving.value = true

  try {
    const response = await fetch('/api/security-education/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        period_id: newRecordForm.value.period_id,
        user_id: newRecordForm.value.user_id,
        course_name: newRecordForm.value.course_name || '',
        completed_count: newRecordForm.value.completed_count || 0,
        incomplete_count: newRecordForm.value.incomplete_count || 0,
        education_date: newRecordForm.value.education_date || null,
        notes: newRecordForm.value.notes || '',
      }),
    })

    const result = await response.json()
    if (!response.ok) throw new Error(result.error || result.message || '등록 실패')

    displayToast(result.message || '교육 기록이 추가되었습니다.', 'success')
    closeAddRecordModal()
    await loadEducationData()
    await loadPeriodStatus()
  } catch (err) {
    console.error('교육 기록 추가 오류:', err)
    displayToast(err.message, 'error')
  } finally {
    saving.value = false
  }
}

// ===== 선택 및 일괄 작업 =====

const toggleSelectAll = () => {
  if (selectAll.value) {
    selectedRecords.value = [...paginatedRecords.value]
  } else {
    selectedRecords.value = []
  }
}

const toggleRecordSelection = (record) => {
  const idx = selectedRecords.value.indexOf(record)
  if (idx > -1) {
    selectedRecords.value.splice(idx, 1)
  } else {
    selectedRecords.value.push(record)
  }
  selectAll.value =
    paginatedRecords.value.length > 0 &&
    selectedRecords.value.length === paginatedRecords.value.length
}

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
    if (!response.ok) throw new Error(result.error || result.message || '제외 상태 변경 실패')

    record.exclude_from_scoring = newExcludeStatus
    record.exclude_reason = newExcludeStatus ? '관리자 설정' : ''

    displayToast(result.message || '제외 상태가 변경되었습니다.', 'success')
  } catch (err) {
    displayToast(err.message, 'error')
  }
}

const bulkToggleException = async (exclude) => {
  if (!confirm(`선택한 ${selectedRecords.value.length}건을 ${exclude ? '제외' : '포함'} 처리하시겠습니까?`)) return

  try {
    for (const record of selectedRecords.value) {
      await fetch('/api/security-education/toggle-exception', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          user_id: record.user_id,
          period_id: record.period_id,
          education_type: record.education_type,
          exclude: exclude,
          exclude_reason: exclude ? '일괄 관리자 설정' : '',
        }),
      })
    }

    displayToast(`${selectedRecords.value.length}건이 ${exclude ? '제외' : '포함'} 처리되었습니다.`, 'success')
    selectedRecords.value = []
    selectAll.value = false
    await loadEducationData()
  } catch (err) {
    displayToast(err.message, 'error')
  }
}

const bulkDeleteRecords = async () => {
  if (!confirm(`선택한 ${selectedRecords.value.length}건을 삭제하시겠습니까?`)) return

  try {
    for (const record of selectedRecords.value) {
      await fetch('/api/security-education/delete', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          user_id: record.user_id,
          period_id: record.period_id,
          education_type: record.education_type,
        }),
      })
    }

    displayToast(`${selectedRecords.value.length}건이 삭제되었습니다.`, 'success')
    selectedRecords.value = []
    selectAll.value = false
    await loadEducationData()
  } catch (err) {
    displayToast(err.message, 'error')
  }
}

// ===== 유틸리티 =====

const formatSuccessRate = (rate) => {
  if (rate === null || rate === undefined) return '0%'
  return `${Math.round(rate * 10) / 10}%`
}

const getSuccessRateClass = (rate) => {
  if (rate >= 100) return 'rate-excellent'
  return 'rate-poor'
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

const getPeriodStatusText = (period) => {
  if (period.is_completed) return '완료됨'
  const now = new Date()
  const startDate = new Date(period.start_date)
  const endDate = new Date(period.end_date)
  if (now < startDate) return '예정'
  if (now > endDate) return '종료됨'
  return '진행중'
}

const getPeriodStatusClass = (period) => {
  if (period.is_completed) return 'status-completed'
  const now = new Date()
  const startDate = new Date(period.start_date)
  const endDate = new Date(period.end_date)
  if (now < startDate) return 'status-upcoming'
  if (now > endDate) return 'status-ended'
  return 'status-active'
}

const getCompletionStatusLabel = (status) => {
  return status === 'success' || status === 'completed' ? '수료' : '미수료'
}

const getCompletionStatusText = (status) => {
  const map = {
    success: '수료',
    completed: '수료',
    partial: '부분수료',
    incomplete: '미수료',
    not_started: '미시작',
    excluded: '제외',
  }
  return map[status] || status || '미수료'
}

const getCompletionStatusClass = (status) => {
  const map = {
    success: 'status-completed',
    completed: 'status-completed',
    partial: 'status-partial',
    incomplete: 'status-incomplete',
    not_started: 'status-not-started',
    excluded: 'status-excluded',
  }
  return map[status] || 'status-incomplete'
}

/**
 * 수료율(completion_rate)로 상태 판정 (DB Generated Column 기반)
 * completion_rate = completed_count / (completed_count + incomplete_count) * 100
 */
const getStatusFromRate = (rate) => {
  const numRate = parseFloat(rate || 0)
  if (numRate >= 100) return { text: '수료', class: 'status-completed' }
  return { text: '미수료', class: 'status-incomplete' }
}

const getCardHeaderStatusText = (record) => {
  const status = record.status
  switch (status) {
    case 'completed': return '수료'
    case 'not_started': return '시작전'
    case 'in_progress': return '진행중'
    case 'incomplete': return '미수료'
    case 'expired': return '기간만료'
    case 'unknown': return '알 수 없음'
    default: return status || '미정'
  }
}

const getCardHeaderStatusClass = (record) => {
  const status = record.status
  switch (status) {
    case 'completed': return 'card-status-completed'
    case 'not_started': return 'card-status-not-started'
    case 'in_progress': return 'card-status-in-progress'
    case 'incomplete': return 'card-status-incomplete'
    case 'expired': return 'card-status-expired'
    case 'unknown': return 'card-status-unknown'
    default: return 'card-status-default'
  }
}

const getTotalCompletedCount = () => {
  return uploadPreview.value.reduce(
    (sum, record) => sum + (parseInt(record.completed_count) || 0), 0
  )
}

const getTotalIncompleteCount = () => {
  return uploadPreview.value.reduce(
    (sum, record) => sum + (parseInt(record.incomplete_count) || 0), 0
  )
}

const displayToast = (message, type = 'success') => {
  toastMessage.value = message
  toastType.value = type
  showToast.value = true

  setTimeout(() => {
    showToast.value = false
  }, 3000)
}

// ===== Watchers =====

watch(selectedYear, () => {
  loadPeriodStatus()
  loadEducationData()
  loadAvailablePeriodsForUpload()
})

</script>

<style scoped>
@import '../styles/AdminSecurityEducationManagement.css';
</style>