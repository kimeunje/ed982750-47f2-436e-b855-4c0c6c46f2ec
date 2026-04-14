<template>
  <div class="admin-user-management">
    <!-- 페이지 헤더 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">사용자 관리</h1>
        <p class="page-subtitle">전체 사용자의 보안 현황을 조회하고 관리합니다</p>
      </div>
      <div class="header-right">
        <div class="header-stat">
          <span class="stat-number">{{ totalUsers }}</span>
          <span class="stat-label">전체 사용자</span>
        </div>
      </div>
    </div>

    <!-- 검색바 + 액션 버튼들 -->
    <div class="toolbar">
      <div class="search-box">
        <svg class="search-icon" width="18" height="18" viewBox="0 0 16 16" fill="none">
          <path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001c.03.04.062.078.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1.007 1.007 0 0 0-.115-.1zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0z" fill="currentColor"/>
        </svg>
        <input type="text" v-model="filters.search" @input="onSearchInput" placeholder="사용자 이름, 부서, IP 주소로 검색..." class="search-input" />
        <button v-if="filters.search" @click="clearSearch" class="search-clear">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/></svg>
        </button>
      </div>
      <div class="toolbar-actions">
        <button @click="showAddModal = true" class="btn-action btn-add" title="사용자 추가">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><path d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4z"/></svg>
          추가
        </button>
        <button @click="showUploadModal = true" class="btn-action btn-upload" title="엑셀 업로드">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/><path d="M7.646 1.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1-.708.708L8.5 2.707V11.5a.5.5 0 0 1-1 0V2.707L5.354 4.854a.5.5 0 1 1-.708-.708l3-3z"/></svg>
          업로드
        </button>
        <button @click="exportAll" class="btn-action btn-export" :disabled="loading" title="CSV 내보내기">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/><path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"/></svg>
          내보내기
        </button>
        <button @click="openAdminModal" class="btn-action btn-admin-mgmt" title="관리자 관리">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><path d="M12.5 16a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7zm.5-5v1h1a.5.5 0 0 1 0 1h-1v1a.5.5 0 0 1-1 0v-1h-1a.5.5 0 0 1 0-1h1v-1a.5.5 0 0 1 1 0z"/><path d="M2 1a2 2 0 0 0-2 2v9.5A1.5 1.5 0 0 0 1.5 14h6.06a3.5 3.5 0 0 1-.56-1H1.5a.5.5 0 0 1-.5-.5V3a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v5.06c.35.14.68.32.97.54V3a2 2 0 0 0-2-2H2z"/></svg>
          관리자
        </button>
      </div>
    </div>

    <!-- 활성 필터 태그 -->
    <div v-if="hasActiveColumnFilters" class="active-filters">
      <span class="filter-label">필터:</span>
      <span v-if="filters.department" class="filter-tag" @click="clearFilter('department')">부서: {{ filters.department }} ✕</span>
      <span v-if="filters.status" class="filter-tag" @click="clearFilter('status')">상태: {{ filters.status === 'active' ? '활성' : '비활성' }} ✕</span>
      <span v-if="filters.ipSubnet" class="filter-tag" @click="clearFilter('ipSubnet')">IP: {{ filters.ipSubnet }}* ✕</span>
      <button class="filter-clear-all" @click="resetColumnFilters">모두 해제</button>
    </div>

    <!-- 로딩/에러/빈 상태 -->
    <div v-if="loading" class="state-container"><div class="loading-spinner"></div><p class="state-text">데이터를 불러오는 중...</p></div>
    <div v-else-if="error" class="state-container error"><div class="state-icon">⚠️</div><h3 class="state-title">데이터 로드 실패</h3><p class="state-text">{{ error }}</p><button @click="loadUsers" class="btn-primary">다시 시도</button></div>
    <div v-else-if="users.length === 0" class="state-container"><div class="state-icon">📋</div><h3 class="state-title">사용자 데이터가 없습니다</h3><p class="state-text">검색 조건을 변경해보세요</p></div>

    <!-- 테이블 -->
    <div v-else class="table-wrapper">
      <div class="table-info">
        <span class="table-count">총 <strong>{{ totalUsers }}</strong>명<template v-if="hasActiveFilters"> (필터 적용됨)</template></span>
        <select v-model="filters.perPage" @change="applyFilters" class="per-page-select">
          <option :value="20">20개씩</option><option :value="50">50개씩</option><option :value="100">100개씩</option>
        </select>
      </div>
      <div class="table-scroll">
        <table class="user-table">
          <thead>
            <tr>
              <th class="col-name" @click="toggleSort('name')"><span class="th-sortable">이름 <span v-if="filters.sortBy === 'name'" class="sort-arrow">{{ filters.sortOrder === 'asc' ? '↑' : '↓' }}</span></span></th>
              <th class="col-dept" ref="deptThRef"><div class="th-filterable" @click.stop="toggleColumnFilter('department', $event)"><span>부서</span><svg :class="['filter-icon', { active: filters.department }]" width="12" height="12" viewBox="0 0 16 16" fill="currentColor"><path d="M1.5 1.5A.5.5 0 0 1 2 1h12a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-.128.334L10 8.692V13.5a.5.5 0 0 1-.342.474l-3 1A.5.5 0 0 1 6 14.5V8.692L1.628 3.834A.5.5 0 0 1 1.5 3.5v-2z"/></svg></div></th>
              <th class="col-ip" ref="ipThRef"><div class="th-filterable" @click.stop="toggleColumnFilter('ip', $event)"><span>IP 주소</span><svg :class="['filter-icon', { active: filters.ipSubnet }]" width="12" height="12" viewBox="0 0 16 16" fill="currentColor"><path d="M1.5 1.5A.5.5 0 0 1 2 1h12a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-.128.334L10 8.692V13.5a.5.5 0 0 1-.342.474l-3 1A.5.5 0 0 1 6 14.5V8.692L1.628 3.834A.5.5 0 0 1 1.5 3.5v-2z"/></svg></div></th>
              <th class="col-penalty" @click="toggleSort('total_penalty')"><span class="th-sortable">총 감점 <span v-if="filters.sortBy === 'total_penalty'" class="sort-arrow">{{ filters.sortOrder === 'asc' ? '↑' : '↓' }}</span></span></th>
              <th class="col-status" ref="statusThRef"><div class="th-filterable" @click.stop="toggleColumnFilter('status', $event)"><span>상태</span><svg :class="['filter-icon', { active: filters.status }]" width="12" height="12" viewBox="0 0 16 16" fill="currentColor"><path d="M1.5 1.5A.5.5 0 0 1 2 1h12a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-.128.334L10 8.692V13.5a.5.5 0 0 1-.342.474l-3 1A.5.5 0 0 1 6 14.5V8.692L1.628 3.834A.5.5 0 0 1 1.5 3.5v-2z"/></svg></div></th>
              <th class="col-actions">작업</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in users" :key="user.uid" :class="{ 'row-inactive': !user.is_active }">
              <td class="col-name"><div class="user-name-cell"><span class="user-name">{{ user.name }}</span><span class="user-email">{{ user.email }}</span></div></td>
              <td class="col-dept">{{ user.department }}</td>
              <td class="col-ip"><span class="ip-text">{{ user.ip || '-' }}</span></td>
              <td class="col-penalty"><span :class="['penalty-badge', getPenaltyClass(user.total_penalty)]">{{ formatPenalty(user.total_penalty) }}점</span></td>
              <td class="col-status"><button @click="toggleUserActive(user)" :class="['status-toggle', user.is_active ? 'active' : 'inactive']"><span class="status-dot"></span>{{ user.is_active ? '활성' : '비활성' }}</button></td>
              <td class="col-actions">
                <div class="action-group">
                  <button @click="goToUserDetail(user.uid)" class="action-btn" title="상세보기"><svg width="15" height="15" viewBox="0 0 16 16" fill="currentColor"><path d="M16 8s-3-5.5-8-5.5S0 8 0 8s3 5.5 8 5.5S16 8 16 8zM1.173 8a13.133 13.133 0 0 1 1.66-2.043C4.12 4.668 5.88 3.5 8 3.5c2.12 0 3.879 1.168 5.168 2.457A13.133 13.133 0 0 1 14.828 8c-.058.087-.122.183-.195.288-.335.48-.83 1.12-1.465 1.755C11.879 11.332 10.119 12.5 8 12.5c-2.12 0-3.879-1.168-5.168-2.457A13.134 13.134 0 0 1 1.172 8z"/><path d="M8 5.5a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5zM4.5 8a3.5 3.5 0 1 1 7 0 3.5 3.5 0 0 1-7 0z"/></svg></button>
                  <button @click="openEditModal(user)" class="action-btn" title="수정"><svg width="15" height="15" viewBox="0 0 16 16" fill="currentColor"><path d="M15.502 1.94a.5.5 0 0 1 0 .706L14.459 3.69l-2-2L13.502.646a.5.5 0 0 1 .707 0l1.293 1.293zm-1.75 2.456-2-2L4.939 9.21a.5.5 0 0 0-.121.196l-.805 2.414a.25.25 0 0 0 .316.316l2.414-.805a.5.5 0 0 0 .196-.12l6.813-6.814z"/><path fill-rule="evenodd" d="M1 13.5A1.5 1.5 0 0 0 2.5 15h11a1.5 1.5 0 0 0 1.5-1.5v-6a.5.5 0 0 0-1 0v6a.5.5 0 0 1-.5.5h-11a.5.5 0 0 1-.5-.5v-11a.5.5 0 0 1 .5-.5H9a.5.5 0 0 0 0-1H2.5A1.5 1.5 0 0 0 1 2.5v11z"/></svg></button>
                  <button v-if="!user.is_active" @click="deleteUser(user)" class="action-btn action-delete" title="삭제"><svg width="15" height="15" viewBox="0 0 16 16" fill="currentColor"><path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/><path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/></svg></button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <!-- 페이지네이션 -->
      <div v-if="pagination && pagination.total_pages > 1" class="pagination">
        <button @click="changePage(pagination.current_page - 1)" :disabled="pagination.current_page <= 1" class="page-btn">‹ 이전</button>
        <template v-for="p in paginationPages" :key="p"><span v-if="p === '...'" class="page-ellipsis">…</span><button v-else @click="changePage(p)" :class="['page-btn', { active: p === pagination.current_page }]">{{ p }}</button></template>
        <button @click="changePage(pagination.current_page + 1)" :disabled="pagination.current_page >= pagination.total_pages" class="page-btn">다음 ›</button>
      </div>
    </div>

    <!-- ===== 모달: 사용자 수정 ===== -->
    <Teleport to="body">
      <div v-if="showEditModal" class="modal-backdrop" @click.self="closeEditModal">
        <div class="modal">
          <div class="modal-header"><h2 class="modal-title">사용자 정보 수정</h2><button @click="closeEditModal" class="modal-close"><svg width="18" height="18" viewBox="0 0 16 16" fill="currentColor"><path d="M2.146 2.854a.5.5 0 1 1 .708-.708L8 7.293l5.146-5.147a.5.5 0 0 1 .708.708L8.707 8l5.147 5.146a.5.5 0 0 1-.708.708L8 8.707l-5.146 5.147a.5.5 0 0 1-.708-.708L7.293 8 2.146 2.854Z"/></svg></button></div>
          <form @submit.prevent="submitEdit" class="modal-body">
            <div class="form-grid">
              <div class="form-field"><label>이름 <span class="required">*</span></label><input v-model="editForm.name" type="text" required /><span v-if="editErrors.name" class="field-error">{{ editErrors.name }}</span></div>
              <div class="form-field"><label>IP 주소 <span class="required">*</span></label><input v-model="editForm.ip" type="text" required placeholder="192.168.0.1" /><span v-if="editErrors.ip" class="field-error">{{ editErrors.ip }}</span></div>
              <div class="form-field"><label>이메일</label><input :value="editForm.email" disabled class="field-disabled" /></div>
              <div class="form-field"><label>부서</label><input :value="editForm.department" disabled class="field-disabled" /></div>
            </div>
            <div class="modal-footer"><button type="button" @click="closeEditModal" class="btn-cancel">취소</button><button type="submit" :disabled="editLoading" class="btn-primary">{{ editLoading ? '저장 중...' : '저장' }}</button></div>
          </form>
        </div>
      </div>
    </Teleport>

    <!-- ===== 모달: 사용자 추가 ===== -->
    <Teleport to="body">
      <div v-if="showAddModal" class="modal-backdrop" @click.self="showAddModal = false">
        <div class="modal">
          <div class="modal-header"><h2 class="modal-title">새 사용자 추가</h2><button @click="showAddModal = false" class="modal-close"><svg width="18" height="18" viewBox="0 0 16 16" fill="currentColor"><path d="M2.146 2.854a.5.5 0 1 1 .708-.708L8 7.293l5.146-5.147a.5.5 0 0 1 .708.708L8.707 8l5.147 5.146a.5.5 0 0 1-.708.708L8 8.707l-5.146 5.147a.5.5 0 0 1-.708-.708L7.293 8 2.146 2.854Z"/></svg></button></div>
          <form @submit.prevent="submitAddUser" class="modal-body">
            <div class="form-grid">
              <div class="form-field"><label>이름 <span class="required">*</span></label><input v-model="addForm.name" type="text" required placeholder="사용자 실명" /><span v-if="addErrors.name" class="field-error">{{ addErrors.name }}</span></div>
              <div class="form-field"><label>이메일 <span class="required">*</span></label><input v-model="addForm.email" type="email" required placeholder="user@company.com" /><span v-if="addErrors.email" class="field-error">{{ addErrors.email }}</span></div>
              <div class="form-field"><label>IP 주소 <span class="required">*</span></label><input v-model="addForm.ip" type="text" required placeholder="192.168.0.1" /><span v-if="addErrors.ip" class="field-error">{{ addErrors.ip }}</span></div>
              <div class="form-field"><label>부서 <span class="required">*</span></label><input v-model="addForm.department" type="text" required placeholder="부서명" /><span v-if="addErrors.department" class="field-error">{{ addErrors.department }}</span></div>
              <div class="form-field"><label>권한</label>
                <select v-model="addForm.role" class="form-select">
                  <option value="user">일반 사용자</option>
                  <option value="admin">관리자</option>
                </select>
              </div>
            </div>
            <div class="modal-footer"><button type="button" @click="showAddModal = false" class="btn-cancel">취소</button><button type="submit" :disabled="addLoading" class="btn-primary">{{ addLoading ? '추가 중...' : '사용자 추가' }}</button></div>
          </form>
        </div>
      </div>
    </Teleport>

    <!-- ===== 모달: 엑셀 업로드 ===== -->
    <Teleport to="body">
      <div v-if="showUploadModal" class="modal-backdrop" @click.self="closeUploadModal">
        <div class="modal modal-wide">
          <div class="modal-header"><h2 class="modal-title">사용자 일괄 등록 (엑셀/CSV)</h2><button @click="closeUploadModal" class="modal-close"><svg width="18" height="18" viewBox="0 0 16 16" fill="currentColor"><path d="M2.146 2.854a.5.5 0 1 1 .708-.708L8 7.293l5.146-5.147a.5.5 0 0 1 .708.708L8.707 8l5.147 5.146a.5.5 0 0 1-.708.708L8 8.707l-5.146 5.147a.5.5 0 0 1-.708-.708L7.293 8 2.146 2.854Z"/></svg></button></div>
          <div class="modal-body">
            <!-- 파일 업로드 영역 -->
            <div class="upload-zone" :class="{ dragover: isDragOver }" @drop.prevent="handleFileDrop" @dragover.prevent="isDragOver = true" @dragleave="isDragOver = false" @click="$refs.fileInput.click()">
              <input ref="fileInput" type="file" accept=".csv,.xlsx,.xls" @change="handleFileSelect" style="display:none" />
              <div v-if="!uploadFile" class="upload-placeholder">
                <div class="upload-icon-large">📁</div>
                <p>CSV 또는 Excel 파일을 드래그하거나 클릭하여 선택</p>
                <small>필수 컬럼: 이름, 이메일, IP주소, 부서</small>
              </div>
              <div v-else class="upload-file-info">
                <span class="file-name">📄 {{ uploadFile.name }}</span>
                <span class="file-size">({{ (uploadFile.size / 1024).toFixed(1) }}KB)</span>
                <button @click.stop="uploadFile = null; uploadPreview = []" class="file-remove">✕</button>
              </div>
            </div>
            <!-- 미리보기 -->
            <div v-if="uploadPreview.length > 0" class="upload-preview">
              <p class="preview-count">{{ uploadPreview.length }}명의 사용자 데이터가 준비되었습니다.</p>
              <div class="preview-table-wrap">
                <table class="preview-table">
                  <thead><tr><th>이름</th><th>이메일</th><th>IP</th><th>부서</th></tr></thead>
                  <tbody>
                    <tr v-for="(row, i) in uploadPreview.slice(0, 5)" :key="i">
                      <td>{{ row.name }}</td><td>{{ row.email }}</td><td>{{ row.ip }}</td><td>{{ row.department }}</td>
                    </tr>
                    <tr v-if="uploadPreview.length > 5"><td colspan="4" class="preview-more">...외 {{ uploadPreview.length - 5 }}명</td></tr>
                  </tbody>
                </table>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" @click="closeUploadModal" class="btn-cancel">취소</button>
              <button @click="submitUpload" :disabled="uploadLoading || !uploadPreview.length" class="btn-primary">
                {{ uploadLoading ? '업로드 중...' : `${uploadPreview.length}명 일괄 등록` }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 컬럼 필터 드롭다운 (Teleport) -->

    <!-- ===== 모달: 관리자 관리 ===== -->
    <Teleport to="body">
      <div v-if="showAdminModal" class="modal-backdrop" @click.self="showAdminModal = false">
        <div class="modal modal-wide">
          <div class="modal-header">
            <h2 class="modal-title">관리자 권한 관리</h2>
            <button @click="showAdminModal = false" class="modal-close"><svg width="18" height="18" viewBox="0 0 16 16" fill="currentColor"><path d="M2.146 2.854a.5.5 0 1 1 .708-.708L8 7.293l5.146-5.147a.5.5 0 0 1 .708.708L8.707 8l5.147 5.146a.5.5 0 0 1-.708.708L8 8.707l-5.146 5.147a.5.5 0 0 1-.708-.708L7.293 8 2.146 2.854Z"/></svg></button>
          </div>
          <div class="modal-body">
            <!-- 현재 관리자 목록 -->
            <div class="admin-section">
              <h3 class="admin-section-title">현재 관리자 <span class="admin-count">{{ adminUsers.length }}명</span></h3>
              <div v-if="adminUsers.length === 0" class="admin-empty">등록된 관리자가 없습니다.</div>
              <div v-else class="admin-list">
                <div v-for="admin in adminUsers" :key="admin.uid" class="admin-card">
                  <div class="admin-info">
                    <span class="admin-name">{{ admin.name }}</span>
                    <span class="admin-detail">{{ admin.department }} · {{ admin.email }}</span>
                  </div>
                  <button @click="demoteFromAdmin(admin)" class="admin-remove-btn" title="관리자 해제">
                    권한 해제
                  </button>
                </div>
              </div>
            </div>

            <!-- 구분선 -->
            <div class="admin-divider"></div>

            <!-- 관리자 추가 검색 -->
            <div class="admin-section">
              <h3 class="admin-section-title">관리자 추가</h3>
              <div class="admin-search-box">
                <input
                  type="text"
                  v-model="adminSearchQuery"
                  @input="onAdminSearchInput"
                  placeholder="이름 또는 부서로 사용자 검색..."
                  class="admin-search-input"
                />
              </div>
              <div v-if="adminSearchResults.length > 0" class="admin-search-results">
                <div v-for="user in adminSearchResults" :key="user.uid" class="admin-search-item">
                  <div class="admin-info">
                    <span class="admin-name">{{ user.name }}</span>
                    <span class="admin-detail">{{ user.department }} · {{ user.email }}</span>
                  </div>
                  <button @click="promoteToAdmin(user)" class="admin-promote-btn">
                    관리자 지정
                  </button>
                </div>
              </div>
              <div v-else-if="adminSearchQuery.length >= 2" class="admin-empty">
                검색 결과가 없습니다.
              </div>
              <div v-else class="admin-empty admin-hint">
                2글자 이상 입력하면 검색됩니다.
              </div>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 컬럼 필터 드롭다운 (Teleport) -->
    <Teleport to="body">
      <div v-if="openFilter" class="cfd-overlay" @click="closeColumnFilter">
        <div v-if="openFilter === 'department'" class="cfd-floating" :style="dropdownPosition" @click.stop>
          <div class="cfd-item" :class="{ selected: !filters.department }" @click="setColumnFilter('department', '')">전체 부서</div>
          <div v-for="dept in departmentOptions" :key="dept" class="cfd-item" :class="{ selected: filters.department === dept }" @click="setColumnFilter('department', dept)">{{ dept }}</div>
        </div>
        <div v-if="openFilter === 'ip'" class="cfd-floating cfd-input-type" :style="dropdownPosition" @click.stop>
          <input ref="ipFilterInputRef" type="text" v-model="filters.ipSubnet" @input="onIpFilterInput" @keydown.enter="closeColumnFilter" placeholder="예: 192.168.1" class="cfd-input" />
          <div v-if="filters.ipSubnet" class="cfd-item cfd-clear" @click="setColumnFilter('ipSubnet', '')">필터 해제</div>
        </div>
        <div v-if="openFilter === 'status'" class="cfd-floating" :style="dropdownPosition" @click.stop>
          <div class="cfd-item" :class="{ selected: !filters.status }" @click="setColumnFilter('status', '')">전체</div>
          <div class="cfd-item" :class="{ selected: filters.status === 'active' }" @click="setColumnFilter('status', 'active')">활성</div>
          <div class="cfd-item" :class="{ selected: filters.status === 'inactive' }" @click="setColumnFilter('status', 'inactive')">비활성</div>
        </div>
      </div>
    </Teleport>

    <!-- 토스트 -->
    <Transition name="toast"><div v-if="toast.show" :class="['toast', `toast-${toast.type}`]">{{ toast.message }}</div></Transition>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Papa from 'papaparse'

const router = useRouter()
const authStore = useAuthStore()

// ===== 상태 =====
const users = ref([])
const loading = ref(false)
const error = ref('')
const pagination = ref(null)
const departmentOptions = ref([])
const openFilter = ref(null)
const ipFilterInputRef = ref(null)
const dropdownPosition = ref({})

const filters = ref({ department: '', status: '', ipSubnet: '', search: '', sortBy: 'total_penalty', sortOrder: 'desc', page: 1, perPage: 20 })

// 수정 모달
const showEditModal = ref(false)
const editLoading = ref(false)
const editForm = ref({ uid: null, name: '', email: '', ip: '', department: '' })
const editErrors = ref({})

// 추가 모달
const showAddModal = ref(false)
const addLoading = ref(false)
const addForm = ref({ name: '', email: '', ip: '', department: '', role: 'user' })
const addErrors = ref({})

// 업로드 모달
const showUploadModal = ref(false)
const uploadLoading = ref(false)
const uploadFile = ref(null)
const uploadPreview = ref([])
const isDragOver = ref(false)
const fileInput = ref(null)

const toast = ref({ show: false, message: '', type: 'success' })
let toastTimer = null
let searchTimeout = null

// ===== Computed =====
const currentYear = new Date().getFullYear()
const totalUsers = computed(() => pagination.value?.total_count || users.value.length)
const hasActiveFilters = computed(() => filters.value.department || filters.value.status || filters.value.ipSubnet || filters.value.search)
const hasActiveColumnFilters = computed(() => filters.value.department || filters.value.status || filters.value.ipSubnet)
const paginationPages = computed(() => {
  if (!pagination.value) return []
  const c = pagination.value.current_page, t = pagination.value.total_pages, p = []
  if (t <= 7) { for (let i = 1; i <= t; i++) p.push(i) }
  else { p.push(1); if (c > 3) p.push('...'); for (let i = Math.max(2, c - 1); i <= Math.min(t - 1, c + 1); i++) p.push(i); if (c < t - 2) p.push('...'); p.push(t) }
  return p
})

// ===== API =====
const api = {
  async loadUsers() {
    const p = new URLSearchParams({ year: currentYear, page: filters.value.page, per_page: filters.value.perPage, sort_by: filters.value.sortBy, sort_order: filters.value.sortOrder })
    if (filters.value.department) p.append('department', filters.value.department)
    if (filters.value.status) p.append('status', filters.value.status)
    if (filters.value.ipSubnet) p.append('ip_subnet', filters.value.ipSubnet)
    if (filters.value.search) p.append('search', filters.value.search)
    const r = await fetch(`/api/admin/dashboard/users?${p}`, { headers: { Authorization: `Bearer ${authStore.token}` } })
    if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json()
  },
  async updateUser(uid, data) {
    const r = await fetch(`/api/admin/users/${uid}`, { method: 'PUT', headers: { Authorization: `Bearer ${authStore.token}`, 'Content-Type': 'application/json' }, body: JSON.stringify(data) })
    if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.message || `HTTP ${r.status}`) }; return r.json()
  },
  async createUser(data) {
    const r = await fetch('/api/admin/users', { method: 'POST', headers: { Authorization: `Bearer ${authStore.token}`, 'Content-Type': 'application/json' }, body: JSON.stringify(data) })
    if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.message || `HTTP ${r.status}`) }; return r.json()
  },
  async toggleActive(uid) {
    const r = await fetch(`/api/admin/users/${uid}/toggle-active`, { method: 'PATCH', headers: { Authorization: `Bearer ${authStore.token}`, 'Content-Type': 'application/json' } })
    if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.message || `HTTP ${r.status}`) }; return r.json()
  },
  async updateRole(uid, role) {
    const r = await fetch(`/api/admin/users/${uid}`, { method: 'PUT', headers: { Authorization: `Bearer ${authStore.token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ role }) })
    if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.message || `HTTP ${r.status}`) }; return r.json()
  },
  async deleteUser(uid) {
    const r = await fetch(`/api/admin/users/${uid}`, { method: 'DELETE', headers: { Authorization: `Bearer ${authStore.token}` } })
    if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.message || `HTTP ${r.status}`) }; return r.json()
  },
  async exportUsers() {
    const p = new URLSearchParams({ year: currentYear, sort_by: filters.value.sortBy, sort_order: filters.value.sortOrder })
    if (filters.value.department) p.append('department', filters.value.department)
    if (filters.value.status) p.append('status', filters.value.status)
    if (filters.value.ipSubnet) p.append('ip_subnet', filters.value.ipSubnet)
    if (filters.value.search) p.append('search', filters.value.search)
    const r = await fetch(`/api/admin/dashboard/export?${p}`, { headers: { Authorization: `Bearer ${authStore.token}` } })
    if (!r.ok) throw new Error(`HTTP ${r.status}`); return r
  },
}

// ===== 데이터 로드 =====
const loadUsers = async () => {
  loading.value = true; error.value = ''
  try {
    const data = await api.loadUsers()
    users.value = (data.users || []).map(u => ({ ...u, is_active: u.is_active === undefined ? true : Boolean(u.is_active), total_penalty: parseFloat(u.total_penalty) || 0 }))
    pagination.value = data.pagination || null
    if (!departmentOptions.value.length && data.users?.length) departmentOptions.value = [...new Set(data.users.map(u => u.department).filter(Boolean))].sort()
  } catch (e) { error.value = e.message || '데이터를 불러오는데 실패했습니다.' }
  finally { loading.value = false }
}

// ===== 검색/필터 =====
const onSearchInput = () => { clearTimeout(searchTimeout); searchTimeout = setTimeout(() => { filters.value.page = 1; loadUsers() }, 400) }
const clearSearch = () => { filters.value.search = ''; applyFilters() }
const toggleColumnFilter = (col, event) => {
  if (openFilter.value === col) { openFilter.value = null; return }
  const rect = event.currentTarget.getBoundingClientRect()
  dropdownPosition.value = { position: 'fixed', top: `${rect.bottom + 4}px`, left: `${rect.left}px` }
  openFilter.value = col
  if (col === 'ip') nextTick(() => ipFilterInputRef.value?.focus())
}
const closeColumnFilter = () => { openFilter.value = null }
const setColumnFilter = (key, val) => { filters.value[key] = val; openFilter.value = null; applyFilters() }
const clearFilter = (key) => { filters.value[key] = ''; applyFilters() }
const resetColumnFilters = () => { filters.value.department = ''; filters.value.status = ''; filters.value.ipSubnet = ''; applyFilters() }
const onIpFilterInput = () => { clearTimeout(searchTimeout); searchTimeout = setTimeout(() => { filters.value.page = 1; loadUsers() }, 400) }
const toggleSort = (field) => {
  if (filters.value.sortBy === field) filters.value.sortOrder = filters.value.sortOrder === 'asc' ? 'desc' : 'asc'
  else { filters.value.sortBy = field; filters.value.sortOrder = field === 'name' ? 'asc' : 'desc' }
  applyFilters()
}
const applyFilters = () => { filters.value.page = 1; loadUsers() }
const changePage = (pg) => { if (pagination.value && pg >= 1 && pg <= pagination.value.total_pages) { filters.value.page = pg; loadUsers() } }

// ===== 활성/비활성 =====
const toggleUserActive = async (user) => {
  const act = user.is_active ? '비활성화' : '활성화'
  if (!confirm(`${user.name} 사용자를 ${act}하시겠습니까?`)) return
  try { const res = await api.toggleActive(user.uid); if (!res.success) throw new Error(res.message); const t = users.value.find(u => u.uid === user.uid); if (t) t.is_active = Boolean(res.is_active); showToast(res.message || `${act}되었습니다.`, 'success') }
  catch (e) { showToast(e.message || `${act} 실패`, 'error') }
}

// ===== 사용자 삭제 (비활성 사용자만) =====
const deleteUser = async (user) => {
  if (user.is_active) { showToast('활성 사용자는 삭제할 수 없습니다. 먼저 비활성화해주세요.', 'error'); return }
  if (!confirm(`⚠️ ${user.name} 사용자를 영구 삭제하시겠습니까?\n\n이 작업은 되돌릴 수 없으며, 해당 사용자의 모든 데이터가 삭제됩니다.`)) return
  // 이중 확인
  if (!confirm(`정말로 "${user.name}" 사용자를 삭제하시겠습니까?`)) return
  try {
    const res = await api.deleteUser(user.uid)
    if (!res.success) throw new Error(res.message)
    showToast(res.message || `${user.name} 사용자가 삭제되었습니다.`, 'success')
    await loadUsers()
  } catch (e) { showToast(e.message || '삭제 실패', 'error') }
}

// ===== 수정 모달 =====
const openEditModal = (user) => { editForm.value = { uid: user.uid, name: user.name || '', email: user.email || '', ip: user.ip || '', department: user.department || '' }; editErrors.value = {}; showEditModal.value = true }
const closeEditModal = () => { showEditModal.value = false }
const submitEdit = async () => {
  const e = {}
  if (!editForm.value.name.trim()) e.name = '이름을 입력해주세요.'
  if (!editForm.value.ip.trim()) e.ip = 'IP를 입력해주세요.'
  else { const pat = /^(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)$/; for (const ip of editForm.value.ip.split(',').map(s => s.trim())) { if (!pat.test(ip)) { e.ip = `올바르지 않은 IP: ${ip}`; break } } }
  editErrors.value = e; if (Object.keys(e).length) return
  editLoading.value = true
  try { await api.updateUser(editForm.value.uid, { name: editForm.value.name.trim(), ip: editForm.value.ip.trim() }); showToast('수정되었습니다.', 'success'); closeEditModal(); await loadUsers() }
  catch (err) { showToast(`수정 실패: ${err.message}`, 'error') }
  finally { editLoading.value = false }
}

// ===== 추가 모달 =====
const submitAddUser = async () => {
  const e = {}
  if (!addForm.value.name.trim()) e.name = '이름을 입력해주세요.'
  if (!addForm.value.email.trim()) e.email = '이메일을 입력해주세요.'
  else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(addForm.value.email)) e.email = '올바른 이메일 형식이 아닙니다.'
  if (!addForm.value.ip.trim()) e.ip = 'IP를 입력해주세요.'
  if (!addForm.value.department.trim()) e.department = '부서를 입력해주세요.'
  addErrors.value = e; if (Object.keys(e).length) return
  addLoading.value = true
  try {
    await api.createUser(addForm.value)
    showToast('사용자가 추가되었습니다.', 'success')
    showAddModal.value = false
    addForm.value = { name: '', email: '', ip: '', department: '', role: 'user' }
    await loadUsers()
  } catch (err) { showToast(`추가 실패: ${err.message}`, 'error') }
  finally { addLoading.value = false }
}

// ===== 관리자 관리 모달 =====
const showAdminModal = ref(false)
const adminSearchQuery = ref('')
const adminSearchResults = ref([])
const adminUsers = ref([])
let adminSearchTimeout = null

const openAdminModal = async () => {
  showAdminModal.value = true
  adminSearchQuery.value = ''
  adminSearchResults.value = []
  await loadAdminUsers()
}

const loadAdminUsers = async () => {
  try {
    // 전체 사용자에서 role=admin만 가져오기 (페이징 없이)
    const params = new URLSearchParams({ year: currentYear, page: 1, per_page: 999 })
    const r = await fetch(`/api/admin/dashboard/users?${params}`, {
      headers: { Authorization: `Bearer ${authStore.token}` }
    })
    if (r.ok) {
      const data = await r.json()
      adminUsers.value = (data.users || []).filter(u => u.role === 'admin')
    }
  } catch { adminUsers.value = [] }
}

const onAdminSearchInput = () => {
  clearTimeout(adminSearchTimeout)
  if (adminSearchQuery.value.length < 2) { adminSearchResults.value = []; return }
  adminSearchTimeout = setTimeout(async () => {
    try {
      const params = new URLSearchParams({
        year: currentYear,
        page: 1,
        per_page: 20,
        search: adminSearchQuery.value,
      })
      const r = await fetch(`/api/admin/dashboard/users?${params}`, {
        headers: { Authorization: `Bearer ${authStore.token}` }
      })
      if (r.ok) {
        const data = await r.json()
        // 이미 관리자인 사용자는 제외
        const adminUids = adminUsers.value.map(a => a.uid)
        adminSearchResults.value = (data.users || []).filter(u => u.role !== 'admin' && !adminUids.includes(u.uid))
      }
    } catch { adminSearchResults.value = [] }
  }, 300)
}

const promoteToAdmin = async (user) => {
  if (!confirm(`${user.name}을(를) 관리자로 지정하시겠습니까?`)) return
  try {
    await api.updateRole(user.uid, 'admin')
    // 관리자 목록 다시 로드
    await loadAdminUsers()
    // 검색 결과에서 제거
    adminSearchResults.value = adminSearchResults.value.filter(u => u.uid !== user.uid)
    // 메인 테이블에도 반영
    const t = users.value.find(u => u.uid === user.uid)
    if (t) t.role = 'admin'
    showToast(`${user.name}이(가) 관리자로 지정되었습니다.`, 'success')
  } catch (e) { showToast(e.message || '관리자 지정 실패', 'error') }
}

const demoteFromAdmin = async (user) => {
  if (!confirm(`${user.name}의 관리자 권한을 해제하시겠습니까?`)) return
  try {
    await api.updateRole(user.uid, 'user')
    // 관리자 목록 다시 로드
    await loadAdminUsers()
    // 메인 테이블에도 반영
    const t = users.value.find(u => u.uid === user.uid)
    if (t) t.role = 'user'
    showToast(`${user.name}의 관리자 권한이 해제되었습니다.`, 'success')
  } catch (e) { showToast(e.message || '관리자 해제 실패', 'error') }
}

// ===== 엑셀 업로드 =====
const handleFileSelect = (e) => { const file = e.target.files?.[0]; if (file) parseUploadFile(file) }
const handleFileDrop = (e) => { isDragOver.value = false; const file = e.dataTransfer.files?.[0]; if (file) parseUploadFile(file) }
const parseUploadFile = (file) => {
  uploadFile.value = file
  const ext = file.name.split('.').pop().toLowerCase()
  if (ext === 'csv') {
    Papa.parse(file, {
      header: true, skipEmptyLines: true, encoding: 'UTF-8',
      complete: (results) => { uploadPreview.value = normalizeUploadData(results.data) },
      error: () => { showToast('CSV 파싱 실패', 'error'); uploadFile.value = null }
    })
  } else {
    // xlsx는 SheetJS 사용
    const reader = new FileReader()
    reader.onload = async (e) => {
      try {
        const XLSX = await import('xlsx')
        const wb = XLSX.read(e.target.result, { type: 'array' })
        const ws = wb.Sheets[wb.SheetNames[0]]
        const data = XLSX.utils.sheet_to_json(ws)
        uploadPreview.value = normalizeUploadData(data)
      } catch { showToast('엑셀 파싱 실패', 'error'); uploadFile.value = null }
    }
    reader.readAsArrayBuffer(file)
  }
}
const normalizeUploadData = (rows) => {
  const mapping = { '이름': 'name', '사용자명': 'name', 'name': 'name', '이메일': 'email', 'email': 'email', 'IP': 'ip', 'IP주소': 'ip', 'ip': 'ip', '부서': 'department', 'department': 'department' }
  return rows.map(row => {
    const r = {}
    Object.entries(row).forEach(([k, v]) => { const mk = mapping[k.trim()] || mapping[k.trim().replace(/\s/g, '')]; if (mk) r[mk] = String(v).trim() })
    return r
  }).filter(r => r.name && (r.email || r.ip))
}
const closeUploadModal = () => { showUploadModal.value = false; uploadFile.value = null; uploadPreview.value = []; isDragOver.value = false }
const submitUpload = async () => {
  if (!uploadPreview.value.length) return
  uploadLoading.value = true
  let success = 0, fail = 0
  try {
    for (const user of uploadPreview.value) {
      try { await api.createUser({ name: user.name, email: user.email || '', ip: user.ip || '', department: user.department || '', role: 'user' }); success++ }
      catch { fail++ }
    }
    showToast(`${success}명 등록 완료${fail ? `, ${fail}명 실패` : ''}`, success > 0 ? 'success' : 'error')
    if (success > 0) { closeUploadModal(); await loadUsers() }
  } catch (e) { showToast('업로드 실패', 'error') }
  finally { uploadLoading.value = false }
}

// ===== 내보내기 =====
const exportAll = async () => {
  try { const r = await api.exportUsers(); const b = await r.blob(); const u = window.URL.createObjectURL(b); const a = document.createElement('a'); a.href = u; a.download = `사용자_보안현황_${currentYear}년_${new Date().toISOString().split('T')[0]}.csv`; document.body.appendChild(a); a.click(); window.URL.revokeObjectURL(u); document.body.removeChild(a); showToast('내보내기 완료', 'success') }
  catch { showToast('내보내기 실패', 'error') }
}

// ===== 유틸 =====
const goToUserDetail = (uid) => router.push({ name: 'AdminUserDetail', params: { userId: uid } })
const formatPenalty = (v) => { const n = parseFloat(v); return isNaN(n) ? '0.0' : n.toFixed(1) }
const getPenaltyClass = (v) => { const n = parseFloat(v); if (isNaN(n) || n === 0) return 'penalty-perfect'; if (n <= 1) return 'penalty-low'; if (n <= 2.5) return 'penalty-medium'; return 'penalty-high' }
const showToast = (msg, type = 'success') => { clearTimeout(toastTimer); toast.value = { show: true, message: msg, type }; toastTimer = setTimeout(() => { toast.value.show = false }, 3000) }

// ===== 이벤트 =====
const handleKeydown = (e) => {
  if (showEditModal.value || showAddModal.value || showUploadModal.value || showAdminModal.value) { if (e.key === 'Escape') { showEditModal.value = false; showAddModal.value = false; closeUploadModal(); showAdminModal.value = false }; return }
  if (openFilter.value && e.key === 'Escape') { openFilter.value = null; return }
  if (e.key === 'F5') { e.preventDefault(); loadUsers() }
}

onMounted(() => {
  if (authStore.isAuthenticated && authStore.user?.role === 'admin') loadUsers()
  else router.push('/login')
  document.addEventListener('keydown', handleKeydown)
})
onUnmounted(() => { clearTimeout(searchTimeout); clearTimeout(toastTimer); document.removeEventListener('keydown', handleKeydown) })
</script>

<style scoped>
.admin-user-management { padding: 24px 30px 40px; background-color: #fff; min-height: calc(100vh - 114px); width: 100%; max-width: 1200px; margin: 20px auto; box-shadow: 0 0 20px rgba(0,0,0,0.05); border-left: 1px solid #e0e4e9; border-right: 1px solid #e0e4e9; border-radius: 8px; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 28px; padding-bottom: 20px; border-bottom: 2px solid #e5e7eb; }
.page-title { font-size: 26px; font-weight: 700; color: var(--dark-blue, #3949ab); margin: 0 0 6px 0; }
.page-subtitle { font-size: 14px; color: #6b7280; margin: 0; }
.header-stat { display: flex; flex-direction: column; align-items: center; background: var(--subtle-blue, #eef1fd); padding: 12px 20px; border-radius: 10px; }
.stat-number { font-size: 24px; font-weight: 700; color: var(--primary-color, #4056b7); line-height: 1; }
.stat-label { font-size: 12px; color: #6b7280; margin-top: 4px; }

.toolbar { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.search-box { position: relative; flex: 1; }
.search-icon { position: absolute; left: 14px; top: 50%; transform: translateY(-50%); color: #9ca3af; pointer-events: none; }
.search-input { width: 100%; padding: 11px 40px 11px 42px; border: 1.5px solid #d1d5db; border-radius: 10px; font-size: 14px; outline: none; transition: border-color 0.2s, box-shadow 0.2s; }
.search-input:focus { border-color: var(--primary-color, #4056b7); box-shadow: 0 0 0 3px rgba(64,86,183,0.1); }
.search-input::placeholder { color: #b0b7c3; }
.search-clear { position: absolute; right: 10px; top: 50%; transform: translateY(-50%); background: none; border: none; cursor: pointer; color: #9ca3af; display: flex; padding: 4px; }

.toolbar-actions { display: flex; gap: 6px; flex-shrink: 0; }
.btn-action { display: flex; align-items: center; gap: 5px; padding: 9px 13px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 13px; font-weight: 500; cursor: pointer; transition: all 0.15s; background: white; color: #374151; white-space: nowrap; }
.btn-action:hover { background-color: #f3f4f6; border-color: #9ca3af; }
.btn-add { border-color: #10b981; color: #059669; } .btn-add:hover { background-color: #ecfdf5; }
.btn-upload { border-color: #6366f1; color: #4f46e5; } .btn-upload:hover { background-color: #eef2ff; }
.btn-export { border-color: var(--primary-color, #4056b7); color: var(--primary-color, #4056b7); } .btn-export:hover { background-color: var(--subtle-blue, #eef1fd); }
.btn-action:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-admin-mgmt { border-color: #d97706; color: #b45309; } .btn-admin-mgmt:hover { background-color: #fffbeb; }

/* 관리자 관리 모달 */
.admin-section { margin-bottom: 4px; }
.admin-section-title { font-size: 14px; font-weight: 600; color: #374151; margin: 0 0 12px 0; display: flex; align-items: center; gap: 8px; }
.admin-count { font-size: 12px; font-weight: 500; color: #6b7280; background: #f3f4f6; padding: 2px 8px; border-radius: 10px; }
.admin-empty { font-size: 13px; color: #9ca3af; text-align: center; padding: 16px; }
.admin-hint { font-style: italic; }
.admin-divider { height: 1px; background: #e5e7eb; margin: 20px 0; }

.admin-list { display: flex; flex-direction: column; gap: 8px; max-height: 200px; overflow-y: auto; }
.admin-card { display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; }
.admin-info { display: flex; flex-direction: column; gap: 2px; }
.admin-name { font-size: 13px; font-weight: 600; color: #1f2937; }
.admin-detail { font-size: 11px; color: #9ca3af; }
.admin-remove-btn { padding: 5px 10px; border: 1px solid #fecaca; border-radius: 6px; background: white; color: #dc2626; font-size: 12px; cursor: pointer; transition: all 0.15s; white-space: nowrap; }
.admin-remove-btn:hover { background-color: #fef2f2; }

.admin-search-box { margin-bottom: 12px; }
.admin-search-input { width: 100%; padding: 9px 14px; border: 1.5px solid #d1d5db; border-radius: 8px; font-size: 13px; outline: none; transition: border-color 0.2s; }
.admin-search-input:focus { border-color: var(--primary-color, #4056b7); box-shadow: 0 0 0 2px rgba(64,86,183,0.1); }

.admin-search-results { display: flex; flex-direction: column; gap: 6px; max-height: 200px; overflow-y: auto; }
.admin-search-item { display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; border: 1px solid #e5e7eb; border-radius: 8px; transition: background-color 0.1s; }
.admin-search-item:hover { background-color: #f9fafb; }
.admin-promote-btn { padding: 5px 10px; border: 1px solid #d97706; border-radius: 6px; background: white; color: #b45309; font-size: 12px; cursor: pointer; transition: all 0.15s; white-space: nowrap; }
.admin-promote-btn:hover { background-color: #fffbeb; }

.active-filters { display: flex; align-items: center; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
.filter-label { font-size: 12px; color: #6b7280; font-weight: 500; }
.filter-tag { display: inline-flex; align-items: center; gap: 4px; padding: 4px 10px; background-color: var(--subtle-blue, #eef1fd); border: 1px solid rgba(64,86,183,0.2); border-radius: 14px; font-size: 12px; color: var(--primary-color, #4056b7); cursor: pointer; }
.filter-tag:hover { background-color: rgba(64,86,183,0.15); }
.filter-clear-all { padding: 4px 10px; background: none; border: 1px solid #d1d5db; border-radius: 14px; font-size: 12px; color: #6b7280; cursor: pointer; }

.state-container { display: flex; flex-direction: column; align-items: center; padding: 60px 20px; text-align: center; }
.state-icon { font-size: 40px; margin-bottom: 12px; } .state-title { font-size: 16px; font-weight: 600; color: #374151; margin: 0 0 8px 0; } .state-text { font-size: 14px; color: #6b7280; margin: 0; }
.loading-spinner { width: 36px; height: 36px; border: 3px solid #e5e7eb; border-top-color: var(--primary-color, #4056b7); border-radius: 50%; animation: spin 0.8s linear infinite; margin-bottom: 16px; }
@keyframes spin { to { transform: rotate(360deg); } }

.table-wrapper { border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; }
.table-info { display: flex; justify-content: space-between; align-items: center; padding: 10px 16px; background-color: #f9fafb; border-bottom: 1px solid #e5e7eb; }
.table-count { font-size: 13px; color: #6b7280; } .per-page-select { padding: 4px 8px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 12px; background: white; }
.table-scroll { overflow-x: auto; }
.user-table { width: 100%; border-collapse: collapse; }
.user-table thead { background-color: #f9fafb; }
.user-table th { padding: 10px 16px; font-size: 12px; font-weight: 600; color: #6b7280; text-align: left; letter-spacing: 0.03em; border-bottom: 1px solid #e5e7eb; white-space: nowrap; position: relative; user-select: none; }
.th-sortable { display: flex; align-items: center; gap: 4px; cursor: pointer; } .th-sortable:hover { color: #374151; }
.sort-arrow { font-size: 11px; color: var(--primary-color, #4056b7); }
.th-filterable { display: flex; align-items: center; gap: 5px; cursor: pointer; padding: 2px 4px; margin: -2px -4px; border-radius: 4px; transition: background-color 0.15s; } .th-filterable:hover { background-color: #eef0f4; }
.filter-icon { color: #c4c9d4; transition: color 0.15s; flex-shrink: 0; } .filter-icon.active { color: var(--primary-color, #4056b7); }
.cfd-overlay { position: fixed; inset: 0; z-index: 9000; }
.cfd-floating { position: fixed; min-width: 160px; max-height: 260px; overflow-y: auto; background: white; border: 1px solid #e5e7eb; border-radius: 8px; box-shadow: 0 8px 24px rgba(0,0,0,0.12); animation: dropIn 0.12s ease; }
.cfd-floating.cfd-input-type { min-width: 220px; padding: 8px; overflow: visible; }
.cfd-item { padding: 8px 14px; font-size: 13px; color: #374151; cursor: pointer; transition: background-color 0.1s; } .cfd-item:hover { background-color: #f3f4f6; }
.cfd-item.selected { background-color: var(--subtle-blue, #eef1fd); color: var(--primary-color, #4056b7); font-weight: 500; }
.cfd-item.cfd-clear { color: #6b7280; border-top: 1px solid #f3f4f6; margin-top: 4px; padding-top: 8px; }
.cfd-input { width: 100%; padding: 8px 10px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px; font-family: 'SF Mono','Consolas',monospace; outline: none; margin-bottom: 4px; } .cfd-input:focus { border-color: var(--primary-color, #4056b7); }
@keyframes dropIn { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: translateY(0); } }

.user-table td { padding: 12px 16px; font-size: 13px; color: #374151; border-bottom: 1px solid #f3f4f6; vertical-align: middle; }
.user-table tbody tr:hover { background-color: #fafbfc; } .row-inactive { opacity: 0.55; } .row-inactive:hover { opacity: 0.75; }
.col-name { min-width: 160px; } .col-dept { min-width: 100px; } .col-ip { min-width: 130px; } .col-penalty { min-width: 90px; } .col-status { min-width: 80px; } .col-actions { min-width: 100px; }
.user-name-cell { display: flex; flex-direction: column; gap: 2px; } .user-name { font-weight: 600; color: #1f2937; } .user-email { font-size: 11px; color: #9ca3af; }
.ip-text { font-family: 'SF Mono','Consolas',monospace; font-size: 12px; color: #6b7280; }
.penalty-badge { display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; }
.penalty-perfect { background-color: #ecfdf5; color: #059669; } .penalty-low { background-color: #eff6ff; color: #2563eb; } .penalty-medium { background-color: #fffbeb; color: #d97706; } .penalty-high { background-color: #fef2f2; color: #dc2626; }
.status-toggle { display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border: 1px solid; border-radius: 14px; font-size: 12px; font-weight: 500; cursor: pointer; transition: all 0.2s; background: white; }
.status-toggle.active { border-color: #bbf7d0; color: #15803d; } .status-toggle.active:hover { background-color: #f0fdf4; }
.status-toggle.inactive { border-color: #fecaca; color: #b91c1c; } .status-toggle.inactive:hover { background-color: #fef2f2; }
.status-dot { width: 7px; height: 7px; border-radius: 50%; } .status-toggle.active .status-dot { background-color: #22c55e; } .status-toggle.inactive .status-dot { background-color: #ef4444; }
.action-group { display: flex; gap: 3px; }
.action-btn { display: flex; align-items: center; justify-content: center; width: 30px; height: 30px; border: 1px solid #e5e7eb; border-radius: 5px; background: white; color: #6b7280; cursor: pointer; transition: all 0.15s; }
.action-btn:hover { background-color: var(--subtle-blue, #eef1fd); border-color: var(--primary-color, #4056b7); color: var(--primary-color, #4056b7); }
.action-delete { color: #dc2626; } .action-delete:hover { background-color: #fef2f2; border-color: #dc2626; color: #b91c1c; }

.pagination { display: flex; align-items: center; justify-content: center; gap: 4px; padding: 14px 16px; background-color: #f9fafb; border-top: 1px solid #e5e7eb; }
.page-btn { padding: 6px 12px; border: 1px solid #d1d5db; border-radius: 4px; background: white; font-size: 13px; color: #374151; cursor: pointer; }
.page-btn:hover:not(:disabled):not(.active) { background-color: #f3f4f6; }
.page-btn.active { background-color: var(--primary-color, #4056b7); border-color: var(--primary-color, #4056b7); color: white; }
.page-btn:disabled { opacity: 0.4; cursor: not-allowed; } .page-ellipsis { padding: 6px 8px; color: #9ca3af; }

/* 모달 공통 */
.modal-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 9999; animation: fadeIn 0.15s ease; }
.modal { background: white; border-radius: 12px; width: 90%; max-width: 520px; box-shadow: 0 20px 60px rgba(0,0,0,0.15); animation: slideUp 0.2s ease; }
.modal-wide { max-width: 640px; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 20px 24px; border-bottom: 1px solid #e5e7eb; }
.modal-title { font-size: 18px; font-weight: 600; color: #1f2937; margin: 0; }
.modal-close { display: flex; align-items: center; justify-content: center; width: 32px; height: 32px; border: none; border-radius: 6px; background: none; color: #9ca3af; cursor: pointer; } .modal-close:hover { background-color: #f3f4f6; color: #374151; }
.modal-body { padding: 24px; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.form-field { display: flex; flex-direction: column; gap: 6px; }
.form-field label { font-size: 13px; font-weight: 500; color: #374151; } .required { color: #ef4444; }
.form-field input, .form-select { padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px; outline: none; transition: border-color 0.2s; }
.form-field input:focus, .form-select:focus { border-color: var(--primary-color, #4056b7); box-shadow: 0 0 0 2px rgba(64,86,183,0.1); }
.form-select { background: white; cursor: pointer; }
.field-disabled { background-color: #f9fafb; color: #9ca3af; cursor: not-allowed; }
.field-error { font-size: 12px; color: #ef4444; }
.modal-footer { display: flex; justify-content: flex-end; gap: 8px; margin-top: 24px; padding-top: 16px; border-top: 1px solid #f3f4f6; }
.btn-cancel { padding: 8px 16px; border: 1px solid #d1d5db; border-radius: 6px; background: white; font-size: 13px; color: #374151; cursor: pointer; } .btn-cancel:hover { background-color: #f3f4f6; }
.btn-primary { padding: 8px 20px; border: none; border-radius: 6px; background-color: var(--primary-color, #4056b7); color: white; font-size: 13px; font-weight: 500; cursor: pointer; }
.btn-primary:hover:not(:disabled) { background-color: var(--dark-blue, #3949ab); } .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }

/* 업로드 모달 */
.upload-zone { border: 2px dashed #d1d5db; border-radius: 10px; padding: 32px; text-align: center; cursor: pointer; transition: all 0.2s; }
.upload-zone:hover, .upload-zone.dragover { border-color: var(--primary-color, #4056b7); background-color: rgba(64,86,183,0.04); }
.upload-icon-large { font-size: 36px; margin-bottom: 8px; }
.upload-placeholder p { color: #6b7280; margin: 4px 0; } .upload-placeholder small { color: #9ca3af; }
.upload-file-info { display: flex; align-items: center; gap: 8px; justify-content: center; }
.file-name { font-weight: 500; color: #1f2937; } .file-size { color: #9ca3af; font-size: 13px; }
.file-remove { background: none; border: none; color: #ef4444; cursor: pointer; font-size: 16px; padding: 2px 6px; border-radius: 4px; } .file-remove:hover { background-color: #fef2f2; }
.upload-preview { margin-top: 16px; }
.preview-count { font-size: 13px; color: #059669; font-weight: 500; margin-bottom: 8px; }
.preview-table-wrap { max-height: 200px; overflow-y: auto; border: 1px solid #e5e7eb; border-radius: 6px; }
.preview-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.preview-table th { background: #f9fafb; padding: 8px 12px; text-align: left; font-weight: 600; color: #6b7280; border-bottom: 1px solid #e5e7eb; }
.preview-table td { padding: 6px 12px; border-bottom: 1px solid #f3f4f6; color: #374151; }
.preview-more { text-align: center; color: #9ca3af; font-style: italic; }

/* 토스트 */
.toast { position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%); padding: 10px 20px; border-radius: 8px; font-size: 13px; font-weight: 500; color: white; z-index: 10000; box-shadow: 0 8px 24px rgba(0,0,0,0.15); }
.toast-success { background-color: #059669; } .toast-error { background-color: #dc2626; }
.toast-enter-active, .toast-leave-active { transition: all 0.3s ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateX(-50%) translateY(12px); }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes slideUp { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }

@media (max-width: 768px) {
  .admin-user-management { padding: 16px; margin: 10px; }
  .page-header { flex-direction: column; gap: 16px; }
  .toolbar { flex-direction: column; } .search-box { width: 100%; } .toolbar-actions { width: 100%; justify-content: stretch; } .btn-action { flex: 1; justify-content: center; }
  .col-ip { display: none; } .form-grid { grid-template-columns: 1fr; } .page-title { font-size: 22px; }
}
</style>