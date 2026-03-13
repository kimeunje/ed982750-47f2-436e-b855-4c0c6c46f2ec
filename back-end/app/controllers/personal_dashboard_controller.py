# app/controllers/personal_dashboard_controller.py - 수정된 버전
"""
개인 보안 점수 현황판 컨트롤러
수시감사와 모의훈련 점수 계산 로직 개선
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
from app.utils.decorators import token_required, handle_exceptions
from app.utils.constants import HTTP_STATUS
from app.utils.database import DatabaseManager, execute_query
import logging

# 블루프린트 생성 (URL 접두사 포함)
personal_dashboard_bp = Blueprint("personal_dashboard", __name__,
                                  url_prefix="/api/personal-dashboard")


@personal_dashboard_bp.route("/summary", methods=["GET"])
@token_required
@handle_exceptions
def get_personal_dashboard_summary():
    """개인 보안 점수 현황 조회 - 4개 테이블 통합"""
    user = request.current_user
    username = user["username"]
    year = request.args.get("year", datetime.now().year, type=int)

    try:
        logging.info(f"개인 현황판 조회: username={username}, year={year}")

        # 사용자 ID 조회 (username으로 uid 찾기)
        user_data = execute_query("SELECT uid FROM users WHERE user_id = %s",
                                  (username, ), fetch_one=True)

        if not user_data:
            return (
                jsonify({"error": "사용자 정보를 찾을 수 없습니다."}),
                HTTP_STATUS["NOT_FOUND"],
            )

        user_id = user_data["uid"]

        # 1. 기본 사용자 정보
        user_info = _get_user_info(user_id)
        if not user_info:
            return (
                jsonify({"error": "사용자 상세 정보를 찾을 수 없습니다."}),
                HTTP_STATUS["NOT_FOUND"],
            )

        # 2. 상시감사 감점 및 통계 (모든 로그 반영)
        audit_penalty, audit_stats = _calculate_audit_penalty_all_logs(user_id, year)

        # 3. 수시감사 감점 및 통계 (수정된 로직)
        manual_penalty, manual_stats = _calculate_manual_check_penalty_fixed(
            user_id, year)

        # 4. 교육 감점 및 통계
        education_penalty, education_stats = _calculate_education_penalty(user_id, year)

        # 5. 모의훈련 감점 및 통계 (수정된 로직)
        training_penalty, training_stats = _calculate_training_penalty_fixed(
            user_id, year)

        # 6. 총 감점 계산
        total_penalty = (audit_penalty + manual_penalty + education_penalty +
                         training_penalty)
        total_penalty = min(5.0, total_penalty)  # 최대 5점 감점

        # 7. 감점 요약 저장/업데이트
        _save_score_summary(
            user_id,
            year,
            audit_penalty,
            manual_penalty,
            education_penalty,
            training_penalty,
            total_penalty,
        )

        response_data = {
            "user_info": user_info,
            "year": year,
            "audit_penalty": float(audit_penalty),
            "manual_check_penalty": float(manual_penalty),
            "education_penalty": float(education_penalty),
            "training_penalty": float(training_penalty),
            "total_penalty": float(total_penalty),
            "audit_stats": audit_stats,
            "manual_check_stats": manual_stats,
            "education_stats": education_stats,
            "training_stats": training_stats,
            "last_updated": datetime.now().isoformat(),
        }

        logging.info(f"개인 현황판 응답: total_penalty={total_penalty}")
        return jsonify(response_data)

    except Exception as e:
        logging.error(f"Personal dashboard error: {str(e)}")
        return (
            jsonify({
                "error": "개인 현황 조회 중 오류가 발생했습니다.",
                "details": str(e)
            }),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


def _get_user_info(user_id):
    """기본 사용자 정보 조회"""
    try:
        return execute_query(
            """
            SELECT uid, user_id, username, department
            FROM users 
            WHERE uid = %s
        """,
            (user_id, ),
            fetch_one=True,
        )
    except Exception as e:
        logging.error(f"User info error: {str(e)}")
        return None


# 기존 방식 유지 (미흡 건수별로 적용)
# def _calculate_audit_penalty_all_logs(user_id, year):
#     """상시감사 감점 계산 - 제외 설정 반영 (수정됨)"""
#     try:
#         # 2025년 모든 상시감사 로그 조회 + 제외 설정 확인
#         audit_logs = execute_query(
#             """
#             SELECT
#                 al.log_id,
#                 al.item_id,
#                 al.passed,
#                 al.checked_at,
#                 ci.item_name,
#                 ci.penalty_weight,
#                 CASE
#                     WHEN (
#                         EXISTS (
#                             SELECT 1 FROM user_item_exceptions uie
#                             WHERE uie.user_id = al.user_id
#                             AND uie.item_id = al.item_id
#                             AND uie.is_active = 1
#                             AND (uie.exclude_type = 'permanent' OR
#                                 (uie.exclude_type = 'temporary' AND CURDATE() BETWEEN uie.start_date AND uie.end_date))
#                         )
#                         OR EXISTS (
#                             SELECT 1 FROM department_item_exceptions die
#                             JOIN users u ON u.department = die.department
#                             WHERE u.uid = al.user_id
#                             AND die.item_id = CAST(al.item_id AS CHAR)
#                             AND die.item_type = 'audit_item'
#                             AND die.is_active = 1
#                             AND (die.exclude_type = 'permanent' OR
#                                 (die.exclude_type = 'temporary' AND CURDATE() BETWEEN die.start_date AND die.end_date))
#                         )
#                     ) THEN 1
#                     ELSE 0
#                 END as is_excluded
#             FROM audit_log al
#             JOIN checklist_items ci ON al.item_id = ci.item_id
#             WHERE al.user_id = %s
#             AND YEAR(al.checked_at) = %s
#             AND ci.check_type = 'daily'
#             ORDER BY al.checked_at DESC
#         """,
#             (user_id, year),
#             fetch_all=True,
#         )

