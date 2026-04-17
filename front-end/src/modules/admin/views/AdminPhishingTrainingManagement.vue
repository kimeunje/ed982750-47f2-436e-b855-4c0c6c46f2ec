<template>
  <div class="admin-training-management">
    <!-- ===== 페이지 헤더 (교육 관리와 동일) ===== -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">악성메일 모의훈련 관리</h1>
        <p class="page-subtitle">훈련 기간 설정 및 훈련 기록 관리</p>
      </div>
      <div class="header-right">
        <select v-model="selectedYear" class="header-year-select" @change="onYearChange">
          <option v-for="year in availableYears" :key="year" :value="year">{{ year }}년</option>
        </select>
      </div>
    </div>

    <!-- ===== 훈련 기간 관리 섹션 (교육 관리와 동일 테이블 형태) ===== -->
    <div class="period-management-section">
      <div class="section-header">
        <h3>
          <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M3.5 0a.5.5 0 0 1 .5.5V1h8V.5a.5.5 0 0 1 1 0V1h1a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V3a2 2 0 0 1 2-2h1V.5a.5.5 0 0 1 .5-.5zM1 4v10a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V4H1z"/></svg>
          훈련 기간 관리
        </h3>
        <button @click="openPeriodModal" class="btn-action btn-add">
          <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16"><path d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4z"/></svg>
          기간 추가
        </button>
      </div>

      <!-- 훈련 기간 테이블형 리스트 -->
      <div
        class="period-list"
        v-if="periodStatus.training_types && Object.keys(periodStatus.training_types).length > 0"
      >
        <div
          v-for="(typeData, trainingType) in periodStatus.training_types"
          :key="trainingType"
          class="training-type-group"
        >
          <div class="type-group-header">
            <span class="type-group-label">{{ trainingType }} 훈련</span>
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
                  <th class="pt-col-stats">통과</th>
                  <th class="pt-col-stats">실패</th>
                  <th class="pt-col-rate">통과율</th>
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
                    <span class="date-range">{{ period.start_date }} ~ {{ period.end_date }}</span>
                  </td>
                  <td class="pt-col-status">
                    <span class="card-status-badge" :class="getPeriodStatusClass(period)">
                      {{ getPeriodStatusText(period) }}
                    </span>
                  </td>
                  <td class="pt-col-stats" style="text-align: center;">
                    <span class="stat-cell">{{ period.stats?.total_targets || 0 }}</span>
                  </td>
                  <td class="pt-col-stats" style="text-align: center;">
                    <span class="stat-cell success">{{ period.stats?.success_count || 0 }}</span>
                  </td>
                  <td class="pt-col-stats" style="text-align: center;">
                    <span class="stat-cell failure">{{ period.stats?.fail_count || 0 }}</span>
                  </td>
                  <td class="pt-col-rate">
                    <div class="rate-inline">
                      <div class="rate-bar-mini">
                        <div
                          class="rate-fill-mini"
                          :class="(period.stats?.success_rate || 0) >= 50 ? 'fill-pass' : 'fill-fail'"
                          :style="{ width: (period.stats?.success_rate || 0) + '%' }"
                        ></div>
                      </div>
                      <span
                        class="rate-pct"
                        :class="(period.stats?.success_rate || 0) >= 50 ? 'pct-pass' : 'pct-fail'"
                      >{{ formatRate(period.stats?.success_rate) }}</span>
                    </div>
                  </td>
                  <td class="pt-col-actions">
                    <div class="action-buttons">
                      <!-- 상세통계 -->
                      <button class="action-btn" title="상세 통계" @click="viewPeriodStats(period)">
                        <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16"><path d="M4 11H2v3h2v-3zm5-4H7v7h2V7zm5-5h-2v12h2V2zm-2-1a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1h-2zM6 7a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v7a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V7zm-5 4a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1H2a1 1 0 0 1-1-1v-3z"/></svg>
                      </button>
                      <!-- 완료/재개 -->
                      <button
                        v-if="!period.is_completed"
                        class="action-btn complete"
                        title="완료 처리"
                        @click="completePeriod(period)"
                      >
                        <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16"><path d="M10.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425a.267.267 0 0 1 .02-.022z"/></svg>
                      </button>
                      <button
                        v-else
                        class="action-btn reopen"
                        title="재개"
                        @click="reopenPeriod(period)"
                      >
                        <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M8 3a5 5 0 1 1-4.546 2.914.5.5 0 0 0-.908-.417A6 6 0 1 0 8 2v1z"/><path d="M8 4.466V.534a.25.25 0 0 0-.41-.192L5.23 2.308a.25.25 0 0 0 0 .384l2.36 1.966A.25.25 0 0 0 8 4.466z"/></svg>
                      </button>
                      <!-- 수정 -->
                      <button class="action-btn" title="수정" @click="editPeriod(period)">
                        <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16"><path d="M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708l-10 10a.5.5 0 0 1-.168.11l-5 2a.5.5 0 0 1-.65-.65l2-5a.5.5 0 0 1 .11-.168l10-10zM11.207 2.5 13.5 4.793 14.793 3.5 12.5 1.207 11.207 2.5zm1.586 3L10.5 3.207 4 9.707V10h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.293l6.5-6.5zm-9.761 5.175-.106.106-1.528 3.821 3.821-1.528.106-.106A.5.5 0 0 1 5 12.5V12h-.5a.5.5 0 0 1-.5-.5V11h-.5a.5.5 0 0 1-.468-.325z"/></svg>
                      </button>
                      <!-- 삭제 -->
                      <button class="action-btn danger" title="삭제" @click="deletePeriod(period)">
                        <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16"><path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/><path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/></svg>
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- 기간이 없을 때 -->
      <div v-else class="no-periods">
        등록된 훈련 기간이 없습니다. '기간 추가' 버튼으로 훈련 기간을 설정해주세요.
      </div>
    </div>

    <!-- ===== 훈련 기록 관리 (헤더 + 툴바 + 테이블 통합) ===== -->
    <div class="table-section">
      <!-- 섹션 헤더 -->
      <div class="table-section-header">
        <h3>훈련 기록 ({{ filteredRecords.length }}건)</h3>
      </div>

      <!-- 툴바: 검색 + 액션 -->
      <div class="table-toolbar">
        <div class="toolbar-left">
          <div class="search-wrapper">
            <span class="search-icon">
              <svg width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
            </span>
            <input
              type="text"
              v-model="searchQuery"
              @input="searchTrainingData"
              placeholder="사용자명, 부서, 이메일 검색..."
              class="search-input"
            />
            <button v-if="searchQuery" class="search-clear" @click="searchQuery = ''; searchTrainingData()">
              <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16"><path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/></svg>
            </button>
          </div>
        </div>
        <div class="toolbar-actions">
          <button @click="openAddRecordModal" class="btn-action btn-add">
            <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16"><path d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4z"/></svg>
            단일 등록
          </button>
          <button @click="openUploadModal" class="btn-action btn-upload">
            <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16"><path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/><path d="M7.646 1.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1-.708.708L8.5 2.707V11.5a.5.5 0 0 1-1 0V2.707L5.354 4.854a.5.5 0 1 1-.708-.708l3-3z"/></svg>
            일괄 등록
          </button>
          <button @click="exportData" class="btn-action btn-export" :disabled="exporting">
            <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16"><path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/><path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"/></svg>
            {{ exporting ? '내보내는 중...' : '내보내기' }}
          </button>
          <button @click="refreshData" class="btn-action btn-refresh" :disabled="loading">
            <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2v1z"/><path d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466z"/></svg>
            {{ loading ? '로딩...' : '새로고침' }}
          </button>
        </div>
      </div>

      <!-- 활성 필터 태그 -->
      <div v-if="hasActiveFilters" class="active-filters">
        <span class="filter-label">필터:</span>
        <span v-if="filterTrainingType" class="filter-tag" @click="filterTrainingType = ''; applyFilters()">
          훈련유형: {{ filterTrainingType }} ✕
        </span>
        <span v-if="filterDepartment" class="filter-tag" @click="filterDepartment = ''; applyFilters()">
          부서: {{ filterDepartment }} ✕
        </span>
        <span v-if="filterPeriod" class="filter-tag" @click="filterPeriod = ''; applyFilters()">
          훈련기간: {{ filterPeriod }} ✕
        </span>
        <span v-if="filterMailType" class="filter-tag" @click="filterMailType = ''; applyFilters()">
          메일유형: {{ filterMailType }} ✕
        </span>
        <span v-if="filterResult" class="filter-tag" @click="filterResult = ''; applyFilters()">
          결과: {{ getResultFilterLabel(filterResult) }} ✕
        </span>
        <span v-if="filterExclude" class="filter-tag" @click="filterExclude = ''; applyFilters()">
          제외: {{ filterExclude === 'excluded' ? '제외' : '포함' }} ✕
        </span>
        <button class="filter-clear-all" @click="clearAllFilters">모두 해제</button>
      </div>

      <!-- 테이블 정보 바 -->
      <div class="table-info">
        <span class="table-count">
          총 {{ filteredRecords.length }}건 중 {{ paginatedRecords.length }}건 표시
        </span>
        <select v-model="recordsPerPage" @change="currentPage = 1" class="per-page-select">
          <option :value="10">10개씩</option>
          <option :value="20">20개씩</option>
          <option :value="50">50개씩</option>
          <option :value="100">100개씩</option>
        </select>
      </div>

      <!-- 로딩 상태 -->
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <span style="color: #6b7280; font-size: 14px;">데이터를 불러오는 중...</span>
      </div>

      <!-- 데이터 테이블 -->
      <div v-else-if="filteredRecords.length > 0" class="data-table-container">
        <!-- 일괄 작업 바 -->
        <div v-if="selectedCount > 0" class="bulk-actions-bar">
          <span class="bulk-selected-count">✓ {{ selectedCount }}건 선택됨</span>
          <div class="bulk-actions-buttons">
            <button class="bulk-btn" @click="bulkToggleExclude(true)">
              🚫 일괄 제외
            </button>
            <button class="bulk-btn" @click="bulkToggleExclude(false)">
              ↩️ 일괄 포함
            </button>
            <button class="bulk-btn bulk-btn-danger" @click="bulkDelete">
              🗑️ 선택 삭제
            </button>
            <button class="bulk-btn-clear" @click="clearSelection">
              ✕ 선택 해제
            </button>
          </div>
        </div>

        <table class="data-table">
          <thead>
            <tr>
              <th class="col-checkbox">
                <input
                  type="checkbox"
                  :checked="isAllSelected"
                  :indeterminate.prop="isPartiallySelected"
                  @change="toggleSelectAll"
                />
              </th>
              <th class="col-user" @click="toggleSort('username')">
                <span>사용자</span>
                <span class="sort-indicator" :class="{ active: sortField === 'username' }">{{ sortField === 'username' ? (sortOrder === 'asc' ? '↑' : '↓') : '↕' }}</span>
              </th>
              <th class="col-dept">
                <div class="th-filterable" @click.stop="toggleColumnFilter('department', $event)">
                  <span>부서</span>
                  <svg :class="['filter-icon', { active: filterDepartment }]" width="12" height="12" viewBox="0 0 16 16" fill="currentColor"><path d="M1.5 1.5A.5.5 0 0 1 2 1h12a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-.128.334L10 8.692V13.5a.5.5 0 0 1-.342.474l-3 1A.5.5 0 0 1 6 14.5V8.692L1.628 3.834A.5.5 0 0 1 1.5 3.5v-2z"/></svg>
                </div>
              </th>
              <th class="col-period">
                <div class="th-filterable" @click.stop="toggleColumnFilter('period', $event)">
                  <span>훈련기간</span>
                  <svg :class="['filter-icon', { active: filterPeriod }]" width="12" height="12" viewBox="0 0 16 16" fill="currentColor"><path d="M1.5 1.5A.5.5 0 0 1 2 1h12a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-.128.334L10 8.692V13.5a.5.5 0 0 1-.342.474l-3 1A.5.5 0 0 1 6 14.5V8.692L1.628 3.834A.5.5 0 0 1 1.5 3.5v-2z"/></svg>
                </div>
              </th>
              <th class="col-dept">
                <div class="th-filterable" @click.stop="toggleColumnFilter('trainingType', $event)">
                  <span>훈련유형</span>
                  <svg :class="['filter-icon', { active: filterTrainingType }]" width="12" height="12" viewBox="0 0 16 16" fill="currentColor"><path d="M1.5 1.5A.5.5 0 0 1 2 1h12a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-.128.334L10 8.692V13.5a.5.5 0 0 1-.342.474l-3 1A.5.5 0 0 1 6 14.5V8.692L1.628 3.834A.5.5 0 0 1 1.5 3.5v-2z"/></svg>
                </div>
              </th>
              <th class="col-detail">
                <div class="th-filterable" @click.stop="toggleColumnFilter('mailType', $event)">
                  <span>훈련 상세</span>
                  <svg :class="['filter-icon', { active: filterMailType }]" width="12" height="12" viewBox="0 0 16 16" fill="currentColor"><path d="M1.5 1.5A.5.5 0 0 1 2 1h12a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-.128.334L10 8.692V13.5a.5.5 0 0 1-.342.474l-3 1A.5.5 0 0 1 6 14.5V8.692L1.628 3.834A.5.5 0 0 1 1.5 3.5v-2z"/></svg>
                </div>
              </th>
              <th class="col-result-time">
                <div class="th-filterable" @click.stop="toggleColumnFilter('result', $event)">
                  <span>결과/시각</span>
                  <svg :class="['filter-icon', { active: filterResult }]" width="12" height="12" viewBox="0 0 16 16" fill="currentColor"><path d="M1.5 1.5A.5.5 0 0 1 2 1h12a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-.128.334L10 8.692V13.5a.5.5 0 0 1-.342.474l-3 1A.5.5 0 0 1 6 14.5V8.692L1.628 3.834A.5.5 0 0 1 1.5 3.5v-2z"/></svg>
                </div>
              </th>
              <th class="col-exclude">
                <div class="th-filterable" @click.stop="toggleColumnFilter('exclude', $event)">
                  <span>제외</span>
                  <svg :class="['filter-icon', { active: filterExclude }]" width="12" height="12" viewBox="0 0 16 16" fill="currentColor"><path d="M1.5 1.5A.5.5 0 0 1 2 1h12a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-.128.334L10 8.692V13.5a.5.5 0 0 1-.342.474l-3 1A.5.5 0 0 1 6 14.5V8.692L1.628 3.834A.5.5 0 0 1 1.5 3.5v-2z"/></svg>
                </div>
              </th>
              <th class="col-actions">작업</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="record in paginatedRecords"
              :key="record.training_id"
              :class="{ excluded: record.exclude_from_scoring, selected: selectedRecordIds.has(record.training_id) }"
            >
              <td class="col-checkbox">
                <input
                  type="checkbox"
                  :checked="selectedRecordIds.has(record.training_id)"
                  @change="toggleSelectRecord(record.training_id)"
                />
              </td>
              <td class="col-user">
                <div class="user-cell-info">
                  <span class="user-name">{{ record.username }}</span>
                  <span class="user-email" :title="record.target_email">{{ record.target_email }}</span>
                </div>
              </td>
              <td class="col-dept">{{ record.department }}</td>
              <td class="col-period">
                <div class="period-info">
                  <span class="period-name">{{ record.period_name }}</span>
                </div>
              </td>
              <td class="col-dept">{{ record.training_type }}</td>
              <td class="col-detail">
                <div v-if="record.mail_type || record.log_type" class="detail-cell">
                  <span v-if="record.mail_type" class="detail-main">{{ record.mail_type }}</span>
                  <span v-if="record.log_type" class="detail-sub">{{ record.log_type }}</span>
                </div>
                <span v-else class="cell-empty">-</span>
              </td>
              <td class="col-result-time">
                <div class="result-time-cell">
                  <span class="result-badge" :class="'result-' + record.training_result">
                    {{ getResultText(record.training_result) }}
                  </span>
                  <div v-if="record.email_sent_time || record.action_time" class="time-lines">
                    <span v-if="record.email_sent_time" class="time-line">발송 {{ formatDate(record.email_sent_time) }}</span>
                    <span v-if="record.action_time" class="time-line">수행 {{ formatDate(record.action_time) }}</span>
                  </div>
                </div>
              </td>
              <td class="col-exclude">
                <button
                  class="exclude-toggle"
                  :class="record.exclude_from_scoring ? 'excluded' : 'included'"
                  @click="toggleExclude(record)"
                >
                  <span class="toggle-dot"></span>
                  {{ record.exclude_from_scoring ? '제외' : '포함' }}
                </button>
              </td>
              <td class="col-actions">
                <div class="action-buttons">
                  <button class="action-btn" title="수정" @click="editRecord(record)">
                    <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16"><path d="M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708l-10 10a.5.5 0 0 1-.168.11l-5 2a.5.5 0 0 1-.65-.65l2-5a.5.5 0 0 1 .11-.168l10-10zM11.207 2.5 13.5 4.793 14.793 3.5 12.5 1.207 11.207 2.5zm1.586 3L10.5 3.207 4 9.707V10h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.293l6.5-6.5zm-9.761 5.175-.106.106-1.528 3.821 3.821-1.528.106-.106A.5.5 0 0 1 5 12.5V12h-.5a.5.5 0 0 1-.5-.5V11h-.5a.5.5 0 0 1-.468-.325z"/></svg>
                  </button>
                  <button class="action-btn danger" title="삭제" @click="deleteRecord(record)">
                    <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16"><path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/><path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/></svg>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 데이터 없음 -->
      <div v-else class="empty-state">
        조건에 해당하는 훈련 기록이 없습니다.
      </div>

      <!-- 페이지네이션 -->
      <div v-if="totalPages > 1" class="pagination">
        <button class="page-btn" :disabled="currentPage <= 1" @click="currentPage = 1">«</button>
        <button class="page-btn" :disabled="currentPage <= 1" @click="currentPage--">‹</button>
        <template v-for="page in paginationPages" :key="page">
          <span v-if="page === '...'" class="page-ellipsis">...</span>
          <button v-else class="page-btn" :class="{ active: currentPage === page }" @click="currentPage = page">
            {{ page }}
          </button>
        </template>
        <button class="page-btn" :disabled="currentPage >= totalPages" @click="currentPage++">›</button>
        <button class="page-btn" :disabled="currentPage >= totalPages" @click="currentPage = totalPages">»</button>
      </div>
    </div>

    <!-- ===== 컬럼 필터 드롭다운 ===== -->
    <div v-if="openFilterColumn" class="cfd-overlay" @click="openFilterColumn = null">
      <div class="cfd-floating" :style="dropdownPosition" @click.stop>
        <!-- 훈련유형 필터 -->
        <template v-if="openFilterColumn === 'trainingType'">
          <div class="cfd-item" :class="{ selected: !filterTrainingType }" @click="filterTrainingType = ''; applyFilters(); openFilterColumn = null">전체</div>
          <div class="cfd-item" :class="{ selected: filterTrainingType === '이메일 피싱' }" @click="filterTrainingType = '이메일 피싱'; applyFilters(); openFilterColumn = null">이메일 피싱</div>
          <div class="cfd-item" :class="{ selected: filterTrainingType === 'SMS 피싱' }" @click="filterTrainingType = 'SMS 피싱'; applyFilters(); openFilterColumn = null">SMS 피싱</div>
          <div class="cfd-item" :class="{ selected: filterTrainingType === '전화 피싱' }" @click="filterTrainingType = '전화 피싱'; applyFilters(); openFilterColumn = null">전화 피싱</div>
        </template>
        <!-- 부서 필터 -->
        <template v-if="openFilterColumn === 'department'">
          <div class="cfd-item" :class="{ selected: !filterDepartment }" @click="filterDepartment = ''; applyFilters(); openFilterColumn = null">전체</div>
          <div
            v-for="dept in uniqueDepartments"
            :key="dept"
            class="cfd-item"
            :class="{ selected: filterDepartment === dept }"
            @click="filterDepartment = dept; applyFilters(); openFilterColumn = null"
          >{{ dept }}</div>
        </template>
        <!-- 훈련기간 필터 -->
        <template v-if="openFilterColumn === 'period'">
          <div class="cfd-item" :class="{ selected: !filterPeriod }" @click="filterPeriod = ''; applyFilters(); openFilterColumn = null">전체</div>
          <div
            v-for="pname in uniquePeriods"
            :key="pname"
            class="cfd-item"
            :class="{ selected: filterPeriod === pname }"
            @click="filterPeriod = pname; applyFilters(); openFilterColumn = null"
          >{{ pname }}</div>
        </template>
        <!-- 메일유형 필터 -->
        <template v-if="openFilterColumn === 'mailType'">
          <div class="cfd-item" :class="{ selected: !filterMailType }" @click="filterMailType = ''; applyFilters(); openFilterColumn = null">전체</div>
          <div
            v-for="mt in uniqueMailTypes"
            :key="mt"
            class="cfd-item"
            :class="{ selected: filterMailType === mt }"
            @click="filterMailType = mt; applyFilters(); openFilterColumn = null"
          >{{ mt }}</div>
        </template>
        <!-- 결과 필터 -->
        <template v-if="openFilterColumn === 'result'">
          <div class="cfd-item" :class="{ selected: !filterResult }" @click="filterResult = ''; applyFilters(); openFilterColumn = null">전체</div>
          <div class="cfd-item" :class="{ selected: filterResult === 'success' }" @click="filterResult = 'success'; applyFilters(); openFilterColumn = null">성공(통과)</div>
          <div class="cfd-item" :class="{ selected: filterResult === 'fail' }" @click="filterResult = 'fail'; applyFilters(); openFilterColumn = null">실패</div>
          <div class="cfd-item" :class="{ selected: filterResult === 'no_response' }" @click="filterResult = 'no_response'; applyFilters(); openFilterColumn = null">무응답</div>
        </template>
        <!-- 제외 필터 -->
        <template v-if="openFilterColumn === 'exclude'">
          <div class="cfd-item" :class="{ selected: !filterExclude }" @click="filterExclude = ''; applyFilters(); openFilterColumn = null">전체</div>
          <div class="cfd-item" :class="{ selected: filterExclude === 'included' }" @click="filterExclude = 'included'; applyFilters(); openFilterColumn = null">포함</div>
          <div class="cfd-item" :class="{ selected: filterExclude === 'excluded' }" @click="filterExclude = 'excluded'; applyFilters(); openFilterColumn = null">제외</div>
        </template>
      </div>
    </div>

    <!-- ===== 기간 추가/수정 모달 ===== -->
    <div v-if="showPeriodModal" class="modal-overlay" @click.self="closePeriodModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>{{ editingPeriod ? '훈련 기간 수정' : '훈련 기간 추가' }}</h3>
          <button class="modal-close" @click="closePeriodModal">✕</button>
        </div>
        <form @submit.prevent="savePeriod">
          <div class="modal-body">
            <div class="form-row">
              <div class="form-group">
                <label>훈련 연도</label>
                <input type="number" v-model.number="periodForm.training_year" class="form-input" min="2020" max="2030" />
              </div>
              <div class="form-group">
                <label>훈련 유형</label>
                <select v-model="periodForm.training_type" class="form-input">
                  <option value="이메일 피싱">이메일 피싱</option>
                  <option value="SMS 피싱">SMS 피싱</option>
                  <option value="전화 피싱">전화 피싱</option>
                </select>
              </div>
            </div>
            <div class="form-group">
              <label>기간명</label>
              <input type="text" v-model="periodForm.period_name" class="form-input" placeholder="예: 1차 피싱 훈련" />
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
              <textarea v-model="periodForm.description" class="form-input" rows="2" placeholder="훈련 기간에 대한 설명"></textarea>
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
    <div v-if="showUploadModal" class="modal-overlay" @click.self="closeUploadModal">
      <div class="modal-content wide">
        <div class="modal-header">
          <h3>📤 훈련 기록 일괄 등록</h3>
          <button class="modal-close" @click="closeUploadModal">✕</button>
        </div>
        <div class="modal-body">
          <!-- 빈 상태: 기간 없음 -->
          <div v-if="!hasAvailablePeriods" class="empty-periods-notice">
            <div class="empty-periods-icon">📅</div>
            <div class="empty-periods-title">등록 가능한 훈련 기간이 없습니다</div>
            <div class="empty-periods-desc">먼저 훈련 기간을 생성해주세요.</div>
            <button type="button" class="empty-periods-btn" @click="goToCreatePeriod">
              + 훈련 기간 추가
            </button>
          </div>

          <template v-else>
          <!-- 기간 선택 -->
          <div class="period-select-container">
            <label class="period-select-label">훈련 기간 선택 <span class="required">*</span></label>
            <select v-model="uploadForm.period_id" class="period-select">
              <option value="">기간을 선택하세요</option>
              <template v-for="(typeData, typeName) in periodStatus.training_types" :key="typeName">
                <optgroup :label="typeName + ' 훈련'">
                  <option
                    v-for="period in typeData.periods"
                    :key="period.period_id"
                    :value="period.period_id"
                    :disabled="period.is_completed"
                  >
                    {{ period.period_name }} ({{ period.start_date }} ~ {{ period.end_date }}){{ period.is_completed ? ' [완료]' : '' }}
                  </option>
                </optgroup>
              </template>
            </select>
          </div>

          <!-- 필드 안내 -->
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
                <span class="field-names">이름, 부서, 훈련결과</span>
              </div>
              <div class="field-row">
                <span class="field-badge optional">선택</span>
                <span class="field-names">메일유형, 로그유형, 발송시각, 수행시각</span>
              </div>
              <div class="field-guide-note">
                💡 선택 필드는 비워둬도 업로드됩니다. 업로드 후 각 행의 수정 버튼으로 상세 내용을 보완할 수 있습니다.
              </div>
              <div class="field-guide-note">
                💡 훈련결과는 <strong>통과</strong>, <strong>실패</strong>, <strong>무응답</strong> 중 하나로 입력하세요.
              </div>
            </div>
          </div>

          <!-- 파일 업로드 영역 -->
          <div class="upload-section">
            <div
              class="upload-area"
              :class="{ 'has-file': uploadForm.file, dragover: isDragover }"
              @click="$refs.fileInput.click()"
              @dragover.prevent="isDragover = true"
              @dragleave="isDragover = false"
              @drop.prevent="handleFileDrop"
            >
              <input
                type="file"
                ref="fileInput"
                accept=".xlsx,.xls,.csv"
                @change="handleFileChange"
                style="display: none"
              />
              <div v-if="!uploadForm.file">
                <div class="upload-icon">📁</div>
                <div class="upload-text">파일을 드래그하거나 클릭하여 선택</div>
                <div class="upload-hint">지원 형식: .xlsx, .xls, .csv (최대 10MB)</div>
              </div>
              <div v-else>
                <div class="upload-icon">✅</div>
                <div class="upload-text">{{ uploadForm.file.name }}</div>
              </div>
            </div>
            <div v-if="uploadForm.file" class="file-info">
              <span class="file-name">📄 {{ uploadForm.file.name }} ({{ (uploadForm.file.size / 1024).toFixed(1) }}KB)</span>
              <button class="file-remove" @click.stop="removeFile">삭제</button>
            </div>
          </div>

          <!-- 검증 경고 -->
          <div v-if="validationWarnings.length > 0" class="validation-warnings">
            <div v-for="(warning, idx) in validationWarnings.slice(0, 5)" :key="idx" class="warning-item">
              ⚠️ {{ warning }}
            </div>
            <div v-if="validationWarnings.length > 5" class="warning-item warning-more">
              ...외 {{ validationWarnings.length - 5 }}건의 경고
            </div>
          </div>

          <!-- 요약 통계 -->
          <div v-if="uploadPreview.length > 0" class="summary-stats">
            <div class="summary-stat">
              <div class="stat-value">{{ uploadPreview.length }}</div>
              <div class="stat-label">총 건수</div>
            </div>
            <div class="summary-stat stat-success">
              <div class="stat-value">{{ uploadPreview.filter(r => r.training_result === 'success').length }}</div>
              <div class="stat-label">통과</div>
            </div>
            <div class="summary-stat stat-danger">
              <div class="stat-value">{{ uploadPreview.filter(r => r.training_result === 'fail').length }}</div>
              <div class="stat-label">실패</div>
            </div>
            <div class="summary-stat stat-warning">
              <div class="stat-value">{{ uploadPreview.filter(r => r.training_result === 'no_response' || r.training_result === 'unknown').length }}</div>
              <div class="stat-label">무응답/기타</div>
            </div>
          </div>

          <!-- 사전 검증 결과 (preflight) -->
          <div v-if="runningPreflight" class="preflight-box preflight-loading">
            <span class="inline-spinner"></span>
            사전 검증 중...
          </div>
          <div v-else-if="preflightResult && uploadPreview.length > 0" class="preflight-box">
            <div class="preflight-title">🔍 사전 검증 결과</div>
            <div class="preflight-stats">
              <div class="preflight-stat preflight-create" v-if="preflightResult.will_create > 0">
                <span class="preflight-label">✨ 신규 등록</span>
                <span class="preflight-value">{{ preflightResult.will_create }}건</span>
              </div>
              <div class="preflight-stat preflight-update" v-if="preflightResult.will_update > 0">
                <span class="preflight-label">🔄 기존 덮어쓰기</span>
                <span class="preflight-value">{{ preflightResult.will_update }}건</span>
              </div>
              <div class="preflight-stat preflight-missing" v-if="preflightResult.not_found_count > 0">
                <span class="preflight-label">⚠️ 사용자 없음</span>
                <span class="preflight-value">{{ preflightResult.not_found_count }}건</span>
              </div>
            </div>
            <div v-if="preflightResult.will_update > 0" class="preflight-note preflight-note-warn">
              ⚠️ <strong>{{ preflightResult.will_update }}건</strong>은 이미 존재하는 기록이며, 업로드 시 덮어쓰기됩니다.
              <span v-if="preflightResult.update_targets && preflightResult.update_targets.length">
                (예: {{ preflightResult.update_targets.slice(0, 3).join(', ') }}<span v-if="preflightResult.update_targets.length > 3"> 등</span>)
              </span>
            </div>
            <div v-if="preflightResult.not_found_count > 0" class="preflight-note preflight-note-error">
              ❌ <strong>{{ preflightResult.not_found_count }}건</strong>의 사용자는 시스템에 등록되어 있지 않아 업로드되지 않습니다.
              <span v-if="preflightResult.not_found_samples && preflightResult.not_found_samples.length">
                (예: {{ preflightResult.not_found_samples.slice(0, 3).map(s => `${s.username}(${s.department})`).join(', ') }})
              </span>
            </div>
          </div>

          <!-- 미리보기 테이블 -->
          <div v-if="uploadPreview.length > 0" class="preview-section">
            <h4>업로드 미리보기 ({{ uploadPreview.length }}건)</h4>
            <div class="preview-table-wrap">
              <table class="preview-table">
                <thead>
                  <tr>
                    <th>이름 <span class="th-required">*</span></th>
                    <th>부서 <span class="th-required">*</span></th>
                    <th>훈련결과 <span class="th-required">*</span></th>
                    <th>메일유형</th>
                    <th>로그유형</th>
                    <th>수행시각</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(item, index) in uploadPreview.slice(0, 10)" :key="index">
                    <td>{{ item.username }}</td>
                    <td>{{ item.department }}</td>
                    <td>
                      <span class="result-badge" :class="'result-' + item.training_result">
                        {{ getResultText(item.training_result) }}
                      </span>
                    </td>
                    <td :class="{ 'cell-empty': !item.mail_type }">{{ item.mail_type || '-' }}</td>
                    <td :class="{ 'cell-empty': !item.log_type }">{{ item.log_type || '-' }}</td>
                    <td :class="{ 'cell-empty': !item.action_time }">{{ item.action_time ? formatDate(item.action_time) : '-' }}</td>
                  </tr>
                </tbody>
              </table>
              <div v-if="uploadPreview.length > 10" class="preview-note">
                외 {{ uploadPreview.length - 10 }}건 더 있음
              </div>
            </div>
          </div>
          </template>
        </div>
        <div class="modal-footer">
          <button class="cancel-button" @click="closeUploadModal">취소</button>
          <button
            class="upload-button"
            @click="processUpload"
            :disabled="!hasAvailablePeriods || !uploadForm.period_id || uploadPreview.length === 0 || isUploading"
          >
            <span v-if="isUploading"><span class="inline-spinner"></span> 업로드 중...</span>
            <span v-else>📤 일괄 등록 ({{ uploadPreview.length }}건)</span>
          </button>
        </div>
      </div>
    </div>

    <!-- ===== 단일 훈련 기록 추가 모달 ===== -->
    <div v-if="showAddRecordModal" class="modal-overlay" @click.self="closeAddRecordModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>훈련 기록 추가</h3>
          <button class="modal-close" @click="closeAddRecordModal">✕</button>
        </div>
        <form @submit.prevent="saveNewRecord">
          <div class="modal-body">
            <!-- 빈 상태: 기간 없음 -->
            <div v-if="!hasAvailablePeriods" class="empty-periods-notice">
              <div class="empty-periods-icon">📅</div>
              <div class="empty-periods-title">등록 가능한 훈련 기간이 없습니다</div>
              <div class="empty-periods-desc">먼저 훈련 기간을 생성해주세요.</div>
              <button type="button" class="empty-periods-btn" @click="goToCreatePeriod">
                + 훈련 기간 추가
              </button>
            </div>

            <template v-else>
              <!-- 훈련 기간 선택 -->
              <div class="form-group">
                <label>훈련 기간 <span class="required">*</span></label>
                <select v-model="newRecordForm.period_id" class="form-input" required>
                  <option value="">기간을 선택하세요</option>
                  <template v-for="(typeData, typeName) in periodStatus.training_types" :key="typeName">
                    <optgroup :label="typeName + ' 훈련'">
                      <option
                        v-for="period in typeData.periods"
                        :key="period.period_id"
                        :value="period.period_id"
                        :disabled="period.is_completed"
                      >
                        {{ period.period_name }} ({{ period.start_date }} ~ {{ period.end_date }}){{ period.is_completed ? ' [완료]' : '' }}
                      </option>
                    </optgroup>
                  </template>
                </select>
              </div>

              <!-- 사용자 검색 -->
              <div class="form-group">
                <label>사용자 <span class="required">*</span></label>
                <div class="search-wrapper" style="max-width: 100%;">
                  <span class="search-icon">
                    <svg width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
                  </span>
                  <input
                    type="text"
                  v-model="userSearchQuery"
                  @input="searchUsers"
                  placeholder="사용자명 또는 부서 검색..."
                  class="search-input"
                />
              </div>
              <!-- 검색 결과 드롭다운 -->
              <div v-if="showUserDropdown && userSearchResults.length > 0" class="user-dropdown">
                <div
                  v-for="user in userSearchResults"
                  :key="user.uid"
                  class="user-dropdown-item"
                  @click="selectUser(user)"
                >
                  <span class="user-dropdown-name">{{ user.username }}</span>
                  <span class="user-dropdown-dept">{{ user.department }}</span>
                  <span class="user-dropdown-email">{{ user.mail }}</span>
                </div>
              </div>
              <div v-if="userSearchLoading" style="font-size: 12px; color: #9ca3af; margin-top: 4px;">검색 중...</div>
              <!-- 선택된 사용자 표시 -->
              <div v-if="newRecordForm.user_id" class="selected-user-info">
                ✅ {{ newRecordForm.username }} ({{ newRecordForm.department }})
              </div>
            </div>

            <!-- 훈련 결과 -->
            <div class="form-group">
              <label>훈련 결과 <span class="required">*</span></label>
              <select v-model="newRecordForm.training_result" class="form-input" required>
                <option value="success">통과</option>
                <option value="fail">실패</option>
                <option value="no_response">무응답</option>
              </select>
            </div>

            <!-- 안내 문구 -->
            <div class="single-register-note">
              💡 메일유형·로그유형·시각 등 상세 정보는 등록 후 해당 행의 <strong>수정</strong> 버튼으로 보완할 수 있습니다.
            </div>
            </template>
          </div>
          <div class="modal-footer">
            <button type="button" class="cancel-button" @click="closeAddRecordModal">취소</button>
            <button
              type="submit"
              class="save-button"
              :disabled="saving || !hasAvailablePeriods || !newRecordForm.user_id || !newRecordForm.period_id"
            >
              {{ saving ? '저장 중...' : '등록' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- ===== 기록 수정 모달 ===== -->
    <div v-if="showEditModal" class="modal-overlay" @click.self="closeEditModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>훈련 기록 수정</h3>
          <button class="modal-close" @click="closeEditModal">✕</button>
        </div>
        <form @submit.prevent="saveRecord">
          <div class="modal-body">
            <!-- 완료된 기간 경고 배너 -->
            <div v-if="editingRecord.period_is_completed" class="period-completed-warning">
              <div class="warning-icon">⚠️</div>
              <div class="warning-content">
                <div class="warning-title">이 훈련 기간은 완료 처리되었습니다</div>
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
                <label>훈련 기간</label>
                <input
                  type="text"
                  :value="`${editingRecord.period_name || ''}${editingRecord.training_type ? ' (' + editingRecord.training_type + ')' : ''}`"
                  class="form-input"
                  readonly
                />
              </div>
            </div>

            <!-- 편집 가능 필드 -->
            <div class="editable-section">
              <div class="editable-section-title">✏️ 상세 정보</div>

              <div class="form-group">
                <label>훈련 결과 <span class="required">*</span></label>
                <select v-model="editingRecord.training_result" class="form-input" required>
                  <option value="success">통과</option>
                  <option value="fail">실패</option>
                  <option value="no_response">무응답</option>
                </select>
              </div>

              <div class="form-group">
                <label>훈련 대상</label>
                <input
                  type="text"
                  v-model="editingRecord.target_email"
                  class="form-input"
                  placeholder="이메일 / 전화번호 등"
                />
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label>메일유형</label>
                  <input
                    type="text"
                    v-model="editingRecord.mail_type"
                    class="form-input"
                    placeholder="예: 퇴직연금 운용"
                  />
                </div>
                <div class="form-group">
                  <label>로그유형</label>
                  <input
                    type="text"
                    v-model="editingRecord.log_type"
                    class="form-input"
                    placeholder="예: 첨부파일 열람"
                  />
                </div>
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label>발송시각</label>
                  <input
                    type="datetime-local"
                    v-model="editingRecord.email_sent_time"
                    class="form-input"
                  />
                </div>
                <div class="form-group">
                  <label>수행시각</label>
                  <input
                    type="datetime-local"
                    v-model="editingRecord.action_time"
                    class="form-input"
                  />
                </div>
              </div>
            </div>

            <!-- 점수 산정 제외 -->
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

    <!-- ===== 토스트 ===== -->
    <div v-if="toast.show" class="toast" :class="toast.type">
      {{ toast.message }}
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

// 업로드 관련
const showUploadModal = ref(false)
const uploadForm = ref({ period_id: '', file: null })
const uploadPreview = ref([])
const isUploading = ref(false)
const isDragover = ref(false)
const fileInput = ref(null)
const validationWarnings = ref([])
// 일괄 업로드 사전 검증 결과
const preflightResult = ref(null)
const runningPreflight = ref(false)
// 일괄 작업: 선택된 기록 ID Set
const selectedRecordIds = ref(new Set())
// 내보내기 상태
const exporting = ref(false)

// 필터링 관련
const selectedYear = ref(new Date().getFullYear())
const filterTrainingType = ref('')
const filterDepartment = ref('')
const filterPeriod = ref('')
const filterMailType = ref('')
const filterExclude = ref('')
const filterResult = ref('')
const searchQuery = ref('')

// 훈련 기록 관련
const trainingRecords = ref([])
const filteredRecords = ref([])
const currentPage = ref(1)
const recordsPerPage = ref(20)

// 정렬 관련
const sortField = ref('')
const sortOrder = ref('desc')

// 컬럼 필터 드롭다운
const openFilterColumn = ref(null)
const dropdownPosition = ref({})

// 수정 모달
const showEditModal = ref(false)
const editingRecord = ref({})
const saving = ref(false)

// 단일 등록 모달
const showAddRecordModal = ref(false)
const userSearchQuery = ref('')
const userSearchResults = ref([])
const showUserDropdown = ref(false)
const userSearchLoading = ref(false)
const userSearchTimeout = ref(null)
const newRecordForm = ref({
  period_id: '',
  user_id: null,
  username: '',
  department: '',
  training_result: 'fail',
})

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
  const start = (currentPage.value - 1) * recordsPerPage.value
  return filteredRecords.value.slice(start, start + recordsPerPage.value)
})

