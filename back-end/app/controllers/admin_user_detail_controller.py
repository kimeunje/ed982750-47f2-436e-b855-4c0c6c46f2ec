# app/controllers/admin_user_detail_controller.py
"""
관리자 사용자 상세 정보 API 컨트롤러
- 개별 사용자 상세 정보 조회
- 감점 내역 상세 분석
- 사용자별 트렌드 분석
- 개선 권고사항 생성
- 개별 사용자 보고서 내보내기
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from app.utils.decorators import token_required, handle_exceptions, admin_required
from app.utils.constants import HTTP_STATUS
from app.utils.database import execute_query
import logging
import csv
import io
from flask import make_response

# 블루프린트 생성 (기존 admin_personal_score_bp 확장)
admin_user_detail_bp = Blueprint("admin_user_detail", __name__,
                                 url_prefix="/api/admin/personal-scores")


@admin_user_detail_bp.route("/users/<int:user_id>/detail", methods=["GET"])
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
        score_detail = _calculate_user_detail_scores(user_id, year)

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


@admin_user_detail_bp.route("/users/<int:user_id>/trend", methods=["GET"])
@token_required
@admin_required
@handle_exceptions
def get_user_trend(user_id):
    """사용자 연도별 트렌드 조회"""
    years = request.args.get("years", 3, type=int)  # 기본 3년

    try:
        logging.info(f"사용자 트렌드 조회: user_id={user_id}, years={years}")

        # 사용자 존재 확인
        user_info = _get_user_info(user_id)
        if not user_info:
            return jsonify({"error": "사용자를 찾을 수 없습니다."}), HTTP_STATUS["NOT_FOUND"]

        # 연도별 트렌드 데이터 조회
        trend_data = _get_user_trend_data(user_id, years)

        response_data = {
            "user_info": user_info,
            "trend_data": trend_data,
            "analysis": _analyze_trend(trend_data),
            "last_updated": datetime.now().isoformat()
        }

        return jsonify(response_data)

    except Exception as e:
        logging.error(f"User trend error: {str(e)}")
        return jsonify({
            "error": "사용자 트렌드 조회 중 오류가 발생했습니다.",
            "details": str(e)
        }), HTTP_STATUS["INTERNAL_SERVER_ERROR"]


@admin_user_detail_bp.route("/users/<int:user_id>/recommendations", methods=["GET"])
@token_required
@admin_required
@handle_exceptions
def get_user_recommendations(user_id):
    """사용자별 개선 권고사항 조회"""
    year = request.args.get("year", datetime.now().year, type=int)

    try:
        logging.info(f"사용자 권고사항 조회: user_id={user_id}, year={year}")

        # 사용자 존재 확인
        user_info = _get_user_info(user_id)
        if not user_info:
            return jsonify({"error": "사용자를 찾을 수 없습니다."}), HTTP_STATUS["NOT_FOUND"]

        # 상세 점수 정보 조회
        score_detail = _calculate_user_detail_scores(user_id, year)

        # 권고사항 생성
        recommendations = _generate_recommendations(score_detail)

        response_data = {
            "user_info": user_info,
            "year": year,
            "recommendations": recommendations,
            "score_summary": {
                "total_penalty": score_detail.get("total_penalty", 0),
                "risk_level": _calculate_risk_level(score_detail.get(
                    "total_penalty", 0))
            },
            "last_updated": datetime.now().isoformat()
        }

        return jsonify(response_data)

    except Exception as e:
        logging.error(f"User recommendations error: {str(e)}")
        return jsonify({
            "error": "사용자 권고사항 조회 중 오류가 발생했습니다.",
            "details": str(e)
        }), HTTP_STATUS["INTERNAL_SERVER_ERROR"]


@admin_user_detail_bp.route("/users/<int:user_id>/export", methods=["GET"])
@token_required
@admin_required
@handle_exceptions
def export_user_detail(user_id):
    """개별 사용자 상세 보고서 내보내기"""
    year = request.args.get("year", datetime.now().year, type=int)
    format_type = request.args.get("format", "csv")
    include_recommendations = request.args.get("recommendations",
                                               "true").lower() == "true"

    try:
        logging.info(f"사용자 상세 보고서 내보내기: user_id={user_id}, year={year}")

        # 사용자 정보 및 상세 데이터 조회
        user_info = _get_user_info(user_id)
        if not user_info:
            return jsonify({"error": "사용자를 찾을 수 없습니다."}), HTTP_STATUS["NOT_FOUND"]

        score_detail = _calculate_user_detail_scores(user_id, year)

        if include_recommendations:
            recommendations = _generate_recommendations(score_detail)
        else:
            recommendations = []

        # 트렌드 데이터 (최근 3년)
        trend_data = _get_user_trend_data(user_id, 3)

        return _create_user_detail_report(user_info, score_detail, trend_data,
                                          recommendations, year, format_type)

    except Exception as e:
        logging.error(f"Export user detail error: {str(e)}")
        return jsonify({
            "error": "사용자 상세 보고서 내보내기 중 오류가 발생했습니다.",
            "details": str(e)
        }), HTTP_STATUS["INTERNAL_SERVER_ERROR"]


# === 헬퍼 함수들 ===


def _get_user_info(user_id):
    """사용자 기본 정보 조회"""
    try:
        user_query = """
            SELECT 
                uid, 
                name, 
                user_id as employee_id, 
                department, 
                position, 
                email,
                created_at,
                last_login
            FROM users 
            WHERE uid = %s AND is_active = 1
        """
        return execute_query(user_query, (user_id, ), fetch_one=True)
    except Exception as e:
        logging.error(f"User info query error: {str(e)}")
        return None


def _calculate_user_detail_scores(user_id, year):
    """
    ✅ 사용자 상세 점수 계산 - 교육 부분만 새로운 스키마 지원
    
    기존: personal_dashboard_controller의 함수 재사용
    수정: 새로운 교육 스키마 지원하면서 기존 호환성 유지
    """
    try:
        # 기존 감사 및 모의훈련 로직은 그대로 유지
        from app.controllers.personal_dashboard_controller import (
            _calculate_audit_penalty_all_logs, _calculate_training_penalty_fixed)

        # 상세 감점 계산
        audit_penalty, audit_stats = _calculate_audit_penalty_all_logs(user_id, year)
        training_penalty, training_stats = _calculate_training_penalty_fixed(
            user_id, year)

        # ✅ 핵심 수정: 교육 감점 계산 - 새로운 스키마 우선 지원
        education_penalty, education_stats = _calculate_education_penalty_enhanced(
            user_id, year)

        total_penalty = audit_penalty + education_penalty + training_penalty
        total_penalty = min(5.0, total_penalty)

        return {
            "total_penalty": float(total_penalty),
            "audit_penalty": float(audit_penalty),
            "education_penalty": float(education_penalty),
            "training_penalty": float(training_penalty),
            "audit_stats": audit_stats,
            "education_stats": education_stats,  # ✅ 새로운 통계 포함
            "training_stats": training_stats
        }

    except Exception as e:
        logging.error(f"User detail scores calculation error: {str(e)}")
        # 오류 발생 시 기존 방식으로 폴백
        from app.controllers.personal_dashboard_controller import _calculate_education_penalty
        education_penalty, education_stats = _calculate_education_penalty(user_id, year)

        return {
            "total_penalty": 0.0,
            "audit_penalty": 0.0,
            "education_penalty": float(education_penalty),
            "training_penalty": 0.0,
            "audit_stats": {},
            "education_stats": education_stats,
            "training_stats": {}
        }


def _calculate_education_penalty_enhanced(user_id, year):
    """
    ✅ 관리자 상세 페이지용 교육 감점 계산 - incomplete_count > 0 기반
    
    기존: SUM(incomplete_count) × 0.5
    신규: COUNT(incomplete_count > 0) × 0.5
    """
    try:
        logging.info(
            f"교육 감점 계산 (관리자 상세, incomplete_count > 0 기준): user_id={user_id}, year={year}"
        )

        education_records = execute_query(
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
                sep.end_date
            FROM security_education se
            LEFT JOIN security_education_periods sep ON se.period_id = sep.period_id
            WHERE se.user_id = %s AND se.education_year = %s
            ORDER BY se.course_name, se.created_at
        """, (user_id, year), fetch_all=True)

        if not education_records:
            return _calculate_education_penalty_legacy_admin(user_id, year)

        # ✅ incomplete_count > 0 기반 계산
        periods_with_incomplete = 0
        total_completed = 0
        total_incomplete = 0
        total_courses = 0
        excluded_count = 0
        incomplete_items = []
        course_summary = []

        for record in education_records:
            completed_count = int(record['completed_count'] or 0)
            incomplete_count = int(record['incomplete_count'] or 0)
            course_total = int(record['total_courses'] or 0)
            completion_rate = float(record['completion_rate'] or 0)
            is_excluded = bool(record['exclude_from_scoring'])

            total_completed += completed_count
            total_incomplete += incomplete_count
            total_courses += course_total

            if is_excluded:
                excluded_count += 1

            # ✅ 핵심 변경: incomplete_count가 0보다 크고 제외되지 않은 경우 감점
            if incomplete_count > 0 and not is_excluded:
                periods_with_incomplete += 1
                incomplete_items.append({
                    "education_name": record['course_name'],
                    "course_name": record['course_name'],
                    "period_name": record['period_name'],
                    "completion_rate": completion_rate,
                    "completed_count": completed_count,
                    "incomplete_count": incomplete_count,
                    "total_courses": course_total,
                    "penalty": 0.5,  # 기간당 0.5점 감점
                    "education_date": record['education_date'],
                    "exclude_from_scoring": is_excluded,
                    "exclude_reason": record['exclude_reason'],
                    "notes": record['notes']
                })

            # 과정별 요약
            course_summary.append({
                "course_name": record['course_name'],
                "completed": completed_count,
                "incomplete": incomplete_count,
                "total": course_total,
                "completion_rate": completion_rate,
                "status": "완료" if incomplete_count == 0 else "미완료"
            })

        # ✅ 감점 계산: incomplete_count > 0인 기간 수 × 0.5점
        education_penalty = float(periods_with_incomplete) * 0.5

        education_stats = {
            "total_count": len(education_records),
            "completed_count": total_completed,
            "incomplete_count": total_incomplete,
            "periods_with_incomplete": periods_with_incomplete,  # 새로운 필드
            "excluded_count": excluded_count,
            "total_penalty": round(education_penalty, 2),
            "total_educations": len(education_records),
            "passed_educations": len(education_records) - periods_with_incomplete,
            "failed_educations": periods_with_incomplete,
            "incomplete_items": incomplete_items,
            "course_summary": course_summary,
            "mode": "incomplete_count_based"
        }

        logging.info(
            f"교육 감점 계산 완료 (incomplete_count > 0 기준): 미완료 기간 {periods_with_incomplete}개, 감점 {education_penalty}점"
        )
        return education_penalty, education_stats

    except Exception as e:
        logging.error(f"Enhanced 교육 감점 계산 오류: {str(e)}")
        return _calculate_education_penalty_legacy_admin(user_id, year)