#         if not audit_logs:
#             return 0.0, {
#                 "total_count": 0,
#                 "passed_count": 0,
#                 "failed_count": 0,
#                 "pending_count": 0,
#                 "total_penalty": 0.0,
#                 "failed_items": [],
#             }

#         # 통계 계산 (제외 설정 반영)
#         total_count = len(audit_logs)
#         passed_count = sum(1 for log in audit_logs
#                            if log["passed"] == 1 and not log["is_excluded"])
#         failed_count = sum(1 for log in audit_logs
#                            if log["passed"] == 0 and not log["is_excluded"])
#         pending_count = sum(1 for log in audit_logs
#                             if log["passed"] is None and not log["is_excluded"])
#         excluded_count = sum(1 for log in audit_logs if log["is_excluded"])

#         # 감점 계산 - 제외되지 않은 실패 로그에 대해서만 감점
#         total_penalty = 0.0
#         failed_item_details = []

#         for log in audit_logs:
#             if log["passed"] == 0 and not log["is_excluded"]:  # 실패했고 제외되지 않은 경우
#                 penalty = float(log["penalty_weight"]) if log["penalty_weight"] else 0.5
#                 total_penalty += penalty
#                 failed_item_details.append({
#                     "item_name": log["item_name"],
#                     "checked_at": log["checked_at"],
#                     "penalty": penalty,
#                     "is_excluded": False,
#                 })

#         audit_stats = {
#             "total_count": total_count,
#             "passed_count": passed_count,
#             "failed_count": failed_count,  # 제외되지 않은 실패 건수만 포함
#             "pending_count": pending_count,
#             "excluded_count": excluded_count,  # 제외된 항목 수 추가
#             "total_penalty": round(total_penalty, 2),
#             "failed_items": failed_item_details,
#         }

#         return total_penalty, audit_stats