const totalPages = computed(() => {
  return Math.max(1, Math.ceil(filteredRecords.value.length / recordsPerPage.value))
})

const paginationPages = computed(() => {
  const total = totalPages.value
  const current = currentPage.value
  const pages = []

  if (total <= 7) {
    for (let i = 1; i <= total; i++) pages.push(i)
  } else {
    pages.push(1)
    if (current > 3) pages.push('...')
    const start = Math.max(2, current - 1)
    const end = Math.min(total - 1, current + 1)
    for (let i = start; i <= end; i++) pages.push(i)
    if (current < total - 2) pages.push('...')
    pages.push(total)
  }

  return pages
})

const hasActiveFilters = computed(() => {
  return filterTrainingType.value || filterDepartment.value || filterPeriod.value || filterMailType.value || filterExclude.value || filterResult.value
})

// 등록/업로드 가능한 훈련 기간이 있는지 확인 (완료되지 않은 기간)
const hasAvailablePeriods = computed(() => {
  if (!periodStatus.value.training_types) return false
  return Object.values(periodStatus.value.training_types).some(
    (td) => td.periods && td.periods.some((p) => !p.is_completed)
  )
})

// 일괄 선택 관련 computed
const selectedCount = computed(() => selectedRecordIds.value.size)
const isAllSelected = computed(() => {
  if (filteredRecords.value.length === 0) return false
  return filteredRecords.value.every((r) => selectedRecordIds.value.has(r.training_id))
})
const isPartiallySelected = computed(() => {
  const total = selectedRecordIds.value.size
  return total > 0 && !isAllSelected.value
})

