# app/services/training_period_service.py
from datetime import datetime, date
from app.utils.database import execute_query, DatabaseManager


class TrainingPeriodService:
    """악성메일 모의훈련 기간 관리 서비스"""

    def get_training_periods(self, year: int = None) -> list:
        """훈련 기간 목록 조회"""
        if year is None:
            year = datetime.now().year

        periods = execute_query(
            """
            SELECT 
                period_id,
                training_year,
                training_period,
                start_date,
                end_date,
                is_completed,
                completed_at,
                completed_by,
                description,
                created_by,
                created_at,
                updated_at,
                is_active
            FROM phishing_training_periods
            WHERE training_year = %s AND is_active = 1
            ORDER BY training_period
            """,
            (year,),
            fetch_all=True,
        )

        # 날짜 포맷팅
        for period in periods:
            if period["start_date"]:
                period["start_date"] = period["start_date"].strftime("%Y-%m-%d")
            if period["end_date"]:
                period["end_date"] = period["end_date"].strftime("%Y-%m-%d")
            if period["completed_at"]:
                period["completed_at"] = period["completed_at"].strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            if period["created_at"]:
                period["created_at"] = period["created_at"].strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            if period["updated_at"]:
                period["updated_at"] = period["updated_at"].strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

        return periods

    def create_training_period(self, data: dict, created_by: str) -> bool:
        """훈련 기간 생성"""
        try:
            result = execute_query(
                """
                INSERT INTO phishing_training_periods 
                (training_year, training_period, start_date, end_date, description, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    data["training_year"],
                    data["training_period"],
                    data["start_date"],
                    data["end_date"],
                    data.get("description", ""),
                    created_by,
                ),
            )
            return result > 0
        except Exception as e:
            raise ValueError(f"기간 생성 실패: {str(e)}")

    def update_training_period(self, period_id: int, data: dict) -> bool:
        """훈련 기간 수정"""
        try:
            result = execute_query(
                """
                UPDATE phishing_training_periods
                SET start_date = %s, end_date = %s, description = %s, updated_at = NOW()
                WHERE period_id = %s AND is_active = 1
                """,
                (
                    data["start_date"],
                    data["end_date"],
                    data.get("description", ""),
                    period_id,
                ),
            )
            return result > 0
        except Exception as e:
            raise ValueError(f"기간 수정 실패: {str(e)}")

    def delete_training_period(self, period_id: int) -> bool:
        """훈련 기간 삭제 (하드 삭제로 변경)"""
        try:
            with DatabaseManager.get_db_cursor() as cursor:
                # 1. 기간 정보 조회
                cursor.execute(
                    """
                    SELECT training_year, training_period
                    FROM phishing_training_periods
                    WHERE period_id = %s AND is_active = 1
                    """,
                    (period_id,),
                )
                period_info = cursor.fetchone()

                if not period_info:
                    raise ValueError("해당 기간을 찾을 수 없습니다.")

                # 2. 관련 훈련 기록 삭제
                cursor.execute(
                    """
                    DELETE FROM phishing_training
                    WHERE training_year = %s AND training_period = %s
                    """,
                    (period_info["training_year"], period_info["training_period"]),
                )

                # 3. 기간 레코드 하드 삭제
                cursor.execute(
                    "DELETE FROM phishing_training_periods WHERE period_id = %s",
                    (period_id,),
                )

                return True
        except Exception as e:
            raise ValueError(f"기간 삭제 실패: {str(e)}")

    def complete_training_period(self, period_id: int, completed_by: str) -> bool:
        """훈련 기간 완료 처리"""
        try:
            with DatabaseManager.get_db_cursor() as cursor:
                # 1. 기간 정보 조회
                cursor.execute(
                    """
                    SELECT training_year, training_period, is_completed
                    FROM phishing_training_periods
                    WHERE period_id = %s AND is_active = 1
                    """,
                    (period_id,),
                )
                period_info = cursor.fetchone()

                if not period_info:
                    raise ValueError("해당 기간을 찾을 수 없습니다.")

                if period_info["is_completed"]:
                    raise ValueError("이미 완료된 기간입니다.")

                # 2. 기간 완료 처리
                cursor.execute(
                    """
                    UPDATE phishing_training_periods
                    SET is_completed = 1, completed_at = NOW(), completed_by = %s, updated_at = NOW()
                    WHERE period_id = %s
                    """,
                    (completed_by, period_id),
                )

                # 3. 기존 pending 레코드들을 pass로 변경
                cursor.execute(
                    """
                    UPDATE phishing_training
                    SET training_result = 'pass', updated_at = NOW()
                    WHERE training_year = %s 
                    AND training_period = %s 
                    AND training_result = 'pending'
                    AND log_type IS NULL
                    """,
                    (period_info["training_year"], period_info["training_period"]),
                )

                # 4. 🔥 NEW: 훈련 기록이 없는 사용자들을 위해 pass 레코드 생성
                cursor.execute(
                    """
                    INSERT INTO phishing_training 
                    (user_id, training_year, training_period, training_result, notes, created_at, updated_at)
                    SELECT 
                        u.uid,
                        %s,
                        %s,
                        'pass',
                        '기간 완료로 인한 자동 통과 처리',
                        NOW(),
                        NOW()
                    FROM users u
                    WHERE u.uid NOT IN (
                        SELECT DISTINCT pt.user_id 
                        FROM phishing_training pt 
                        WHERE pt.training_year = %s 
                        AND pt.training_period = %s
                    )
                    AND u.uid NOT IN (
                        SELECT uee.user_id 
                        FROM user_extended_exceptions uee 
                        WHERE uee.item_id = CONCAT('training_', %s, '_', %s)
                        AND uee.is_active = 1
                    )
                    """,
                    (
                        period_info["training_year"],
                        period_info["training_period"],
                        period_info["training_year"],
                        period_info["training_period"],
                        period_info["training_year"],
                        period_info["training_period"],
                    ),
                )

                return True
        except Exception as e:
            raise ValueError(f"완료 처리 실패: {str(e)}")

    def reopen_training_period(self, period_id: int) -> bool:
        """훈련 기간 재개 (완료 상태 취소)"""
        try:
            with DatabaseManager.get_db_cursor() as cursor:
                # 기간 정보 조회
                cursor.execute(
                    """
                    SELECT training_year, training_period, is_completed
                    FROM phishing_training_periods
                    WHERE period_id = %s AND is_active = 1
                    """,
                    (period_id,),
                )
                period_info = cursor.fetchone()

                if not period_info:
                    raise ValueError("해당 기간을 찾을 수 없습니다.")

                # 완료 처리로 생성된 레코드들만 삭제
                cursor.execute(
                    """
                    DELETE FROM phishing_training
                    WHERE training_year = %s 
                    AND training_period = %s 
                    AND notes = '기간 완료로 인한 자동 통과 처리'
                    """,
                    (period_info["training_year"], period_info["training_period"]),
                )

                # 기간 상태 되돌리기
                cursor.execute(
                    """
                    UPDATE phishing_training_periods
                    SET is_completed = 0, completed_at = NULL, completed_by = NULL, updated_at = NOW()
                    WHERE period_id = %s
                    """,
                    (period_id,),
                )

                return True
        except Exception as e:
            raise ValueError(f"재개 처리 실패: {str(e)}")

    def check_period_exists(self, year: int, period: str) -> bool:
        """기간 중복 체크"""
        result = execute_query(
            """
            SELECT COUNT(*) as count
            FROM phishing_training_periods
            WHERE training_year = %s AND training_period = %s AND is_active = 1
            """,
            (year, period),
            fetch_one=True,
        )
        return result["count"] > 0

    def get_current_period_status(self, year: int = None) -> dict:
        """현재 기간 상태 요약"""
        if year is None:
            year = datetime.now().year

        today = date.today()

        periods = execute_query(
            """
            SELECT 
                period_id,
                training_period,
                start_date,
                end_date,
                completed_at,
                is_completed,
                CASE 
                    WHEN %s BETWEEN start_date AND end_date THEN 'active'
                    WHEN %s < start_date THEN 'upcoming'
                    WHEN %s > end_date THEN 'ended'
                    ELSE 'unknown'
                END as status
            FROM phishing_training_periods
            WHERE training_year = %s AND is_active = 1
            ORDER BY training_period
            """,
            (today, today, today, year),
            fetch_all=True,
        )

        # 통계 정보 조회
        stats = execute_query(
            """
            SELECT 
                training_period,
                COUNT(*) as total_records,
                SUM(CASE WHEN training_result = 'pass' THEN 1 ELSE 0 END) as pass_count,
                SUM(CASE WHEN training_result = 'fail' THEN 1 ELSE 0 END) as fail_count,
                SUM(CASE WHEN training_result = 'pending' THEN 1 ELSE 0 END) as pending_count
            FROM phishing_training
            WHERE training_year = %s
            GROUP BY training_period
            """,
            (year,),
            fetch_all=True,
        )

        # 통계를 딕셔너리로 변환
        stats_dict = {stat["training_period"]: stat for stat in stats}

        # 기간 정보에 통계 추가
        for period in periods:
            period_key = period["training_period"]
            if period_key in stats_dict:
                period.update(stats_dict[period_key])
            else:
                period.update(
                    {
                        "total_records": 0,
                        "pass_count": 0,
                        "fail_count": 0,
                        "pending_count": 0,
                    }
                )

        return {
            "year": year,
            "periods": periods,
            "today": today.strftime("%Y-%m-%d"),
        }
