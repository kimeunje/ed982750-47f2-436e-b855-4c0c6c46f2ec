# app/controllers/training_period_controller.py - 수정된 버전
from datetime import datetime
from flask import Blueprint, request, jsonify
from app.services.training_period_service import TrainingPeriodService
from app.utils.decorators import admin_required, validate_json, handle_exceptions
from app.utils.constants import HTTP_STATUS

# 블루프린트 이름을 기존과 겹치지 않게 수정
training_period_bp = Blueprint("training_period", __name__)
training_period_service = TrainingPeriodService()


@training_period_bp.route("/periods/status", methods=["GET"])
@admin_required
@handle_exceptions
def get_period_status():
    """현재 기간 상태 요약"""
    year = request.args.get("year", datetime.now().year, type=int)
    status = training_period_service.get_current_period_status(year)
    return jsonify(status)


@training_period_bp.route("/periods", methods=["GET"])
@admin_required
@handle_exceptions
def get_training_periods():
    """훈련 기간 목록 조회"""
    year = request.args.get("year", datetime.now().year, type=int)
    periods = training_period_service.get_training_periods(year)
    return jsonify(periods)


@training_period_bp.route("/periods", methods=["POST"])
@admin_required
@handle_exceptions
def create_training_period():
    """훈련 기간 생성"""
    data = request.get_json()
    
    # 필수 필드 검증
    required_fields = ["training_year", "training_period", "start_date", "end_date"]
    for field in required_fields:
        if not data or field not in data or not data[field]:
            return jsonify({"error": f"{field}는 필수 항목입니다."}), HTTP_STATUS["BAD_REQUEST"]
    
    user = request.current_user
    
    # 중복 체크
    if training_period_service.check_period_exists(
        data["training_year"], data["training_period"]
    ):
        return jsonify({"error": "해당 연도/기간이 이미 존재합니다."}), HTTP_STATUS["BAD_REQUEST"]

    try:
        success = training_period_service.create_training_period(data, user["username"])
        if success:
            return jsonify({"message": "훈련 기간이 생성되었습니다."}), HTTP_STATUS["CREATED"]
        else:
            return jsonify({"error": "생성에 실패했습니다."}), HTTP_STATUS["BAD_REQUEST"]
    except ValueError as e:
        return jsonify({"error": str(e)}), HTTP_STATUS["BAD_REQUEST"]


@training_period_bp.route("/periods/<int:period_id>", methods=["PUT"])
@admin_required
@handle_exceptions
def update_training_period(period_id):
    """훈련 기간 수정"""
    data = request.get_json()
    
    # 필수 필드 검증
    required_fields = ["start_date", "end_date"]
    for field in required_fields:
        if not data or field not in data or not data[field]:
            return jsonify({"error": f"{field}는 필수 항목입니다."}), HTTP_STATUS["BAD_REQUEST"]
    
    try:
        success = training_period_service.update_training_period(period_id, data)
        if success:
            return jsonify({"message": "훈련 기간이 수정되었습니다."})
        else:
            return jsonify({"error": "수정에 실패했습니다."}), HTTP_STATUS["BAD_REQUEST"]
    except ValueError as e:
        return jsonify({"error": str(e)}), HTTP_STATUS["BAD_REQUEST"]


@training_period_bp.route("/periods/<int:period_id>", methods=["DELETE"])
@admin_required
@handle_exceptions
def delete_training_period(period_id):
    """훈련 기간 삭제"""
    try:
        success = training_period_service.delete_training_period(period_id)
        if success:
            return jsonify({"message": "훈련 기간이 삭제되었습니다."})
        else:
            return jsonify({"error": "삭제에 실패했습니다."}), HTTP_STATUS["BAD_REQUEST"]
    except ValueError as e:
        return jsonify({"error": str(e)}), HTTP_STATUS["BAD_REQUEST"]


@training_period_bp.route("/periods/<int:period_id>/complete", methods=["POST"])
@admin_required
@handle_exceptions
def complete_training_period(period_id):
    """훈련 기간 완료 처리"""
    user = request.current_user
    
    try:
        success = training_period_service.complete_training_period(period_id, user["username"])
        if success:
            return jsonify({"message": "훈련 기간이 완료 처리되었습니다. 미실시 사용자들이 성공으로 처리되었습니다."})
        else:
            return jsonify({"error": "완료 처리에 실패했습니다."}), HTTP_STATUS["BAD_REQUEST"]
    except ValueError as e:
        return jsonify({"error": str(e)}), HTTP_STATUS["BAD_REQUEST"]


@training_period_bp.route("/periods/<int:period_id>/reopen", methods=["POST"])
@admin_required
@handle_exceptions
def reopen_training_period(period_id):
    """훈련 기간 재개 (완료 상태 취소)"""
    try:
        success = training_period_service.reopen_training_period(period_id)
        if success:
            return jsonify({"message": "훈련 기간이 재개되었습니다."})
        else:
            return jsonify({"error": "재개 처리에 실패했습니다."}), HTTP_STATUS["BAD_REQUEST"]
    except ValueError as e:
        return jsonify({"error": str(e)}), HTTP_STATUS["BAD_REQUEST"]


# 디버깅용 엔드포인트 (개발 중에만 사용)
@training_period_bp.route("/debug/routes", methods=["GET"])
@admin_required
def debug_routes():
    """등록된 라우트 확인용 (개발용)"""
    from flask import current_app
    routes = []
    for rule in current_app.url_map.iter_rules():
        if 'period' in rule.rule:
            routes.append({
                'url': rule.rule,
                'methods': list(rule.methods - {'HEAD', 'OPTIONS'}),
                'endpoint': rule.endpoint
            })
    return jsonify(routes)