def _calculate_education_penalty_legacy_admin(user_id, year):
    """
    ✅ 레거시 교육 감점 계산 - 관리자 상세 페이지용
    """
    try:
        logging.warning(f"교육 감점 계산 - 레거시 모드 (관리자): user_id={user_id}, year={year}")

        # 기존 completion_status 기반 조회
        education_records = execute_query(
            """
            SELECT 
                se.education_type,
                se.completion_status,
                se.education_date,
                se.exclude_from_scoring,
                se.exclude_reason,
                se.notes,
                sep.period_name,
                sep.start_date,
                sep.end_date
            FROM security_education se
            LEFT JOIN security_education_periods sep ON se.period_id = sep.period_id
            WHERE se.user_id = %s AND se.education_year = %s
            ORDER BY se.education_type, se.created_at
        """, (user_id, year), fetch_all=True)

        if not education_records:
            # 데이터가 아예 없는 경우
            return 0.0, {
                "total_count": 0,
                "completed_count": 0,
                "incomplete_count": 0,
                "excluded_count": 0,
                "total_penalty": 0.0,
                "incomplete_items": [],
                "course_summary": [],
                "message": "교육 데이터가 없어 감점하지 않음"
            }

        # 레거시 스키마 기반 계산
        total_count = len(education_records)
        completed_count = len(
            [r for r in education_records if r['completion_status'] == 1])
        incomplete_records = [
            r for r in education_records if r['completion_status'] == 0
        ]
        incomplete_count = len(incomplete_records)
        excluded_count = len(
            [r for r in education_records if r['exclude_from_scoring']])

        # 감점 계산 (제외된 것 제외)
        scoring_incomplete = len(
            [r for r in incomplete_records if not r['exclude_from_scoring']])
        education_penalty = float(scoring_incomplete) * 0.5

        # 레거시 호환 통계
        education_stats = {
            "total_count": total_count,
            "completed_count": completed_count,
            "incomplete_count": incomplete_count,
            "excluded_count": excluded_count,
            "total_penalty": round(education_penalty, 2),
            "total_educations": total_count,
            "passed_educations": completed_count,
            "failed_educations": incomplete_count,

            # 레거시 상세 아이템
            "incomplete_items": [
                {
                    "education_name": record['education_type'],
                    "course_name": record['education_type'],
                    "incomplete_count": 1,  # 레거시에서는 항상 1
                    "penalty": 0.5 if not record['exclude_from_scoring'] else 0,
                    "period_name": record['period_name'],
                    "education_date": record['education_date'],
                    "exclude_from_scoring": bool(record['exclude_from_scoring']),
                    "exclude_reason": record['exclude_reason'],
                    "notes": record['notes']
                } for record in incomplete_records
            ],
            "course_summary": [{
                "course_name": record['education_type'],
                "completed": 1 if record['completion_status'] == 1 else 0,
                "incomplete": 1 if record['completion_status'] == 0 else 0,
                "total": 1,
                "completion_rate": 100.0 if record['completion_status'] == 1 else 0.0,
                "status": "완료" if record['completion_status'] == 1 else "미완료"
            } for record in education_records],
            "mode": "legacy"
        }

        logging.info(
            f"교육 감점 계산 완료 (레거시): 미이수 {incomplete_count}회, 감점 {education_penalty}점")
        return education_penalty, education_stats

    except Exception as e:
        logging.error(f"레거시 교육 감점 계산 오류 (관리자): {str(e)}")
        return 0.0, {
            "total_count": 0,
            "completed_count": 0,
            "incomplete_count": 0,
            "excluded_count": 0,
            "total_penalty": 0.0,
            "incomplete_items": [],
            "course_summary": [],
            "error": str(e)
        }


def _get_user_trend_data(user_id, years):
    """사용자 연도별 트렌드 데이터 조회"""
    try:
        current_year = datetime.now().year
        trend_data = {}

        for i in range(years):
            target_year = current_year - i

            trend_query = """
                SELECT 
                    evaluation_year,
                    total_penalty,
                    audit_penalty,
                    education_penalty,
                    training_penalty,
                    audit_failed_count,
                    education_incomplete_count,
                    training_failed_count,
                    last_calculated
                FROM security_score_summary
                WHERE user_id = %s AND evaluation_year = %s
            """

            result = execute_query(trend_query, (user_id, target_year), fetch_one=True)

            if result:
                trend_data[str(target_year)] = {
                    "year": target_year,
                    "total_penalty": float(result["total_penalty"] or 0),
                    "audit_penalty": float(result["audit_penalty"] or 0),
                    "education_penalty": float(result["education_penalty"] or 0),
                    "training_penalty": float(result["training_penalty"] or 0),
                    "audit_failed_count": result["audit_failed_count"] or 0,
                    "education_incomplete_count": result["education_incomplete_count"]
                    or 0,
                    "training_failed_count": result["training_failed_count"] or 0,
                    "last_calculated": result["last_calculated"].isoformat()
                    if result["last_calculated"] else None
                }

        return trend_data

    except Exception as e:
        logging.error(f"User trend data error: {str(e)}")
        return {}


def _analyze_trend(trend_data):
    """트렌드 분석"""
    try:
        if len(trend_data) < 2:
            return {
                "status": "insufficient_data",
                "message": "트렌드 분석을 위한 충분한 데이터가 없습니다."
            }

        # 최근 2년 비교
        years = sorted(trend_data.keys(), reverse=True)
        current_year = years[0]
        previous_year = years[1]

        current_penalty = trend_data[current_year]["total_penalty"]
        previous_penalty = trend_data[previous_year]["total_penalty"]

        change = current_penalty - previous_penalty

        if abs(change) < 0.1:
            trend_status = "stable"
            message = "보안 점수가 안정적으로 유지되고 있습니다."
        elif change > 0:
            trend_status = "deteriorating"
            message = f"전년 대비 {change:.2f}점 증가했습니다. 개선이 필요합니다."
        else:
            trend_status = "improving"
            message = f"전년 대비 {abs(change):.2f}점 감소했습니다. 좋은 개선을 보이고 있습니다."

        return {
            "status": trend_status,
            "change": change,
            "message": message,
            "current_penalty": current_penalty,
            "previous_penalty": previous_penalty
        }

    except Exception as e:
        logging.error(f"Trend analysis error: {str(e)}")
        return {"status": "error", "message": "트렌드 분석 중 오류가 발생했습니다."}


