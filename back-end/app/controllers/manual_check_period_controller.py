# app/controllers/manual_check_period_controller.py
from datetime import datetime
from flask import Blueprint, request, jsonify
from app.services.manual_check_period_service import ManualCheckPeriodService
from app.utils.decorators import admin_required, validate_json, handle_exceptions
from app.utils.constants import HTTP_STATUS

manual_check_period_bp = Blueprint("manual_check_period", __name__)
manual_check_period_service = ManualCheckPeriodService()


@manual_check_period_bp.route("/periods/status", methods=["GET"])
@admin_required
@handle_exceptions
def get_period_status():
    """점검 기간 현황 조회"""
    year = request.args.get("year", datetime.now().year, type=int)

    try:
        result = manual_check_period_service.get_period_status(year)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return (
            jsonify({"success": False, "error": str(e)}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@manual_check_period_bp.route("/periods", methods=["GET"])
@admin_required
@handle_exceptions
def get_periods():
    """특정 연도의 모든 점검 기간 조회"""
    year = request.args.get("year", datetime.now().year, type=int)
    check_type = request.args.get("check_type")

    try:
        result = manual_check_period_service.get_period_status(year)

        # 특정 점검 유형만 필터링
        if check_type and check_type in result["check_types"]:
            filtered_result = {
                "year": result["year"],
                "check_types": {check_type: result["check_types"][check_type]},
            }
            return jsonify({"success": True, "data": filtered_result})

        return jsonify({"success": True, "data": result})
    except Exception as e:
        return (
            jsonify({"success": False, "error": str(e)}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@manual_check_period_bp.route("/periods", methods=["POST"])
@admin_required
@validate_json(["check_type", "period_year", "period_name", "start_date", "end_date"])
@handle_exceptions
def create_period():
    """기간 생성 - 날짜 겹침 검사 포함"""
    data = request.json
    user = request.current_user

    try:
        # 점검 유형 검증
        valid_check_types = manual_check_period_service.get_check_types().keys()
        if data["check_type"] not in valid_check_types:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"지원되지 않는 점검 유형입니다.",
                        "valid_types": list(valid_check_types),
                    }
                ),
                HTTP_STATUS["BAD_REQUEST"],
            )

        # 생성자 정보 추가
        data["created_by"] = user["username"]

        # 기간 생성 (내부에서 겹침 검사 포함)
        result = manual_check_period_service.create_period(data)

        if result["success"]:
            return jsonify(result), HTTP_STATUS["CREATED"]
        else:
            response_data = {"success": False, "error": result["message"]}

            # 겹치는 기간 정보가 있으면 포함
            if "overlapping_periods" in result:
                response_data["overlapping_periods"] = result["overlapping_periods"]

            return jsonify(response_data), HTTP_STATUS["BAD_REQUEST"]

    except Exception as e:
        return (
            jsonify(
                {
                    "success": False,
                    "error": f"기간 생성 중 오류가 발생했습니다: {str(e)}",
                }
            ),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@manual_check_period_bp.route("/periods/<int:period_id>", methods=["PUT"])
@admin_required
@validate_json(["start_date", "end_date"])
@handle_exceptions
def update_period(period_id):
    """기간 수정 - 날짜 겹침 검사 포함"""
    data = request.json

    try:
        # 기간 수정 (내부에서 겹침 검사 포함)
        result = manual_check_period_service.update_period(period_id, data)

        if result["success"]:
            return jsonify(result)
        else:
            response_data = {"success": False, "error": result["message"]}

            # 겹치는 기간 정보가 있으면 포함
            if "overlapping_periods" in result:
                response_data["overlapping_periods"] = result["overlapping_periods"]

            return jsonify(response_data), HTTP_STATUS["BAD_REQUEST"]

    except Exception as e:
        return (
            jsonify(
                {
                    "success": False,
                    "error": f"기간 수정 중 오류가 발생했습니다: {str(e)}",
                }
            ),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@manual_check_period_bp.route("/periods/<int:period_id>", methods=["DELETE"])
@admin_required
@handle_exceptions
def delete_period(period_id):
    """점검 기간 삭제"""
    try:
        result = manual_check_period_service.delete_period(period_id)

        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), HTTP_STATUS["BAD_REQUEST"]

    except Exception as e:
        return (
            jsonify(
                {
                    "success": False,
                    "error": f"기간 삭제 중 오류가 발생했습니다: {str(e)}",
                }
            ),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@manual_check_period_bp.route("/periods/<int:period_id>/complete", methods=["POST"])
@admin_required
@handle_exceptions
def complete_period(period_id):
    """점검 기간 완료 처리"""
    current_user = request.current_user

    try:
        result = manual_check_period_service.complete_period(
            period_id, current_user["username"]
        )

        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), HTTP_STATUS["BAD_REQUEST"]

    except Exception as e:
        return (
            jsonify(
                {
                    "success": False,
                    "error": f"완료 처리 중 오류가 발생했습니다: {str(e)}",
                }
            ),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@manual_check_period_bp.route("/periods/<int:period_id>/reopen", methods=["POST"])
@admin_required
@handle_exceptions
def reopen_period(period_id):
    """점검 기간 재개"""
    try:
        result = manual_check_period_service.reopen_period(period_id)

        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), HTTP_STATUS["BAD_REQUEST"]

    except Exception as e:
        return (
            jsonify(
                {
                    "success": False,
                    "error": f"재개 처리 중 오류가 발생했습니다: {str(e)}",
                }
            ),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@manual_check_period_bp.route("/check-types", methods=["GET"])
@admin_required
@handle_exceptions
def get_check_types():
    """지원되는 점검 유형 목록 조회"""
    try:
        check_types = manual_check_period_service.get_check_types()

        return jsonify(
            {
                "success": True,
                "data": [
                    {"code": code, "name": name} for code, name in check_types.items()
                ],
            }
        )
    except Exception as e:
        return (
            jsonify({"success": False, "error": str(e)}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@manual_check_period_bp.route("/periods/<int:period_id>/details", methods=["GET"])
@admin_required
@handle_exceptions
def get_period_details(period_id):
    """특정 기간의 상세 정보 조회"""
    try:
        from app.utils.database import execute_query

        # 기간 기본 정보
        period_info = execute_query(
            """
            SELECT 
                mcp.*,
                CASE 
                    WHEN CURDATE() BETWEEN start_date AND end_date THEN 'active'
                    WHEN CURDATE() < start_date THEN 'upcoming'
                    WHEN CURDATE() > end_date THEN 'ended'
                    ELSE 'unknown'
                END as status
            FROM manual_check_periods mcp
            WHERE period_id = %s AND is_active = 1
            """,
            (period_id,),
            fetch_one=True,
        )

        if not period_info:
            return (
                jsonify({"success": False, "error": "해당 기간을 찾을 수 없습니다."}),
                HTTP_STATUS["NOT_FOUND"],
            )

        # 점검 결과 통계
        stats = execute_query(
            """
            SELECT 
                COUNT(DISTINCT user_id) as total_users,
                COALESCE(SUM(CASE WHEN overall_result = 'pass' THEN 1 ELSE 0 END), 0) as pass_count,
                COALESCE(SUM(CASE WHEN overall_result = 'fail' THEN 1 ELSE 0 END), 0) as fail_count,
                COALESCE(SUM(CASE WHEN overall_result = 'partial' THEN 1 ELSE 0 END), 0) as partial_count,
                COALESCE(AVG(total_score), 0) as avg_score
            FROM manual_check_results
            WHERE period_id = %s
            """,
            (period_id,),
            fetch_one=True,
        )

        # 부서별 통계
        dept_stats = execute_query(
            """
            SELECT 
                u.department,
                COUNT(*) as dept_total,
                COALESCE(SUM(CASE WHEN mcr.overall_result = 'pass' THEN 1 ELSE 0 END), 0) as dept_pass,
                COALESCE(AVG(mcr.total_score), 0) as dept_avg_score
            FROM manual_check_results mcr
            JOIN users u ON mcr.user_id = u.uid
            WHERE mcr.period_id = %s
            GROUP BY u.department
            ORDER BY dept_avg_score DESC
            """,
            (period_id,),
            fetch_all=True,
        )

        # 날짜 포맷팅
        if period_info["start_date"]:
            period_info["start_date"] = period_info["start_date"].strftime("%Y-%m-%d")
        if period_info["end_date"]:
            period_info["end_date"] = period_info["end_date"].strftime("%Y-%m-%d")
        if period_info["completed_at"]:
            period_info["completed_at"] = period_info["completed_at"].strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        if period_info["created_at"]:
            period_info["created_at"] = period_info["created_at"].strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        if period_info["updated_at"]:
            period_info["updated_at"] = period_info["updated_at"].strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        return jsonify(
            {
                "success": True,
                "data": {
                    "period_info": period_info,
                    "stats": stats,
                    "department_stats": dept_stats,
                },
            }
        )

    except Exception as e:
        return (
            jsonify(
                {
                    "success": False,
                    "error": f"기간 상세 정보 조회 중 오류가 발생했습니다: {str(e)}",
                }
            ),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@manual_check_period_bp.route("/periods/validate", methods=["POST"])
@admin_required
@validate_json(["check_type", "period_year", "start_date", "end_date"])
@handle_exceptions
def validate_period_data():
    """기간 데이터 유효성 검사 (실제 생성 전 검증용) - 날짜 겹침 검사 추가"""
    data = request.json

    try:
        # 기본 유효성 검사
        valid_check_types = manual_check_period_service.get_check_types().keys()
        if data["check_type"] not in valid_check_types:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"지원되지 않는 점검 유형입니다.",
                        "valid_types": list(valid_check_types),
                    }
                ),
                HTTP_STATUS["BAD_REQUEST"],
            )

        # 날짜 및 겹침 검증 (새로운 검증 함수 사용)
        validation_result = manual_check_period_service.validate_period_dates(
            data["check_type"],
            data["start_date"],
            data["end_date"],
            exclude_period_id=data.get("period_id"),  # 수정 시 현재 기간 제외
        )

        if not validation_result["valid"]:
            response_data = {"success": False, "error": validation_result["message"]}

            # 겹치는 기간 정보가 있으면 포함
            if "overlapping_periods" in validation_result:
                response_data["overlapping_periods"] = validation_result[
                    "overlapping_periods"
                ]

            return jsonify(response_data), HTTP_STATUS["BAD_REQUEST"]

        # 중복 검사 (period_name이 있는 경우 - 기존 로직 유지)
        if data.get("period_name"):
            from app.utils.database import execute_query

            existing = execute_query(
                """
                SELECT period_id FROM manual_check_periods
                WHERE check_type = %s AND period_year = %s AND period_name = %s AND is_active = 1
                """,
                (data["check_type"], data["period_year"], data["period_name"]),
                fetch_one=True,
            )

            if existing:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": f"{data['period_year']}년 {data['period_name']} 기간이 이미 존재합니다.",
                        }
                    ),
                    HTTP_STATUS["BAD_REQUEST"],
                )

        return jsonify({"success": True, "message": "유효한 기간 데이터입니다."})

    except Exception as e:
        return (
            jsonify(
                {
                    "success": False,
                    "error": f"유효성 검사 중 오류가 발생했습니다: {str(e)}",
                }
            ),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


# 새로운 엔드포인트: 기간 겹침 검사 전용
@manual_check_period_bp.route("/periods/check-overlap", methods=["POST"])
@admin_required
@validate_json(["check_type", "start_date", "end_date"])
@handle_exceptions
def check_period_overlap():
    """기간 겹침 검사 전용 엔드포인트"""
    data = request.json

    try:
        overlap_result = manual_check_period_service.check_period_overlap(
            data["check_type"],
            data["start_date"],
            data["end_date"],
            exclude_period_id=data.get("exclude_period_id"),
        )

        return jsonify(
            {
                "success": True,
                "has_overlap": overlap_result["has_overlap"],
                "message": overlap_result["message"],
                "overlapping_periods": overlap_result["overlapping_periods"],
            }
        )

    except Exception as e:
        return (
            jsonify(
                {
                    "success": False,
                    "error": f"겹침 검사 중 오류가 발생했습니다: {str(e)}",
                }
            ),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )
