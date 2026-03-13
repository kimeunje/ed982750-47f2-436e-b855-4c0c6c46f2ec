<template>
  <div class="admin-user-management">
    <!-- 헤더 -->
    <div class="admin-header">
      <div class="header-content">
        <div class="title-section">
          <h1>사용자 관리</h1>
          <p>전체 사용자의 보안 현황을 조회하고 관리합니다</p>
        </div>
        <div class="header-stats">
          <div class="stat-item">
            <span class="stat-label">전체 사용자</span>
            <span class="stat-value">{{ totalUsers }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">선택됨</span>
            <span class="stat-value">{{ selectedUsers.length }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 액션 버튼 섹션 -->
    <div class="action-buttons-section">
      <div class="button-group">
        <button @click="showAddUserModal = true" class="add-user-btn">
          <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
            <path
              d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4z"
            />
          </svg>
          사용자 추가
        </button>

        <button
          @click="exportSelected"
          :disabled="selectedUsers.length === 0"
          class="export-selected-btn"
        >
          <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
            <path
              d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"
            />
            <path
              d="M7.646 1.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1-.708.708L8.5 2.707V11.5a.5.5 0 0 1-1 0V2.707L5.354 4.854a.5.5 0 1 1-.708-.708l3-3z"
            />
          </svg>
          선택된 사용자 내보내기 ({{ selectedUsers.length }})
        </button>

        <button @click="exportAll" class="export-btn">
          <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
            <path
              d="M14 14V4.5L9.5 0H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2zM9.5 3A1.5 1.5 0 0 0 11 4.5h2V14a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1h5.5v2z"
            />
          </svg>
          전체 내보내기
        </button>
      </div>
    </div>

    <!-- 필터 및 검색 섹션 -->
    <div class="filters-section">
      <div class="filters-header">
        <h3>필터 및 검색</h3>
        <div class="filter-actions">
          <button @click="toggleFilters" class="toggle-btn">
            <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
              <path
                d="M6 10.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 0 1h-3a.5.5 0 0 1-.5-.5zm-2-3a.5.5 0 0 1 .5-.5h7a.5.5 0 0 1 0 1h-7a.5.5 0 0 1-.5-.5zm-2-3a.5.5 0 0 1 .5-.5h11a.5.5 0 0 1 0 1h-11a.5.5 0 0 1-.5-.5z"
              />
            </svg>
            {{ showFilters ? '필터 숨기기' : '필터 표시' }}
          </button>
          <button @click="applyFilters" class="apply-btn">적용</button>
          <button @click="resetFilters" class="reset-btn">초기화</button>
        </div>
      </div>

      <div v-if="showFilters" class="filters-content">
        <div class="filter-grid">
          <div class="filter-item">
            <label>년도</label>
            <select v-model="filters.year">
              <option v-for="year in yearOptions" :key="year" :value="year">{{ year }}년</option>
            </select>
          </div>

          <div class="filter-item">
            <label>부서</label>
            <select v-model="filters.department">
              <option value="">전체 부서</option>
              <option v-for="dept in departmentOptions" :key="dept" :value="dept">
                {{ dept }}
              </option>
            </select>
          </div>

          <div class="filter-item">
            <label>직급</label>
            <select v-model="filters.position">
              <option value="">전체 직급</option>
              <option v-for="pos in positionOptions" :key="pos" :value="pos">
                {{ pos }}
              </option>
            </select>
          </div>

          <div class="filter-item">
            <label>위험도</label>
            <select v-model="filters.riskLevel">
              <option value="">전체</option>
              <option value="low">우수 (80점 이상)</option>
              <option value="medium">주의 (60-79점)</option>
              <option value="high">위험 (40-59점)</option>
              <option value="critical">매우 위험 (40점 미만)</option>
              <option value="not_evaluated">미평가</option>
            </select>
          </div>

          <div class="filter-item full-width">
            <label>검색</label>
            <div class="search-input-container">
              <input
                v-model="filters.search"
                @input="onSearchInput"
                type="text"
                placeholder="이름, 사번, 이메일로 검색..."
                class="search-input"
              />
              <svg
                class="search-icon"
                width="16"
                height="16"
                fill="currentColor"
                viewBox="0 0 16 16"
              >
                <path
                  d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001c.03.04.062.078.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1.007 1.007 0 0 0-.115-.1zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0z"
                />
              </svg>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 데이터 테이블 -->
    <div class="table-section">
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner"></div>
        <p>사용자 데이터를 불러오는 중...</p>
      </div>

      <div v-else-if="error" class="error-state">
        <svg width="48" height="48" fill="currentColor" viewBox="0 0 16 16">
          <path
            d="M8.982 1.566a1.13 1.13 0 0 0-1.96 0L.165 13.233c-.457.778.091 1.767.98 1.767h13.713c.889 0 1.438-.99.98-1.767L8.982 1.566zM8 5c.535 0 .954.462.9.995l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 5.995A.905.905 0 0 1 8 5zm.002 6a1 1 0 1 1 0 2 1 1 0 0 1 0-2z"
          />
        </svg>
        <h3>데이터를 불러오지 못했습니다</h3>
        <p>{{ error }}</p>
        <button @click="loadUsers" class="retry-btn">다시 시도</button>
      </div>

      <div v-else class="table-container">
        <div class="table-header">
          <div class="table-controls">
            <div class="select-controls">
              <label class="checkbox-container">
                <input
                  type="checkbox"
                  :checked="isAllSelected"
                  :indeterminate="isPartiallySelected"
                  @change="toggleSelectAll"
                />
                <span class="checkmark"></span>
              </label>
              <span class="select-count">{{ selectedUsers.length }}개 선택됨</span>
            </div>

            <div class="sort-controls">
              <label>정렬:</label>
              <select v-model="filters.sortBy" @change="applyFilters">
                <option value="total_penalty">총 감점</option>
                <option value="name">이름</option>
                <option value="department">부서</option>
                <option value="updated_at">업데이트 시간</option>
              </select>
              <button @click="toggleSortOrder" class="sort-btn">
                <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                  <path
                    v-if="filters.sortOrder === 'asc'"
                    d="M7.247 11.14 2.451 5.658C1.885 5.013 2.345 4 3.204 4h9.592a1 1 0 0 1 .753 1.659l-4.796 5.48a1 1 0 0 1-1.506 0z"
                  />
                  <path
                    v-else
                    d="m7.247 4.86-4.796 5.481c-.566.647-.106 1.659.753 1.659h9.592a1 1 0 0 0 .753-1.659l-4.796-5.48a1 1 0 0 0-1.506 0z"
                  />
                </svg>
              </button>
            </div>
          </div>
        </div>

        <table class="users-table">
          <thead>
            <tr>
              <th class="checkbox-col">
                <input
                  type="checkbox"
                  :checked="isAllSelected"
                  :indeterminate="isPartiallySelected"
                  @change="toggleSelectAll"
                />
              </th>
              <th>이름</th>
              <th>부서</th>
              <th>이메일</th>
              <!-- ✅ 상태 열 추가 -->
              <th class="status-col">상태</th>
              <th>총 감점</th>
              <th>리스크 레벨</th>
              <th>최근 업데이트</th>
              <th class="actions-col">작업</th>
            </tr>
          </thead>
          <tbody>
            <!-- ✅ 비활성 사용자 행에 클래스 추가 -->
            <tr 
              v-for="user in users" 
              :key="user.uid"
              :class="{ 'inactive-user': !user.is_active }"
            >
              <td class="checkbox-col">
                <input
                  type="checkbox"
                  :value="user.uid"
                  v-model="selectedUsers"
                />
              </td>
              <td>
                <div class="user-info">
                  <span class="user-name">{{ user.name }}</span>
                  <span class="user-id">{{ user.employee_id }}</span>
                </div>
              </td>
              <td>{{ user.department }}</td>
              <td>{{ user.email }}</td>
              
              <!-- ✅ 상태 버튼 추가 -->
              <td class="status-col">
                <button
                  @click="toggleUserActive(user)"
                  :class="['status-badge', user.is_active ? 'active' : 'inactive']"
                  :title="user.is_active ? '클릭하여 비활성화' : '클릭하여 활성화'"
                >
                  {{ user.is_active ? '활성' : '비활성' }}
                </button>
              </td>
              
              <td>
                <span :class="['penalty-badge', getPenaltyClass(user.total_penalty)]">
                  {{ formatPenalty(user.total_penalty) }}점
                </span>
              </td>
              <td>
                <span :class="['risk-badge', getRiskClass(user.risk_level)]">
                  {{ user.risk_level }}
                </span>
              </td>
              <td>{{ formatDate(user.last_updated) }}</td>
              <td class="actions-col">
                <div class="action-buttons">
                  <button
                    @click="openEditUserModal(user)"
                    class="edit-btn"
                    title="수정"
                  >
                    <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
                      <path d="M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708L8.5 11.207l-3 1a.5.5 0 0 1-.604-.604l1-3L12.146.146zM11.207 2.5 13.5 4.793 14.793 3.5 12.5 1.207 11.207 2.5zm1.586 3L10.5 3.207 4 9.707V10h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.293l6.5-6.5zm-9.761 5.175-.106.106-1.528 3.821 3.821-1.528.106-.106A.5.5 0 0 1 5 12.5V12h-.5a.5.5 0 0 1-.5-.5V11h-.5a.5.5 0 0 1-.468-.325z"/>
                    </svg>
                  </button>
                  <button
                    @click="goToUserDetail(user.uid)"
                    class="detail-btn"
                    title="상세 보기"
                  >
                    <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
                      <path d="M8 4.754a3.246 3.246 0 1 0 0 6.492 3.246 3.246 0 0 0 0-6.492zM5.754 8a2.246 2.246 0 1 1 4.492 0 2.246 2.246 0 0 1-4.492 0z"/>
                      <path d="M9.796 1.343c-.527-1.79-3.065-1.79-3.592 0l-.094.319a.873.873 0 0 1-1.255.52l-.292-.16c-1.64-.892-3.433.902-2.54 2.541l.159.292a.873.873 0 0 1-.52 1.255l-.319.094c-1.79.527-1.79 3.065 0 3.592l.319.094a.873.873 0 0 1 .52 1.255l-.16.292c-.892 1.64.901 3.434 2.541 2.54l.292-.159a.873.873 0 0 1 1.255.52l.094.319c.527 1.79 3.065 1.79 3.592 0l.094-.319a.873.873 0 0 1 1.255-.52l.292.16c1.64.893 3.434-.902 2.54-2.541l-.159-.292a.873.873 0 0 1 .52-1.255l.319-.094c1.79-.527 1.79-3.065 0-3.592l-.319-.094a.873.873 0 0 1-.52-1.255l.16-.292c.893-1.64-.902-3.433-2.541-2.54l-.292.159a.873.873 0 0 1-1.255-.52l-.094-.319zm-2.633.283c.246-.835 1.428-.835 1.674 0l.094.319a1.873 1.873 0 0 0 2.693 1.115l.291-.16c.764-.415 1.6.42 1.184 1.185l-.159.292a1.873 1.873 0 0 0 1.116 2.692l.318.094c.835.246.835 1.428 0 1.674l-.319.094a1.873 1.873 0 0 0-1.115 2.693l.16.291c.415.764-.42 1.6-1.185 1.184l-.291-.159a1.873 1.873 0 0 0-2.693 1.116l-.094.318c-.246.835-1.428.835-1.674 0l-.094-.319a1.873 1.873 0 0 0-2.692-1.115l-.292.16c-.764.415-1.6-.42-1.184-1.185l.159-.291A1.873 1.873 0 0 0 1.945 8.93l-.319-.094c-.835-.246-.835-1.428 0-1.674l.319-.094A1.873 1.873 0 0 0 3.06 4.377l-.16-.292c-.415-.764.42-1.6 1.185-1.184l.292.159a1.873 1.873 0 0 0 2.692-1.115l.094-.319z"/>
                    </svg>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 페이지네이션 -->
    <div v-if="pagination && totalUsers > 0" class="pagination-section">
      <div class="pagination-info">
        <span>
          {{ (pagination.current_page - 1) * pagination.per_page + 1 }} -
          {{ Math.min(pagination.current_page * pagination.per_page, totalUsers) }} /
          {{ totalUsers }}
        </span>
      </div>

      <div class="pagination-controls">
        <button
          @click="changePage(pagination.current_page - 1)"
          :disabled="pagination.current_page <= 1"
          class="page-btn"
        >
          이전
        </button>

        <div class="page-numbers">
          <button
            v-for="page in paginationPages"
            :key="page"
            @click="changePage(page)"
            :class="{ active: page === pagination.current_page }"
            class="page-btn"
          >
            {{ page }}
          </button>
        </div>

        <button
          @click="changePage(pagination.current_page + 1)"
          :disabled="pagination.current_page >= pagination.total_pages"
          class="page-btn"
        >
          다음
        </button>
      </div>

      <div class="per-page-selector">
        <label>페이지당:</label>
        <select v-model="filters.perPage" @change="applyFilters">
          <option value="10">10개</option>
          <option value="20">20개</option>
          <option value="50">50개</option>
          <option value="100">100개</option>
        </select>
      </div>
    </div>

    <!-- 사용자 추가 모달 -->
    <div v-if="showAddUserModal" class="modal-overlay" @click="closeAddUserModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>새 사용자 추가</h2>
          <button @click="closeAddUserModal" class="modal-close-btn">
            <svg width="20" height="20" fill="currentColor" viewBox="0 0 16 16">
              <path
                d="M.293.293a1 1 0 0 1 1.414 0L8 6.586 14.293.293a1 1 0 1 1 1.414 1.414L9.414 8l6.293 6.293a1 1 0 0 1-1.414 1.414L8 9.414l-6.293 6.293a1 1 0 0 1-1.414-1.414L6.586 8 .293 1.707a1 1 0 0 1 0-1.414z"
              />
            </svg>
          </button>
        </div>

        <form @submit.prevent="addUser" class="modal-form">
          <div class="form-row">
            <div class="form-group">
              <label for="new-name">이름 *</label>
              <input
                id="new-name"
                v-model="newUser.name"
                type="text"
                required
                :class="{ error: newUserErrors.name }"
                placeholder="사용자 실명을 입력하세요"
              />
              <span v-if="newUserErrors.name" class="error-message">{{ newUserErrors.name }}</span>
            </div>

            <div class="form-group">
              <label for="new-email">이메일 *</label>
              <input
                id="new-email"
                v-model="newUser.email"
                type="email"
                required
                :class="{ error: newUserErrors.email }"
                placeholder="example@company.com"
              />
              <span v-if="newUserErrors.email" class="error-message">{{
                newUserErrors.email
              }}</span>
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label for="new-ip">IP 주소 *</label>
              <input
                id="new-ip"
                v-model="newUser.ip"
                type="text"
                required
                :class="{ error: newUserErrors.ip }"
                placeholder="192.168.1.100 (여러 개는 쉼표로 구분)"
              />
              <span v-if="newUserErrors.ip" class="error-message">{{ newUserErrors.ip }}</span>
            </div>

            <div class="form-group">
              <label for="new-department">부서 *</label>
              <input
                id="new-department"
                v-model="newUser.department"
                type="text"
                required
                :class="{ error: newUserErrors.department }"
                placeholder="소속 부서를 입력하세요"
              />
              <span v-if="newUserErrors.department" class="error-message">{{
                newUserErrors.department
              }}</span>
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label for="new-role">권한</label>
              <select id="new-role" v-model="newUser.role">
                <option value="user">일반 사용자</option>
                <option value="admin">관리자</option>
              </select>
            </div>

            <div class="form-group">
              <label for="new-notes">메모</label>
              <input
                id="new-notes"
                v-model="newUser.notes"
                type="text"
                placeholder="추가 메모 (선택사항)"
              />
            </div>
          </div>

          <div class="modal-actions">
            <button type="button" @click="closeAddUserModal" class="cancel-btn">취소</button>
            <button type="submit" :disabled="addUserLoading" class="submit-btn">
              {{ addUserLoading ? '추가 중...' : '사용자 추가' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- 사용자 수정 모달 -->
    <div v-if="showEditUserModal" class="modal-overlay" @click="closeEditUserModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>사용자 정보 수정</h2>
          <button @click="closeEditUserModal" class="modal-close-btn">
            <svg width="20" height="20" fill="currentColor" viewBox="0 0 16 16">
              <path
                d="M.293.293a1 1 0 0 1 1.414 0L8 6.586 14.293.293a1 1 0 1 1 1.414 1.414L9.414 8l6.293 6.293a1 1 0 0 1-1.414 1.414L8 9.414l-6.293 6.293a1 1 0 0 1-1.414-1.414L6.586 8 .293 1.707a1 1 0 0 1 0-1.414z"
              />
            </svg>
          </button>
        </div>

        <form @submit.prevent="updateUser" class="modal-form">
          <div class="form-row">
            <div class="form-group">
              <label for="edit-name">이름 *</label>
              <input
                id="edit-name"
                v-model="editingUser.name"
                type="text"
                required
                :class="{ error: editUserErrors.name }"
                placeholder="사용자 실명을 입력하세요"
              />
              <span v-if="editUserErrors.name" class="error-message">{{
                editUserErrors.name
              }}</span>
            </div>

            <div class="form-group">
              <label for="edit-ip">IP 주소 *</label>
              <input
                id="edit-ip"
                v-model="editingUser.ip"
                type="text"
                required
                :class="{ error: editUserErrors.ip }"
                placeholder="192.168.1.100 (여러 개는 쉼표로 구분)"
              />
              <span v-if="editUserErrors.ip" class="error-message">{{ editUserErrors.ip }}</span>
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label for="edit-email">이메일 (읽기전용)</label>
              <input
                id="edit-email"
                v-model="editingUser.email"
                type="email"
                disabled
                class="disabled-field"
              />
              <small class="field-help">이메일은 수정할 수 없습니다</small>
            </div>

            <div class="form-group">
              <label for="edit-department">부서 (읽기전용)</label>
              <input
                id="edit-department"
                v-model="editingUser.department"
                type="text"
                disabled
                class="disabled-field"
              />
              <small class="field-help">부서는 수정할 수 없습니다</small>
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label for="edit-user-id">사번 (읽기전용)</label>
              <input
                id="edit-user-id"
                v-model="editingUser.user_id"
                type="text"
                disabled
                class="disabled-field"
              />
              <small class="field-help">사번은 자동 생성됩니다</small>
            </div>

            <div class="form-group">
              <label for="edit-role">권한 (읽기전용)</label>
              <select id="edit-role" v-model="editingUser.role" disabled class="disabled-field">
                <option value="user">일반 사용자</option>
                <option value="admin">관리자</option>
              </select>
              <small class="field-help">권한은 수정할 수 없습니다</small>
            </div>
          </div>

          <div class="modal-actions">
            <button type="button" @click="closeEditUserModal" class="cancel-btn">취소</button>
            <button type="submit" :disabled="editUserLoading" class="submit-btn">
              {{ editUserLoading ? '수정 중...' : '수정 완료' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

// 기존 상태
const users = ref([])
const selectedUsers = ref([])
const loading = ref(false)
const error = ref('')
const showFilters = ref(false)
const pagination = ref(null)
const departmentOptions = ref([])
const positionOptions = ref([])

// 사용자 추가 관련 상태
const showAddUserModal = ref(false)
const addUserLoading = ref(false)
const newUser = ref({
  name: '',
  email: '',
  ip: '',
  department: '',
  role: 'user',
  is_active: true,
  notes: '',
})
const newUserErrors = ref({})

// 사용자 수정 관련 상태 (새로 추가)
const showEditUserModal = ref(false)
const editUserLoading = ref(false)
const editingUser = ref({
  uid: null,
  name: '',
  email: '',
  ip: '',
  department: '',
  user_id: '',
  role: 'user',
})
const editUserErrors = ref({})

// 필터 상태
const filters = ref({
  year: new Date().getFullYear(),
  department: '',
  position: '',
  riskLevel: '',
  search: '',
  sortBy: 'total_penalty',
  sortOrder: 'desc',
  page: 1,
  perPage: 20,
})

// 검색 디바운스
let searchTimeout = null

// 연도 옵션
const yearOptions = computed(() => {
  const currentYear = new Date().getFullYear()
  return Array.from({ length: 5 }, (_, i) => currentYear - i)
})

// 계산된 속성들
const totalUsers = computed(() => pagination.value?.total_count || 0)

const isAllSelected = computed(() => {
  return users.value.length > 0 && selectedUsers.value.length === users.value.length
})

const isPartiallySelected = computed(() => {
  return selectedUsers.value.length > 0 && selectedUsers.value.length < users.value.length
})

const paginationPages = computed(() => {
  if (!pagination.value) return []

  const current = pagination.value.current_page
  const total = pagination.value.total_pages
  const pages = []

  if (total <= 7) {
    for (let i = 1; i <= total; i++) {
      pages.push(i)
    }
  } else {
    if (current <= 4) {
      pages.push(1, 2, 3, 4, 5, '...', total)
    } else if (current >= total - 3) {
      pages.push(1, '...', total - 4, total - 3, total - 2, total - 1, total)
    } else {
      pages.push(1, '...', current - 1, current, current + 1, '...', total)
    }
  }

  return pages
})

// 사용자 관리 API
const userApi = {
  async loadUsers() {
    const params = new URLSearchParams({
      year: filters.value.year,
      page: filters.value.page,
      per_page: filters.value.perPage,
      sort_by: filters.value.sortBy,
      sort_order: filters.value.sortOrder,
    })

    if (filters.value.department) params.append('department', filters.value.department)
    if (filters.value.position) params.append('position', filters.value.position)
    if (filters.value.riskLevel) params.append('risk_level', filters.value.riskLevel)
    if (filters.value.search) params.append('search', filters.value.search)

    const response = await fetch(`/api/admin/dashboard/users?${params}`, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${authStore.token}`,
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    return await response.json()
  },

  async addUser(userData) {
    const response = await fetch('/api/admin/users', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${authStore.token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`)
    }

    return await response.json()
  },

  async updateUser(userId, userData) {
    const response = await fetch(`/api/admin/users/${userId}`, {
      method: 'PUT',
      headers: {
        Authorization: `Bearer ${authStore.token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`)
    }

    return await response.json()
  },

  async exportUsers(selectedOnly = false) {
    const params = new URLSearchParams({
      year: filters.value.year,
      sort_by: filters.value.sortBy,
      sort_order: filters.value.sortOrder,
    })

    if (selectedOnly && selectedUsers.value.length > 0) {
      params.append('user_ids', selectedUsers.value.join(','))
    }

    if (filters.value.department) params.append('department', filters.value.department)
    if (filters.value.position) params.append('position', filters.value.position)
    if (filters.value.riskLevel) params.append('risk_level', filters.value.riskLevel)
    if (filters.value.search) params.append('search', filters.value.search)

    const response = await fetch(`/api/admin/dashboard/export?${params}`, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${authStore.token}`,
      },
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    return response
  },
}

// 사용자 관리 함수들
const loadUsers = async () => {
  console.log('=== loadUsers 시작 ===')
  loading.value = true
  error.value = ''

  try {
    const response = await userApi.loadUsers()
    console.log('API 응답:', response)
    
    // ✅ 데이터 정규화: total_penalty를 숫자로 변환
    users.value = (response.users || []).map(user => ({
      ...user,
      is_active: user.is_active !== undefined ? user.is_active : true,
      total_penalty: parseFloat(user.total_penalty) || 0,  // ← 숫자로 변환
      audit_penalty: parseFloat(user.audit_penalty) || 0,
      education_penalty: parseFloat(user.education_penalty) || 0,
      training_penalty: parseFloat(user.training_penalty) || 0,
    }))
    
    console.log('정규화된 users.value:', users.value)
    
    pagination.value = response.pagination
    departmentOptions.value = response.department_options || []
    positionOptions.value = response.position_options || []

    selectedUsers.value = []
    
    console.log('=== loadUsers 완료 ===')
  } catch (err) {
    console.error('사용자 데이터 로드 실패:', err)
    error.value = err.message
  } finally {
    loading.value = false
  }
}

// 사용자 추가 관련 함수들
function resetNewUser() {
  newUser.value = {
    name: '',
    email: '',
    ip: '',
    department: '',
    role: 'user',
    is_active: true,
    notes: '',
  }
  newUserErrors.value = {}
}

function closeAddUserModal() {
  showAddUserModal.value = false
  resetNewUser()
}

function validateNewUser() {
  const errors = {}

  if (!newUser.value.name.trim()) {
    errors.name = '이름은 필수입니다.'
  }

  if (!newUser.value.ip.trim()) {
    errors.ip = 'IP 주소는 필수입니다.'
  } else {
    const ipAddresses = newUser.value.ip.split(',').map((ip) => ip.trim())
    const ipPattern =
      /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/

    for (const ip of ipAddresses) {
      if (!ipPattern.test(ip)) {
        errors.ip = `올바르지 않은 IP 주소 형식입니다: ${ip}`
        break
      }
    }
  }

  if (!newUser.value.email.trim()) {
    errors.email = '이메일은 필수입니다.'
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(newUser.value.email)) {
    errors.email = '올바른 이메일 형식을 입력해주세요.'
  }

  if (!newUser.value.department.trim()) {
    errors.department = '부서는 필수입니다.'
  }

  newUserErrors.value = errors
  return Object.keys(errors).length === 0
}

const addUser = async () => {
  if (!validateNewUser()) return

  addUserLoading.value = true
  try {
    const response = await userApi.addUser(newUser.value)

    // 성공 메시지 표시 (실제 앱에서는 토스트나 알림으로 대체)
    alert(response.message || '사용자가 성공적으로 추가되었습니다.')

    closeAddUserModal()
    await loadUsers() // 목록 새로고침
  } catch (err) {
    console.error('사용자 추가 실패:', err)
    alert(`사용자 추가 실패: ${err.message}`)
  } finally {
    addUserLoading.value = false
  }
}

// 사용자 수정 관련 함수들 (새로 추가)
// 사용자 수정 관련 함수들
const openEditUserModal = (user) => {
  editingUser.value = {
    uid: user.uid,
    name: user.name || user.username,
    email: user.email || user.mail,
    ip: user.ip || '',
    department: user.department || '',
    user_id: user.user_id || '',
    role: user.role || 'user',
  }
  editUserErrors.value = {}
  showEditUserModal.value = true
}

const closeEditUserModal = () => {
  showEditUserModal.value = false
  editingUser.value = {
    uid: null,
    name: '',
    email: '',
    ip: '',
    department: '',
    user_id: '',
    role: 'user',
  }
  editUserErrors.value = {}
}

const validateEditUser = () => {
  const errors = {}

  if (!editingUser.value.name.trim()) {
    errors.name = '이름은 필수입니다.'
  }

  if (!editingUser.value.ip.trim()) {
    errors.ip = 'IP 주소는 필수입니다.'
  } else {
    const ipAddresses = editingUser.value.ip.split(',').map((ip) => ip.trim())
    const ipPattern =
      /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/

    for (const ip of ipAddresses) {
      if (!ipPattern.test(ip)) {
        errors.ip = `올바르지 않은 IP 주소 형식입니다: ${ip}`
        break
      }
    }
  }

  editUserErrors.value = errors
  return Object.keys(errors).length === 0
}

const updateUser = async () => {
  if (!validateEditUser()) return

  editUserLoading.value = true
  try {
    const updateData = {
      name: editingUser.value.name.trim(),
      ip: editingUser.value.ip.trim(),
    }

    const response = await userApi.updateUser(editingUser.value.uid, updateData)
    alert(response.message || '사용자 정보가 성공적으로 수정되었습니다.')
    
    closeEditUserModal()
    await loadUsers()
  } catch (err) {
    console.error('사용자 수정 실패:', err)
    alert(`사용자 수정 실패: ${err.message}`)
  } finally {
    editUserLoading.value = false
  }
}

// ============================================
// 사용자 활성화/비활성화 토글 함수
// ============================================
// ✅ 5. toggleUserActive 함수에서도 데이터 정규화
const toggleUserActive = async (user) => {
  const action = user.is_active ? '비활성화' : '활성화'
  const statusMessage = user.is_active 
    ? '비활성화된 사용자는 로그인할 수 없습니다.' 
    : '활성화된 사용자는 로그인할 수 있습니다.'
  
  if (!confirm(`${user.name} 사용자를 ${action}하시겠습니까?\n\n${statusMessage}`)) {
    return
  }

  try {
    const response = await fetch(`/api/admin/users/${user.uid}/toggle-active`, {
      method: 'PATCH',
      headers: {
        Authorization: `Bearer ${authStore.token}`,
        'Content-Type': 'application/json',
      },
    })

    const result = await response.json()

    if (!response.ok || !result.success) {
      throw new Error(result.message || `사용자 ${action} 실패`)
    }

    console.log('Toggle result:', result)

    // ✅ 즉시 로컬 상태 업데이트 (숫자 타입 유지)
    users.value = users.value.map(u => 
      u.uid === user.uid 
        ? { 
            ...u, 
            is_active: result.is_active,
            total_penalty: parseFloat(u.total_penalty) || 0  // ← 숫자 타입 보장
          }
        : u
    )
    
    alert(result.message)
    await loadUsers()
    
  } catch (err) {
    console.error(`사용자 ${action} 실패:`, err)
    alert(err.message)
    await loadUsers()
  }
}


// 기존 함수들 (변경 없음)
const goToUserDetail = (userId) => {
  router.push({ name: 'AdminUserDetail', params: { userId } })
}

const toggleFilters = () => {
  showFilters.value = !showFilters.value
}

const applyFilters = () => {
  filters.value.page = 1
  loadUsers()
}

const resetFilters = () => {
  filters.value = {
    year: new Date().getFullYear(),
    department: '',
    position: '',
    riskLevel: '',
    search: '',
    sortBy: 'total_penalty',
    sortOrder: 'desc',
    page: 1,
    perPage: 20,
  }
  applyFilters()
}

const changePage = (page) => {
  if (page >= 1 && page <= pagination.value.total_pages) {
    filters.value.page = page
    loadUsers()
  }
}

const toggleSortOrder = () => {
  filters.value.sortOrder = filters.value.sortOrder === 'asc' ? 'desc' : 'asc'
  applyFilters()
}

const toggleSelectAll = () => {
  if (isAllSelected.value) {
    selectedUsers.value = []
  } else {
    selectedUsers.value = users.value.map((user) => user.uid)
  }
}

const onSearchInput = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    applyFilters()
  }, 500)
}

const exportSelected = async () => {
  if (selectedUsers.value.length === 0) return

  try {
    const response = await userApi.exportUsers(true)
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.style.display = 'none'
    a.href = url
    a.download = `사용자_보안현황_선택항목_${new Date().toISOString().split('T')[0]}.xlsx`
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
  } catch (err) {
    console.error('내보내기 실패:', err)
    alert('내보내기에 실패했습니다.')
  }
}

const exportAll = async () => {
  try {
    const response = await userApi.exportUsers(false)
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.style.display = 'none'
    a.href = url
    a.download = `사용자_보안현황_전체_${new Date().toISOString().split('T')[0]}.xlsx`
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
  } catch (err) {
    console.error('내보내기 실패:', err)
    alert('내보내기에 실패했습니다.')
  }
}

// 유틸리티 함수들
const getRiskLabel = (riskLevel) => {
  const labels = {
    low: '우수',
    medium: '주의',
    high: '위험',
    critical: '매우 위험',
    not_evaluated: '미평가',
  }
  return labels[riskLevel] || '미평가'
}

// ✅ 2. getPenaltyClass 함수 수정
const getPenaltyClass = (penalty) => {
  const penaltyNum = parseFloat(penalty)
  if (isNaN(penaltyNum) || penaltyNum === 0) return 'penalty-perfect'
  if (penaltyNum <= 1.0) return 'penalty-low'
  if (penaltyNum <= 2.5) return 'penalty-medium'
  return 'penalty-high'
}

// ✅ 3. getRiskClass 함수도 안전하게 처리
const getRiskClass = (riskLevel) => {
  if (!riskLevel) return 'risk-none'
  return `risk-${riskLevel}`
}


// ✅ 1. 헬퍼 함수 추가 (script setup 부분 맨 위)
const formatPenalty = (penalty) => {
  const num = parseFloat(penalty)
  return isNaN(num) ? '0.0' : num.toFixed(1)
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  try {
    const date = new Date(dateString)
    if (isNaN(date.getTime())) return '-'
    return date.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    })
  } catch (e) {
    return '-'
  }
}

// const formatDate = (dateString) => {
//   if (!dateString) return '-'
//   const date = new Date(dateString)
//   if (isNaN(date.getTime())) return '-'
//   return date.toLocaleDateString('ko-KR')
// }

const formatTime = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  if (isNaN(date.getTime())) return '-'
  return date.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })
}

const isAdmin = () => {
  return authStore.user?.role === 'admin'
}

const validateFilters = () => {
  if (!filters.value.year) {
    filters.value.year = new Date().getFullYear()
  }
}

// 키보드 단축키
const handleKeydown = (event) => {
  if (showAddUserModal.value || showEditUserModal.value) return

  if (event.ctrlKey && event.key === 'a' && !event.target.matches('input, textarea')) {
    event.preventDefault()
    toggleSelectAll()
  }

  if (event.ctrlKey && event.key === 'e' && selectedUsers.value.length > 0) {
    event.preventDefault()
    exportSelected()
  }

  if (event.ctrlKey && event.key === 'n') {
    event.preventDefault()
    showAddUserModal.value = true
  }

  if (event.key === 'F5') {
    event.preventDefault()
    loadUsers()
  }

  if (event.key === 'Escape') {
    if (showAddUserModal.value) {
      closeAddUserModal()
    } else if (showEditUserModal.value) {
      closeEditUserModal()
    }
  }
}

// 라이프사이클
watch(
  () => filters.value.year,
  () => {
    if (filters.value.year) {
      applyFilters()
    }
  },
)

watch(
  () => authStore.user,
  (newUser) => {
    if (!newUser || !isAdmin()) {
      router.push('/login')
    }
  },
  { immediate: true },
)

onMounted(() => {
  if (authStore.isAuthenticated && isAdmin()) {
    validateFilters()
    loadUsers()
  }

  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  clearTimeout(searchTimeout)
})
</script>

<style scoped>
@import '../styles/AdminUserManagement.css';

/* 사용자 수정 모달 관련 추가 스타일 */
.disabled-field {
  background-color: #f5f5f5 !important;
  color: #6b7280 !important;
  cursor: not-allowed !important;
}

.field-help {
  color: #6b7280;
  font-size: 0.75rem;
  margin-top: 0.25rem;
  display: block;
}

.modal-form .form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 1rem;
}

.modal-form .form-group {
  display: flex;
  flex-direction: column;
}

.modal-form .form-group label {
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #374151;
}

.modal-form .form-group input,
.modal-form .form-group select {
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.875rem;
}

.modal-form .form-group input:focus,
.modal-form .form-group select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.modal-form .form-group input.error {
  border-color: #ef4444;
}

.error-message {
  color: #ef4444;
  font-size: 0.75rem;
  margin-top: 0.25rem;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 2rem;
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
}

.cancel-btn {
  padding: 0.75rem 1.5rem;
  background-color: #f3f4f6;
  color: #374151;
  border: none;
  border-radius: 0.375rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.cancel-btn:hover {
  background-color: #e5e7eb;
}

.submit-btn {
  padding: 0.75rem 1.5rem;
  background-color: #3b82f6;
  color: white;
  border: none;
  border-radius: 0.375rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.submit-btn:hover:not(:disabled) {
  background-color: #2563eb;
}

.submit-btn:disabled {
  background-color: #9ca3af;
  cursor: not-allowed;
}

.edit-btn {
  background-color: #f59e0b;
  color: white;
  border: none;
  border-radius: 0.25rem;
  padding: 0.5rem;
  cursor: pointer;
  transition: background-color 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.edit-btn:hover {
  background-color: #d97706;
}

.action-buttons {
  display: flex;
  gap: 0.5rem;
}
</style>