def _generate_recommendations(score_detail):
    """개선 권고사항 생성"""
    try:
        recommendations = []

        total_penalty = score_detail.get("total_penalty", 0)
        audit_penalty = score_detail.get("audit_penalty", 0)
        education_penalty = score_detail.get("education_penalty", 0)
        training_penalty = score_detail.get("training_penalty", 0)

        audit_stats = score_detail.get("audit_stats", {})
        education_stats = score_detail.get("education_stats", {})
        training_stats = score_detail.get("training_stats", {})

        # 상시감사 관련 권고사항
        if audit_penalty > 2.0:
            recommendations.append({
                "priority": "high",
                "category": "audit",
                "title": "상시감사 항목 긴급 개선 필요",
                "description": f"{audit_stats.get('failed_count', 0)}건의 보안 항목에서 실패했습니다. 보안 정책을 즉시 검토하고 개선하세요.",
                "action_items": [
                    "실패한 보안 항목 목록 확인", "보안 정책 재교육 수강", "시스템 보안 설정 점검", "정기적인 자가 점검 실시"
                ]
            })
        elif audit_penalty > 1.0:
            recommendations.append({
                "priority": "medium",
                "category": "audit",
                "title": "상시감사 주의 필요",
                "description": "일부 보안 항목에서 미흡한 부분이 있습니다. 정기적인 점검을 권장합니다.",
                "action_items": ["실패 항목 분석 및 개선", "보안 체크리스트 숙지", "월간 자가 점검 실시"]
            })
        elif audit_penalty > 0:
            recommendations.append({
                "priority": "low",
                "category": "audit",
                "title": "상시감사 소폭 개선",
                "description": "대체로 양호하나 일부 항목에서 주의가 필요합니다.",
                "action_items": ["미흡 항목 확인 및 개선", "보안 의식 유지"]
            })

        # 교육 관련 권고사항
        if education_penalty > 1.0:
            recommendations.append({
                "priority": "high",
                "category": "education",
                "title": "정보보호 교육 즉시 이수 필요",
                "description": f"{education_stats.get('incomplete_count', 0)}건의 필수 교육이 미완료되었습니다. 즉시 이수하세요.",
                "action_items": [
                    "미완료 교육 목록 확인", "교육 일정 계획 수립", "우선순위 교육부터 이수", "교육 완료 후 복습"
                ]
            })
        elif education_penalty > 0:
            recommendations.append({
                "priority": "medium",
                "category": "education",
                "title": "정보보호 교육 이수",
                "description": "일부 교육이 미완료되었습니다. 빠른 시일 내에 이수하세요.",
                "action_items": ["미완료 교육 이수", "정기 교육 일정 관리"]
            })

        # 모의훈련 관련 권고사항
        if training_penalty > 1.5:
            recommendations.append({
                "priority": "high",
                "category": "training",
                "title": "모의훈련 대응 능력 향상 긴급 필요",
                "description": f"{training_stats.get('failed_count', 0)}건의 모의훈련에서 실패했습니다. 보안 인식 개선이 필요합니다.",
                "action_items": [
                    "모의훈련 실패 원인 분석", "피싱 메일 식별 교육 수강", "보안 인식 개선 프로그램 참여", "실제 상황 대응 연습"
                ]
            })
        elif training_penalty > 0.5:
            recommendations.append({
                "priority": "medium",
                "category": "training",
                "title": "모의훈련 주의사항 숙지",
                "description": "모의훈련에서 일부 실패가 있었습니다. 보안 인식을 높이세요.",
                "action_items": ["피싱 메일 특징 학습", "의심스러운 메일 신고 절차 숙지", "보안 교육 자료 검토"]
            })

        # 종합 평가
        if total_penalty == 0:
            recommendations.append({
                "priority": "low",
                "category": "general",
                "title": "완벽한 보안 수준 유지",
                "description": "모든 보안 항목에서 우수한 성과를 보이고 있습니다. 현재 수준을 유지하세요.",
                "action_items": ["현재 보안 수준 유지", "정기적인 보안 교육 참여", "보안 모범 사례 공유"]
            })
        elif total_penalty <= 0.5:
            recommendations.append({
                "priority": "low",
                "category": "general",
                "title": "우수한 보안 수준 유지",
                "description": "전반적으로 우수한 보안 수준을 유지하고 있습니다. 지속적인 관리를 권장합니다.",
                "action_items": ["현재 수준 유지", "정기적인 자가 점검", "보안 인식 지속 관리"]
            })

        # 우선순위 정렬
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 3))

        return recommendations

    except Exception as e:
        logging.error(f"Generate recommendations error: {str(e)}")
        return []


