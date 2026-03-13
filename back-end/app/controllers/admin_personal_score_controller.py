# app/controllers/admin_personal_score_controller.py
"""
관리자용 개인 보안 점수 관리 컨트롤러
- 전체 사용자 감점 현황 조회
- 사용자별 점수 상세 정보
- 통계 및 필터링 기능
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
from app.utils.decorators import token_required, handle_exceptions, admin_required
from app.utils.constants import HTTP_STATUS
from app.utils.database import DatabaseManager, execute_query
import logging

# 블루프린트 생성 (URL 접두사 포함)
admin_personal_score_bp = Blueprint("admin_personal_score", __name__, url_prefix="/api/admin/personal-scores")

@admin_personal_score_bp.route("/overview", methods=["GET"])
@token_required
@admin_required
@handle_exceptions
def get_admin_overview():
    """관리자용 전체 개인 보안 점수 현황 조회"""
    year = request.args.get("year", datetime.now().year, type=int)
    
    try:
        logging.info(f"관리자 개인 점수 현황 조회: year={year}")
        
        # 1. 전체 통계 계산
        overall_stats = _calculate_overall_statistics(year)
        
        # 2. 모든 사용자 점수 데이터 조회
        user_scores = _get_all_user_scores(year)
        
        response_data = {
            "year": year,
            "overall_stats": overall_stats,
            "user_scores": user_scores,
            "last_updated": datetime.now().isoformat()
        }
        
        logging.info(f"관리자 현황 응답: total_users={overall_stats['total_users']}")
        return jsonify(response_data)
            
    except Exception as e:
        logging.error(f"Admin overview error: {str(e)}")
        return jsonify({
            "error": "관리자 현황 조회 중 오류가 발생했습니다.",
            "details": str(e)
        }), HTTP_STATUS["INTERNAL_SERVER_ERROR"]


@admin_personal_score_bp.route("/users", methods=["GET"])
@token_required
@admin_required
@handle_exceptions
def get_filtered_users():
    """필터링된 사용자 목록 조회"""
    year = request.args.get("year", datetime.now().year, type=int)
    department = request.args.get("department", "all")
    position = request.args.get("position", "all")
    penalty_range = request.args.get("penalty_range", "all")
    search = request.args.get("search", "")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    
    try:
        logging.info(f"필터링된 사용자 조회: year={year}, dept={department}, position={position}")
        
        # 필터링된 사용자 데이터 조회
        filtered_users, total_count = _get_filtered_user_scores(
            year, department, position, penalty_range, search, page, per_page
        )
        
        response_data = {
            "year": year,
            "users": filtered_users,
            "pagination": {
                "current_page": page,
                "per_page": per_page,
                "total_count": total_count,
                "total_pages": (total_count + per_page - 1) // per_page
            },
            "filters": {
                "department": department,
                "position": position,
                "penalty_range": penalty_range,
                "search": search
            }
        }
        
        return jsonify(response_data)
            
    except Exception as e:
        logging.error(f"Filtered users error: {str(e)}")
        return jsonify({
            "error": "사용자 목록 조회 중 오류가 발생했습니다.",
            "details": str(e)
        }), HTTP_STATUS["INTERNAL_SERVER_ERROR"]


@admin_personal_score_bp.route("/users/<int:user_id>/detail", methods=["GET"])
@token_required
@admin_required
@handle_exceptions
def get_user_detail(user_id):
    """특정 사용자의 상세 점수 정보 조회"""
    year = request.args.get("year", datetime.now().year, type=int)
    
    try:
        logging.info(f"사용자 상세 조회: user_id={user_id}, year={year}")
        
        # 사용자 기본 정보 조회
        user_info = _get_user_info(user_id)
        if not user_info:
            return jsonify({"error": "사용자를 찾을 수 없습니다."}), HTTP_STATUS["NOT_FOUND"]
        
        # 상세 점수 계산
        user_detail = _calculate_user_detail_scores(user_id, year)
        
        response_data = {
            "user_info": user_info,
            "year": year,
            "score_detail": user_detail,
            "last_updated": datetime.now().isoformat()
        }
        
        return jsonify(response_data)
            
    except Exception as e:
        logging.error(f"User detail error: {str(e)}")
        return jsonify({
            "error": "사용자 상세 정보 조회 중 오류가 발생했습니다.",
            "details": str(e)
        }), HTTP_STATUS["INTERNAL_SERVER_ERROR"]


@admin_personal_score_bp.route("/statistics", methods=["GET"])
@token_required
@admin_required
@handle_exceptions
def get_statistics():
    """부서별, 직급별 감점 통계 조회"""
    year = request.args.get("year", datetime.now().year, type=int)
    
    try:
        logging.info(f"통계 조회: year={year}")
        
        # 부서별 통계
        department_stats = _get_department_statistics(year)
        
        # 직급별 통계
        position_stats = _get_position_statistics(year)
        
        # 감점 구간별 통계
        penalty_range_stats = _get_penalty_range_statistics(year)
        
        response_data = {
            "year": year,
            "department_stats": department_stats,
            "position_stats": position_stats,
            "penalty_range_stats": penalty_range_stats,
            "last_updated": datetime.now().isoformat()
        }
        
        return jsonify(response_data)
            
    except Exception as e:
        logging.error(f"Statistics error: {str(e)}")
        return jsonify({
            "error": "통계 조회 중 오류가 발생했습니다.",
            "details": str(e)
        }), HTTP_STATUS["INTERNAL_SERVER_ERROR"]


@admin_personal_score_bp.route("/export", methods=["POST"])
@token_required
@admin_required
@handle_exceptions
def export_user_scores():
    """사용자 점수 데이터 내보내기"""
    data = request.json or {}
    year = data.get("year", datetime.now().year)
    format_type = data.get("format", "csv")  # csv, excel
    filters = data.get("filters", {})
    
    try:
        logging.info(f"데이터 내보내기: year={year}, format={format_type}")
        
        # 내보낼 데이터 조회 (필터 적용)
        export_data = _get_export_data(year, filters)
        
        if format_type == "excel":
            # Excel 파일 생성 로직
            file_content = _create_excel_export(export_data, year)
            mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = f"personal_scores_{year}.xlsx"
        else:
            # CSV 파일 생성 로직
            file_content = _create_csv_export(export_data, year)
            mimetype = "text/csv"
            filename = f"personal_scores_{year}.csv"
        
        return jsonify({
            "message": "데이터 내보내기가 완료되었습니다.",
            "filename": filename,
            "format": format_type,
            "record_count": len(export_data)
        })
            
    except Exception as e:
        logging.error(f"Export error: {str(e)}")
        return jsonify({
            "error": "데이터 내보내기 중 오류가 발생했습니다.",
            "details": str(e)
        }), HTTP_STATUS["INTERNAL_SERVER_ERROR"]


# =============================================================================
# 헬퍼 함수들
# =============================================================================

def _calculate_overall_statistics(year):
    """전체 통계 계산"""
    try:
        # 전체 사용자 수 및 평균 감점 계산
        stats_query = """
            SELECT 
                COUNT(*) as total_users,
                COALESCE(AVG(total_penalty), 0) as average_penalty,
                COUNT(CASE WHEN total_penalty <= 0.5 THEN 1 END) as excellent_users,
                COUNT(CASE WHEN total_penalty > 0.5 AND total_penalty <= 2.0 THEN 1 END) as warning_users,
                COUNT(CASE WHEN total_penalty > 2.0 THEN 1 END) as critical_users
            FROM security_score_summary sss
            JOIN users u ON sss.user_id = u.uid
            WHERE sss.evaluation_year = %s AND u.is_active = 1
        """
        
        stats = execute_query(stats_query, (year,), fetch_one=True)
        
        if not stats or stats['total_users'] == 0:
            return {
                "total_users": 0,
                "average_penalty": 0.0,
                "excellent_users": 0,
                "warning_users": 0,
                "critical_users": 0
            }
        
        return {
            "total_users": int(stats['total_users']),
            "average_penalty": round(float(stats['average_penalty']), 2),
            "excellent_users": int(stats['excellent_users']),
            "warning_users": int(stats['warning_users']),
            "critical_users": int(stats['critical_users'])
        }
        
    except Exception as e:
        logging.error(f"Overall statistics calculation error: {str(e)}")
        return {
            "total_users": 0,
            "average_penalty": 0.0,
            "excellent_users": 0,
            "warning_users": 0,
            "critical_users": 0
        }


def _get_all_user_scores(year):
    """모든 사용자의 점수 데이터 조회"""
    try:
        user_scores_query = """
            SELECT 
                u.uid,
                u.name,
                u.user_id as employee_id,
                u.department,
                u.position,
                COALESCE(sss.total_penalty, 0) as total_penalty,
                COALESCE(sss.audit_penalty, 0) as audit_penalty,
                COALESCE(sss.education_penalty, 0) as education_penalty,
                COALESCE(sss.training_penalty, 0) as training_penalty,
                sss.last_calculated,
                CASE 
                    WHEN sss.total_penalty <= 0.5 THEN 'low'
                    WHEN sss.total_penalty <= 2.0 THEN 'medium'
                    ELSE 'high'
                END as risk_level
            FROM users u
            LEFT JOIN security_score_summary sss ON u.uid = sss.user_id AND sss.evaluation_year = %s
            WHERE u.is_active = 1
            ORDER BY sss.total_penalty DESC, u.name ASC
        """
        
        users = execute_query(user_scores_query, (year,))
        
        # 데이터 형변환 및 추가 정보
        for user in users:
            user['total_penalty'] = float(user['total_penalty'] or 0)
            user['audit_penalty'] = float(user['audit_penalty'] or 0)
            user['education_penalty'] = float(user['education_penalty'] or 0)
            user['training_penalty'] = float(user['training_penalty'] or 0)
            user['last_updated'] = user['last_calculated'].strftime('%Y-%m-%d') if user['last_calculated'] else None
            
            # 트렌드 계산 (임시로 랜덤 설정, 실제로는 이전 기간과 비교)
            user['trend'] = _calculate_user_trend(user['uid'], year)
        
        return users
        
    except Exception as e:
        logging.error(f"User scores query error: {str(e)}")
        return []


def _get_filtered_user_scores(year, department, position, penalty_range, search, page, per_page):
    """필터링된 사용자 점수 조회"""
    try:
        # WHERE 조건 구성
        where_conditions = ["u.is_active = 1"]
        params = [year]
        
        if department != "all":
            where_conditions.append("u.department = %s")
            params.append(department)
        
        if position != "all":
            where_conditions.append("u.position = %s")
            params.append(position)
        
        if penalty_range == "excellent":
            where_conditions.append("COALESCE(sss.total_penalty, 0) <= 0.5")
        elif penalty_range == "warning":
            where_conditions.append("COALESCE(sss.total_penalty, 0) > 0.5 AND COALESCE(sss.total_penalty, 0) <= 2.0")
        elif penalty_range == "critical":
            where_conditions.append("COALESCE(sss.total_penalty, 0) > 2.0")
        
        if search:
            where_conditions.append("(u.name LIKE %s OR u.user_id LIKE %s)")
            search_param = f"%{search}%"
            params.extend([search_param, search_param])
        
        where_clause = " AND ".join(where_conditions)
        
        # 총 개수 조회
        count_query = f"""
            SELECT COUNT(*) as total_count
            FROM users u
            LEFT JOIN security_score_summary sss ON u.uid = sss.user_id AND sss.evaluation_year = %s
            WHERE {where_clause}
        """
        
        total_count = execute_query(count_query, params, fetch_one=True)['total_count']
        
        # 페이징된 데이터 조회
        offset = (page - 1) * per_page
        
        data_query = f"""
            SELECT 
                u.uid,
                u.name,
                u.user_id as employee_id,
                u.department,
                u.position,
                COALESCE(sss.total_penalty, 0) as total_penalty,
                COALESCE(sss.audit_penalty, 0) as audit_penalty,
                COALESCE(sss.education_penalty, 0) as education_penalty,
                COALESCE(sss.training_penalty, 0) as training_penalty,
                sss.last_calculated,
                CASE 
                    WHEN sss.total_penalty <= 0.5 THEN 'low'
                    WHEN sss.total_penalty <= 2.0 THEN 'medium'
                    ELSE 'high'
                END as risk_level
            FROM users u
            LEFT JOIN security_score_summary sss ON u.uid = sss.user_id AND sss.evaluation_year = %s
            WHERE {where_clause}
            ORDER BY sss.total_penalty DESC, u.name ASC
            LIMIT %s OFFSET %s
        """
        
        params_with_pagination = params + [per_page, offset]
        users = execute_query(data_query, params_with_pagination)
        
        # 데이터 형변환
        for user in users:
            user['total_penalty'] = float(user['total_penalty'] or 0)
            user['audit_penalty'] = float(user['audit_penalty'] or 0)
            user['education_penalty'] = float(user['education_penalty'] or 0)
            user['training_penalty'] = float(user['training_penalty'] or 0)
            user['last_updated'] = user['last_calculated'].strftime('%Y-%m-%d') if user['last_calculated'] else None
            user['trend'] = _calculate_user_trend(user['uid'], year)
        
        return users, total_count
        
    except Exception as e:
        logging.error(f"Filtered users query error: {str(e)}")
        return [], 0


def _get_user_info(user_id):
    """사용자 기본 정보 조회"""
    try:
        user_query = """
            SELECT uid, name, user_id as employee_id, department, position, email
            FROM users 
            WHERE uid = %s AND is_active = 1
        """
        return execute_query(user_query, (user_id,), fetch_one=True)
    except Exception as e:
        logging.error(f"User info query error: {str(e)}")
        return None


def _calculate_user_detail_scores(user_id, year):
    """사용자 상세 점수 계산"""
    try:
        # 기존 personal_dashboard_controller의 로직 재사용
        from app.controllers.personal_dashboard_controller import (
            _calculate_audit_penalty_all_logs,
            _calculate_education_penalty,
            _calculate_training_penalty_fixed
        )
        
        # 상세 감점 계산
        audit_penalty, audit_stats = _calculate_audit_penalty_all_logs(user_id, year)
        education_penalty, education_stats = _calculate_education_penalty(user_id, year)
        training_penalty, training_stats = _calculate_training_penalty_fixed(user_id, year)
        
        total_penalty = audit_penalty + education_penalty + training_penalty
        total_penalty = min(5.0, total_penalty)
        
        return {
            "total_penalty": float(total_penalty),
            "audit_penalty": float(audit_penalty),
            "education_penalty": float(education_penalty),
            "training_penalty": float(training_penalty),
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


def _get_department_statistics(year):
    """부서별 통계 조회"""
    try:
        dept_query = """
            SELECT 
                u.department,
                COUNT(*) as user_count,
                COALESCE(AVG(sss.total_penalty), 0) as avg_penalty,
                COUNT(CASE WHEN sss.total_penalty <= 0.5 THEN 1 END) as excellent_count,
                COUNT(CASE WHEN sss.total_penalty > 0.5 AND sss.total_penalty <= 2.0 THEN 1 END) as warning_count,
                COUNT(CASE WHEN sss.total_penalty > 2.0 THEN 1 END) as critical_count
            FROM users u
            LEFT JOIN security_score_summary sss ON u.uid = sss.user_id AND sss.evaluation_year = %s
            WHERE u.is_active = 1
            GROUP BY u.department
            ORDER BY avg_penalty DESC
        """
        
        return execute_query(dept_query, (year,))
        
    except Exception as e:
        logging.error(f"Department statistics error: {str(e)}")
        return []


def _get_position_statistics(year):
    """직급별 통계 조회"""
    try:
        position_query = """
            SELECT 
                u.position,
                COUNT(*) as user_count,
                COALESCE(AVG(sss.total_penalty), 0) as avg_penalty,
                COUNT(CASE WHEN sss.total_penalty <= 0.5 THEN 1 END) as excellent_count,
                COUNT(CASE WHEN sss.total_penalty > 0.5 AND sss.total_penalty <= 2.0 THEN 1 END) as warning_count,
                COUNT(CASE WHEN sss.total_penalty > 2.0 THEN 1 END) as critical_count
            FROM users u
            LEFT JOIN security_score_summary sss ON u.uid = sss.user_id AND sss.evaluation_year = %s
            WHERE u.is_active = 1
            GROUP BY u.position
            ORDER BY avg_penalty DESC
        """
        
        return execute_query(position_query, (year,))
        
    except Exception as e:
        logging.error(f"Position statistics error: {str(e)}")
        return []


def _get_penalty_range_statistics(year):
    """감점 구간별 통계 조회"""
    try:
        range_query = """
            SELECT 
                CASE 
                    WHEN COALESCE(sss.total_penalty, 0) <= 0.5 THEN 'excellent'
                    WHEN COALESCE(sss.total_penalty, 0) <= 2.0 THEN 'warning'
                    ELSE 'critical'
                END as penalty_range,
                COUNT(*) as user_count,
                COALESCE(AVG(sss.total_penalty), 0) as avg_penalty
            FROM users u
            LEFT JOIN security_score_summary sss ON u.uid = sss.user_id AND sss.evaluation_year = %s
            WHERE u.is_active = 1
            GROUP BY penalty_range
            ORDER BY 
                CASE penalty_range 
                    WHEN 'excellent' THEN 1
                    WHEN 'warning' THEN 2
                    WHEN 'critical' THEN 3
                END
        """
        
        return execute_query(range_query, (year,))
        
    except Exception as e:
        logging.error(f"Penalty range statistics error: {str(e)}")
        return []


def _calculate_user_trend(user_id, year):
    """사용자 트렌드 계산 (간단 버전)"""
    try:
        # 이전 년도와 비교하여 트렌드 계산
        prev_year = year - 1
        
        current_penalty = execute_query("""
            SELECT total_penalty FROM security_score_summary 
            WHERE user_id = %s AND evaluation_year = %s
        """, (user_id, year), fetch_one=True)
        
        prev_penalty = execute_query("""
            SELECT total_penalty FROM security_score_summary 
            WHERE user_id = %s AND evaluation_year = %s
        """, (user_id, prev_year), fetch_one=True)
        
        if not current_penalty or not prev_penalty:
            return 'stable'
        
        current = float(current_penalty['total_penalty'])
        previous = float(prev_penalty['total_penalty'])
        
        if current < previous - 0.5:
            return 'up'  # 감점이 줄어들면 개선됨
        elif current > previous + 0.5:
            return 'down'  # 감점이 늘어나면 악화됨
        else:
            return 'stable'
            
    except Exception as e:
        logging.error(f"Trend calculation error: {str(e)}")
        return 'stable'


def _get_export_data(year, filters):
    """내보내기용 데이터 조회"""
    try:
        # 필터 조건 적용한 전체 데이터 조회
        export_query = """
            SELECT 
                u.name,
                u.user_id as employee_id,
                u.department,
                u.position,
                u.email,
                COALESCE(sss.total_penalty, 0) as total_penalty,
                COALESCE(sss.audit_penalty, 0) as audit_penalty,
                COALESCE(sss.education_penalty, 0) as education_penalty,
                COALESCE(sss.training_penalty, 0) as training_penalty,
                sss.last_calculated
            FROM users u
            LEFT JOIN security_score_summary sss ON u.uid = sss.user_id AND sss.evaluation_year = %s
            WHERE u.is_active = 1
            ORDER BY sss.total_penalty DESC, u.name ASC
        """
        
        return execute_query(export_query, (year,))
        
    except Exception as e:
        logging.error(f"Export data error: {str(e)}")
        return []


def _create_csv_export(data, year):
    """CSV 파일 생성"""
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 헤더 작성
    writer.writerow([
        '이름', '사번', '부서', '직급', '이메일',
        '총 감점', '감사 감점', '교육 감점', '훈련 감점', '최종 업데이트'
    ])
    
    # 데이터 작성
    for row in data:
        writer.writerow([
            row['name'],
            row['employee_id'],
            row['department'],
            row['position'],
            row['email'],
            row['total_penalty'],
            row['audit_penalty'],
            row['education_penalty'],
            row['training_penalty'],
            row['last_calculated'].strftime('%Y-%m-%d') if row['last_calculated'] else ''
        ])
    
    return output.getvalue()


def _create_excel_export(data, year):
    """Excel 파일 생성 (추후 구현)"""
    # openpyxl 라이브러리 사용하여 Excel 파일 생성
    # 현재는 CSV와 동일한 데이터 반환
    return _create_csv_export(data, year)