#     except Exception as e:
#         logging.error(f"Audit penalty calculation error: {str(e)}")
#         return 0.0, {
#             "total_count": 0,
#             "passed_count": 0,
#             "failed_count": 0,
#             "pending_count": 0,
#             "total_penalty": 0.0,
#             "failed_items": [],
#         }



def _calculate_audit_penalty_all_logs(user_id, year):
    """
    ✅ 최종 수정된 상시감사 감점 계산 로직 - items 배열 포함
    """
    try:
        logging.info(f"[AUDIT_ITEMS_DEBUG] 감사 항목 계산 시작: user_id={user_id}, year={year}")

        # 1. 정기점검 로그 조회
        audit_logs = execute_query(
            """
            SELECT 
                al.log_id,
                al.item_id,
                al.passed,
                al.checked_at,
                ci.item_name,
                ci.penalty_weight,
                CASE 
                    WHEN (
                        EXISTS (
                            SELECT 1 FROM user_item_exceptions uie 
                            WHERE uie.user_id = al.user_id 
                            AND uie.item_id = al.item_id 
                            AND uie.is_active = 1
                            AND (uie.exclude_type = 'permanent' OR 
                                (uie.exclude_type = 'temporary' AND CURDATE() BETWEEN uie.start_date AND uie.end_date))
                        )
                        OR EXISTS (
                            SELECT 1 FROM department_item_exceptions die
                            JOIN users u ON u.department = die.department
                            WHERE u.uid = al.user_id
                            AND die.item_id = CAST(al.item_id AS CHAR)
                            AND die.item_type = 'audit_item'
                            AND die.is_active = 1
                            AND (die.exclude_type = 'permanent' OR 
                                (die.exclude_type = 'temporary' AND CURDATE() BETWEEN die.start_date AND die.end_date))
                        )
                    ) THEN 1
                    ELSE 0
                END as is_excluded
            FROM audit_log al
            JOIN checklist_items ci ON al.item_id = ci.item_id
            WHERE al.user_id = %s 
            AND YEAR(al.checked_at) = %s 
            AND ci.check_type = 'daily'
            ORDER BY al.checked_at DESC
        """,
            (user_id, year),
            fetch_all=True,
        )

        logging.info(f"[AUDIT_ITEMS_DEBUG] 조회된 로그 수: {len(audit_logs) if audit_logs else 0}개")

        if not audit_logs:
            logging.warning(f"[AUDIT_ITEMS_DEBUG] 로그가 없음 - 빈 응답 반환")
            return 0.0, {
                "total_count": 0,
                "passed_count": 0,
                "failed_count": 0,
                "pending_count": 0,
                "excluded_count": 0,
                "total_penalty": 0.0,
                "failed_items": [],
                "items": [],
            }

        # 2. 통계 계산
        total_count = len(audit_logs)
        passed_count = sum(1 for log in audit_logs
                           if log["passed"] == 1 and not log["is_excluded"])
        pending_count = sum(1 for log in audit_logs
                            if log["passed"] is None and not log["is_excluded"])
        excluded_count = sum(1 for log in audit_logs if log["is_excluded"])

        logging.info(f"[AUDIT_ITEMS_DEBUG] 통계 - 전체:{total_count}, 통과:{passed_count}, 대기:{pending_count}, 제외:{excluded_count}")

        # 3. 감점 계산 - 항목별로 1건만
        total_penalty = 0.0
        failed_item_details = []
        processed_items = set()

        for log in audit_logs:
            if log["passed"] == 0 and not log["is_excluded"]:
                item_id = log["item_id"]
                if item_id not in processed_items:
                    penalty = float(log["penalty_weight"]) if log["penalty_weight"] else 0.5
                    total_penalty += penalty
                    processed_items.add(item_id)
                    failed_item_details.append({
                        "item_id": item_id,
                        "item_name": log["item_name"],
                        "checked_at": log["checked_at"],
                        "penalty": penalty,
                        "is_excluded": False,
                        "calculation_method": "per_item"
                    })

        failed_count = len(processed_items)
        logging.info(f"[AUDIT_ITEMS_DEBUG] 실패 항목: {failed_count}개, 총 감점: {total_penalty}점")

        # 4. ✅ items 배열 생성 - item_id별로 실패가 있으면 fail, 없으면 최신 상태
        items_dict = {}
        for log in audit_logs:
            if log["is_excluded"]:
                continue  # 제외된 로그는 처음부터 제외
                
            item_id = log["item_id"]
            
            if item_id not in items_dict:
                # 첫 번째 로그 저장
                items_dict[item_id] = log
            else:
                # 이미 저장된 로그가 있는 경우
                existing_log = items_dict[item_id]
                
                # 실패한 로그가 있으면 실패를 우선 표시
                if log["passed"] == 0:
                    items_dict[item_id] = log
                # 기존이 실패가 아니고, 새 로그가 더 최신이면 업데이트
                elif existing_log["passed"] != 0 and log["checked_at"] > existing_log["checked_at"]:
                    items_dict[item_id] = log

        logging.info(f"[AUDIT_ITEMS_DEBUG] 고유 항목 수: {len(items_dict)}개")

        # items 배열 생성
        all_items = []
        for item_id, log in items_dict.items():
            # passed 값을 확인하여 result 결정
            if log["passed"] == 1:
                result_status = "pass"
            elif log["passed"] == 0:
                result_status = "fail"
            else:
                result_status = "pending"
            
            all_items.append({
                "item_id": item_id,
                "item_name": log["item_name"],
                "result": result_status,
                "checked_at": log["checked_at"],
                "penalty_weight": float(log["penalty_weight"]) if log["penalty_weight"] else 0.5,
                # 디버깅용 필드
                "passed_raw": log["passed"],  # 실제 DB 값
            })
            
            logging.debug(f"[AUDIT_ITEMS_DEBUG] 항목 추가: id={item_id}, name={log['item_name']}, passed={log['passed']}, result={result_status}")

        # item_id 순서로 정렬
        all_items.sort(key=lambda x: x["item_id"])

        logging.info(f"[AUDIT_ITEMS_DEBUG] 최종 items 배열 크기: {len(all_items)}개")
        logging.info(f"[AUDIT_ITEMS_DEBUG] items 배열 내용 샘플 (처음 3개): {all_items[:3] if len(all_items) >= 3 else all_items}")

        # 5. audit_stats 구성
        audit_stats = {
            "total_count": len(all_items),  # ✅ 수정: 고유 항목 수 (items 배열 길이)
            "passed_count": passed_count,
            "failed_count": failed_count,
            "pending_count": pending_count,
            "excluded_count": excluded_count,
            "total_penalty": round(total_penalty, 2),
            "failed_items": failed_item_details,  # 하위 호환성
            "items": all_items,  # ✅ 모든 항목 배열
            "calculation_method": "daily_per_item",
            "total_failure_logs": sum(
                1 for log in audit_logs
                if log["passed"] == 0 and not log["is_excluded"]),
            "total_logs": len(audit_logs),  # ✅ 추가: 전체 로그 수 (참고용)
        }

        logging.info(
            f"[AUDIT_ITEMS_DEBUG] audit_stats 반환 완료 - "
            f"고유 항목: {len(all_items)}개, "
            f"전체 로그: {len(audit_logs)}개, "
            f"items 배열: {len(all_items)}개, "
            f"failed_items: {len(failed_item_details)}개"
        )
        
        return total_penalty, audit_stats

    except Exception as e:
        logging.error(f"[AUDIT_ITEMS_DEBUG] 오류 발생: {str(e)}")
        import traceback
        logging.error(f"[AUDIT_ITEMS_DEBUG] 스택 트레이스:\n{traceback.format_exc()}")
        return 0.0, {
            "total_count": 0,
            "passed_count": 0,
            "failed_count": 0,
            "pending_count": 0,
            "excluded_count": 0,
            "total_penalty": 0.0,
            "failed_items": [],
            "items": [],
        }


