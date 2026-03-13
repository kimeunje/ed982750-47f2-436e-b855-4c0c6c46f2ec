# app/controllers/admin_dashboard_controller_fixed.py
"""
실제 데이터베이스 스키마에 맞춘 관리자 대시보드 API
"""

import csv
import io
from flask import Blueprint, make_response, request, jsonify
from datetime import datetime, timedelta
from app.utils.decorators import token_required, handle_exceptions, admin_required
from app.utils.constants import HTTP_STATUS
from app.utils.database import execute_query
from urllib.parse import quote

import logging

# 블루프린트 생성
admin_dashboard_bp = Blueprint("admin_dashboard", __name__,
                               url_prefix="/api/admin/dashboard")


# 대시보드 overview 함수도 수정 - 자동 계산을 선택적으로
@admin_dashboard_bp.route("/overview", methods=["GET"])
@token_required
@admin_required
@handle_exceptions
def get_dashboard_overview():
    """관리자 대시보드 종합 현황 - 자동 점수 계산을 선택적으로"""
    year = request.args.get("year", datetime.now().year, type=int)
    auto_calculate = request.args.get("auto_calculate",
                                      "false").lower() == "true"  # 기본값을 false로 변경

    try:
        logging.info(f"관리자 대시보드 현황 조회: year={year}, auto_calculate={auto_calculate}")

        calculated_count = 0

        # 자동 계산이 활성화된 경우에만 미계산 사용자들의 점수를 계산
        if auto_calculate:
            calculated_count = _auto_calculate_missing_scores(year)
            if calculated_count > 0:
                logging.info(f"자동 계산 완료: {calculated_count}명의 점수 계산됨")

        # 대시보드 데이터 조회
        user_stats = _get_user_statistics_fixed(year)
        score_distribution = _get_score_distribution_fixed(year)
        monthly_trends = _get_monthly_trends_fixed(year)
        department_overview = _get_department_overview_fixed(year)
        recent_activities = _get_recent_activities_fixed()
        risk_users = _get_risk_users_fixed(year)

        response_data = {
            "year": year,
            "user_stats": user_stats,
            "score_distribution": score_distribution,
            "monthly_trends": monthly_trends,
            "department_overview": department_overview,
            "position_overview": [],
            "recent_activities": recent_activities,
            "risk_users": risk_users,
            "last_updated": datetime.now().isoformat(),
            "auto_calculated_users": calculated_count
        }

        return jsonify(response_data)

    except Exception as e:
        logging.error(f"Dashboard overview error: {str(e)}")
        return jsonify({
            "error": "대시보드 현황 조회 중 오류가 발생했습니다.",
            "details": str(e)
        }), HTTP_STATUS["INTERNAL_SERVER_ERROR"]


def _auto_calculate_missing_scores(year):
    """미계산된 사용자들의 점수를 자동으로 계산 - 개선된 버전"""
    from app.services.total_score_service import ScoreService

    try:
        # 해당 연도에 점수 데이터가 없는 사용자들 조회
        missing_users_query = """
            SELECT u.uid, u.user_id, u.username 
            FROM users u
            LEFT JOIN security_score_summary sss ON u.uid = sss.user_id AND sss.evaluation_year = %s
            WHERE sss.summary_id IS NULL
            ORDER BY u.uid
        """

        missing_users = execute_query(missing_users_query, (year, ), fetch_all=True)

        if not missing_users:
            logging.info("미계산 사용자가 없습니다.")
            return 0

        logging.info(f"미계산 사용자 {len(missing_users)}명 발견, 자동 계산 시작")

        score_service = ScoreService()
        calculated_count = 0

        for user in missing_users:
            try:
                # 개별 사용자 점수 계산
                score_service.calculate_security_score(user["uid"], year)
                calculated_count += 1
                logging.debug(f"사용자 {user['user_id']} 자동 계산 완료")

            except Exception as user_error:
                logging.error(f"사용자 {user['user_id']} 자동 계산 실패: {str(user_error)}")
                continue

        logging.info(f"자동 계산 완료: {calculated_count}/{len(missing_users)}명 성공")
        return calculated_count

    except Exception as e:
        logging.error(f"자동 점수 계산 중 오류: {str(e)}")
        return 0


def _get_user_statistics_fixed(year):
    """전체 사용자 통계 - 수정된 스키마"""
    try:
        stats_query = """
            SELECT 
                COUNT(*) as total_users,
                COUNT(CASE WHEN sss.total_penalty IS NOT NULL THEN 1 END) as evaluated_users,
                COUNT(CASE WHEN sss.total_penalty <= 0.5 THEN 1 END) as excellent_users,
                COUNT(CASE WHEN sss.total_penalty > 0.5 AND sss.total_penalty <= 2.0 THEN 1 END) as warning_users,
                COUNT(CASE WHEN sss.total_penalty > 2.0 THEN 1 END) as critical_users,
                COALESCE(AVG(sss.total_penalty), 0) as avg_penalty,
                COALESCE(MAX(sss.total_penalty), 0) as max_penalty,
                COALESCE(MIN(sss.total_penalty), 0) as min_penalty,
                COUNT(DISTINCT u.department) as total_departments
            FROM users u
            LEFT JOIN security_score_summary sss ON u.uid = sss.user_id AND sss.evaluation_year = %s
        """

        result = execute_query(stats_query, (year, ), fetch_one=True)
        return dict(result) if result else {}

    except Exception as e:
        logging.error(f"User statistics error: {str(e)}")
        return {}


def _get_score_distribution_fixed(year):
    """보안 점수 분포 - 수정된 스키마"""
    try:
        distribution_query = """
            SELECT 
                CASE 
                    WHEN sss.total_penalty IS NULL THEN 'not_evaluated'
                    WHEN sss.total_penalty = 0 THEN 'perfect'
                    WHEN sss.total_penalty <= 0.5 THEN 'excellent'
                    WHEN sss.total_penalty <= 1.0 THEN 'good'
                    WHEN sss.total_penalty <= 2.0 THEN 'warning'
                    WHEN sss.total_penalty <= 3.0 THEN 'danger'
                    ELSE 'critical'
                END as score_range,
                COUNT(*) as user_count,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM users), 2) as percentage
            FROM users u
            LEFT JOIN security_score_summary sss ON u.uid = sss.user_id AND sss.evaluation_year = %s
            GROUP BY score_range
            ORDER BY 
                CASE score_range
                    WHEN 'perfect' THEN 1
                    WHEN 'excellent' THEN 2
                    WHEN 'good' THEN 3
                    WHEN 'warning' THEN 4
                    WHEN 'danger' THEN 5
                    WHEN 'critical' THEN 6
                    WHEN 'not_evaluated' THEN 7
                END
        """

        return execute_query(distribution_query, (year, ))

    except Exception as e:
        logging.error(f"Score distribution error: {str(e)}")
        return []


def _get_monthly_trends_fixed(year):
    """월별 트렌드 분석 - 수정된 스키마"""
    try:
        trends_query = """
            SELECT 
                MONTH(al.checked_at) as month,
                COUNT(DISTINCT al.user_id) as active_users,
                COUNT(al.log_id) as total_checks,
                COUNT(CASE WHEN al.passed = 0 THEN 1 END) as failed_checks,
                ROUND(COUNT(CASE WHEN al.passed = 0 THEN 1 END) * 100.0 / COUNT(al.log_id), 2) as failure_rate
            FROM audit_log al
            WHERE YEAR(al.checked_at) = %s
            GROUP BY MONTH(al.checked_at)
            ORDER BY month
        """

        return execute_query(trends_query, (year, ))

    except Exception as e:
        logging.error(f"Monthly trends error: {str(e)}")
        return []


