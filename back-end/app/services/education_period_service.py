# back-end/app/services/education_period_service.py
from datetime import datetime, date
from app.utils.database import execute_query, DatabaseManager
import logging


class EducationPeriodService:
    """정보보호 교육 기간 관리 서비스"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def format_date_for_frontend(self, date_value):
        """날짜를 프론트엔드용 YYYY-MM-DD 형식으로 변환"""
        if not date_value:
            return None

        if isinstance(date_value, str):
            try:
                if (len(date_value) == 10 and date_value[4] == "-"
                        and date_value[7] == "-"):
                    return date_value
                parsed_date = datetime.strptime(date_value, "%Y-%m-%d")
                return parsed_date.strftime("%Y-%m-%d")
            except:
                return date_value

        try:
            return date_value.strftime("%Y-%m-%d")
        except:
            return str(date_value) if date_value else None

    def get_period_status(self, year: int = None) -> dict:
        """연도별 교육 기간 현황 조회"""
        if year is None:
            year = datetime.now().year

        periods = execute_query(
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
                CASE 
                    WHEN CURDATE() BETWEEN start_date AND end_date THEN 'active'
                    WHEN CURDATE() < start_date THEN 'upcoming'
                    WHEN CURDATE() > end_date THEN 'ended'
                    ELSE 'unknown'
                END as status
            FROM security_education_periods
            WHERE education_year = %s
            ORDER BY education_type, start_date
            """,
            (year, ),
            fetch_all=True,
        )

        for period in periods:
            period["start_date"] = self.format_date_for_frontend(
                period.get("start_date"))
            period["end_date"] = self.format_date_for_frontend(
                period.get("end_date"))
            if period.get("completed_at"):
                period["completed_at"] = period["completed_at"].isoformat(
                ) if hasattr(period["completed_at"],
                             "isoformat") else str(period["completed_at"])
            # SQL 상태값 대신 사용자 페이지와 동일한 상태 판정 적용
            period["status"] = self._determine_period_status(period)

        education_types = {}
        for period in periods:
            edu_type = period.get("education_type", "기타")
            if edu_type not in education_types:
                education_types[edu_type] = {"periods": []}
            education_types[edu_type]["periods"].append(period)

        return {"year": year, "education_types": education_types}

    def get_periods_with_statistics(self, year: int = None) -> dict:
        """교육 기간 목록과 통계 정보를 함께 조회"""
        try:
            if year is None:
                year = datetime.now().year

            query = """
            SELECT 
                sep.period_id,
                sep.education_year,
                sep.period_name,
                sep.education_type,
                sep.start_date,
                sep.end_date,
                sep.is_completed,
                sep.completed_at,
                sep.completed_by,
                sep.description,
                sep.auto_pass_setting,
                sep.created_by,
                sep.created_at,
                sep.updated_at,
                COUNT(DISTINCT se.user_id) as total_participants,
                COUNT(DISTINCT CASE WHEN se.incomplete_count = 0 AND se.completed_count > 0 
                      THEN se.user_id END) as success_count,
                COUNT(DISTINCT CASE WHEN se.incomplete_count > 0 
                      THEN se.user_id END) as failure_count,
                COALESCE(
                    CASE 
                        WHEN COUNT(DISTINCT se.user_id) > 0 
                        THEN ROUND(
                            COUNT(DISTINCT CASE WHEN se.incomplete_count = 0 AND se.completed_count > 0 
                                  THEN se.user_id END) 
                            / COUNT(DISTINCT se.user_id) * 100, 
                            2
                        )
                        ELSE 0 
                    END, 
                    0
                ) as success_rate
            FROM security_education_periods sep
            LEFT JOIN security_education se ON sep.period_id = se.period_id
            WHERE sep.education_year = %s
            GROUP BY sep.period_id
            ORDER BY sep.education_type, sep.start_date DESC
            """

            periods = execute_query(query, (year, ), fetch_all=True)

            education_types = {}
            for period in periods:
                period["start_date"] = self.format_date_for_frontend(
                    period.get("start_date"))
                period["end_date"] = self.format_date_for_frontend(
                    period.get("end_date"))
                if period.get("completed_at"):
                    period["completed_at"] = period[
                        "completed_at"].isoformat() if hasattr(
                            period["completed_at"],
                            "isoformat") else str(period["completed_at"])

                period["statistics"] = {
                    "total_participants":
                    int(period.pop("total_participants", 0)),
                    "success_count":
                    int(period.pop("success_count", 0)),
                    "failure_count":
                    int(period.pop("failure_count", 0)),
                    "success_rate":
                    float(period.pop("success_rate", 0)),
                }

                # 사용자 페이지와 동일한 상태 판정
                period["status"] = self._determine_period_status(period)

                edu_type = period.get("education_type", "기타")
                if edu_type not in education_types:
                    education_types[edu_type] = {"periods": []}
                education_types[edu_type]["periods"].append(period)

            return {"year": year, "education_types": education_types}

        except Exception as e:
            print(f"[DB_DEBUG] 기간+통계 조회 실패: {str(e)}")
            return {"year": year, "education_types": {}}

    def create_education_period(self, period_data: dict,
                                created_by: str) -> dict:
        """교육 기간 생성"""
        try:
            print(
                f"[DB_DEBUG] 교육 기간 생성 시작: {period_data.get('period_name')}"
            )

            # 기간 중복 확인
            existing = execute_query(
                """
                SELECT period_id FROM security_education_periods
                WHERE education_year = %s AND period_name = %s AND education_type = %s
                """,
                (
                    period_data["education_year"],
                    period_data["period_name"],
                    period_data["education_type"],
                ),
                fetch_one=True,
            )

            if existing:
                return {
                    "success":
                    False,
                    "message":
                    f"동일한 교육 기간이 이미 존재합니다. (기간명: {period_data['period_name']}, 유형: {period_data['education_type']})",
                }

            print(f"[DB_DEBUG] 기간 생성 진행")

            with DatabaseManager.get_db_cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO security_education_periods 
                    (education_year, period_name, education_type, start_date, end_date, 
                    description, auto_pass_setting, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        period_data["education_year"],
                        period_data["period_name"],
                        period_data["education_type"],
                        period_data["start_date"],
                        period_data["end_date"],
                        period_data.get("description", ""),
                        period_data.get("auto_pass_setting", 1),
                        created_by,
                    ),
                )

                period_id = cursor.lastrowid

            print(f"[DB_DEBUG] 기간 생성 완료, period_id: {period_id}")

            return {
                "success": True,
                "message":
                f"{period_data['period_name']} 기간이 생성되었습니다.",
                "period_id": period_id,
            }

        except Exception as e:
            print(f"[DB_DEBUG] 기간 생성 예외: {str(e)}")
            return {"success": False, "message": f"기간 생성 실패: {str(e)}"}

    def complete_period(self, period_id: int, completed_by: str) -> dict:
        """
        교육 기간 완료 처리
        - 미참여 사용자 → 자동 미수료 처리 (completed_count=0, incomplete_count=1)
        - 부분 수료 사용자 → 변경 없이 그대로 유지
        """
        try:
            print(f"[DB_DEBUG] 완료 처리 시작 - period_id: {period_id}, completed_by: {completed_by}")

            with DatabaseManager.get_db_cursor() as cursor:
                # 1. 기간 정보 확인
                cursor.execute(
                    """
                    SELECT period_id, period_name, education_type, education_year, 
                        is_completed, auto_pass_setting
                    FROM security_education_periods
                    WHERE period_id = %s
                    """,
                    (period_id,),
                )

                period_info = cursor.fetchone()
                if not period_info:
                    return {"success": False, "message": "해당 기간을 찾을 수 없습니다."}

                if period_info["is_completed"]:
                    return {"success": False, "message": "이미 완료된 기간입니다."}

                # 2. 미참여 사용자를 미수료로 자동 처리
                auto_fail_count = 0

                print(f"[DB_DEBUG] 미참여 사용자 미수료 처리 시작")

                try:
                    # 교육 기록이 없는 활성 사용자 조회
                    cursor.execute(
                        """
                        SELECT u.uid, u.username
                        FROM users u
                        WHERE u.is_active = 1
                        AND u.uid NOT IN (
                            SELECT DISTINCT user_id 
                            FROM security_education 
                            WHERE period_id = %s
                        )
                        """,
                        (period_id,),
                    )

                    users_not_participated = cursor.fetchall()
                    print(f"[DB_DEBUG] 미참여 사용자: {len(users_not_participated)}명")

                    # 미참여 사용자별로 미수료 기록 생성
                    for user in users_not_participated:
                        try:
                            cursor.execute(
                                """
                                INSERT INTO security_education 
                                (user_id, period_id, education_type, education_year,
                                course_name, completed_count, incomplete_count, notes, created_at)
                                VALUES (%s, %s, %s, %s, %s, 0, 1, 
                                        '기간 완료 - 미참여 자동 미수료 처리', NOW())
                                """,
                                (
                                    user["uid"],
                                    period_id,
                                    period_info["education_type"],
                                    period_info["education_year"],
                                    period_info["period_name"],
                                ),
                            )

                            if cursor.rowcount > 0:
                                auto_fail_count += 1

                        except Exception as user_error:
                            print(f"[DB_DEBUG] 사용자 {user['username']} 미수료 처리 실패: {str(user_error)}")
                            continue

                    print(f"[DB_DEBUG] 미참여 사용자 미수료 처리 완료: {auto_fail_count}명")

                except Exception as e:
                    print(f"[DB_DEBUG] 미수료 자동 처리 실패: {str(e)}")
                    # 자동 처리 실패해도 기간 완료는 계속 진행

                # 3. 기간 완료 상태 업데이트
                print(f"[DB_DEBUG] 기간 완료 상태 업데이트 중...")
                cursor.execute(
                    """
                    UPDATE security_education_periods
                    SET is_completed = 1, completed_at = NOW(), completed_by = %s, updated_at = NOW()
                    WHERE period_id = %s
                    """,
                    (completed_by, period_id),
                )

                print(f"[DB_DEBUG] 기간 완료 처리 성공")

                # 4. 결과 메시지 생성
                message = f"{period_info['period_name']} 기간이 완료되었습니다."
                if auto_fail_count > 0:
                    message += f" 미참여 사용자 {auto_fail_count}명이 미수료 처리되었습니다."

                return {
                    "success": True,
                    "message": message,
                    "auto_fail_count": auto_fail_count,
                }

        except Exception as e:
            print(f"[DB_DEBUG] 완료 처리 예외: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": f"완료 처리 실패: {str(e)}"}

    def reopen_period(self, period_id: int) -> dict:
        """
        교육 기간 재개 (완료 상태 취소)
        - 수정되지 않은 자동 미수료 기록만 삭제
        - 관리자가 수정한 기록(수료로 변경 등)은 유지
        - 기간 상태를 미완료로 변경
        """
        try:
            print(f"[DB_DEBUG] 기간 재개 시작 - period_id: {period_id}")

            with DatabaseManager.get_db_cursor() as cursor:
                # 1. 기간 정보 조회
                cursor.execute(
                    """
                    SELECT period_name, is_completed
                    FROM security_education_periods 
                    WHERE period_id = %s
                    """,
                    (period_id, ),
                )
                period_info = cursor.fetchone()

                if not period_info:
                    return {
                        "success": False,
                        "message": "해당 기간을 찾을 수 없습니다.",
                    }

                if not period_info["is_completed"]:
                    return {"success": False, "message": "완료되지 않은 기간입니다."}

                # 2. 관리자가 수정한 자동 기록 수 확인 (삭제하지 않을 건수)
                cursor.execute(
                    """
                    SELECT COUNT(*) as cnt FROM security_education 
                    WHERE period_id = %s 
                    AND (notes = '기간 완료 - 미참여 자동 미수료 처리'
                         OR notes = '기간 완료로 인한 자동 통과 처리')
                    AND NOT (completed_count = 0 AND incomplete_count = 1)
                    """,
                    (period_id, ),
                )
                kept_count = cursor.fetchone()["cnt"]

                # 3. 수정되지 않은 자동 미수료 기록만 삭제
                #    (completed_count=0, incomplete_count=1 → 자동 생성 상태 그대로)
                cursor.execute(
                    """
                    DELETE FROM security_education 
                    WHERE period_id = %s 
                    AND (notes = '기간 완료 - 미참여 자동 미수료 처리'
                         OR notes = '기간 완료로 인한 자동 통과 처리')
                    AND completed_count = 0 AND incomplete_count = 1
                    """,
                    (period_id, ),
                )

                deleted_count = cursor.rowcount
                print(f"[DB_DEBUG] 자동 처리 기록 삭제: {deleted_count}건, 수정되어 유지: {kept_count}건")

                # 4. 기간 상태를 미완료로 변경
                cursor.execute(
                    """
                    UPDATE security_education_periods
                    SET is_completed = 0, completed_at = NULL, completed_by = NULL, updated_at = NOW()
                    WHERE period_id = %s
                    """,
                    (period_id, ),
                )

                message = f"{period_info['period_name']} 기간이 재개되었습니다."
                if deleted_count > 0:
                    message += f" 미수정 자동 기록 {deleted_count}건이 삭제되었습니다."
                if kept_count > 0:
                    message += f" 관리자가 수정한 {kept_count}건은 유지되었습니다."

                return {
                    "success": True,
                    "message": message,
                    "deleted_count": deleted_count,
                    "kept_count": kept_count,
                }

        except Exception as e:
            print(f"[DB_DEBUG] 재개 처리 예외: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": f"재개 처리 실패: {str(e)}"}

    def update_education_period(self, period_id: int,
                                period_data: dict) -> dict:
        """교육 기간 수정 + 하위 교육 기록 연동"""
        try:
            print(
                f"[DB_DEBUG] 교육 기간 수정 시작 - period_id: {period_id}, data: {period_data}"
            )

            with DatabaseManager.get_db_cursor() as cursor:
                # 1. 기존 기간 정보 조회 (변경 전 값 보존)
                cursor.execute(
                    """SELECT period_id, period_name, education_type,
                              education_year, is_completed
                       FROM security_education_periods WHERE period_id = %s""",
                    (period_id, ),
                )
                existing = cursor.fetchone()

                if not existing:
                    return {
                        "success": False,
                        "message": "해당 교육 기간을 찾을 수 없습니다.",
                    }

                old_period_name = existing["period_name"]
                old_education_type = existing["education_type"]
                old_education_year = existing["education_year"]

                new_period_name = period_data.get("period_name",
                                                   old_period_name)
                new_education_type = period_data.get("education_type",
                                                      old_education_type)
                new_education_year = period_data.get("education_year",
                                                      old_education_year)

                # 2. 기간 테이블 업데이트
                cursor.execute(
                    """
                    UPDATE security_education_periods
                    SET period_name = %s, education_type = %s,
                        start_date = %s, end_date = %s,
                        description = %s, auto_pass_setting = %s,
                        updated_at = NOW()
                    WHERE period_id = %s
                    """,
                    (
                        new_period_name,
                        new_education_type,
                        period_data.get("start_date"),
                        period_data.get("end_date"),
                        period_data.get("description", ""),
                        period_data.get("auto_pass_setting", 1),
                        period_id,
                    ),
                )

                if cursor.rowcount == 0:
                    return {
                        "success": False,
                        "message": "수정된 내용이 없습니다.",
                    }

                # 3. 하위 교육 기록(security_education) 연동
                synced_count = 0
                sync_details = []

                # 4-a. 기간명 변경 → course_name 연동
                if new_period_name != old_period_name:
                    cursor.execute(
                        """
                        UPDATE security_education
                        SET course_name = %s, updated_at = NOW()
                        WHERE period_id = %s AND course_name = %s
                        """,
                        (new_period_name, period_id, old_period_name),
                    )
                    cnt = cursor.rowcount
                    if cnt > 0:
                        synced_count += cnt
                        sync_details.append(f"과정명 {cnt}건")
                    print(
                        f"[DB_DEBUG] 과정명 연동: '{old_period_name}' → '{new_period_name}' ({cnt}건)"
                    )

                # 4-b. 교육 유형 변경 → education_type 연동
                if new_education_type != old_education_type:
                    cursor.execute(
                        """
                        UPDATE security_education
                        SET education_type = %s, updated_at = NOW()
                        WHERE period_id = %s AND education_type = %s
                        """,
                        (new_education_type, period_id,
                         old_education_type),
                    )
                    cnt = cursor.rowcount
                    if cnt > 0:
                        synced_count += cnt
                        sync_details.append(f"교육유형 {cnt}건")
                    print(
                        f"[DB_DEBUG] 교육유형 연동: '{old_education_type}' → '{new_education_type}' ({cnt}건)"
                    )

                # 4-c. 교육 연도 변경 → education_year 연동
                if int(new_education_year) != int(old_education_year):
                    cursor.execute(
                        """
                        UPDATE security_education
                        SET education_year = %s, updated_at = NOW()
                        WHERE period_id = %s AND education_year = %s
                        """,
                        (new_education_year, period_id,
                         old_education_year),
                    )
                    cnt = cursor.rowcount
                    if cnt > 0:
                        synced_count += cnt
                        sync_details.append(f"연도 {cnt}건")
                    print(
                        f"[DB_DEBUG] 교육연도 연동: {old_education_year} → {new_education_year} ({cnt}건)"
                    )

                # 4. 결과 메시지 생성
                message = f"{new_period_name} 기간이 수정되었습니다."
                if synced_count > 0:
                    message += f" (교육 기록 연동: {', '.join(sync_details)})"

                print(
                    f"[DB_DEBUG] 교육 기간 수정 완료: {new_period_name}, 연동: {synced_count}건"
                )

                return {
                    "success": True,
                    "message": message,
                    "synced_count": synced_count,
                }

        except Exception as e:
            print(f"[DB_DEBUG] 교육 기간 수정 예외: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": f"수정 실패: {str(e)}"}

    def delete_education_period(self, period_id: int) -> dict:
        """교육 기간 삭제"""
        try:
            print(f"[DB_DEBUG] 교육 기간 삭제 시작 - period_id: {period_id}")

            with DatabaseManager.get_db_cursor() as cursor:
                # 기간 존재 확인
                cursor.execute(
                    "SELECT period_id, period_name, is_completed FROM security_education_periods WHERE period_id = %s",
                    (period_id, ),
                )
                existing = cursor.fetchone()

                if not existing:
                    return {
                        "success": False,
                        "message": "해당 교육 기간을 찾을 수 없습니다.",
                    }

                if existing["is_completed"]:
                    return {
                        "success": False,
                        "message":
                        "완료된 기간은 삭제할 수 없습니다. 먼저 재개해주세요.",
                    }

                # 관련 교육 기록 확인
                cursor.execute(
                    "SELECT COUNT(*) as count FROM security_education WHERE period_id = %s",
                    (period_id, ),
                )
                education_count = cursor.fetchone()["count"]

                if education_count > 0:
                    # 교육 기록이 있으면 확인 필요
                    return {
                        "success": False,
                        "message":
                        f"이 기간에 {education_count}건의 교육 기록이 있습니다. 기록을 먼저 삭제하거나, 강제 삭제를 사용해주세요.",
                        "requires_confirmation": True,
                        "education_count": education_count,
                    }

                # 삭제 실행
                cursor.execute(
                    "DELETE FROM security_education_periods WHERE period_id = %s",
                    (period_id, ),
                )

                return {
                    "success": True,
                    "message":
                    f"{existing['period_name']} 기간이 삭제되었습니다.",
                }

        except Exception as e:
            print(f"[DB_DEBUG] 교육 기간 삭제 예외: {str(e)}")
            return {"success": False, "message": f"삭제 실패: {str(e)}"}

    def force_delete_education_period(self, period_id: int) -> dict:
        """교육 기간 강제 삭제 (관련 교육 기록 포함)"""
        try:
            print(
                f"[DB_DEBUG] 교육 기간 강제 삭제 시작 - period_id: {period_id}"
            )

            with DatabaseManager.get_db_cursor() as cursor:
                # 기간 존재 확인
                cursor.execute(
                    "SELECT period_id, period_name FROM security_education_periods WHERE period_id = %s",
                    (period_id, ),
                )
                existing = cursor.fetchone()

                if not existing:
                    return {
                        "success": False,
                        "message": "해당 교육 기간을 찾을 수 없습니다.",
                    }

                period_name = existing["period_name"]

                # 관련 교육 기록 먼저 삭제
                cursor.execute(
                    "DELETE FROM security_education WHERE period_id = %s",
                    (period_id, ),
                )
                deleted_records = cursor.rowcount
                print(
                    f"[DB_DEBUG] 관련 교육 기록 삭제: {deleted_records}건"
                )

                # 기간 삭제
                cursor.execute(
                    "DELETE FROM security_education_periods WHERE period_id = %s",
                    (period_id, ),
                )

                message = f"{period_name} 기간이 삭제되었습니다."
                if deleted_records > 0:
                    message += f" (관련 교육 기록 {deleted_records}건 함께 삭제)"

                return {
                    "success": True,
                    "message": message,
                    "deleted_records": deleted_records,
                }

        except Exception as e:
            print(f"[DB_DEBUG] 강제 삭제 예외: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": f"강제 삭제 실패: {str(e)}"}

    # ===== 컨트롤러 호환 alias 메서드 =====

    def _determine_period_status(self, period):
        """교육 기간 상태 결정 (사용자 페이지와 동일한 로직)"""
        today = date.today()

        start_date = period.get("start_date")
        end_date = period.get("end_date")
        is_completed = period.get("is_completed")

        # 문자열이면 date로 변환
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        if is_completed:
            return "completed"
        elif today < start_date:
            return "not_started"
        elif start_date <= today <= end_date:
            return "in_progress"
        elif today > end_date:
            return "expired"
        else:
            return "unknown"

    def create_period(self, data: dict, created_by: str) -> dict:
        """create_education_period 의 alias (컨트롤러 호환)"""
        return self.create_education_period(data, created_by)

    def update_period(self, period_id: int, data: dict,
                      updated_by: str = None) -> dict:
        """update_education_period 의 alias (컨트롤러 호환)"""
        return self.update_education_period(period_id, data)

    def check_period_exists(self, year: int, period_name: str,
                            education_type: str) -> bool:
        """기간 중복 체크"""
        result = execute_query(
            """
            SELECT COUNT(*) as count
            FROM security_education_periods
            WHERE education_year = %s AND period_name = %s AND education_type = %s
            """,
            (year, period_name, education_type),
            fetch_one=True,
        )
        return result["count"] > 0

    def check_date_overlap(self,
                           education_type: str,
                           start_date,
                           end_date,
                           exclude_period_id: int = None) -> dict:
        """날짜 겹침 검사"""
        try:
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date,
                                               "%Y-%m-%d").date()
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

            query = """
            SELECT period_id, period_name, education_year, start_date, end_date
            FROM security_education_periods
            WHERE education_type = %s
            AND start_date <= %s AND end_date >= %s
            """
            params = [education_type, end_date, start_date]

            if exclude_period_id:
                query += " AND period_id != %s"
                params.append(exclude_period_id)

            overlapping = execute_query(query,
                                        tuple(params),
                                        fetch_all=True)

            if overlapping:
                formatted_periods = []
                for p in overlapping:
                    formatted_periods.append({
                        "period_id":
                        p["period_id"],
                        "period_name":
                        p["period_name"],
                        "year":
                        p["education_year"],
                        "start_date":
                        self.format_date_for_frontend(p["start_date"]),
                        "end_date":
                        self.format_date_for_frontend(p["end_date"]),
                    })

                return {
                    "has_overlap": True,
                    "overlapping_periods": formatted_periods,
                }

            return {"has_overlap": False}

        except Exception as e:
            print(f"[DB_DEBUG] 날짜 겹침 검사 실패: {str(e)}")
            return {"has_overlap": False}

    def get_period_statistics(self, period_id: int) -> dict:
        """교육 기간 상세 통계 조회"""
        try:
            # 기간 정보
            period = execute_query(
                "SELECT * FROM security_education_periods WHERE period_id = %s",
                (period_id, ),
                fetch_one=True,
            )

            if not period:
                return {"error": "기간을 찾을 수 없습니다."}

            # 참가자 목록 및 통계
            participants = execute_query(
                """
                SELECT 
                    se.user_id,
                    u.username,
                    u.department,
                    se.completed_count,
                    se.incomplete_count,
                    se.exclude_from_scoring,
                    se.exclude_reason,
                    CASE 
                        WHEN (se.completed_count + se.incomplete_count) > 0 
                        THEN ROUND((se.completed_count / (se.completed_count + se.incomplete_count)) * 100, 1)
                        ELSE 0 
                    END as completion_rate,
                    CASE 
                        WHEN se.incomplete_count = 0 AND se.completed_count > 0 THEN 'success'
                        ELSE 'failure'
                    END as user_status
                FROM security_education se
                JOIN users u ON se.user_id = u.uid
                WHERE se.period_id = %s
                ORDER BY u.department, u.username
                """,
                (period_id, ),
                fetch_all=True,
            )

            total = len(participants)
            success_count = sum(1 for p in participants
                                if p["user_status"] == "success")
            failure_count = total - success_count

            return {
                "period_info":
                period,
                "total_participants":
                total,
                "success_count":
                success_count,
                "failure_count":
                failure_count,
                "success_rate":
                round((success_count / total * 100), 1) if total > 0 else 0,
                "participants":
                participants,
            }

        except Exception as e:
            print(f"[DB_DEBUG] 통계 조회 실패: {str(e)}")
            return {"error": f"통계 조회 실패: {str(e)}"}