// 데이터 기반 동적 필터 옵션
const uniqueDepartments = computed(() => {
  const set = new Set(trainingRecords.value.map(r => r.department).filter(Boolean))
  return [...set].sort((a, b) => a.localeCompare(b, 'ko'))
})

const uniquePeriods = computed(() => {
  const map = new Map()
  trainingRecords.value.forEach(r => {
    if (r.period_name && !map.has(r.period_name)) {
      map.set(r.period_name, r.period_id)
    }
  })
  return [...map.entries()].map(([name]) => name)
})

const uniqueMailTypes = computed(() => {
  const set = new Set(trainingRecords.value.map(r => r.mail_type).filter(Boolean))
  return [...set].sort((a, b) => a.localeCompare(b, 'ko'))
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

// ===== 라이프사이클 =====
onMounted(() => {
  loadPeriodStatus()
  loadTrainingData()
})

// 연도 변경 감시
watch(selectedYear, () => {
  loadPeriodStatus()
  loadTrainingData()
})

// ===== 메서드 =====

const displayToast = (message, type = 'success') => {
  toast.value = { show: true, message, type }
  setTimeout(() => {
    toast.value.show = false
  }, 3000)
}

const onYearChange = () => {
  // watch에서 처리
}

// ===== 기간 관리 =====

const loadPeriodStatus = async () => {
  try {
    const response = await fetch(
      `/api/phishing-training/periods/status?year=${selectedYear.value}`,
      { credentials: 'include' }
    )
    if (!response.ok) throw new Error('기간 현황 조회 실패')
    const result = await response.json()
    periodStatus.value = result
  } catch (error) {
    console.error('기간 현황 로드 실패:', error)
    displayToast('기간 현황을 불러오는데 실패했습니다.', 'error')
  }
}

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
  showPeriodModal.value = true
}

const closePeriodModal = () => {
  showPeriodModal.value = false
  editingPeriod.value = null
}

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
  showPeriodModal.value = true
}