# 새로운 엔드포인트: 실시간 점수 계산 상태 확인
@admin_dashboard_bp.route("/calculation-status", methods=["GET"])
@token_required
@admin_required
@handle_exceptions
def get_calculation_status():
    """점수 계산 상태 조회"""
    year = request.args.get("year", datetime.now().year, type=int)

    try:
        # 전체 사용자 수
        total_users = execute_query("SELECT COUNT(*) as count FROM users",
                                    fetch_one=True)["count"]

        # 계산된 사용자 수
        calculated_users = execute_query(
            "SELECT COUNT(*) as count FROM security_score_summary WHERE evaluation_year = %s",
            (year, ), fetch_one=True)["count"]

        # 최근 계산 시간
        last_calculation = execute_query(
            """
            SELECT MAX(last_calculated) as last_time, COUNT(*) as recent_count
            FROM security_score_summary 
            WHERE evaluation_year = %s AND last_calculated >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
            """, (year, ), fetch_one=True)

        response_data = {
            "year": year,
            "total_users": total_users,
            "calculated_users": calculated_users,
            "missing_users": total_users - calculated_users,
            "calculation_percentage": round(
                (calculated_users / total_users) * 100, 1) if total_users > 0 else 0,
            "last_calculation_time": last_calculation["last_time"].isoformat()
            if last_calculation["last_time"] else None,
            "recent_calculations": last_calculation["recent_count"] or 0,
            "needs_calculation": (total_users - calculated_users) > 0
        }

        return jsonify(response_data)

    except Exception as e:
        logging.error(f"Calculation status error: {str(e)}")
        return jsonify({
            "error": "계산 상태 조회 중 오류가 발생했습니다.",
            "details": str(e)
        }), HTTP_STATUS["INTERNAL_SERVER_ERROR"]


@admin_dashboard_bp.route("/trigger-calculation", methods=["POST"])
@token_required
@admin_required
@handle_exceptions
def trigger_full_calculation():
    """모든 사용자 점수 강제 재계산 - 개선된 버전"""
    data = request.json or {}
    year = data.get("year", datetime.now().year)
    force_recalculate = data.get("force_recalculate", False)

    try:
        logging.info(f"점수 계산 요청: year={year}, force_recalculate={force_recalculate}")

        if force_recalculate:
            # 모든 사용자 강제 재계산
            users_query = "SELECT uid, user_id, username FROM users ORDER BY uid"
            users = execute_query(users_query, fetch_all=True)

            if not users:
                return jsonify({"message": "계산할 사용자가 없습니다.", "calculated_count": 0})

            success_count = 0
            error_count = 0
            errors = []

            logging.info(f"전체 사용자 {len(users)}명의 점수를 강제 재계산 시작")

            from app.services.total_score_service import ScoreService
            score_service = ScoreService()

            for user in users:
                try:
                    # 기존 점수 데이터 삭제 (강제 재계산)
                    execute_query(
                        "DELETE FROM security_score_summary WHERE user_id = %s AND evaluation_year = %s",
                        (user["uid"], year))

                    # 새로 계산
                    score_service.calculate_security_score(user["uid"], year)
                    success_count += 1

                    logging.debug(f"사용자 {user['user_id']} 점수 재계산 완료")

                except Exception as user_error:
                    error_count += 1
                    error_msg = f"사용자 {user['user_id']} 계산 실패: {str(user_error)}"
                    errors.append(error_msg)
                    logging.error(error_msg)

            message = f"전체 재계산 완료: 성공 {success_count}명, 실패 {error_count}명"
            logging.info(message)

            response_data = {
                "message": message,
                "calculated_count": success_count,
                "error_count": error_count,
                "total_users": len(users),
                "year": year,
                "force_recalculate": True
            }

            if errors:
                response_data["errors"] = errors[:10]  # 최대 10개의 에러만 반환

            return jsonify(response_data)

        else:
            # 미계산 사용자만 계산 (기존 로직)
            calculated_count = _auto_calculate_missing_scores(year)

            return jsonify({
                "message": f"{calculated_count}명의 미계산 사용자 점수를 계산했습니다.",
                "calculated_count": calculated_count,
                "year": year,
                "force_recalculate": False
            })

    except Exception as e:
        logging.error(f"점수 계산 실행 중 오류: {str(e)}")
        return jsonify({
            "error": "점수 계산 중 오류가 발생했습니다.",
            "details": str(e)
        }), HTTP_STATUS["INTERNAL_SERVER_ERROR"]


def _get_department_overview_fixed(year):
    """부서별 현황 - 수정된 스키마"""
    try:
        dept_query = """
            SELECT 
                u.department,
                COUNT(*) as total_users,
                COUNT(CASE WHEN sss.total_penalty IS NOT NULL THEN 1 END) as evaluated_users,
                COALESCE(AVG(sss.total_penalty), 0) as avg_penalty,
                COUNT(CASE WHEN sss.total_penalty <= 0.5 THEN 1 END) as excellent_count,
                COUNT(CASE WHEN sss.total_penalty > 0.5 AND sss.total_penalty <= 2.0 THEN 1 END) as warning_count,
                COUNT(CASE WHEN sss.total_penalty > 2.0 THEN 1 END) as critical_count,
                ROUND(COUNT(CASE WHEN sss.total_penalty <= 0.5 THEN 1 END) * 100.0 / COUNT(*), 2) as excellent_rate
            FROM users u
            LEFT JOIN security_score_summary sss ON u.uid = sss.user_id AND sss.evaluation_year = %s
            WHERE u.department IS NOT NULL
            GROUP BY u.department
            ORDER BY avg_penalty DESC, total_users DESC
        """

        return execute_query(dept_query, (year, ))

    except Exception as e:
        logging.error(f"Department overview error: {str(e)}")
        return []


def _get_recent_activities_fixed(limit=10):
    """최근 활동 현황 - 수정된 스키마"""
    try:
        activities_query = """
            SELECT 
                'audit' as activity_type,
                u.username as user_name,
                u.department,
                ci.item_name as activity_description,
                al.checked_at as activity_time,
                CASE WHEN al.passed = 1 THEN 'success' 
                     WHEN al.passed = 0 THEN 'failure' 
                     ELSE 'pending' END as status
            FROM audit_log al
            JOIN users u ON al.user_id = u.uid
            JOIN checklist_items ci ON al.item_id = ci.item_id
            WHERE al.checked_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            ORDER BY al.checked_at DESC
            LIMIT %s
        """

        return execute_query(activities_query, (limit, ))

    except Exception as e:
        logging.error(f"Recent activities error: {str(e)}")
        return []


def _get_risk_users_fixed(year, limit=10):
    """위험 사용자 목록 - 수정된 스키마"""
    try:
        risk_query = """
            SELECT 
                u.uid,
                u.username as name,
                u.user_id as employee_id,
                u.department,
                '' as position,  -- position 컬럼이 없으므로 빈 문자열
                sss.total_penalty,
                sss.audit_penalty,
                sss.education_penalty,
                sss.training_penalty,
                sss.audit_failed_count,
                sss.education_incomplete_count,
                sss.training_failed_count,
                CASE 
                    WHEN sss.total_penalty > 3.0 THEN 'critical'
                    WHEN sss.total_penalty > 2.0 THEN 'high'
                    WHEN sss.total_penalty > 1.0 THEN 'medium'
                    ELSE 'low'
                END as risk_level
            FROM users u
            JOIN security_score_summary sss ON u.uid = sss.user_id AND sss.evaluation_year = %s
            WHERE sss.total_penalty > 1.0
            ORDER BY sss.total_penalty DESC, sss.audit_failed_count DESC
            LIMIT %s
        """

        return execute_query(risk_query, (year, limit))

    except Exception as e:
        logging.error(f"Risk users error: {str(e)}")
        return []


