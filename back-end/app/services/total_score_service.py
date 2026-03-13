# app/services/total_score_service.py - DB 스키마에 맞게 수정

from datetime import datetime
from app.utils.database import execute_query, DatabaseManager
import logging


class ScoreService:
    """KPI 보안 감점 계산 관련 서비스 - 실제 DB 스키마에 맞춘 버전"""

    def get_user_security_score(self, username: str, year: int = None) -> dict:
        """사용자명으로 보안 감점 조회"""
        if year is None:
            year = datetime.now().year

        # 사용자 ID 가져오기
        user = execute_query(
            "SELECT uid FROM users WHERE user_id = %s", (username,), fetch_one=True
        )

        if not user:
            raise ValueError("사용자를 찾을 수 없습니다.")

        return self.calculate_security_score(user["uid"], year)

    def calculate_security_score(self, user_id: int, year: int = None) -> dict:
        """사용자의 KPI 보안 감점 계산 - 실제 DB 스키마 기반"""
        if year is None:
            year = datetime.now().year

        logging.info(f"점수 계산 시작: user_id={user_id}, year={year}")

        with DatabaseManager.get_db_cursor() as cursor:
            # 1. 상시감사 감점 계산 (audit_log + manual_check_results)
            audit_penalty, audit_stats = self._calculate_audit_penalty_from_real_data(
                cursor, user_id, year
            )
            logging.info(f"감사 감점 계산 완료: {audit_penalty}")

            # 2. 교육 감점 계산 (security_education 테이블)
            education_penalty, education_stats = (
                self._calculate_education_penalty_from_real_data(cursor, user_id, year)
            )
            logging.info(f"교육 감점 계산 완료: {education_penalty}")

            # 3. 모의훈련 감점 계산 (phishing_training 테이블)
            training_penalty, training_stats = (
                self._calculate_training_penalty_from_real_data(cursor, user_id, year)
            )
            logging.info(f"훈련 감점 계산 완료: {training_penalty}")

            # 4. 총 감점 계산 (최대 -5.0점)
            total_penalty = audit_penalty + education_penalty + training_penalty
            total_penalty = min(5.0, total_penalty)  # 최대 5점 감점

            # 5. 감점 요약 저장
            self._save_score_summary(
                cursor,
                user_id,
                year,
                audit_penalty,
                education_penalty,
                training_penalty,
                total_penalty,
                education_stats,
                training_stats,
                audit_stats,
            )
            logging.info(f"점수 저장 완료: total_penalty={total_penalty}")

            return {
                "user_id": user_id,
                "year": year,
                "audit_penalty": float(audit_penalty),
                "education_penalty": float(education_penalty),
                "training_penalty": float(training_penalty),
                "total_penalty": float(total_penalty),
                "education_stats": education_stats,
                "training_stats": training_stats,
                "audit_stats": audit_stats,
            }

    def _calculate_audit_penalty_from_real_data(
        self, cursor, user_id: int, year: int
    ) -> tuple:
        """실제 DB 스키마를 바탕으로 감사 감점 계산"""

        # 1. audit_log에서 상시감사 로그 조회 (daily 타입만)
        cursor.execute(
            """
            SELECT 
                al.log_id,
                al.item_id,
                al.passed,
                al.checked_at,
                ci.item_name,
                ci.penalty_weight
            FROM audit_log al
            INNER JOIN checklist_items ci ON al.item_id = ci.item_id
            WHERE al.user_id = %s 
            AND YEAR(al.checked_at) = %s 
            AND ci.check_type = 'daily'
            ORDER BY al.checked_at DESC
            """,
            (user_id, year),
        )

        audit_logs = cursor.fetchall()

        # 2. manual_check_results에서 수시감사 로그 조회
        cursor.execute(
            """
            SELECT 
                mcr.check_id,
                mcr.check_item_code,
                mcr.overall_result,
                mcr.check_date,
                mcr.exclude_from_scoring,
                0.5 as penalty_weight
            FROM manual_check_results mcr
            WHERE mcr.user_id = %s 
            AND mcr.check_year = %s
            ORDER BY mcr.check_date DESC
            """,
            (user_id, year),
        )

        manual_checks = cursor.fetchall()

        # 3. 감점 계산
        total_penalty = 0.0
        failed_items = []

        # audit_log 감점 계산
        audit_failed_count = 0
        for log in audit_logs:
            if log["passed"] == 0:  # 실패한 경우
                penalty = float(log["penalty_weight"]) if log["penalty_weight"] else 0.5
                total_penalty += penalty
                audit_failed_count += 1
                failed_items.append(
                    {
                        "item_name": log["item_name"],
                        "checked_at": log["checked_at"],
                        "penalty": penalty,
                        "source": "audit_log",
                    }
                )

        # manual_check_results 감점 계산
        manual_failed_count = 0
        for check in manual_checks:
            if check["overall_result"] == "fail" and check["exclude_from_scoring"] == 0:
                penalty = float(check["penalty_weight"])
                total_penalty += penalty
                manual_failed_count += 1
                failed_items.append(
                    {
                        "item_name": f"수시감사 - {check['check_item_code']}",
                        "checked_at": check["check_date"],
                        "penalty": penalty,
                        "source": "manual_check_results",
                    }
                )

        audit_stats = {
            "total_count": len(audit_logs) + len(manual_checks),
            "passed_count": len(audit_logs)
            - audit_failed_count
            + len([c for c in manual_checks if c["overall_result"] == "pass"]),
            "failed_count": audit_failed_count + manual_failed_count,
            "pending_count": len([log for log in audit_logs if log["passed"] is None]),
            "total_penalty": round(total_penalty, 2),
            "failed_items": failed_items,
            "audit_log_count": len(audit_logs),
            "manual_check_count": len(manual_checks),
        }

        return total_penalty, audit_stats

    def _calculate_education_penalty_from_real_data(
        self, cursor, user_id: int, year: int
    ) -> tuple:
        """
        ✅ 수정된 교육 감점 계산 - incomplete_count > 0 기반

        기존: SUM(incomplete_count) × 0.5
        신규: COUNT(incomplete_count > 0) × 0.5
        """
        try:
            logging.info(
                f"교육 감점 계산 (incomplete_count > 0 기준): user_id={user_id}, year={year}"
            )

            # ✅ 핵심 수정: incomplete_count > 0 기반 쿼리
            cursor.execute(
                """
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
            """,
                (user_id, year),
            )

            result = cursor.fetchone()

            if not result or result["periods_with_incomplete"] is None:
                # 새로운 스키마에 데이터가 없는 경우 레거시 모드 실행
                logging.warning(f"새로운 교육 스키마에 데이터 없음, 레거시 모드 실행")
                return self._calculate_education_penalty_legacy(cursor, user_id, year)

            # ✅ 새로운 감점 계산: incomplete_count > 0인 기간 수
            periods_with_incomplete = (
                int(result["periods_with_incomplete"])
                if result["periods_with_incomplete"]
                else 0
            )
            total_completed = (
                int(result["total_completed"]) if result["total_completed"] else 0
            )
            total_incomplete = (
                int(result["total_incomplete"]) if result["total_incomplete"] else 0
            )
            total_records = (
                int(result["total_records"]) if result["total_records"] else 0
            )
            total_courses = (
                int(result["total_courses"]) if result["total_courses"] else 0
            )
            avg_completion_rate = (
                float(result["avg_completion_rate"])
                if result["avg_completion_rate"]
                else 0.0
            )
            unique_courses = (
                int(result["unique_courses"]) if result["unique_courses"] else 0
            )

            # ✅ 감점 계산: incomplete_count > 0인 기간 수 × 0.5점
            education_penalty = float(periods_with_incomplete) * 0.5

            # 통계 정보
            education_stats = {
                "periods_with_incomplete": periods_with_incomplete,  # 새로운 필드
                "incomplete_count": total_incomplete,
                "completed_count": total_completed,
                "total_records": total_records,
                "total_courses": total_courses,
                "avg_completion_rate": round(avg_completion_rate, 2),
                "unique_courses": unique_courses,
                "total_penalty": round(education_penalty, 2),
                # 기존 호환성 필드
                "total_educations": total_records,
                "passed_educations": total_records - periods_with_incomplete,
                "failed_educations": periods_with_incomplete,
                "mode": "incomplete_count_based",
            }

            logging.info(
                f"교육 감점 계산 완료 (incomplete_count > 0 기준): 미완료 기간 {periods_with_incomplete}개, 감점 {education_penalty}점"
            )

            return education_penalty, education_stats

        except Exception as e:
            logging.error(f"교육 감점 계산 오류 (incomplete_count > 0 기준): {str(e)}")
            return self._calculate_education_penalty_legacy(cursor, user_id, year)

    def _calculate_education_penalty_legacy(
        self, cursor, user_id: int, year: int
    ) -> tuple:
        """
        ✅ 레거시 교육 감점 계산 - 기존 completion_status 기반
        """
        try:
            logging.warning(
                f"교육 감점 계산 - 레거시 모드 (ScoreService): user_id={user_id}, year={year}"
            )

            # 기존 completion_status 기반 계산
            cursor.execute(
                """
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(CASE WHEN completion_status = 1 THEN 1 END) as completed_count,
                    COUNT(CASE WHEN completion_status = 0 AND exclude_from_scoring = 0 THEN 1 END) as incomplete_count,
                    COUNT(CASE WHEN exclude_from_scoring = 1 THEN 1 END) as excluded_count
                FROM security_education
                WHERE user_id = %s AND education_year = %s
            """,
                (user_id, year),
            )

            result = cursor.fetchone()

            if not result:
                # 데이터가 아예 없는 경우
                education_stats = {
                    "incomplete_count": 0,
                    "completed_count": 0,
                    "total_records": 0,
                    "total_courses": 0,
                    "avg_completion_rate": 0.0,
                    "unique_courses": 0,
                    "total_penalty": 0.0,
                    "total_educations": 0,
                    "passed_educations": 0,
                    "failed_educations": 0,
                    "message": "교육 데이터가 없어 감점하지 않음",
                }
                return 0.0, education_stats

            # 레거시 스키마 기반 계산
            total_records = (
                int(result["total_records"]) if result["total_records"] else 0
            )
            completed_count = (
                int(result["completed_count"]) if result["completed_count"] else 0
            )
            incomplete_count = (
                int(result["incomplete_count"]) if result["incomplete_count"] else 0
            )
            excluded_count = (
                int(result["excluded_count"]) if result["excluded_count"] else 0
            )

            # 감점 계산
            education_penalty = float(incomplete_count) * 0.5

            # 레거시 통계
            education_stats = {
                "incomplete_count": incomplete_count,
                "completed_count": completed_count,
                "total_records": total_records,
                "total_courses": total_records,  # 레거시에서는 동일
                "avg_completion_rate": round(
                    (completed_count / total_records * 100) if total_records > 0 else 0,
                    2,
                ),
                "unique_courses": total_records,  # 레거시에서는 동일
                "excluded_count": excluded_count,
                "total_penalty": round(education_penalty, 2),
                "total_educations": total_records,
                "passed_educations": completed_count,
                "failed_educations": incomplete_count,
                "mode": "legacy",
            }

            logging.info(
                f"교육 감점 계산 완료 (레거시): 미이수 {incomplete_count}회, 감점 {education_penalty}점"
            )

            return education_penalty, education_stats

        except Exception as e:
            logging.error(f"레거시 교육 감점 계산 오류 (ScoreService): {str(e)}")
            # 최후의 수단: 빈 통계 반환
            education_stats = {
                "incomplete_count": 0,
                "completed_count": 0,
                "total_records": 0,
                "total_courses": 0,
                "avg_completion_rate": 0.0,
                "unique_courses": 0,
                "total_penalty": 0.0,
                "total_educations": 0,
                "passed_educations": 0,
                "failed_educations": 0,
                "error": str(e),
            }
            return 0.0, education_stats


    def _calculate_training_penalty_from_real_data(self, cursor, user_id: int,
                                                    year: int) -> tuple:
            """실제 DB 스키마를 바탕으로 모의훈련 감점 계산 - 정확한 스키마 사용"""

            print(f"[DEBUG] 모의훈련 감점 계산 시작: user_id={user_id}, year={year}")
            
            cursor.execute(
                """
                SELECT 
                    pt.training_id,
                    pt.period_id,
                    pt.training_result,
                    pt.exclude_from_scoring,
                    ptp.period_name,
                    ptp.training_type
                FROM phishing_training pt
                LEFT JOIN phishing_training_periods ptp ON pt.period_id = ptp.period_id
                WHERE pt.user_id = %s 
                AND pt.training_year = %s
                """,
                (user_id, year),
            )

            training_records = cursor.fetchall()
            print(f"[DEBUG] 조회된 훈련 기록 수: {len(training_records)}")
            for i, record in enumerate(training_records):
                print(f"[DEBUG] 기록 {i+1}: {record}")

            # 훈련 데이터가 없는 경우 → 감점 없음
            if not training_records:
                print(f"[DEBUG] 훈련 데이터 없음 - 감점 없음")
                training_stats = {
                    "total_required": 0,
                    "passed_count": 0,
                    "failed_count": 0,
                    "total_penalty": 0.0,
                    "failed_sessions": [],
                    "message": "모의훈련 데이터가 없어 감점하지 않음"
                }
                return 0.0, training_stats

            # 점수 계산에 포함되는 훈련만 필터링
            scoring_records = [r for r in training_records if not r["exclude_from_scoring"]]
            print(f"[DEBUG] 점수 계산 대상 기록: {len(scoring_records)}개")
            
            # 실제 훈련 기록이 있는 경우만 감점 계산
            passed_count = sum(1 for record in scoring_records
                            if record["training_result"] == "success")
            failed_count = sum(1 for record in scoring_records
                            if record["training_result"] == "fail")
            no_response_count = sum(1 for record in scoring_records
                                if record["training_result"] == "no_response")

            print(f"[DEBUG] 결과 분석: 성공={passed_count}, 실패={failed_count}, 무응답={no_response_count}")

            # 실패한 훈련에 대해서만 감점 (0.5점씩)
            training_penalty = failed_count * 0.5
            print(f"[DEBUG] 계산된 감점: {training_penalty}점 (실패 {failed_count}회 × 0.5점)")

            # 실패한 세션 정보 수집
            failed_sessions = []
            for record in scoring_records:
                if record["training_result"] == "fail":
                    period_name = record.get("period_name", "알 수 없는 기간")
                    failed_sessions.append(f"{year}년 {period_name}")

            training_stats = {
                "total_required": len(scoring_records),
                "passed_count": passed_count,
                "failed_count": failed_count,
                "no_response_count": no_response_count,
                "total_penalty": round(training_penalty, 2),
                "failed_sessions": failed_sessions,
            }

            print(f"[DEBUG] 최종 통계: {training_stats}")
            return training_penalty, training_stats

    def _save_score_summary(
        self,
        cursor,
        user_id: int,
        year: int,
        audit_penalty: float,
        education_penalty: float,
        training_penalty: float,
        total_penalty: float,
        education_stats: dict,
        training_stats: dict,
        audit_stats: dict,
    ):
        """KPI 감점 요약 저장"""
        cursor.execute(
            """
            INSERT INTO security_score_summary 
            (user_id, evaluation_year, audit_penalty, education_penalty, 
            training_penalty, total_penalty, audit_failed_count, education_incomplete_count,
            training_failed_count)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            audit_penalty = VALUES(audit_penalty),
            education_penalty = VALUES(education_penalty),
            training_penalty = VALUES(training_penalty),
            total_penalty = VALUES(total_penalty),
            audit_failed_count = VALUES(audit_failed_count),
            education_incomplete_count = VALUES(education_incomplete_count),
            training_failed_count = VALUES(training_failed_count),
            last_calculated = NOW()
            """,
            (
                user_id,
                year,
                audit_penalty,
                education_penalty,
                training_penalty,
                total_penalty,
                audit_stats["failed_count"],
                education_stats["incomplete_count"],
                training_stats["failed_count"],
            ),
        )

    def get_dashboard_overview(self, username: str, year: int = None) -> dict:
        """대시보드용 KPI 감점 정보 조회"""
        if year is None:
            year = datetime.now().year

        # 사용자 감점 정보 가져오기
        score_data = self.get_user_security_score(username, year)

        # 추가 대시보드 정보 생성
        dashboard_data = {
            "user_score": score_data,
            "risk_level": self._calculate_risk_level(score_data["total_penalty"]),
            "last_updated": datetime.now().isoformat(),
        }

        return dashboard_data

    def _calculate_risk_level(self, total_penalty: float) -> str:
        """위험도 계산"""
        if total_penalty >= 3.0:
            return "critical"
        elif total_penalty >= 2.0:
            return "high"
        elif total_penalty >= 1.0:
            return "medium"
        elif total_penalty > 0:
            return "low"
        else:
            return "excellent"