const savePeriod = async () => {
  if (!isValidPeriodForm.value) {
    displayToast('필수 필드를 모두 입력해주세요.', 'error')
    return
  }

  if (new Date(periodForm.value.start_date) >= new Date(periodForm.value.end_date)) {
    displayToast('종료일은 시작일보다 늦어야 합니다.', 'error')
    return
  }

  saving.value = true
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
    if (!response.ok) throw new Error(result.error || result.message || '기간 저장 실패')

    displayToast(result.message || '저장되었습니다.', 'success')
    closePeriodModal()
    await loadPeriodStatus()
    await loadTrainingData()
  } catch (err) {
    console.error('기간 저장 오류:', err)
    displayToast(err.message, 'error')
  } finally {
    saving.value = false
  }
}

const deletePeriod = async (period) => {
  if (!confirm(`"${period.period_name}" 훈련 기간을 삭제하시겠습니까?`)) return

  try {
    const response = await fetch(`/api/phishing-training/periods/${period.period_id}`, {
      method: 'DELETE',
      credentials: 'include',
    })
    const result = await response.json()
    if (response.ok) {
      displayToast(result.message || '삭제되었습니다.', 'success')
      await loadPeriodStatus()
      await loadTrainingData()
    } else {
      throw new Error(result.error || result.message || '삭제 실패')
    }
  } catch (err) {
    console.error('기간 삭제 오류:', err)
    displayToast(err.message, 'error')
  }
}