# === 사용자 관리 API 수정 ===


# @admin_dashboard_bp.route("/users", methods=["GET"])
# @token_required
# @admin_required
# @handle_exceptions
# def get_users_list():
#     """사용자 목록 조회 - 수정된 스키마"""
#     year = request.args.get("year", datetime.now().year, type=int)
#     department = request.args.get("department", "")
#     risk_level = request.args.get("risk_level", "")
#     search = request.args.get("search", "")
#     page = request.args.get("page", 1, type=int)
#     per_page = request.args.get("per_page", 20, type=int)
#     sort_by = request.args.get("sort_by", "total_penalty")
#     sort_order = request.args.get("sort_order", "desc")

#     try:
#         users_data, total_count = _get_filtered_users_fixed(year, department,
#                                                             risk_level, search, page,
#                                                             per_page, sort_by,
#                                                             sort_order)

#         response_data = {
#             "users": users_data,
#             "pagination": {
#                 "current_page": page,
#                 "per_page": per_page,
#                 "total_count": total_count,
#                 "total_pages": (total_count + per_page - 1) // per_page
#             },
#             "filters": {
#                 "year": year,
#                 "department": department,
#                 "risk_level": risk_level,
#                 "search": search,
#                 "sort_by": sort_by,
#                 "sort_order": sort_order
#             }
#         }

#         return jsonify(response_data)

#     except Exception as e:
#         logging.error(f"Users list error: {str(e)}")
#         return jsonify({
#             "error": "사용자 목록 조회 중 오류가 발생했습니다.",
#             "details": str(e)
#         }), HTTP_STATUS["INTERNAL_SERVER_ERROR"]



def _get_filtered_users_fixed(year, department, risk_level, search, page, per_page, 
                               sort_by="total_penalty", order="desc"):
    """필터링된 사용자 목록 조회 - 건수 포함"""
    try:
        where_conditions = ["u.is_active = 1"]
        params = [year]

        # 필터 조건
        if department:
            where_conditions.append("u.department = %s")
            params.append(department)

        if search:
            where_conditions.append(
                "(u.username LIKE %s OR u.user_id LIKE %s OR u.mail LIKE %s)"
            )
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])

        if risk_level:
            risk_conditions = {
                'critical': 'sss.total_penalty > 3.0',
                'high': 'sss.total_penalty > 2.0 AND sss.total_penalty <= 3.0',
                'medium': 'sss.total_penalty > 1.0 AND sss.total_penalty <= 2.0',
                'low': 'sss.total_penalty > 0 AND sss.total_penalty <= 1.0',
                'excellent': 'COALESCE(sss.total_penalty, 0) = 0'
            }
            if risk_level in risk_conditions:
                where_conditions.append(f"({risk_conditions[risk_level]})")

        where_clause = " AND ".join(where_conditions)

        # 전체 개수 조회
        count_query = f"""
            SELECT COUNT(*) as total
            FROM users u
            LEFT JOIN security_score_summary sss ON u.uid = sss.user_id 
                AND sss.evaluation_year = %s
            WHERE {where_clause}
        """
        
        count_result = execute_query(count_query, params, fetch_one=True)
        total_count = count_result['total'] if count_result else 0

        # 정렬
        sort_columns = {
            'name': 'u.username',
            'user_id': 'u.user_id',
            'department': 'u.department',
            'total_penalty': 'COALESCE(sss.total_penalty, 0)',
            'audit_penalty': 'COALESCE(sss.audit_penalty, 0)',
            'education_penalty': 'COALESCE(sss.education_penalty, 0)',
            'training_penalty': 'COALESCE(sss.training_penalty, 0)'
        }
        
        sort_column = sort_columns.get(sort_by, 'COALESCE(sss.total_penalty, 0)')
        order_direction = 'DESC' if order.lower() == 'desc' else 'ASC'

        # 페이징
        offset = (page - 1) * per_page
        params.extend([per_page, offset])

        # 메인 쿼리 - 건수 컬럼 추가
        query = f"""
            SELECT 
                u.uid,
                u.user_id,
                u.username as name,
                u.mail as email,
                u.department,
                u.ip,
                u.role,
                COALESCE(sss.total_penalty, 0.0) as total_penalty,
                COALESCE(sss.audit_penalty, 0.0) as audit_penalty,
                COALESCE(sss.education_penalty, 0.0) as education_penalty,
                COALESCE(sss.training_penalty, 0.0) as training_penalty,
                -- ✅ 건수 컬럼 추가
                COALESCE(sss.audit_failed_count, 0) as audit_failed_count,
                COALESCE(sss.education_incomplete_count, 0) as education_incomplete_count,
                COALESCE(sss.training_failed_count, 0) as training_failed_count,
                COALESCE(sss.audit_failed_count, 0) as security_audit_penalty,
                COALESCE(sss.education_incomplete_count, 0) as education_penalty_count,
                COALESCE(sss.training_failed_count, 0) as training_penalty_count,
                (SELECT MAX(al.checked_at) 
                 FROM audit_log al 
                 WHERE al.user_id = u.uid) as last_audit_time,
                CASE 
                    WHEN sss.total_penalty IS NULL THEN 'not_evaluated'
                    WHEN sss.total_penalty > 3.0 THEN 'critical'
                    WHEN sss.total_penalty > 2.0 THEN 'high'
                    WHEN sss.total_penalty > 1.0 THEN 'medium'
                    ELSE 'low'
                END as risk_level
            FROM users u
            LEFT JOIN security_score_summary sss ON u.uid = sss.user_id 
                AND sss.evaluation_year = %s
            WHERE {where_clause}
            ORDER BY {sort_column} {order_direction}, u.username ASC
            LIMIT %s OFFSET %s
        """

        users_data = execute_query(query, params)

        # 데이터 후처리
        for user in users_data:
            if user['last_audit_time']:
                user['last_updated'] = user['last_audit_time'].strftime('%Y-%m-%d %H:%M:%S')
            else:
                user['last_updated'] = '업데이트 없음'

        return users_data, total_count

    except Exception as e:
        logging.error(f"Filtered users query error: {str(e)}")
        return [], 0

# === 사용자 상세 API 수정 ===


@admin_dashboard_bp.route("/users/<int:user_id>/detail", methods=["GET"])
@token_required
@admin_required
@handle_exceptions
def get_user_detail(user_id):
    """특정 사용자의 상세 점수 정보 조회 - 수정된 스키마"""
    year = request.args.get("year", datetime.now().year, type=int)

    try:
        # 사용자 기본 정보 조회
        user_info = _get_user_info_fixed(user_id)
        if not user_info:
            return jsonify({"error": "사용자를 찾을 수 없습니다."}), HTTP_STATUS["NOT_FOUND"]

        # 상세 점수 계산
        score_detail = _calculate_user_detail_scores_fixed(user_id, year)

        response_data = {
            "user_info": user_info,
            "year": year,
            "score_detail": score_detail,
            "last_updated": datetime.now().isoformat()
        }

        return jsonify(response_data)

    except Exception as e:
        logging.error(f"User detail error: {str(e)}")
        return jsonify({
            "error": "사용자 상세 정보 조회 중 오류가 발생했습니다.",
            "details": str(e)
        }), HTTP_STATUS["INTERNAL_SERVER_ERROR"]