def _calculate_manual_check_penalty_fixed(user_id, year):
    """수시감사 감점 계산 - 수정된 로직 (overall_result='fail'이면 무조건 0.5점 감점)"""
    try:
        manual_checks = execute_query(
            """
            SELECT 
                check_id,
                check_item_code,
                overall_result,
                penalty_points,
                exclude_from_scoring,
                check_date,
                check_period
            FROM manual_check_results
            WHERE user_id = %s AND check_year = %s
            ORDER BY check_date DESC
        """,
            (user_id, year),
            fetch_all=True,
        )

        if not manual_checks:
            return 0.0, {
                "total_count": 0,
                "passed_count": 0,
                "failed_count": 0,
                "total_penalty": 0.0,
                "items": [],
            }

        # 통계 계산
        total_count = len(manual_checks)
        passed_count = sum(1 for check in manual_checks
                           if check["overall_result"] == "pass")
        failed_count = sum(
            1 for check in manual_checks
            if check["overall_result"] == "fail" and not check["exclude_from_scoring"])

        # 감점 계산 - 수정된 로직: overall_result가 'fail'이고 제외되지 않은 경우 무조건 0.5점 감점
        total_penalty = 0.0
        check_details = []

        check_type_names = {
            "seal_check": "봉인씰 점검",
            "malware_scan": "악성코드 검사",
            "file_encryption": "파일 암호화 점검",
        }

        for check in manual_checks:
            penalty = 0.0
            if not check["exclude_from_scoring"] and check["overall_result"] == "fail":
                penalty = 0.5  # penalty_points 필드와 관계없이 고정 0.5점 감점
                total_penalty += penalty

            check_details.append({
                "check_type": check_type_names.get(check["check_item_code"],
                                                   check["check_item_code"]),
                "result": check["overall_result"],
                "penalty": penalty,
                "check_date": check["check_date"],
                "excluded": bool(check["exclude_from_scoring"]),
            })

        manual_stats = {
            "total_count": total_count,
            "passed_count": passed_count,
            "failed_count": failed_count,
            "total_penalty": round(total_penalty, 2),
            "items": check_details,
        }

        return total_penalty, manual_stats

    except Exception as e:
        logging.error(f"Manual check penalty calculation error: {str(e)}")
        return 0.0, {
            "total_count": 0,
            "passed_count": 0,
            "failed_count": 0,
            "total_penalty": 0.0,
            "items": [],
        }


