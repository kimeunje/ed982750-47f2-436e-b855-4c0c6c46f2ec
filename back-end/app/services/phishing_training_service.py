# app/services/phishing_training_service.py
from datetime import datetime
from typing import Dict, List, Optional, Any
import pandas as pd
import logging
import io
import csv
from werkzeug.datastructures import FileStorage
from app.utils.database import execute_query, DatabaseManager

logger = logging.getLogger(__name__)


class PhishingTrainingService:
    """피싱 훈련 데이터 관리 서비스"""


# app/services/phishing_training_service.py
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from urllib.parse import quote
from app.utils.database import execute_query, DatabaseManager
import logging


class PhishingTrainingService:
    """모의훈련 데이터 관리 서비스"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def get_user_training_status(self, username: str, year: int = None) -> dict:
        """사용자별 모의훈련 현황 조회"""
        if year is None:
            year = datetime.now().year

        try:
            # username으로 사용자 정보 조회 (user_id 컬럼이 실제 로그인 ID)
            user = execute_query(
                "SELECT uid, user_id as username, department FROM users WHERE user_id = %s",
                (username, ),
                fetch_one=True,
            )

            if not user:
                raise ValueError("사용자를 찾을 수 없습니다.")

            user_uid = user["uid"]

            # 사용자의 훈련 기록 조회 (실제 DB 스키마에 맞춤)
            training_records = execute_query(
                """
                SELECT 
                    pt.training_id,
                    pt.training_year,
                    pt.email_sent_time,
                    pt.action_time,
                    pt.log_type,
                    pt.mail_type,
                    pt.target_email,
                    pt.training_result,
                    pt.response_time_minutes,
                    pt.notes,
                    pt.exclude_from_scoring,
                    pt.exclude_reason,
                    ptp.period_name,
                    ptp.training_type,
                    ptp.start_date,
                    ptp.end_date,
                    ptp.is_completed as period_completed
                FROM phishing_training pt
                LEFT JOIN phishing_training_periods ptp ON pt.period_id = ptp.period_id
                WHERE pt.user_id = %s AND pt.training_year = %s
                ORDER BY pt.email_sent_time DESC
                """,
                (user_uid, year),
                fetch_all=True,
            )

            # 훈련 통계 계산
            training_summary = self._calculate_training_summary(training_records)

            # 기간별 상태 계산
            period_status = self._calculate_period_status(training_records, year,
                                                          user_uid)

            return {
                "user_info": user,
                "year": year,
                "training_records": training_records,
                "summary": training_summary,
                "period_status": period_status,
            }

        except Exception as e:
            self.logger.error(f"모의훈련 현황 조회 실패: {str(e)}")
            raise ValueError(f"모의훈련 현황 조회 실패: {str(e)}")

    def _calculate_training_summary(self, training_records: List[Dict]) -> Dict:
        """훈련 통계 계산"""
        summary = {
            "conducted": 0,
            "passed": 0,
            "failed": 0,
            "pending": 0,
            "not_started": 0,
            "overall_score": 0,
            "pass_rate": 0,
            "penalty_score": 0,
            "excluded_count": 0,
        }

        if not training_records:
            return summary

        # 실제 결과값에 따른 계산 (success, fail, no_response)
        summary["conducted"] = len([
            r for r in training_records if r["training_result"] in ["success", "fail"]
        ])
        summary["passed"] = len(
            [r for r in training_records if r["training_result"] == "success"])
        summary["failed"] = len(
            [r for r in training_records if r["training_result"] == "fail"])
        summary["pending"] = len(
            [r for r in training_records if r["training_result"] == "no_response"])
        summary["excluded_count"] = len(
            [r for r in training_records if r["exclude_from_scoring"]])

        # 감점 계산 (실패한 훈련은 0.5점 감점)
        penalty_score = 0
        for record in training_records:
            if (record["training_result"] == "fail"
                    and not record["exclude_from_scoring"]):
                penalty_score += 0.5  # 기본 감점 0.5점

        summary["penalty_score"] = penalty_score

        # 통과율 계산
        total_completed = summary["conducted"]
        if total_completed > 0:
            summary["pass_rate"] = round((summary["passed"] / total_completed) * 100, 1)

        return summary

    def _calculate_period_status(self, training_records: List[Dict], year: int,
                                 user_uid: int) -> List[Dict]:
        """기간별 상태 계산 - 실제 DB에서 기간 정보 조회"""

        # 해당 연도의 모든 훈련 기간 조회
        all_periods = execute_query(
            """
            SELECT 
                period_id,
                period_name,
                training_type,
                start_date,
                end_date,
                is_completed
            FROM phishing_training_periods
            WHERE training_year = %s
            ORDER BY start_date
            """,
            (year, ),
            fetch_all=True,
        )

        period_status = []

        for period in all_periods:
            # 해당 기간의 사용자 훈련 기록 찾기
            user_record = None
            for record in training_records:
                if record.get("period_name") == period["period_name"]:
                    user_record = record
                    break

            if user_record:
                # 훈련 기록이 있는 경우
                period_data = {
                    "period": f"period_{period['period_id']}",
                    "period_name": period["period_name"],
                    "training_year": year,
                    "start_date": (period["start_date"].strftime("%Y-%m-%d")
                                   if period["start_date"] else None),
                    "end_date": (period["end_date"].strftime("%Y-%m-%d")
                                 if period["end_date"] else None),
                    "result": ("pass" if user_record["training_result"] == "success"
                               else ("fail" if user_record["training_result"] == "fail"
                                     else "pending")),
                    "email_sent_time": (user_record["email_sent_time"].isoformat() + "Z"
                                        if user_record["email_sent_time"] else None),
                    "action_time": (user_record["action_time"].isoformat() +
                                    "Z" if user_record["action_time"] else None),
                    "log_type": user_record["log_type"],
                    "mail_type": user_record["mail_type"],
                    "user_email": user_record["target_email"],
                    "ip_address": None,  # IP 정보는 스키마에 없음
                    "response_time_minutes": user_record["response_time_minutes"],
                    "score_impact": (-0.5 if user_record["training_result"] == "fail"
                                     and not user_record["exclude_from_scoring"] else
                                     0),
                    "notes": user_record["notes"],
                    "exclude_from_scoring": user_record["exclude_from_scoring"],
                    "exclude_reason": user_record["exclude_reason"],
                }
            else:
                # 훈련 기록이 없는 경우
                current_date = datetime.now().date()
                period_start = period["start_date"] if period["start_date"] else None
                period_end = period["end_date"] if period["end_date"] else None

                if period["is_completed"]:
                    result = "pass"  # 완료된 기간은 자동 통과
                elif period_end and current_date > period_end:
                    result = "pending"  # 기간이 지났지만 기록 없음
                elif period_start and current_date < period_start:
                    result = "not_started"  # 아직 시작 안됨
                else:
                    result = "pending"  # 진행 중

                period_data = {
                    "period": f"period_{period['period_id']}",
                    "period_name": period["period_name"],
                    "training_year": year,
                    "start_date": (period_start.strftime("%Y-%m-%d")
                                   if period_start else None),
                    "end_date": period_end.strftime("%Y-%m-%d") if period_end else None,
                    "result": result,
                    "email_sent_time": None,
                    "action_time": None,
                    "log_type": None,
                    "mail_type": None,
                    "user_email": None,
                    "ip_address": None,
                    "response_time_minutes": None,
                    "score_impact": 0,
                    "notes": ("훈련이 실시되지 않았습니다." if result == "pending" else None),
                    "exclude_from_scoring": False,
                    "exclude_reason": None,
                }

            period_status.append(period_data)

        return period_status

    def get_training_records(
        self,
        year: int,
        period_id: Optional[int] = None,
        training_type: Optional[str] = None,
        result_filter: Optional[str] = None,
        search_query: str = "",
        page: int = 1,
        per_page: int = 20,
    ) -> Dict[str, Any]:
        """훈련 기록 목록 조회 (관리자용)"""
        try:
            # 기본 쿼리
            base_query = """
            SELECT 
                pt.training_id,
                pt.user_id,
                u.username,
                u.department,
                pt.period_id,
                ptp.period_name,
                ptp.training_type,
                ptp.is_completed as period_is_completed,
                pt.target_email,
                pt.mail_type,
                pt.log_type,
                pt.email_sent_time,
                pt.action_time,
                pt.training_result,
                pt.response_time_minutes,
                pt.exclude_from_scoring,
                pt.exclude_reason,
                pt.notes,
                pt.created_at,
                pt.updated_at
            FROM phishing_training pt
            JOIN users u ON pt.user_id = u.uid
            JOIN phishing_training_periods ptp ON pt.period_id = ptp.period_id
            WHERE pt.training_year = %s
            """

            # 필터 조건 추가
            conditions = [year]

            if period_id:
                base_query += " AND pt.period_id = %s"
                conditions.append(period_id)

            if training_type:
                base_query += " AND ptp.training_type = %s"
                conditions.append(training_type)

            if result_filter:
                base_query += " AND pt.training_result = %s"
                conditions.append(result_filter)

            if search_query:
                base_query += " AND (u.username LIKE %s OR u.department LIKE %s OR pt.target_email LIKE %s OR pt.mail_type LIKE %s)"
                search_pattern = f"%{search_query}%"
                conditions.extend(
                    [search_pattern, search_pattern, search_pattern, search_pattern])

            # 전체 레코드 수 조회
            count_query = f"SELECT COUNT(*) as total FROM ({base_query}) as count_query"
            total_count = execute_query(count_query, conditions,
                                        fetch_one=True)["total"]

            # 페이지네이션 적용
            offset = (page - 1) * per_page
            base_query += " ORDER BY pt.email_sent_time DESC LIMIT %s OFFSET %s"
            conditions.extend([per_page, offset])

            records = execute_query(base_query, conditions, fetch_all=True)

            return {
                "records": [self._format_record(record) for record in records],
                "pagination": {
                    "total": total_count,
                    "page": page,
                    "per_page": per_page,
                    "total_pages": (total_count + per_page - 1) // per_page,
                },
            }

        except Exception as e:
            logger.error(f"훈련 기록 조회 오류: {str(e)}")
            raise

    def _format_record(self, record: Dict) -> Dict:
        """레코드 포맷팅"""
        return {
            "training_id": record["training_id"],
            "user_id": record["user_id"],
            "username": record["username"],
            "department": record["department"],
            "period_id": record["period_id"],
            "period_name": record["period_name"],
            "training_type": record["training_type"],
            "period_is_completed": bool(record.get("period_is_completed", False)),
            "target_email": record["target_email"],
            "mail_type": record["mail_type"],
            "log_type": record["log_type"],
            "email_sent_time": (record["email_sent_time"].isoformat()
                                if record["email_sent_time"] else None),
            "action_time": (record["action_time"].isoformat()
                            if record["action_time"] else None),
            "training_result": record["training_result"],
            "response_time_minutes": record["response_time_minutes"],
            "exclude_from_scoring": bool(record["exclude_from_scoring"]),
            "exclude_reason": record["exclude_reason"],
            "notes": record["notes"],
            "created_at": (record["created_at"].isoformat()
                           if record["created_at"] else None),
            "updated_at": (record["updated_at"].isoformat()
                           if record["updated_at"] else None),
        }

    def update_training_record(self, record_id: int, data: Dict[str,
                                                                Any]) -> Dict[str, Any]:
        """
        훈련 기록 수정 (모든 편집 가능 필드 지원)
        - 편집 가능: target_email, mail_type, log_type, email_sent_time, action_time,
                     training_result, exclude_from_scoring, exclude_reason, notes
        - 발송/수행시각이 모두 있으면 응답 시간 자동 재계산
        """
        try:
            # 기록 존재 확인
            record = self._get_record_by_id(record_id)
            if not record:
                return {"success": False, "error": "훈련 기록을 찾을 수 없습니다."}

            update_fields = []
            values = []

            # 문자열 필드 (빈 문자열은 None으로 저장)
            string_fields = ["target_email", "mail_type", "log_type", "notes", "exclude_reason"]
            for field in string_fields:
                if field in data:
                    update_fields.append(f"{field} = %s")
                    val = data[field]
                    values.append(val if val else None)

            # 날짜시간 필드
            datetime_fields = ["email_sent_time", "action_time"]
            for field in datetime_fields:
                if field in data:
                    update_fields.append(f"{field} = %s")
                    values.append(self._parse_datetime_for_update(data[field]))

            # 훈련 결과
            if "training_result" in data:
                result_value = data["training_result"]
                if result_value not in ("success", "fail", "no_response"):
                    return {"success": False, "error": "훈련결과 값이 올바르지 않습니다."}
                update_fields.append("training_result = %s")
                values.append(result_value)

            # 제외 여부
            if "exclude_from_scoring" in data:
                update_fields.append("exclude_from_scoring = %s")
                values.append(1 if data["exclude_from_scoring"] else 0)

            # 발송/수행시각이 모두 있으면 응답시간 재계산
            sent_time = self._parse_datetime_for_update(
                data.get("email_sent_time") if "email_sent_time" in data
                else record.get("email_sent_time")
            )
            acted_time = self._parse_datetime_for_update(
                data.get("action_time") if "action_time" in data
                else record.get("action_time")
            )

            if sent_time and acted_time:
                try:
                    diff = (acted_time - sent_time).total_seconds()
                    if diff > 0:
                        update_fields.append("response_time_minutes = %s")
                        values.append(int(diff / 60))
                    else:
                        update_fields.append("response_time_minutes = %s")
                        values.append(None)
                except Exception:
                    pass
            elif "email_sent_time" in data or "action_time" in data:
                # 한쪽만 지정된 경우 응답시간 초기화
                update_fields.append("response_time_minutes = %s")
                values.append(None)

            if not update_fields:
                return {"success": False, "error": "수정할 필드가 지정되지 않았습니다."}

            update_fields.append("updated_at = NOW()")
            values.append(record_id)

            query = f"""
            UPDATE phishing_training 
            SET {', '.join(update_fields)}
            WHERE training_id = %s
            """

            execute_query(query, values)

            return {"success": True, "message": "훈련 기록이 수정되었습니다."}

        except Exception as e:
            logger.error(f"훈련 기록 수정 오류: {str(e)}")
            return {
                "success": False,
                "error": f"기록 수정 중 오류가 발생했습니다: {str(e)}",
            }

    def _parse_datetime_for_update(self, value):
        """업데이트용 datetime 파싱 (ISO, YYYY-MM-DD HH:MM:SS 등)"""
        if not value:
            return None
        try:
            if hasattr(value, 'isoformat'):
                return value
            s = str(value).strip()
            if not s:
                return None
            # ISO 8601 (2025-06-02T09:30:00.000Z 또는 2025-06-02T09:30:00)
            s = s.replace("Z", "").replace("T", " ")
            if "+" in s:
                s = s.split("+")[0]
            if "." in s:
                s = s.split(".")[0]
            # 여러 포맷 시도
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"]:
                try:
                    return datetime.strptime(s, fmt)
                except ValueError:
                    continue
            return None
        except Exception:
            return None

    def toggle_record_exclude(self, record_id: int, exclude: bool,
                              reason: str = "") -> Dict[str, Any]:
        """훈련 기록 제외/포함 토글"""
        try:
            record = self._get_record_by_id(record_id)
            if not record:
                return {"success": False, "error": "훈련 기록을 찾을 수 없습니다."}

            query = """
            UPDATE phishing_training 
            SET exclude_from_scoring = %s, exclude_reason = %s, updated_at = NOW()
            WHERE training_id = %s
            """

            execute_query(query, (exclude, reason if exclude else None, record_id))

            action = "제외" if exclude else "포함"
            return {
                "success": True,
                "message": f"훈련 기록이 점수 계산에서 {action} 처리되었습니다.",
            }

        except Exception as e:
            logger.error(f"훈련 기록 제외/포함 처리 오류: {str(e)}")
            return {"success": False, "error": f"처리 중 오류가 발생했습니다: {str(e)}"}

    def delete_training_record(self, record_id: int) -> Dict[str, Any]:
        """훈련 기록 삭제"""
        try:
            record = self._get_record_by_id(record_id)
            if not record:
                return {"success": False, "error": "훈련 기록을 찾을 수 없습니다."}

            query = "DELETE FROM phishing_training WHERE training_id = %s"
            execute_query(query, (record_id, ))

            return {"success": True, "message": "훈련 기록이 삭제되었습니다."}

        except Exception as e:
            logger.error(f"훈련 기록 삭제 오류: {str(e)}")
            return {"success": False, "error": f"삭제 중 오류가 발생했습니다: {str(e)}"}

    def _get_record_by_id(self, record_id: int) -> Optional[Dict]:
        """ID로 훈련 기록 조회"""
        query = "SELECT * FROM phishing_training WHERE training_id = %s"
        return execute_query(query, (record_id, ), fetch_one=True)

    def process_excel_upload(self, file: FileStorage, period_id: int) -> Dict[str, Any]:
        """엑셀 파일 업로드 처리"""
        try:
            # 기간 정보 확인
            period_query = """
            SELECT period_id, training_year, period_name, training_type, is_completed
            FROM phishing_training_periods WHERE period_id = %s
            """
            period = execute_query(period_query, (period_id, ), fetch_one=True)

            if not period:
                return {
                    "success": False,
                    "error": "선택한 훈련 기간을 찾을 수 없습니다.",
                }

            if period["is_completed"]:
                return {
                    "success": False,
                    "error": "완료된 훈련 기간에는 데이터를 업로드할 수 없습니다.",
                }

            # 엑셀 파일 읽기
            df = pd.read_excel(file, engine="openpyxl")

            # 필수 컬럼 확인
            required_columns = [
                "메일발송시각",
                "수행시각",
                "로그유형",
                "메일유형",
                "이메일",
            ]
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                return {
                    "success": False,
                    "error": f"필수 컬럼이 누락되었습니다: {', '.join(missing_columns)}",
                }

            # 데이터 처리
            success_count = 0
            error_count = 0
            errors = []

            for index, row in df.iterrows():
                try:
                    # 이메일로 사용자 찾기
                    target_email = str(row["이메일"]).strip()
                    user_query = "SELECT uid FROM users WHERE mail = %s"
                    user = execute_query(user_query, (target_email, ), fetch_one=True)

                    if not user:
                        error_count += 1
                        errors.append(f"행 {index+2}: 사용자를 찾을 수 없습니다 ({target_email})")
                        continue

                    # 중복 체크
                    duplicate_query = """
                    SELECT COUNT(*) as count FROM phishing_training 
                    WHERE user_id = %s AND period_id = %s AND target_email = %s
                    """
                    duplicate = execute_query(
                        duplicate_query,
                        (user["uid"], period_id, target_email),
                        fetch_one=True,
                    )

                    if duplicate["count"] > 0:
                        error_count += 1
                        errors.append(f"행 {index+2}: 중복된 기록입니다 ({target_email})")
                        continue

                    # 훈련 결과 판정
                    training_result = self._determine_training_result(row)

                    # 응답 시간 계산
                    response_time = self._calculate_response_time(row)

                    # 데이터 삽입
                    insert_query = """
                    INSERT INTO phishing_training 
                    (user_id, period_id, training_year, email_sent_time, action_time, 
                     log_type, mail_type, target_email, training_result, response_time_minutes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """

                    values = (
                        user["uid"],
                        period_id,
                        period["training_year"],
                        (pd.to_datetime(row["메일발송시각"])
                         if pd.notna(row["메일발송시각"]) else None),
                        (pd.to_datetime(row["수행시각"])
                         if pd.notna(row["수행시각"]) else None),
                        str(row["로그유형"]),
                        str(row["메일유형"]),
                        target_email,
                        training_result,
                        response_time,
                    )

                    execute_query(insert_query, values)
                    success_count += 1

                except Exception as e:
                    error_count += 1
                    errors.append(f"행 {index+2}: {str(e)}")
                    logger.error(f"데이터 처리 오류 (행 {index+2}): {str(e)}")

            return {
                "success": True,
                "message": f"총 {len(df)}건 중 {success_count}건 성공, {error_count}건 실패",
                "details": {
                    "total_rows": len(df),
                    "success_count": success_count,
                    "error_count": error_count,
                    "errors": errors[:10],  # 최대 10개 오류만 반환
                },
            }

        except Exception as e:
            logger.error(f"엑셀 업로드 오류: {str(e)}")
            return {
                "success": False,
                "error": f"파일 처리 중 오류가 발생했습니다: {str(e)}",
            }

    def _determine_training_result(self, row: pd.Series) -> str:
        """훈련 결과 판정 로직 - 간소화된 버전"""

        # 로그 유형 확인
        log_type = row.get("로그유형", "")

        # None이나 NaN 처리
        if pd.isna(log_type):
            log_type = ""
        else:
            log_type = str(log_type).strip()

        # 수행시각 확인 (무응답 처리용)
        action_time = row.get("수행시각", "")
        if pd.isna(action_time):
            action_time = ""
        else:
            action_time = str(action_time).strip()

        # 판정 로직
        if not log_type or log_type == "":
            # 로그 유형이 없으면 무응답
            return "no_response"
        else:
            # 로그 유형이 있으면 무조건 실패 (피싱에 걸림)
            return "fail"

    def _calculate_response_time(self, row: pd.Series) -> Optional[int]:
        """응답 시간 계산 (분 단위)"""
        try:
            if pd.isna(row["메일발송시각"]) or pd.isna(row["수행시각"]):
                return None

            sent_time = pd.to_datetime(row["메일발송시각"])
            action_time = pd.to_datetime(row["수행시각"])

            if action_time <= sent_time:
                return 0

            diff = action_time - sent_time
            return int(diff.total_seconds() / 60)

        except Exception:
            return None

    def get_upload_template(self) -> str:
        """
        업로드용 CSV 템플릿 생성
        - 필수: 이름, 부서, 훈련결과
        - 선택: 메일유형, 로그유형, 발송시각, 수행시각
          → 비워둬도 업로드 가능, 업로드 후 수정 모달에서 보완
        - 예시: 실패/무응답 케이스 (통과는 기본값이므로 제외)
        """
        template_content = """이름,부서,훈련결과,메일유형,로그유형,발송시각,수행시각
홍길동,개발팀,실패,세금계산서,링크 클릭,2025-06-02 09:30:00,2025-06-02 14:20:00
김철수,인사팀,실패,퇴직연금 운용,첨부파일 열람,2025-06-02 09:30:00,
이영희,마케팅팀,무응답,,,,"""

        return template_content

    def _find_user_by_name_dept(self, username: str, department: str = "") -> Optional[int]:
        """
        유연한 사용자 검색 로직 (교육 관리와 동일한 3단계 폴백)
        1차: 이름 + 부서 정확 매칭
        2차: 이름만 정확 매칭
        3차: 이름 유사(LIKE) 매칭
        """
        username = (username or "").strip()
        department = (department or "").strip()

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
                self.logger.info(f"[매칭] 이름+부서 정확: {username} ({department})")
                return user["uid"]

        # 2. 정확한 이름만 매칭 (부서 무시)
        user = execute_query(
            "SELECT uid, department FROM users WHERE username = %s LIMIT 1",
            (username,),
            fetch_one=True,
        )
        if user:
            self.logger.info(f"[매칭] 이름 정확: {username} (실제 부서: {user['department']})")
            return user["uid"]

        # 3. 유사 이름 검색
        user = execute_query(
            "SELECT uid, username, department FROM users WHERE username LIKE %s LIMIT 1",
            (f"%{username}%",),
            fetch_one=True,
        )
        if user:
            self.logger.info(f"[매칭] 이름 유사: {username} -> {user['username']}")
            return user["uid"]

        self.logger.warning(f"[매칭 실패] 사용자를 찾을 수 없음: {username} ({department})")
        return None

    def preflight_bulk_upload(self, period_id: int, records: List[Dict]) -> Dict[str, Any]:
        """
        일괄 업로드 사전 검증 (실제 DB 저장 없음)
        각 레코드에 대해 (사용자 매칭 가능 여부 + 신규/업데이트 구분) 판정
        """
        try:
            # 기간 확인
            period = execute_query(
                "SELECT period_id, training_year, period_name, training_type, is_completed FROM phishing_training_periods WHERE period_id = %s",
                (period_id,),
                fetch_one=True,
            )

            if not period:
                return {"success": False, "error": "선택한 훈련 기간을 찾을 수 없습니다."}

            will_create = 0
            will_update = 0
            not_found = []
            update_targets = []  # 덮어쓰기 대상 미리보기

            for idx, record in enumerate(records):
                row_num = idx + 2
                username = str(record.get("이름") or record.get("username") or "").strip()
                department = str(record.get("부서") or record.get("department") or "").strip()

                if not username:
                    continue

                user_uid = self._find_user_by_name_dept(username, department)
                if not user_uid:
                    not_found.append({
                        "row": row_num,
                        "username": username,
                        "department": department or "(부서없음)",
                    })
                    continue

                # 기존 기록 확인
                existing = execute_query(
                    "SELECT training_id FROM phishing_training WHERE user_id = %s AND period_id = %s LIMIT 1",
                    (user_uid, period_id),
                    fetch_one=True,
                )

                if existing:
                    will_update += 1
                    if len(update_targets) < 10:  # 샘플 최대 10건
                        update_targets.append(f"{username} ({department or '부서없음'})")
                else:
                    will_create += 1

            return {
                "success": True,
                "period_name": period["period_name"],
                "period_completed": bool(period["is_completed"]),
                "total": len(records),
                "will_create": will_create,
                "will_update": will_update,
                "not_found_count": len(not_found),
                "not_found_samples": not_found[:10],
                "update_targets": update_targets,
            }

        except Exception as e:
            self.logger.error(f"사전 검증 실패: {str(e)}")
            return {"success": False, "error": str(e)}

    def process_json_upload(self, period_id: int, records: List[Dict], uploaded_by: str = "admin") -> Dict[str, Any]:
        """
        JSON 형식 일괄 업로드 처리 (교육 관리와 동일한 방식)
        - 클라이언트에서 파싱한 레코드를 JSON으로 받음
        - 사용자 식별: 이름 + 부서 (3단계 폴백)
        - 대상 식별자(이메일/전화번호 등)는 기록용
        """
        from datetime import datetime as dt

        success_count = 0
        update_count = 0
        error_count = 0
        errors = []

        try:
            # 1. 기간 정보 검증
            period = execute_query(
                """
                SELECT period_id, training_year, period_name, training_type, is_completed
                FROM phishing_training_periods WHERE period_id = %s
                """,
                (period_id,),
                fetch_one=True,
            )

            if not period:
                return {"success": False, "error": "선택한 훈련 기간을 찾을 수 없습니다."}

            if period["is_completed"]:
                return {"success": False, "error": "완료된 훈련 기간에는 업로드할 수 없습니다."}

            training_year = period["training_year"]

            # 2. 레코드별 처리
            for idx, record in enumerate(records):
                row_num = idx + 2  # 엑셀 행 번호 (헤더 + 1)

                try:
                    # 한글 키 / 영문 키 양쪽 지원
                    username = str(record.get("이름") or record.get("username") or "").strip()
                    department = str(record.get("부서") or record.get("department") or "").strip()

                    # 훈련 결과 (필수)
                    training_result_raw = str(
                        record.get("훈련결과") or record.get("결과") or
                        record.get("training_result") or ""
                    ).strip()

                    # 선택 필드 (업로드 후 수정 가능)
                    target = str(record.get("훈련대상") or record.get("target_email") or record.get("이메일") or "").strip()
                    mail_type = str(record.get("메일유형") or record.get("mail_type") or "").strip()
                    log_type = str(record.get("로그유형") or record.get("log_type") or "").strip()
                    email_sent_time_raw = record.get("발송시각") or record.get("메일발송시각") or record.get("email_sent_time")
                    action_time_raw = record.get("수행시각") or record.get("action_time")

                    # 필수 필드 검증
                    if not username:
                        errors.append(f"행 {row_num}: 이름이 누락되었습니다.")
                        error_count += 1
                        continue

                    if not department:
                        errors.append(f"행 {row_num}: 부서가 누락되었습니다.")
                        error_count += 1
                        continue

                    # 사용자 검색 (3단계 폴백)
                    user_uid = self._find_user_by_name_dept(username, department)
                    if not user_uid:
                        errors.append(f"행 {row_num}: 사용자를 찾을 수 없습니다 ({username}, {department})")
                        error_count += 1
                        continue

                    # 날짜 파싱
                    email_sent_time = self._parse_datetime(email_sent_time_raw)
                    action_time = self._parse_datetime(action_time_raw)

                    # 훈련 결과 결정
                    # 1) 명시된 훈련결과가 있으면 정규화하여 사용
                    # 2) 없으면 로그유형 + 수행시각으로 자동 판정
                    training_result = self._normalize_training_result(training_result_raw)
                    if not training_result:
                        training_result = self._determine_result_by_log_type(log_type, action_time)

                    if training_result not in ("success", "fail", "no_response"):
                        errors.append(f"행 {row_num}: 훈련결과 값이 올바르지 않습니다 ('{training_result_raw}')")
                        error_count += 1
                        continue

                    # 응답 시간 계산
                    response_time = None
                    if email_sent_time and action_time:
                        try:
                            diff = (action_time - email_sent_time).total_seconds()
                            if diff > 0:
                                response_time = int(diff / 60)
                        except Exception:
                            pass

                    # UPSERT: 동일한 (user_id, period_id) 조합이 있으면 업데이트
                    # target_email은 선택 필드라 중복 키에서 제외
                    existing = execute_query(
                        """
                        SELECT training_id FROM phishing_training
                        WHERE user_id = %s AND period_id = %s
                        LIMIT 1
                        """,
                        (user_uid, period_id),
                        fetch_one=True,
                    )

                    if existing:
                        # 기존 레코드 업데이트 (빈 값은 덮어쓰지 않도록 COALESCE 처리)
                        execute_query(
                            """
                            UPDATE phishing_training
                            SET training_result = %s,
                                target_email = COALESCE(NULLIF(%s, ''), target_email),
                                mail_type = COALESCE(NULLIF(%s, ''), mail_type),
                                log_type = COALESCE(NULLIF(%s, ''), log_type),
                                email_sent_time = COALESCE(%s, email_sent_time),
                                action_time = COALESCE(%s, action_time),
                                response_time_minutes = COALESCE(%s, response_time_minutes),
                                updated_at = NOW()
                            WHERE training_id = %s
                            """,
                            (training_result, target, mail_type, log_type,
                             email_sent_time, action_time, response_time,
                             existing["training_id"]),
                        )
                        update_count += 1
                    else:
                        execute_query(
                            """
                            INSERT INTO phishing_training
                                (user_id, period_id, training_year, target_email,
                                 mail_type, log_type, email_sent_time, action_time,
                                 training_result, response_time_minutes)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """,
                            (user_uid, period_id, training_year,
                             target or None, mail_type or None, log_type or None,
                             email_sent_time, action_time,
                             training_result, response_time),
                        )
                        success_count += 1

                except Exception as e:
                    error_count += 1
                    errors.append(f"행 {row_num}: 처리 중 오류 - {str(e)}")
                    self.logger.error(f"레코드 처리 오류 (행 {row_num}): {str(e)}")

            return {
                "success": True,
                "success_count": success_count,
                "update_count": update_count,
                "error_count": error_count,
                "total_count": len(records),
                "errors": errors[:10],
                "message": f"총 {len(records)}건 중 {success_count}건 신규, {update_count}건 업데이트, {error_count}건 실패",
            }

        except Exception as e:
            self.logger.error(f"JSON 일괄 업로드 실패: {str(e)}")
            return {"success": False, "error": f"업로드 처리 실패: {str(e)}"}

    def _parse_datetime(self, value):
        """날짜 문자열/Date → datetime 객체 변환"""
        if not value:
            return None
        try:
            from datetime import datetime as dt
            if hasattr(value, 'isoformat'):
                return value
            s = str(value).strip().replace("Z", "").replace("T", " ")
            if "+" in s:
                s = s.split("+")[0]
            # 다양한 포맷 시도
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d"]:
                try:
                    return dt.strptime(s, fmt)
                except ValueError:
                    continue
            return None
        except Exception:
            return None

    def _normalize_training_result(self, value: str) -> Optional[str]:
        """훈련결과 문자열을 DB 값(success/fail/no_response)으로 정규화"""
        if not value:
            return None

        v = str(value).strip().lower()

        # 성공(통과)
        success_aliases = {"success", "pass", "성공", "통과", "완료", "ok", "o", "정상", "안전"}
        if v in success_aliases:
            return "success"

        # 실패
        fail_aliases = {"fail", "failed", "실패", "미흡", "낚임", "클릭", "x"}
        if v in fail_aliases:
            return "fail"

        # 무응답
        no_response_aliases = {"no_response", "noresponse", "none", "무응답", "미응답", "미실시", "-"}
        if v in no_response_aliases:
            return "no_response"

        return None  # 알 수 없는 값

    def _determine_result_by_log_type(self, log_type: str, action_time) -> str:
        """로그유형 + 수행시각으로 훈련 결과 자동 판정"""
        if not log_type or not log_type.strip():
            return "no_response" if not action_time else "fail"

        lt = log_type.lower()
        # 실패 패턴 (피싱에 걸린 경우)
        fail_patterns = [
            "첨부파일 열람", "첨부파일 실행", "링크 클릭", "스크립트 실행",
            "매크로 실행", "다운로드", "통화 응답", "답장",
            "attachment", "click", "download", "execute",
        ]
        if any(p in lt for p in fail_patterns):
            return "fail"

        # 성공 패턴 (단순 열람만)
        success_patterns = ["이메일 열람", "메일 읽기", "열람만", "view", "read"]
        if any(p in lt for p in success_patterns):
            return "success"

        # 기본적으로 실패 (보수적)
        return "fail"

    def add_single_record(self, data: dict) -> dict:
        """
        단일 훈련 기록 등록
        - 필수: period_id, user_id, training_result
        - 선택 필드는 비워도 됨 (업로드 후 수정 모달에서 보완)
        """
        try:
            period_id = data["period_id"]
            user_id = data["user_id"]
            training_result = data.get("training_result", "fail")

            # 기간 정보 조회
            period = execute_query(
                "SELECT training_year, training_type, is_completed FROM phishing_training_periods WHERE period_id = %s",
                (period_id,),
                fetch_one=True,
            )

            if not period:
                return {"success": False, "error": "훈련 기간을 찾을 수 없습니다."}

            if period["is_completed"]:
                return {"success": False, "error": "완료된 훈련 기간에는 기록을 추가할 수 없습니다."}

            training_year = period["training_year"]

            # 중복 체크 (user_id + period_id 기준 - 일괄 업로드와 동일한 키)
            existing = execute_query(
                """
                SELECT training_id FROM phishing_training
                WHERE user_id = %s AND period_id = %s
                LIMIT 1
                """,
                (user_id, period_id),
                fetch_one=True,
            )

            if existing:
                return {
                    "success": False,
                    "error": "해당 사용자의 훈련 기록이 이미 존재합니다. 기존 기록을 수정해주세요.",
                }

            # INSERT (선택 필드는 NULL)
            execute_query(
                """
                INSERT INTO phishing_training 
                    (user_id, training_year, period_id, training_result)
                VALUES (%s, %s, %s, %s)
                """,
                (user_id, training_year, period_id, training_result),
            )

            return {"success": True, "message": "훈련 기록이 등록되었습니다."}

        except Exception as e:
            self.logger.error(f"단일 기록 등록 오류: {str(e)}")
            return {"success": False, "error": str(e)}

    def export_training_data(self, year: int,
                             format_type: str = "csv") -> Dict[str, Any]:
        """훈련 데이터 내보내기"""
        try:
            query = """
            SELECT 
                u.username as '사용자명',
                u.department as '부서',
                ptp.period_name as '훈련기간',
                ptp.training_type as '훈련유형',
                pt.target_email as '대상이메일',
                pt.mail_type as '메일유형',
                pt.log_type as '로그유형',
                pt.email_sent_time as '발송시각',
                pt.action_time as '수행시각',
                pt.response_time_minutes as '응답시간_분',
                CASE pt.training_result
                    WHEN 'success' THEN '성공'
                    WHEN 'fail' THEN '실패'
                    WHEN 'no_response' THEN '무응답'
                    ELSE pt.training_result
                END as '훈련결과',
                CASE pt.exclude_from_scoring
                    WHEN 1 THEN '제외'
                    ELSE '포함'
                END as '점수계산포함여부',
                pt.exclude_reason as '제외사유',
                pt.notes as '비고'
            FROM phishing_training pt
            JOIN users u ON pt.user_id = u.uid
            JOIN phishing_training_periods ptp ON pt.period_id = ptp.period_id
            WHERE pt.training_year = %s
            ORDER BY u.department, u.username, pt.email_sent_time
            """

            records = execute_query(query, (year, ), fetch_all=True)

            if not records:
                return {"success": False, "error": "내보낼 데이터가 없습니다."}

            if format_type == "csv":
                # CSV 생성
                output = io.StringIO()
                fieldnames = records[0].keys()
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(records)

                csv_content = output.getvalue()
                output.close()

                return {
                    "success": True,
                    "data": csv_content.encode("utf-8-sig"),  # BOM 추가로 한글 깨짐 방지
                    "content_type": "text/csv; charset=utf-8-sig",
                    "filename": (
                        f"attachment; "
                        f"filename=\"phishing_training_{year}.csv\"; "
                        f"filename*=UTF-8''{quote(f'피싱훈련데이터_{year}.csv'.encode('utf-8'))}"
                    ),
                }

            else:
                return {"success": False, "error": "지원하지 않는 형식입니다."}

        except Exception as e:
            logger.error(f"데이터 내보내기 오류: {str(e)}")
            return {
                "success": False,
                "error": f"내보내기 중 오류가 발생했습니다: {str(e)}",
            }

    def get_training_statistics(self, year: int,
                                period_id: Optional[int] = None) -> Dict[str, Any]:
        """훈련 통계 조회"""
        try:
            base_query = """
            SELECT 
                ptp.period_name,
                ptp.training_type,
                u.department,
                COUNT(*) as total_count,
                COUNT(CASE WHEN pt.training_result = 'success' AND pt.exclude_from_scoring = 0 THEN 1 END) as success_count,
                COUNT(CASE WHEN pt.training_result = 'fail' AND pt.exclude_from_scoring = 0 THEN 1 END) as fail_count,
                COUNT(CASE WHEN pt.training_result = 'no_response' AND pt.exclude_from_scoring = 0 THEN 1 END) as no_response_count,
                COUNT(CASE WHEN pt.exclude_from_scoring = 1 THEN 1 END) as excluded_count
            FROM phishing_training pt
            JOIN users u ON pt.user_id = u.uid
            JOIN phishing_training_periods ptp ON pt.period_id = ptp.period_id
            WHERE pt.training_year = %s
            """

            conditions = [year]

            if period_id:
                base_query += " AND pt.period_id = %s"
                conditions.append(period_id)

            base_query += """
            GROUP BY ptp.period_name, ptp.training_type, u.department
            ORDER BY ptp.period_name, u.department
            """

            statistics = execute_query(base_query, conditions, fetch_all=True)

            # 부서별, 기간별 통계 정리
            result = {
                "overall": {
                    "total_participants": 0,
                    "total_success": 0,
                    "total_fail": 0,
                    "total_no_response": 0,
                    "total_excluded": 0,
                    "overall_success_rate": 0,
                },
                "by_period": {},
                "by_department": {},
                "detailed_stats": statistics,
            }

            department_stats = {}
            period_stats = {}

            for stat in statistics:
                # 전체 통계 누적
                scored_count = stat["total_count"] - stat["excluded_count"]
                result["overall"]["total_participants"] += stat["total_count"]
                result["overall"]["total_success"] += stat["success_count"]
                result["overall"]["total_fail"] += stat["fail_count"]
                result["overall"]["total_no_response"] += stat["no_response_count"]
                result["overall"]["total_excluded"] += stat["excluded_count"]

                # 기간별 통계
                period_key = f"{stat['period_name']} ({stat['training_type']})"
                if period_key not in period_stats:
                    period_stats[period_key] = {
                        "total_participants": 0,
                        "success_count": 0,
                        "fail_count": 0,
                        "no_response_count": 0,
                        "excluded_count": 0,
                        "success_rate": 0,
                    }

                period_stats[period_key]["total_participants"] += stat["total_count"]
                period_stats[period_key]["success_count"] += stat["success_count"]
                period_stats[period_key]["fail_count"] += stat["fail_count"]
                period_stats[period_key]["no_response_count"] += stat[
                    "no_response_count"]
                period_stats[period_key]["excluded_count"] += stat["excluded_count"]

                # 부서별 통계
                dept = stat["department"]
                if dept not in department_stats:
                    department_stats[dept] = {
                        "total_participants": 0,
                        "success_count": 0,
                        "fail_count": 0,
                        "no_response_count": 0,
                        "excluded_count": 0,
                        "success_rate": 0,
                    }

                department_stats[dept]["total_participants"] += stat["total_count"]
                department_stats[dept]["success_count"] += stat["success_count"]
                department_stats[dept]["fail_count"] += stat["fail_count"]
                department_stats[dept]["no_response_count"] += stat["no_response_count"]
                department_stats[dept]["excluded_count"] += stat["excluded_count"]

            # 성공률 계산
            total_scored = (result["overall"]["total_participants"] -
                            result["overall"]["total_excluded"])
            if total_scored > 0:
                result["overall"]["overall_success_rate"] = round(
                    (result["overall"]["total_success"] / total_scored) * 100, 2)

            # 기간별 성공률 계산
            for period_key in period_stats:
                period_data = period_stats[period_key]
                scored = (period_data["total_participants"] -
                          period_data["excluded_count"])
                if scored > 0:
                    period_data["success_rate"] = round(
                        (period_data["success_count"] / scored) * 100, 2)

            # 부서별 성공률 계산
            for dept in department_stats:
                dept_data = department_stats[dept]
                scored = dept_data["total_participants"] - dept_data["excluded_count"]
                if scored > 0:
                    dept_data["success_rate"] = round(
                        (dept_data["success_count"] / scored) * 100, 2)

            result["by_period"] = period_stats
            result["by_department"] = department_stats

            return result

        except Exception as e:
            logger.error(f"훈련 통계 조회 오류: {str(e)}")
            raise