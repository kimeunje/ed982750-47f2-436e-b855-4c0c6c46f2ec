<!-- ManualCheckManagement.vue - Template 부분 -->
<template>
  <div class="admin-training">
    <div class="admin-header">
      <h1>수시 점검 관리</h1>
      <div class="admin-nav">
        <RouterLink to="/admin/training" class="nav-item">모의훈련 관리</RouterLink>
        <RouterLink to="/admin/manual-check" class="nav-item active">점검 관리</RouterLink>
        <RouterLink to="/admin/exceptions" class="nav-item">제외 설정</RouterLink>
      </div>
    </div>
    <!-- 토글형 기간 설정 섹션 -->
    <div class="period-management-section">
      <div class="section-header toggleable" @click="togglePeriodSection">
        <h3>
          <span class="toggle-icon" :class="{ collapsed: !showPeriodSection }">▼</span>
          🗓️ 점검 기간 관리
          <span class="section-subtitle">{{ getPeriodsCountText() }}</span>
        </h3>
        <button @click.stop="openPeriodModal" class="primary-button" v-if="showPeriodSection">
          <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
            <path
              d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4z"
            />
          </svg>
          기간 추가
        </button>
      </div>

      <!-- 토글 가능한 기간 관리 컨텐츠 -->
      <div class="period-content" v-show="showPeriodSection">
        <!-- 점검 유형별 기간 현황 카드 -->
        <div class="check-types-grid" v-if="periodStatus.check_types">
          <div
            v-for="(typeData, checkType) in periodStatus.check_types"
            :key="checkType"
            class="check-type-section"
          >
            <div class="type-header">
              <h4>{{ getCheckTypeName(checkType) }} 점검</h4>
              <div class="type-summary">
                <span class="summary-badge"> {{ typeData.periods?.length || 0 }}개 기간 </span>
              </div>
            </div>

            <!-- 기간 카드들 -->
            <div class="periods-grid">
              <div
                v-for="period in typeData.periods"
                :key="period.period_id"
                class="period-card"
                :class="[`status-${period.status}`, { completed: period.is_completed }]"
              >
                <div class="card-header">
                  <h5>{{ period.period_name }}</h5>
                  <div class="status-badges">
                    <span class="status-badge" :class="period.status">
                      {{ getStatusText(period.status) }}
                    </span>
                    <span v-if="period.is_completed" class="completion-badge">완료</span>
                  </div>
                </div>

                <div class="card-content">
                  <div class="period-info">
                    <p><strong>기간:</strong> {{ period.start_date }} ~ {{ period.end_date }}</p>
                    <p v-if="period.description"><strong>설명:</strong> {{ period.description }}</p>
                    <p v-if="period.completed_at">
                      <strong>완료 시각:</strong> {{ formatDateTime(period.completed_at) }}
                    </p>
                    <p v-if="period.completed_by">
                      <strong>완료 처리자:</strong> {{ period.completed_by }}
                    </p>
                  </div>

                  <div class="stats" v-if="period.stats">
                    <div class="stat pass">
                      <span>통과</span>
                      <strong>{{ period.stats.pass_count || 0 }}</strong>
                    </div>
                    <div class="stat fail">
                      <span>실패</span>
                      <strong>{{ period.stats.fail_count || 0 }}</strong>
                    </div>
                    <div class="stat total">
                      <span>전체</span>
                      <strong>{{ period.stats.total_users || 0 }}</strong>
                    </div>
                  </div>

                  <!-- 새로 추가되는 액션 버튼들 -->
                  <div class="card-actions">
                    <!-- 수정 버튼 -->
                    <button
                      @click="editPeriod(period)"
                      class="edit-button"
                      :disabled="period.is_completed"
                      title="기간 수정"
                    >
                      <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
                        <path
                          d="M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708L14.5 5.207l-3-3L12.146.146zM11.207 1.5L1.5 11.207V14.5h3.293L14.5 4.793l-3.293-3.293z"
                        />
                      </svg>
                      수정
                    </button>

                    <!-- 완료 버튼 (종료된 기간에만 표시) -->
                    <button
                      @click="completePeriod(period.period_id)"
                      class="btn btn-success btn-sm"
                      :disabled="period.is_completed"
                      title="기간을 완료하고 미실시 사용자를 자동 통과 처리합니다"
                    >
                      <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
                        <path
                          d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"
                        />
                      </svg>
                      완료
                    </button>

                    <!-- 재개 버튼 (완료된 기간에만 표시) -->
                    <button
                      v-if="period.is_completed"
                      @click="reopenPeriod(period.period_id)"
                      class="reopen-button"
                      title="완료 상태 취소"
                    >
                      <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
                        <path d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2v1z" />
                        <path
                          d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466z"
                        />
                      </svg>
                      재개
                    </button>

                    <!-- 삭제 버튼 -->
                    <button
                      @click="deletePeriod(period.period_id)"
                      class="delete-button"
                      :disabled="
                        period.is_completed && period.stats && period.stats.total_users > 0
                      "
                      title="기간 삭제"
                    >
                      <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
                        <path
                          d="M6.5 1h3a.5.5 0 0 1 .5.5v1H6v-1a.5.5 0 0 1 .5-.5ZM11 2.5v-1A1.5 1.5 0 0 0 9.5 0h-3A1.5 1.5 0 0 0 5 1.5v1H2.506a.58.58 0 0 0-.01 0H1.5a.5.5 0 0 0 0 1h.538l.853 10.66A2 2 0 0 0 4.885 16h6.23a2 2 0 0 0 1.994-1.84L14.962 3.5H15.5a.5.5 0 0 0 0-1h-1.004a.58.58 0 0 0-.01 0H11Zm1.958 1-.846 10.58a1 1 0 0 1-.997.92h-6.23a1 1 0 0 1-.997-.92L3.042 3.5h9.916Zm-7.487 1a.5.5 0 0 1 .528.47l.5 8.5a.5.5 0 0 1-.998.06L5 5.03a.5.5 0 0 1 .47-.53Zm5.058 0a.5.5 0 0 1 .47.53l-.5 8.5a.5.5 0 1 1-.998-.06l.5-8.5a.5.5 0 0 1 .528-.47ZM8 4.5a.5.5 0 0 1 .5.5v8.5a.5.5 0 0 1-1 0V5a.5.5 0 0 1 .5-.5Z"
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
      </div>
    </div>
    <div class="management-content">
      <!-- 통합된 점검 결과 섹션 (필터 + 결과) -->
      <div class="integrated-results-section">
        <div class="section-header">
          <h3>📋 점검 결과 관리</h3>
          <div class="section-actions">
            <button @click="downloadTemplate" class="secondary-button">📄 템플릿 다운로드</button>
            <button @click="openBulkUploadModal" class="primary-button">📤 엑셀 업로드</button>
          </div>
        </div>

        <!-- 필터 섹션을 내부로 이동 -->
        <div class="filter-section">
          <div class="filter-group">
            <label>연도:</label>
            <select v-model="selectedYear" @change="loadCheckData">
              <option v-for="year in availableYears" :key="year" :value="year">{{ year }}년</option>
            </select>
          </div>

          <div class="filter-group">
            <label>점검 유형:</label>
            <select v-model="selectedCheckType" @change="loadCheckData">
              <option value="">전체</option>
              <option value="seal_check">PC 봉인씰 확인</option>
              <option value="malware_scan">악성코드 전체 검사</option>
              <option value="file_encryption">개인정보 파일 암호화</option>
            </select>
          </div>

          <div class="filter-group">
            <label>결과:</label>
            <select v-model="selectedResult" @change="loadCheckData">
              <option value="">전체</option>
              <option value="pass">통과</option>
              <option value="fail">실패</option>
            </select>
          </div>

          <div class="search-group">
            <label>검색:</label>
            <input
              type="text"
              v-model="searchQuery"
              @input="searchCheckData"
              placeholder="사용자명, ID 또는 이메일 검색..."
              class="search-input"
            />
          </div>
        </div>

        <!-- 선택 및 액션 -->
        <div class="bulk-actions" v-if="selectedRecords.length > 0">
          <span>{{ selectedRecords.length }}개 선택됨</span>
          <button @click="bulkDelete" class="danger-button">선택 삭제</button>
        </div>

        <!-- 결과 테이블 -->
        <div v-else class="table-container">
          <table class="training-table">
            <thead>
              <tr>
                <th>
                  <input type="checkbox" v-model="selectAll" @change="toggleSelectAll" />
                </th>
                <th>사용자</th>
                <th>점검 유형</th>
                <th>기간</th>
                <th>IP 주소</th>
                <th>점검 결과</th>
                <th>점수</th>
                <th>점검일시</th>
                <th>비고</th>
                <th>액션</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="record in paginatedRecords"
                :key="`${record.user_id}-${record.check_type}-${record.period_id}`"
                :class="{ selected: selectedRecords.includes(record.result_id) }"
              >
                <td>
                  <input type="checkbox" :value="record.result_id" v-model="selectedRecords" />
                </td>
                <td>
                  <div class="user-info">
                    <strong>{{ record.username }}</strong>
                    <small>{{ record.user_email }}</small>
                  </div>
                </td>
                <td>
                  <span
                    class="check-type-badge"
                    :class="record.check_item_code || record.check_type"
                  >
                    {{ getCheckTypeName(record.check_item_code || record.check_type) }}
                  </span>
                </td>
                <td>{{ record.period_name }}</td>
                <!-- 새로 추가된 IP 주소 컬럼 -->
                <td>
                  <span class="ip-address">{{ record.source_ip || '-' }}</span>
                </td>
                <td>
                  <span
                    class="result-badge"
                    :class="getResultClass(record.check_result || record.overall_result)"
                  >
                    {{ getResultText(record.check_result || record.overall_result) }}
                  </span>
                </td>
                <!-- 새로 추가된 점수 컬럼 -->
                <td>
                  <span class="score-badge" :class="getScoreClass(record.total_score)">
                    {{ record.total_score || 0 }}점
                  </span>
                </td>
                <td>{{ formatDateTime(record.check_date || record.created_at) }}</td>
                <td>
                  <span class="notes">{{ truncateText(record.notes, 30) }}</span>
                </td>
                <td>
                  <div class="action-buttons">
                    <button @click="editRecord(record)" class="edit-btn" title="수정">✏️</button>
                    <button @click="deleteRecord(record)" class="delete-btn" title="삭제">
                      🗑️
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>

          <!-- 데이터가 없을 때 -->
          <div v-if="!loading && paginatedRecords.length === 0" class="no-data">
            <p>조건에 맞는 점검 결과가 없습니다.</p>
          </div>
        </div>

        <!-- 페이지네이션 -->
        <div class="pagination" v-if="totalPages > 1">
          <button @click="changePage(currentPage - 1)" :disabled="currentPage === 1">이전</button>
          <span class="page-info">
            {{ currentPage }} / {{ totalPages }} (총 {{ totalRecords }}건)
          </span>
          <button @click="changePage(currentPage + 1)" :disabled="currentPage === totalPages">
            다음
          </button>
        </div>
      </div>
    </div>

    <!-- 기간 추가/수정 모달 -->
    <!-- ManualCheckManagement.vue에 추가할 기간 수정 모달 -->
    <div v-if="showPeriodModal" class="modal-overlay" @click.self="closePeriodModal">
      <div class="modal-container">
        <div class="modal-header">
          <h3>{{ editingPeriod ? '기간 수정' : '기간 추가' }}</h3>
          <button @click="closePeriodModal" class="close-button">×</button>
        </div>

        <div class="modal-body">
          <form @submit.prevent="savePeriod">
            <div class="form-row">
              <div class="form-group">
                <label>점검 유형 *</label>
                <select v-model="periodForm.check_type" :disabled="editingPeriod" required>
                  <option value="">선택하세요</option>
                  <option value="seal_check">PC 봉인씰 확인</option>
                  <option value="malware_scan">악성코드 전체 검사</option>
                  <option value="file_encryption">개인정보 파일 암호화</option>
                </select>
                <small v-if="editingPeriod" class="form-help">
                  수정 시에는 점검 유형을 변경할 수 없습니다.
                </small>
              </div>

              <div class="form-group">
                <label>연도 *</label>
                <input
                  type="number"
                  v-model.number="periodForm.period_year"
                  :disabled="editingPeriod"
                  min="2020"
                  max="2030"
                  required
                />
                <small v-if="editingPeriod" class="form-help">
                  수정 시에는 연도를 변경할 수 없습니다.
                </small>
              </div>

              <div class="form-group">
                <label>연도 *</label>
                <input
                  type="number"
                  v-model.number="periodForm.period_year"
                  :disabled="editingPeriod"
                  min="2020"
                  max="2030"
                  required
                />
                <small v-if="editingPeriod" class="form-help">
                  수정 시에는 연도를 변경할 수 없습니다.
                </small>
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>기간명 *</label>
                <input
                  type="text"
                  v-model="periodForm.period_name"
                  :disabled="editingPeriod"
                  placeholder="예: 1월, Q1, 상반기 등"
                  required
                />
                <small v-if="editingPeriod" class="form-help">
                  수정 시에는 기간명을 변경할 수 없습니다.
                </small>
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>시작일 *</label>
                <input type="date" v-model="periodForm.start_date" required />
              </div>

              <div class="form-group">
                <label>종료일 *</label>
                <input type="date" v-model="periodForm.end_date" required />
              </div>
            </div>

            <div class="form-group">
              <label>설명</label>
              <textarea
                v-model="periodForm.description"
                rows="3"
                placeholder="기간에 대한 설명을 입력하세요..."
              ></textarea>
            </div>

            <!-- 검증 중 상태 표시 -->
            <div v-if="isValidating" class="validation-status">
              <span class="loading-text">📋 기간 검증 중...</span>
            </div>

            <!-- 겹침 경고 표시 -->
            <div v-if="overlapWarning" class="overlap-warning">
              <div class="warning-header">⚠️ 기간 겹침 경고</div>
              <p>{{ overlapWarning.message }}</p>
              <ul v-if="overlapWarning.overlapping_periods?.length" class="overlap-list">
                <li v-for="period in overlapWarning.overlapping_periods" :key="period.period_id">
                  {{ period.period_year }}년 {{ period.period_name }} ({{ period.start_date }} ~
                  {{ period.end_date }})
                </li>
              </ul>
            </div>

            <!-- 유효성 검사 오류 표시 -->
            <div v-if="validationErrors.length" class="validation-errors">
              <div class="error-header">❌ 입력 오류</div>
              <ul>
                <li v-for="error in validationErrors" :key="error">{{ error }}</li>
              </ul>
            </div>

            <div class="form-actions">
              <button type="button" @click="closePeriodModal" class="cancel-button">취소</button>
              <button
                type="submit"
                class="save-button"
                :disabled="savingPeriod || isValidating || validationErrors.length > 0"
              >
                <span v-if="savingPeriod" class="loading-spinner"></span>
                {{ savingPeriod ? '저장 중...' : editingPeriod ? '수정' : '저장' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- 일괄 업로드 모달 - 개선된 버전 -->
    <!-- 일괄 업로드 모달 - 기간 선택 추가 버전 -->
    <div v-if="showBulkUploadModal" class="modal-overlay" @click="closeBulkUploadModal">
      <div class="modal-content upload-modal" @click.stop>
        <div class="modal-header">
          <h3>점검 결과 엑셀 업로드</h3>
          <button @click="closeBulkUploadModal" class="close-button">×</button>
        </div>

        <div class="modal-body">
          <!-- ✅ 1단계: 점검 기간 선택 -->
          <div class="upload-step">
            <h4>1단계: 점검 기간 선택 (필수)</h4>
            <div class="period-selection">
              <select 
                v-model="selectedUploadPeriod" 
                @change="onPeriodChange" 
                class="period-select"
              >
                <option value="">점검 기간을 선택하세요</option>
                <optgroup
                  v-for="(typeData, checkType) in availablePeriodsForUpload"
                  :key="checkType"
                  :label="`${getCheckTypeName(checkType)} 점검`"
                >
                  <option
                    v-for="period in typeData.periods"
                    :key="period.period_id"
                    :value="period.period_id"
                  >
                    {{ period.period_year }}년 - {{ period.period_name }} 
                    ({{ formatDateRange(period.start_date, period.end_date) }})
                    - {{ getPeriodStatusText(period) }}
                  </option>
                </optgroup>
              </select>
            </div>

            <!-- ✅ 선택된 기간 정보 표시 -->
            <div v-if="selectedPeriodInfo" class="selected-period-info">
              <div class="info-card">
                <h5>선택된 점검 기간</h5>
                <p><strong>기간명:</strong> {{ selectedPeriodInfo.period_name }}</p>
                <p><strong>점검유형:</strong> {{ getCheckTypeName(selectedPeriodInfo.check_type) }}</p>
                <p>
                  <strong>기간:</strong> 
                  {{ formatDateRange(selectedPeriodInfo.start_date, selectedPeriodInfo.end_date) }}
                </p>
                <p>
                  <strong>상태:</strong>
                  <span :class="getPeriodStatusClass(selectedPeriodInfo)">
                    {{ getPeriodStatusText(selectedPeriodInfo) }}
                  </span>
                </p>
              </div>
            </div>
          </div>

          <!-- ✅ 2단계: 파일 업로드 -->
          <div class="upload-step" :class="{ disabled: !selectedUploadPeriod }">
            <h4>2단계: Excel/CSV 파일 업로드</h4>

            <!-- 기간 미선택 시 안내 메시지 -->
            <div v-if="!selectedUploadPeriod" class="warning-message">
              <p>⚠️ 먼저 점검 기간을 선택해주세요.</p>
            </div>

            <div v-else class="upload-section">
              <div class="upload-area" @drop="handleFileDrop" @dragover.prevent @dragenter.prevent>
                <input
                  type="file"
                  ref="fileInput"
                  @change="handleFileSelect"
                  accept=".csv,.xlsx,.xls"
                  style="display: none"
                />

                <div v-if="!selectedFile" class="upload-placeholder">
                  <div class="upload-icon">📁</div>
                  <p>Excel 또는 CSV 파일을 드래그하거나 클릭하여 선택하세요</p>
                  <p class="upload-subtitle">파일 유형이 자동으로 감지됩니다</p>
                  <button @click="$refs.fileInput.click()" class="select-file-button">
                    파일 선택
                  </button>
                </div>

                <div v-else class="file-selected">
                  <div class="file-info">
                    <div class="file-icon">📄</div>
                    <div>
                      <div class="file-name">{{ selectedFile.name }}</div>
                      <div class="file-size">{{ formatFileSize(selectedFile.size) }}</div>
                    </div>
                  </div>
                  <button @click="removeSelectedFile" class="remove-file-button">×</button>
                </div>
              </div>

              <!-- 파일 미리보기 정보 -->
              <div v-if="filePreviewInfo" class="preview-info">
                <div class="preview-header">
                  <h4>📄 파일 분석 결과</h4>
                  <span class="detected-type">{{ filePreviewInfo.type_name }}</span>
                </div>

                <!-- ✅ 점검 유형 일치 확인 -->
                <div 
                  v-if="selectedPeriodInfo && filePreviewInfo.check_type !== selectedPeriodInfo.check_type" 
                  class="type-mismatch-warning"
                >
                  <p>⚠️ <strong>점검 유형 불일치!</strong></p>
                  <p>
                    선택한 기간: <strong>{{ getCheckTypeName(selectedPeriodInfo.check_type) }}</strong><br>
                    파일 유형: <strong>{{ getCheckTypeName(filePreviewInfo.check_type) }}</strong>
                  </p>
                  <p>올바른 점검 유형의 기간을 선택하거나 다른 파일을 업로드해주세요.</p>
                </div>

                <div class="preview-stats">
                  <div class="stat-item">
                    <span class="stat-label">총 레코드:</span>
                    <span class="stat-value">{{ filePreviewInfo.total_records }}건</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-label">예상 통과:</span>
                    <span class="stat-value success">
                      {{ filePreviewInfo.expected_results?.expected_pass || 0 }}건
                    </span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-label">예상 실패:</span>
                    <span class="stat-value danger">
                      {{ filePreviewInfo.expected_results?.expected_fail || 0 }}건
                    </span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-label">통과율:</span>
                    <span class="stat-value">
                      {{ filePreviewInfo.expected_results?.pass_rate || 0 }}%
                    </span>
                  </div>
                </div>

                <!-- 개인정보 암호화 추가 정보 -->
                <div v-if="filePreviewInfo.additional_info?.detected_rounds" class="encryption-info">
                  <h5>🔐 회차별 검증 정보</h5>
                  <p>
                    <strong>감지된 회차:</strong>
                    {{ filePreviewInfo.additional_info.detected_rounds.join(', ') }}
                  </p>
                  <p>
                    <strong>최신 회차:</strong> {{ filePreviewInfo.additional_info.latest_round }}회차
                  </p>
                </div>
              </div>

              <div class="upload-instructions">
                <h4>💡 업로드 가이드</h4>
                <ul>
                  <li><strong>PC 봉인씰 확인:</strong> 일시, 이름, 부서, 훼손여부</li>
                  <li><strong>악성코드 전체 검사:</strong> 일시, IP, 악성코드명, 분류, 경로, 탐지항목</li>
                  <li><strong>개인정보 파일 암호화:</strong> 로컬 IP, 파일명, 보호상태, 주민번호 건수</li>
                  <li>동일한 사용자/날짜의 기존 데이터는 자동 업데이트됩니다</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button @click="closeBulkUploadModal" class="cancel-button">취소</button>
          <button
            @click="uploadFile"
            :disabled="!canUpload || hasTypeMismatch"
            class="upload-button"
            :title="getUploadButtonTooltip()"
          >
            <span v-if="uploading" class="loading-spinner"></span>
            {{ uploading ? '업로드 중...' : '업로드 시작' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 수정 모달 -->
    <div v-if="showEditModal" class="modal-overlay" @click="closeEditModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>점검 결과 수정</h3>
          <button @click="closeEditModal" class="close-button">✕</button>
        </div>

        <div class="modal-body">
          <form @submit.prevent="saveRecord">
            <div class="form-group">
              <label>사용자</label>
              <input type="text" :value="editingRecord.username" disabled />
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>점검 유형</label>
                <input
                  type="text"
                  :value="
                    getCheckTypeName(editingRecord.check_item_code || editingRecord.check_type)
                  "
                  disabled
                />
              </div>

              <div class="form-group">
                <label>결과 *</label>
                <select v-model="editingRecord.check_result" required>
                  <option value="pass">통과</option>
                  <option value="fail">실패</option>
                </select>
              </div>
            </div>

            <div class="form-group">
              <label>비고</label>
              <textarea
                v-model="editingRecord.notes"
                placeholder="비고사항을 입력하세요"
                rows="3"
              ></textarea>
            </div>

            <div class="modal-footer">
              <button type="button" @click="closeEditModal" class="secondary-button">취소</button>
              <button type="submit" class="primary-button" :disabled="saving">
                {{ saving ? '저장 중...' : '저장' }}
              </button>
            </div>
          </form>
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
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { RouterLink } from 'vue-router'

// 기본 필터 및 검색
const selectedYear = ref(new Date().getFullYear())
const selectedCheckType = ref('')
const selectedResult = ref('')
const searchQuery = ref('')
const checkData = ref([])
const filteredRecords = ref([])
const selectedRecords = ref([])
const selectAll = ref(false)
const loading = ref(false)

// 기간 섹션 토글
const showPeriodSection = ref(false)

// 페이지네이션
const currentPage = ref(1)
const itemsPerPage = ref(20)
const totalPages = ref(1)
const totalRecords = ref(0)

// 모달 상태
const showBulkUploadModal = ref(false)
const showEditModal = ref(false)
const showPeriodModal = ref(false)
const selectedFile = ref(null)
const uploadPreview = ref([])
const uploading = ref(false)
const editingRecord = ref({})
const saving = ref(false)

// ✅ 추가: 업로드용 기간 선택 관련 상태
const selectedUploadPeriod = ref('')  // 선택된 기간 ID
const availablePeriodsForUpload = ref({})  // 업로드 가능한 기간 목록

// 기간 관리
const editingPeriod = ref(null)
const savingPeriod = ref(false)
const periodStatus = ref({ check_types: {} })

// 토스트
const showToast = ref(false)
const toastMessage = ref('')
const toastType = ref('success')

// 기존 변수에 추가
const filePreviewInfo = ref(null)

// 새로 추가할 검증 관련 반응형 데이터
const overlapWarning = ref(null) // 겹침 경고 정보
const validationErrors = ref([]) // 유효성 검사 오류 목록
const isValidating = ref(false) // 검증 진행 중 상태
const dateChangeTimeout = ref(null) // 디바운스용 타이머

// 기간 폼
const periodForm = reactive({
  check_type: '',
  period_year: new Date().getFullYear(),
  period_name: '',
  start_date: '',
  end_date: '',
  description: '',
  auto_pass_setting: true,
})

// 계산된 속성
const availableYears = computed(() => {
  const currentYear = new Date().getFullYear()
  return Array.from({ length: 11 }, (_, i) => currentYear - 5 + i)
})

const paginatedRecords = computed(() => {
  return filteredRecords.value
})


// 기존 computed 속성들 뒤에 추가

// ✅ 선택된 기간 정보
const selectedPeriodInfo = computed(() => {
  if (!selectedUploadPeriod.value) return null

  for (const typeData of Object.values(availablePeriodsForUpload.value)) {
    const period = typeData.periods?.find((p) => p.period_id == selectedUploadPeriod.value)
    if (period) return period
  }
  return null
})

// ✅ 점검 유형 불일치 여부
const hasTypeMismatch = computed(() => {
  if (!selectedPeriodInfo.value || !filePreviewInfo.value) return false
  return filePreviewInfo.value.check_type !== selectedPeriodInfo.value.check_type
})

// ✅ 업로드 가능 여부
const canUpload = computed(() => {
  return (
    selectedUploadPeriod.value &&
    selectedFile.value &&
    filePreviewInfo.value &&
    !uploading.value &&
    !hasTypeMismatch.value
  )
})


// 기간 섹션 토글
const togglePeriodSection = () => {
  showPeriodSection.value = !showPeriodSection.value
}

const getPeriodsCountText = () => {
  if (!periodStatus.value.check_types) return ''

  let totalPeriods = 0
  let activePeriods = 0

  Object.values(periodStatus.value.check_types).forEach((typeData) => {
    if (typeData.periods) {
      totalPeriods += typeData.periods.length
      activePeriods += typeData.periods.filter((p) => p.status === 'active').length
    }
  })

  if (totalPeriods === 0) return '(기간 없음)'
  if (activePeriods > 0) return `(${totalPeriods}개 기간, ${activePeriods}개 진행중)`
  return `(${totalPeriods}개 기간)`
}

// 데이터 로딩
const loadCheckData = async () => {
  try {
    loading.value = true

    const params = new URLSearchParams({
      year: selectedYear.value,
      page: currentPage.value,
      size: itemsPerPage.value,
    })

    if (selectedCheckType.value) params.append('check_type', selectedCheckType.value)
    if (selectedResult.value) params.append('result', selectedResult.value)
    if (searchQuery.value) params.append('search', searchQuery.value)

    const response = await fetch(`/api/manual-check/results?${params}`, {
      credentials: 'include',
    })

    if (!response.ok) {
      throw new Error(`API 요청 실패: ${response.status}`)
    }

    const result = await response.json()

    if (result.success) {
      checkData.value = result.data || []
      filteredRecords.value = result.data || []

      if (result.pagination) {
        totalPages.value = result.pagination.total_pages
        currentPage.value = result.pagination.current_page
      }

      if (result.data.total !== undefined) {
        totalRecords.value = result.data.total
      }
    } else {
      checkData.value = []
      filteredRecords.value = []
      totalPages.value = 1
      totalRecords.value = 0
    }
  } catch (err) {
    console.error('점검 결과 조회 오류:', err)
    displayToast('점검 결과 조회에 실패했습니다.', 'error')
    checkData.value = []
    filteredRecords.value = []
    totalPages.value = 1
    totalRecords.value = 0
  } finally {
    loading.value = false
  }
}

const loadPeriodStatus = async () => {
  try {
    const response = await fetch(`/api/manual-check/periods/status?year=${selectedYear.value}`, {
      credentials: 'include',
    })

    if (!response.ok) throw new Error('기간 상태 조회 실패')

    const result = await response.json()
    if (result.success) {
      periodStatus.value = result.data
    } else {
      periodStatus.value = result.data
    }
  } catch (err) {
    console.error('기간 상태 조회 오류:', err)
    displayToast('기간 상태 조회에 실패했습니다.', 'error')
  }
}

// ✅ 업로드 가능한 기간 목록 로드
const loadAvailablePeriodsForUpload = async () => {
  try {
    const response = await fetch('/api/manual-check/periods/status', {
      credentials: 'include',
    })

    if (!response.ok) throw new Error('기간 목록 로드 실패')

    const result = await response.json()
    
    if (result.success) {
      // 완료되지 않은 기간만 필터링
      const filteredPeriods = {}
      
      for (const [checkType, typeData] of Object.entries(result.data.check_types || {})) {
        const activePeriods = typeData.periods?.filter(p => !p.is_completed) || []
        if (activePeriods.length > 0) {
          filteredPeriods[checkType] = {
            ...typeData,
            periods: activePeriods
          }
        }
      }
      
      availablePeriodsForUpload.value = filteredPeriods
      
      console.log('[DEBUG] 업로드 가능한 기간:', availablePeriodsForUpload.value)
    }
  } catch (err) {
    console.error('기간 목록 로드 오류:', err)
    displayToast('기간 목록을 불러오는데 실패했습니다.', 'error')
  }
}

// 검색
const searchCheckData = () => {
  setTimeout(() => {
    loadCheckData()
  }, 300)
}

// 유틸리티 함수
const getCheckTypeName = (type) => {
  const names = {
    seal_check: 'PC 봉인씰 확인',
    malware_scan: '악성코드 전체 검사',
    file_encryption: '개인정보 파일 암호화',
  }
  return names[type] || type
}

const getStatusText = (status) => {
  const statusMap = {
    upcoming: '예정',
    active: '진행중',
    ended: '종료',
    completed: '완료',
  }
  return statusMap[status] || status
}

const getResultClass = (result) => {
  const classes = {
    pass: 'success',
    fail: 'danger',
  }
  return classes[result] || 'warning'
}

const getResultText = (result) => {
  const texts = {
    pass: '통과',
    fail: '실패',
  }
  return texts[result] || '알 수 없음'
}

const getScoreClass = (score) => {
  if (!score) return 'score-unknown'
  if (score >= 90) return 'score-excellent'
  if (score >= 80) return 'score-good'
  if (score >= 70) return 'score-average'
  return 'score-poor'
}

const formatDateTime = (datetime) => {
  if (!datetime) return ''
  return new Date(datetime).toLocaleString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const truncateText = (text, maxLength) => {
  if (!text) return ''
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
}

// 기간 관리
const openPeriodModal = () => {
  resetPeriodForm()
  editingPeriod.value = null
  showPeriodModal.value = true
}

const closePeriodModal = () => {
  showPeriodModal.value = false
  editingPeriod.value = null
  resetPeriodForm()
}

// 수정된 resetPeriodForm 함수
const resetPeriodForm = () => {
  periodForm.check_type = ''
  periodForm.period_year = new Date().getFullYear()
  periodForm.period_name = ''
  periodForm.start_date = ''
  periodForm.end_date = ''
  periodForm.description = ''

  // 검증 관련 초기화
  validationErrors.value = []
  overlapWarning.value = null
  isValidating.value = false
}

// 기간 겹침 검사 함수
const checkPeriodOverlap = async (checkType, startDate, endDate, excludePeriodId = null) => {
  if (!checkType || !startDate || !endDate) {
    return { has_overlap: false, overlapping_periods: [], message: '' }
  }

  try {
    const payload = {
      check_type: checkType,
      start_date: startDate,
      end_date: endDate,
    }

    if (excludePeriodId) {
      payload.exclude_period_id = excludePeriodId
    }

    const response = await fetch('/api/manual-check/periods/check-overlap', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify(payload),
    })

    if (!response.ok) {
      // 백엔드 API가 아직 구현되지 않은 경우 프론트엔드에서 검증
      return await checkOverlapLocally(checkType, startDate, endDate, excludePeriodId)
    }

    const result = await response.json()
    return result.success ? result : { has_overlap: false, overlapping_periods: [], message: '' }
  } catch (error) {
    console.warn('서버 겹침 검사 실패, 로컬 검증으로 대체:', error)
    // 서버 오류 시 로컬 검증으로 대체
    return await checkOverlapLocally(checkType, startDate, endDate, excludePeriodId)
  }
}

// 로컬 기간 겹침 검사 (백엔드 API가 없을 때 사용)
const checkOverlapLocally = async (checkType, startDate, endDate, excludePeriodId = null) => {
  try {
    // periodStatus에서 현재 점검 유형의 기간들 가져오기
    const typeData = periodStatus.value.check_types?.[checkType]
    if (!typeData?.periods) {
      return { has_overlap: false, overlapping_periods: [], message: '' }
    }

    const newStart = new Date(startDate)
    const newEnd = new Date(endDate)
    const overlappingPeriods = []

    for (const period of typeData.periods) {
      // 수정 시 현재 기간 제외
      if (excludePeriodId && period.period_id === excludePeriodId) {
        continue
      }

      const existingStart = new Date(period.start_date)
      const existingEnd = new Date(period.end_date)

      // 기간 겹침 검사 로직
      const isOverlapping =
        // 새 시작일이 기존 기간 내
        (existingStart <= newStart && newStart <= existingEnd) ||
        // 새 종료일이 기존 기간 내
        (existingStart <= newEnd && newEnd <= existingEnd) ||
        // 새 기간이 기존 기간을 포함
        (newStart <= existingStart && newEnd >= existingEnd) ||
        // 기존 기간이 새 기간을 포함
        (existingStart <= newStart && existingEnd >= newEnd)

      if (isOverlapping) {
        overlappingPeriods.push({
          period_id: period.period_id,
          period_name: period.period_name,
          start_date: period.start_date,
          end_date: period.end_date,
          period_year: period.period_year,
        })
      }
    }

    const hasOverlap = overlappingPeriods.length > 0
    let message = ''

    if (hasOverlap) {
      const overlapInfo = overlappingPeriods
        .map((p) => `${p.period_year}년 ${p.period_name} (${p.start_date} ~ ${p.end_date})`)
        .join(', ')
      message = `다음 기간과 겹칩니다: ${overlapInfo}`
    }

    return {
      has_overlap: hasOverlap,
      overlapping_periods: overlappingPeriods,
      message: message,
    }
  } catch (error) {
    console.error('로컬 겹침 검사 오류:', error)
    return { has_overlap: false, overlapping_periods: [], message: '' }
  }
}

// 실시간 날짜 겹침 검사
const checkDateOverlap = async () => {
  if (!periodForm.start_date || !periodForm.end_date || !periodForm.check_type) {
    overlapWarning.value = null
    return
  }

  try {
    isValidating.value = true

    const result = await checkPeriodOverlap(
      periodForm.check_type,
      periodForm.start_date,
      periodForm.end_date,
      editingPeriod.value?.period_id,
    )

    if (result.has_overlap) {
      overlapWarning.value = {
        message: result.message,
        overlapping_periods: result.overlapping_periods,
      }
    } else {
      overlapWarning.value = null
    }
  } catch (error) {
    console.error('겹침 검사 실패:', error)
    overlapWarning.value = null
  } finally {
    isValidating.value = false
  }
}

// 날짜 변경 시 디바운스 적용
const onDateChange = () => {
  clearTimeout(dateChangeTimeout.value)
  dateChangeTimeout.value = setTimeout(() => {
    checkDateOverlap()
  }, 500)
}

// 저장 전 종합 검증
const validateBeforeSave = async () => {
  validationErrors.value = []

  // 기본 필드 검증
  if (!periodForm.period_name?.trim()) {
    validationErrors.value.push('기간명을 입력해주세요.')
  }
  if (!periodForm.start_date) {
    validationErrors.value.push('시작일을 선택해주세요.')
  }
  if (!periodForm.end_date) {
    validationErrors.value.push('종료일을 선택해주세요.')
  }
  if (!periodForm.check_type) {
    validationErrors.value.push('점검 유형을 선택해주세요.')
  }

  // 날짜 순서 검증
  if (periodForm.start_date && periodForm.end_date) {
    if (new Date(periodForm.start_date) >= new Date(periodForm.end_date)) {
      validationErrors.value.push('종료일은 시작일보다 늦어야 합니다.')
    }
  }

  // 기간 겹침 검증
  if (periodForm.check_type && periodForm.start_date && periodForm.end_date) {
    try {
      const overlapResult = await checkPeriodOverlap(
        periodForm.check_type,
        periodForm.start_date,
        periodForm.end_date,
        editingPeriod.value?.period_id,
      )

      if (overlapResult.has_overlap) {
        validationErrors.value.push(overlapResult.message)
        overlapWarning.value = {
          message: overlapResult.message,
          overlapping_periods: overlapResult.overlapping_periods,
        }
      }
    } catch (error) {
      console.error('겹침 검증 오류:', error)
      validationErrors.value.push('기간 겹침 검증 중 오류가 발생했습니다.')
    }
  }

  return validationErrors.value.length === 0
}

// 수정된 savePeriod 함수
const savePeriod = async () => {
  if (savingPeriod.value) return

  // 검증 실행
  const isValid = await validateBeforeSave()
  if (!isValid) {
    return
  }

  savingPeriod.value = true

  try {
    const url = editingPeriod.value
      ? `/api/manual-check/periods/${editingPeriod.value.period_id}`
      : '/api/manual-check/periods'

    const method = editingPeriod.value ? 'PUT' : 'POST'

    const response = await fetch(url, {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify(periodForm),
    })

    const result = await response.json()

    if (!response.ok) {
      // 서버에서 겹침 오류 반환 시 처리
      if (result.overlapping_periods) {
        overlapWarning.value = {
          message: result.error,
          overlapping_periods: result.overlapping_periods,
        }
      }
      validationErrors.value = [result.error || '저장 실패']
      return
    }

    displayToast(result.message, 'success')
    closePeriodModal()
    await loadPeriodStatus()
  } catch (err) {
    console.error('기간 저장 오류:', err)
    validationErrors.value = [err.message || '저장 중 오류가 발생했습니다.']
  } finally {
    savingPeriod.value = false
  }
}

const editPeriod = (period) => {
  editingPeriod.value = period
  periodForm.check_type = period.check_type
  periodForm.period_year = period.period_year
  periodForm.period_name = period.period_name
  periodForm.start_date = period.start_date
  periodForm.end_date = period.end_date
  periodForm.description = period.description || ''
  showPeriodModal.value = true
}

const deletePeriod = async (periodId) => {
  if (!confirm('이 기간을 삭제하시겠습니까? 관련된 모든 점검 결과도 함께 삭제됩니다.')) {
    return
  }

  try {
    const response = await fetch(`/api/manual-check/periods/${periodId}`, {
      method: 'DELETE',
      credentials: 'include',
    })

    const result = await response.json()

    if (!response.ok) {
      throw new Error(result.error || '삭제 실패')
    }

    displayToast(result.message, 'success')
    await loadPeriodStatus()
    await loadCheckData()
  } catch (err) {
    console.error('삭제 오류:', err)
    displayToast(err.message, 'error')
  }
}
const completePeriod = async (periodId) => {
  if (!confirm('이 기간을 완료 처리하시겠습니까? 미실시 사용자들이 자동으로 통과 처리됩니다.')) {
    return
  }

  try {
    const response = await fetch(`/api/manual-check/periods/${periodId}/complete`, {
      method: 'POST',
      credentials: 'include',
    })

    const result = await response.json()

    if (!response.ok) {
      throw new Error(result.error || '완료 처리 실패')
    }

    displayToast(result.message, 'success')
    await loadPeriodStatus()
    await loadCheckData()
  } catch (err) {
    console.error('완료 처리 오류:', err)
    displayToast(err.message, 'error')
  }
}

const reopenPeriod = async (periodId) => {
  if (!confirm('이 기간의 완료 상태를 취소하시겠습니까?')) {
    return
  }

  try {
    const response = await fetch(`/api/manual-check/periods/${periodId}/reopen`, {
      method: 'POST',
      credentials: 'include',
    })

    const result = await response.json()

    if (!response.ok) {
      throw new Error(result.error || '재개 처리 실패')
    }

    displayToast(result.message, 'success')
    await loadPeriodStatus()
    await loadCheckData()
  } catch (err) {
    console.error('재개 처리 오류:', err)
    displayToast(err.message, 'error')
  }
}

// 점검 결과 관리
const editRecord = (record) => {
  editingRecord.value = { ...record }
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
    const response = await fetch('/api/manual-check/results/update', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({
        check_id: editingRecord.value.check_id || editingRecord.value.result_id,
        check_result: editingRecord.value.check_result || editingRecord.value.overall_result,
        notes: editingRecord.value.notes,
        check_type: editingRecord.value.check_item_code || editingRecord.value.check_type,
      }),
    })

    const result = await response.json()

    if (result.success) {
      displayToast(result.message || '수정이 완료되었습니다.', 'success')
      closeEditModal()
      await loadCheckData()
    } else {
      throw new Error(result.error || '수정 실패')
    }
  } catch (err) {
    console.error('기록 수정 오류:', err)
    displayToast(err.message, 'error')
  } finally {
    saving.value = false
  }
}

const deleteRecord = async (record) => {
  const checkId = record.check_id || record.result_id
  const typeName = getCheckTypeName(record.check_item_code || record.check_type)

  if (!confirm(`${record.username}의 ${typeName} 점검 결과를 삭제하시겠습니까?`)) return

  try {
    const response = await fetch(`/api/manual-check/results/${checkId}`, {
      method: 'DELETE',
      credentials: 'include',
    })

    const result = await response.json()

    if (result.success) {
      displayToast(result.message || '삭제가 완료되었습니다.', 'success')
      await loadCheckData()
    } else {
      throw new Error(result.error || '삭제 실패')
    }
  } catch (err) {
    console.error('기록 삭제 오류:', err)
    displayToast(err.message, 'error')
  }
}

// 일괄 처리
const toggleSelectAll = () => {
  if (selectAll.value) {
    selectedRecords.value = paginatedRecords.value.map(
      (record) => record.check_id || record.result_id,
    )
  } else {
    selectedRecords.value = []
  }
}

const bulkDelete = async () => {
  if (!confirm(`선택된 ${selectedRecords.value.length}개의 결과를 삭제하시겠습니까?`)) return

  try {
    const response = await fetch('/api/manual-check/results/bulk-delete', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({ result_ids: selectedRecords.value }),
    })

    const result = await response.json()

    if (result.success) {
      displayToast(result.message || '일괄 삭제가 완료되었습니다.', 'success')
      selectedRecords.value = []
      selectAll.value = false
      await loadCheckData()
    } else {
      throw new Error(result.error || '일괄 삭제 실패')
    }
  } catch (err) {
    console.error('일괄 삭제 오류:', err)
    displayToast(err.message, 'error')
  }
}

// ✅ 업로드 모달 열기 - 기간 목록도 함께 로드
const openBulkUploadModal = async () => {
  showBulkUploadModal.value = true
  selectedFile.value = null
  selectedUploadPeriod.value = ''  // ✅ 기간 선택 초기화
  filePreviewInfo.value = null
  uploadPreview.value = []
  
  // ✅ 업로드 가능한 기간 목록 로드
  await loadAvailablePeriodsForUpload()
}

// ✅ 업로드 모달 닫기
const closeBulkUploadModal = () => {
  showBulkUploadModal.value = false
  selectedFile.value = null
  selectedUploadPeriod.value = ''  // ✅ 기간 선택 초기화
  filePreviewInfo.value = null
  uploadPreview.value = []
}

// ✅ 기간 선택 변경 시 파일 초기화
const onPeriodChange = () => {
  if (selectedFile.value) {
    // 기간 변경 시 파일 초기화하고 재선택 필요 알림
    selectedFile.value = null
    filePreviewInfo.value = null
    uploadPreview.value = []
    displayToast('기간이 변경되어 파일을 다시 선택해주세요.', 'info')
  }
}

// ✅ 파일 선택 처리 - 기간 선택 확인 추가
const handleFileSelect = async (event) => {
  // ✅ 기간 선택 여부 확인
  if (!selectedUploadPeriod.value) {
    displayToast('먼저 점검 기간을 선택해주세요.', 'warning')
    event.target.value = '' // input 초기화
    return
  }

  const file = event.target.files[0]
  if (!file) return

  selectedFile.value = file
  await previewFile(file)
}

// ✅ 드래그 앤 드롭 처리 - 기간 선택 확인 추가
const handleFileDrop = async (event) => {
  event.preventDefault()
  
  // ✅ 기간 선택 여부 확인
  if (!selectedUploadPeriod.value) {
    displayToast('먼저 점검 기간을 선택해주세요.', 'warning')
    return
  }

  const files = event.dataTransfer.files
  if (files.length > 0) {
    const file = files[0]
    const allowedTypes = [
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/vnd.ms-excel',
      'text/csv',
    ]

    if (
      allowedTypes.includes(file.type) ||
      file.name.endsWith('.xlsx') ||
      file.name.endsWith('.xls') ||
      file.name.endsWith('.csv')
    ) {
      selectedFile.value = file
      await previewFile(file)
    } else {
      displayToast('Excel 또는 CSV 파일만 업로드 가능합니다.', 'error')
    }
  }
}

const previewFile = async (file) => {
  if (!file) return

  try {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch('/api/manual-check/upload/preview', {
      method: 'POST',
      credentials: 'include',
      body: formData,
    })

    const result = await response.json()

    if (result.success) {
      filePreviewInfo.value = result.data
      console.log('[DEBUG] 파일 미리보기 성공:', result.data)

      // 성공 메시지 표시
      if (result.data.additional_info?.detected_rounds) {
        displayToast(
          `${result.data.type_name} 파일 인식 완료! ${result.data.additional_info.detected_rounds.length}개 회차 감지`,
          'success',
        )
      } else {
        displayToast(`${result.data.type_name} 파일이 인식되었습니다.`, 'success')
      }
    } else {
      filePreviewInfo.value = null
      console.error('[DEBUG] 파일 미리보기 실패:', result)

      // 상세한 오류 정보 표시
      let errorMessage = result.error || '파일 분석에 실패했습니다.'

      if (result.found_columns) {
        errorMessage += `\n\n발견된 컬럼: ${result.found_columns.join(', ')}`
      }

      if (result.suggestions) {
        errorMessage += `\n\n필요한 컬럼:\n${result.suggestions.join('\n')}`
      }

      displayToast(errorMessage, 'error')
    }
  } catch (err) {
    console.error('파일 미리보기 오류:', err)
    filePreviewInfo.value = null
    displayToast('파일 미리보기 중 오류가 발생했습니다.', 'error')
  }
}
const removeSelectedFile = () => {
  selectedFile.value = null
  filePreviewInfo.value = null
  uploadPreview.value = []
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// ✅ 파일 업로드 실행 - period_id 포함
const uploadFile = async () => {
  // ✅ 업로드 전 검증
  if (!selectedUploadPeriod.value) {
    displayToast('점검 기간을 선택해주세요.', 'warning')
    return
  }

  if (!selectedFile.value) {
    displayToast('파일을 선택해주세요.', 'warning')
    return
  }

  if (!filePreviewInfo.value) {
    displayToast('파일 분석이 완료되지 않았습니다.', 'warning')
    return
  }

  // ✅ 점검 유형 일치 확인
  if (hasTypeMismatch.value) {
    displayToast(
      `점검 유형이 일치하지 않습니다.\n기간: ${getCheckTypeName(selectedPeriodInfo.value.check_type)}\n파일: ${getCheckTypeName(filePreviewInfo.value.check_type)}`,
      'error'
    )
    return
  }

  if (uploading.value) return

  uploading.value = true

  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('period_id', selectedUploadPeriod.value)  // ✅ period_id 추가

    console.log('[DEBUG] 업로드 요청:', {
      filename: selectedFile.value.name,
      period_id: selectedUploadPeriod.value,
      period_name: selectedPeriodInfo.value?.period_name,
      check_type: selectedPeriodInfo.value?.check_type
    })

    const response = await fetch('/api/manual-check/upload', {
      method: 'POST',
      credentials: 'include',
      body: formData,
    })

    const result = await response.json()

    if (result.success) {
      const data = result.data
      let message = result.message || `업로드 완료! ${data.file_type}`
      
      // ✅ 상세 결과 추가
      if (data.success_count > 0 || data.error_count > 0) {
        message += `\n총 ${data.total_records}건 중 ${data.success_count}건 성공`
        
        if (data.error_count > 0) {
          message += `, ${data.error_count}건 실패`
          
          // 오류 상세 정보가 있으면 콘솔에 출력
          if (data.errors && data.errors.length > 0) {
            console.log('업로드 오류 상세:', data.errors)
          }
        }
      }

      displayToast(message, 'success')
      closeBulkUploadModal()
      
      // ✅ 데이터 새로고침
      await loadCheckData()
      await loadPeriodStatus()
    } else {
      throw new Error(result.error || '업로드 실패')
    }
  } catch (err) {
    console.error('파일 업로드 오류:', err)
    displayToast(err.message, 'error')
  } finally {
    uploading.value = false
  }
}

// ✅ 업로드 버튼 툴팁 메시지
const getUploadButtonTooltip = () => {
  if (!selectedUploadPeriod.value) {
    return '먼저 점검 기간을 선택해주세요'
  }
  if (!selectedFile.value) {
    return '파일을 선택해주세요'
  }
  if (hasTypeMismatch.value) {
    return '점검 유형이 일치하지 않습니다'
  }
  if (!filePreviewInfo.value) {
    return '파일 분석 중...'
  }
  if (uploading.value) {
    return '업로드 중...'
  }
  return '업로드 시작'
}


// 템플릿 다운로드 개선
const downloadTemplate = async () => {
  try {
    // 특정 유형별 템플릿 다운로드 옵션 제공
    const templateType = selectedCheckType.value || 'all'
    const url =
      templateType === 'all'
        ? '/api/manual-check/template'
        : `/api/manual-check/template?type=${templateType}`

    const response = await fetch(url, {
      credentials: 'include',
    })

    if (!response.ok) throw new Error('템플릿 다운로드 실패')

    const blob = await response.blob()
    const downloadUrl = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = downloadUrl

    const filename =
      templateType === 'all' ? 'manual_check_templates.txt' : `${templateType}_template.csv`

    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(downloadUrl)

    displayToast('템플릿이 다운로드되었습니다.', 'success')
  } catch (err) {
    console.error('템플릿 다운로드 오류:', err)
    displayToast('템플릿 다운로드에 실패했습니다.', 'error')
  }
}

// ✅ 날짜 범위 포맷팅
const formatDateRange = (startDate, endDate) => {
  if (!startDate || !endDate) return '-'
  
  const start = new Date(startDate).toLocaleDateString('ko-KR', {
    month: 'short',
    day: 'numeric'
  })
  const end = new Date(endDate).toLocaleDateString('ko-KR', {
    month: 'short',
    day: 'numeric'
  })
  
  return `${start} ~ ${end}`
}

// ✅ 기간 상태 텍스트 반환
const getPeriodStatusText = (period) => {
  if (period.is_completed) return '완료됨'

  const now = new Date()
  const startDate = new Date(period.start_date)
  const endDate = new Date(period.end_date)

  if (now < startDate) return '예정'
  if (now > endDate) return '종료됨'
  return '진행중'
}

// ✅ 기간 상태 CSS 클래스 반환
const getPeriodStatusClass = (period) => {
  if (period.is_completed) return 'status-completed'

  const now = new Date()
  const startDate = new Date(period.start_date)
  const endDate = new Date(period.end_date)

  if (now < startDate) return 'status-upcoming'
  if (now > endDate) return 'status-ended'
  return 'status-active'
}


// 페이지네이션
const changePage = (page) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
    loadCheckData()
  }
}

// 토스트
const displayToast = (message, type = 'success') => {
  toastMessage.value = message
  toastType.value = type
  showToast.value = true
  setTimeout(() => {
    showToast.value = false
  }, 3000)
}

// ✅ 연도 변경 시 모든 데이터 새로고침
watch(selectedYear, () => {
  currentPage.value = 1
  loadPeriodStatus()
  loadCheckData()
  loadAvailablePeriodsForUpload()  // ✅ 추가
})

// 기존 watch 유지
watch([selectedCheckType, selectedResult], () => {
  currentPage.value = 1
  loadCheckData()
})

watch(() => periodForm.start_date, onDateChange)
watch(() => periodForm.end_date, onDateChange)
watch(() => periodForm.check_type, onDateChange)

// ✅ 생명주기 - 기간 목록 로드 추가
onMounted(() => {
  loadPeriodStatus()
  loadCheckData()
  loadAvailablePeriodsForUpload()  // ✅ 추가
})
</script>

<style scoped>
@import '../styles/ManualCheckManagement.css';
</style>