const completePeriod = async (period) => {
  if (!confirm(`"${period.period_name}"을 완료 처리하시겠습니까?`)) return

  try {
    const response = await fetch(`/api/phishing-training/periods/${period.period_id}/complete`, {
      method: 'PUT',
      credentials: 'include',
    })
    const result = await response.json()
    if (!response.ok) throw new Error(result.error || '완료 처리 실패')
    displayToast('완료 처리되었습니다.', 'success')
    await loadPeriodStatus()
  } catch (err) {
    displayToast(err.message, 'error')
  }
}

const reopenPeriod = async (period) => {
  if (!confirm(`"${period.period_name}"을 재개하시겠습니까?`)) return

  try {
    const response = await fetch(`/api/phishing-training/periods/${period.period_id}/reopen`, {
      method: 'PUT',
      credentials: 'include',
    })
    const result = await response.json()
    if (!response.ok) throw new Error(result.error || '재개 처리 실패')
    displayToast('재개되었습니다.', 'success')
    await loadPeriodStatus()
  } catch (err) {
    displayToast(err.message, 'error')
  }
}

const viewPeriodStats = (period) => {
  // 상세 통계 - 추후 모달로 구현 가능
  displayToast(`${period.period_name} 상세 통계 조회`, 'success')
}

// ===== 훈련 데이터 =====

const loadTrainingData = async () => {
  try {
    loading.value = true
    const params = new URLSearchParams({
      year: selectedYear.value,
      per_page: 10000,
      page: 1,
    })

    const response = await fetch(`/api/phishing-training/records?${params}`, {
      credentials: 'include',
    })

    if (!response.ok) throw new Error('훈련 데이터 조회 실패')

    const result = await response.json()
    trainingRecords.value = result.records || []
    applyFilters()
  } catch (error) {
    console.error('훈련 데이터 로드 실패:', error)
    displayToast('훈련 데이터를 불러오는데 실패했습니다.', 'error')
    trainingRecords.value = []
    filteredRecords.value = []
  } finally {
    loading.value = false
  }
}

const searchTrainingData = () => {
  applyFilters()
}