def _calculate_risk_level(total_penalty):
    """위험도 계산"""
    if total_penalty > 3.0:
        return "critical"
    elif total_penalty > 2.0:
        return "high"
    elif total_penalty > 1.0:
        return "medium"
    elif total_penalty > 0:
        return "low"
    else:
        return "excellent"


def _create_user_detail_report(user_info, score_detail, trend_data, recommendations,
                               year, format_type):
    """사용자 상세 보고서 생성"""
    try:
        if format_type == "csv":
            output = io.StringIO()
            writer = csv.writer(output)

            # 보고서 헤더
            writer.writerow([f'{user_info["name"]} 상세 보안 보고서 ({year}년)'])
            writer.writerow([''])

            # 기본 정보
            writer.writerow(['=== 기본 정보 ==='])
            writer.writerow(['이름', user_info["name"]])
            writer.writerow(['사번', user_info["employee_id"]])
            writer.writerow(['부서', user_info["department"]])
            writer.writerow(['직급', user_info["position"]])
            writer.writerow(['이메일', user_info["email"]])
            writer.writerow([''])

            # 종합 점수
            writer.writerow(['=== 종합 보안 점수 ==='])
            writer.writerow(['구분', '감점'])
            writer.writerow(['총 감점', f"{score_detail['total_penalty']:.2f}"])
            writer.writerow(['상시감사 감점', f"{score_detail['audit_penalty']:.2f}"])
            writer.writerow(['교육 감점', f"{score_detail['education_penalty']:.2f}"])
            writer.writerow(['모의훈련 감점', f"{score_detail['training_penalty']:.2f}"])
            writer.writerow(
                ['위험도', _calculate_risk_level(score_detail['total_penalty'])])
            writer.writerow([''])

            # 상세 통계
            writer.writerow(['=== 상세 통계 ==='])
            audit_stats = score_detail.get('audit_stats', {})
            education_stats = score_detail.get('education_stats', {})
            training_stats = score_detail.get('training_stats', {})

            writer.writerow(['상시감사 실패 건수', audit_stats.get('failed_count', 0)])
            writer.writerow(['교육 미완료 건수', education_stats.get('incomplete_count', 0)])
            writer.writerow(['모의훈련 실패 건수', training_stats.get('failed_count', 0)])
            writer.writerow([''])

            # 트렌드 분석
            if trend_data:
                writer.writerow(['=== 연도별 트렌드 ==='])
                writer.writerow(['년도', '총 감점', '감사 감점', '교육 감점', '훈련 감점'])
                for year_key in sorted(trend_data.keys(), reverse=True):
                    trend = trend_data[year_key]
                    writer.writerow([
                        trend['year'], f"{trend['total_penalty']:.2f}",
                        f"{trend['audit_penalty']:.2f}",
                        f"{trend['education_penalty']:.2f}",
                        f"{trend['training_penalty']:.2f}"
                    ])
                writer.writerow([''])

            # 개선 권고사항
            if recommendations:
                writer.writerow(['=== 개선 권고사항 ==='])
                for i, rec in enumerate(recommendations, 1):
                    writer.writerow([f'{i}. {rec["title"]} (우선순위: {rec["priority"]})'])
                    writer.writerow(['', rec["description"]])
                    if rec.get("action_items"):
                        writer.writerow(['', '실행 항목:'])
                        for item in rec["action_items"]:
                            writer.writerow(['', f'- {item}'])
                    writer.writerow([''])

            csv_content = output.getvalue()
            output.close()

            # UTF-8 BOM 추가
            csv_content = '\ufeff' + csv_content

            response = make_response(csv_content.encode('utf-8'))
            response.headers["Content-Type"] = "text/csv; charset=utf-8"
            response.headers[
                "Content-Disposition"] = f"attachment; filename={user_info['name']}_detail_report_{year}.csv"
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

            return response

    except Exception as e:
        logging.error(f"Create user detail report error: {str(e)}")
        raise e
