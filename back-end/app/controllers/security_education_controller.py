# back-end/app/controllers/security_education_controller.py
from flask import Blueprint, request, jsonify, make_response
from datetime import datetime
from urllib.parse import quote
from app.services.security_education_service import SecurityEducationService
from app.services.education_period_service import EducationPeriodService
from app.utils.decorators import (
    token_required,
    admin_required,
    handle_exceptions,
    validate_json,
)
from app.utils.constants import HTTP_STATUS
from app.utils.database import execute_query, DatabaseManager

# Blueprint 생성
education_bp = Blueprint("security_education", __name__)

# 서비스 인스턴스
education_service = SecurityEducationService()
period_service = EducationPeriodService()




@education_bp.route("/user-summary", methods=["GET"])
@token_required
@handle_exceptions
def get_user_education_summary():
    """
    User education summary - Status determined by completion rate even after period completion
    """
    year = request.args.get("year", datetime.now().year, type=int)

    current_user = request.current_user
    user_id = current_user.get("uid")
    username = current_user.get("username")

    try:
        print(
            f"[DEBUG] User education summary query: username={username}, user_id={user_id}, year={year}"
        )

        # Get user ID
        if not user_id:
            user_data = execute_query("SELECT uid FROM users WHERE user_id = %s",
                                      (username, ), fetch_one=True)
            if not user_data:
                return (
                    jsonify({"error": "사용자 정보를 찾을 수 없습니다."}),
                    HTTP_STATUS["NOT_FOUND"],
                )
            user_id = user_data["uid"]

        # Query education status with corrected logic
        education_status = execute_query(
            """
            SELECT 
                se.course_name,
                se.completed_count,
                se.incomplete_count,
                se.total_courses,
                se.completion_rate,
                se.education_date,
                se.education_type,
                se.exclude_from_scoring,
                se.exclude_reason,
                se.notes,
                sep.period_name,
                sep.start_date,
                sep.end_date,
                sep.is_completed as period_completed,
                CASE 
                    WHEN sep.is_completed = 1 THEN
                        CASE 
                            WHEN se.completion_rate >= 100 THEN 'completed'
                            WHEN se.completion_rate > 0 THEN 'incomplete'
                            ELSE 'incomplete'
                        END
                    WHEN CURDATE() >= sep.start_date AND CURDATE() <= sep.end_date THEN
                        CASE 
                            WHEN se.completion_rate >= 100 THEN 'completed'
                            WHEN se.completion_rate > 0 THEN 'incomplete'
                            ELSE 'in_progress'
                        END
                    WHEN CURDATE() < sep.start_date THEN 'not_started'
                    WHEN CURDATE() > sep.end_date AND sep.is_completed = 0 THEN
                        CASE 
                            WHEN se.completion_rate >= 100 THEN 'completed'
                            WHEN se.completion_rate > 0 THEN 'incomplete'
                            ELSE 'expired'
                        END
                    ELSE 'unknown'
                END as status
            FROM security_education se
            LEFT JOIN security_education_periods sep ON se.period_id = sep.period_id
            WHERE se.user_id = %s AND se.education_year = %s
            ORDER BY se.course_name, se.created_at
        """,
            (user_id, year),
            fetch_all=True,
        )

        # Query periods without education records
        missing_periods = execute_query(
            """
            SELECT 
                sep.period_name as course_name,
                0 as completed_count,
                0 as incomplete_count, 
                0 as total_courses,
                0 as completion_rate,
                NULL as education_date,
                sep.education_type,
                0 as exclude_from_scoring,
                NULL as exclude_reason,
                NULL as notes,
                sep.period_name,
                sep.start_date,
                sep.end_date,
                sep.is_completed as period_completed,
                CASE 
                    WHEN sep.is_completed = 1 THEN 'incomplete'
                    WHEN CURDATE() >= sep.start_date AND CURDATE() <= sep.end_date THEN 'in_progress'
                    WHEN CURDATE() < sep.start_date THEN 'not_started'
                    WHEN CURDATE() > sep.end_date AND sep.is_completed = 0 THEN 'expired'
                    ELSE 'unknown'
                END as status
            FROM security_education_periods sep
            WHERE sep.education_year = %s
                AND NOT EXISTS (
                    SELECT 1 
                    FROM security_education se 
                    WHERE se.period_id = sep.period_id 
                    AND se.user_id = %s
                )
            ORDER BY sep.period_name
        """,
            (year, user_id),
            fetch_all=True,
        )

        # Merge results
        all_education_status = list(education_status) + list(missing_periods)

        print(f"[DEBUG] Education status query: existing records {len(education_status)}, "
              f"missing periods {len(missing_periods)}, total {len(all_education_status)}")

        # Build response data
        result_records = []
        total_completed = 0
        total_incomplete = 0
        total_in_progress = 0
        total_not_started = 0
        total_penalty = 0.0
        excluded_count = 0

        for record in all_education_status:
            # Count by status
            status = record["status"]
            if status == "completed":
                total_completed += 1
            elif status in ["incomplete", "expired"]:
                total_incomplete += 1
            elif status == "in_progress":
                total_in_progress += 1
            elif status == "not_started":
                total_not_started += 1

            # Check exclusion
            if record["exclude_from_scoring"]:
                excluded_count += 1
            
            # Calculate penalty
            penalty_applied = 0.0
            if not record["exclude_from_scoring"]:
                if status in ["incomplete", "expired"]:
                    penalty_applied = 0.5
            
            total_penalty += penalty_applied

            # Build result record
            result_record = {
                "course_name": record["course_name"],
                "completed_count": record["completed_count"] or 0,
                "incomplete_count": record["incomplete_count"] or 0,
                "total_courses": record["total_courses"] or 0,
                "completion_rate": float(record["completion_rate"] or 0),
                "education_date": (str(record["education_date"])
                                  if record["education_date"] else None),
                "education_type": record["education_type"],
                "exclude_from_scoring": bool(record["exclude_from_scoring"]),
                "exclude_reason": record["exclude_reason"],
                "notes": record["notes"],
                "period_name": record["period_name"],
                "status": status,
                "start_date": (str(record["start_date"])
                              if record["start_date"] else None),
                "end_date": (str(record["end_date"]) 
                            if record["end_date"] else None),
                "period_completed": bool(record["period_completed"]),
                "penalty_applied": penalty_applied,
            }
            result_records.append(result_record)

        # Calculate overall statistics
        total_courses = len(all_education_status)
        overall_completion_rate = 0.0
        if total_courses > 0:
            overall_completion_rate = round(
                (total_completed / total_courses) * 100, 2)

        print(f"[DEBUG] Statistics - completed: {total_completed}, incomplete: {total_incomplete}, "
              f"in_progress: {total_in_progress}, not_started: {total_not_started}, "
              f"overall completion rate: {overall_completion_rate}%")

        return jsonify({
            "year": year,
            "education_status": result_records,
            "summary": {
                "total_courses": total_courses,
                "completed": total_completed,
                "incomplete": total_incomplete,
                "in_progress": total_in_progress,
                "not_started": total_not_started,
                "completion_rate": overall_completion_rate,
                "penalty_score": round(total_penalty, 2),
                "excluded_count": excluded_count,
                "unique_courses": len(set(r["course_name"] 
                                        for r in result_records)),
                "avg_completion_rate": round(
                    sum(r["completion_rate"] for r in result_records) / 
                    len(result_records) if result_records else 0, 2
                ),
            },
        })

    except Exception as e:
        print(f"[ERROR] User education summary query failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return (
            jsonify({"error": f"교육 현황 조회 실패: {str(e)}"}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@education_bp.route("/records", methods=["GET"])
@admin_required
@handle_exceptions
def get_education_records():
    """
    ✅ 교육 기록 조회 (관리자용)
    """
    year = request.args.get("year", datetime.now().year, type=int)
    education_type = request.args.get("education_type", "")
    status = request.args.get("status", "")

    try:
        print(f"[DEBUG] 교육 기록 조회: year={year}, type={education_type}, status={status}")

        # ✅ 새로운 스키마만 사용
        records = _get_education_records(year, education_type, status)

        print(f"[DEBUG] 새 스키마 기반 응답: {len(records)}건")
        return jsonify(records)

    except Exception as e:
        print(f"[ERROR] 교육 기록 조회 실패: {str(e)}")
        return (
            jsonify({"error": f"기록 조회 실패: {str(e)}"}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


def _get_education_records(year, education_type, status):
    try:
        base_query = """
            SELECT 
                se.education_id,
                se.user_id,
                se.course_name,
                se.education_type,
                se.completed_count,
                se.incomplete_count,
                se.total_courses,
                se.completion_rate,
                se.education_date,
                se.exclude_from_scoring,
                se.exclude_reason,
                se.notes,
                se.period_id,
                u.uid,
                u.user_id,
                u.username,
                u.department,
                u.mail,
                sep.period_name,
                sep.start_date,
                sep.end_date,
                sep.is_completed as period_completed
            FROM security_education se
            LEFT JOIN users u ON se.user_id = u.uid
            LEFT JOIN security_education_periods sep ON se.period_id = sep.period_id
            WHERE se.education_year = %s
        """

        query_params = [year]

        # 필터 조건 추가
        if education_type:
            base_query += " AND se.education_type = %s"
            query_params.append(education_type)

        if status == "1":  # 완료
            base_query += " AND se.completion_rate >= 80"
        elif status == "0":  # 미완료
            base_query += " AND se.completion_rate < 80"

        base_query += " ORDER BY u.user_id, se.course_name"

        records = execute_query(base_query, tuple(query_params), fetch_all=True)
        print(f"[DEBUG] 새 스키마 조회 결과: {len(records)}건")

        result_records = []
        for record in records:
            # ✅ 감점 계산 (단순화)
            penalty_applied = (0.5 if (record["incomplete_count"] or 0) > 0
                               and not record["exclude_from_scoring"] else 0.0)

            status_text = _get_status_text(record)

            result_record = {
                "education_id": record["education_id"],
                "user_id": record["uid"],
                "login_id": record["user_id"],
                "username": record["username"],
                "department": record["department"],
                "mail": record["mail"],
                "course_name": record["course_name"],
                "education_type": record["education_type"],
                "completed_count": record["completed_count"] or 0,
                "incomplete_count": record["incomplete_count"] or 0,
                "total_courses": record["total_courses"] or 0,
                "completion_rate": float(record["completion_rate"] or 0),
                "completion_status_text": status_text,
                "education_date": (str(record["education_date"])
                                   if record["education_date"] else None),
                "exclude_from_scoring": bool(record["exclude_from_scoring"]),
                "exclude_reason": record["exclude_reason"],
                "notes": record["notes"],
                "period_id": record["period_id"],
                "period_name": record["period_name"],
                "start_date": (str(record["start_date"])
                               if record["start_date"] else None),
                "end_date": str(record["end_date"]) if record["end_date"] else None,
                "period_completed": bool(record["period_completed"]),
                "penalty_applied": penalty_applied,
            }
            result_records.append(result_record)

        print(f"[DEBUG] 새 스키마 기반 기록 조회 완료: {len(result_records)}건")
        return result_records

    except Exception as e:
        print(f"[ERROR] 새 스키마 기록 조회 오류: {str(e)}")
        return []


def _get_status_text(record):
    """Status text generation function - 100% required for completion"""
    if record["exclude_from_scoring"]:
        return "제외"

    completion_rate = float(record["completion_rate"] or 0)
    if completion_rate >= 100:
        return "완료"
    elif completion_rate > 0:
        return f"부분완료({completion_rate:.0f}%)"
    else:
        return "미실시"


@education_bp.route("/admin/records", methods=["GET"])
@admin_required
@handle_exceptions
def get_all_education_records():
    """모든 교육 기록 조회 (기존)"""
    year = request.args.get("year", datetime.now().year, type=int)
    education_type = request.args.get("education_type")

    try:
        records = education_service.get_all_education_records(year, education_type)
        return jsonify({"records": records})
    except Exception as e:
        return (
            jsonify({"error": f"기록 조회 실패: {str(e)}"}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@education_bp.route("/admin/overview", methods=["GET"])
@admin_required
@handle_exceptions
def get_education_overview():
    """교육 현황 개요 (관리자용)"""
    year = request.args.get("year", datetime.now().year, type=int)

    try:
        result = education_service.get_education_status(None, year)  # 전체 현황
        return jsonify(result)
    except Exception as e:
        return (
            jsonify({"error": f"현황 조회 실패: {str(e)}"}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@education_bp.route("/periods/active", methods=["GET"])
@admin_required
@handle_exceptions
def get_active_periods():
    """활성 교육 기간 조회"""
    year = request.args.get("year", datetime.now().year, type=int)

    try:
        # 활성 기간 조회 (완료되지 않은 기간들)
        periods = execute_query(
            """
            SELECT 
                period_id, period_name, education_type, education_year,
                start_date, end_date, is_completed, description,
                CASE 
                    WHEN CURDATE() BETWEEN start_date AND end_date THEN 'active'
                    WHEN CURDATE() < start_date THEN 'upcoming'  
                    WHEN CURDATE() > end_date THEN 'ended'
                    ELSE 'unknown'
                END as status
            FROM security_education_periods
            WHERE education_year = %s
            AND is_completed = 0
            ORDER BY education_type, start_date
            """,
            (year, ),
            fetch_all=True,
        )

        print(f"[DB_DEBUG] 조회된 활성 기간 수: {len(periods)}")

        # 날짜 포맷팅
        for period in periods:
            if period["start_date"]:
                period["start_date"] = period["start_date"].strftime("%Y-%m-%d")
            if period["end_date"]:
                period["end_date"] = period["end_date"].strftime("%Y-%m-%d")

        return jsonify({
            "success": True,
            "periods": periods,
            "year": year,
            "total_count": len(periods),
        })

    except Exception as e:
        print(f"[DB_DEBUG] 활성 기간 조회 실패: {e}")
        return (
            jsonify({
                "success": False,
                "error": f"활성 기간 조회 실패: {str(e)}",
                "periods": [],
                "year": year,
                "total_count": 0,
            }),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@education_bp.route("/bulk-upload", methods=["POST"])
@admin_required
@handle_exceptions
@validate_json(["period_id", "records"])
def bulk_upload():
    """
    ✅ 수정된 CSV 업로드 로직 - 새로운 스키마에 맞게 개선

    기존 구조 유지하면서 다음만 변경:
    1. CSV 형식: 이름,부서,수강과정,수료,미수료
    2. DB 매핑: course_name, completed_count, incomplete_count 사용
    3. 기존 completion_status 대신 새로운 컬럼 사용
    """
    data = request.json
    period_id = data.get("period_id")
    records = data.get("records", [])

    # 기본 검증 (기존 로직 유지)
    if not period_id:
        return (
            jsonify({"error": "교육 기간을 선택해주세요."}),
            HTTP_STATUS["BAD_REQUEST"],
        )

    if not records:
        return (
            jsonify({"error": "업로드할 기록이 없습니다."}),
            HTTP_STATUS["BAD_REQUEST"],
        )

    try:
        # 업로더 정보 (기존 로직 유지)
        uploaded_by = getattr(request, "current_user", {}).get("user_id", "admin")

        print(f"[DEBUG] 교육 업로드 시작 - period_id: {period_id}, records: {len(records)}건")

        # ✅ 핵심 수정: 새로운 CSV 형식 처리를 위한 서비스 호출
        result = education_service.process_csv_bulk_upload(
            period_id=period_id,
            csv_records=records,  # CSV 원본 데이터
            uploaded_by=uploaded_by,
        )

        if result["success"]:
            print(f"[DEBUG] 교육 업로드 성공: {result['message']}")

            # 기존 응답 형식 유지
            response_data = {
                "success": True,
                "message": result["message"],
                "success_count": result["success_count"],
                "update_count": result.get("update_count", 0),
                "error_count": result.get("error_count", 0),
            }

            if result.get("error_count", 0) > 0:
                response_data["errors"] = result.get("errors", [])

            return jsonify(response_data)
        else:
            print(f"[DEBUG] 교육 업로드 실패: {result.get('error')}")
            return (
                jsonify({
                    "success": False,
                    "error": result.get("error", "업로드 처리 실패")
                }),
                HTTP_STATUS["BAD_REQUEST"],
            )

    except Exception as e:
        print(f"[ERROR] 교육 업로드 예외: {str(e)}")
        return (
            jsonify({
                "success": False,
                "error": f"업로드 처리 중 오류가 발생했습니다: {str(e)}",
            }),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


def bulk_update_education_with_period(self, period_id: int, records: list) -> dict:
    """교육 결과 일괄 업로드 (특정 기간에 대해)"""
    success_count = 0
    error_count = 0
    errors = []

    try:
        with DatabaseManager() as db:
            cursor = db.cursor()

            # 기간 정보 조회
            cursor.execute(
                """
                SELECT period_id, period_name, education_type, 
                       education_year, is_completed
                FROM security_education_periods
                WHERE period_id = %s
                """,
                (period_id, ),
            )

            period_info = cursor.fetchone()
            if not period_info:
                raise ValueError("교육 기간을 찾을 수 없습니다.")

            expected_education_type = period_info["education_type"]
            education_year = period_info["education_year"]

            print(f"[DB_DEBUG] 기간 정보: {period_info}")

            for record in records:
                try:
                    # 사용자 조회
                    username = record.get("username", "").strip()
                    department = record.get("department", "").strip()
                    education_type = record.get("education_type", "").strip()

                    if not username or not department:
                        errors.append(f"필수 정보 누락: {username} ({department})")
                        error_count += 1
                        continue

                    # 교육 유형이 기간과 일치하는지 확인
                    if education_type != expected_education_type:
                        errors.append(
                            f"교육 유형 불일치: {username} - "
                            f"기대값({expected_education_type}) vs 실제값({education_type})")
                        error_count += 1
                        continue

                    # 사용자 조회 (기존 로직과 동일)
                    user_uid = self._find_user_by_name_and_department(
                        cursor, username, department)

                    if not user_uid:
                        errors.append(f"사용자를 찾을 수 없음: {username} ({department})")
                        error_count += 1
                        continue

                    # 기존 레코드 삭제 (동일 사용자 + 기간 + 교육유형)
                    cursor.execute(
                        """
                        DELETE FROM security_education
                        WHERE user_id = %s AND period_id = %s AND education_type = %s
                        """,
                        (user_uid, period_id, education_type),
                    )

                    # 새 레코드들 생성
                    completed_count = int(record.get("completed_count", 0))
                    incomplete_count = int(record.get("incomplete_count", 0))

                    # 수료 레코드 생성
                    for i in range(completed_count):
                        cursor.execute(
                            """
                            INSERT INTO security_education 
                            (user_id, period_id, education_type, completion_status, 
                             education_year, notes, created_at)
                            VALUES (%s, %s, %s, 1, %s, %s, NOW())
                            """,
                            (
                                user_uid,
                                period_id,
                                education_type,
                                education_year,
                                f"엑셀 업로드 - 수료 {i+1}회차",
                            ),
                        )

                    # 미수료 레코드 생성
                    for i in range(incomplete_count):
                        cursor.execute(
                            """
                            INSERT INTO security_education 
                            (user_id, period_id, education_type, completion_status,
                             education_year, notes, created_at)
                            VALUES (%s, %s, %s, 0, %s, %s, NOW())
                            """,
                            (
                                user_uid,
                                period_id,
                                education_type,
                                education_year,
                                f"엑셀 업로드 - 미수료 {i+1}회차",
                            ),
                        )

                    success_count += 1
                    print(
                        f"[DB_DEBUG] 성공: {username} - 수료 {completed_count}건, 미수료 {incomplete_count}건"
                    )

                except Exception as record_error:
                    error_count += 1
                    errors.append(f"{username}: {str(record_error)}")
                    print(f"[DB_DEBUG] 레코드 처리 실패: {username} - {record_error}")
                    continue

            # 트랜잭션 커밋
            cursor.execute("COMMIT")

            return {
                "success": True,
                "success_count": success_count,
                "error_count": error_count,
                "errors": errors,
                "message": f"총 {len(records)}건 중 {success_count}건 성공, {error_count}건 실패",
                "period_info": {
                    "period_id": period_id,
                    "period_name": period_info["period_name"],
                    "education_type": period_info["education_type"],
                },
            }

    except Exception as e:
        print(f"[DB_DEBUG] 일괄 업로드 실패: {e}")
        return {
            "success": False,
            "success_count": success_count,
            "error_count": error_count + 1,
            "errors": errors + [f"시스템 오류: {str(e)}"],
            "message": f"업로드 처리 중 오류가 발생했습니다: {str(e)}",
        }


def _find_user_by_name_and_department(self, cursor, username: str,
                                      department: str) -> int:
    """사용자명과 부서로 사용자 찾기 (기존 로직과 동일)"""
    print(f"[DB_DEBUG] 사용자 조회: {username} ({department})")

    # 1. 정확 매칭 (이름 + 부서)
    cursor.execute(
        "SELECT uid FROM users WHERE username = %s AND department = %s LIMIT 1",
        (username, department),
    )
    result = cursor.fetchone()

    if result:
        print(f"[DB_DEBUG] 정확 매칭으로 사용자 발견: {username} ({department})")
        return result["uid"]

    # 2. 이름만으로 검색
    cursor.execute("SELECT uid, department FROM users WHERE username = %s LIMIT 1",
                   (username, ))
    result = cursor.fetchone()

    if result:
        print(f"[DB_DEBUG] 이름으로만 사용자 발견: {username} -> 실제 부서: {result['department']}")
        return result["uid"]

    # 3. 유사 이름 검색
    cursor.execute(
        "SELECT uid, username, department FROM users WHERE username LIKE %s LIMIT 1",
        (f"%{username}%", ),
    )
    result = cursor.fetchone()

    if result:
        print(
            f"[DB_DEBUG] 유사 이름으로 사용자 발견: {result['username']} ({result['department']})")
        return result["uid"]

    print(f"[DB_DEBUG] 사용자를 찾을 수 없음: {username} ({department})")
    return None


# ✅ 템플릿 다운로드도 새로운 형식으로 수정
@education_bp.route("/template/download", methods=["GET"])
@admin_required
@handle_exceptions
def download_template():
    """CSV 업로드 템플릿 다운로드 - 새로운 형식"""
    try:
        # ✅ 수정: 새로운 CSV 형식의 템플릿 생성
        csv_data = education_service.get_new_csv_template()

        csv_bytes = csv_data.encode("utf-8")
        response = make_response(csv_bytes)

        response.headers["Content-Type"] = "text/csv; charset=utf-8"
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

        # 한글 파일명 인코딩
        filename = "정보보호교육_업로드_템플릿.csv"
        encoded_filename = quote(filename.encode("utf-8"))

        response.headers["Content-Disposition"] = (
            f"attachment; "
            f"filename*=UTF-8''{encoded_filename}; "
            f'filename="education_template.csv"')

        return response
    except Exception as e:
        return (
            jsonify({"error": f"템플릿 다운로드 실패: {str(e)}"}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@education_bp.route("/update", methods=["PUT"])
@admin_required
@handle_exceptions
@validate_json(["education_id"])
def update_education_record():
    """개별 교육 기록 수정 - Generated Column 제외"""
    data = request.json
    education_id = data.get("education_id")

    try:
        # 기존 레코드 조회
        existing_record = execute_query(
            "SELECT * FROM security_education WHERE education_id = %s",
            (education_id, ),
            fetch_one=True,
        )

        if not existing_record:
            return (
                jsonify({"error": "수정할 교육 기록을 찾을 수 없습니다."}),
                HTTP_STATUS["NOT_FOUND"],
            )

        # 수정할 필드들 - Generated Column 제외
        update_fields = []
        update_values = []

        # ✅ 직접 수정 가능한 필드들만 처리
        if "course_name" in data:
            update_fields.append("course_name = %s")
            update_values.append(data["course_name"])

        if "completed_count" in data:
            update_fields.append("completed_count = %s")
            update_values.append(
                int(data["completed_count"]
                    ) if data["completed_count"] is not None else 0)

        if "incomplete_count" in data:
            update_fields.append("incomplete_count = %s")
            update_values.append(
                int(data["incomplete_count"]
                    ) if data["incomplete_count"] is not None else 0)

        # ✅ Generated Column은 제외 (total_courses, completion_rate는 자동 계산됨)

        if "education_date" in data:
            update_fields.append("education_date = %s")
            update_values.append(data["education_date"])

        if "notes" in data:
            update_fields.append("notes = %s")
            update_values.append(data["notes"])

        if "exclude_from_scoring" in data:
            update_fields.append("exclude_from_scoring = %s")
            update_values.append(bool(data["exclude_from_scoring"]))

        if "exclude_reason" in data:
            update_fields.append("exclude_reason = %s")
            update_values.append(data["exclude_reason"])

        if not update_fields:
            return (
                jsonify({"error": "수정할 항목이 없습니다."}),
                HTTP_STATUS["BAD_REQUEST"],
            )

        # 업데이트 실행
        update_values.append(education_id)  # WHERE 조건용

        update_query = f"""
            UPDATE security_education 
            SET {', '.join(update_fields)}, updated_at = NOW()
            WHERE education_id = %s
        """

        print(f"[DB_DEBUG] 업데이트 쿼리: {update_query}")
        print(f"[DB_DEBUG] 파라미터: {tuple(update_values)}")

        execute_query(update_query, tuple(update_values))

        print(f"[DEBUG] 교육 기록 업데이트 완료: education_id={education_id}")
        print(f"[DEBUG] 업데이트된 필드: {update_fields}")

        return jsonify({"success": True, "message": "교육 기록이 성공적으로 수정되었습니다."})

    except Exception as e:
        print(f"[ERROR] 교육 기록 수정 실패: {str(e)}")
        import traceback

        traceback.print_exc()
        return (
            jsonify({"error": f"교육 기록 수정 실패: {str(e)}"}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@education_bp.route("/toggle-exception", methods=["POST"])
@admin_required
@handle_exceptions
@validate_json(["user_id", "period_id", "education_type", "exclude"])
def toggle_education_exception():
    """교육 예외 처리 토글"""
    data = request.json

    try:
        result = education_service.toggle_education_exception(
            data["user_id"],
            data["period_id"],
            data["education_type"],
            data["exclude"],
            data.get("exclude_reason", ""),
        )

        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), HTTP_STATUS["BAD_REQUEST"]

    except Exception as e:
        return (
            jsonify({"error": f"예외 처리 실패: {str(e)}"}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@education_bp.route("/delete", methods=["DELETE"])
@admin_required
@handle_exceptions
@validate_json(["user_id", "period_id", "education_type"])
def delete_education_record():
    """교육 기록 삭제"""
    data = request.json

    try:
        result = education_service.delete_education_record(data["user_id"],
                                                           data["period_id"],
                                                           data["education_type"])

        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), HTTP_STATUS["BAD_REQUEST"]

    except Exception as e:
        return (
            jsonify({"error": f"삭제 실패: {str(e)}"}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@education_bp.route("/export", methods=["GET"])
@admin_required
@handle_exceptions
def export_education_data():
    """
    교육 데이터 CSV 내보내기 - 새로운 스키마 사용

    변경사항:
    1. 새로운 스키마 컬럼 사용 (course_name, completed_count, incomplete_count 등)
    2. mail 컬럼 사용 (u.mail as email)
    3. 레거시 스키마 제거
    """
    year = request.args.get("year", datetime.now().year, type=int)
    format_type = request.args.get("format", "csv")

    try:
        if format_type != "csv":
            return (
                jsonify({"error": "현재 CSV 형식만 지원됩니다."}),
                HTTP_STATUS["BAD_REQUEST"],
            )

        # ✅ 새로운 스키마 기반 교육 데이터 조회
        education_records = execute_query(
            """
            SELECT 
                u.user_id, 
                u.username, 
                u.department,
                u.mail as email,
                se.course_name,
                se.completed_count,
                se.incomplete_count,
                se.total_courses,
                se.completion_rate,
                se.education_type, 
                se.education_year, 
                se.education_date, 
                se.notes,
                se.exclude_from_scoring, 
                se.exclude_reason,
                sep.period_name, 
                sep.start_date, 
                sep.end_date,
                -- ✅ 호환성을 위한 상태 계산
                CASE 
                    WHEN se.completion_rate >= 80 THEN '수료'
                    WHEN se.completion_rate > 0 THEN '부분완료'
                    ELSE '미수료'
                END as completion_status_text
            FROM security_education se
            JOIN users u ON se.user_id = u.uid
            LEFT JOIN security_education_periods sep ON se.period_id = sep.period_id
            WHERE se.education_year = %s
            ORDER BY u.username, se.course_name, se.created_at
            """,
            (year, ),
            fetch_all=True,
        )

        if not education_records:
            return (
                jsonify({"error": f"{year}년 교육 데이터가 없습니다."}),
                HTTP_STATUS["NOT_FOUND"],
            )

        # CSV 데이터 생성
        csv_lines = []

        # UTF-8 BOM 추가 (Excel에서 한글 인식용)
        bom = "\ufeff"

        # ✅ 새로운 헤더 구성
        headers = [
            "사용자ID",
            "사용자명",
            "부서",
            "이메일",
            "과정명",
            "수료건수",
            "미수료건수",
            "전체과정수",
            "수료율(%)",
            "교육유형",
            "교육연도",
            "교육기간",
            "수료상태",
            "교육일",
            "비고",
            "점수제외",
            "제외사유",
            "기간명",
            "시작일",
            "종료일",
        ]

        # BOM과 함께 헤더 추가
        csv_lines.append(bom + ",".join(headers))

        # ✅ 새로운 스키마 데이터 처리
        for record in education_records:
            row = [
                str(record.get("user_id", "")).replace('"', '""'),
                str(record.get("username", "")).replace('"', '""'),
                str(record.get("department", "")).replace('"', '""'),
                str(record.get("email", "")).replace('"', '""'),
                str(record.get("course_name", "")).replace('"', '""'),
                str(record.get("completed_count", 0)),
                str(record.get("incomplete_count", 0)),
                str(record.get("total_courses", 0)),
                str(float(record.get("completion_rate", 0))),
                str(record.get("education_type", "")).replace('"', '""'),
                str(record.get("education_year", "")),
                str(record.get("completion_status_text", "")).replace('"', '""'),
                str(record.get("education_date", "")).replace('"', '""'),
                str(record.get("notes", "")).replace('"', '""'),
                "제외" if record.get("exclude_from_scoring") == 1 else "포함",
                str(record.get("exclude_reason", "")).replace('"', '""'),
                str(record.get("period_name", "")).replace('"', '""'),
                str(record.get("start_date", "")).replace('"', '""'),
                str(record.get("end_date", "")).replace('"', '""'),
            ]
            # CSV RFC 4180 표준에 따라 필드를 따옴표로 감싸기
            csv_lines.append(",".join(f'"{item}"' for item in row))

        csv_content = "\n".join(csv_lines)

        # 응답 생성
        response = make_response(csv_content.encode("utf-8"))
        response.headers["Content-Type"] = "text/csv; charset=utf-8"
        response.headers["Content-Disposition"] = (
            f'attachment; filename="교육데이터_{year}.csv"')

        return response

    except Exception as e:
        print(f"[ERROR] 교육 데이터 내보내기 실패: {str(e)}")
        return (
            jsonify({"error": f"데이터 내보내기 실패: {str(e)}"}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


# ✅ 교육 기간 상태 조회 API 추가
@education_bp.route("/periods/status", methods=["GET"])
@admin_required
@handle_exceptions
def get_periods_status():
    """업로드 가능한 교육 기간 목록 조회"""
    year = request.args.get("year", datetime.now().year, type=int)

    try:
        result = period_service.get_period_status(year)
        return jsonify(result)
    except Exception as e:
        print(f"[ERROR] 교육 기간 상태 조회 실패: {str(e)}")
        return (
            jsonify({"error": f"교육 기간 상태 조회 실패: {str(e)}"}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@education_bp.route("/periods", methods=["GET"])
@admin_required
@handle_exceptions
def get_period_status():
    """교육 기간 현황 조회 (기존 엔드포인트)"""
    year = request.args.get("year", datetime.now().year, type=int)

    try:
        result = period_service.get_period_status(year)
        return jsonify(result)
    except Exception as e:
        return (
            jsonify({"error": f"기간 조회 실패: {str(e)}"}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@education_bp.route("/periods", methods=["POST"])
@admin_required
@handle_exceptions
@validate_json(
    ["education_year", "period_name", "education_type", "start_date", "end_date"])
def create_period():
    """새 교육 기간 생성"""
    data = request.json
    created_by = request.current_user.get("user_id", "admin")

    try:
        result = period_service.create_period(data, created_by)

        if result["success"]:
            return jsonify(result), HTTP_STATUS["CREATED"]
        else:
            return jsonify(result), HTTP_STATUS["BAD_REQUEST"]

    except Exception as e:
        return (
            jsonify({"error": f"기간 생성 실패: {str(e)}"}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@education_bp.route("/periods/<int:period_id>/complete", methods=["POST"])
@admin_required
@handle_exceptions
def complete_period(period_id):
    """교육 기간 완료 처리"""
    completed_by = request.current_user.get("user_id", "admin")

    try:
        result = period_service.complete_period(period_id, completed_by)

        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), HTTP_STATUS["BAD_REQUEST"]

    except Exception as e:
        return (
            jsonify({"error": f"완료 처리 실패: {str(e)}"}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@education_bp.route("/periods/<int:period_id>/reopen", methods=["POST"])
@admin_required
@handle_exceptions
def reopen_period(period_id):
    """교육 기간 재개"""
    try:
        result = period_service.reopen_period(period_id)

        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), HTTP_STATUS["BAD_REQUEST"]

    except Exception as e:
        return (
            jsonify({"error": f"재개 처리 실패: {str(e)}"}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@education_bp.route("/periods/<int:period_id>", methods=["DELETE"])
@admin_required
@handle_exceptions
def delete_education_period(period_id):
    """교육 기간 삭제"""
    try:
        result = period_service.delete_education_period(period_id)

        if result["success"]:
            return jsonify({"message": result["message"]})
        else:
            # requires_confirmation이 있는 경우 400으로 반환
            status_code = HTTP_STATUS["BAD_REQUEST"]
            response_data = {"error": result["message"]}

            # 확인이 필요한 경우 추가 정보 포함
            if result.get("requires_confirmation"):
                response_data["requires_confirmation"] = True
                response_data["education_count"] = result.get("education_count", 0)

            return jsonify(response_data), status_code

    except Exception as e:
        print(f"[ERROR] 교육 기간 삭제 실패: {str(e)}")
        return (
            jsonify({"error": f"교육 기간 삭제 실패: {str(e)}"}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@education_bp.route("/periods/<int:period_id>/force-delete", methods=["DELETE"])
@admin_required
@handle_exceptions
def force_delete_education_period(period_id):
    """교육 기간 강제 삭제 (교육 기록 포함)"""
    try:
        result = period_service.force_delete_education_period(period_id)

        if result["success"]:
            return jsonify({"message": result["message"]})
        else:
            return jsonify({"error": result["message"]}), HTTP_STATUS["BAD_REQUEST"]

    except Exception as e:
        print(f"[ERROR] 교육 기간 강제 삭제 실패: {str(e)}")
        return (
            jsonify({"error": f"교육 기간 강제 삭제 실패: {str(e)}"}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@education_bp.route("/periods/<int:period_id>", methods=["PUT"])
@admin_required
@handle_exceptions
@validate_json(
    ["education_year", "period_name", "education_type", "start_date", "end_date"])
def update_education_period(period_id):
    """교육 기간 수정"""
    data = request.json
    updated_by = request.current_user.get("user_id", "admin")

    try:
        print(f"[DEBUG] 교육 기간 수정 요청: period_id={period_id}, data={data}")

        result = period_service.update_period(period_id, data, updated_by)

        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), HTTP_STATUS["BAD_REQUEST"]

    except Exception as e:
        print(f"[ERROR] 교육 기간 수정 실패: {str(e)}")
        return (
            jsonify({"error": f"기간 수정 실패: {str(e)}"}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@education_bp.route('/periods/statistics', methods=['GET'])
@admin_required
@handle_exceptions
def get_periods_with_statistics():
    """교육 기간 목록과 통계 정보 조회"""
    try:
        year = request.args.get('year', type=int)
        if not year:
            year = datetime.now().year

        # 교육 기간별 통계를 포함한 쿼리
        query = """
        SELECT 
            sep.period_id,
            sep.education_year,
            sep.period_name,
            sep.education_type,
            sep.start_date,
            sep.end_date,
            sep.is_completed,
            sep.completed_at,
            sep.completed_by,
            sep.description,
            sep.auto_pass_setting,
            sep.created_by,
            sep.created_at,
            sep.updated_at,
            -- 통계 정보 (사용자 상태 기반)
            COUNT(DISTINCT se.user_id) as total_participants,
            -- 성공: incomplete_count = 0인 사용자 수
            COUNT(DISTINCT CASE WHEN se.incomplete_count = 0 THEN se.user_id END) as success_user_count,
            -- 실패: incomplete_count > 0인 사용자 수  
            COUNT(DISTINCT CASE WHEN se.incomplete_count > 0 THEN se.user_id END) as failure_user_count,
            -- 성공률: 성공한 사용자 / 전체 참가자
            COALESCE(
                CASE 
                    WHEN COUNT(DISTINCT se.user_id) > 0 
                    THEN ROUND(
                        (COUNT(DISTINCT CASE WHEN se.incomplete_count = 0 THEN se.user_id END) / COUNT(DISTINCT se.user_id)) * 100, 
                        2
                    )
                    ELSE 0 
                END, 
                0
            ) as success_rate
        FROM security_education_periods sep
        LEFT JOIN security_education se ON sep.period_id = se.period_id
        WHERE sep.education_year = %s
        GROUP BY sep.period_id
        ORDER BY sep.education_type, sep.start_date DESC
        """

        periods = execute_query(query, (year, ), fetch_all=True)

        # 교육 유형별로 그룹화
        education_types = {}

        for period in periods:
            education_type = period['education_type']

            if education_type not in education_types:
                education_types[education_type] = {
                    'type_name': education_type,
                    'periods': [],
                    'total_participants': 0,
                    'total_success': 0,
                    'total_failure': 0
                }

            # 기간별 상태 결정
            status = determine_period_status(period)

            period_info = {
                'period_id': period['period_id'],
                'period_name': period['period_name'],
                'education_year': period['education_year'],
                'education_type': period['education_type'],
                'start_date': period['start_date'].isoformat()
                if period['start_date'] else None,
                'end_date': period['end_date'].isoformat()
                if period['end_date'] else None,
                'is_completed': bool(period['is_completed']),
                'completed_at': period['completed_at'].isoformat()
                if period['completed_at'] else None,
                'completed_by': period['completed_by'],
                'description': period['description'],
                'status': status,
                # 통계 정보
                'statistics': {
                    'total_participants': int(period['total_participants'] or 0),
                    'success_user_count': int(period['success_user_count'] or 0),
                    'failure_user_count': int(period['failure_user_count'] or 0),
                    'success_rate': float(period['success_rate'] or 0),
                    'total_attempts': int(period['total_participants']
                                          or 0)  # 총 참가자와 동일
                }
            }

            education_types[education_type]['periods'].append(period_info)

            # 교육 유형별 통계 누적
            education_types[education_type]['total_participants'] += period_info[
                'statistics']['total_participants']
            education_types[education_type]['total_success'] += period_info[
                'statistics']['success_user_count']
            education_types[education_type]['total_failure'] += period_info[
                'statistics']['failure_user_count']

        # 교육 유형별 성공률 계산
        for type_data in education_types.values():
            if type_data['total_participants'] > 0:
                type_data['success_rate'] = round(
                    (type_data['total_success'] / type_data['total_participants']) *
                    100, 2)
            else:
                type_data['success_rate'] = 0.0

        return jsonify({
            'success': True,
            'year': year,
            'education_types': education_types,
            'total_periods': len(periods)
        })

    except Exception as e:
        print(f"교육 기간 통계 조회 실패: {str(e)}")
        return jsonify({
            'success': False,
            'message': '교육 기간 통계 조회에 실패했습니다.',
            'error': str(e)
        }), 500


@education_bp.route('/periods/<int:period_id>/statistics', methods=['GET'])
@admin_required
@handle_exceptions
def get_period_detailed_statistics(period_id):
    """특정 교육 기간의 상세 통계"""
    try:
        # 기간별 상세 통계 쿼리
        detailed_stats = execute_query(
            """
            SELECT 
                u.username,
                u.department,
                se.completed_count,
                se.incomplete_count,
                se.total_courses,
                se.completion_rate,
                se.education_date,
                se.exclude_from_scoring,
                se.exclude_reason
            FROM security_education se
            JOIN users u ON se.user_id = u.uid  
            WHERE se.period_id = %s
            ORDER BY u.department, u.username
        """, (period_id, ), fetch_all=True)

        # 부서별 통계 계산
        department_stats = {}
        for record in detailed_stats:
            dept = record['department']
            if dept not in department_stats:
                department_stats[dept] = {
                    'department': dept,
                    'participants': 0,
                    'success_users': 0,
                    'failure_users': 0,
                    'success_rate': 0
                }

            department_stats[dept]['participants'] += 1
            # 사용자 상태 기반 판단
            if record['incomplete_count'] == 0:
                department_stats[dept]['success_users'] += 1
            else:
                department_stats[dept]['failure_users'] += 1

        # 부서별 성공률 계산
        for dept_stat in department_stats.values():
            if dept_stat['participants'] > 0:
                dept_stat['success_rate'] = round(
                    (dept_stat['success_users'] / dept_stat['participants']) * 100, 2)
            else:
                dept_stat['success_rate'] = 0

        # 전체 요약 통계
        total_participants = len(detailed_stats)
        success_users = len([r for r in detailed_stats if r['incomplete_count'] == 0])
        failure_users = len([r for r in detailed_stats if r['incomplete_count'] > 0])

        return jsonify({
            'success': True,
            'period_id': period_id,
            'participant_details': [
                {
                    'username': r['username'],
                    'department': r['department'],
                    'completed_count': r['completed_count'] or 0,
                    'incomplete_count': r['incomplete_count'] or 0,
                    'completion_rate': float(r['completion_rate'] or 0),
                    'education_date': r['education_date'].isoformat()
                    if r['education_date'] else None,
                    'exclude_from_scoring': bool(r['exclude_from_scoring']),
                    'exclude_reason': r['exclude_reason'],
                    'user_status': 'success'
                    if r['incomplete_count'] == 0 else 'failure'  # 사용자 상태 추가
                } for r in detailed_stats
            ],
            'department_statistics': list(department_stats.values()),
            'summary': {
                'total_participants': total_participants,
                'success_users': success_users,
                'failure_users': failure_users,
                'overall_success_rate': round((success_users / total_participants) *
                                              100, 2) if total_participants > 0 else 0
            }
        })

    except Exception as e:
        print(f"교육 기간 상세 통계 조회 실패: {str(e)}")
        return jsonify({
            'success': False,
            'message': '상세 통계 조회에 실패했습니다.',
            'error': str(e)
        }), 500


def determine_period_status(period):
    """교육 기간 상태 결정"""
    from datetime import date

    today = date.today()
    start_date = period['start_date']
    end_date = period['end_date']
    is_completed = period['is_completed']

    if is_completed:
        return 'completed'
    elif today < start_date:
        return 'not_started'
    elif start_date <= today <= end_date:
        return 'in_progress'
    elif today > end_date:
        return 'expired'
    else:
        return 'unknown'