const applyFilters = () => {
  let filtered = [...trainingRecords.value]

  // 훈련 유형 필터
  if (filterTrainingType.value) {
    filtered = filtered.filter((r) => r.training_type === filterTrainingType.value)
  }

  // 부서 필터
  if (filterDepartment.value) {
    filtered = filtered.filter((r) => r.department === filterDepartment.value)
  }

  // 훈련기간 필터
  if (filterPeriod.value) {
    filtered = filtered.filter((r) => r.period_name === filterPeriod.value)
  }

  // 메일유형 필터
  if (filterMailType.value) {
    filtered = filtered.filter((r) => r.mail_type === filterMailType.value)
  }

  // 결과 필터
  if (filterResult.value) {
    filtered = filtered.filter((r) => r.training_result === filterResult.value)
  }

  // 제외 필터
  if (filterExclude.value) {
    if (filterExclude.value === 'excluded') {
      filtered = filtered.filter((r) => r.exclude_from_scoring)
    } else if (filterExclude.value === 'included') {
      filtered = filtered.filter((r) => !r.exclude_from_scoring)
    }
  }

  // 검색어 필터
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase().trim()
    filtered = filtered.filter(
      (r) =>
        r.username?.toLowerCase().includes(query) ||
        r.department?.toLowerCase().includes(query) ||
        r.target_email?.toLowerCase().includes(query) ||
        r.mail_type?.toLowerCase().includes(query)
    )
  }

  // 정렬
  if (sortField.value) {
    filtered.sort((a, b) => {
      const aVal = a[sortField.value] || ''
      const bVal = b[sortField.value] || ''
      const cmp = String(aVal).localeCompare(String(bVal), 'ko')
      return sortOrder.value === 'asc' ? cmp : -cmp
    })
  }

  filteredRecords.value = filtered
  currentPage.value = 1
}

const clearAllFilters = () => {
  filterTrainingType.value = ''
  filterDepartment.value = ''
  filterPeriod.value = ''
  filterMailType.value = ''
  filterResult.value = ''
  filterExclude.value = ''
  searchQuery.value = ''
  applyFilters()
}

// ===== 정렬 =====

const toggleSort = (field) => {
  if (sortField.value === field) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortField.value = field
    sortOrder.value = 'asc'
  }
  applyFilters()
}

// ===== 컬럼 필터 =====

const toggleColumnFilter = (filterName, event) => {
  if (openFilterColumn.value === filterName) {
    openFilterColumn.value = null
    return
  }

  const rect = event.target.closest('th').getBoundingClientRect()
  dropdownPosition.value = {
    top: rect.bottom + 4 + 'px',
    left: Math.min(rect.left, window.innerWidth - 180) + 'px',
  }
  openFilterColumn.value = filterName
}

// ===== 업로드 =====

const openUploadModal = () => {
  uploadForm.value = { period_id: '', file: null }
  uploadPreview.value = []
  validationWarnings.value = []
  preflightResult.value = null
  showUploadModal.value = true
}

const closeUploadModal = () => {
  showUploadModal.value = false
  uploadForm.value = { period_id: '', file: null }
  uploadPreview.value = []
  validationWarnings.value = []
  preflightResult.value = null
}

/**
 * 일괄 업로드 사전 검증 (서버에 dry-run 호출)
 * - 파일 파싱 완료 + 기간 선택 시에만 실행
 * - 덮어쓰기 vs 신규 등록 vs 사용자 없음 판정
 */
const runPreflight = async () => {
  if (!uploadForm.value.period_id || uploadPreview.value.length === 0) {
    preflightResult.value = null
    return
  }

  runningPreflight.value = true
  try {
    const response = await fetch('/api/phishing-training/bulk-upload/preflight', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        period_id: uploadForm.value.period_id,
        records: uploadPreview.value.map((r) => ({
          이름: r.username,
          부서: r.department,
        })),
      }),
    })

    const result = await response.json()
    if (response.ok && result.success) {
      preflightResult.value = result
    } else {
      preflightResult.value = null
    }
  } catch (err) {
    console.warn('사전 검증 실패:', err)
    preflightResult.value = null
  } finally {
    runningPreflight.value = false
  }
}

// 기간 변경 시 preflight 재실행
watch(() => uploadForm.value.period_id, () => {
  if (showUploadModal.value && uploadPreview.value.length > 0) {
    runPreflight()
  }
})

const handleFileChange = (event) => {
  const file = event.target.files[0]
  if (file) {
    uploadForm.value.file = file
    previewFile(file)
  }
}

const handleFileDrop = (event) => {
  isDragover.value = false
  const file = event.dataTransfer.files[0]
  if (file) {
    uploadForm.value.file = file
    previewFile(file)
  }
}

const removeFile = () => {
  uploadForm.value.file = null
  uploadPreview.value = []
  validationWarnings.value = []
  if (fileInput.value) fileInput.value.value = ''
}

/**
 * 파일 파싱 (PapaParse + SheetJS)
 * CSV는 인코딩 자동 감지 (UTF-8 / EUC-KR) 지원
 */
const previewFile = async (file) => {
  uploadPreview.value = []
  validationWarnings.value = []

  // 파일 크기 제한 (10MB)
  if (file.size > 10 * 1024 * 1024) {
    displayToast('파일 크기는 10MB 이하여야 합니다.', 'error')
    removeFile()
    return
  }

  const ext = file.name.split('.').pop().toLowerCase()

  if (ext === 'csv') {
    try {
      const Papa = await import('papaparse')
      const csvText = await readFileWithAutoEncoding(file)

      Papa.default.parse(csvText, {
        header: true,
        skipEmptyLines: true,
        complete: (results) => {
          try {
            const processed = normalizePhishingFields(results.data)
            const validation = validateUploadData(processed)
            uploadPreview.value = processed
            validationWarnings.value = validation.warnings

            if (validation.errors.length > 0) {
              displayToast(`파일 검증 실패: ${validation.errors[0]}`, 'error')
              uploadPreview.value = []
              return
            }
            displayToast(`${processed.length}건의 데이터가 준비되었습니다.`, 'success')
            runPreflight()
          } catch (err) {
            console.error('CSV 데이터 처리 실패:', err)
            displayToast(`데이터 처리 실패: ${err.message}`, 'error')
            uploadPreview.value = []
          }
        },
        error: (err) => {
          console.error('CSV 파싱 실패:', err)
          displayToast('CSV 파일 파싱에 실패했습니다.', 'error')
          removeFile()
        },
      })
    } catch (err) {
      displayToast(`파일 읽기 실패: ${err.message}`, 'error')
    }
  } else if (ext === 'xlsx' || ext === 'xls') {
    const reader = new FileReader()
    reader.onload = async (e) => {
      try {
        const XLSX = await import('xlsx')
        const wb = XLSX.read(e.target.result, { type: 'array', cellDates: true, dateNF: 'yyyy-mm-dd hh:mm:ss' })
        const ws = wb.Sheets[wb.SheetNames[0]]

        if (!ws) throw new Error('엑셀 파일에 시트가 없습니다.')

        const rawData = XLSX.utils.sheet_to_json(ws, { raw: false, defval: '' })

        if (rawData.length === 0) throw new Error('엑셀 파일에 데이터가 없습니다.')

        const processed = normalizePhishingFields(rawData)
        const validation = validateUploadData(processed)
        uploadPreview.value = processed
        validationWarnings.value = validation.warnings

        if (validation.errors.length > 0) {
          displayToast(`파일 검증 실패: ${validation.errors[0]}`, 'error')
          uploadPreview.value = []
          return
        }
        displayToast(`${processed.length}건의 데이터가 준비되었습니다.`, 'success')
        runPreflight()
      } catch (err) {
        console.error('엑셀 파싱 실패:', err)
        displayToast(`엑셀 파싱 실패: ${err.message}`, 'error')
        removeFile()
      }
    }
    reader.readAsArrayBuffer(file)
  } else {
    displayToast('CSV 또는 Excel 파일을 선택해주세요.', 'error')
    removeFile()
  }
}

/**
 * CSV 인코딩 자동 감지 (UTF-8 → EUC-KR)
 */
const readFileWithAutoEncoding = async (file) => {
  const buffer = await file.arrayBuffer()
  try {
    const text = new TextDecoder('utf-8', { fatal: true }).decode(buffer)
    return text.replace(/^\uFEFF/, '')
  } catch { /* UTF-8 실패 */ }
  try {
    return new TextDecoder('euc-kr').decode(buffer)
  } catch { /* EUC-KR 실패 */ }
  return new TextDecoder('latin1').decode(buffer)
}

/**
 * 필드명 정규화 (한글 → 영문 매핑)
 * 필수: 이름, 부서, 훈련결과
 * 선택: 훈련대상, 메일유형, 로그유형, 발송시각, 수행시각 (업로드 후 수정 가능)
 */