def _calculate_training_penalty_fixed(user_id, year):
    """모의훈련 감점 계산 - 실제 DB 스키마 사용"""
    try:
        print(f"[DEBUG] 모의훈련 감점 계산: user_id={user_id}, year={year}")

        training_records = execute_query(
            """
            SELECT 
                pt.training_id,
                pt.training_result, 
                pt.exclude_from_scoring,
                ptp.period_name,
                ptp.training_type
            FROM phishing_training pt
            LEFT JOIN phishing_training_periods ptp ON pt.period_id = ptp.period_id
            WHERE pt.user_id = %s AND pt.training_year = %s
            """,
            (user_id, year),
            fetch_all=True,
        )

        print(f"[DEBUG] 조회된 모의훈련 기록: {len(training_records)}개")

        # 모의훈련 데이터가 없는 경우 감점 없음
        if not training_records:
            training_stats = {
                "total_count": 0,
                "passed_count": 0,
                "failed_count": 0,
                "pending_count": 0,
                "total_penalty": 0.0,
                "items": [],
                "message": "모의훈련 데이터가 없어 감점하지 않음",
            }
            print(f"[DEBUG] 모의훈련 데이터 없음 - 감점 없음")
            return 0.0, training_stats

        # 점수 계산에 포함되는 기록만 필터링
        scoring_records = [
            r for r in training_records if not r.get("exclude_from_scoring", False)
        ]
        print(f"[DEBUG] 점수 계산 대상: {len(scoring_records)}개")

        # 실제 훈련 기록이 있는 경우만 감점 계산
        total_count = len(scoring_records)
        passed_count = 0
        failed_count = 0
        total_penalty = 0.0
        training_details = []

        for record in scoring_records:
            penalty = 0.0
            if record["training_result"] == "fail":
                failed_count += 1
                penalty = 0.5
                total_penalty += penalty
            elif record["training_result"] == "success":
                passed_count += 1

            training_details.append({
                "period": record.get("period_name", "알 수 없는 기간"),
                "training_type": record.get("training_type", ""),
                "result": record["training_result"],
                "penalty": penalty,
            })

        pending_count = total_count - passed_count - failed_count

        training_stats = {
            "total_count": total_count,
            "passed_count": passed_count,
            "failed_count": failed_count,
            "pending_count": pending_count,
            "total_penalty": round(total_penalty, 2),
            "items": training_details,
        }

        print(f"[DEBUG] 최종 모의훈련 통계: {training_stats}")
        return total_penalty, training_stats

    except Exception as e:
        logging.error(f"Training penalty calculation error: {str(e)}")
        print(f"[DEBUG] 모의훈련 계산 오류: {str(e)}")
        # 에러 발생시에도 감점 없음
        return 0.0, {
            "total_count": 0,
            "passed_count": 0,
            "failed_count": 0,
            "pending_count": 0,
            "total_penalty": 0.0,
            "items": [],
            "message": "모의훈련 데이터 조회 오류로 감점하지 않음",
        }