def _get_user_info_fixed(user_id):
    """사용자 기본 정보 조회 - audit_log 기반 마지막 업데이트 포함"""
    try:
        user_query = """
            SELECT 
                u.uid,
                u.user_id,
                u.username as name,
                u.mail as email,
                u.department,
                u.ip,
                u.role,
                u.created_at,
                u.updated_at,
                -- audit_log에서 사용자의 가장 최근 checked_at 시간
                (SELECT MAX(al.checked_at) 
                 FROM audit_log al 
                 WHERE al.user_id = u.uid) as last_audit_time
            FROM users u
            WHERE u.uid = %s
        """

        user_info = execute_query(user_query, (user_id, ), fetch_one=True)

        if user_info:
            # 마지막 업데이트 시간을 audit_log 기반으로 설정
            if user_info['last_audit_time']:
                user_info['updated_at'] = user_info['last_audit_time']

            # datetime 객체를 문자열로 변환
            if user_info.get("created_at"):
                user_info["created_at"] = user_info["created_at"].isoformat()
            if user_info.get("updated_at"):
                user_info["updated_at"] = user_info["updated_at"].isoformat()

        return user_info

    except Exception as e:
        logging.error(f"사용자 정보 조회 오류: {str(e)}")
        return None


def _calculate_user_detail_scores_fixed(user_id, year):
    """사용자 상세 점수 계산 - 수정된 스키마"""
    try:
        # security_score_summary에서 직접 조회
        summary_query = """
            SELECT 
                total_penalty,
                audit_penalty,
                education_penalty,
                training_penalty,
                audit_failed_count,
                education_incomplete_count,
                training_failed_count
            FROM security_score_summary
            WHERE user_id = %s AND evaluation_year = %s
        """

        summary_result = execute_query(summary_query, (user_id, year), fetch_one=True)

        if not summary_result:
            # 데이터가 없으면 0으로 초기화
            return {
                "total_penalty": 0.0,
                "audit_penalty": 0.0,
                "education_penalty": 0.0,
                "training_penalty": 0.0,
                "audit_stats": {
                    "failed_count": 0,
                    "total_count": 0,
                    "failed_items": []
                },
                "education_stats": {
                    "incomplete_count": 0,
                    "total_count": 0,
                    "incomplete_items": []
                },
                "training_stats": {
                    "failed_count": 0,
                    "total_count": 0,
                    "failed_items": []
                }
            }

        # 상세 내역 조회
        audit_stats = _get_audit_details_fixed(user_id, year)
        education_stats = _get_education_details_fixed(user_id, year)
        training_stats = _get_training_details_fixed(user_id, year)

        return {
            "total_penalty": float(summary_result["total_penalty"] or 0),
            "audit_penalty": float(summary_result["audit_penalty"] or 0),
            "education_penalty": float(summary_result["education_penalty"] or 0),
            "training_penalty": float(summary_result["training_penalty"] or 0),
            "audit_stats": audit_stats,
            "education_stats": education_stats,
            "training_stats": training_stats
        }

    except Exception as e:
        logging.error(f"User detail calculation error: {str(e)}")
        return {
            "total_penalty": 0.0,
            "audit_penalty": 0.0,
            "education_penalty": 0.0,
            "training_penalty": 0.0,
            "audit_stats": {},
            "education_stats": {},
            "training_stats": {}
        }


def _get_audit_details_fixed(user_id, year):
    """감사 상세 내역 조회 - 수정된 스키마"""
    try:
        audit_query = """
            SELECT 
                ci.item_name,
                al.checked_at,
                ci.penalty_weight
            FROM audit_log al
            JOIN checklist_items ci ON al.item_id = ci.item_id
            WHERE al.user_id = %s 
            AND YEAR(al.checked_at) = %s 
            AND al.passed = 0
            ORDER BY al.checked_at DESC
        """

        failed_items = execute_query(audit_query, (user_id, year))

        return {
            "failed_count": len(failed_items),
            "total_count": len(failed_items),  # 간단하게 처리
            "failed_items": [{
                "item_name": item["item_name"],
                "checked_at": item["checked_at"].isoformat()
                if item["checked_at"] else None,
                "penalty": float(item["penalty_weight"] or 0.5)
            } for item in failed_items]
        }

    except Exception as e:
        logging.error(f"Audit details error: {str(e)}")
        return {"failed_count": 0, "total_count": 0, "failed_items": []}


def _get_education_details_fixed(user_id, year):
    """교육 상세 내역 조회 - 수정된 스키마"""
    try:
        # security_education 테이블 구조에 맞게 조회
        education_query = """
            SELECT
                completion_status,
                completion_date
            FROM security_education
            WHERE user_id = %s 
            AND education_year = %s 
            AND completion_status != 'completed'
        """

        incomplete_items = execute_query(education_query, (user_id, year))

        return {
            "incomplete_count": len(incomplete_items),
            "total_count": len(incomplete_items),
            "incomplete_items": [
                {
                    "education_name": f"{year}년 정보보호 교육",
                    "due_date": None,  # 마감일 정보가 없음
                    "penalty": 0.5
                } for item in incomplete_items
            ]
        }

    except Exception as e:
        logging.error(f"Education details error: {str(e)}")
        return {"incomplete_count": 0, "total_count": 0, "incomplete_items": []}


def _get_training_details_fixed(user_id, year):
    """훈련 상세 내역 조회 - 수정된 스키마"""
    try:
        # phishing_training 테이블 구조에 맞게 조회
        training_query = """
            SELECT 
                training_period,
                training_result,
                email_sent_time,
                action_time
            FROM phishing_training
            WHERE user_id = %s 
            AND training_year = %s 
            AND training_result = 'fail'
        """

        failed_items = execute_query(training_query, (user_id, year))

        return {
            "failed_count": len(failed_items),
            "total_count": len(failed_items),
            "failed_items": [{
                "training_name": f"{year}년 {item['training_period']} 악성메일 모의훈련",
                "conducted_at": item["email_sent_time"].isoformat()
                if item["email_sent_time"] else None,
                "result": item["training_result"],
                "penalty": 0.5
            } for item in failed_items]
        }

    except Exception as e:
        logging.error(f"Training details error: {str(e)}")
        return {"failed_count": 0, "total_count": 0, "failed_items": []}


# 필터 옵션 API
@admin_dashboard_bp.route("/users/filters", methods=["GET"])
@token_required
@admin_required
@handle_exceptions
def get_filter_options():
    """필터 옵션 조회 - 수정된 스키마"""
    try:
        # 부서 목록 조회
        departments_query = """
            SELECT DISTINCT department 
            FROM users 
            WHERE department IS NOT NULL AND department != ''
            ORDER BY department
        """
        departments = [row['department'] for row in execute_query(departments_query)]

        return jsonify({
            "departments": departments,
            "positions": [],  # position 컬럼이 없으므로 빈 배열
            "risk_levels": [{
                "value": "low",
                "label": "낮음"
            }, {
                "value": "medium",
                "label": "보통"
            }, {
                "value": "high",
                "label": "높음"
            }, {
                "value": "critical",
                "label": "매우 높음"
            }, {
                "value": "not_evaluated",
                "label": "미평가"
            }]
        })

    except Exception as e:
        logging.error(f"Filter options error: {str(e)}")
        return jsonify({
            "error": "필터 옵션 조회 중 오류가 발생했습니다.",
            "details": str(e)
        }), HTTP_STATUS["INTERNAL_SERVER_ERROR"]