const normalizePhishingFields = (records) => {
  const fieldMapping = {
    // 필수 - 사용자 식별
    이름: 'username', 사용자명: 'username', 사용자이름: 'username', 성명: 'username',
    username: 'username', name: 'username',
    부서: 'department', 소속: 'department', 소속부서: 'department', 팀: 'department',
    department: 'department',
    // 필수 - 훈련 결과
    훈련결과: 'training_result', 결과: 'training_result',
    training_result: 'training_result', result: 'training_result',
    // 선택 - 상세 내용 (업로드 후 수정 가능)
    훈련대상: 'target', 대상: 'target', 연락처: 'target',
    이메일: 'target', 대상이메일: 'target', 사용자이메일: 'target', 수신자: 'target',
    전화번호: 'target', 휴대폰: 'target',
    email: 'target', target_email: 'target', target: 'target',
    메일유형: 'mail_type', 메일타입: 'mail_type', 메일종류: 'mail_type', 훈련유형: 'mail_type', 시나리오: 'mail_type',
    mail_type: 'mail_type',
    로그유형: 'log_type', 액션유형: 'log_type', 행동유형: 'log_type', 로그타입: 'log_type',
    log_type: 'log_type',
    메일발송시각: 'email_sent_time', 발송시각: 'email_sent_time', 발송일시: 'email_sent_time', 메일발송일시: 'email_sent_time',
    email_sent_time: 'email_sent_time',
    수행시각: 'action_time', 액션시각: 'action_time', 클릭시각: 'action_time', 응답시각: 'action_time',
    action_time: 'action_time',
  }

  return records
    .map((record, idx) => {
      const processed = {}
      Object.keys(record).forEach((key) => {
        const normalizedKey = key.trim().replace(/\s+/g, '')
        const mappedKey = fieldMapping[normalizedKey] || fieldMapping[key] || null
        if (mappedKey) processed[mappedKey] = record[key]
      })

      // 문자열 정리
      if (processed.username) processed.username = String(processed.username).trim()
      if (processed.department) processed.department = String(processed.department).trim()
      if (processed.target) processed.target = String(processed.target).trim()
      if (processed.mail_type) processed.mail_type = String(processed.mail_type).trim()
      if (processed.log_type) processed.log_type = String(processed.log_type).trim()

      // 훈련결과 정규화 (한글 → 영문)
      processed.training_result = normalizeResult(processed.training_result, processed.log_type, processed.action_time)

      // 날짜 정리
      processed.email_sent_time = extractDateTime(processed.email_sent_time)
      processed.action_time = extractDateTime(processed.action_time)

      processed.row_number = idx + 2
      return processed
    })
    .filter((r) => r.username) // 이름 없는 행은 제외
}

/**
 * 훈련 결과 정규화 (한글 값 → DB 값)
 * 1) 명시된 값이 있으면 변환
 * 2) 없으면 로그유형 기반 자동 판정
 */
const normalizeResult = (value, logType, actionTime) => {
  if (value) {
    const v = String(value).trim().toLowerCase()
    const successAliases = ['success', 'pass', '성공', '통과', '완료', 'ok', 'o', '정상', '안전']
    const failAliases = ['fail', 'failed', '실패', '미흡', '낚임', '클릭', 'x']
    const noRespAliases = ['no_response', 'noresponse', 'none', '무응답', '미응답', '미실시', '-']

    if (successAliases.includes(v)) return 'success'
    if (failAliases.includes(v)) return 'fail'
    if (noRespAliases.includes(v)) return 'no_response'
  }

  // 명시된 값이 없으면 로그유형으로 자동 판정
  return determineTrainingResult(logType, actionTime)
}

/**
 * 날짜시간 추출
 */
const extractDateTime = (value) => {
  if (!value) return null
  try {
    if (value instanceof Date) return value.toISOString()
    const d = new Date(value)
    return isNaN(d.getTime()) ? null : d.toISOString()
  } catch {
    return null
  }
}

/**
 * 훈련 결과 판정
 */
const determineTrainingResult = (logType, actionTime) => {
  if (!logType || String(logType).trim() === '') {
    return actionTime ? 'fail' : 'no_response'
  }

  const lt = String(logType).toLowerCase()
  const failPatterns = ['첨부파일 열람', '첨부파일 실행', '링크 클릭', '스크립트 실행', '매크로 실행', '다운로드', 'attachment', 'click', 'download', 'execute']
  if (failPatterns.some((p) => lt.includes(p))) return 'fail'

  const successPatterns = ['이메일 열람', '메일 읽기', '열람만', 'view', 'read']
  if (successPatterns.some((p) => lt.includes(p))) return 'success'

  return 'fail' // 보수적 접근
}

/**
 * 업로드 데이터 검증
 */
const validateUploadData = (records) => {
  const warnings = []
  const errors = []

  if (records.length === 0) {
    errors.push('유효한 데이터가 없습니다. 필수 컬럼(이름, 부서, 훈련결과)을 확인해주세요.')
    return { warnings, errors }
  }

  // 필수: 이름
  const missingName = records.filter((r) => !r.username)
  if (missingName.length > 0) {
    warnings.push(`이름 누락 ${missingName.length}건 → 해당 행은 등록되지 않습니다.`)
  }

  // 필수: 부서
  const missingDept = records.filter((r) => !r.department)
  if (missingDept.length > 0) {
    warnings.push(`부서 누락 ${missingDept.length}건 → 해당 행은 등록되지 않습니다.`)
  }

  // 필수: 훈련결과
  const missingResult = records.filter((r) => !r.training_result || !['success', 'fail', 'no_response'].includes(r.training_result))
  if (missingResult.length > 0) {
    warnings.push(`훈련결과가 불명확한 ${missingResult.length}건 → 무응답으로 처리됩니다.`)
  }

  // 중복 체크 (이름+부서 기준 - 같은 기간에 같은 사용자 중복)
  const seen = new Set()
  let dupCount = 0
  records.forEach((r) => {
    const key = `${r.username}_${r.department}`
    if (seen.has(key)) dupCount++
    else seen.add(key)
  })
  if (dupCount > 0) {
    warnings.push(`동일 사용자 중복 ${dupCount}건 → 마지막 값으로 업데이트됩니다.`)
  }

  return { warnings, errors }
}

/**
 * 업로드 실행 (JSON 전송, 교육 관리와 동일한 방식)
 */
const processUpload = async () => {
  if (!uploadForm.value.period_id || uploadPreview.value.length === 0) {
    displayToast('기간을 선택하고 파일을 먼저 업로드해주세요.', 'error')
    return
  }

  isUploading.value = true
  try {
    // 클라이언트 파싱 결과를 JSON으로 전송 (교육 관리와 동일)
    const uploadData = {
      period_id: uploadForm.value.period_id,
      records: uploadPreview.value.map((r) => {
        // 필수 3필드는 항상 포함
        const payload = {
          이름: r.username,
          부서: r.department,
          훈련결과: r.training_result,
        }
        // 선택 필드는 값이 있을 때만 포함 (DB의 기존 값 유지용)
        if (r.target) payload['훈련대상'] = r.target
        if (r.mail_type) payload['메일유형'] = r.mail_type
        if (r.log_type) payload['로그유형'] = r.log_type
        if (r.email_sent_time) payload['발송시각'] = r.email_sent_time
        if (r.action_time) payload['수행시각'] = r.action_time
        return payload
      }),
    }

    const response = await fetch('/api/phishing-training/bulk-upload', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(uploadData),
    })

    const result = await response.json()
    if (!response.ok) throw new Error(result.error || result.message || '업로드 실패')

    const msgs = []
    if (result.success_count > 0) msgs.push(`✅ 신규: ${result.success_count}건`)
    if (result.update_count > 0) msgs.push(`🔄 업데이트: ${result.update_count}건`)
    if (result.error_count > 0) msgs.push(`❌ 오류: ${result.error_count}건`)

    displayToast(msgs.join(' / ') || '업로드 완료', result.error_count > 0 ? 'warning' : 'success')

    if (result.error_count > 0 && result.errors) {
      console.warn('업로드 오류 상세:', result.errors)
      setTimeout(() => {
        displayToast(`오류 상세: ${result.errors.slice(0, 3).join(' / ')}`, 'warning')
      }, 2000)
    }

    closeUploadModal()
    await loadPeriodStatus()
    await loadTrainingData()
  } catch (err) {
    console.error('업로드 오류:', err)
    displayToast(`업로드 실패: ${err.message}`, 'error')
  } finally {
    isUploading.value = false
  }
}

// ===== 단일 등록 =====

const openAddRecordModal = () => {
  newRecordForm.value = {
    period_id: '',
    user_id: null,
    username: '',
    department: '',
    training_result: 'fail',
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

/**
 * 빈 상태에서 기간 추가 모달로 전환
 * (단일 등록/일괄 등록 모달에서 "기간이 없을 때" 클릭)
 */
const goToCreatePeriod = () => {
  showAddRecordModal.value = false
  showUploadModal.value = false
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
      const response = await fetch(`/api/phishing-training/search-users?q=${encodeURIComponent(query)}`, {
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

const selectUser = (user) => {
  newRecordForm.value.user_id = user.uid
  newRecordForm.value.username = user.username
  newRecordForm.value.department = user.department
  userSearchQuery.value = user.username
  showUserDropdown.value = false
}

const saveNewRecord = async () => {
  if (saving.value) return
  if (!newRecordForm.value.user_id || !newRecordForm.value.period_id) {
    displayToast('훈련 기간과 사용자를 선택해주세요.', 'error')
    return
  }

  saving.value = true
  try {
    const response = await fetch('/api/phishing-training/add-record', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(newRecordForm.value),
    })

    const result = await response.json()
    if (!response.ok) throw new Error(result.error || result.message || '등록 실패')

    displayToast(result.message || '등록되었습니다.', 'success')
    closeAddRecordModal()
    await loadTrainingData()
  } catch (err) {
    console.error('기록 등록 오류:', err)
    displayToast(err.message, 'error')
  } finally {
    saving.value = false
  }
}

// ===== 템플릿 다운로드 =====

const downloadTemplate = async () => {
  try {
    const response = await fetch('/api/phishing-training/template/download', {
      credentials: 'include',
    })

    if (!response.ok) throw new Error('템플릿 다운로드 실패')

    const text = await response.text()
    const bom = '\uFEFF'
    const blob = new Blob([bom + text], { type: 'text/csv;charset=utf-8;' })

    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = '모의훈련_업로드_템플릿.csv'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)

    displayToast('템플릿이 다운로드되었습니다.', 'success')
  } catch (err) {
    displayToast(err.message, 'error')
  }
}

// ===== 새로고침 =====

const refreshData = async () => {
  await loadPeriodStatus()
  await loadTrainingData()
  displayToast('데이터를 새로고침했습니다.', 'success')
}

// ===== 내보내기 =====

/**
 * 훈련 데이터 CSV 내보내기 (현재 선택된 연도 전체)
 */
const exportData = async () => {
  if (exporting.value) return
  exporting.value = true

  try {
    const url = `/api/phishing-training/export?year=${selectedYear.value}&format=csv`
    const response = await fetch(url, { credentials: 'include' })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: '내보내기 실패' }))
      throw new Error(errorData.error || '내보내기 실패')
    }

    const blob = await response.blob()
    const downloadUrl = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = downloadUrl
    a.download = `피싱훈련_${selectedYear.value}년.csv`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(downloadUrl)

    displayToast(`${selectedYear.value}년 훈련 데이터가 다운로드되었습니다.`, 'success')
  } catch (err) {
    console.error('내보내기 오류:', err)
    displayToast(err.message || '내보내기 실패', 'error')
  } finally {
    exporting.value = false
  }
}