def _calculate_education_penalty(user_id, year):
    """
    ✅ 수정된 교육 감점 계산 - incomplete_count > 0 기반

    기존: SUM(incomplete_count) × 0.5
    신규: COUNT(incomplete_count > 0) × 0.5
    """
    try:
        logging.info(
            f"교육 감점 계산 시작 (incomplete_count > 0 기준): user_id={user_id}, year={year}")

        # ✅ 핵심 수정: incomplete_count > 0 기반 쿼리
        penalty_query = """
            SELECT 
                COUNT(CASE WHEN se.incomplete_count > 0 THEN 1 END) as periods_with_incomplete,
                SUM(se.completed_count) as total_completed,
                SUM(se.incomplete_count) as total_incomplete,
                COUNT(*) as total_records,
                SUM(se.total_courses) as total_courses,
                AVG(se.completion_rate) as avg_completion_rate,
                COUNT(DISTINCT se.course_name) as unique_courses
            FROM security_education se
            LEFT JOIN security_education_periods sep ON se.period_id = sep.period_id
            WHERE se.user_id = %s 
              AND se.education_year = %s
              AND se.exclude_from_scoring = 0
        """

        result = execute_query(penalty_query, (user_id, year), fetch_one=True)

        if not result or result["periods_with_incomplete"] is None:
            logging.info("교육 데이터가 없어 감점하지 않음")
            return 0.0, {
                "periods_with_incomplete": 0,
                "completed_count": 0,
                "incomplete_count": 0,
                "total_courses": 0,
                "avg_completion_rate": 0.0,
                "total_penalty": 0.0,
                "message": "교육 데이터가 없어 감점하지 않음",
            }

        # ✅ 새로운 감점 계산
        periods_with_incomplete = (int(result["periods_with_incomplete"])
                                   if result["periods_with_incomplete"] else 0)
        total_completed = (int(result["total_completed"])
                           if result["total_completed"] else 0)
        total_incomplete = (int(result["total_incomplete"])
                            if result["total_incomplete"] else 0)
        total_records = int(result["total_records"]) if result["total_records"] else 0
        total_courses = int(result["total_courses"]) if result["total_courses"] else 0
        avg_completion_rate = (float(result["avg_completion_rate"])
                               if result["avg_completion_rate"] else 0.0)
        unique_courses = (int(result["unique_courses"])
                          if result["unique_courses"] else 0)

        # ✅ 감점 계산: incomplete_count > 0인 기간 수 × 0.5점
        education_penalty = float(periods_with_incomplete) * 0.5

        logging.info(
            f"교육 감점 계산 완료: 미완료 기간 {periods_with_incomplete}개, 감점 {education_penalty}점")

        # 통계 정보
        education_stats = {
            "periods_with_incomplete": periods_with_incomplete,  # 새로운 필드
            "completed_count": total_completed,
            "incomplete_count": total_incomplete,
            "total_records": total_records,
            "total_courses": total_courses,
            "avg_completion_rate": round(avg_completion_rate, 2),
            "unique_courses": unique_courses,
            "total_penalty": round(education_penalty, 2),
            # 기존 호환성 필드
            "total_educations": total_records,
            "passed_educations": total_records - periods_with_incomplete,
            "failed_educations": periods_with_incomplete,
        }

        return education_penalty, education_stats

    except Exception as e:
        logging.error(f"교육 감점 계산 오류: {str(e)}")
        return _calculate_education_penalty_legacy(user_id, year)


