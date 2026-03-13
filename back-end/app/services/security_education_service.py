# back-end/app/services/security_education_service.py
from datetime import datetime, date

from typing import Dict, List, Any, Optional

from app.utils.database import execute_query, DatabaseManager
import logging


class SecurityEducationService:
    """정보보호 교육 데이터 관리 서비스"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def get_education_status(self, user_id: str = None, year: int = None) -> dict:
        """교육 현황 조회 (개별 사용자 또는 전체)"""
        if year is None:
            year = datetime.now().year

        try:
            if user_id:
                # 개별 사용자 교육 현황
                return self._get_user_education_status(user_id, year)
            else:
                # 전체 교육 현황 (관리자용)
                return self._get_all_education_status(year)

        except Exception as e:
            logging.error(f"교육 현황 조회 실패: {str(e)}")
            raise ValueError(f"교육 현황 조회 실패: {str(e)}")

    def _get_user_education_status(self, user_id: str, year: int) -> dict:
        """개별 사용자 교육 현황"""
        # 사용자 정보 조회
        user = execute_query(
            "SELECT uid, username, department FROM users WHERE user_id = %s",
            (user_id, ),
            fetch_one=True,
        )

        if not user:
            raise ValueError("사용자를 찾을 수 없습니다.")

        user_uid = user["uid"]

        # 사용자의 교육 기록 조회
        education_records = execute_query(
            """
            SELECT 
                se.education_id,
                se.education_type,
                se.completion_status,
                se.education_date,
                se.notes,
                se.exclude_from_scoring,
                se.exclude_reason,
                sep.period_name,
                sep.start_date,
                sep.end_date,
                sep.is_completed as period_completed
            FROM security_education se
            JOIN security_education_periods sep ON se.period_id = sep.period_id
            WHERE se.user_id = %s AND sep.education_year = %s
            ORDER BY sep.start_date, se.education_type
            """,
            (user_uid, year),
            fetch_all=True,
        )

        # 교육 유형별 통계 계산
        education_summary = self._calculate_education_summary(education_records)

        return {
            "user_info": user,
            "year": year,
            "education_records": education_records,
            "summary": education_summary,
        }

    def _get_all_education_status(self, year: int) -> dict:
        """전체 교육 현황 (관리자용)"""
        # 전체 교육 통계
        total_stats = execute_query(
            """
                SELECT 
                    COUNT(DISTINCT se.user_id) as total_users,
                    COUNT(se.education_id) as total_records,
                    SUM(CASE WHEN se.completion_status = 1 THEN 1 ELSE 0 END) as completed_count,
                    SUM(CASE WHEN se.completion_status = 0 THEN 1 ELSE 0 END) as incomplete_count,
                    SUM(CASE WHEN se.exclude_from_scoring = 1 THEN 1 ELSE 0 END) as excluded_count
                FROM security_education se
                JOIN security_education_periods sep ON se.period_id = sep.period_id
                WHERE sep.education_year = %s
                """,
            (year, ),
            fetch_one=True,
        )

        # 교육 유형별 통계
        type_stats = execute_query(
            """
                SELECT 
                    se.education_type,
                    COUNT(se.education_id) as total_count,
                    SUM(CASE WHEN se.completion_status = 1 THEN 1 ELSE 0 END) as completed_count,
                    SUM(CASE WHEN se.completion_status = 0 THEN 1 ELSE 0 END) as incomplete_count,
                    COUNT(DISTINCT se.user_id) as user_count
                FROM security_education se
                JOIN security_education_periods sep ON se.period_id = sep.period_id
                WHERE sep.education_year = %s
                GROUP BY se.education_type
                ORDER BY se.education_type
                """,
            (year, ),
            fetch_all=True,
        )

        # 기간별 통계
        period_stats = execute_query(
            """
                SELECT 
                    sep.period_id,
                    sep.period_name,
                    sep.education_type,
                    sep.start_date,
                    sep.end_date,
                    sep.is_completed,
                    COUNT(se.education_id) as total_records,
                    SUM(CASE WHEN se.completion_status = 1 THEN 1 ELSE 0 END) as completed_count,
                    COUNT(DISTINCT se.user_id) as participated_users
                FROM security_education_periods sep
                LEFT JOIN security_education se ON sep.period_id = se.period_id
                WHERE sep.education_year = %s
                GROUP BY sep.period_id
                ORDER BY sep.start_date
                """,
            (year, ),
            fetch_all=True,
        )

        return {
            "year": year,
            "total_stats": total_stats,
            "type_stats": type_stats,
            "period_stats": period_stats,
        }

    def _calculate_education_summary(self, education_records: list) -> dict:
        """교육 기록을 바탕으로 요약 통계 계산"""
        total_courses = len(education_records)
        completed = sum(1 for record in education_records
                        if record["completion_status"] == 1)
        incomplete = sum(1 for record in education_records
                         if record["completion_status"] == 0)
        excluded = sum(1 for record in education_records
                       if record["exclude_from_scoring"] == 1)

        # 점수 계산용 미완료 수 (제외된 항목 제외)
        penalty_incomplete = sum(
            1 for record in education_records
            if record["completion_status"] == 0 and not record["exclude_from_scoring"])

        return {
            "total_courses": total_courses,
            "completed": completed,
            "incomplete": incomplete,
            "excluded": excluded,
            "penalty_incomplete": penalty_incomplete,
            "penalty_points": penalty_incomplete * 0.5,  # 미완료당 0.5점 감점
            "completion_rate": round(
                (completed / total_courses * 100) if total_courses > 0 else 0, 1),
        }

    def bulk_update_education(self, records: list, uploaded_by: str = "admin") -> dict:
        """교육 결과 일괄 업로드 - 개선된 사용자 검색"""
        try:
            success_count = 0
            error_count = 0
            update_count = 0
            errors = []
            processed_users = []  # 처리된 사용자 추적

            current_year = datetime.now().year

            with DatabaseManager.get_db_cursor() as cursor:
                for i, record in enumerate(records):
                    try:
                        # 필수 필드 검증
                        if not record.get("username"):
                            errors.append(f"행 {i+1}: 사용자명이 누락되었습니다.")
                            error_count += 1
                            continue

                        if not record.get("education_type"):
                            errors.append(f"행 {i+1}: 교육 유형이 누락되었습니다.")
                            error_count += 1
                            continue

                        # 개선된 사용자 검색 로직
                        user_uid = self._find_user_flexible(record)

                        if not user_uid:
                            errors.append(
                                f"행 {i+1}: 사용자를 찾을 수 없습니다 - 이름: {record.get('username')}, 부서: {record.get('department', '미지정')}"
                            )
                            error_count += 1
                            continue

                        # 교육 기간 찾기 또는 생성
                        period_id = self._get_or_create_education_period(
                            record.get("education_year", current_year),
                            record.get("education_type"),
                            uploaded_by,
                        )

                        if not period_id:
                            errors.append(f"행 {i+1}: 교육 기간을 생성할 수 없습니다.")
                            error_count += 1
                            continue

                        # 교육 기록 업서트 (INSERT OR UPDATE)
                        result = self._upsert_education_record(
                            user_uid, period_id, record, uploaded_by)

                        if result["success"]:
                            success_count += 1
                            if result["updated"]:
                                update_count += 1

                            processed_users.append({
                                "username": record.get("username"),
                                "department": record.get("department"),
                                "education_type": record.get("education_type"),
                                "action": ("updated"
                                           if result["updated"] else "created"),
                            })
                        else:
                            errors.append(f"행 {i+1}: {result['message']}")
                            error_count += 1

                    except Exception as e:
                        error_count += 1
                        errors.append(f"행 {i+1}: 처리 중 오류 - {str(e)}")
                        logging.error(f"교육 기록 처리 오류 (행 {i+1}): {str(e)}")

                return {
                    "success_count": success_count,
                    "error_count": error_count,
                    "update_count": update_count,
                    "total_count": len(records),
                    "errors": errors[:10],  # 최대 10개 오류만 반환
                    "processed_users": processed_users[:5],  # 처리된 사용자 샘플
                    "message": f"총 {len(records)}건 중 {success_count}건 성공 ({update_count}건 업데이트), {error_count}건 실패",
                }

        except Exception as e:
            logging.error(f"일괄 업로드 실패: {str(e)}")
            raise ValueError(f"일괄 업로드 실패: {str(e)}")

    def _find_user_flexible(self, record: dict) -> int:
        """유연한 사용자 검색 로직"""
        username = record.get("username", "").strip()
        department = record.get("department", "").strip()

        if not username:
            return None

        # 1. 정확한 이름 + 부서 매칭 (가장 우선)
        if department:
            user = execute_query(
                "SELECT uid FROM users WHERE username = %s AND department = %s LIMIT 1",
                (username, department),
                fetch_one=True,
            )
            if user:
                logging.info(f"정확 매칭으로 사용자 발견: {username} ({department})")
                return user["uid"]

        # 2. 정확한 이름만 매칭 (부서 무시)
        user = execute_query(
            "SELECT uid, department FROM users WHERE username = %s LIMIT 1",
            (username, ),
            fetch_one=True,
        )
        if user:
            logging.info(f"이름으로만 사용자 발견: {username} -> 실제 부서: {user['department']}")
            return user["uid"]

        # 3. 유사한 이름 검색 (LIKE 사용)
        user = execute_query(
            "SELECT uid, username, department FROM users WHERE username LIKE %s LIMIT 1",
            (f"%{username}%", ),
            fetch_one=True,
        )
        if user:
            logging.info(
                f"유사 이름으로 사용자 발견: {username} -> {user['username']} ({user['department']})"
            )
            return user["uid"]

        # 4. 이름에서 공백 제거 후 검색
        username_no_space = username.replace(" ", "")
        if username_no_space != username:
            user = execute_query(
                "SELECT uid, username FROM users WHERE REPLACE(username, ' ', '') = %s LIMIT 1",
                (username_no_space, ),
                fetch_one=True,
            )
            if user:
                logging.info(f"공백 제거 후 사용자 발견: {username} -> {user['username']}")
                return user["uid"]

        logging.warning(f"사용자를 찾을 수 없음: {username} ({department})")
        return None

    def _get_or_create_education_period(self, year: int, period_name: str,
                                        education_type: str, created_by: str) -> int:
        """교육 기간 찾기 또는 생성"""
        # 기존 기간 찾기
        period = execute_query(
            """
            SELECT period_id FROM security_education_periods 
            WHERE education_year = %s AND period_name = %s AND education_type = %s
            """,
            (year, period_name, education_type),
            fetch_one=True,
        )

        if period:
            return period["period_id"]

        # 새 기간 생성
        try:
            period_id = execute_query(
                """
                INSERT INTO security_education_periods 
                (education_year, period_name, education_type, start_date, end_date, created_by, description)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    year,
                    period_name,
                    education_type,
                    date(year, 1, 1),  # 기본 시작일
                    date(year, 12, 31),  # 기본 종료일
                    created_by,
                    f"일괄 업로드로 생성된 {year}년 {period_name} {education_type}",
                ),
                return_insert_id=True,
            )

            logging.info(
                f"새 교육 기간 생성: {year}년 {period_name} {education_type} (ID: {period_id})")
            return period_id

        except Exception as e:
            logging.error(f"교육 기간 생성 실패: {str(e)}")
            return None

    def get_new_csv_template(self) -> str:
        """
        ✅ 새로운 CSV 템플릿 생성
        형식: 이름,부서,수강과정,수료,미수료
        """
        template_content = """이름,부서,수강과정,수료,미수료
    홍길동,개발팀,온라인교육,2,0
    김철수,인사팀,오프라인교육,0,1
    이영희,마케팅팀,종합교육,1,1
    박민수,IT팀,신입교육,3,0"""

        return template_content

    def process_csv_bulk_upload(self, period_id: int, csv_records: list,
                                uploaded_by: str) -> dict:
        """
        ✅ 수정된 CSV 형식 처리 메서드 - DatabaseManager 사용법 수정
        """
        success_count = 0
        error_count = 0
        update_count = 0
        errors = []

        try:
            # ✅ 수정: 올바른 DatabaseManager 사용법
            with DatabaseManager.get_db_connection() as db:
                cursor = db.cursor()

                # 1. 교육 기간 정보 조회
                period_info = self._get_period_info(cursor, period_id)
                if not period_info:
                    return {"success": False, "error": "교육 기간을 찾을 수 없습니다."}

                print(f"[DEBUG] 교육 기간 정보: {period_info}")

                # 2. CSV 레코드별 처리
                for idx, record in enumerate(csv_records, 1):
                    try:
                        print(f"[DEBUG] 처리 중 - 행 {idx}: {record}")

                        # 필수 필드 검증
                        required_fields = ["이름", "부서", "수강과정", "수료", "미수료"]
                        missing_fields = [
                            field for field in required_fields if field not in record
                        ]

                        if missing_fields:
                            raise ValueError(f"필수 필드 누락: {', '.join(missing_fields)}")

                        # 사용자 검색
                        user_id = self._find_user_by_name_dept(
                            cursor, record["이름"], record["부서"])
                        if not user_id:
                            raise ValueError(
                                f"사용자를 찾을 수 없습니다: {record['이름']} ({record['부서']})")

                        print(f"[DEBUG] 사용자 발견: {record['이름']} -> user_id: {user_id}")

                        # 데이터 검증 및 변환
                        completed_count = int(record["수료"]) if record["수료"] else 0
                        incomplete_count = (int(record["미수료"]) if record["미수료"] else 0)

                        if completed_count < 0 or incomplete_count < 0:
                            raise ValueError("수료/미수료 횟수는 0 이상이어야 합니다")

                        if completed_count + incomplete_count == 0:
                            raise ValueError("수료 또는 미수료 횟수 중 하나는 0보다 커야 합니다")

                        print(
                            f"[DEBUG] 데이터 검증 완료: 수료={completed_count}, 미수료={incomplete_count}"
                        )

                        # ✅ 새로운 스키마에 맞는 UPSERT 실행
                        is_updated = self._upsert_education_record(
                            cursor=cursor,
                            user_id=user_id,
                            period_id=period_id,
                            course_name=record["수강과정"],
                            completed_count=completed_count,
                            incomplete_count=incomplete_count,
                            education_year=period_info["education_year"],
                            uploaded_by=uploaded_by,
                        )

                        if is_updated:
                            update_count += 1
                            print(f"[DEBUG] 업데이트 완료: {record['이름']}")
                        else:
                            success_count += 1
                            print(f"[DEBUG] 신규 생성 완료: {record['이름']}")

                    except Exception as e:
                        error_count += 1
                        error_msg = (
                            f"행 {idx} ({record.get('이름', 'Unknown')}): {str(e)}")
                        errors.append(error_msg)
                        print(f"[ERROR] CSV 처리 오류 - {error_msg}")

                # 3. 트랜잭션 커밋
                db.commit()
                print(f"[DEBUG] 트랜잭션 커밋 완료")

                return {
                    "success": True,
                    "message": f"처리 완료: 신규 {success_count}건, 업데이트 {update_count}건, 오류 {error_count}건",
                    "success_count": success_count,
                    "update_count": update_count,
                    "error_count": error_count,
                    "errors": errors,
                }

        except Exception as e:
            print(f"[ERROR] CSV 업로드 처리 실패: {str(e)}")
            import traceback

            traceback.print_exc()
            return {"success": False, "error": f"업로드 처리 실패: {str(e)}"}

    def _find_user_by_name_dept(self, cursor, username: str, department: str) -> int:
        """
        ✅ 사용자 검색 로직 - 기존 컨트롤러에서 가져온 로직 사용
        """
        print(f"[DB_DEBUG] 사용자 검색: {username} ({department})")

        # 1. 정확한 이름+부서 매칭
        cursor.execute(
            "SELECT uid FROM users WHERE username = %s AND department = %s LIMIT 1",
            (username, department),
        )
        result = cursor.fetchone()

        if result:
            print(
                f"[DB_DEBUG] 정확 매칭 발견: {username} ({department}) -> uid: {result['uid']}"
            )
            return result["uid"]

        # 2. 이름만으로 검색
        cursor.execute("SELECT uid, department FROM users WHERE username = %s LIMIT 1",
                       (username, ))
        result = cursor.fetchone()

        if result:
            print(
                f"[DB_DEBUG] 이름으로만 사용자 발견: {username} -> 실제 부서: {result['department']}")
            return result["uid"]

        # 3. 유사 이름 검색
        cursor.execute(
            "SELECT uid, username, department FROM users WHERE username LIKE %s LIMIT 1",
            (f"%{username}%", ),
        )
        result = cursor.fetchone()

        if result:
            print(
                f"[DB_DEBUG] 유사 이름으로 사용자 발견: {result['username']} ({result['department']})"
            )
            return result["uid"]

        print(f"[DB_DEBUG] 사용자를 찾을 수 없음: {username} ({department})")
        return None

    def _upsert_education_record(
        self,
        cursor,
        user_id: int,
        period_id: int,
        course_name: str,
        completed_count: int,
        incomplete_count: int,
        education_year: int,
        uploaded_by: str,
    ) -> bool:
        """교육 기록 UPSERT - period_name을 course_name으로 사용하도록 수정"""
        try:
            # 1. 기간 정보에서 period_name 조회
            cursor.execute(
                """
                SELECT period_name, education_type 
                FROM security_education_periods 
                WHERE period_id = %s
                """,
                (period_id, ),
            )

            period_info = cursor.fetchone()
            if not period_info:
                raise ValueError(f"교육 기간 정보를 찾을 수 없습니다: period_id={period_id}")

            # 과정명을 기간명으로 사용 (수정 부분)
            actual_course_name = period_info["period_name"]
            education_type = period_info["education_type"]

            print(f"[DB_DEBUG] 과정명 설정: {course_name} -> {actual_course_name}")

            # 2. 기존 레코드 확인
            cursor.execute(
                """
                SELECT education_id, completed_count, incomplete_count 
                FROM security_education 
                WHERE user_id = %s AND period_id = %s AND course_name = %s
                """,
                (user_id, period_id, actual_course_name),
            )

            existing_record = cursor.fetchone()

            if existing_record:
                # 업데이트
                cursor.execute(
                    """
                    UPDATE security_education 
                    SET completed_count = %s, incomplete_count = %s, notes = %s, updated_at = NOW()
                    WHERE user_id = %s AND period_id = %s AND course_name = %s
                    """,
                    (
                        completed_count,
                        incomplete_count,
                        f"CSV 업데이트 - {uploaded_by}",
                        user_id,
                        period_id,
                        actual_course_name,
                    ),
                )
                print(
                    f"[DB_DEBUG] 업데이트 실행: user_id={user_id}, course_name={actual_course_name}"
                )
                return True
            else:
                # 삽입 (course_name을 period_name으로 설정)
                cursor.execute(
                    """
                    INSERT INTO security_education (
                        user_id, period_id, course_name, completed_count, incomplete_count,
                        education_year, notes, education_type
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        user_id,
                        period_id,
                        actual_course_name,  # 기간명을 과정명으로 사용
                        completed_count,
                        incomplete_count,
                        education_year,
                        f"CSV 업로드 - {uploaded_by}",
                        education_type,
                    ),
                )
                print(
                    f"[DB_DEBUG] 신규 삽입 실행: user_id={user_id}, course_name={actual_course_name}"
                )
                return False

        except Exception as e:
            print(f"[ERROR] UPSERT 실행 오류: {str(e)}")
            raise e

    def _get_period_info(self, cursor, period_id: int) -> dict:
        """교육 기간 정보 조회"""
        cursor.execute(
            """
            SELECT period_id, education_year, period_name, education_type,
                start_date, end_date, is_completed
            FROM security_education_periods
            WHERE period_id = %s
        """,
            (period_id, ),
        )

        result = cursor.fetchone()

        return result

    def get_education_excel_template(self) -> str:
        """엑셀 업로드용 템플릿 생성"""
        template_data = [
            "이름,부서,수강과정,수료,미수료",
            "테스터,관리실,오프라인,2,0",
            "홍길동,개발팀,온라인,1,0",
            "김철수,운영팀,오프라인,0,1",
            "이영희,기획팀,온라인,3,1",
        ]
        return "\n".join(template_data)

    def toggle_education_exception(
        self,
        user_id: int,
        period_id: int,
        education_type: str,
        exclude: bool,
        exclude_reason: str = "",
    ) -> dict:
        """교육 예외 처리 토글 - user_id는 이제 숫자 uid"""
        try:
            # ✅ user_id가 이미 숫자 uid이므로 바로 사용
            user = execute_query(
                "SELECT uid, username FROM users WHERE uid = %s",
                (user_id, ),
                fetch_one=True,
            )

            if not user:
                return {"success": False, "message": "사용자를 찾을 수 없습니다."}

            user_uid = user["uid"]

            # 교육 레코드 업데이트
            result = execute_query(
                """
                UPDATE security_education 
                SET exclude_from_scoring = %s, 
                    exclude_reason = %s,
                    updated_at = NOW()
                WHERE user_id = %s AND period_id = %s AND education_type = %s
                """,
                (
                    1 if exclude else 0,
                    exclude_reason if exclude else "",
                    user_uid,
                    period_id,
                    education_type,
                ),
            )

            if result == 0:
                return {
                    "success": False,
                    "message": "해당 교육 기록을 찾을 수 없습니다.",
                }

            action = "제외" if exclude else "포함"
            return {
                "success": True,
                "message": f"{user['username']}의 교육이 점수 계산에서 {action}되었습니다.",
            }

        except Exception as e:
            return {"success": False, "message": f"예외 처리 실패: {str(e)}"}

    def delete_education_record(self, user_id: int, period_id: int,
                                education_type: str) -> dict:
        """교육 기록 삭제 - user_id는 이제 숫자 uid"""
        try:
            # ✅ user_id가 이미 숫자 uid이므로 바로 사용
            user = execute_query(
                "SELECT uid, username FROM users WHERE uid = %s",
                (user_id, ),
                fetch_one=True,
            )

            if not user:
                return {"success": False, "message": "사용자를 찾을 수 없습니다."}

            user_uid = user["uid"]

            # 교육 기록 삭제
            result = execute_query(
                """
                DELETE FROM security_education
                WHERE user_id = %s AND period_id = %s AND education_type = %s
                """,
                (user_uid, period_id, education_type),
            )

            if result == 0:
                return {
                    "success": False,
                    "message": "삭제할 교육 기록을 찾을 수 없습니다.",
                }

            return {
                "success": True,
                "message": f"{user['username']}의 교육 기록이 삭제되었습니다.",
            }

        except Exception as e:
            return {"success": False, "message": f"삭제 실패: {str(e)}"}

    def get_all_education_records(self, year: int = None, education_type: str = None,
                                  status: str = None) -> list:
        """모든 교육 기록 조회 (관리자용) - status 파라미터 추가"""
        if year is None:
            year = datetime.now().year

        print(
            f"[DB_DEBUG] 교육 기록 조회 - year: {year}, education_type: {education_type}, status: {status}"
        )

        query = """
            SELECT 
                se.education_id,
                u.user_id,
                u.username,
                u.department,
                se.education_type,
                se.completion_status,
                se.education_date,
                se.exclude_from_scoring,
                se.exclude_reason,
                se.notes,
                se.created_at,
                se.updated_at,
                sep.period_name,
                sep.start_date,
                sep.end_date,
                sep.is_completed as period_completed
            FROM security_education se
            JOIN users u ON se.user_id = u.uid
            JOIN security_education_periods sep ON se.period_id = sep.period_id
            WHERE sep.education_year = %s
        """

        params = [year]

        # education_type 필터
        if education_type:
            query += " AND se.education_type = %s"
            params.append(education_type)

        # status 필터 추가
        if status:
            if status == "completed":
                query += " AND se.completion_status = 1"
            elif status == "incomplete":
                query += " AND se.completion_status = 0"
            elif status == "excluded":
                query += " AND se.exclude_from_scoring = 1"

        query += " ORDER BY sep.start_date, u.username, se.education_type"

        print(f"[DB_DEBUG] 실행할 쿼리: {query}")
        print(f"[DB_DEBUG] 파라미터: {params}")

        result = execute_query(query, params, fetch_all=True)

        print(f"[DB_DEBUG] 조회된 기록 수: {len(result) if result else 0}")
        if result:
            for i, record in enumerate(result[:3]):  # 처음 3개만 로그 출력
                print(
                    f"[DB_DEBUG] 기록 {i+1}: {record['username']} - {record['education_type']} - {record['completion_status']} - {record['notes']}"
                )

        return result

    def get_period_info(self, period_id: int) -> dict:
        """특정 교육 기간 정보 조회"""
        try:
            period_info = execute_query(
                """
                SELECT 
                    period_id,
                    education_year,
                    period_name,
                    education_type,
                    start_date,
                    end_date,
                    is_completed,
                    completed_at,
                    completed_by,
                    description,
                    auto_pass_setting,
                FROM security_education_periods 
                WHERE period_id = %s
                """,
                (period_id, ),
                fetch_one=True,
            )

            return period_info
        except Exception as e:
            print(f"[ERROR] 교육 기간 정보 조회 실패: {str(e)}")
            return None

    def bulk_update_education_with_period(self, period_id: int, records: list,
                                          uploaded_by: str) -> dict:
        """특정 교육 기간에 대한 교육 결과 일괄 업로드"""
        try:
            print(
                f"[DEBUG] 교육 기간별 일괄 업로드 시작 - period_id: {period_id}, 레코드 수: {len(records)}"
            )

            # 1. 교육 기간 정보 검증
            period_info = self.get_period_info(period_id)
            if not period_info:
                raise ValueError(f"교육 기간 ID {period_id}를 찾을 수 없습니다.")

            if period_info["is_completed"]:
                raise ValueError(
                    f"완료된 교육 기간({period_info['period_name']})에는 업로드할 수 없습니다.")

            print(
                f"[DEBUG] 교육 기간 검증 완료: {period_info['period_name']} ({period_info['education_type']})"
            )

            success_count = 0
            update_count = 0
            error_count = 0
            errors = []

            with DatabaseManager.get_db_cursor() as cursor:
                for idx, record in enumerate(records):
                    try:
                        print(
                            f"[DEBUG] 처리 중 ({idx+1}/{len(records)}): {record.get('username', 'Unknown')}"
                        )

                        # 2. 사용자 정보 확인
                        username = record.get("username", "").strip()
                        if not username:
                            error_msg = f"행 {idx+1}: 사용자명이 없습니다."
                            errors.append(error_msg)
                            error_count += 1
                            continue

                        # 사용자 UID 조회
                        cursor.execute("SELECT uid FROM users WHERE username = %s",
                                       (username, ))
                        user_result = cursor.fetchone()

                        if not user_result:
                            error_msg = (f"행 {idx+1}: 사용자 '{username}'를 찾을 수 없습니다.")
                            errors.append(error_msg)
                            error_count += 1
                            continue

                        user_uid = user_result["uid"]

                        # 3. 교육 유형 검증 (기간의 교육 유형과 일치해야 함)
                        record_education_type = record.get("education_type", "").strip()
                        if (record_education_type and record_education_type
                                != period_info["education_type"]):
                            print(
                                f"[WARNING] 교육 유형 불일치 - 기간: {period_info['education_type']}, 레코드: {record_education_type}"
                            )
                            # 경고만 출력하고 기간의 교육 유형으로 통일

                        # 4. 기존 레코드 삭제 (동일 사용자 + 기간)
                        cursor.execute(
                            """
                            DELETE FROM security_education 
                            WHERE user_id = %s AND period_id = %s
                            """,
                            (user_uid, period_id),
                        )
                        deleted_count = cursor.rowcount

                        # 5. 새 레코드들 생성
                        completed_count = int(record.get("completed_count", 0))
                        incomplete_count = int(record.get("incomplete_count", 0))

                        print(
                            f"[DEBUG] {username}: 기존 {deleted_count}개 삭제, 수료 {completed_count}개, 미수료 {incomplete_count}개 생성"
                        )

                        records_created = 0

                        # 수료 레코드 생성
                        for i in range(completed_count):
                            cursor.execute(
                                """
                                INSERT INTO security_education 
                                (user_id, period_id, education_type, education_year, 
                                completion_status, notes, created_at)
                                VALUES (%s, %s, %s, %s, 1, %s, NOW())
                                """,
                                (
                                    user_uid,
                                    period_id,
                                    period_info["education_type"],
                                    period_info["education_year"],
                                    self._get_education_period_from_date(
                                        period_info["start_date"]),
                                    f"일괄 업로드 - 수료 {i+1}회차 (업로더: {uploaded_by})",
                                ),
                            )
                            records_created += 1

                        # 미수료 레코드 생성
                        for i in range(incomplete_count):
                            cursor.execute(
                                """
                                INSERT INTO security_education 
                                (user_id, period_id, education_type, education_year, 
                                completion_status, notes, created_at)
                                VALUES (%s, %s, %s, %s, 0, %s, NOW())
                                """,
                                (
                                    user_uid,
                                    period_id,
                                    period_info["education_type"],
                                    period_info["education_year"],
                                    self._get_education_period_from_date(
                                        period_info["start_date"]),
                                    f"일괄 업로드 - 미수료 {i+1}회차 (업로더: {uploaded_by})",
                                ),
                            )
                            records_created += 1

                        if deleted_count > 0:
                            update_count += 1
                        else:
                            success_count += 1

                        print(f"[DEBUG] {username} 처리 완료: {records_created}개 레코드 생성")

                    except Exception as e:
                        error_msg = f"행 {idx+1} ({record.get('username', 'Unknown')}): {str(e)}"
                        errors.append(error_msg)
                        error_count += 1
                        print(f"[ERROR] 개별 레코드 처리 실패 - {error_msg}")
                        import traceback

                        traceback.print_exc()

                # 6. 트랜잭션 커밋
                cursor.connection.commit()

            print(
                f"[DEBUG] 일괄 업로드 완료 - 성공: {success_count}, 업데이트: {update_count}, 오류: {error_count}"
            )

            # 7. 결과 메시지 생성
            total_processed = success_count + update_count
            if total_processed > 0:
                if update_count > 0:
                    message = f"{period_info['period_name']}에 {total_processed}건 처리 완료 (신규: {success_count}건, 업데이트: {update_count}건)"
                else:
                    message = f"{period_info['period_name']}에 {success_count}건 신규 업로드 완료"
            else:
                message = "처리된 레코드가 없습니다."

            if error_count > 0:
                message += f" ({error_count}건 오류)"

            return {
                "success": True,
                "message": message,
                "success_count": success_count,
                "update_count": update_count,
                "error_count": error_count,
                "errors": errors[:10],  # 최대 10개 오류만 반환
                "period_name": period_info["period_name"],
                "education_type": period_info["education_type"],
            }

        except Exception as e:
            print(f"[ERROR] 교육 기간별 일괄 업로드 실패: {str(e)}")
            import traceback

            traceback.print_exc()

            return {
                "success": False,
                "message": f"업로드 실패: {str(e)}",
                "success_count": 0,
                "update_count": 0,
                "error_count": len(records),
                "errors": [str(e)],
            }

    def _get_education_period_from_date(self, date_obj) -> str:
        """날짜로부터 교육 기간(상반기/하반기) 결정"""
        try:
            if isinstance(date_obj, str):
                date_obj = datetime.strptime(date_obj, "%Y-%m-%d").date()
            elif isinstance(date_obj, datetime):
                date_obj = date_obj.date()

            # 6월까지는 상반기, 7월부터는 하반기
            if date_obj.month <= 6:
                return "first_half"
            else:
                return "second_half"
        except Exception as e:
            print(f"[WARNING] 교육 기간 결정 실패: {str(e)}, 기본값 'first_half' 사용")
            return "first_half"

    def _find_user_by_name_and_department(self, cursor, username: str,
                                          department: str) -> int:
        """사용자명과 부서로 사용자 찾기"""
        print(f"[DB_DEBUG] 사용자 조회: {username} ({department})")

        # 1. 정확 매칭 (이름 + 부서)
        cursor.execute(
            "SELECT uid FROM users WHERE username = %s AND department = %s LIMIT 1",
            (username, department),
        )
        result = cursor.fetchone()

        if result:
            print(f"[DB_DEBUG] 정확 매칭으로 사용자 발견: {username} ({department})")
            return result["uid"]

        # 2. 이름만으로 검색
        cursor.execute("SELECT uid, department FROM users WHERE username = %s LIMIT 1",
                       (username, ))
        result = cursor.fetchone()

        if result:
            print(
                f"[DB_DEBUG] 이름으로만 사용자 발견: {username} -> 실제 부서: {result['department']}")
            return result["uid"]

        # 3. 유사 이름 검색
        cursor.execute(
            "SELECT uid, username, department FROM users WHERE username LIKE %s LIMIT 1",
            (f"%{username}%", ),
        )
        result = cursor.fetchone()

        if result:
            print(
                f"[DB_DEBUG] 유사 이름으로 사용자 발견: {result['username']} ({result['department']})"
            )
            return result["uid"]

        print(f"[DB_DEBUG] 사용자를 찾을 수 없음: {username} ({department})")
        return None

    # ✅ 개선된 일괄 업로드 처리 - 비즈니스 로직을 백엔드로 이전
    def process_bulk_upload(self, period_id: int, records: List[Dict],
                            uploaded_by: str) -> Dict[str, Any]:
        """
        교육 결과 일괄 업로드 - 개선된 백엔드 로직

        개선사항:
        1. 수료/미수료 결정 로직을 백엔드에서 처리
        2. 비즈니스 규칙을 서버에서 검증
        3. 데이터 일관성 보장
        """
        try:
            self.logger.info(
                f"교육 일괄 업로드 시작 - period_id: {period_id}, records: {len(records)}건")

            # 1. 교육 기간 정보 조회 및 검증
            period_info = self._get_and_validate_period(period_id)
            if not period_info:
                return {"success": False, "error": "유효하지 않은 교육 기간입니다."}

            # 2. 업로드된 레코드들을 처리
            processed_results = self._process_education_records(
                records, period_info, uploaded_by)

            # 3. 데이터베이스에 저장
            save_results = self._save_education_records(processed_results, period_id)

            self.logger.info(
                f"교육 업로드 완료 - 성공: {save_results['success_count']}, 오류: {save_results['error_count']}"
            )

            return {
                "success": True,
                "success_count": save_results["success_count"],
                "update_count": save_results["update_count"],
                "error_count": save_results["error_count"],
                "errors": save_results["errors"][:10],  # 최대 10개 오류만 반환
                "message": self._generate_upload_message(save_results,
                                                         period_info["period_name"]),
            }

        except Exception as e:
            self.logger.error(f"교육 일괄 업로드 실패: {str(e)}")
            return {"success": False, "error": f"업로드 처리 실패: {str(e)}"}

    def _get_and_validate_period(self, period_id: int) -> Optional[Dict]:
        """교육 기간 정보 조회 및 검증"""
        try:
            period_info = execute_query(
                """
                SELECT period_id, period_name, education_type, education_year, 
                       start_date, end_date, is_completed, auto_pass_setting
                FROM security_education_periods 
                WHERE period_id = %s
                """,
                (period_id, ),
                fetch_one=True,
            )

            if not period_info:
                self.logger.warning(f"교육 기간을 찾을 수 없음: period_id={period_id}")
                return None

            if period_info["is_completed"]:
                self.logger.warning(f"완료된 교육 기간: period_id={period_id}")
                return None

            return period_info

        except Exception as e:
            self.logger.error(f"교육 기간 조회 실패: {str(e)}")
            return None

    def _process_education_records(self, records: List[Dict], period_info: Dict,
                                   uploaded_by: str) -> List[Dict]:
        """
        교육 레코드 처리 - 핵심 비즈니스 로직

        개선사항: 프론트엔드에서 전송된 원시 데이터를
        백엔드 비즈니스 규칙에 따라 수료/미수료로 판정
        """
        processed_records = []

        for idx, record in enumerate(records):
            try:
                # 1. 사용자 정보 검증
                user_info = self._validate_and_get_user(record.get("username"),
                                                        record.get("department"))
                if not user_info:
                    self.logger.warning(
                        f"사용자를 찾을 수 없음: {record.get('username')} ({record.get('department')})"
                    )
                    continue

                # 2. 교육 유형 검증
                education_type = self._validate_education_type(
                    record.get("education_type"), period_info["education_type"])
                if not education_type:
                    self.logger.warning(
                        f"유효하지 않은 교육 유형: {record.get('education_type')}")
                    continue

                # 3. ✅ 핵심 개선: 수료/미수료 결정 로직을 백엔드에서 처리
                completion_records = self._determine_completion_status(
                    record, period_info, uploaded_by)

                # 4. 처리된 레코드 추가
                for comp_record in completion_records:
                    comp_record.update({
                        "user_id": user_info["uid"],
                        "username": user_info["username"],
                        "department": user_info["department"],
                        "education_type": education_type,
                        "period_id": period_info["period_id"],
                        "education_year": period_info["education_year"],
                        "row_index": idx + 1,
                    })
                    processed_records.append(comp_record)

            except Exception as e:
                self.logger.error(f"레코드 처리 실패 (행 {idx+1}): {str(e)}")
                continue

        self.logger.info(f"레코드 처리 완료: {len(processed_records)}개 생성")
        return processed_records

    def _determine_completion_status(self, record: Dict, period_info: Dict,
                                     uploaded_by: str) -> List[Dict]:
        """
        ✅ 핵심 개선: 수료/미수료 결정 로직을 백엔드에서 처리

        비즈니스 규칙:
        1. 템플릿의 '수료' 컬럼 값 → 수료 레코드 생성
        2. 템플릿의 '미수료' 컬럼 값 → 미수료 레코드 생성
        3. 교육 유형별 추가 검증 로직 적용
        4. 기본값 및 예외 처리
        """
        completion_records = []

        # 원시 데이터에서 수료/미수료 횟수 추출
        completed_count = self._safe_int_conversion(record.get("completed_count", 0))
        incomplete_count = self._safe_int_conversion(record.get("incomplete_count", 0))

        # 비즈니스 규칙 검증
        validation_result = self._validate_education_counts(completed_count,
                                                            incomplete_count,
                                                            period_info)
        if not validation_result["valid"]:
            self.logger.warning(f"교육 횟수 검증 실패: {validation_result['message']}")
            return []

        # 수료 레코드 생성
        for i in range(completed_count):
            completion_records.append({
                "completion_status": 1,  # 수료
                "education_date": self._determine_education_date(record, period_info),
                "notes": f"일괄 업로드 - 수료 {i+1}회차 (업로더: {uploaded_by})",
                "exclude_from_scoring": False,
                "exclude_reason": None,
            })

        # 미수료 레코드 생성
        for i in range(incomplete_count):
            completion_records.append({
                "completion_status": 0,  # 미수료
                "education_date": None,  # 미수료는 날짜 없음
                "notes": f"일괄 업로드 - 미수료 {i+1}회차 (업로더: {uploaded_by})",
                "exclude_from_scoring": False,
                "exclude_reason": None,
            })

        self.logger.debug(
            f"수료/미수료 결정 완료: 수료 {completed_count}개, 미수료 {incomplete_count}개")
        return completion_records

    def _safe_int_conversion(self, value: Any) -> int:
        """안전한 정수 변환"""
        try:
            if value is None or value == "":
                return 0
            return max(0, int(float(str(value))))  # 음수 방지
        except (ValueError, TypeError):
            self.logger.warning(f"정수 변환 실패: {value}")
            return 0

    def _validate_education_counts(self, completed: int, incomplete: int,
                                   period_info: Dict) -> Dict:
        """교육 횟수 검증 - 비즈니스 규칙 적용"""

        # 기본 검증
        if completed < 0 or incomplete < 0:
            return {"valid": False, "message": "교육 횟수는 0 이상이어야 합니다."}

        if completed == 0 and incomplete == 0:
            return {"valid": False, "message": "수료 또는 미수료 횟수가 있어야 합니다."}

        # 교육 유형별 검증
        education_type = period_info["education_type"]
        total_count = completed + incomplete

        # 오프라인 교육은 일반적으로 1회성
        if education_type == "오프라인" and total_count > 3:
            self.logger.warning(f"오프라인 교육 횟수가 많음: {total_count}회")

        # 온라인 교육은 여러 과정 가능하지만 상한선 설정
        if education_type == "온라인" and total_count > 10:
            return {
                "valid": False,
                "message": f"온라인 교육 횟수가 너무 많습니다: {total_count}회 (최대 10회)",
            }

        return {"valid": True, "message": "검증 통과"}

    def _determine_education_date(self, record: Dict,
                                  period_info: Dict) -> Optional[str]:
        """교육 완료 날짜 결정"""
        # 1. 레코드에 명시적 날짜가 있는 경우
        if record.get("education_date"):
            try:
                # 날짜 형식 검증
                datetime.strptime(record["education_date"], "%Y-%m-%d")
                return record["education_date"]
            except ValueError:
                self.logger.warning(f"잘못된 날짜 형식: {record['education_date']}")

        # 2. 교육 기간 내의 기본 날짜 설정
        if period_info["start_date"] and period_info["end_date"]:
            # 교육 기간 중간 날짜를 기본값으로 사용
            start_date = period_info["start_date"]
            return start_date.strftime("%Y-%m-%d")

        # 3. 현재 날짜를 기본값으로 사용
        return datetime.now().strftime("%Y-%m-%d")

    def _validate_and_get_user(self, username: str, department: str) -> Optional[Dict]:
        """사용자 정보 검증 및 조회"""
        if not username or not department:
            return None

        try:
            # 1. 정확한 매칭 시도
            user = execute_query(
                "SELECT uid, username, department FROM users WHERE username = %s AND department = %s LIMIT 1",
                (username.strip(), department.strip()),
                fetch_one=True,
            )

            if user:
                return user

            # 2. 이름만으로 검색 (부서가 다를 수 있음)
            user = execute_query(
                "SELECT uid, username, department FROM users WHERE username = %s LIMIT 1",
                (username.strip(), ),
                fetch_one=True,
            )

            if user:
                self.logger.info(
                    f"부서 불일치 - 템플릿: {department}, DB: {user['department']}")
                return user

            return None

        except Exception as e:
            self.logger.error(f"사용자 조회 실패: {str(e)}")
            return None

    def _validate_education_type(self, education_type: str,
                                 period_education_type: str) -> Optional[str]:
        """교육 유형 검증"""
        if not education_type:
            return None

        # 표준화된 교육 유형 목록
        valid_types = ["오프라인", "온라인"]

        # 정확한 매칭
        if education_type in valid_types:
            # 교육 기간의 유형과 일치하는지 확인
            if education_type == period_education_type:
                return education_type
            else:
                self.logger.warning(
                    f"교육 유형 불일치 - 템플릿: {education_type}, 기간: {period_education_type}")
                # 경고하지만 처리는 계속 (유연성 제공)
                return education_type

        return None

    def _save_education_records(self, processed_records: List[Dict],
                                period_id: int) -> Dict:
        """처리된 교육 레코드를 데이터베이스에 저장"""
        success_count = 0
        update_count = 0
        error_count = 0
        errors = []

        try:
            with DatabaseManager.get_db_cursor() as cursor:
                for record in processed_records:
                    try:
                        # 기존 레코드 삭제 (동일 사용자 + 기간 + 교육유형)
                        cursor.execute(
                            """
                            DELETE FROM security_education 
                            WHERE user_id = %s AND period_id = %s AND education_type = %s
                            """,
                            (record["user_id"], period_id, record["education_type"]),
                        )
                        deleted_count = cursor.rowcount

                        # 새 레코드 삽입
                        cursor.execute(
                            """
                            INSERT INTO security_education 
                            (user_id, period_id, education_type, education_year,
                             completion_status, education_date, notes, exclude_from_scoring, 
                             exclude_reason, created_at, updated_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                            """,
                            (
                                record["user_id"],
                                record["period_id"],
                                record["education_type"],
                                record["education_year"],
                                self._get_education_period_from_date(
                                    record.get("education_date")),
                                record["completion_status"],
                                record.get("education_date"),
                                record["notes"],
                                record["exclude_from_scoring"],
                                record["exclude_reason"],
                            ),
                        )

                        if deleted_count > 0:
                            update_count += 1
                        else:
                            success_count += 1

                    except Exception as e:
                        error_msg = f"행 {record.get('row_index', '?')} ({record.get('username', 'Unknown')}): {str(e)}"
                        errors.append(error_msg)
                        error_count += 1
                        self.logger.error(f"레코드 저장 실패 - {error_msg}")

        except Exception as e:
            self.logger.error(f"데이터베이스 저장 실패: {str(e)}")
            raise

        return {
            "success_count": success_count,
            "update_count": update_count,
            "error_count": error_count,
            "errors": errors,
        }

    def _get_education_period_from_date(self, education_date: Optional[str]) -> str:
        """교육 날짜로부터 교육 기간 결정"""
        if not education_date:
            return "first_half"  # 기본값

        try:
            date_obj = datetime.strptime(education_date, "%Y-%m-%d")
            return "first_half" if date_obj.month <= 6 else "second_half"
        except ValueError:
            return "first_half"

    def _generate_upload_message(self, save_results: Dict, period_name: str) -> str:
        """업로드 결과 메시지 생성"""
        success_count = save_results["success_count"]
        update_count = save_results["update_count"]
        error_count = save_results["error_count"]

        if update_count > 0:
            return f"{period_name}에 업로드 완료 (신규: {success_count}건, 업데이트: {update_count}건, 오류: {error_count}건)"
        else:
            return (f"{period_name}에 {success_count}건 업로드 완료 (오류: {error_count}건)")

    # ✅ 추가 개선: 교육 기간 정보 조회
    def get_period_info(self, period_id: int) -> Optional[Dict]:
        """교육 기간 정보 조회"""
        return self._get_and_validate_period(period_id)

    # ✅ 기존 템플릿 생성 함수 개선
    def get_education_excel_template(self) -> str:
        """
        개선된 엑셀 업로드용 템플릿 생성
        - 명확한 컬럼명 사용
        - 예시 데이터로 사용법 설명
        """
        template_data = [
            "# 정보보호 교육 업로드 템플릿",
            "# 수료: 수료한 교육 횟수, 미수료: 미수료한 교육 횟수",
            "# 교육유형은 선택한 교육 기간의 유형과 일치해야 합니다",
            "",
            "이름,부서,수강과정,수료,미수료",
            "홍길동,개발팀,오프라인,1,0",
            "김철수,운영팀,오프라인,0,1",
            "이영희,기획팀,온라인,2,1",
            "박민수,인사팀,온라인,3,0",
        ]
        return "\n".join(template_data)
