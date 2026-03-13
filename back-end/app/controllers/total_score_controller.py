# app/controllers/score_controller.py - KPI 감점 시스템으로 수정
from datetime import datetime
from flask import Blueprint, request, jsonify
from app.services.total_score_service import ScoreService
from app.utils.decorators import token_required, handle_exceptions
from app.utils.constants import HTTP_STATUS

score_bp = Blueprint("score", __name__)
score_service = ScoreService()


@score_bp.route("/summary", methods=["GET"])
@token_required
@handle_exceptions
def get_security_score_summary():
    """사용자의 KPI 보안 감점 요약 조회 (100점 기준 제거)"""
    user = request.current_user
    username = user["username"]

    # 요청 파라미터에서 연도 가져오기 (기본값: 현재 연도)
    year = request.args.get("year", datetime.now().year, type=int)

    try:
        score_data = score_service.get_user_security_score(username, year)

        # 프론트엔드에서 기대하는 형식으로 데이터 변환 (KPI 감점 기준)
        response_data = {
            "user_id": score_data["user_id"],
            "year": score_data["year"],
            "audit_penalty": score_data[
                "audit_penalty"],  # 수정: audit_score -> audit_penalty
            "education_penalty": score_data["education_penalty"],
            "training_penalty": score_data["training_penalty"],
            "total_penalty": score_data[
                "total_penalty"],  # 수정: total_score -> total_penalty
            # 수정: grade 제거 (KPI에서 등급 불필요)
            "education_stats": score_data["education_stats"],
            "training_stats": score_data["training_stats"],
            "audit_stats": score_data["audit_stats"],
        }

        return jsonify(response_data)
    except ValueError as e:
        return jsonify({"message": str(e)}), HTTP_STATUS["NOT_FOUND"]
    except Exception as e:
        return (
            jsonify({
                "error": "감점 계산 중 오류가 발생했습니다.",
                "details": str(e)
            }),  # 수정: 점수 -> 감점
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@score_bp.route("/dashboard/overview", methods=["GET"])
@token_required
@handle_exceptions
def get_security_dashboard_overview():
    """KPI 보안 대시보드 데이터 조회 (감점 기준)"""
    user = request.current_user
    username = user["username"]

    year = request.args.get("year", datetime.now().year, type=int)

    try:
        dashboard_data = score_service.get_dashboard_overview(username, year)
        return jsonify(dashboard_data)
    except ValueError as e:
        return jsonify({"message": str(e)}), HTTP_STATUS["NOT_FOUND"]
    except Exception as e:
        return (
            jsonify({
                "error": "대시보드 데이터 조회 중 오류가 발생했습니다.",
                "details": str(e),
            }),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@score_bp.route("/calculate", methods=["POST"])
@token_required
@handle_exceptions
def calculate_security_score():
    """KPI 보안 감점 강제 재계산"""
    user = request.current_user
    username = user["username"]

    data = request.json or {}
    year = data.get("year", datetime.now().year)

    try:
        # 사용자 ID 조회
        from app.utils.database import execute_query

        user_data = execute_query("SELECT uid FROM users WHERE user_id = %s",
                                  (username, ), fetch_one=True)

        if not user_data:
            return (
                jsonify({"error": "사용자를 찾을 수 없습니다."}),
                HTTP_STATUS["NOT_FOUND"],
            )

        # 감점 재계산
        score_data = score_service.calculate_security_score(user_data["uid"], year)

        return jsonify({
            "message": "KPI 보안 감점이 성공적으로 재계산되었습니다.",  # 수정
            "penalty_data": score_data,  # 수정: score_data -> penalty_data
        })
    except Exception as e:
        return (
            jsonify({
                "error": "감점 재계산 중 오류가 발생했습니다.",
                "details": str(e)
            }  # 수정
                    ),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@score_bp.route("/history", methods=["GET"])
@token_required
@handle_exceptions
def get_score_history():
    """사용자의 연도별 감점 이력 조회 (KPI 기준)"""
    user = request.current_user
    username = user["username"]

    try:
        from app.utils.database import execute_query

        # 사용자 ID 조회
        user_data = execute_query("SELECT uid FROM users WHERE user_id = %s",
                                  (username, ), fetch_one=True)
        if not user_data:
            return (
                jsonify({"error": "사용자를 찾을 수 없습니다."}),
                HTTP_STATUS["NOT_FOUND"],
            )

        user_id = user_data["uid"]

        # 최근 3년간의 감점 이력 조회
        current_year = datetime.now().year
        years = [current_year - 2, current_year - 1, current_year]

        history = []
        for year in years:
            try:
                score_data = score_service.calculate_security_score(user_id, year)
                history.append({
                    "year": year,
                    "total_penalty": score_data[
                        "total_penalty"],  # 수정: total_score -> total_penalty
                    # 수정: grade 제거
                    "audit_penalty": score_data[
                        "audit_penalty"],  # 수정: audit_score -> audit_penalty
                    "education_penalty": score_data["education_penalty"],
                    "training_penalty": score_data["training_penalty"],
                })
            except Exception as e:
                # 해당 연도 데이터가 없으면 건너뛰기
                continue

        return jsonify({"username": username, "history": history})
    except Exception as e:
        return (
            jsonify({
                "error": "감점 이력 조회 중 오류가 발생했습니다.",
                "details": str(e)
            }  # 수정
                    ),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@score_bp.route("/breakdown", methods=["GET"])
@token_required
@handle_exceptions
def get_score_breakdown():
    """감점 구성 요소별 상세 분석 (KPI 기준)"""
    user = request.current_user
    username = user["username"]

    year = request.args.get("year", datetime.now().year, type=int)

    try:
        from app.utils.database import execute_query, DatabaseManager

        # 사용자 ID 조회
        user_data = execute_query("SELECT uid FROM users WHERE user_id = %s",
                                  (username, ), fetch_one=True)
        if not user_data:
            return (
                jsonify({"error": "사용자를 찾을 수 없습니다."}),
                HTTP_STATUS["NOT_FOUND"],
            )

        user_id = user_data["uid"]

        with DatabaseManager.get_db_cursor(commit=False) as cursor:
            # 감사 항목별 상세 정보 (감점 중심)
            cursor.execute(
                """
                SELECT 
                    ci.item_name,
                    ci.category,
                    ci.penalty_weight,
                    al.passed,
                    al.checked_at,
                    al.notes,
                    CASE WHEN al.passed = 0 THEN ci.penalty_weight ELSE 0 END as penalty_applied
                FROM audit_log al
                INNER JOIN (
                    SELECT item_id, MAX(checked_at) as max_checked_at
                    FROM audit_log 
                    WHERE user_id = %s AND YEAR(checked_at) = %s
                    GROUP BY item_id
                ) latest ON al.item_id = latest.item_id AND al.checked_at = latest.max_checked_at
                INNER JOIN checklist_items ci ON al.item_id = ci.item_id
                WHERE al.user_id = %s
                ORDER BY ci.category, ci.item_name
                """,
                (user_id, year, user_id),
            )
            audit_breakdown = cursor.fetchall()

            # 교육 상세 정보 (감점 중심)
            cursor.execute(
                """
                SELECT
                    education_type,
                    education_date,
                    completion_status,
                    score,
                    exclude_from_scoring,
                    notes,
                    CASE 
                        WHEN exclude_from_scoring = 1 THEN 0
                        WHEN completion_status = 0 THEN 0.5
                        ELSE 0
                    END as penalty_applied
                FROM security_education
                WHERE user_id = %s AND education_year = %s
                """,
                (user_id, year),
            )
            education_breakdown = cursor.fetchall()

            # 모의훈련 상세 정보 (감점 중심)
            cursor.execute(
                """
                SELECT 
                    training_period,
                    email_sent_time,
                    action_time,
                    log_type,
                    mail_type,
                    training_result,
                    response_time_minutes,
                    exclude_from_scoring,
                    notes,
                    CASE 
                        WHEN exclude_from_scoring = 1 THEN 0
                        WHEN training_result = 'fail' THEN 0.5
                        ELSE 0
                    END as penalty_applied
                FROM phishing_training
                WHERE user_id = %s AND training_year = %s
                ORDER BY training_period
                """,
                (user_id, year),
            )
            training_breakdown = cursor.fetchall()

        return jsonify({
            "year": year,
            "audit_breakdown": audit_breakdown,
            "education_breakdown": education_breakdown,
            "training_breakdown": training_breakdown,
        })
    except Exception as e:
        return (
            jsonify({
                "error": "감점 분석 중 오류가 발생했습니다.",
                "details": str(e)
            }),  # 수정
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@score_bp.route("/recommendations", methods=["GET"])
@token_required
@handle_exceptions
def get_improvement_recommendations():
    """개선 권장사항 조회 (KPI 감점 기준)"""
    user = request.current_user
    username = user["username"]

    year = request.args.get("year", datetime.now().year, type=int)

    try:
        # 현재 감점 조회
        score_data = score_service.get_user_security_score(username, year)

        recommendations = []

        # 교육 관련 권장사항
        if score_data["education_penalty"] > 0:
            incomplete_count = score_data["education_stats"]["incomplete_count"]
            recommendations.append({
                "priority": "high",
                "category": "education",
                "title": "정보보호 교육 이수",
                "description": f'미이수된 교육이 {incomplete_count}회 있습니다. 교육을 완료하여 -{score_data["education_penalty"]}점 감점을 해소하세요.',
                "penalty_score": score_data[
                    "education_penalty"],  # 수정: impact_score -> penalty_score
                "action_url": "/security-education",
            })

        # 모의훈련 관련 권장사항
        if score_data["training_penalty"] > 0:
            failed_count = score_data["training_stats"]["failed_count"]
            recommendations.append({
                "priority": "high",
                "category": "training",
                "title": "악성메일 대응 능력 향상",
                "description": f'모의훈련에서 {failed_count}회 실패했습니다. 악성메일 식별 능력을 향상시켜 -{score_data["training_penalty"]}점 감점을 해소하세요.',
                "penalty_score": score_data["training_penalty"],  # 수정
                "action_url": "/phishing-training",
            })

        # 감사 관련 권장사항
        if score_data["audit_penalty"] > 0:
            failed_count = score_data["audit_stats"]["failed_count"]
            recommendations.append({
                "priority": "medium",
                "category": "audit",
                "title": "보안 설정 개선",
                "description": f'{failed_count}개 보안 설정이 정책에 맞지 않습니다. 감사 결과를 확인하고 조치하여 -{score_data["audit_penalty"]}점 감점을 해소하세요.',
                "penalty_score": score_data["audit_penalty"],  # 수정
                "action_url": "/security-audit/results",
            })

        # 총 감점에 따른 일반적인 권장사항
        if score_data["total_penalty"] >= 2.0:  # 수정: 80점 기준 -> 2점 이상 감점
            recommendations.append({
                "priority": "info",
                "category": "general",
                "title": "종합적인 보안 의식 개선",
                "description": f'현재 총 -{score_data["total_penalty"]}점 감점되었습니다. 정기적인 보안 교육 참여와 정책 준수를 권장합니다.',
                "penalty_score": 0,  # 수정
                "action_url": "/security-audit/solutions",
            })

        return jsonify({
            "current_penalty": score_data[
                "total_penalty"],  # 수정: current_score -> current_penalty
            # 수정: grade 제거
            "potential_improvement": score_data["education_penalty"] +
            score_data["training_penalty"] + score_data["audit_penalty"],
            "recommendations": recommendations,
        })
    except Exception as e:
        return (
            jsonify({
                "error": "권장사항 조회 중 오류가 발생했습니다.",
                "details": str(e)
            }),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )
