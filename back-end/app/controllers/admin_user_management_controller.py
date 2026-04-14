# app/controllers/admin_user_management_controller.py
"""
관리자 사용자 관리 API 컨트롤러
- 사용자 목록 조회 (필터링, 정렬, 페이징)
- 사용자 검색
- 일괄 내보내기
- 사용자 선택 및 관리
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
from app.utils.decorators import token_required, handle_exceptions, admin_required
from app.utils.constants import HTTP_STATUS
from app.utils.database import execute_query
import logging
import csv
import io
from flask import make_response

# 블루프린트 생성
admin_user_management_bp = Blueprint(
    "admin_user_management", __name__, url_prefix="/api/admin/dashboard"
)


# ============================================================
# API 엔드포인트
# ============================================================


@admin_user_management_bp.route("/users", methods=["GET"])
@token_required
@admin_required
@handle_exceptions
def get_users_list():
    """사용자 목록 조회 (필터링, 검색, 페이징)"""
    year = request.args.get("year", datetime.now().year, type=int)
    department = request.args.get("department", "")
    position = request.args.get("position", "")
    risk_level = request.args.get("risk_level", "")
    search = request.args.get("search", "")
    status = request.args.get("status", "")          # ✅ 활성/비활성 필터
    ip_subnet = request.args.get("ip_subnet", "")    # ✅ IP 대역 필터
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    sort_by = request.args.get("sort_by", "total_penalty")
    sort_order = request.args.get("sort_order", "desc")

    try:
        logging.info(
            f"사용자 목록 조회: year={year}, dept={department}, "
            f"status={status}, ip_subnet={ip_subnet}, search={search}, page={page}"
        )

        # 필터링된 사용자 데이터 조회
        users_data, total_count = _get_filtered_users(
            year=year,
            department=department,
            position=position,
            risk_level=risk_level,
            search=search,
            status=status,
            ip_subnet=ip_subnet,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        logging.info(f"조회 완료: {len(users_data)}명 / 전체 {total_count}명")

        response_data = {
            "users": users_data,
            "pagination": {
                "current_page": page,
                "per_page": per_page,
                "total_count": total_count,
                "total_pages": (total_count + per_page - 1) // per_page,
            },
            "filters": {
                "year": year,
                "department": department,
                "position": position,
                "risk_level": risk_level,
                "search": search,
                "status": status,
                "ip_subnet": ip_subnet,
                "sort_by": sort_by,
                "sort_order": sort_order,
            },
        }

        return jsonify(response_data)

    except Exception as e:
        logging.error(f"Users list error: {str(e)}")
        return (
            jsonify(
                {"error": "사용자 목록 조회 중 오류가 발생했습니다.", "details": str(e)}
            ),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@admin_user_management_bp.route("/users/export", methods=["GET"])
@token_required
@admin_required
@handle_exceptions
def export_users():
    """사용자 데이터 내보내기"""
    year = request.args.get("year", datetime.now().year, type=int)
    user_ids = request.args.get("user_ids", "")
    format_type = request.args.get("format", "csv")
    export_type = request.args.get("type", "selected")

    # 추가 필터 파라미터
    department = request.args.get("department", "")
    position = request.args.get("position", "")
    risk_level = request.args.get("risk_level", "")
    search = request.args.get("search", "")
    status = request.args.get("status", "")
    ip_subnet = request.args.get("ip_subnet", "")

    try:
        if export_type == "selected" and user_ids:
            # 선택된 사용자만 내보내기
            user_id_list = [
                int(uid.strip()) for uid in user_ids.split(",") if uid.strip()
            ]
            return _export_selected_users(user_id_list, year, format_type)
        elif export_type == "filtered":
            # 필터된 사용자 전체 내보내기
            return _export_filtered_users(
                year, department, position, risk_level, search,
                format_type, status=status, ip_subnet=ip_subnet,
            )
        else:
            # 전체 사용자 내보내기
            return _export_all_users(year, format_type)

    except Exception as e:
        logging.error(f"Export users error: {str(e)}")
        return (
            jsonify(
                {
                    "error": "사용자 데이터 내보내기 중 오류가 발생했습니다.",
                    "details": str(e),
                }
            ),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@admin_user_management_bp.route("/users/search", methods=["GET"])
@token_required
@admin_required
@handle_exceptions
def search_users():
    """사용자 실시간 검색"""
    query = request.args.get("q", "").strip()
    limit = request.args.get("limit", 10, type=int)

    if not query or len(query) < 2:
        return jsonify({"users": []})

    try:
        search_query = """
            SELECT 
                u.uid,
                u.username as name,
                u.user_id as employee_id,
                u.department,
                u.position,
                u.mail as email,
                u.ip
            FROM users u
            WHERE u.is_active = 1 
            AND (
                u.username LIKE %s 
                OR u.user_id LIKE %s 
                OR u.mail LIKE %s
                OR u.department LIKE %s
                OR u.ip LIKE %s
            )
            ORDER BY 
                CASE 
                    WHEN u.username LIKE %s THEN 1
                    WHEN u.user_id LIKE %s THEN 2
                    WHEN u.ip LIKE %s THEN 3
                    ELSE 4
                END,
                u.username
            LIMIT %s
        """

        search_term = f"%{query}%"
        exact_term = f"{query}%"

        users = execute_query(
            search_query,
            (
                search_term, search_term, search_term, search_term, search_term,
                exact_term, exact_term, exact_term,
                limit,
            ),
        )

        return jsonify({"users": users})

    except Exception as e:
        logging.error(f"Search users error: {str(e)}")
        return (
            jsonify(
                {"error": "사용자 검색 중 오류가 발생했습니다.", "details": str(e)}
            ),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@admin_user_management_bp.route("/users/filters", methods=["GET"])
@token_required
@admin_required
@handle_exceptions
def get_filter_options():
    """필터 옵션 조회 (부서, 직급 목록)"""
    try:
        # 부서 목록 조회 (비활성 사용자 포함)
        departments_query = """
            SELECT DISTINCT department 
            FROM users 
            WHERE department IS NOT NULL AND department != ''
            ORDER BY department
        """
        departments = [row["department"] for row in execute_query(departments_query)]

        # 직급 목록 조회
        positions_query = """
            SELECT DISTINCT position 
            FROM users 
            WHERE position IS NOT NULL AND position != ''
            ORDER BY position
        """
        positions = [row["position"] for row in execute_query(positions_query)]

        # IP 대역 목록 조회
        ip_subnets_query = """
            SELECT DISTINCT 
                SUBSTRING_INDEX(ip, '.', 3) as ip_subnet
            FROM users 
            WHERE ip IS NOT NULL AND ip != ''
            ORDER BY INET_ATON(CONCAT(SUBSTRING_INDEX(ip, '.', 3), '.0'))
        """
        try:
            ip_subnets = [row["ip_subnet"] for row in execute_query(ip_subnets_query)]
        except Exception:
            ip_subnets = []

        return jsonify(
            {
                "departments": departments,
                "positions": positions,
                "ip_subnets": ip_subnets,
                "risk_levels": [
                    {"value": "low", "label": "우수"},
                    {"value": "medium", "label": "주의"},
                    {"value": "high", "label": "위험"},
                    {"value": "critical", "label": "매우 위험"},
                ],
                "statuses": [
                    {"value": "active", "label": "활성"},
                    {"value": "inactive", "label": "비활성"},
                ],
            }
        )

    except Exception as e:
        logging.error(f"Filter options error: {str(e)}")
        return (
            jsonify(
                {"error": "필터 옵션 조회 중 오류가 발생했습니다.", "details": str(e)}
            ),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


# ============================================================
# 핵심 헬퍼 함수: _get_filtered_users
# ============================================================


def _get_filtered_users(
    year,
    department="",
    position="",
    risk_level="",
    search="",
    status="",
    ip_subnet="",
    page=1,
    per_page=20,
    sort_by="total_penalty",
    sort_order="desc",
):
    """
    필터링된 사용자 목록 조회
    - status: "active" | "inactive" | "" (전체)
    - ip_subnet: IP 대역 필터 (예: "192.168.1")
    - search: 이름, 사번, 부서, IP 통합 검색
    """
    try:
        # WHERE 조건 구성
        where_conditions = []
        params = []

        # ✅ 활성/비활성 상태 필터
        if status == "active":
            where_conditions.append("u.is_active = 1")
        elif status == "inactive":
            where_conditions.append("u.is_active = 0")
        # status가 빈 문자열이면 전체 조회 (조건 없음)

        # ✅ IP 대역 필터
        if ip_subnet:
            where_conditions.append("u.ip LIKE %s")
            params.append(f"{ip_subnet}%")

        # ✅ 통합 검색 (이름, 사번, 부서, IP)
        if search:
            where_conditions.append(
                "(u.username LIKE %s OR u.user_id LIKE %s OR u.department LIKE %s OR u.ip LIKE %s)"
            )
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param, search_param])

        # 부서 필터
        if department:
            where_conditions.append("u.department = %s")
            params.append(department)

        # 직급 필터
        if position:
            where_conditions.append("u.position = %s")
            params.append(position)

        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

        # 정렬 필드 검증
        allowed_sort_fields = {
            "name": "u.username",
            "department": "u.department",
            "total_penalty": "COALESCE(sss.total_penalty, 0)",
            "last_updated": "sss.last_calculated",
        }

        sort_field = allowed_sort_fields.get(sort_by, "COALESCE(sss.total_penalty, 0)")
        order = "DESC" if sort_order.upper() == "DESC" else "ASC"

        # 리스크 레벨 필터 (HAVING 대신 서브쿼리나 조건으로 처리)
        risk_condition = ""
        if risk_level:
            risk_conditions = {
                "critical": "COALESCE(sss.total_penalty, 0) > 5.0",
                "high": "COALESCE(sss.total_penalty, 0) > 2.0 AND COALESCE(sss.total_penalty, 0) <= 5.0",
                "medium": "COALESCE(sss.total_penalty, 0) > 0.5 AND COALESCE(sss.total_penalty, 0) <= 2.0",
                "low": "COALESCE(sss.total_penalty, 0) <= 0.5",
            }
            if risk_level in risk_conditions:
                risk_condition = risk_conditions[risk_level]
                if where_clause != "1=1":
                    where_clause += f" AND ({risk_condition})"
                else:
                    where_clause = risk_condition

        # 전체 개수 조회
        count_query = f"""
            SELECT COUNT(DISTINCT u.uid) as cnt
            FROM users u
            LEFT JOIN security_score_summary sss 
                ON u.uid = sss.user_id AND sss.evaluation_year = %s
            WHERE {where_clause}
        """

        count_params = [year] + params
        count_result = execute_query(count_query, count_params, fetch_one=True)
        total_count = count_result["cnt"] if count_result else 0

        # 페이지네이션
        offset = (page - 1) * per_page

        # 메인 데이터 조회
        data_query = f"""
            SELECT 
                u.uid,
                u.username as name,
                u.user_id,
                u.mail as email,
                u.ip,
                u.department,
                u.role,
                u.is_active,
                u.created_at,
                u.updated_at,
                COALESCE(sss.total_penalty, 0) as total_penalty,
                COALESCE(sss.audit_penalty, 0) as audit_penalty,
                COALESCE(sss.education_penalty, 0) as education_penalty,
                COALESCE(sss.training_penalty, 0) as training_penalty,
                COALESCE(sss.audit_failed_count, 0) as audit_failed_count,
                COALESCE(sss.education_incomplete_count, 0) as education_incomplete_count,
                COALESCE(sss.training_failed_count, 0) as training_failed_count,
                sss.last_calculated
            FROM users u
            LEFT JOIN security_score_summary sss 
                ON u.uid = sss.user_id AND sss.evaluation_year = %s
            WHERE {where_clause}
            ORDER BY {sort_field} {order}, u.username ASC
            LIMIT %s OFFSET %s
        """

        data_params = [year] + params + [per_page, offset]
        users = execute_query(data_query, data_params)

        # 결과 데이터 포맷팅
        users_data = []
        for user in users:
            user_dict = dict(user)

            # is_active 변환
            is_active_raw = user_dict.get("is_active")
            if is_active_raw is None:
                user_dict["is_active"] = True
            elif is_active_raw == 0:
                user_dict["is_active"] = False
            else:
                user_dict["is_active"] = True

            # 날짜 포맷팅
            for date_field in ["last_calculated", "created_at", "updated_at"]:
                if user_dict.get(date_field):
                    if hasattr(user_dict[date_field], "isoformat"):
                        user_dict[date_field] = user_dict[date_field].isoformat()
                    else:
                        user_dict[date_field] = str(user_dict[date_field])

            # 리스크 레벨 계산
            total_penalty = float(user_dict.get("total_penalty", 0))
            if total_penalty == 0:
                risk_level_val = "low"
            elif total_penalty <= 0.5:
                risk_level_val = "low"
            elif total_penalty <= 2.0:
                risk_level_val = "medium"
            elif total_penalty <= 5.0:
                risk_level_val = "high"
            else:
                risk_level_val = "critical"

            user_dict["risk_level"] = risk_level_val
            users_data.append(user_dict)

        return users_data, total_count

    except Exception as e:
        logging.error(f"Filtered users query error: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        raise


# ============================================================
# 내보내기 헬퍼 함수들
# ============================================================


def _export_selected_users(user_ids, year, format_type):
    """선택된 사용자 내보내기"""
    try:
        if not user_ids:
            raise ValueError("내보낼 사용자가 선택되지 않았습니다.")

        placeholders = ",".join(["%s"] * len(user_ids))
        users_query = f"""
            SELECT 
                u.username as name,
                u.user_id as employee_id,
                u.department,
                u.position,
                u.mail as email,
                u.ip,
                COALESCE(sss.total_penalty, 0) as total_penalty,
                COALESCE(sss.audit_penalty, 0) as audit_penalty,
                COALESCE(sss.education_penalty, 0) as education_penalty,
                COALESCE(sss.training_penalty, 0) as training_penalty,
                COALESCE(sss.audit_failed_count, 0) as audit_failed_count,
                COALESCE(sss.education_incomplete_count, 0) as education_incomplete_count,
                COALESCE(sss.training_failed_count, 0) as training_failed_count,
                sss.last_calculated,
                CASE 
                    WHEN sss.total_penalty IS NULL THEN '미평가'
                    WHEN sss.total_penalty > 5.0 THEN '매우 위험'
                    WHEN sss.total_penalty > 2.0 THEN '위험'
                    WHEN sss.total_penalty > 0.5 THEN '주의'
                    ELSE '우수'
                END as risk_level
            FROM users u
            LEFT JOIN security_score_summary sss 
                ON u.uid = sss.user_id AND sss.evaluation_year = %s
            WHERE u.uid IN ({placeholders})
            ORDER BY sss.total_penalty DESC, u.username
        """

        users_data = execute_query(users_query, [year] + user_ids)

        return _create_csv_response(
            users_data, f"selected_users_{len(user_ids)}_members_{year}"
        )

    except Exception as e:
        logging.error(f"Export selected users error: {str(e)}")
        raise e


def _export_filtered_users(
    year, department, position, risk_level, search, format_type,
    status="", ip_subnet="",
):
    """필터된 사용자 전체 내보내기"""
    try:
        users_data, _ = _get_filtered_users(
            year=year,
            department=department,
            position=position,
            risk_level=risk_level,
            search=search,
            status=status,
            ip_subnet=ip_subnet,
            page=1,
            per_page=999999,
            sort_by="total_penalty",
            sort_order="desc",
        )

        filename_parts = ["filtered_users"]
        if department:
            filename_parts.append(f"dept_{department}")
        if position:
            filename_parts.append(f"pos_{position}")
        if risk_level:
            filename_parts.append(f"risk_{risk_level}")
        if status:
            filename_parts.append(f"status_{status}")
        filename_parts.append(str(year))

        filename = "_".join(filename_parts)

        return _create_csv_response(users_data, filename)

    except Exception as e:
        logging.error(f"Export filtered users error: {str(e)}")
        raise e


def _export_all_users(year, format_type):
    """전체 사용자 내보내기"""
    try:
        users_data, _ = _get_filtered_users(
            year=year,
            page=1,
            per_page=999999,
            sort_by="total_penalty",
            sort_order="desc",
        )

        return _create_csv_response(users_data, f"all_users_{year}")

    except Exception as e:
        logging.error(f"Export all users error: {str(e)}")
        raise e


def _create_csv_response(users_data, filename):
    """CSV 응답 생성"""
    try:
        output = io.StringIO()
        writer = csv.writer(output)

        # 헤더
        writer.writerow(
            [
                "이름",
                "사번",
                "부서",
                "직급",
                "이메일",
                "IP주소",
                "상태",
                "총 감점",
                "감사 감점",
                "교육 감점",
                "훈련 감점",
                "감사 실패",
                "교육 미완료",
                "훈련 실패",
                "위험도",
                "마지막 업데이트",
            ]
        )

        # 데이터
        for user in users_data:
            # is_active 처리
            is_active = user.get("is_active")
            if isinstance(is_active, bool):
                status_text = "활성" if is_active else "비활성"
            else:
                status_text = "활성" if is_active in (1, True, "true") else "비활성"

            writer.writerow(
                [
                    user.get("name", ""),
                    user.get("employee_id", user.get("user_id", "")),
                    user.get("department", ""),
                    user.get("position", ""),
                    user.get("email", ""),
                    user.get("ip", ""),
                    status_text,
                    f"{float(user.get('total_penalty', 0)):.2f}",
                    f"{float(user.get('audit_penalty', 0)):.2f}",
                    f"{float(user.get('education_penalty', 0)):.2f}",
                    f"{float(user.get('training_penalty', 0)):.2f}",
                    user.get("audit_failed_count", 0),
                    user.get("education_incomplete_count", 0),
                    user.get("training_failed_count", 0),
                    user.get("risk_level", "미평가"),
                    user.get("last_calculated", user.get("last_updated", "")),
                ]
            )

        csv_content = output.getvalue()
        output.close()

        # UTF-8 BOM 추가 (Excel 호환성)
        csv_content = "\ufeff" + csv_content

        response = make_response(csv_content.encode("utf-8"))
        response.headers["Content-Type"] = "text/csv; charset=utf-8"
        response.headers["Content-Disposition"] = f"attachment; filename={filename}.csv"
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

        return response

    except Exception as e:
        logging.error(f"Create CSV response error: {str(e)}")
        raise e


# ============================================================
# 통계 헬퍼 함수
# ============================================================


def _get_user_statistics_summary():
    """사용자 통계 요약"""
    try:
        current_year = datetime.now().year

        stats_query = """
            SELECT 
                COUNT(*) as total_active_users,
                COUNT(CASE WHEN sss.total_penalty IS NOT NULL THEN 1 END) as evaluated_users,
                COUNT(CASE WHEN sss.total_penalty <= 0.5 THEN 1 END) as excellent_users,
                COUNT(CASE WHEN sss.total_penalty > 2.0 THEN 1 END) as risk_users,
                COALESCE(AVG(sss.total_penalty), 0) as avg_penalty
            FROM users u
            LEFT JOIN security_score_summary sss 
                ON u.uid = sss.user_id AND sss.evaluation_year = %s
            WHERE u.is_active = 1
        """

        result = execute_query(stats_query, (current_year,), fetch_one=True)
        return dict(result) if result else {}

    except Exception as e:
        logging.error(f"User statistics summary error: {str(e)}")
        return {}