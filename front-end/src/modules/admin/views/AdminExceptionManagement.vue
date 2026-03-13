<!-- views/admin/AdminExceptionManagement.vue - Template -->
<template>
  <div class="admin-exception-management">
    <div class="admin-header">
      <h1>제외 설정 관리</h1>
      <p>사용자별/부서별 보안 감사 항목 제외 설정을 관리합니다.</p>
      <div class="admin-nav">
        <RouterLink to="/admin/training" class="nav-item">모의훈련 관리</RouterLink>
        <RouterLink to="/admin/manual-check" class="nav-item">수시 점검 관리</RouterLink>
        <RouterLink to="/admin/exceptions" class="nav-item active">제외 설정</RouterLink>
      </div>
    </div>

    <!-- 탭 네비게이션 -->
    <div class="tabs-container">
      <div class="tabs-header">
        <button
          @click="activeTab = 'user'"
          class="tab-button"
          :class="{ active: activeTab === 'user' }"
        >
          <svg width="20" height="20" fill="currentColor" viewBox="0 0 16 16">
            <path
              d="M8 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6zm2-3a2 2 0 1 1-4 0 2 2 0 0 1 4 0zm4 8c0 1-1 1-1 1H3s-1 0-1-1 1-4 6-4 6 3 6 4zm-1-.004c-.001-.246-.154-.986-.832-1.664C11.516 10.68 10.289 10 8 10c-2.29 0-3.516.68-4.168 1.332-.678.678-.83 1.418-.832 1.664h10z"
            />
          </svg>
          사용자별 제외 설정
          <span class="tab-count">{{ userExceptions.length }}개</span>
        </button>

        <button
          @click="activeTab = 'department'"
          class="tab-button"
          :class="{ active: activeTab === 'department' }"
        >
          <svg width="20" height="20" fill="currentColor" viewBox="0 0 16 16">
            <path
              d="m8.186 1.113a.5.5 0 0 0-.372 0L1.846 3.5l2.404.961L10.404 2l-2.218-.887zm3.564 1.426L5.596 5 8 5.961 14.154 3.5l-2.404-.961zm3.25 1.7-6.5 2.6v7.922l6.5-2.6V4.24zM7.5 14.762V6.838L1 4.239v7.923l6.5 2.6zM7.443.184a1.5 1.5 0 0 1 1.114 0l7.129 2.852A.5.5 0 0 1 16 3.5v8.662a1 1 0 0 1-.629.928l-7.185 2.874a.5.5 0 0 1-.372 0L.629 13.09a1 1 0 0 1-.629-.928V3.5a.5.5 0 0 1 .314-.464L7.443.184z"
            />
          </svg>
          부서별 제외 설정
          <span class="tab-count">{{ departmentExceptions.length }}개</span>
        </button>

        <button
          @click="activeTab = 'summary'"
          class="tab-button"
          :class="{ active: activeTab === 'summary' }"
        >
          <svg width="20" height="20" fill="currentColor" viewBox="0 0 16 16">
            <path
              d="M1 2.5A1.5 1.5 0 0 1 2.5 1h3A1.5 1.5 0 0 1 7 2.5v3A1.5 1.5 0 0 1 5.5 7h-3A1.5 1.5 0 0 1 1 5.5v-3zM2.5 2a.5.5 0 0 0-.5.5v3a.5.5 0 0 0 .5.5h3a.5.5 0 0 0 .5-.5v-3a.5.5 0 0 0-.5-.5h-3zm6.5.5A1.5 1.5 0 0 1 10.5 1h3A1.5 1.5 0 0 1 15 2.5v3A1.5 1.5 0 0 1 13.5 7h-3A1.5 1.5 0 0 1 9 5.5v-3zm1.5-.5a.5.5 0 0 0-.5.5v3a.5.5 0 0 0 .5.5h3a.5.5 0 0 0 .5-.5v-3a.5.5 0 0 0-.5-.5h-3zM1 10.5A1.5 1.5 0 0 1 2.5 9h3A1.5 1.5 0 0 1 7 10.5v3A1.5 1.5 0 0 1 5.5 15h-3A1.5 1.5 0 0 1 1 13.5v-3zm1.5-.5a.5.5 0 0 0-.5.5v3a.5.5 0 0 0 .5.5h3a.5.5 0 0 0 .5-.5v-3a.5.5 0 0 0-.5-.5h-3zm6.5.5A1.5 1.5 0 0 1 10.5 9h3a1.5 1.5 0 0 1 1.5 1.5v3a1.5 1.5 0 0 1-1.5 1.5h-3A1.5 1.5 0 0 1 9 13.5v-3zm1.5-.5a.5.5 0 0 0-.5.5v3a.5.5 0 0 0 .5.5h3a.5.5 0 0 0 .5-.5v-3a.5.5 0 0 0-.5-.5h-3z"
            />
          </svg>
          요약 통계
        </button>
      </div>
    </div>

    <!-- 액션 바 - 검색 기능 개선 -->
    <div v-if="activeTab !== 'summary'" class="action-bar">
      <div class="filters">
        <div class="search-group">
          <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16" class="search-icon">
            <path
              d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001c.03.04.062.078.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1.007 1.007 0 0 0-.115-.1zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0z"
            />
          </svg>
          <input
            type="text"
            placeholder="사용자명, ID, 이메일로 검색..."
            v-model="searchQuery"
            class="search-input"
          />
        </div>

        <select v-model="filterDepartment" class="filter-select">
          <option value="">모든 부서</option>
          <option v-for="dept in departments" :key="dept" :value="dept">{{ dept }}</option>
        </select>

        <select v-model="filterCategory" class="filter-select">
          <option value="">모든 카테고리</option>
          <option value="정보보안 감사">정보보안 감사</option>
          <option value="정보보호 교육">정보보호 교육</option>
          <option value="악성메일 모의훈련">악성메일 모의훈련</option>
        </select>
      </div>

      <div class="action-buttons">
        <button @click="showAddModal = true" class="primary-button">
          <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
            <path
              d="M8 2a.5.5 0 0 1 .5.5v5h5a.5.5 0 0 1 0 1h-5v5a.5.5 0 0 1-1 0v-5h-5a.5.5 0 0 1 0-1h5v-5A.5.5 0 0 1 8 2z"
            />
          </svg>
          제외 설정 추가
        </button>

        <button @click="handleExport('csv')" class="secondary-button">
          <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
            <path
              d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"
            />
            <path
              d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"
            />
          </svg>
          CSV 내보내기
        </button>
      </div>
    </div>

    <!-- 컨텐츠 영역 -->
    <div class="content-area">
      <!-- 로딩 상태 -->
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner"></div>
        <p>데이터를 불러오는 중...</p>
      </div>

      <!-- 사용자별 제외 설정 테이블 -->
      <div v-else-if="activeTab === 'user'" class="table-container">
        <table class="exception-table">
          <thead>
            <tr>
              <th>사용자</th>
              <th>부서</th>
              <th>점검 항목</th>
              <th>제외 사유</th>
              <th>제외 유형</th>
              <th>기간</th>
              <th>생성자</th>
              <th>액션</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="filteredUserExceptions.length === 0">
              <td colspan="8" class="no-data">사용자별 제외 설정이 없습니다.</td>
            </tr>
            <tr
              v-for="exc in filteredUserExceptions"
              :key="`${exc.user_id}-${exc.item_id}`"
              class="table-row"
            >
              <td>
                <div class="user-info">
                  <div class="user-name">{{ exc.username }}</div>
                  <div class="user-id">{{ exc.user_login_id }}</div>
                </div>
              </td>
              <td>{{ exc.department }}</td>
              <td>
                <div class="item-info">
                  <div class="item-name">{{ exc.item_name }}</div>
                  <div class="item-category">{{ exc.category }}</div>
                </div>
              </td>
              <td>
                <div class="exclude-reason" :title="exc.exclude_reason">
                  {{ truncateText(exc.exclude_reason, 50) }}
                </div>
              </td>
              <td>
                <div class="exclude-type" :class="exc.exclude_type">
                  <span class="type-icon">
                    {{ exc.exclude_type === 'permanent' ? '🔒' : '⏰' }}
                  </span>
                  {{ exc.exclude_type === 'permanent' ? '영구' : '임시' }}
                </div>
              </td>
              <td>
                {{
                  exc.exclude_type === 'temporary' && exc.start_date && exc.end_date
                    ? `${exc.start_date} ~ ${exc.end_date}`
                    : '-'
                }}
              </td>
              <td>{{ exc.created_by }}</td>
              <td>
                <div class="action-buttons">
                  <button
                    @click="handleDeleteException('user', exc.user_id, exc.item_id)"
                    class="delete-button"
                    title="삭제"
                  >
                    <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
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

      <!-- 부서별 제외 설정 테이블 -->
      <div v-else-if="activeTab === 'department'" class="table-container">
        <table class="exception-table">
          <thead>
            <tr>
              <th>부서</th>
              <th>점검 항목</th>
              <th>제외 사유</th>
              <th>제외 유형</th>
              <th>기간</th>
              <th>영향받는 사용자</th>
              <th>생성자</th>
              <th>액션</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="filteredDepartmentExceptions.length === 0">
              <td colspan="8" class="no-data">부서별 제외 설정이 없습니다.</td>
            </tr>
            <tr
              v-for="exc in filteredDepartmentExceptions"
              :key="`${exc.department}-${exc.item_id}`"
              class="table-row"
            >
              <td class="department-name">{{ exc.department }}</td>
              <td>
                <div class="item-info">
                  <div class="item-name">{{ exc.item_name }}</div>
                  <div class="item-category">{{ exc.category }}</div>
                </div>
              </td>
              <td>
                <div class="exclude-reason" :title="exc.exclude_reason">
                  {{ truncateText(exc.exclude_reason, 50) }}
                </div>
              </td>
              <td>
                <div class="exclude-type" :class="exc.exclude_type">
                  <span class="type-icon">
                    {{ exc.exclude_type === 'permanent' ? '🔒' : '⏰' }}
                  </span>
                  {{ exc.exclude_type === 'permanent' ? '영구' : '임시' }}
                </div>
              </td>
              <td>
                {{
                  exc.exclude_type === 'temporary' && exc.start_date && exc.end_date
                    ? `${exc.start_date} ~ ${exc.end_date}`
                    : '-'
                }}
              </td>
              <td>
                <span class="affected-users">{{ exc.affected_users }}명</span>
              </td>
              <td>{{ exc.created_by }}</td>
              <td>
                <div class="action-buttons">
                  <button
                    @click="handleDeleteException('department', exc.department, exc.item_id)"
                    class="delete-button"
                    title="삭제"
                  >
                    <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
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

      <!-- 요약 통계 -->
      <div v-else-if="activeTab === 'summary' && summary" class="summary-container">
        <div class="summary-grid">
          <!-- 사용자별 제외 설정 통계 -->
          <div class="summary-card user-stats">
            <h3>사용자별 제외 설정</h3>
            <div class="stats-list">
              <div class="stat-item">
                <span class="stat-label">총 설정 수:</span>
                <span class="stat-value">{{
                  summary.user_exceptions?.total_user_exceptions || 0
                }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">영구 제외:</span>
                <span class="stat-value">{{
                  summary.user_exceptions?.permanent_user_exceptions || 0
                }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">임시 제외:</span>
                <span class="stat-value">{{
                  summary.user_exceptions?.temporary_user_exceptions || 0
                }}</span>
              </div>
            </div>
          </div>

          <!-- 부서별 제외 설정 통계 -->
          <div class="summary-card dept-stats">
            <h3>부서별 제외 설정</h3>
            <div class="stats-list">
              <div class="stat-item">
                <span class="stat-label">총 설정 수:</span>
                <span class="stat-value">{{
                  summary.department_exceptions?.total_dept_exceptions || 0
                }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">영구 제외:</span>
                <span class="stat-value">{{
                  summary.department_exceptions?.permanent_dept_exceptions || 0
                }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">임시 제외:</span>
                <span class="stat-value">{{
                  summary.department_exceptions?.temporary_dept_exceptions || 0
                }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">영향받는 부서:</span>
                <span class="stat-value">{{
                  summary.department_exceptions?.affected_departments || 0
                }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 가장 많이 제외된 항목들 -->
        <div
          v-if="summary.top_excluded_items && summary.top_excluded_items.length > 0"
          class="top-items-card"
        >
          <h3>가장 많이 제외된 항목</h3>
          <div class="top-items-list">
            <div v-for="(item, index) in summary.top_excluded_items" :key="index" class="top-item">
              <div class="item-info">
                <span class="item-name">{{ item.item_name }}</span>
                <span class="item-category">({{ item.category }})</span>
              </div>
              <span class="exception-count">{{ item.exception_count }}건</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 제외 설정 추가 모달 - 개선된 버전 -->
    <div v-if="showAddModal" class="modal-overlay" @click="closeAddModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>제외 설정 추가</h3>
          <button @click="closeAddModal" class="close-button">×</button>
        </div>

        <div class="modal-body">
          <form @submit.prevent="handleAddException" class="exception-form">
            <!-- 제외 유형 선택 -->
            <div class="form-group">
              <label>제외 유형:</label>
              <div class="radio-group">
                <label class="radio-option">
                  <input type="radio" v-model="formData.type" value="user" />
                  <span>사용자별</span>
                </label>
                <label class="radio-option">
                  <input type="radio" v-model="formData.type" value="department" />
                  <span>부서별</span>
                </label>
              </div>
            </div>

            <!-- 사용자 검색 (사용자별인 경우) -->
            <div v-if="formData.type === 'user'" class="form-group">
              <label>사용자 검색:</label>
              <div class="user-search-container">
                <input
                  type="text"
                  v-model="userSearchQuery"
                  @input="searchUsers"
                  placeholder="사용자명, ID, 이메일로 검색..."
                  class="form-input"
                />
                <div v-if="searchedUsers.length > 0" class="user-dropdown">
                  <div
                    v-for="user in searchedUsers"
                    :key="user.uid"
                    @click="selectUser(user)"
                    class="user-option"
                    :class="{ selected: formData.user_id === user.uid }"
                  >
                    <div class="user-info">
                      <div class="user-name">{{ user.username }}</div>
                      <div class="user-details">{{ user.user_id }} - {{ user.department }}</div>
                    </div>
                  </div>
                </div>
                <div v-if="selectedUser" class="selected-user">
                  <span
                    >선택된 사용자: {{ selectedUser.username }} ({{ selectedUser.user_id }})</span
                  >
                  <button type="button" @click="clearSelectedUser" class="clear-button">×</button>
                </div>
              </div>
            </div>

            <!-- 부서 선택 (부서별인 경우) -->
            <div v-if="formData.type === 'department'" class="form-group">
              <label>부서:</label>
              <select v-model="formData.department" required class="form-select">
                <option value="">부서를 선택하세요</option>
                <option v-for="dept in departments" :key="dept" :value="dept">
                  {{ dept }}
                </option>
              </select>
            </div>

            <!-- 점검 항목 선택 - 개선된 버전 -->
            <div class="form-group">
              <label>점검 카테고리:</label>
              <select
                v-model="formData.item_category"
                @change="onCategoryChange"
                required
                class="form-select"
              >
                <option value="">카테고리를 선택하세요</option>
                <option value="정보보안 감사">정보보안 감사</option>
                <option value="정보보호 교육">정보보호 교육</option>
                <option value="악성메일 모의훈련">악성메일 모의훈련</option>
              </select>
            </div>

            <!-- 세부 항목 선택 -->

            <!-- 세부 항목 선택 -->
            <div v-if="formData.item_category" class="form-group">
              <label>세부 항목:</label>
              <select v-model="formData.item_type" required class="form-select">
                <option value="">항목을 선택하세요</option>

                <!-- 정보보안 감사 항목 (실제 데이터 구조에 맞게 수정) -->
                <template v-if="formData.item_category === '정보보안 감사'">
                  <optgroup
                    v-for="(items, categoryName) in auditItemsByCategory"
                    :key="categoryName"
                    :label="categoryName"
                  >
                    <option
                      v-for="item in items"
                      :key="item.item_id"
                      :value="item.item_id"
                      :data-name="item.item_name"
                    >
                      {{ item.item_name }} ({{
                        item.check_type === 'daily' ? '정기점검' : '수시점검'
                      }})
                    </option>
                  </optgroup>
                </template>

                <!-- 정보보호 교육 항목 -->
                <template v-if="formData.item_category === '정보보호 교육'">
                  <optgroup
                    v-for="(items, year) in educationItems"
                    :key="year"
                    :label="`${year}년`"
                  >
                    <option
                      v-for="item in items"
                      :key="item.item_id"
                      :value="item.item_id"
                      :data-name="item.item_name"
                    >
                      {{ item.item_name }}
                    </option>
                  </optgroup>
                </template>

                <!-- 악성메일 모의훈련 항목 -->
                <template v-if="formData.item_category === '악성메일 모의훈련'">
                  <optgroup v-for="(items, year) in trainingItems" :key="year" :label="`${year}년`">
                    <option
                      v-for="item in items"
                      :key="item.item_id"
                      :value="item.item_id"
                      :data-name="item.item_name"
                    >
                      {{ item.item_name }}
                    </option>
                  </optgroup>
                </template>
              </select>
            </div>

            <!-- 나머지 폼 필드들은 기존과 동일 -->
            <div class="form-group">
              <label>제외 사유:</label>
              <textarea
                v-model="formData.exclude_reason"
                required
                class="form-textarea"
                rows="3"
                placeholder="제외 사유를 입력하세요..."
              ></textarea>
            </div>

            <!-- 제외 기간 유형 -->
            <div class="form-group">
              <label>제외 기간:</label>
              <div class="radio-group">
                <label class="radio-option">
                  <input type="radio" v-model="formData.exclude_type" value="permanent" />
                  <span>영구 제외</span>
                </label>
                <label class="radio-option">
                  <input type="radio" v-model="formData.exclude_type" value="temporary" />
                  <span>임시 제외</span>
                </label>
              </div>
            </div>

            <!-- 임시 제외 기간 설정 -->
            <div v-if="formData.exclude_type === 'temporary'" class="form-row">
              <div class="form-group">
                <label>시작일:</label>
                <input type="date" v-model="formData.start_date" required class="form-input" />
              </div>
              <div class="form-group">
                <label>종료일:</label>
                <input type="date" v-model="formData.end_date" required class="form-input" />
              </div>
            </div>
          </form>
        </div>

        <div class="modal-footer">
          <button @click="closeAddModal" class="cancel-button">취소</button>
          <button @click="handleAddException" :disabled="!isFormValid" class="save-button">
            추가
          </button>
        </div>
      </div>
    </div>

    <!-- 토스트 메시지 -->
    <div v-if="showToast" :class="['toast-message', toastType]">
      {{ toastMessage }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { RouterLink } from 'vue-router'

// 반응형 데이터
const loading = ref(false)
const activeTab = ref('user')
const userExceptions = ref([])
const departmentExceptions = ref([])
const summary = ref(null)

// 폼 데이터 - 개선된 버전
const departments = ref([])
const availableItems = ref({}) // 카테고리별 항목들
const searchedUsers = ref([]) // 검색된 사용자 목록
const selectedUser = ref(null) // 선택된 사용자

// 모달 상태
const showAddModal = ref(false)

// 폼 상태 - 개선된 버전
const formData = ref({
  type: 'user',
  user_id: '',
  department: '',
  item_category: '', // 새로 추가: 카테고리 선택
  item_type: '', // 변경: item_id에서 item_type으로
  item_name: '', // 새로 추가: 항목명 저장
  exclude_reason: '',
  exclude_type: 'permanent',
  start_date: '',
  end_date: '',
})

// 검색 관련
const userSearchQuery = ref('')
const searchQuery = ref('')
const filterDepartment = ref('')
const filterCategory = ref('') // 새로 추가: 카테고리 필터

// 토스트 메시지
const showToast = ref(false)
const toastMessage = ref('')
const toastType = ref('success')

// 모든 감사 항목들을 하나의 배열로 (기존 auditItemCategories 대체)
const auditItemCategories = computed(() => {
  const categories = []

  Object.keys(availableItems.value).forEach((categoryName) => {
    if (categoryName !== '정보보호 교육' && categoryName !== '악성메일 모의훈련') {
      const items = availableItems.value[categoryName] || []
      if (items.length > 0) {
        categories.push({
          name: categoryName,
          items: items,
        })
      }
    }
  })

  return categories
})

// 또는 더 간단하게 모든 감사 관련 항목들을 하나로 묶기
const allAuditItems = computed(() => {
  const items = []

  // 정보보호 교육과 악성메일 모의훈련을 제외한 모든 항목들
  Object.keys(availableItems.value).forEach((categoryName) => {
    if (categoryName !== '정보보호 교육' && categoryName !== '악성메일 모의훈련') {
      const categoryItems = availableItems.value[categoryName] || []
      items.push(...categoryItems)
    }
  })

  return items
})

// 카테고리별로 분류된 감사 항목들 (정보보호 교육과 악성메일 모의훈련 제외)
const auditItemsByCategory = computed(() => {
  const result = {}

  Object.keys(availableItems.value).forEach((categoryName) => {
    if (categoryName !== '정보보호 교육' && categoryName !== '악성메일 모의훈련') {
      result[categoryName] = availableItems.value[categoryName] || []
    }
  })

  return result
})

// 교육 항목들 (기존 코드 유지)
const educationItems = computed(() => {
  const baseItems = availableItems.value['정보보호 교육'] || []
  // 연도별로 그룹화
  const groupedByYear = {}

  baseItems.forEach((item) => {
    const year = item.year || new Date().getFullYear()
    if (!groupedByYear[year]) {
      groupedByYear[year] = []
    }
    groupedByYear[year].push(item)
  })

  return groupedByYear
})

// 훈련 항목들 (기존 코드 유지)
const trainingItems = computed(() => {
  const baseItems = availableItems.value['악성메일 모의훈련'] || []
  // 연도별로 그룹화
  const groupedByYear = {}

  baseItems.forEach((item) => {
    const year = item.year || new Date().getFullYear()
    if (!groupedByYear[year]) {
      groupedByYear[year] = []
    }
    groupedByYear[year].push(item)
  })

  return groupedByYear
})

const filteredUserExceptions = computed(() => {
  return userExceptions.value.filter((exc) => {
    const matchesSearch =
      !searchQuery.value ||
      exc.username.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      exc.user_login_id.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      exc.item_name.toLowerCase().includes(searchQuery.value.toLowerCase())

    const matchesDept = !filterDepartment.value || exc.department === filterDepartment.value
    const matchesCategory = !filterCategory.value || exc.item_category === filterCategory.value

    return matchesSearch && matchesDept && matchesCategory
  })
})

const filteredDepartmentExceptions = computed(() => {
  return departmentExceptions.value.filter((exc) => {
    const matchesSearch =
      !searchQuery.value ||
      exc.department.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      exc.item_name.toLowerCase().includes(searchQuery.value.toLowerCase())

    const matchesDept = !filterDepartment.value || exc.department === filterDepartment.value
    const matchesCategory = !filterCategory.value || exc.item_category === filterCategory.value

    return matchesSearch && matchesDept && matchesCategory
  })
})

const isFormValid = computed(() => {
  const basicValid = formData.value.exclude_reason && formData.value.item_type

  if (formData.value.type === 'user') {
    return basicValid && formData.value.user_id
  } else {
    return basicValid && formData.value.department
  }
})

// 메서드 - 개선된 버전
const loadInitialData = async () => {
  try {
    const [deptsRes, itemsRes] = await Promise.all([
      fetch('/api/exceptions/departments', { credentials: 'include' }),
      fetch('/api/exceptions/available-items', { credentials: 'include' }),
    ])

    if (deptsRes.ok) {
      departments.value = await deptsRes.json()
    }
    if (itemsRes.ok) {
      availableItems.value = await itemsRes.json()
      console.log(availableItems.value)
    }
  } catch (error) {
    showToastMessage('초기 데이터 로드 실패: ' + error.message, 'error')
  }
}

const searchUsers = async () => {
  if (userSearchQuery.value.length < 2) {
    searchedUsers.value = []
    return
  }

  try {
    const response = await fetch(
      `/api/exceptions/search-users?q=${encodeURIComponent(userSearchQuery.value)}&limit=20`,
      { credentials: 'include' },
    )

    if (response.ok) {
      searchedUsers.value = await response.json()
    }
  } catch (error) {
    console.error('사용자 검색 실패:', error)
  }
}

const selectUser = (user) => {
  selectedUser.value = user
  formData.value.user_id = user.uid
  userSearchQuery.value = user.username
  searchedUsers.value = []
}

const clearSelectedUser = () => {
  selectedUser.value = null
  formData.value.user_id = ''
  userSearchQuery.value = ''
  searchedUsers.value = []
}

const onCategoryChange = () => {
  // 카테고리 변경 시 세부 항목 초기화
  formData.value.item_type = ''
  formData.value.item_name = ''
}

const loadUserExceptions = async () => {
  loading.value = true
  try {
    const response = await fetch('/api/exceptions/user-exceptions', {
      credentials: 'include',
    })

    if (response.ok) {
      userExceptions.value = await response.json()
    } else {
      throw new Error('사용자 제외 설정 로드 실패')
    }
  } catch (error) {
    showToastMessage('사용자 제외 설정 로드 실패', 'error')
  } finally {
    loading.value = false
  }
}

const loadDepartmentExceptions = async () => {
  loading.value = true
  try {
    const response = await fetch('/api/exceptions/department-exceptions', {
      credentials: 'include',
    })

    if (response.ok) {
      departmentExceptions.value = await response.json()
    } else {
      throw new Error('부서 제외 설정 로드 실패')
    }
  } catch (error) {
    showToastMessage('부서 제외 설정 로드 실패', 'error')
  } finally {
    loading.value = false
  }
}

const loadSummary = async () => {
  loading.value = true
  try {
    const response = await fetch('/api/exceptions/summary', {
      credentials: 'include',
    })

    if (response.ok) {
      summary.value = await response.json()
    } else {
      throw new Error('요약 데이터 로드 실패')
    }
  } catch (error) {
    showToastMessage('요약 데이터 로드 실패', 'error')
  } finally {
    loading.value = false
  }
}

const handleAddException = async () => {
  if (!isFormValid.value) {
    showToastMessage('필수 항목을 모두 입력해주세요.', 'error')
    return
  }

  try {
    const endpoint = formData.value.type === 'user' ? 'user-exceptions' : 'department-exceptions'
    const payload = { ...formData.value }

    // 선택된 항목의 이름 가져오기
    const selectedOption = document.querySelector(
      `select option[value="${formData.value.item_type}"]`,
    )
    if (selectedOption) {
      payload.item_name = selectedOption.getAttribute('data-name') || selectedOption.textContent
    }

    // item_id 설정 - 중요!
    payload.item_id = formData.value.item_type // item_type을 item_id로 사용

    // 필요 없는 필드 제거
    if (formData.value.type === 'user') {
      delete payload.department
      payload.user_id = parseInt(payload.user_id)
    } else {
      delete payload.user_id
    }

    delete payload.type

    // 임시 제외가 아닌 경우 날짜 필드 제거
    if (payload.exclude_type !== 'temporary') {
      delete payload.start_date
      delete payload.end_date
    }

    console.log('제외 설정 추가 요청:', payload) // 디버깅용

    const response = await fetch(`/api/exceptions/${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify(payload),
    })

    if (response.ok) {
      const result = await response.json()
      showToastMessage(result.message || '제외 설정이 추가되었습니다.', 'success')
      closeAddModal()
      resetForm()

      // 현재 탭에 따라 데이터 새로고침
      if (activeTab.value === 'user') {
        await loadUserExceptions()
      } else if (activeTab.value === 'department') {
        await loadDepartmentExceptions()
      }
    } else {
      const error = await response.json()
      showToastMessage(error.error || '추가 실패', 'error')
    }
  } catch (error) {
    console.error('제외 설정 추가 실패:', error)
    showToastMessage('제외 설정 추가 실패: ' + error.message, 'error')
  }
}

const handleDeleteException = async (type, id1, id2) => {
  if (!confirm('이 제외 설정을 삭제하시겠습니까?')) {
    return
  }

  try {
    const endpoint =
      type === 'user'
        ? `user-exceptions/${id1}/${id2}`
        : `department-exceptions/${encodeURIComponent(id1)}/${id2}`

    const response = await fetch(`/api/exceptions/${endpoint}`, {
      method: 'DELETE',
      credentials: 'include',
    })

    if (response.ok) {
      const result = await response.json()
      showToastMessage(result.message || '제외 설정이 삭제되었습니다.', 'success')

      // 현재 탭에 따라 데이터 새로고침
      if (type === 'user') {
        await loadUserExceptions()
      } else {
        await loadDepartmentExceptions()
      }
    } else {
      const error = await response.json()
      showToastMessage(error.error || '삭제 실패', 'error')
    }
  } catch (error) {
    showToastMessage('제외 설정 삭제 실패: ' + error.message, 'error')
  }
}

const handleExport = async (format = 'json') => {
  try {
    const response = await fetch(`/api/exceptions/export?format=${format}`, {
      credentials: 'include',
    })

    if (response.ok) {
      if (format === 'csv') {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = 'exception_settings.csv'
        a.click()
        window.URL.revokeObjectURL(url)
      } else {
        const data = await response.json()
        const blob = new Blob([JSON.stringify(data, null, 2)], {
          type: 'application/json',
        })
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = 'exception_settings.json'
        a.click()
        window.URL.revokeObjectURL(url)
      }
      showToastMessage('제외 설정이 내보내졌습니다.', 'success')
    } else {
      throw new Error('내보내기 실패')
    }
  } catch (error) {
    showToastMessage('내보내기 실패: ' + error.message, 'error')
  }
}

const closeAddModal = () => {
  showAddModal.value = false
  searchedUsers.value = []
}

const resetForm = () => {
  formData.value = {
    type: 'user',
    user_id: '',
    department: '',
    item_category: '',
    item_type: '',
    item_name: '',
    exclude_reason: '',
    exclude_type: 'permanent',
    start_date: '',
    end_date: '',
  }
  selectedUser.value = null
  userSearchQuery.value = ''
  searchedUsers.value = []
}

const truncateText = (text, maxLength) => {
  if (!text) return '-'
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
}

const showToastMessage = (message, type = 'success') => {
  toastMessage.value = message
  toastType.value = type
  showToast.value = true

  setTimeout(() => {
    showToast.value = false
  }, 3000)
}

// 감시자
watch(activeTab, async (newTab) => {
  if (newTab === 'user') {
    await loadUserExceptions()
  } else if (newTab === 'department') {
    await loadDepartmentExceptions()
  } else if (newTab === 'summary') {
    await loadSummary()
  }
})

// 감시자 - 개선된 버전
watch(
  () => formData.value.type,
  (newType) => {
    if (newType === 'user') {
      formData.value.department = ''
    } else {
      formData.value.user_id = ''
      clearSelectedUser()
    }
  },
)

// 제외 유형 변경시 날짜 필드 초기화
watch(
  () => formData.value.exclude_type,
  (newType) => {
    if (newType === 'permanent') {
      formData.value.start_date = ''
      formData.value.end_date = ''
    }
  },
)

// 라이프사이클 훅
onMounted(async () => {
  await loadInitialData()
  await loadUserExceptions()
})
</script>

<style scoped>
@import '../styles/AdminExceptionManagement.css';
</style>
