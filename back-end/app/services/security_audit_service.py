# app/services/audit_service.py - 제외 설정 반영 수정 버전
import json
from datetime import datetime
from app.utils.database import execute_query, DatabaseManager
from app.utils.validation import validate_security_item, generate_notes
from app.utils.constants import EXCEPTION_ITEM_NAMES
from app.services.admin_exception_service import ExceptionService


class AuditService:
    """보안 감사 관련 서비스 - 제외 설정 반영 (뷰 테이블 제거)"""

    def __init__(self):
        self.exception_service = ExceptionService()

    def get_user_stats(self, username: str, check_type: str = None) -> dict:
        """사용자별 보안 통계 데이터 조회 (하이브리드 방식으로 변경)"""
        return self.get_user_stats_hybrid(username, check_type)

    def _check_item_excluded_for_user(self, user_id: int, item_id: int) -> dict:
        """특정 사용자-항목이 제외 대상인지 확인 (모든 제외 테이블 확인)"""
        result = execute_query(
            """
            SELECT 
                CASE 
                    WHEN uie.exception_id IS NOT NULL THEN 'user'
                    WHEN uee.exception_id IS NOT NULL THEN 'user_extended'
                    WHEN die.dept_exception_id IS NOT NULL THEN 'department'
                    WHEN dee.dept_exception_id IS NOT NULL THEN 'department_extended'
                    ELSE NULL
                END as exception_type,
                COALESCE(uie.exclude_reason, uee.exclude_reason, die.exclude_reason, dee.exclude_reason) as exclude_reason,
                COALESCE(uie.exclude_type, uee.exclude_type, die.exclude_type, dee.exclude_type) as exclude_type,
                COALESCE(uie.start_date, uee.start_date, die.start_date, dee.start_date) as start_date,
                COALESCE(uie.end_date, uee.end_date, die.end_date, dee.end_date) as end_date
            FROM users u
            LEFT JOIN user_item_exceptions uie ON (
                uie.user_id = u.uid 
                AND uie.item_id = %s 
                AND uie.is_active = 1
                AND (uie.exclude_type = 'permanent' OR 
                     (uie.exclude_type = 'temporary' AND CURDATE() BETWEEN uie.start_date AND uie.end_date))
            )
            LEFT JOIN user_extended_exceptions uee ON (
                uee.user_id = u.uid 
                AND uee.item_id = CAST(%s AS CHAR)
                AND uee.item_type = 'audit_item'
                AND uee.is_active = 1
                AND (uee.exclude_type = 'permanent' OR 
                     (uee.exclude_type = 'temporary' AND CURDATE() BETWEEN uee.start_date AND uee.end_date))
            )
            LEFT JOIN department_item_exceptions die ON (
                die.department = u.department
                AND die.item_id = %s 
                AND die.is_active = 1
                AND (die.exclude_type = 'permanent' OR 
                     (die.exclude_type = 'temporary' AND CURDATE() BETWEEN die.start_date AND die.end_date))
            )
            LEFT JOIN department_extended_exceptions dee ON (
                dee.department = u.department
                AND dee.item_id = CAST(%s AS CHAR)
                AND dee.item_type = 'audit_item'
                AND dee.is_active = 1
                AND (dee.exclude_type = 'permanent' OR 
                     (dee.exclude_type = 'temporary' AND CURDATE() BETWEEN dee.start_date AND dee.end_date))
            )
            WHERE u.uid = %s
            AND (uie.exception_id IS NOT NULL OR uee.exception_id IS NOT NULL OR die.dept_exception_id IS NOT NULL OR dee.dept_exception_id IS NOT NULL)
            LIMIT 1
            """,
            (item_id, item_id, item_id, item_id, user_id),
            fetch_one=True,
        )

        if result:
            return {
                "is_excluded": True,
                "exception_type": result["exception_type"],
                "exclude_reason": result["exclude_reason"],
                "exclude_type": result["exclude_type"],
                "start_date": result["start_date"],
                "end_date": result["end_date"],
            }

        return {"is_excluded": False}

    # 나머지 메서드들도 동일한 방식으로 수정...
    def get_user_logs(self, username: str, check_type: str = None) -> list:
        return self.get_user_logs_hybrid(username, check_type)


    def _is_pending_status(self, actual_value, notes):
        """pending 상태 여부 확인"""
        # actual_value에서 pending 상태 확인
        if isinstance(actual_value, dict):
            if actual_value.get("status") == "pending":
                return True
            if "검사 대기 중" in str(actual_value.get("message", "")):
                return True
        
        # actual_value가 문자열인 경우 JSON 파싱 시도
        if isinstance(actual_value, str):
            try:
                parsed_value = json.loads(actual_value)
                if isinstance(parsed_value, dict):
                    if parsed_value.get("status") == "pending":
                        return True
                    if "검사 대기 중" in str(parsed_value.get("message", "")):
                        return True
            except (json.JSONDecodeError, TypeError):
                # JSON 파싱 실패 시 문자열로 직접 확인
                if "pending" in actual_value.lower() or "검사 대기 중" in actual_value:
                    return True
        
        # notes에서 pending 상태 확인
        if notes and ("검사 대기 중" in notes or "pending" in notes.lower()):
            return True
            
        return False


    # 나머지 메서드들은 기존과 동일 (validate_check, execute_manual_check 등)
    def validate_check(self, data: dict) -> dict:
        """항목 검증 및 로그 업데이트 (제외 설정 반영)"""
        required_fields = ["user_id", "item_type", "actual_value"]
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            raise ValueError(f"필수 필드가 누락되었습니다: {', '.join(missing_fields)}")

        # 체크리스트 항목 조회
        item_result = execute_query(
            """
            SELECT item_id, item_name, penalty_weight
            FROM checklist_items
            WHERE item_name LIKE %s AND check_type = 'daily'
            """, (data["item_type"], ), fetch_one=True)

        if not item_result:
            raise ValueError(f"[{data['item_type']}] 정기 점검 항목을 찾을 수 없습니다")

        user_id = data["user_id"]
        item_id = item_result["item_id"]
        item_name = item_result["item_name"]
        penalty_weight = float(item_result["penalty_weight"] or 0.5)
        actual_value = data["actual_value"]
        notes = data.get("notes", "")

        # 제외 설정 확인 (수정된 버전)
        exception_info = self._check_item_excluded_for_user(user_id, item_id)

        # ✅ 추가: pending 상태 자동 처리 로직
        if self._is_pending_status(actual_value, notes):
            passed = 1  # pending 상태는 자동으로 통과 처리
            if not notes or notes == "검사 대기 중":
                notes = "pending 상태 자동 통과 처리"
            else:
                notes += " [pending 상태 자동 통과 처리]"
        else:
            # 검증 로직
            passed = None
            
            # 예외 목록에 없는 경우만 검증
            if item_name not in EXCEPTION_ITEM_NAMES:
                # 검증 수행
                passed = 1 if validate_security_item(item_name, actual_value) else 0

                # 검증 결과에 따라 자동으로 notes 생성
                if notes == "":
                    notes = generate_notes(item_name, passed, actual_value)

        # 제외 설정이 있는 경우 notes에 추가
        if exception_info["is_excluded"]:
            if notes:
                notes += f" [제외사유: {exception_info['exclude_reason']}]"
            else:
                notes = f"제외사유: {exception_info['exclude_reason']}"

        # JSON 문자열로 변환
        actual_value_json = json.dumps(actual_value, ensure_ascii=False)

        # 감점 계산 (제외 설정 반영)
        if exception_info["is_excluded"]:
            penalty_applied = 0
        else:
            penalty_applied = penalty_weight if passed == 0 else 0

        # 기존 로그 업데이트 또는 새로 생성
        log_action = self._update_or_create_log(user_id, item_id, actual_value_json,
                                                passed, notes,
                                                exception_info.get('exclude_reason'))

        return {
            "status": "success",
            "item_id": item_id,
            "item_name": item_name,
            "passed": passed,
            "penalty_weight": penalty_weight,
            "penalty_applied": penalty_applied,
            "is_excluded": exception_info["is_excluded"],
            "exclude_reason": exception_info.get("exclude_reason"),
            "log_action": log_action,
        }

    def execute_manual_check(self, user_id: int, item_id: int,
                             check_result: dict) -> dict:
        """수시 점검 실행 및 결과 저장 (제외 설정 확인)"""
        # 제외 설정 확인
        exception_info = self._check_item_excluded_for_user(user_id, item_id)

        # 항목 정보 확인
        item_info = execute_query(
            """
            SELECT item_id, item_name, check_type, penalty_weight
            FROM checklist_items
            WHERE item_id = %s AND check_type = 'manual'
            """, (item_id, ), fetch_one=True)

        if not item_info:
            raise ValueError("해당 수시 점검 항목을 찾을 수 없습니다.")

        item_name = item_info["item_name"]
        penalty_weight = float(item_info["penalty_weight"] or 0.5)
        actual_value = check_result.get("actual_value", {})
        passed = check_result.get("passed")
        notes = check_result.get("notes", "")

        # 수시 점검은 수동 입력이므로 passed 값이 반드시 필요
        if passed is None:
            raise ValueError("점검 결과(통과/실패)를 반드시 입력해야 합니다.")

        # JSON 문자열로 변환
        actual_value_json = json.dumps(actual_value, ensure_ascii=False)

        # 감점 계산 (제외 설정 반영)
        if exception_info["is_excluded"]:
            penalty_applied = 0
            if notes:
                notes += f" [제외사유: {exception_info['exclude_reason']}]"
            else:
                notes = f"제외사유: {exception_info['exclude_reason']}"
        else:
            penalty_applied = penalty_weight if passed == 0 else 0

        # 로그 저장 (수시 점검은 매번 새로 생성)
        execute_query(
            """
            INSERT INTO audit_log (user_id, item_id, actual_value, passed, notes, exclude_reason)
            VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, item_id, actual_value_json, passed, notes,
                  exception_info.get('exclude_reason')
                  if exception_info["is_excluded"] else None))

        return {
            "status": "success",
            "item_id": item_id,
            "item_name": item_name,
            "passed": passed,
            "penalty_weight": penalty_weight,
            "penalty_applied": penalty_applied,
            "is_excluded": exception_info["is_excluded"],
            "exclude_reason": exception_info.get("exclude_reason"),
            "log_action": "created",
            "message": "수시 점검 결과가 성공적으로 저장되었습니다."
        }

    def _update_or_create_log(self, user_id: int, item_id: int, actual_value_json: str,
                              passed: int, notes: str,
                              exclude_reason: str = None) -> str:
        """기존 로그 업데이트 또는 새로 생성 (제외 사유 포함)"""
        # 오늘 날짜의 해당 항목 로그를 찾아서 업데이트
        existing_log = execute_query(
            """
            SELECT log_id 
            FROM audit_log 
            WHERE user_id = %s AND item_id = %s AND DATE(checked_at) = DATE(NOW())
            ORDER BY checked_at DESC
            LIMIT 1
            """, (user_id, item_id), fetch_one=True)

        if existing_log:
            # 기존 로그 업데이트
            execute_query(
                """
                UPDATE audit_log 
                SET actual_value = %s, passed = %s, notes = %s, exclude_reason = %s, checked_at = NOW()
                WHERE log_id = %s
                """, (actual_value_json, passed, notes, exclude_reason,
                      existing_log["log_id"]))
            return "updated"
        else:
            # 새로 생성
            execute_query(
                """
                INSERT INTO audit_log (user_id, item_id, actual_value, passed, notes, exclude_reason)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (user_id, item_id, actual_value_json, passed, notes, exclude_reason))
            return "created"

    def get_penalty_summary(self, username: str, check_type: str = None) -> dict:
        """사용자 감점 요약 조회 (제외 설정 반영)"""
        user_stats = self.get_user_stats(username, check_type)

        # 감점 레벨 계산
        total_penalty = user_stats.get("totalPenalty", 0)
        penalty_level = "none"
        if total_penalty > 0:
            if total_penalty <= 1.0:
                penalty_level = "low"
            elif total_penalty <= 2.5:
                penalty_level = "medium"
            else:
                penalty_level = "high"

        return {
            "total_penalty": total_penalty,
            "penalty_level": penalty_level,
            "failed_items": user_stats.get("criticalIssues", 0),
            "total_items": user_stats.get("totalChecks", 0),
            "excluded_items": user_stats.get("excludedItems", 0),
            "check_type": check_type,
            "last_audit_date": user_stats.get("lastAuditDate", "")
        }

    def get_manual_check_items(self):
        """수시 점검 가능한 항목 목록 조회 (감점 가중치 포함)"""
        return execute_query(
            """
            SELECT item_id, category, item_name as name, description, penalty_weight
            FROM checklist_items
            WHERE check_type = 'manual'
            ORDER BY category, item_name
            """, fetch_all=True)

    def get_checklist_items(self, check_type: str = None) -> list:
        """체크리스트 항목 조회 (하이브리드 방식으로 변경)"""
        return self.get_checklist_items_hybrid(check_type)

    def get_user_exceptions_summary(self, username: str) -> dict:
        """사용자의 제외 설정 요약"""
        user = execute_query("SELECT uid FROM users WHERE user_id = %s", (username, ),
                             fetch_one=True)

        if not user:
            raise ValueError("사용자 정보를 찾을 수 없습니다.")

        exceptions = self.exception_service.get_active_exceptions_for_user(user["uid"])

        return {
            "total_exceptions": len(exceptions),
            "user_specific": len(
                [e for e in exceptions if e["exception_type"] == "user"]),
            "department_based": len(
                [e for e in exceptions if e["exception_type"] == "department"]),
            "exceptions": exceptions
        }

    def get_manual_check_logs_from_results(self, username: str) -> list:
        """수시 점검 로그 조회 (manual_check_results 테이블에서)"""
        try:
            # 사용자 ID 조회
            user = execute_query("SELECT uid FROM users WHERE user_id = %s",
                                 (username, ), fetch_one=True)
            if not user:
                raise ValueError("사용자 정보를 찾을 수 없습니다.")

            user_id = user["uid"]

            # manual_check_results 테이블에서 로그 조회
            logs = execute_query(
                """
                SELECT 
                    mcr.check_id as log_id,
                    mcr.user_id,
                    mci.item_id,
                    mci.item_name,
                    mcr.check_item_code,
                    mcr.check_date as checked_at,
                    CASE 
                        WHEN mcr.overall_result = 'pass' THEN 1
                        WHEN mcr.overall_result = 'fail' THEN 0
                        ELSE NULL
                    END as passed,
                    mcr.notes,
                    'manual' as check_type,
                    'periodic' as check_frequency,
                    mci.penalty_weight,
                    CASE 
                        WHEN mcr.exclude_from_scoring = 1 THEN 0
                        WHEN mcr.overall_result = 'fail' AND mcr.exclude_from_scoring = 0 THEN COALESCE(mci.penalty_weight, 0.5)
                        ELSE 0
                    END as penalty_applied,
                    mcr.exclude_from_scoring as is_excluded,
                    mcr.exclude_reason,
                    -- 실제 값을 JSON 형태로 구성
                    JSON_OBJECT(
                        'seal_status', mcr.seal_status,
                        'seal_number', mcr.seal_number,
                        'malware_scan_result', mcr.malware_scan_result,
                        'threats_found', mcr.threats_found,
                        'threats_cleaned', mcr.threats_cleaned,
                        'antivirus_version', mcr.antivirus_version,
                        'encryption_status', mcr.encryption_status,
                        'files_scanned', mcr.files_scanned,
                        'unencrypted_files', mcr.unencrypted_files,
                        'encryption_completed', mcr.encryption_completed,
                        'total_score', mcr.total_score,
                        'penalty_points', mcr.penalty_points
                    ) as actual_value
                FROM manual_check_results mcr
                LEFT JOIN manual_check_items mci ON mcr.check_item_code = mci.item_code
                WHERE mcr.user_id = %s
                ORDER BY mcr.check_date DESC
                """, (user_id, ), fetch_all=True)

            # 결과 포맷팅
            result = []
            for log in logs:
                # 날짜 포맷팅
                if isinstance(log["checked_at"], datetime):
                    checked_at = log["checked_at"].strftime("%Y-%m-%d %H:%M:%S")
                else:
                    checked_at = log["checked_at"]

                # actual_value가 문자열인 경우 JSON 파싱
                actual_value = log["actual_value"]
                if isinstance(actual_value, str):
                    try:
                        actual_value = json.loads(actual_value)
                    except (json.JSONDecodeError, TypeError):
                        actual_value = {"raw_data": actual_value}

                result.append({
                    "log_id": log["log_id"],
                    "user_id": log["user_id"],
                    "item_id": log["item_id"]
                    or 0,  # manual_check_items에 item_id가 없을 경우 기본값
                    "item_name": log["item_name"]
                    or f"수시 점검 - {log['check_item_code']}",
                    "actual_value": actual_value,
                    "passed": log["passed"],
                    "notes": log["notes"],
                    "checked_at": checked_at,
                    "check_type": log["check_type"],
                    "check_frequency": log["check_frequency"],
                    "penalty_weight": float(log["penalty_weight"] or 0.5),
                    "penalty_applied": float(log["penalty_applied"] or 0),
                    "is_excluded": bool(log["is_excluded"])
                })

            return result

        except Exception as e:
            print(f"[ERROR] 수시 점검 로그 조회 오류: {str(e)}")
            import traceback
            traceback.print_exc()
            return []

    def get_manual_check_stats_from_results(self, username: str) -> dict:
        """수시 점검 통계 조회 (manual_check_results 테이블에서)"""
        try:
            # 사용자 ID 조회
            user = execute_query("SELECT uid FROM users WHERE user_id = %s",
                                 (username, ), fetch_one=True)
            if not user:
                raise ValueError("사용자 정보를 찾을 수 없습니다.")

            user_id = user["uid"]

            # 통계 데이터 조회
            stats_data = execute_query(
                """
                SELECT 
                    COUNT(*) as total_checks,
                    COUNT(CASE WHEN mcr.overall_result = 'pass' AND mcr.exclude_from_scoring = 0 THEN 1 END) as completed_checks,
                    COUNT(CASE WHEN mcr.overall_result = 'fail' AND mcr.exclude_from_scoring = 0 THEN 1 END) as critical_issues,
                    COUNT(CASE WHEN mcr.exclude_from_scoring = 1 THEN 1 END) as excluded_items,
                    MAX(mcr.check_date) as last_audit_date,
                    SUM(CASE 
                        WHEN mcr.overall_result = 'fail' AND mcr.exclude_from_scoring = 0 
                        THEN COALESCE(mci.penalty_weight, 0.5)
                        ELSE 0 
                    END) as total_penalty
                FROM manual_check_results mcr
                LEFT JOIN manual_check_items mci ON mcr.check_item_code = mci.item_code
                WHERE mcr.user_id = %s
                """, (user_id, ), fetch_one=True)

            if not stats_data:
                return {
                    "totalChecks": 0,
                    "activeChecks": 0,
                    "completedChecks": 0,
                    "criticalIssues": 0,
                    "excludedItems": 0,
                    "lastAuditDate": "",
                    "totalPenalty": 0.0
                }

            # 날짜 포맷팅
            last_audit_date = ""
            if stats_data["last_audit_date"]:
                if isinstance(stats_data["last_audit_date"], datetime):
                    last_audit_date = stats_data["last_audit_date"].strftime(
                        "%Y-%m-%d %H:%M:%S")
                else:
                    last_audit_date = str(stats_data["last_audit_date"])

            # 활성 점검 항목 수 (제외되지 않은 항목)
            active_checks = stats_data["completed_checks"] + stats_data[
                "critical_issues"]

            return {
                "totalChecks": stats_data["total_checks"],
                "activeChecks": active_checks,
                "completedChecks": stats_data["completed_checks"],
                "criticalIssues": stats_data["critical_issues"],
                "excludedItems": stats_data["excluded_items"],
                "lastAuditDate": last_audit_date,
                "totalPenalty": float(stats_data["total_penalty"] or 0)
            }

        except Exception as e:
            print(f"[ERROR] 수시 점검 통계 조회 오류: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "totalChecks": 0,
                "activeChecks": 0,
                "completedChecks": 0,
                "criticalIssues": 0,
                "excludedItems": 0,
                "lastAuditDate": "",
                "totalPenalty": 0.0
            }

    def get_manual_check_items_from_table(self) -> list:
        """수시 점검 항목 목록 조회 (manual_check_items 테이블에서)"""
        try:
            items = execute_query(
                """
                SELECT 
                    item_id,
                    item_code,
                    item_name as name,
                    item_category as category,
                    description,
                    penalty_weight,
                    'manual' as check_type,
                    'periodic' as check_frequency,
                    is_active
                FROM manual_check_items
                WHERE is_active = 1
                ORDER BY item_category, item_name
                """, fetch_all=True)

            # 결과 포맷팅
            result = []
            for item in items:
                result.append({
                    "item_id": item["item_id"],
                    "name": item["name"],
                    "category": item["category"],
                    "description": item["description"],
                    "check_type": item["check_type"],
                    "check_frequency": item["check_frequency"],
                    "penalty_weight": float(item["penalty_weight"] or 0.5)
                })

            return result

        except Exception as e:
            print(f"[ERROR] 수시 점검 항목 조회 오류: {str(e)}")
            import traceback
            traceback.print_exc()
            return []

    def get_user_logs_hybrid(self, username: str, check_type: str = None) -> list:
        """
        사용자별 보안 감사 로그 목록 조회 (하이브리드 방식)
        - 매일 점검(daily): audit_log 테이블 사용
        - 수시 점검(manual): manual_check_results 테이블 사용
        - 전체(all): 두 테이블 모두 사용
        """
        try:
            # 사용자 ID 조회
            user = execute_query("SELECT uid FROM users WHERE user_id = %s",
                                 (username, ), fetch_one=True)
            if not user:
                raise ValueError("사용자 정보를 찾을 수 없습니다.")

            user_id = user["uid"]
            result = []

            if check_type == 'daily':
                # 매일 점검만 - 기존 audit_log 테이블 사용
                result = self._get_daily_logs_from_audit_log(user_id)
                # None 체크 추가
                if result is None:
                    result = []
            elif check_type == 'manual':
                # 수시 점검만 - manual_check_results 테이블 사용
                result = self._get_manual_logs_from_results_table(user_id)
                # None 체크 추가
                if result is None:
                    result = []
            else:
                # 전체 - 두 테이블 모두 사용
                daily_logs = self._get_daily_logs_from_audit_log(user_id)
                manual_logs = self._get_manual_logs_from_results_table(user_id)

                # None 체크 및 기본값 설정
                if daily_logs is None:
                    daily_logs = []
                if manual_logs is None:
                    manual_logs = []

                result = daily_logs + manual_logs
                # 날짜순 정렬
                if result:
                    result.sort(key=lambda x: x.get('checked_at', ''), reverse=True)

            return result

        except Exception as e:
            print(f"[ERROR] 로그 조회 오류: {str(e)}")
            import traceback
            traceback.print_exc()
            return []

    def _get_daily_logs_from_audit_log(self, user_id: int) -> list:
        """매일 점검 로그 조회 (audit_log 테이블에서) - 오류 처리 강화"""
        try:
            logs = execute_query(
                """
                SELECT 
                    al.log_id,
                    al.user_id,
                    al.item_id,
                    ci.item_name,
                    al.actual_value,
                    al.passed,
                    al.notes,
                    al.checked_at,
                    ci.check_type,
                    ci.check_frequency,
                    ci.penalty_weight,
                    CASE 
                        WHEN (
                            EXISTS (
                                SELECT 1 FROM user_item_exceptions uie 
                                WHERE uie.user_id = al.user_id 
                                AND uie.item_id = al.item_id 
                                AND uie.is_active = 1
                                AND (uie.exclude_type = 'permanent' OR 
                                    (uie.exclude_type = 'temporary' AND CURDATE() BETWEEN uie.start_date AND uie.end_date))
                            )
                            OR EXISTS (
                                SELECT 1 FROM user_extended_exceptions uee 
                                WHERE uee.user_id = al.user_id 
                                AND uee.item_id = CAST(al.item_id AS CHAR)
                                AND uee.item_type = 'audit_item'
                                AND uee.is_active = 1
                                AND (uee.exclude_type = 'permanent' OR 
                                    (uee.exclude_type = 'temporary' AND CURDATE() BETWEEN uee.start_date AND uee.end_date))
                            )
                            OR EXISTS (
                                SELECT 1 FROM department_item_exceptions die 
                                WHERE die.department = (SELECT department FROM users WHERE uid = al.user_id)
                                AND die.item_id = al.item_id 
                                AND die.is_active = 1
                                AND (die.exclude_type = 'permanent' OR 
                                    (die.exclude_type = 'temporary' AND CURDATE() BETWEEN die.start_date AND die.end_date))
                            )
                            OR EXISTS (
                                SELECT 1 FROM department_extended_exceptions dee 
                                WHERE dee.department = (SELECT department FROM users WHERE uid = al.user_id)
                                AND dee.item_id = CAST(al.item_id AS CHAR)
                                AND dee.item_type = 'audit_item'
                                AND dee.is_active = 1
                                AND (dee.exclude_type = 'permanent' OR 
                                    (dee.exclude_type = 'temporary' AND CURDATE() BETWEEN dee.start_date AND dee.end_date))
                            )
                        ) THEN 1 ELSE 0 
                    END as is_excluded,
                    CASE 
                        WHEN (
                            EXISTS (
                                SELECT 1 FROM user_item_exceptions uie 
                                WHERE uie.user_id = al.user_id 
                                AND uie.item_id = al.item_id 
                                AND uie.is_active = 1
                                AND (uie.exclude_type = 'permanent' OR 
                                    (uie.exclude_type = 'temporary' AND CURDATE() BETWEEN uie.start_date AND uie.end_date))
                            )
                            OR EXISTS (
                                SELECT 1 FROM user_extended_exceptions uee 
                                WHERE uee.user_id = al.user_id 
                                AND uee.item_id = CAST(al.item_id AS CHAR)
                                AND uee.item_type = 'audit_item'
                                AND uee.is_active = 1
                                AND (uee.exclude_type = 'permanent' OR 
                                    (uee.exclude_type = 'temporary' AND CURDATE() BETWEEN uee.start_date AND uee.end_date))
                            )
                            OR EXISTS (
                                SELECT 1 FROM department_item_exceptions die 
                                WHERE die.department = (SELECT department FROM users WHERE uid = al.user_id)
                                AND die.item_id = al.item_id 
                                AND die.is_active = 1
                                AND (die.exclude_type = 'permanent' OR 
                                    (die.exclude_type = 'temporary' AND CURDATE() BETWEEN die.start_date AND die.end_date))
                            )
                            OR EXISTS (
                                SELECT 1 FROM department_extended_exceptions dee 
                                WHERE dee.department = (SELECT department FROM users WHERE uid = al.user_id)
                                AND dee.item_id = CAST(al.item_id AS CHAR)
                                AND dee.item_type = 'audit_item'
                                AND dee.is_active = 1
                                AND (dee.exclude_type = 'permanent' OR 
                                    (dee.exclude_type = 'temporary' AND CURDATE() BETWEEN dee.start_date AND dee.end_date))
                            )
                        ) AND al.passed = 0 THEN 0
                        WHEN al.passed = 0 THEN COALESCE(ci.penalty_weight, 0.5) 
                        ELSE 0 
                    END as penalty_applied
                FROM audit_log al
                LEFT JOIN checklist_items ci ON al.item_id = ci.item_id
                WHERE al.user_id = %s AND ci.check_type = 'daily'
                ORDER BY al.checked_at DESC
                """, (user_id, ), fetch_all=True)

            # logs가 None인 경우 빈 리스트 반환
            if logs is None:
                return []

            # 결과 포맷팅
            result = []
            for log in logs:
                try:
                    # 날짜 포맷팅
                    if isinstance(log["checked_at"], datetime):
                        checked_at = log["checked_at"].strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        checked_at = str(log["checked_at"]) if log["checked_at"] else ""

                    # actual_value JSON 파싱
                    actual_value = log["actual_value"]
                    if isinstance(actual_value, str):
                        try:
                            actual_value = json.loads(actual_value)
                        except (json.JSONDecodeError, TypeError):
                            actual_value = {"raw_data": actual_value}
                    elif actual_value is None:
                        actual_value = {}

                    result.append({
                        "log_id": log["log_id"],
                        "user_id": log["user_id"],
                        "item_id": log["item_id"],
                        "item_name": log["item_name"] or "",
                        "actual_value": actual_value,
                        "passed": log["passed"],
                        "notes": log["notes"] or "",
                        "checked_at": checked_at,
                        "check_type": log["check_type"] or "daily",
                        "check_frequency": log["check_frequency"] or "daily",
                        "penalty_weight": float(log["penalty_weight"] or 0),
                        "penalty_applied": float(log["penalty_applied"] or 0),
                        "is_excluded": bool(log["is_excluded"])
                    })
                except Exception as row_error:
                    print(f"[WARNING] 로그 행 처리 중 오류: {str(row_error)}")
                    continue

            return result

        except Exception as e:
            print(f"[ERROR] 매일 점검 로그 조회 오류: {str(e)}")
            import traceback
            traceback.print_exc()
            return []  # None 대신 빈 리스트 반환

    def get_checklist_items_hybrid(self, check_type: str = None) -> list:
        """
        체크리스트 항목 조회 (하이브리드 방식)
        - 매일 점검(daily): checklist_items 테이블 사용
        - 수시 점검(manual): manual_check_items 테이블 사용
        - 전체(all): 두 테이블 모두 사용
        """
        try:
            if check_type == 'daily':
                # 매일 점검만 - 기존 checklist_items 테이블 사용
                return execute_query(
                    """
                    SELECT item_id, category, item_name as name, description, check_type, check_frequency, penalty_weight
                    FROM checklist_items
                    WHERE check_type = 'daily'
                    ORDER BY item_id ASC
                    """, fetch_all=True)
            elif check_type == 'manual':
                # 수시 점검만 - manual_check_items 테이블 사용
                return execute_query(
                    """
                    SELECT 
                        item_id,
                        item_category as category,
                        item_name as name,
                        description,
                        'manual' as check_type,
                        'periodic' as check_frequency,
                        penalty_weight
                    FROM manual_check_items
                    WHERE is_active = 1
                    ORDER BY item_category, item_name
                    """, fetch_all=True)
            else:
                # 전체 - 두 테이블 모두 사용
                daily_items = execute_query(
                    """
                    SELECT item_id, category, item_name as name, description, check_type, check_frequency, penalty_weight
                    FROM checklist_items
                    WHERE check_type = 'daily'
                    ORDER BY item_id ASC
                    """, fetch_all=True)

                manual_items = execute_query(
                    """
                    SELECT 
                        item_id,
                        item_category as category,
                        item_name as name,
                        description,
                        'manual' as check_type,
                        'periodic' as check_frequency,
                        penalty_weight
                    FROM manual_check_items
                    WHERE is_active = 1
                    ORDER BY item_category, item_name
                    """, fetch_all=True)

                # 두 결과를 합치고 정렬
                all_items = daily_items + manual_items
                return sorted(all_items, key=lambda x:
                              (x['check_type'], x.get('item_id', 0)))

        except Exception as e:
            print(f"[ERROR] 체크리스트 항목 조회 오류: {str(e)}")
            import traceback
            traceback.print_exc()
            return ([])

        return result

    def _get_manual_logs_from_results_table(self, user_id: int) -> list:
        """수시 점검 로그 조회 (manual_check_results 테이블에서) - 오류 처리 강화"""
        try:
            logs = execute_query(
                """
                SELECT 
                    mcr.check_id as log_id,
                    mcr.user_id,
                    mci.item_id,
                    mci.item_name,
                    mcr.check_item_code,
                    mcr.check_date as checked_at,
                    CASE 
                        WHEN mcr.overall_result = 'pass' THEN 1
                        WHEN mcr.overall_result = 'fail' THEN 0
                        ELSE NULL
                    END as passed,
                    mcr.notes,
                    'manual' as check_type,
                    'periodic' as check_frequency,
                    COALESCE(mci.penalty_weight, 0.5) as penalty_weight,
                    CASE 
                        WHEN mcr.exclude_from_scoring = 1 THEN 0
                        WHEN mcr.overall_result = 'fail' AND mcr.exclude_from_scoring = 0 THEN COALESCE(mci.penalty_weight, 0.5)
                        ELSE 0
                    END as penalty_applied,
                    mcr.exclude_from_scoring as is_excluded,
                    mcr.exclude_reason,
                    -- 실제 값을 JSON 형태로 구성
                    mcr.seal_status,
                    mcr.seal_number,
                    mcr.seal_notes,
                    mcr.malware_scan_result,
                    mcr.threats_found,
                    mcr.threats_cleaned,
                    mcr.antivirus_version,
                    mcr.malware_notes,
                    mcr.malware_name,
                    mcr.malware_classification,
                    mcr.malware_path,
                    mcr.detection_item,
                    mcr.encryption_status,
                    mcr.files_scanned,
                    mcr.unencrypted_files,
                    mcr.encryption_completed,
                    mcr.encryption_notes,
                    mcr.round_number,
                    mcr.ssn_included,
                    mcr.total_score,
                    mcr.penalty_points
                FROM manual_check_results mcr
                LEFT JOIN manual_check_items mci ON mcr.check_item_code = mci.item_code
                WHERE mcr.user_id = %s
                ORDER BY mcr.check_date DESC
                """, (user_id, ), fetch_all=True)

            # logs가 None인 경우 빈 리스트 반환
            if logs is None:
                return []

            # 결과 포맷팅
            result = []
            for log in logs:
                try:
                    # 날짜 포맷팅
                    if isinstance(log["checked_at"], datetime):
                        checked_at = log["checked_at"].strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        checked_at = str(log["checked_at"]) if log["checked_at"] else ""

                    # actual_value JSON 객체 구성
                    actual_value = {
                        'seal_status': log["seal_status"],
                        'seal_number': log["seal_number"],
                        'seal_notes': log["seal_notes"],
                        'malware_scan_result': log["malware_scan_result"],
                        'threats_found': log["threats_found"],
                        'threats_cleaned': log["threats_cleaned"],
                        'antivirus_version': log["antivirus_version"],
                        'malware_notes': log["malware_notes"],
                        'malware_name': log["malware_name"],
                        'malware_classification': log["malware_classification"],
                        'malware_path': log["malware_path"],
                        'detection_item': log["detection_item"],
                        'encryption_status': log["encryption_status"],
                        'files_scanned': log["files_scanned"],
                        'unencrypted_files': log["unencrypted_files"],
                        'encryption_completed': log["encryption_completed"],
                        'encryption_notes': log["encryption_notes"],
                        'round_number': log["round_number"],
                        'ssn_included': log["ssn_included"],
                        'total_score': log["total_score"],
                        'penalty_points': log["penalty_points"]
                    }

                    # item_id가 None인 경우 기본값 설정
                    item_id = log["item_id"] if log["item_id"] is not None else 0
                    item_name = log["item_name"] if log[
                        "item_name"] else f"수시 점검 - {log['check_item_code']}"

                    result.append({
                        "log_id": log["log_id"],
                        "user_id": log["user_id"],
                        "item_id": item_id,
                        "item_name": item_name,
                        "actual_value": actual_value,
                        "passed": log["passed"],
                        "notes": log["notes"] or "",
                        "checked_at": checked_at,
                        "check_type": log["check_type"],
                        "check_frequency": log["check_frequency"],
                        "penalty_weight": float(log["penalty_weight"] or 0.5),
                        "penalty_applied": float(log["penalty_applied"] or 0),
                        "is_excluded": bool(log["is_excluded"])
                    })
                except Exception as row_error:
                    print(f"[WARNING] 수시 점검 로그 행 처리 중 오류: {str(row_error)}")
                    continue

            return result

        except Exception as e:
            print(f"[ERROR] 수시 점검 로그 조회 오류: {str(e)}")
            import traceback
            traceback.print_exc()
            return []  # None 대신 빈 리스트 반환

    def get_user_stats_hybrid(self, username: str, check_type: str = None) -> dict:
        """
        사용자별 보안 통계 데이터 조회 (하이브리드 방식)
        - 매일 점검(daily): audit_log 테이블 사용
        - 수시 점검(manual): manual_check_results 테이블 사용
        - 전체(all): 두 테이블 모두 사용
        """
        try:
            # 사용자 ID 조회
            user = execute_query("SELECT uid FROM users WHERE user_id = %s",
                                 (username, ), fetch_one=True)
            if not user:
                raise ValueError("사용자 정보를 찾을 수 없습니다.")

            user_id = user["uid"]

            if check_type == 'daily':
                # 매일 점검만 - 기존 audit_log 테이블 사용
                return self._get_daily_stats_from_audit_log(user_id)
            elif check_type == 'manual':
                # 수시 점검만 - manual_check_results 테이블 사용
                return self._get_manual_stats_from_results_table(user_id)
            else:
                # 전체 - 두 테이블 모두 사용하여 통합 통계 생성
                daily_stats = self._get_daily_stats_from_audit_log(user_id)
                manual_stats = self._get_manual_stats_from_results_table(user_id)

                # 통합 통계 계산
                return {
                    "totalChecks": daily_stats["totalChecks"] +
                    manual_stats["totalChecks"],
                    "activeChecks": daily_stats["activeChecks"] +
                    manual_stats["activeChecks"],
                    "completedChecks": daily_stats["completedChecks"] +
                    manual_stats["completedChecks"],
                    "criticalIssues": daily_stats["criticalIssues"] +
                    manual_stats["criticalIssues"],
                    "excludedItems": daily_stats["excludedItems"] +
                    manual_stats["excludedItems"],
                    "lastAuditDate": max(daily_stats["lastAuditDate"],
                                         manual_stats["lastAuditDate"]) if
                    daily_stats["lastAuditDate"] and manual_stats["lastAuditDate"] else
                    (daily_stats["lastAuditDate"] or manual_stats["lastAuditDate"]),
                    "totalPenalty": daily_stats["totalPenalty"] +
                    manual_stats["totalPenalty"]
                }

        except Exception as e:
            print(f"[ERROR] 통계 조회 오류: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "totalChecks": 0,
                "activeChecks": 0,
                "completedChecks": 0,
                "criticalIssues": 0,
                "excludedItems": 0,
                "lastAuditDate": "",
                "totalPenalty": 0.0
            }

    def _get_manual_stats_from_results_table(self, user_id: int) -> dict:
        """수시 점검 통계 조회 (manual_check_results 테이블에서)"""
        stats_data = execute_query(
            """
            SELECT 
                COUNT(*) as total_checks,
                COUNT(CASE WHEN mcr.overall_result = 'pass' AND mcr.exclude_from_scoring = 0 THEN 1 END) as completed_checks,
                COUNT(CASE WHEN mcr.overall_result = 'fail' AND mcr.exclude_from_scoring = 0 THEN 1 END) as critical_issues,
                COUNT(CASE WHEN mcr.exclude_from_scoring = 1 THEN 1 END) as excluded_items,
                MAX(mcr.check_date) as last_audit_date,
                SUM(CASE 
                    WHEN mcr.overall_result = 'fail' AND mcr.exclude_from_scoring = 0 
                    THEN COALESCE(mci.penalty_weight, 0.5)
                    ELSE 0 
                END) as total_penalty
            FROM manual_check_results mcr
            LEFT JOIN manual_check_items mci ON mcr.check_item_code = mci.item_code
            WHERE mcr.user_id = %s
            """, (user_id, ), fetch_one=True)

        if not stats_data:
            return {
                "totalChecks": 0,
                "activeChecks": 0,
                "completedChecks": 0,
                "criticalIssues": 0,
                "excludedItems": 0,
                "lastAuditDate": "",
                "totalPenalty": 0.0
            }

        # 날짜 포맷팅
        last_audit_date = ""
        if stats_data["last_audit_date"]:
            if isinstance(stats_data["last_audit_date"], datetime):
                last_audit_date = stats_data["last_audit_date"].strftime(
                    "%Y-%m-%d %H:%M:%S")
            else:
                last_audit_date = str(stats_data["last_audit_date"])

        # 활성 점검 항목 수 (제외되지 않은 항목)
        active_checks = stats_data["completed_checks"] + stats_data["critical_issues"]

        return {
            "totalChecks": stats_data["total_checks"],
            "activeChecks": active_checks,
            "completedChecks": stats_data["completed_checks"],
            "criticalIssues": stats_data["critical_issues"],
            "excludedItems": stats_data["excluded_items"],
            "lastAuditDate": last_audit_date,
            "totalPenalty": float(stats_data["total_penalty"] or 0)
        }

    def _get_daily_stats_from_audit_log(self, user_id: int) -> dict:
        """매일 점검 통계 조회 (audit_log 테이블에서)"""
        stats_data = execute_query(
            """
            SELECT 
                COUNT(DISTINCT ci.item_id) as total_items,
                COUNT(DISTINCT CASE 
                    WHEN NOT (
                        EXISTS (
                            SELECT 1 FROM user_item_exceptions uie 
                            WHERE uie.user_id = al.user_id 
                            AND uie.item_id = al.item_id 
                            AND uie.is_active = 1
                            AND (uie.exclude_type = 'permanent' OR 
                                (uie.exclude_type = 'temporary' AND CURDATE() BETWEEN uie.start_date AND uie.end_date))
                        )
                        OR EXISTS (
                            SELECT 1 FROM user_extended_exceptions uee 
                            WHERE uee.user_id = al.user_id 
                            AND uee.item_id = CAST(al.item_id AS CHAR)
                            AND uee.item_type = 'audit_item'
                            AND uee.is_active = 1
                            AND (uee.exclude_type = 'permanent' OR 
                                (uee.exclude_type = 'temporary' AND CURDATE() BETWEEN uee.start_date AND uee.end_date))
                        )
                        OR EXISTS (
                            SELECT 1 FROM department_item_exceptions die 
                            WHERE die.department = (SELECT department FROM users WHERE uid = al.user_id)
                            AND die.item_id = al.item_id 
                            AND die.is_active = 1
                            AND (die.exclude_type = 'permanent' OR 
                                (die.exclude_type = 'temporary' AND CURDATE() BETWEEN die.start_date AND die.end_date))
                        )
                        OR EXISTS (
                            SELECT 1 FROM department_extended_exceptions dee 
                            WHERE dee.department = (SELECT department FROM users WHERE uid = al.user_id)
                            AND dee.item_id = CAST(al.item_id AS CHAR)
                            AND dee.item_type = 'audit_item'
                            AND dee.is_active = 1
                            AND (dee.exclude_type = 'permanent' OR 
                                (dee.exclude_type = 'temporary' AND CURDATE() BETWEEN dee.start_date AND dee.end_date))
                        )
                    ) AND al.passed = 1 THEN al.item_id 
                END) as completed_checks,
                COUNT(DISTINCT CASE 
                    WHEN NOT (
                        EXISTS (
                            SELECT 1 FROM user_item_exceptions uie 
                            WHERE uie.user_id = al.user_id 
                            AND uie.item_id = al.item_id 
                            AND uie.is_active = 1
                            AND (uie.exclude_type = 'permanent' OR 
                                (uie.exclude_type = 'temporary' AND CURDATE() BETWEEN uie.start_date AND uie.end_date))
                        )
                        OR EXISTS (
                            SELECT 1 FROM user_extended_exceptions uee 
                            WHERE uee.user_id = al.user_id 
                            AND uee.item_id = CAST(al.item_id AS CHAR)
                            AND uee.item_type = 'audit_item'
                            AND uee.is_active = 1
                            AND (uee.exclude_type = 'permanent' OR 
                                (uee.exclude_type = 'temporary' AND CURDATE() BETWEEN uee.start_date AND uee.end_date))
                        )
                        OR EXISTS (
                            SELECT 1 FROM department_item_exceptions die 
                            WHERE die.department = (SELECT department FROM users WHERE uid = al.user_id)
                            AND die.item_id = al.item_id 
                            AND die.is_active = 1
                            AND (die.exclude_type = 'permanent' OR 
                                (die.exclude_type = 'temporary' AND CURDATE() BETWEEN die.start_date AND die.end_date))
                        )
                        OR EXISTS (
                            SELECT 1 FROM department_extended_exceptions dee 
                            WHERE dee.department = (SELECT department FROM users WHERE uid = al.user_id)
                            AND dee.item_id = CAST(al.item_id AS CHAR)
                            AND dee.item_type = 'audit_item'
                            AND dee.is_active = 1
                            AND (dee.exclude_type = 'permanent' OR 
                                (dee.exclude_type = 'temporary' AND CURDATE() BETWEEN dee.start_date AND dee.end_date))
                        )
                    ) AND al.passed = 0 THEN al.item_id 
                END) as critical_issues,
                COUNT(DISTINCT CASE 
                    WHEN (
                        EXISTS (
                            SELECT 1 FROM user_item_exceptions uie 
                            WHERE uie.user_id = al.user_id 
                            AND uie.item_id = al.item_id 
                            AND uie.is_active = 1
                            AND (uie.exclude_type = 'permanent' OR 
                                (uie.exclude_type = 'temporary' AND CURDATE() BETWEEN uie.start_date AND uie.end_date))
                        )
                        OR EXISTS (
                            SELECT 1 FROM user_extended_exceptions uee 
                            WHERE uee.user_id = al.user_id 
                            AND uee.item_id = CAST(al.item_id AS CHAR)
                            AND uee.item_type = 'audit_item'
                            AND uee.is_active = 1
                            AND (uee.exclude_type = 'permanent' OR 
                                (uee.exclude_type = 'temporary' AND CURDATE() BETWEEN uee.start_date AND uee.end_date))
                        )
                        OR EXISTS (
                            SELECT 1 FROM department_item_exceptions die 
                            WHERE die.department = (SELECT department FROM users WHERE uid = al.user_id)
                            AND die.item_id = al.item_id 
                            AND die.is_active = 1
                            AND (die.exclude_type = 'permanent' OR 
                                (die.exclude_type = 'temporary' AND CURDATE() BETWEEN die.start_date AND die.end_date))
                        )
                        OR EXISTS (
                            SELECT 1 FROM department_extended_exceptions dee 
                            WHERE dee.department = (SELECT department FROM users WHERE uid = al.user_id)
                            AND dee.item_id = CAST(al.item_id AS CHAR)
                            AND dee.item_type = 'audit_item'
                            AND dee.is_active = 1
                            AND (dee.exclude_type = 'permanent' OR 
                                (dee.exclude_type = 'temporary' AND CURDATE() BETWEEN dee.start_date AND dee.end_date))
                        )
                    ) THEN al.item_id 
                END) as excluded_items,
                MAX(al.checked_at) as last_audit_date,
                SUM(CASE 
                    WHEN NOT (
                        EXISTS (
                            SELECT 1 FROM user_item_exceptions uie 
                            WHERE uie.user_id = al.user_id 
                            AND uie.item_id = al.item_id 
                            AND uie.is_active = 1
                            AND (uie.exclude_type = 'permanent' OR 
                                (uie.exclude_type = 'temporary' AND CURDATE() BETWEEN uie.start_date AND uie.end_date))
                        )
                        OR EXISTS (
                            SELECT 1 FROM user_extended_exceptions uee 
                            WHERE uee.user_id = al.user_id 
                            AND uee.item_id = CAST(al.item_id AS CHAR)
                            AND uee.item_type = 'audit_item'
                            AND uee.is_active = 1
                            AND (uee.exclude_type = 'permanent' OR 
                                (uee.exclude_type = 'temporary' AND CURDATE() BETWEEN uee.start_date AND uee.end_date))
                        )
                        OR EXISTS (
                            SELECT 1 FROM department_item_exceptions die 
                            WHERE die.department = (SELECT department FROM users WHERE uid = al.user_id)
                            AND die.item_id = al.item_id 
                            AND die.is_active = 1
                            AND (die.exclude_type = 'permanent' OR 
                                (die.exclude_type = 'temporary' AND CURDATE() BETWEEN die.start_date AND die.end_date))
                        )
                        OR EXISTS (
                            SELECT 1 FROM department_extended_exceptions dee 
                            WHERE dee.department = (SELECT department FROM users WHERE uid = al.user_id)
                            AND dee.item_id = CAST(al.item_id AS CHAR)
                            AND dee.item_type = 'audit_item'
                            AND dee.is_active = 1
                            AND (dee.exclude_type = 'permanent' OR 
                                (dee.exclude_type = 'temporary' AND CURDATE() BETWEEN dee.start_date AND dee.end_date))
                        )
                    ) AND al.passed = 0 THEN COALESCE(ci.penalty_weight, 0.5) 
                    ELSE 0 
                END) as total_penalty
            FROM audit_log al
            INNER JOIN (
                SELECT item_id, MAX(checked_at) as max_checked_at
                FROM audit_log 
                WHERE user_id = %s
                GROUP BY item_id
            ) latest ON al.item_id = latest.item_id AND al.checked_at = latest.max_checked_at
            INNER JOIN checklist_items ci ON al.item_id = ci.item_id
            WHERE al.user_id = %s AND ci.check_type = 'daily'
            """, (user_id, user_id), fetch_one=True)

        if not stats_data:
            return {
                "totalChecks": 0,
                "activeChecks": 0,
                "completedChecks": 0,
                "criticalIssues": 0,
                "excludedItems": 0,
                "lastAuditDate": "",
                "totalPenalty": 0.0
            }

        # 날짜 포맷팅
        last_audit_date = ""
        if stats_data["last_audit_date"]:
            if isinstance(stats_data["last_audit_date"], datetime):
                last_audit_date = stats_data["last_audit_date"].strftime(
                    "%Y-%m-%d %H:%M:%S")
            else:
                last_audit_date = str(stats_data["last_audit_date"])

        # 활성 점검 항목 수 (제외되지 않은 항목)
        active_checks = stats_data["completed_checks"] + stats_data["critical_issues"]

        return {
            "totalChecks": stats_data["total_items"],
            "activeChecks": active_checks,
            "completedChecks": stats_data["completed_checks"],
            "criticalIssues": stats_data["critical_issues"],
            "excludedItems": stats_data["excluded_items"],
            "lastAuditDate": last_audit_date,
            "totalPenalty": float(stats_data["total_penalty"] or 0)
        }