# app/services/manual_check_period_service.py
from datetime import datetime, date
from app.utils.database import execute_query, DatabaseManager


class ManualCheckPeriodService:
    """수시 점검 기간 관리 서비스"""

    def get_period_status(self, year: int = None) -> dict:
        """연도별 점검 기간 현황 조회"""
        if year is None:
            year = datetime.now().year

        # 기본 점검 유형 정의
        check_types = {
            "seal_check": "PC 봉인씰 확인",
            "malware_scan": "악성코드 전체 검사",
            "file_encryption": "개인정보 파일 암호화",
        }

        result = {"year": year, "check_types": {}}

        for check_type, type_name in check_types.items():
            # 해당 연도/유형의 기간 목록 조회
            periods = execute_query(
                """
                SELECT 
                    period_id,
                    period_name,
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
                FROM manual_check_periods
                WHERE check_type = %s AND period_year = %s AND is_active = 1
                ORDER BY start_date
                """,
                (check_type, year),
                fetch_all=True,
            )

            # 각 기간별 통계 조회
            for period in periods:
                stats = execute_query(
                    """
                    SELECT 
                        COUNT(DISTINCT user_id) as total_users,
                        COALESCE(SUM(CASE WHEN overall_result = 'pass' THEN 1 ELSE 0 END), 0) as pass_count,
                        COALESCE(SUM(CASE WHEN overall_result = 'fail' THEN 1 ELSE 0 END), 0) as fail_count
                    FROM manual_check_results
                    WHERE check_item_code = %s 
                    AND check_year = %s 
                    AND period_id = %s
                    """,
                    (check_type, year, period["period_id"]),
                    fetch_one=True,
                )

                if stats:
                    # None 값을 0으로 변환
                    period.update(
                        {
                            "total_users": stats.get("total_users") or 0,
                            "pass_count": stats.get("pass_count") or 0,
                            "fail_count": stats.get("fail_count") or 0,
                        }
                    )
                else:
                    period.update({"total_users": 0, "pass_count": 0, "fail_count": 0})

                # 날짜 포맷팅
                if period["start_date"]:
                    period["start_date"] = period["start_date"].strftime("%Y-%m-%d")
                if period["end_date"]:
                    period["end_date"] = period["end_date"].strftime("%Y-%m-%d")
                if period["completed_at"]:
                    period["completed_at"] = period["completed_at"].strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )

            result["check_types"][check_type] = {
                "type_name": type_name,
                "periods": periods,
                "total_users": sum(p.get("total_users", 0) or 0 for p in periods),
                "pass_count": sum(p.get("pass_count", 0) or 0 for p in periods),
                "fail_count": sum(p.get("fail_count", 0) or 0 for p in periods),
            }

        return result


    def check_period_overlap(self, check_type: str, start_date, end_date, exclude_period_id=None) -> dict:
        """
        기간 겹침 검사 - 같은 점검 유형에서 날짜 범위가 겹치는 기간이 있는지 확인
        
        Args:
            check_type: 점검 유형 (file_encryption, seal_check, malware_scan)
            start_date: 시작일 (datetime.date 또는 str)
            end_date: 종료일 (datetime.date 또는 str)
            exclude_period_id: 수정 시 제외할 기간 ID (선택사항)
        
        Returns:
            dict: {
                'has_overlap': bool,
                'overlapping_periods': list,
                'message': str
            }
        """
        try:
            from datetime import datetime
            
            # 날짜 타입 변환
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            
            # 기본 쿼리 - 같은 점검 유형의 활성 기간들 조회
            query = """
                SELECT period_id, period_name, start_date, end_date, period_year
                FROM manual_check_periods 
                WHERE check_type = %s 
                AND is_active = 1
            """
            params = [check_type]
            
            # 수정 시 현재 기간 제외
            if exclude_period_id:
                query += " AND period_id != %s"
                params.append(exclude_period_id)
            
            existing_periods = execute_query(query, params, fetch_all=True)
            
            overlapping_periods = []
            
            for period in existing_periods:
                existing_start = period['start_date']
                existing_end = period['end_date']
                
                # 날짜 겹침 검사 로직
                # 경우 1: 새 기간의 시작일이 기존 기간 내에 있는 경우
                # 경우 2: 새 기간의 종료일이 기존 기간 내에 있는 경우  
                # 경우 3: 새 기간이 기존 기간을 완전히 포함하는 경우
                # 경우 4: 기존 기간이 새 기간을 완전히 포함하는 경우
                
                if (
                    # 새 시작일이 기존 기간 내
                    (existing_start <= start_date <= existing_end) or
                    # 새 종료일이 기존 기간 내  
                    (existing_start <= end_date <= existing_end) or
                    # 새 기간이 기존 기간을 포함
                    (start_date <= existing_start and end_date >= existing_end) or
                    # 기존 기간이 새 기간을 포함
                    (existing_start <= start_date and existing_end >= end_date)
                ):
                    overlapping_periods.append({
                        'period_id': period['period_id'],
                        'period_name': period['period_name'],
                        'start_date': existing_start.strftime("%Y-%m-%d"),
                        'end_date': existing_end.strftime("%Y-%m-%d"),
                        'period_year': period['period_year']
                    })
            
            has_overlap = len(overlapping_periods) > 0
            
            if has_overlap:
                # 겹치는 기간들의 정보를 포함한 메시지 생성
                overlap_info = []
                for period in overlapping_periods:
                    overlap_info.append(f"{period['period_year']}년 {period['period_name']} ({period['start_date']} ~ {period['end_date']})")
                
                message = f"다음 기간과 겹칩니다: {', '.join(overlap_info)}"
            else:
                message = "기간 겹침 없음"
            
            return {
                'has_overlap': has_overlap,
                'overlapping_periods': overlapping_periods,
                'message': message
            }
            
        except Exception as e:
            print(f"[ERROR] 기간 겹침 검사 오류: {str(e)}")
            return {
                'has_overlap': False,
                'overlapping_periods': [],
                'message': f"검사 중 오류 발생: {str(e)}"
            }


    def create_period(self, period_data: dict) -> dict:
        """기간 생성 (날짜 겹침 검사 추가)"""
        try:
            # 1. 기존 중복 체크 (같은 연도/기간명/점검유형)
            if self.check_period_exists(
                period_data["period_year"],
                period_data["period_name"], 
                period_data["check_type"],
            ):
                return {
                    "success": False,
                    "message": f"{period_data['period_year']}년 {period_data['period_name']} {period_data['check_type']} 기간이 이미 존재합니다.",
                }
            
            # 2. 새로 추가: 날짜 겹침 검사
            overlap_result = self.check_period_overlap(
                period_data["check_type"],
                period_data["start_date"],
                period_data["end_date"]
            )
            
            if overlap_result['has_overlap']:
                return {
                    "success": False,
                    "message": f"기간이 겹칩니다. {overlap_result['message']}",
                    "overlapping_periods": overlap_result['overlapping_periods']
                }
            
            # 3. 기간 생성
            with DatabaseManager.get_db_cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO manual_check_periods
                    (check_type, period_year, period_name, start_date, end_date, 
                     description, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        period_data["check_type"],
                        period_data["period_year"],
                        period_data["period_name"],
                        period_data["start_date"],
                        period_data["end_date"],
                        period_data.get("description", ""),
                        period_data["created_by"],
                    ),
                )
                period_id = cursor.lastrowid

            return {
                "success": True,
                "message": "기간이 생성되었습니다.",
                "period_id": period_id,
            }

        except Exception as e:
            return {"success": False, "message": f"기간 생성 실패: {str(e)}"}

    def check_period_exists(self, year: int, period_name: str, check_type: str) -> bool:
        """기간 중복 체크"""
        try:
            result = execute_query(
                """
                SELECT COUNT(*) as count 
                FROM manual_check_periods 
                WHERE period_year = %s 
                AND period_name = %s 
                AND check_type = %s 
                AND is_active = 1
                """,
                (year, period_name, check_type),
                fetch_one=True,
            )

            count = result["count"] if isinstance(result, dict) else result[0]
            return count > 0

        except Exception as e:
            print(f"[ERROR] 기간 중복 체크 오류: {str(e)}")
            return False

    def update_period(self, period_id: int, period_data: dict) -> dict:
        """기간 수정 (날짜 겹침 검사 추가)"""
        try:
            # 기간 존재 여부 확인
            existing = execute_query(
                "SELECT period_id, check_type FROM manual_check_periods WHERE period_id = %s AND is_active = 1",
                (period_id,),
                fetch_one=True,
            )

            if not existing:
                return {"success": False, "message": "기간을 찾을 수 없습니다."}

            # 날짜 겹침 검사 (현재 기간 제외)
            overlap_result = self.check_period_overlap(
                existing['check_type'],
                period_data["start_date"],
                period_data["end_date"],
                exclude_period_id=period_id
            )
            
            if overlap_result['has_overlap']:
                return {
                    "success": False,
                    "message": f"기간이 겹칩니다. {overlap_result['message']}",
                    "overlapping_periods": overlap_result['overlapping_periods']
                }

            # 기간 수정
            execute_query(
                """
                UPDATE manual_check_periods
                SET start_date = %s, end_date = %s, description = %s, updated_at = NOW()
                WHERE period_id = %s
                """,
                (
                    period_data["start_date"],
                    period_data["end_date"],
                    period_data.get("description", ""),
                    period_id,
                ),
            )

            return {"success": True, "message": "기간이 수정되었습니다."}

        except Exception as e:
            return {"success": False, "message": f"기간 수정 실패: {str(e)}"}


    # 컨트롤러에서 사용할 검증 엔드포인트도 추가
    def validate_period_dates(self, check_type: str, start_date, end_date, exclude_period_id=None) -> dict:
        """
        기간 생성/수정 전 유효성 검사
        
        Returns:
            dict: {
                'valid': bool,
                'message': str,
                'overlapping_periods': list (optional)
            }
        """
        try:
            from datetime import datetime
            
            # 날짜 형식 검증
            if isinstance(start_date, str):
                try:
                    start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
                except ValueError:
                    return {"valid": False, "message": "시작일 형식이 올바르지 않습니다. (YYYY-MM-DD)"}
            
            if isinstance(end_date, str):
                try:
                    end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
                except ValueError:
                    return {"valid": False, "message": "종료일 형식이 올바르지 않습니다. (YYYY-MM-DD)"}
            
            # 시작일과 종료일 관계 검증
            if end_date <= start_date:
                return {"valid": False, "message": "종료일은 시작일보다 늦어야 합니다."}
            
            # 겹침 검사
            overlap_result = self.check_period_overlap(check_type, start_date, end_date, exclude_period_id)
            
            if overlap_result['has_overlap']:
                return {
                    "valid": False,
                    "message": overlap_result['message'],
                    "overlapping_periods": overlap_result['overlapping_periods']
                }
            
            return {"valid": True, "message": "유효한 기간입니다."}
            
        except Exception as e:
            return {"valid": False, "message": f"검증 중 오류 발생: {str(e)}"}

    def delete_period(self, period_id: int) -> dict:
        """점검 기간 삭제"""
        try:
            with DatabaseManager.get_db_cursor() as cursor:
                # 기간 존재 확인
                cursor.execute(
                    "SELECT period_id, is_completed FROM manual_check_periods WHERE period_id = %s AND is_active = 1",
                    (period_id,),
                )
                existing = cursor.fetchone()

                if not existing:
                    return {
                        "success": False,
                        "message": "해당 기간을 찾을 수 없습니다.",
                    }

                if existing["is_completed"]:
                    return {
                        "success": False,
                        "message": "완료된 기간은 삭제할 수 없습니다.",
                    }

                # 연결된 점검 결과 확인
                cursor.execute(
                    "SELECT COUNT(*) as count FROM manual_check_results WHERE period_id = %s",
                    (period_id,),
                )
                result_count = cursor.fetchone()["count"]

                if result_count > 0:
                    return {
                        "success": False,
                        "message": f"해당 기간에 {result_count}개의 점검 결과가 있어 삭제할 수 없습니다.",
                    }

                # 기간 삭제 (소프트 삭제)
                cursor.execute(
                    "UPDATE manual_check_periods SET is_active = 0, updated_at = NOW() WHERE period_id = %s",
                    (period_id,),
                )

                return {
                    "success": True,
                    "message": "점검 기간이 성공적으로 삭제되었습니다.",
                }

        except Exception as e:
            return {"success": False, "message": f"기간 삭제 실패: {str(e)}"}

    def complete_period(self, period_id: int, completed_by: str) -> dict:
        """기간 완료 처리 (자동 통과 처리 항상 실행) - 단순화된 버전"""
        try:
            with DatabaseManager.get_db_cursor() as cursor:
                # 1. 기간 정보 조회
                cursor.execute(
                    """
                    SELECT period_id, check_type, period_year, period_name, 
                        start_date, end_date, is_completed
                    FROM manual_check_periods
                    WHERE period_id = %s AND is_active = 1
                    """,
                    (period_id,),
                )
                period_info = cursor.fetchone()

                if not period_info:
                    return {"success": False, "message": "기간을 찾을 수 없습니다."}

                if period_info["is_completed"]:
                    return {"success": False, "message": "이미 완료된 기간입니다."}

                # 2. 기간 완료 처리
                cursor.execute(
                    """
                    UPDATE manual_check_periods
                    SET is_completed = 1, completed_at = NOW(), completed_by = %s, updated_at = NOW()
                    WHERE period_id = %s
                    """,
                    (completed_by, period_id),
                )

                print(
                    f"[DEBUG] 자동 통과 처리 시작 - 점검 유형: {period_info['check_type']}"
                )

                # 3. 단순화된 자동 통과 처리 - 이미 결과가 있는 사용자 제외하고 모든 사용자를 통과 처리
                cursor.execute(
                    """
                    INSERT INTO manual_check_results
                    (user_id, check_item_code, check_year, check_period, check_date, 
                    checker_name, overall_result, total_score, notes, period_id)
                    SELECT 
                        u.uid,
                        %s,
                        %s,
                        'auto_complete',
                        NOW(),
                        '자동완료',
                        'pass',
                        100.0,
                        '기간 완료로 인한 자동 통과 처리',
                        %s
                    FROM users u
                    WHERE u.uid NOT IN (
                        SELECT DISTINCT mcr.user_id 
                        FROM manual_check_results mcr 
                        WHERE mcr.period_id = %s
                    )
                    """,
                    (
                        period_info["check_type"],  # check_item_code
                        period_info["period_year"],  # check_year
                        period_id,  # period_id (INSERT용)
                        period_id,  # period_id 조건 (이미 결과가 있는 사용자 제외)
                    ),
                )

                # 4. 자동 통과 처리된 사용자 수 확인
                auto_passed_count = cursor.rowcount
                print(f"[DEBUG] 자동 통과 처리 완료 - {auto_passed_count}명")

                return {
                    "success": True,
                    "message": f"{period_info['period_name']} 기간이 완료되었습니다. (자동 통과: {auto_passed_count}명)",
                }

        except Exception as e:
            print(f"[ERROR] 완료 처리 실패: {str(e)}")
            import traceback

            traceback.print_exc()
            return {"success": False, "message": f"완료 처리 실패: {str(e)}"}

    def reopen_period(self, period_id: int) -> dict:
        """점검 기간 재개"""
        try:
            with DatabaseManager.get_db_cursor() as cursor:
                # 기간 정보 조회
                cursor.execute(
                    "SELECT period_name, is_completed FROM manual_check_periods WHERE period_id = %s AND is_active = 1",
                    (period_id,),
                )
                period_info = cursor.fetchone()

                if not period_info:
                    return {
                        "success": False,
                        "message": "해당 기간을 찾을 수 없습니다.",
                    }

                if not period_info["is_completed"]:
                    return {"success": False, "message": "완료되지 않은 기간입니다."}

                # 자동 통과 처리된 결과 삭제
                cursor.execute(
                    """
                    DELETE FROM manual_check_results
                    WHERE period_id = %s AND notes = '기간 완료로 인한 자동 통과 처리'
                    """,
                    (period_id,),
                )

                # 기간 재개
                cursor.execute(
                    """
                    UPDATE manual_check_periods
                    SET is_completed = 0, completed_at = NULL, completed_by = NULL, updated_at = NOW()
                    WHERE period_id = %s
                    """,
                    (period_id,),
                )

                return {
                    "success": True,
                    "message": f"{period_info['period_name']} 기간이 재개되었습니다.",
                }

        except Exception as e:
            return {"success": False, "message": f"재개 처리 실패: {str(e)}"}

    def get_check_types(self) -> dict:
        """지원되는 점검 유형 목록 반환"""
        return {
            "seal_check": "PC 봉인씰 확인",
            "malware_scan": "악성코드 전체 검사",
            "file_encryption": "개인정보 파일 암호화",
        }

    def _map_check_type_to_db(self, check_type: str) -> str:
        """프론트엔드 점검 유형을 데이터베이스 ENUM 값으로 매핑"""
        # 임시 매핑 (기존 ENUM 값 활용)
        mapping = {
            "seal_check": "screen_saver",  # 임시로 기존 값 사용
            "malware_scan": "antivirus",  # 임시로 기존 값 사용
            "file_encryption": "patch_update",  # 임시로 기존 값 사용
        }
        return mapping.get(check_type, check_type)