# 추가: 계산 진행 상황을 실시간으로 확인할 수 있는 API
@admin_dashboard_bp.route("/calculation-progress", methods=["GET"])
@token_required
@admin_required
@handle_exceptions
def get_calculation_progress():
    """점수 계산 진행 상황 조회 (실시간)"""
    year = request.args.get("year", datetime.now().year, type=int)

    try:
        # 전체 사용자 수
        total_users = execute_query("SELECT COUNT(*) as count FROM users",
                                    fetch_one=True)["count"]

        # 해당 연도에 계산된 사용자 수
        calculated_users = execute_query(
            "SELECT COUNT(*) as count FROM security_score_summary WHERE evaluation_year = %s",
            (year, ), fetch_one=True)["count"]

        # 최근 1분간 계산된 사용자 수 (실시간 진행률 확인용)
        recent_calculations = execute_query(
            """
            SELECT COUNT(*) as count FROM security_score_summary 
            WHERE evaluation_year = %s 
            AND last_calculated >= DATE_SUB(NOW(), INTERVAL 1 MINUTE)
            """, (year, ), fetch_one=True)["count"]

        progress_percentage = round(
            (calculated_users / total_users) * 100, 1) if total_users > 0 else 0

        return jsonify({
            "year": year,
            "total_users": total_users,
            "calculated_users": calculated_users,
            "missing_users": total_users - calculated_users,
            "progress_percentage": progress_percentage,
            "recent_calculations": recent_calculations,
            "is_complete": calculated_users >= total_users,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logging.error(f"Calculation progress error: {str(e)}")
        return jsonify({
            "error": "계산 진행 상황 조회 중 오류가 발생했습니다.",
            "details": str(e)
        }), HTTP_STATUS["INTERNAL_SERVER_ERROR"]



@admin_dashboard_bp.route("/export", methods=["GET"])
@token_required
@admin_required
@handle_exceptions
def export_users():
    """사용자 데이터 내보내기 (CSV)"""
    year = request.args.get("year", datetime.now().year, type=int)
    department = request.args.get("department", "")
    risk_level = request.args.get("risk_level", "")
    search = request.args.get("search", "")
    user_ids = request.args.get("user_ids", "")
    format_type = request.args.get("format", "csv")
    export_type = request.args.get("type", "summary")
    export_mode = request.args.get("mode", "count")  # count | item_count | normalized

    try:
        logging.info(f"데이터 내보내기 요청: year={year}, type={export_type}, mode={export_mode}")

        # 선택된 사용자만 내보내기
        if user_ids:
            user_id_list = [int(uid.strip()) for uid in user_ids.split(",") if uid.strip()]
            users_data = _get_selected_users_for_export(user_id_list, year)
        else:
            # 전체 또는 필터링된 데이터 내보내기
            users_data, _ = _get_filtered_users_fixed(year, department, risk_level,
                                                      search, 1, 10000, "total_penalty", "desc")

        if format_type.lower() == "csv":
            if export_type == "detailed":
                # 상세 보고서 (사용자별 전체 내역)
                return _export_as_csv_detailed(users_data, year)
            elif export_mode == "normalized":
                # 항목별 정규화 (결함 있으면 1건)
                return _export_as_csv_item_normalized(users_data, year)
            elif export_mode == "item_count":
                # 항목별 상세 건수
                return _export_as_csv_with_item_details(users_data, year)
            else:
                # 기본 요약 보고서
                return _export_as_csv(users_data, year)
        else:
            return jsonify({"error": "지원하지 않는 형식입니다."}), HTTP_STATUS["BAD_REQUEST"]

    except Exception as e:
        logging.error(f"Export error: {str(e)}")
        return jsonify({"error": "내보내기 중 오류가 발생했습니다."}), HTTP_STATUS["INTERNAL_SERVER_ERROR"]


def _get_selected_users_for_export(user_ids, year):
    """선택된 사용자들의 데이터 조회 - 건수 포함"""
    try:
        if not user_ids:
            return []

        placeholders = ",".join(["%s"] * len(user_ids))

        query = f"""
            SELECT 
                u.uid,
                u.user_id,
                u.username as name,
                u.mail as email,
                u.department,
                u.ip,
                u.role,
                COALESCE(sss.total_penalty, 0.0) as total_penalty,
                COALESCE(sss.audit_penalty, 0.0) as audit_penalty,
                COALESCE(sss.education_penalty, 0.0) as education_penalty,
                COALESCE(sss.training_penalty, 0.0) as training_penalty,
                -- ✅ 건수 컬럼 추가
                COALESCE(sss.audit_failed_count, 0) as audit_failed_count,
                COALESCE(sss.education_incomplete_count, 0) as education_incomplete_count,
                COALESCE(sss.training_failed_count, 0) as training_failed_count,
                COALESCE(sss.audit_failed_count, 0) as security_audit_penalty,
                COALESCE(sss.education_incomplete_count, 0) as education_penalty_count,
                COALESCE(sss.training_failed_count, 0) as training_penalty_count,
                -- audit_log에서 가장 최근 checked_at 시간
                (SELECT MAX(al.checked_at) 
                 FROM audit_log al 
                 WHERE al.user_id = u.uid) as last_audit_time,
                CASE 
                    WHEN sss.total_penalty IS NULL THEN 'not_evaluated'
                    WHEN sss.total_penalty > 3.0 THEN 'critical'
                    WHEN sss.total_penalty > 2.0 THEN 'high'
                    WHEN sss.total_penalty > 1.0 THEN 'medium'
                    ELSE 'low'
                END as risk_level
            FROM users u
            LEFT JOIN security_score_summary sss ON u.uid = sss.user_id AND sss.evaluation_year = %s
            WHERE u.uid IN ({placeholders})
            ORDER BY u.username ASC
        """

        params = [year] + user_ids
        users_data = execute_query(query, params)

        # 데이터 후처리
        for user in users_data:
            user['total_penalty'] = float(user['total_penalty'])
            user['audit_penalty'] = float(user['audit_penalty'])
            user['education_penalty'] = float(user['education_penalty'])
            user['training_penalty'] = float(user['training_penalty'])

            # 마지막 업데이트 시간을 audit_log 기반으로 설정
            if user['last_audit_time']:
                user['updated_at'] = user['last_audit_time']
                user['last_updated'] = user['last_audit_time'].strftime('%Y-%m-%d %H:%M:%S')
            else:
                user['last_updated'] = '업데이트 없음'

        return users_data

    except Exception as e:
        logging.error(f"Selected users export error: {str(e)}")
        return []


def _export_as_csv(users_data, year):
    """CSV 형식으로 데이터 내보내기 - 건수 기반"""
    try:
        output = io.StringIO()
        writer = csv.writer(output)

        # CSV 헤더 - 건수 중심으로 변경
        headers = [
            "사번", "이름", "이메일", "부서", "IP주소", "권한",
            "총 미흡 건수",  # 변경: 총감점 → 총 미흡 건수
            "감사 미흡 건수",  # 변경: 감사감점 → 감사 미흡 건수
            "교육 미완료 건수",  # 변경: 교육감점 → 교육 미완료 건수
            "훈련 실패 건수",  # 변경: 훈련감점 → 훈련 실패 건수
            "위험도",
            "마지막업데이트"
        ]
        writer.writerow(headers)

        # 데이터 행
        for user in users_data:
            risk_labels = {
                'low': '우수',
                'medium': '주의',
                'high': '위험',
                'critical': '매우위험',
                'not_evaluated': '미평가'
            }

            # 건수 계산
            audit_count = user.get('security_audit_penalty', 0) or user.get('audit_failed_count', 0)
            education_count = user.get('education_penalty_count', 0) or user.get('education_incomplete_count', 0)
            training_count = user.get('training_penalty_count', 0) or user.get('training_failed_count', 0)
            total_count = audit_count + education_count + training_count

            row = [
                user.get('user_id', ''),
                user.get('name', ''),
                user.get('email', ''),
                user.get('department', ''),
                user.get('ip', ''),
                '관리자' if user.get('role') == 'admin' else '일반사용자',
                f"{total_count}건",  # 총 건수
                f"{audit_count}건",  # 감사 건수
                f"{education_count}건",  # 교육 건수
                f"{training_count}건",  # 훈련 건수
                risk_labels.get(user.get('risk_level', 'not_evaluated'), '미평가'),
                user.get('last_updated', '업데이트 없음')
            ]
            writer.writerow(row)

        # CSV 데이터 생성
        csv_data = output.getvalue()
        output.close()

        # UTF-8 BOM 추가
        csv_with_bom = '\ufeff' + csv_data
        csv_bytes = csv_with_bom.encode('utf-8')
        
        response = make_response(csv_bytes)
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        
        # 파일명 설정
        filename = f"사용자_보안현황_{year}년_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        encoded_filename = quote(filename)
        
        response.headers['Content-Disposition'] = (
            f"attachment; "
            f"filename*=UTF-8''{encoded_filename}; "
            f'filename="security_status_{year}.csv"'
        )

        logging.info(f"CSV 파일 생성 완료 (건수 기반): {filename} (총 {len(users_data)}명)")
        return response

    except Exception as e:
        logging.error(f"CSV export error: {str(e)}")
        raise



def _export_as_csv_detailed(users_data, year):
    """
    상세 보고서 CSV 내보내기 - 각 사용자의 감점 상세 내역 포함
    """
    try:
        output = io.StringIO()
        writer = csv.writer(output)

        # 메인 헤더
        writer.writerow([f'종합보안점수 상세 보고서 ({year}년)'])
        writer.writerow(['생성일시:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        writer.writerow([])  # 빈 줄

        # 사용자별 상세 정보 작성
        for idx, user in enumerate(users_data, 1):
            # 사용자 기본 정보 섹션
            writer.writerow([f'=== {idx}. {user.get("name", "Unknown")} ({user.get("user_id", "")}) ==='])
            writer.writerow([])
            
            # 기본 정보
            writer.writerow(['[기본 정보]'])
            writer.writerow(['사번', user.get('user_id', '')])
            writer.writerow(['이름', user.get('name', '')])
            writer.writerow(['부서', user.get('department', '')])
            writer.writerow(['이메일', user.get('email', '')])
            writer.writerow(['IP주소', user.get('ip', '')])
            writer.writerow([])
            
            # 종합 점수
            writer.writerow(['[종합 보안 점수]'])
            writer.writerow(['총 감점', f"{user.get('total_penalty', 0):.1f}점"])
            writer.writerow(['상시감사 감점', f"{user.get('audit_penalty', 0):.1f}점"])
            writer.writerow(['교육 감점', f"{user.get('education_penalty', 0):.1f}점"])
            writer.writerow(['모의훈련 감점', f"{user.get('training_penalty', 0):.1f}점"])
            
            risk_labels = {
                'low': '우수',
                'medium': '주의',
                'high': '위험',
                'critical': '매우위험',
                'not_evaluated': '미평가'
            }
            writer.writerow(['위험도', risk_labels.get(user.get('risk_level', 'not_evaluated'), '미평가')])
            writer.writerow([])
            
            # 상세 감점 내역 조회
            user_id = user.get('uid')
            if user_id:
                # 1. 상시감사 상세 내역
                audit_details = _get_audit_details(user_id, year)
                if audit_details:
                    writer.writerow(['[상시감사 상세 내역]'])
                    writer.writerow(['점검일시', '항목명', '결과', '감점'])
                    for detail in audit_details:
                        writer.writerow([
                            detail.get('checked_at', ''),
                            detail.get('item_name', ''),
                            '미흡' if detail.get('passed') == 0 else '양호',
                            f"{detail.get('penalty', 0):.1f}점" if detail.get('passed') == 0 else '0점'
                        ])
                    writer.writerow([])
                
                # 2. 교육 상세 내역
                education_details = _get_education_details(user_id, year)
                if education_details:
                    writer.writerow(['[정보보호 교육 상세 내역]'])
                    writer.writerow(['교육기간', '상태', '감점'])
                    for detail in education_details:
                        writer.writerow([
                            detail.get('period_name', ''),
                            '미완료' if detail.get('is_incomplete') else '완료',
                            f"{detail.get('penalty', 0):.1f}점" if detail.get('is_incomplete') else '0점'
                        ])
                    writer.writerow([])
                
                # 3. 모의훈련 상세 내역
                training_details = _get_training_details(user_id, year)
                if training_details:
                    writer.writerow(['[모의훈련 상세 내역]'])
                    writer.writerow(['훈련일시', '훈련유형', '결과', '감점'])
                    for detail in training_details:
                        writer.writerow([
                            detail.get('sent_time', ''),
                            detail.get('mail_type', ''),
                            detail.get('result', ''),
                            f"{detail.get('penalty', 0):.1f}점" if detail.get('failed') else '0점'
                        ])
                    writer.writerow([])
            
            writer.writerow([])  # 사용자 구분 빈 줄
            writer.writerow(['-' * 80])  # 구분선
            writer.writerow([])

        # 요약 통계
        writer.writerow(['=== 전체 요약 통계 ==='])
        writer.writerow([])
        total_users = len(users_data)
        high_risk_users = len([u for u in users_data if u.get('total_penalty', 0) > 2.0])
        medium_risk_users = len([u for u in users_data if 1.0 < u.get('total_penalty', 0) <= 2.0])
        low_risk_users = len([u for u in users_data if 0 < u.get('total_penalty', 0) <= 1.0])
        excellent_users = len([u for u in users_data if u.get('total_penalty', 0) == 0])
        
        writer.writerow(['전체 사용자 수', total_users])
        writer.writerow(['우수 (0점)', excellent_users])
        writer.writerow(['양호 (0-1점)', low_risk_users])
        writer.writerow(['주의 (1-2점)', medium_risk_users])
        writer.writerow(['위험 (2점 초과)', high_risk_users])
        writer.writerow([])
        
        avg_penalty = sum([u.get('total_penalty', 0) for u in users_data]) / total_users if total_users > 0 else 0
        writer.writerow(['평균 감점', f"{avg_penalty:.2f}점"])

        # CSV 데이터 생성
        csv_data = output.getvalue()
        output.close()

        # UTF-8 BOM 추가
        csv_with_bom = '\ufeff' + csv_data
        csv_bytes = csv_with_bom.encode('utf-8')
        
        response = make_response(csv_bytes)
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        
        # 파일명 설정
        filename = f"상세보고서_전체사용자_{year}년_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        encoded_filename = quote(filename)
        
        response.headers['Content-Disposition'] = (
            f"attachment; "
            f"filename*=UTF-8''{encoded_filename}; "
            f'filename="detailed_report_{year}.csv"'
        )

        logging.info(f"상세 보고서 CSV 파일 생성 완료: {filename} (총 {len(users_data)}명)")
        return response

    except Exception as e:
        logging.error(f"Detailed CSV export error: {str(e)}")
        raise



def _get_audit_details(user_id, year):
    """상시감사 상세 내역 조회"""
    try:
        from app.utils.database import execute_query
        
        query = """
            SELECT 
                al.checked_at,
                ci.item_name,
                al.passed,
                ci.penalty_weight as penalty
            FROM audit_log al
            INNER JOIN checklist_items ci ON al.item_id = ci.item_id
            WHERE al.user_id = %s 
            AND YEAR(al.checked_at) = %s
            AND al.passed = 0
            ORDER BY al.checked_at DESC
            LIMIT 100
        """
        
        return execute_query(query, (user_id, year))
    except Exception as e:
        logging.error(f"Audit details error: {str(e)}")
        return []


def _get_education_details(user_id, year):
    """교육 상세 내역 조회"""
    try:
        from app.utils.database import execute_query
        
        query = """
            SELECT 
                ep.period_name,
                CASE 
                    WHEN se.completion_status = 'incomplete' THEN 1
                    ELSE 0
                END as is_incomplete,
                CASE 
                    WHEN se.completion_status = 'incomplete' THEN 0.5
                    ELSE 0
                END as penalty
            FROM security_education se
            INNER JOIN education_periods ep ON se.period_id = ep.period_id
            WHERE se.user_id = %s 
            AND se.education_year = %s
            AND se.exclude_from_scoring = 0
            ORDER BY ep.start_date DESC
        """
        
        return execute_query(query, (user_id, year))
    except Exception as e:
        logging.error(f"Education details error: {str(e)}")
        return []


def _get_training_details(user_id, year):
    """모의훈련 상세 내역 조회"""
    try:
        from app.utils.database import execute_query
        
        query = """
            SELECT 
                pt.email_sent_time as sent_time,
                pt.mail_type,
                pt.training_result as result,
                CASE 
                    WHEN pt.training_result = 'fail' THEN 1
                    ELSE 0
                END as failed,
                CASE 
                    WHEN pt.training_result = 'fail' THEN 0.5
                    ELSE 0
                END as penalty
            FROM phishing_training pt
            WHERE pt.user_id = %s 
            AND pt.training_year = %s
            AND pt.exclude_from_scoring = 0
            ORDER BY pt.email_sent_time DESC
            LIMIT 50
        """
        
        return execute_query(query, (user_id, year))
    except Exception as e:
        logging.error(f"Training details error: {str(e)}")
        return []
    

def _export_as_csv_with_item_details(users_data, year):
    """
    CSV 형식으로 데이터 내보내기 - 개별 항목별 건수 포함
    각 감사 항목별로 미흡 건수를 개별 컬럼으로 표시
    """
    try:
        # 1단계: 모든 감사 항목 목록 조회
        checklist_items = _get_all_checklist_items()
        manual_check_items = _get_all_manual_check_items()
        
        output = io.StringIO()
        writer = csv.writer(output)

        # CSV 헤더 구성
        base_headers = [
            "사번", "이름", "이메일", "부서", "IP주소", "권한"
        ]
        
        # 상시감사 항목별 헤더 추가
        audit_headers = [item['item_name'] for item in checklist_items]
        
        # 수시점검 항목별 헤더 추가
        manual_headers = [item['item_name'] for item in manual_check_items]
        
        # 교육/훈련 헤더
        summary_headers = [
            "교육 미완료 건수",
            "훈련 실패 건수",
            "총 미흡 건수",
            "위험도",
            "마지막업데이트"
        ]
        
        # 전체 헤더 조합
        headers = base_headers + audit_headers + manual_headers + summary_headers
        writer.writerow(headers)

        # 데이터 행
        for user in users_data:
            # 2단계: 사용자별 항목별 미흡 건수 조회
            user_id = user.get('uid')
            item_counts = _get_user_item_counts(user_id, year, checklist_items, manual_check_items)
            
            risk_labels = {
                'low': '우수',
                'medium': '주의',
                'high': '위험',
                'critical': '매우위험',
                'not_evaluated': '미평가'
            }

            # 기본 정보
            base_data = [
                user.get('user_id', ''),
                user.get('name', ''),
                user.get('email', ''),
                user.get('department', ''),
                user.get('ip', ''),
                '관리자' if user.get('role') == 'admin' else '일반사용자'
            ]
            
            # 상시감사 항목별 건수
            audit_counts = [f"{item_counts['audit'].get(item['item_id'], 0)}건" 
                          for item in checklist_items]
            
            # 수시점검 항목별 건수
            manual_counts = [f"{item_counts['manual'].get(item['item_id'], 0)}건" 
                           for item in manual_check_items]
            
            # 교육/훈련/총합
            education_count = user.get('education_incomplete_count', 0)
            training_count = user.get('training_failed_count', 0)
            
            # 총 미흡 건수 계산
            total_audit = sum(item_counts['audit'].values())
            total_manual = sum(item_counts['manual'].values())
            total_count = total_audit + total_manual + education_count + training_count
            
            summary_data = [
                f"{education_count}건",
                f"{training_count}건",
                f"{total_count}건",
                risk_labels.get(user.get('risk_level', 'not_evaluated'), '미평가'),
                user.get('last_updated', '업데이트 없음')
            ]
            
            # 전체 행 조합
            row = base_data + audit_counts + manual_counts + summary_data
            writer.writerow(row)

        # CSV 데이터 생성
        csv_data = output.getvalue()
        output.close()

        # UTF-8 BOM 추가
        csv_with_bom = '\ufeff' + csv_data
        csv_bytes = csv_with_bom.encode('utf-8')
        
        response = make_response(csv_bytes)
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        
        # 파일명 설정
        filename = f"사용자_보안현황_항목별_{year}년_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        encoded_filename = quote(filename)
        
        response.headers['Content-Disposition'] = (
            f"attachment; "
            f"filename*=UTF-8''{encoded_filename}; "
            f'filename="security_status_detailed_{year}.csv"'
        )

        logging.info(f"CSV 파일 생성 완료 (항목별 상세): {filename} (총 {len(users_data)}명)")
        return response

    except Exception as e:
        logging.error(f"CSV export with item details error: {str(e)}")
        raise


def _get_all_checklist_items():
    """모든 상시감사 항목 조회"""
    try:
        from app.utils.database import execute_query
        
        query = """
            SELECT item_id, item_name, category
            FROM checklist_items
            WHERE check_type = 'daily'
            ORDER BY item_id ASC
        """
        
        return execute_query(query, fetch_all=True)
    except Exception as e:
        logging.error(f"Get checklist items error: {str(e)}")
        return []


def _get_all_manual_check_items():
    """모든 수시점검 항목 조회"""
    try:
        from app.utils.database import execute_query
        
        query = """
            SELECT item_id, item_name, item_category as category
            FROM manual_check_items
            WHERE is_active = 1
            ORDER BY item_id ASC
        """
        
        return execute_query(query, fetch_all=True)
    except Exception as e:
        logging.error(f"Get manual check items error: {str(e)}")
        return []


def _get_user_item_counts(user_id, year, checklist_items, manual_check_items):
    """
    사용자별 개별 항목 미흡 건수 조회
    
    Returns:
        {
            'audit': {item_id: count, ...},  # 상시감사 항목별 건수
            'manual': {item_id: count, ...}  # 수시점검 항목별 건수
        }
    """
    try:
        from app.utils.database import execute_query
        
        result = {
            'audit': {},
            'manual': {}
        }
        
        # 1. 상시감사 항목별 미흡 건수 (audit_log)
        if checklist_items:
            audit_query = """
                SELECT 
                    al.item_id,
                    COUNT(*) as fail_count
                FROM audit_log al
                WHERE al.user_id = %s 
                AND YEAR(al.checked_at) = %s
                AND al.passed = 0
                GROUP BY al.item_id
            """
            
            audit_results = execute_query(audit_query, (user_id, year), fetch_all=True)
            
            # 딕셔너리로 변환
            for row in audit_results:
                result['audit'][row['item_id']] = row['fail_count']
        
        # 2. 수시점검 항목별 미흡 건수 (manual_check_results)
        if manual_check_items:
            manual_query = """
                SELECT 
                    mci.item_id,
                    COUNT(*) as fail_count
                FROM manual_check_results mcr
                INNER JOIN manual_check_items mci 
                    ON mcr.check_item_code = CONCAT(
                        CASE 
                            WHEN mci.item_code = 'seal_check' THEN 'seal_check'
                            WHEN mci.item_code = 'malware_scan' THEN 'malware_scan'
                            WHEN mci.item_code = 'file_encryption' THEN 'file_encryption'
                            ELSE mci.item_code
                        END
                    )
                WHERE mcr.user_id = %s 
                AND mcr.check_year = %s
                AND mcr.overall_result = 'fail'
                AND mcr.exclude_from_scoring = 0
                GROUP BY mci.item_id
            """
            
            manual_results = execute_query(manual_query, (user_id, year), fetch_all=True)
            
            # 딕셔너리로 변환
            for row in manual_results:
                result['manual'][row['item_id']] = row['fail_count']
        
        return result
        
    except Exception as e:
        logging.error(f"Get user item counts error: {str(e)}")
        return {'audit': {}, 'manual': {}}


def _export_as_csv_item_normalized(users_data, year):
    """
    CSV 형식으로 데이터 내보내기 - 항목별 정규화 (결함 있으면 1건)
    
    기존: 화면보호기 49건, 백신 3건 → 점수 계산 복잡
    신규: 화면보호기 1건, 백신 1건 → 결함 여부만 표시
    """
    try:
        # 1단계: 모든 감사 항목 목록 조회
        checklist_items = _get_all_checklist_items()
        manual_check_items = _get_all_manual_check_items()
        
        output = io.StringIO()
        writer = csv.writer(output)

        # CSV 헤더 구성
        base_headers = [
            "사번", "이름", "이메일", "부서", "IP주소", "권한"
        ]
        
        # 상시감사 항목별 헤더 추가
        audit_headers = [item['item_name'] for item in checklist_items]
        
        # 수시점검 항목별 헤더 추가
        manual_headers = [item['item_name'] for item in manual_check_items]
        
        # 교육/훈련 헤더
        summary_headers = [
            "교육 미완료",
            "훈련 실패",
            "총 미흡 항목수",
            "위험도",
            "마지막업데이트"
        ]
        
        # 전체 헤더 조합
        headers = base_headers + audit_headers + manual_headers + summary_headers
        writer.writerow(headers)

        # 데이터 행
        for user in users_data:
            # 2단계: 사용자별 항목별 결함 여부 조회 (정규화)
            user_id = user.get('uid')
            item_status = _get_user_item_status_normalized(user_id, year, checklist_items, manual_check_items)
            
            risk_labels = {
                'low': '우수',
                'medium': '주의',
                'high': '위험',
                'critical': '매우위험',
                'not_evaluated': '미평가'
            }

            # 기본 정보
            base_data = [
                user.get('user_id', ''),
                user.get('name', ''),
                user.get('email', ''),
                user.get('department', ''),
                user.get('ip', ''),
                '관리자' if user.get('role') == 'admin' else '일반사용자'
            ]
            
            # 상시감사 항목별 상태 (결함 있으면 1건, 없으면 0건)
            audit_status = ["1건" if item_status['audit'].get(item['item_id'], False) else "0건"
                          for item in checklist_items]
            
            # 수시점검 항목별 상태
            manual_status = ["1건" if item_status['manual'].get(item['item_id'], False) else "0건"
                           for item in manual_check_items]
            
            # 교육/훈련
            education_has_issue = user.get('education_incomplete_count', 0) > 0
            training_has_issue = user.get('training_failed_count', 0) > 0
            
            # 총 미흡 항목 수 계산 (결함이 있는 항목 개수)
            total_issues = (
                sum(1 for status in item_status['audit'].values() if status) +
                sum(1 for status in item_status['manual'].values() if status) +
                (1 if education_has_issue else 0) +
                (1 if training_has_issue else 0)
            )
            
            summary_data = [
                "1건" if education_has_issue else "0건",
                "1건" if training_has_issue else "0건",
                f"{total_issues}건",
                risk_labels.get(user.get('risk_level', 'not_evaluated'), '미평가'),
                user.get('last_updated', '업데이트 없음')
            ]
            
            # 전체 행 조합
            row = base_data + audit_status + manual_status + summary_data
            writer.writerow(row)

        # CSV 데이터 생성
        csv_data = output.getvalue()
        output.close()

        # UTF-8 BOM 추가
        csv_with_bom = '\ufeff' + csv_data
        csv_bytes = csv_with_bom.encode('utf-8')
        
        response = make_response(csv_bytes)
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        
        # 파일명 설정
        filename = f"사용자_보안현황_정규화_{year}년_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        encoded_filename = quote(filename)
        
        response.headers['Content-Disposition'] = (
            f"attachment; "
            f"filename*=UTF-8''{encoded_filename}; "
            f'filename="security_status_normalized_{year}.csv"'
        )

        logging.info(f"CSV 파일 생성 완료 (정규화): {filename} (총 {len(users_data)}명)")
        return response

    except Exception as e:
        logging.error(f"CSV export normalized error: {str(e)}")
        raise


def _get_user_item_status_normalized(user_id, year, checklist_items, manual_check_items):
    """
    사용자별 개별 항목 결함 여부 조회 (정규화 - 있으면 True, 없으면 False)
    
    Returns:
        {
            'audit': {item_id: True/False, ...},  # 상시감사 항목별 결함 여부
            'manual': {item_id: True/False, ...}  # 수시점검 항목별 결함 여부
        }
    """
    try:
        from app.utils.database import execute_query
        
        result = {
            'audit': {},
            'manual': {}
        }
        
        # 1. 상시감사 항목별 결함 여부 (audit_log)
        if checklist_items:
            audit_query = """
                SELECT 
                    al.item_id,
                    COUNT(*) as fail_count
                FROM audit_log al
                WHERE al.user_id = %s 
                AND YEAR(al.checked_at) = %s
                AND al.passed = 0
                GROUP BY al.item_id
            """
            
            audit_results = execute_query(audit_query, (user_id, year), fetch_all=True)
            
            # 모든 항목을 False로 초기화
            for item in checklist_items:
                result['audit'][item['item_id']] = False
            
            # 결함이 있는 항목만 True로 설정 (건수 상관없이)
            for row in audit_results:
                if row['fail_count'] > 0:
                    result['audit'][row['item_id']] = True
        
        # 2. 수시점검 항목별 결함 여부 (manual_check_results)
        if manual_check_items:
            manual_query = """
                SELECT 
                    mci.item_id,
                    COUNT(*) as fail_count
                FROM manual_check_results mcr
                INNER JOIN manual_check_items mci 
                    ON mcr.check_item_code = CONCAT(
                        CASE 
                            WHEN mci.item_code = 'seal_check' THEN 'seal_check'
                            WHEN mci.item_code = 'malware_scan' THEN 'malware_scan'
                            WHEN mci.item_code = 'file_encryption' THEN 'file_encryption'
                            ELSE mci.item_code
                        END
                    )
                WHERE mcr.user_id = %s 
                AND mcr.check_year = %s
                AND mcr.overall_result = 'fail'
                AND mcr.exclude_from_scoring = 0
                GROUP BY mci.item_id
            """
            
            manual_results = execute_query(manual_query, (user_id, year), fetch_all=True)
            
            # 모든 항목을 False로 초기화
            for item in manual_check_items:
                result['manual'][item['item_id']] = False
            
            # 결함이 있는 항목만 True로 설정
            for row in manual_results:
                if row['fail_count'] > 0:
                    result['manual'][row['item_id']] = True
        
        return result
        
    except Exception as e:
        logging.error(f"Get user item status error: {str(e)}")
        return {'audit': {}, 'manual': {}}