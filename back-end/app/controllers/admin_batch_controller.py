# app/controllers/admin_batch_controller.py
"""
관리자용 배치 작업 컨트롤러
- 전체 사용자 점수 일괄 계산
- 배치 작업 상태 조회
- 작업 로그 관리
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import threading
import time
import logging
from app.utils.decorators import token_required, handle_exceptions, admin_required
from app.utils.constants import HTTP_STATUS
from app.utils.database import execute_query
from app.services.total_score_service import ScoreService

# 블루프린트 생성
admin_batch_bp = Blueprint("admin_batch", __name__, url_prefix="/api/admin/batch")

# 배치 작업 상태 관리
batch_status = {
    "is_running": False,
    "current_task": None,
    "progress": 0,
    "total": 0,
    "start_time": None,
    "end_time": None,
    "success_count": 0,
    "error_count": 0,
    "errors": []
}

score_service = ScoreService()


@admin_batch_bp.route("/calculate-all-scores", methods=["POST"])
@token_required
@admin_required
@handle_exceptions
def calculate_all_user_scores():
    """전체 사용자 점수 일괄 계산"""
    global batch_status

    # 이미 실행 중인지 확인
    if batch_status["is_running"]:
        return jsonify({
            "error": "이미 배치 작업이 실행 중입니다.",
            "current_progress": batch_status["progress"],
            "total": batch_status["total"]
        }), HTTP_STATUS["CONFLICT"]

    # 요청 데이터 파싱
    data = request.json or {}
    year = data.get("year", datetime.now().year)
    force_recalculate = data.get("force_recalculate", False)  # 기존 데이터도 다시 계산할지 여부

    try:
        # 계산할 사용자 목록 조회
        if force_recalculate:
            # 모든 사용자
            users_query = "SELECT uid, user_id, username FROM users ORDER BY uid"
        else:
            # 해당 연도에 점수 데이터가 없는 사용자만
            users_query = """
                SELECT u.uid, u.user_id, u.username 
                FROM users u
                LEFT JOIN security_score_summary sss ON u.uid = sss.user_id AND sss.evaluation_year = %s
                WHERE sss.summary_id IS NULL
                ORDER BY u.uid
            """

        if force_recalculate:
            users = execute_query(users_query, fetch_all=True)
        else:
            users = execute_query(users_query, (year, ), fetch_all=True)

        if not users:
            return jsonify({
                "message": "계산할 사용자가 없습니다.",
                "year": year,
                "total_users": 0
            })

        # 배치 작업을 별도 스레드에서 실행
        thread = threading.Thread(target=_execute_batch_calculation,
                                  args=(users, year, force_recalculate), daemon=True)
        thread.start()

        return jsonify({
            "message": "전체 사용자 점수 계산을 시작했습니다.",
            "year": year,
            "total_users": len(users),
            "force_recalculate": force_recalculate,
            "estimated_time": f"{len(users) * 0.5:.1f}초"
        })

    except Exception as e:
        logging.error(f"Batch calculation start error: {str(e)}")
        return jsonify({
            "error": "배치 작업 시작 중 오류가 발생했습니다.",
            "details": str(e)
        }), HTTP_STATUS["INTERNAL_SERVER_ERROR"]


@admin_batch_bp.route("/status", methods=["GET"])
@token_required
@admin_required
@handle_exceptions
def get_batch_status():
    """배치 작업 상태 조회"""
    global batch_status

    # 진행률 계산
    progress_percentage = 0
    if batch_status["total"] > 0:
        progress_percentage = round(
            (batch_status["progress"] / batch_status["total"]) * 100, 1)

    # 예상 완료 시간 계산
    estimated_completion = None
    if batch_status["is_running"] and batch_status["start_time"] and batch_status[
            "progress"] > 0:
        elapsed_time = (datetime.now() - batch_status["start_time"]).total_seconds()
        time_per_user = elapsed_time / batch_status["progress"]
        remaining_users = batch_status["total"] - batch_status["progress"]
        remaining_seconds = remaining_users * time_per_user
        estimated_completion = (
            datetime.now() + datetime.timedelta(seconds=remaining_seconds)).isoformat()

    response_data = {
        "is_running": batch_status["is_running"],
        "current_task": batch_status["current_task"],
        "progress": batch_status["progress"],
        "total": batch_status["total"],
        "progress_percentage": progress_percentage,
        "start_time": batch_status["start_time"].isoformat()
        if batch_status["start_time"] else None,
        "end_time": batch_status["end_time"].isoformat()
        if batch_status["end_time"] else None,
        "estimated_completion": estimated_completion,
        "success_count": batch_status["success_count"],
        "error_count": batch_status["error_count"],
        "recent_errors": batch_status["errors"][-5:]
        if batch_status["errors"] else []  # 최근 5개 에러만
    }

    return jsonify(response_data)


@admin_batch_bp.route("/cancel", methods=["POST"])
@token_required
@admin_required
@handle_exceptions
def cancel_batch_operation():
    """배치 작업 취소 (진행 중인 작업은 완료하고 다음 작업을 중단)"""
    global batch_status

    if not batch_status["is_running"]:
        return jsonify({"message": "실행 중인 배치 작업이 없습니다."}), HTTP_STATUS["BAD_REQUEST"]

    # 취소 플래그 설정 (실제 구현에서는 더 정교한 취소 메커니즘 필요)
    batch_status["current_task"] = "취소 요청됨"

    return jsonify({"message": "배치 작업 취소가 요청되었습니다. 현재 진행 중인 작업 완료 후 중단됩니다."})


def _execute_batch_calculation(users, year, force_recalculate):
    """배치 계산 실행 (별도 스레드에서 실행)"""
    global batch_status

    # 배치 상태 초기화
    batch_status.update({
        "is_running": True,
        "current_task": "초기화 중...",
        "progress": 0,
        "total": len(users),
        "start_time": datetime.now(),
        "end_time": None,
        "success_count": 0,
        "error_count": 0,
        "errors": []
    })

    logging.info(f"배치 점수 계산 시작: {len(users)}명, 연도={year}, 강제재계산={force_recalculate}")

    try:
        for i, user in enumerate(users):
            # 취소 요청 확인
            if batch_status["current_task"] == "취소 요청됨":
                logging.info(f"배치 작업 취소됨: {i}/{len(users)} 완료")
                break

            try:
                # 현재 작업 업데이트
                batch_status[
                    "current_task"] = f"{user['username']} ({user['user_id']}) 점수 계산 중..."
                batch_status["progress"] = i

                # 개별 사용자 점수 계산
                score_data = score_service.calculate_security_score(user["uid"], year)

                batch_status["success_count"] += 1
                logging.debug(
                    f"사용자 {user['user_id']} 점수 계산 완료: 총감점={score_data['total_penalty']}"
                )

                # 너무 빠르게 진행되지 않도록 약간의 딜레이
                time.sleep(0.1)

            except Exception as user_error:
                error_msg = f"사용자 {user['user_id']} ({user['username']}) 계산 실패: {str(user_error)}"
                logging.error(error_msg)

                batch_status["error_count"] += 1
                batch_status["errors"].append({
                    "user_id": user["user_id"],
                    "username": user["username"],
                    "error": str(user_error),
                    "timestamp": datetime.now().isoformat()
                })

                # 에러가 너무 많이 쌓이지 않도록 제한
                if len(batch_status["errors"]) > 50:
                    batch_status["errors"] = batch_status["errors"][-40:]

        # 최종 진행률 업데이트
        batch_status["progress"] = len(users)

    except Exception as e:
        logging.error(f"배치 계산 중 심각한 오류: {str(e)}")
        batch_status["errors"].append({
            "user_id": "SYSTEM",
            "username": "시스템",
            "error": f"배치 작업 중단: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })

    finally:
        # 배치 작업 완료
        batch_status.update({
            "is_running": False,
            "current_task": "완료",
            "end_time": datetime.now()
        })

        duration = (batch_status["end_time"] -
                    batch_status["start_time"]).total_seconds()
        logging.info(f"배치 점수 계산 완료: "
                     f"성공={batch_status['success_count']}, "
                     f"실패={batch_status['error_count']}, "
                     f"소요시간={duration:.1f}초")


@admin_batch_bp.route("/calculate-single", methods=["POST"])
@token_required
@admin_required
@handle_exceptions
def calculate_single_user_score():
    """특정 사용자 점수 재계산"""
    data = request.json or {}
    user_id = data.get("user_id")
    year = data.get("year", datetime.now().year)

    if not user_id:
        return jsonify({"error": "user_id가 필요합니다."}), HTTP_STATUS["BAD_REQUEST"]

    try:
        # 사용자 존재 확인
        user = execute_query("SELECT uid, user_id, username FROM users WHERE uid = %s",
                             (user_id, ), fetch_one=True)

        if not user:
            return jsonify({"error": "사용자를 찾을 수 없습니다."}), HTTP_STATUS["NOT_FOUND"]

        # 점수 계산
        score_data = score_service.calculate_security_score(user["uid"], year)

        return jsonify({
            "message": f"사용자 {user['username']}의 {year}년 점수가 재계산되었습니다.",
            "user_info": {
                "user_id": user["user_id"],
                "username": user["username"]
            },
            "year": year,
            "score_data": {
                "total_penalty": float(score_data["total_penalty"]),
                "audit_penalty": float(score_data["audit_penalty"]),
                "education_penalty": float(score_data["education_penalty"]),
                "training_penalty": float(score_data["training_penalty"])
            }
        })

    except Exception as e:
        logging.error(f"Single user calculation error: {str(e)}")
        return jsonify({
            "error": "사용자 점수 계산 중 오류가 발생했습니다.",
            "details": str(e)
        }), HTTP_STATUS["INTERNAL_SERVER_ERROR"]


@admin_batch_bp.route("/statistics", methods=["GET"])
@token_required
@admin_required
@handle_exceptions
def get_calculation_statistics():
    """점수 계산 통계 조회"""
    year = request.args.get("year", datetime.now().year, type=int)

    try:
        # 전체 사용자 수
        total_users = execute_query("SELECT COUNT(*) as count FROM users",
                                    fetch_one=True)["count"]

        # 계산된 사용자 수
        calculated_users = execute_query(
            "SELECT COUNT(*) as count FROM security_score_summary WHERE evaluation_year = %s",
            (year, ), fetch_one=True)["count"]

        # 점수 분포
        score_distribution = execute_query(
            """
            SELECT 
                CASE 
                    WHEN total_penalty = 0 THEN 'perfect'
                    WHEN total_penalty <= 0.5 THEN 'excellent'
                    WHEN total_penalty <= 1.0 THEN 'good'
                    WHEN total_penalty <= 2.0 THEN 'warning'
                    WHEN total_penalty <= 3.0 THEN 'danger'
                    ELSE 'critical'
                END as score_range,
                COUNT(*) as count
            FROM security_score_summary 
            WHERE evaluation_year = %s
            GROUP BY score_range
            """, (year, ), fetch_all=True)

        # 최근 계산 시간
        last_calculation = execute_query(
            """
            SELECT MAX(last_calculated) as last_time 
            FROM security_score_summary 
            WHERE evaluation_year = %s
            """, (year, ), fetch_one=True)

        return jsonify({
            "year": year,
            "total_users": total_users,
            "calculated_users": calculated_users,
            "uncalculated_users": total_users - calculated_users,
            "calculation_percentage": round(
                (calculated_users / total_users) * 100, 1) if total_users > 0 else 0,
            "score_distribution": score_distribution,
            "last_calculation_time": last_calculation["last_time"].isoformat()
            if last_calculation["last_time"] else None
        })

    except Exception as e:
        logging.error(f"Statistics error: {str(e)}")
        return jsonify({
            "error": "통계 조회 중 오류가 발생했습니다.",
            "details": str(e)
        }), HTTP_STATUS["INTERNAL_SERVER_ERROR"]