// ===== 일괄 선택/작업 =====

const toggleSelectRecord = (recordId) => {
  const newSet = new Set(selectedRecordIds.value)
  if (newSet.has(recordId)) {
    newSet.delete(recordId)
  } else {
    newSet.add(recordId)
  }
  selectedRecordIds.value = newSet
}

const toggleSelectAll = () => {
  if (isAllSelected.value) {
    selectedRecordIds.value = new Set()
  } else {
    selectedRecordIds.value = new Set(filteredRecords.value.map((r) => r.training_id))
  }
}

const clearSelection = () => {
  selectedRecordIds.value = new Set()
}

/**
 * 선택된 기록 일괄 삭제
 */
const bulkDelete = async () => {
  if (selectedRecordIds.value.size === 0) return
  const count = selectedRecordIds.value.size
  if (!confirm(`선택된 ${count}건의 훈련 기록을 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.`)) return

  const ids = [...selectedRecordIds.value]
  let success = 0
  let fail = 0

  try {
    const results = await Promise.allSettled(
      ids.map((id) =>
        fetch(`/api/phishing-training/records/${id}`, {
          method: 'DELETE',
          credentials: 'include',
        }).then((r) => (r.ok ? r.json() : Promise.reject(r)))
      )
    )

    results.forEach((r) => {
      if (r.status === 'fulfilled') success++
      else fail++
    })

    if (success > 0 && fail === 0) {
      displayToast(`${success}건 삭제 완료`, 'success')
    } else if (success > 0 && fail > 0) {
      displayToast(`${success}건 성공 / ${fail}건 실패`, 'warning')
    } else {
      displayToast(`일괄 삭제 실패 (${fail}건)`, 'error')
    }

    clearSelection()
    await loadTrainingData()
  } catch (err) {
    console.error('일괄 삭제 오류:', err)
    displayToast(err.message || '일괄 삭제 실패', 'error')
  }
}

/**
 * 선택된 기록의 점수 산정 제외/포함 일괄 토글
 */
const bulkToggleExclude = async (exclude) => {
  if (selectedRecordIds.value.size === 0) return
  const count = selectedRecordIds.value.size
  const actionText = exclude ? '제외' : '포함'

  if (!confirm(`선택된 ${count}건을 점수 산정에서 ${actionText} 처리하시겠습니까?`)) return

  const ids = [...selectedRecordIds.value]
  let success = 0
  let fail = 0

  try {
    const results = await Promise.allSettled(
      ids.map((id) =>
        fetch(`/api/phishing-training/records/${id}/exclude`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({
            exclude: exclude,
            reason: exclude ? '관리자 일괄 제외 처리' : '',
          }),
        }).then((r) => (r.ok ? r.json() : Promise.reject(r)))
      )
    )

    results.forEach((r) => {
      if (r.status === 'fulfilled') success++
      else fail++
    })

    if (success > 0 && fail === 0) {
      displayToast(`${success}건 ${actionText} 처리 완료`, 'success')
    } else if (success > 0 && fail > 0) {
      displayToast(`${success}건 성공 / ${fail}건 실패`, 'warning')
    } else {
      displayToast(`일괄 ${actionText} 실패`, 'error')
    }

    clearSelection()
    await loadTrainingData()
  } catch (err) {
    console.error(`일괄 ${actionText} 오류:`, err)
    displayToast(err.message || `일괄 ${actionText} 실패`, 'error')
  }
}

// 필터 변경 시 선택 해제 (다른 데이터에 적용되지 않도록)
watch(() => [selectedYear.value, filterTrainingType.value, filterPeriod.value], () => {
  clearSelection()
})

// ===== 기록 수정/삭제 =====

/**
 * ISO 문자열 / Date → datetime-local 포맷 (yyyy-MM-ddTHH:mm)
 */
const toDatetimeLocalFormat = (value) => {
  if (!value) return ''
  try {
    const d = new Date(value)
    if (isNaN(d.getTime())) return ''
    // 로컬 타임존 기준 yyyy-MM-ddTHH:mm
    const pad = (n) => String(n).padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
  } catch {
    return ''
  }
}

/**
 * datetime-local → ISO 문자열 (백엔드 전송용)
 */
const fromDatetimeLocalFormat = (value) => {
  if (!value) return null
  try {
    const d = new Date(value)
    if (isNaN(d.getTime())) return null
    return d.toISOString()
  } catch {
    return null
  }
}

const editRecord = (record) => {
  editingRecord.value = {
    ...record,
    // datetime-local 형식으로 변환
    email_sent_time: toDatetimeLocalFormat(record.email_sent_time),
    action_time: toDatetimeLocalFormat(record.action_time),
    // null이면 빈 문자열로
    target_email: record.target_email || '',
    mail_type: record.mail_type || '',
    log_type: record.log_type || '',
    exclude_reason: record.exclude_reason || '',
    notes: record.notes || '',
    exclude_from_scoring: !!record.exclude_from_scoring,
    period_is_completed: !!record.period_is_completed,
  }
  showEditModal.value = true
}

const closeEditModal = () => {
  showEditModal.value = false
  editingRecord.value = {}
}

const saveRecord = async () => {
  if (saving.value) return
  saving.value = true

  try {
    // datetime-local → ISO 변환 후 전송
    const payload = {
      training_result: editingRecord.value.training_result,
      target_email: editingRecord.value.target_email || null,
      mail_type: editingRecord.value.mail_type || null,
      log_type: editingRecord.value.log_type || null,
      email_sent_time: fromDatetimeLocalFormat(editingRecord.value.email_sent_time),
      action_time: fromDatetimeLocalFormat(editingRecord.value.action_time),
      exclude_from_scoring: !!editingRecord.value.exclude_from_scoring,
      exclude_reason: editingRecord.value.exclude_from_scoring
        ? (editingRecord.value.exclude_reason || '')
        : '',
      notes: editingRecord.value.notes || '',
    }

    const response = await fetch(`/api/phishing-training/records/${editingRecord.value.training_id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(payload),
    })

    const result = await response.json()
    if (!response.ok) throw new Error(result.error || result.message || '수정 실패')

    displayToast(result.message || '수정되었습니다.', 'success')
    closeEditModal()
    await loadTrainingData()
  } catch (err) {
    console.error('기록 수정 오류:', err)
    displayToast(err.message, 'error')
  } finally {
    saving.value = false
  }
}

const deleteRecord = async (record) => {
  if (!confirm('이 훈련 기록을 삭제하시겠습니까?')) return

  try {
    const response = await fetch(`/api/phishing-training/records/${record.training_id}`, {
      method: 'DELETE',
      credentials: 'include',
    })

    const result = await response.json()
    if (!response.ok) throw new Error(result.error || result.message || '삭제 실패')

    displayToast(result.message || '삭제되었습니다.', 'success')
    await loadTrainingData()
  } catch (err) {
    console.error('기록 삭제 오류:', err)
    displayToast(err.message, 'error')
  }
}

const toggleExclude = async (record) => {
  try {
    const newValue = !record.exclude_from_scoring
    const response = await fetch(`/api/phishing-training/records/${record.training_id}/exclude`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        exclude: newValue,
        reason: newValue ? '관리자가 제외 처리' : '',
      }),
    })

    const result = await response.json()
    if (!response.ok) throw new Error(result.error || '제외 설정 실패')

    record.exclude_from_scoring = newValue
    displayToast(newValue ? '점수 산정에서 제외되었습니다.' : '점수 산정에 포함되었습니다.', 'success')
  } catch (err) {
    displayToast(err.message, 'error')
  }
}

// ===== 유틸리티 =====

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  try {
    const d = new Date(dateStr)
    if (isNaN(d.getTime())) return dateStr
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  } catch {
    return dateStr
  }
}

const formatRate = (rate) => {
  if (rate === null || rate === undefined) return '0%'
  return `${Number(rate).toFixed(1)}%`
}

const getResultText = (result) => {
  const map = { success: '통과', fail: '실패', no_response: '무응답' }
  return map[result] || result || '-'
}

const getResultFilterLabel = (result) => {
  const map = { success: '성공(통과)', fail: '실패', no_response: '무응답' }
  return map[result] || result
}

const getPeriodStatusClass = (period) => {
  if (period.is_completed) return 'card-status-completed'
  const now = new Date()
  const start = new Date(period.start_date)
  const end = new Date(period.end_date)
  if (now < start) return 'card-status-not-started'
  if (now > end) return 'card-status-expired'
  return 'card-status-in-progress'
}

const getPeriodStatusText = (period) => {
  if (period.is_completed) return '완료'
  const now = new Date()
  const start = new Date(period.start_date)
  const end = new Date(period.end_date)
  if (now < start) return '예정'
  if (now > end) return '기간만료'
  return '진행중'
}
</script>

<style scoped>
@import '../styles/AdminPhishingTrainingManagement.css';
</style>