def _calculate_education_penalty_legacy(user_id, year):
    """
    ✅ 기존 로직 백업 - 새로운 스키마가 없는 경우 사용
    """
    try:
        logging.warning(f"교육 감점 계산 - 레거시 모드 실행: user_id={user_id}, year={year}")

        # 기존 completion_status 기반 계산
        legacy_query = """
            SELECT COUNT(*) as incomplete_count
            FROM security_education se
            WHERE se.user_id = %s 
              AND se.education_year = %s
              AND se.completion_status = 0
              AND se.exclude_from_scoring = 0
        """

        result = execute_query(legacy_query, (user_id, year), fetch_one=True)
        incomplete_count = result["incomplete_count"] if result else 0

        education_penalty = float(incomplete_count) * 0.5

        # 레거시 통계
        education_stats = {
            "total_records": incomplete_count,
            "completed_count": 0,
            "incomplete_count": incomplete_count,
            "total_courses": incomplete_count,
            "avg_completion_rate": 0.0,
            "unique_courses": incomplete_count,
            "total_educations": incomplete_count,
            "passed_educations": 0,
            "failed_educations": incomplete_count,
        }

        logging.info(f"레거시 교육 감점: {education_penalty}점")
        return education_penalty, education_stats

    except Exception as e:
        logging.error(f"레거시 교육 감점 계산 오류: {str(e)}")
        return 0.0, {
            "total_records": 0,
            "completed_count": 0,
            "incomplete_count": 0,
            "total_courses": 0,
            "avg_completion_rate": 0.0,
            "unique_courses": 0,
            "total_educations": 0,
            "passed_educations": 0,
            "failed_educations": 0,
        }


def _save_score_summary(
    user_id,
    year,
    audit_penalty,
    manual_penalty,
    education_penalty,
    training_penalty,
    total_penalty,
):
    """점수 요약 저장/업데이트"""
    try:
        # 기존 요약 확인
        existing = execute_query(
            """
            SELECT summary_id FROM security_score_summary 
            WHERE user_id = %s AND evaluation_year = %s
        """,
            (user_id, year),
            fetch_one=True,
        )

        if existing:
            # 업데이트
            execute_query(
                """
                UPDATE security_score_summary 
                SET audit_penalty = %s, education_penalty = %s, training_penalty = %s, 
                    total_penalty = %s, last_calculated = NOW()
                WHERE user_id = %s AND evaluation_year = %s
            """,
                (
                    audit_penalty,
                    education_penalty,
                    training_penalty,
                    total_penalty,
                    user_id,
                    year,
                ),
            )
        else:
            # 새로 생성
            execute_query(
                """
                INSERT INTO security_score_summary 
                (user_id, evaluation_year, audit_penalty, education_penalty, training_penalty, total_penalty)
                VALUES (%s, %s, %s, %s, %s, %s)
            """,
                (
                    user_id,
                    year,
                    audit_penalty,
                    education_penalty,
                    training_penalty,
                    total_penalty,
                ),
            )
    except Exception as e:
        logging.error(f"Score summary save error: {str(e)}")


