# app/controllers/phishing_training_controller.py
from datetime import datetime
from flask import Blueprint, request, jsonify, make_response
from app.services.phishing_training_service import PhishingTrainingService
from app.services.phishing_training_period_service import PhishingTrainingPeriodService
from app.utils.decorators import (
    admin_required,
    handle_exceptions,
    validate_json,
    token_required,
)
from app.utils.constants import HTTP_STATUS
import logging

logger = logging.getLogger(__name__)

training_bp = Blueprint("phishing_training", __name__)
training_service = PhishingTrainingService()
period_service = PhishingTrainingPeriodService()

# ===== 사용자용 API =====


@training_bp.route("/status", methods=["GET"])
@token_required
@handle_exceptions
def get_training_status():
    """사용자별 모의훈련 현황 조회"""
    username = request.current_user["username"]
    year = request.args.get("year", default=datetime.now().year, type=int)

    try:
        status = training_service.get_user_training_status(username, year)
        return jsonify(status), HTTP_STATUS["OK"]
    except Exception as e:
        logging.error(
            f"모의훈련 현황 조회 실패 (username: {username}, year: {year}): {str(e)}"
        )
        return (
            jsonify({"error": "모의훈련 현황을 조회할 수 없습니다."}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


# ===== 관리자용 API =====


@training_bp.route("/periods/status", methods=["GET"])
@admin_required
@handle_exceptions
def get_periods_status():
    """훈련 기간 현황 조회"""
    try:
        year = request.args.get("year", datetime.now().year, type=int)
        result = period_service.get_period_status(year)
        return jsonify(result)

    except Exception as e:
        logger.error(f"훈련 기간 현황 조회 오류: {str(e)}")
        return (
            jsonify({"error": f"기간 현황 조회 실패: {str(e)}"}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@training_bp.route("/periods", methods=["GET"])
@admin_required
@handle_exceptions
def get_periods():
    """훈련 기간 목록 조회"""
    try:
        year = request.args.get("year", datetime.now().year, type=int)
        result = period_service.get_period_status(year)
        return jsonify(result)

    except Exception as e:
        logger.error(f"훈련 기간 목록 조회 오류: {str(e)}")
        return (
            jsonify({"error": f"기간 조회 실패: {str(e)}"}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@training_bp.route("/periods", methods=["POST"])
@admin_required
@handle_exceptions
@validate_json(
    ["training_year", "period_name", "training_type", "start_date", "end_date"]
)
def create_period():
    """새 훈련 기간 생성"""
    try:
        data = request.json
        created_by = request.current_user.get("user_id", "admin")

        result = period_service.create_period(data, created_by)

        if result["success"]:
            return jsonify(result), HTTP_STATUS["CREATED"]
        else:
            return jsonify(result), HTTP_STATUS["BAD_REQUEST"]

    except Exception as e:
        logger.error(f"훈련 기간 생성 오류: {str(e)}")
        return (
            jsonify({"error": f"기간 생성 실패: {str(e)}"}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@training_bp.route("/periods/<int:period_id>", methods=["PUT"])
@admin_required
@handle_exceptions
@validate_json(
    ["training_year", "period_name", "training_type", "start_date", "end_date"]
)
def update_period(period_id):
    """훈련 기간 수정"""
    try:
        data = request.json
        updated_by = request.current_user.get("user_id", "admin")

        result = period_service.update_period(period_id, data, updated_by)

        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), HTTP_STATUS["BAD_REQUEST"]

    except Exception as e:
        logger.error(f"훈련 기간 수정 오류: {str(e)}")
        return (
            jsonify({"error": f"기간 수정 실패: {str(e)}"}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@training_bp.route("/periods/<int:period_id>/complete", methods=["POST"])
@admin_required
@handle_exceptions
def complete_period(period_id):
    """훈련 기간 완료 처리"""
    try:
        completed_by = request.current_user.get("user_id", "admin")
        result = period_service.complete_period(period_id, completed_by)

        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), HTTP_STATUS["BAD_REQUEST"]

    except Exception as e:
        logger.error(f"훈련 기간 완료 처리 오류: {str(e)}")
        return (
            jsonify({"error": f"완료 처리 실패: {str(e)}"}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@training_bp.route("/periods/<int:period_id>/reopen", methods=["POST"])
@admin_required
@handle_exceptions
def reopen_period(period_id):
    """훈련 기간 재개"""
    try:
        result = period_service.reopen_period(period_id)

        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), HTTP_STATUS["BAD_REQUEST"]

    except Exception as e:
        logger.error(f"훈련 기간 재개 오류: {str(e)}")
        return (
            jsonify({"error": f"재개 처리 실패: {str(e)}"}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@training_bp.route("/periods/<int:period_id>", methods=["DELETE"])
@admin_required
@handle_exceptions
def delete_period(period_id):
    """훈련 기간 삭제"""
    try:
        result = period_service.delete_training_period(period_id)

        if result["success"]:
            return jsonify({"message": result["message"]})
        else:
            status_code = HTTP_STATUS["BAD_REQUEST"]
            response_data = {"error": result["error"]}

            if result.get("requires_confirmation"):
                response_data["requires_confirmation"] = True
                response_data["training_count"] = result.get("training_count", 0)

            return jsonify(response_data), status_code

    except Exception as e:
        logger.error(f"훈련 기간 삭제 오류: {str(e)}")
        return (
            jsonify({"error": f"기간 삭제 실패: {str(e)}"}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@training_bp.route("/periods/<int:period_id>/force-delete", methods=["DELETE"])
@admin_required
@handle_exceptions
def force_delete_period(period_id):
    """훈련 기간 강제 삭제 (훈련 기록 포함)"""
    try:
        result = period_service.force_delete_training_period(period_id)

        if result["success"]:
            return jsonify({"message": result["message"]})
        else:
            return jsonify({"error": result["error"]}), HTTP_STATUS["BAD_REQUEST"]

    except Exception as e:
        logger.error(f"훈련 기간 강제 삭제 오류: {str(e)}")
        return (
            jsonify({"error": f"강제 삭제 실패: {str(e)}"}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@training_bp.route("/records", methods=["GET"])
@admin_required
@handle_exceptions
def get_training_records():
    """훈련 기록 조회"""
    try:
        year = request.args.get("year", datetime.now().year, type=int)
        period_id = request.args.get("period_id", type=int)
        training_type = request.args.get("training_type")
        result_filter = request.args.get("result")
        search_query = request.args.get("search", "")
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)

        result = training_service.get_training_records(
            year=year,
            period_id=period_id,
            training_type=training_type,
            result_filter=result_filter,
            search_query=search_query,
            page=page,
            per_page=per_page,
        )

        return jsonify(result)

    except Exception as e:
        logger.error(f"훈련 기록 조회 오류: {str(e)}")
        return (
            jsonify({"error": f"기록 조회 실패: {str(e)}"}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@training_bp.route("/records/<int:record_id>", methods=["PUT"])
@admin_required
@handle_exceptions
def update_training_record(record_id):
    """훈련 기록 수정"""
    try:
        data = request.json
        result = training_service.update_training_record(record_id, data)

        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), HTTP_STATUS["BAD_REQUEST"]

    except Exception as e:
        logger.error(f"훈련 기록 수정 오류: {str(e)}")
        return (
            jsonify({"error": f"기록 수정 실패: {str(e)}"}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@training_bp.route("/records/<int:record_id>/exclude", methods=["POST"])
@admin_required
@handle_exceptions
def toggle_record_exclude(record_id):
    """훈련 기록 제외/포함 토글"""
    try:
        data = request.json
        exclude = data.get("exclude", True)
        reason = data.get("reason", "")

        result = training_service.toggle_record_exclude(record_id, exclude, reason)

        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), HTTP_STATUS["BAD_REQUEST"]

    except Exception as e:
        logger.error(f"훈련 기록 제외/포함 처리 오류: {str(e)}")
        return (
            jsonify({"error": f"처리 실패: {str(e)}"}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@training_bp.route("/records/<int:record_id>", methods=["DELETE"])
@admin_required
@handle_exceptions
def delete_training_record(record_id):
    """훈련 기록 삭제"""
    try:
        result = training_service.delete_training_record(record_id)

        if result["success"]:
            return jsonify({"message": result["message"]})
        else:
            return jsonify({"error": result["message"]}), HTTP_STATUS["BAD_REQUEST"]

    except Exception as e:
        logger.error(f"훈련 기록 삭제 오류: {str(e)}")
        return (
            jsonify({"error": f"기록 삭제 실패: {str(e)}"}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@training_bp.route("/bulk-upload", methods=["POST"])
@admin_required
@handle_exceptions
def bulk_upload():
    """훈련 결과 일괄 업로드"""
    try:
        if "file" not in request.files:
            return (
                jsonify({"error": "파일이 업로드되지 않았습니다."}),
                HTTP_STATUS["BAD_REQUEST"],
            )

        file = request.files["file"]
        period_id = request.form.get("period_id", type=int)

        if not period_id:
            return (
                jsonify({"error": "훈련 기간을 선택해주세요."}),
                HTTP_STATUS["BAD_REQUEST"],
            )

        if file.filename == "":
            return (
                jsonify({"error": "파일이 선택되지 않았습니다."}),
                HTTP_STATUS["BAD_REQUEST"],
            )

        result = training_service.process_excel_upload(file, period_id)

        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), HTTP_STATUS["BAD_REQUEST"]

    except Exception as e:
        logger.error(f"일괄 업로드 오류: {str(e)}")
        return (
            jsonify({"error": f"업로드 실패: {str(e)}"}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@training_bp.route("/export", methods=["GET"])
@admin_required
@handle_exceptions
def export_training_data():
    """훈련 데이터 내보내기"""
    try:
        year = request.args.get("year", datetime.now().year, type=int)
        format_type = request.args.get("format", "csv")

        result = training_service.export_training_data(year, format_type)

        if result["success"]:
            response = make_response(result["data"])
            response.headers["Content-Type"] = result["content_type"]
            response.headers["Content-Disposition"] = result["filename"]
            return response
        else:
            return jsonify({"error": result["error"]}), HTTP_STATUS["BAD_REQUEST"]

    except Exception as e:
        logger.error(f"데이터 내보내기 오류: {str(e)}")
        return (
            jsonify({"error": f"내보내기 실패: {str(e)}"}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@training_bp.route("/statistics", methods=["GET"])
@admin_required
@handle_exceptions
def get_training_statistics():
    """훈련 통계 조회"""
    try:
        year = request.args.get("year", datetime.now().year, type=int)
        period_id = request.args.get("period_id", type=int)

        result = training_service.get_training_statistics(year, period_id)
        return jsonify(result)

    except Exception as e:
        logger.error(f"훈련 통계 조회 오류: {str(e)}")
        return (
            jsonify({"error": f"통계 조회 실패: {str(e)}"}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


# ===== 에러 핸들러 =====


@training_bp.errorhandler(404)
def not_found(error):
    return (
        jsonify({"error": "요청한 리소스를 찾을 수 없습니다."}),
        HTTP_STATUS["NOT_FOUND"],
    )


@training_bp.errorhandler(405)
def method_not_allowed(error):
    return (
        jsonify({"error": "허용되지 않은 HTTP 메서드입니다."}),
        HTTP_STATUS["METHOD_NOT_ALLOWED"],
    )