@personal_dashboard_bp.route("/recommendations", methods=["GET"])
@token_required
@handle_exceptions
def get_personal_recommendations():
    """개인 보안 개선 권장사항 조회"""
    user = request.current_user
    username = user["username"]
    year = request.args.get("year", datetime.now().year, type=int)

    try:
        logging.info(f"개인 권장사항 조회: username={username}, year={year}")

        # 사용자 ID 조회
        user_data = execute_query("SELECT uid FROM users WHERE user_id = %s",
                                  (username, ), fetch_one=True)

        if not user_data:
            return (
                jsonify({"error": "사용자 정보를 찾을 수 없습니다."}),
                HTTP_STATUS["NOT_FOUND"],
            )

        user_id = user_data["uid"]

        # 현재 감점 정보 조회
        score_summary = execute_query(
            """
            SELECT audit_penalty, education_penalty, training_penalty, total_penalty
            FROM security_score_summary 
            WHERE user_id = %s AND evaluation_year = %s
        """,
            (user_id, year),
            fetch_one=True,
        )

        if not score_summary:
            return jsonify({"recommendations": [], "message": "점수 데이터가 없습니다."})

        recommendations = []

        # 교육 관련 권장사항 - 임시로 비활성화
        # if score_summary["education_penalty"] > 0:
        #     recommendations.append({
        #         "priority": "high",
        #         "category": "education",
        #         "title": "📚 정보보호 교육 이수",
        #         "description": f"미이수된 교육으로 인해 -{score_summary['education_penalty']}점 감점되었습니다. 교육을 완료하여 감점을 해소하세요.",
        #         "penalty_score": float(score_summary["education_penalty"]),
        #         "action_url": "/security-education"
        #     })

        # 모의훈련 관련 권장사항
        if score_summary["training_penalty"] > 0:
            recommendations.append({
                "priority": "high",
                "category": "training",
                "title": "🎯 악성메일 대응 능력 향상",
                "description": f"모의훈련 실패로 인해 -{score_summary['training_penalty']}점 감점되었습니다. 악성메일 식별 능력을 향상시키세요.",
                "penalty_score": float(score_summary["training_penalty"]),
                "action_url": "/phishing-training",
            })

        # 상시감사 관련 권장사항
        if score_summary["audit_penalty"] > 0:
            recommendations.append({
                "priority": "medium",
                "category": "audit",
                "title": "🛡️ 보안 설정 개선",
                "description": f"상시감사 실패로 인해 -{score_summary['audit_penalty']}점 감점되었습니다. 보안 설정을 확인하고 조치하세요.",
                "penalty_score": float(score_summary["audit_penalty"]),
                "action_url": "/security-audit/results",
            })

        # 종합 권장사항
        if score_summary["total_penalty"] >= 2.0:
            recommendations.append({
                "priority": "info",
                "category": "general",
                "title": "💡 종합적인 보안 의식 개선",
                "description": f"현재 총 -{score_summary['total_penalty']}점 감점되었습니다. 정기적인 보안 교육 참여와 정책 준수를 권장합니다.",
                "penalty_score": 0,
                "action_url": "/security-audit/solutions",
            })

        response_data = {
            "current_penalty": float(score_summary["total_penalty"]),
            "potential_improvement": float(score_summary["education_penalty"] +
                                           score_summary["training_penalty"] +
                                           score_summary["audit_penalty"]),
            "recommendations": recommendations,
        }

        logging.info(f"개인 권장사항 응답: {len(recommendations)}개")
        return jsonify(response_data)

    except Exception as e:
        logging.error(f"Personal recommendations error: {str(e)}")
        return (
            jsonify({
                "error": "권장사항 조회 중 오류가 발생했습니다.",
                "details": str(e)
            }),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )
