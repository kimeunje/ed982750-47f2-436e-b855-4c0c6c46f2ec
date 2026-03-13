# app/services/exception_service.py - 뷰 테이블 제거 버전
from datetime import datetime, date
from typing import List, Dict, Optional
from app.utils.database import execute_query, DatabaseManager


class ExceptionService:
    """사용자별/부서별 감사 항목 제외 설정 관리 서비스 - 뷰 테이블 제거 버전"""

    def get_active_exceptions_for_user(self, user_id: int) -> List[Dict]:
        """특정 사용자에게 적용되는 모든 유효한 제외 설정 조회 (뷰 테이블 제거)"""

        # 1. 사용자별 감사 항목 제외 설정
        user_audit_exceptions = execute_query(
            """
            SELECT 
                'user' as exception_type,
                uie.user_id,
                CAST(uie.item_id AS CHAR) as item_id,
                uie.item_name,
                uie.item_category as category,
                uie.exclude_reason,
                uie.exclude_type
            FROM user_item_exceptions uie
            WHERE uie.user_id = %s 
            AND uie.is_active = 1
            AND (uie.exclude_type = 'permanent' OR 
                 (uie.exclude_type = 'temporary' AND CURDATE() BETWEEN uie.start_date AND uie.end_date))
            """,
            (user_id, ),
            fetch_all=True,
        )

        # 2. 사용자별 확장 제외 설정 (교육/훈련)
        user_extended_exceptions = execute_query(
            """
            SELECT 
                'user_extended' as exception_type,
                uee.user_id,
                uee.item_id,
                uee.item_name,
                uee.item_category as category,
                uee.exclude_reason,
                uee.exclude_type
            FROM user_extended_exceptions uee
            WHERE uee.user_id = %s 
            AND uee.is_active = 1
            AND (uee.exclude_type = 'permanent' OR 
                 (uee.exclude_type = 'temporary' AND CURDATE() BETWEEN uee.start_date AND uee.end_date))
            """,
            (user_id, ),
            fetch_all=True,
        )

        # 3. 사용자 부서 정보 조회
        user_dept = execute_query("SELECT department FROM users WHERE uid = %s",
                                  (user_id, ), fetch_one=True)

        if not user_dept:
            return user_audit_exceptions + user_extended_exceptions

        department = user_dept["department"]

        # 4. 부서별 감사 항목 제외 설정
        dept_audit_exceptions = execute_query(
            """
            SELECT 
                'department' as exception_type,
                %s as user_id,
                CAST(die.item_id AS CHAR) as item_id,
                die.item_name,
                die.item_category as category,
                die.exclude_reason,
                die.exclude_type
            FROM department_item_exceptions die
            WHERE die.department = %s 
            AND die.is_active = 1
            AND (die.exclude_type = 'permanent' OR 
                 (die.exclude_type = 'temporary' AND CURDATE() BETWEEN die.start_date AND die.end_date))
            """,
            (user_id, department),
            fetch_all=True,
        )

        # 5. 부서별 확장 제외 설정 (교육/훈련)
        dept_extended_exceptions = execute_query(
            """
            SELECT 
                'department_extended' as exception_type,
                %s as user_id,
                dee.item_id,
                dee.item_name,
                dee.item_category as category,
                dee.exclude_reason,
                dee.exclude_type
            FROM department_extended_exceptions dee
            WHERE dee.department = %s 
            AND dee.is_active = 1
            AND (dee.exclude_type = 'permanent' OR 
                 (dee.exclude_type = 'temporary' AND CURDATE() BETWEEN dee.start_date AND dee.end_date))
            """,
            (user_id, department),
            fetch_all=True,
        )

        # 모든 예외 설정 합치기
        all_exceptions = (user_audit_exceptions + user_extended_exceptions +
                          dept_audit_exceptions + dept_extended_exceptions)

        # 중복 제거 (같은 item_id에 대해 사용자별 설정이 부서별 설정보다 우선)
        unique_exceptions = {}
        for exc in all_exceptions:
            item_key = exc["item_id"]
            if item_key not in unique_exceptions:
                unique_exceptions[item_key] = exc
            elif exc["exception_type"] in ["user", "user_extended"]:
                # 사용자별 설정이 부서별 설정보다 우선
                unique_exceptions[item_key] = exc

        result = list(unique_exceptions.values())
        result.sort(key=lambda x: x["item_name"])

        return result

    def is_item_excluded_for_user(self, user_id: int, item_id: int) -> Dict:
        """특정 사용자-항목이 제외 대상인지 확인 (뷰 테이블 제거)"""
        # 1. 사용자별 감사 항목 제외 설정 확인
        user_audit_exception = execute_query(
            """
            SELECT 
                'user' as exception_type,
                exclude_reason,
                exclude_type,
                start_date,
                end_date
            FROM user_item_exceptions
            WHERE user_id = %s 
            AND item_id = %s 
            AND is_active = 1
            AND (exclude_type = 'permanent' OR 
                 (exclude_type = 'temporary' AND CURDATE() BETWEEN start_date AND end_date))
            LIMIT 1
            """,
            (user_id, item_id),
            fetch_one=True,
        )

        if user_audit_exception:
            return {
                "is_excluded": True,
                "exception_type": user_audit_exception["exception_type"],
                "exclude_reason": user_audit_exception["exclude_reason"],
                "exclude_type": user_audit_exception["exclude_type"],
                "start_date": user_audit_exception["start_date"],
                "end_date": user_audit_exception["end_date"],
            }

        # 2. 사용자별 확장 제외 설정 확인 (교육/훈련)
        user_extended_exception = execute_query(
            """
            SELECT 
                'user_extended' as exception_type,
                exclude_reason,
                exclude_type,
                start_date,
                end_date
            FROM user_extended_exceptions
            WHERE user_id = %s 
            AND item_id = CAST(%s AS CHAR)
            AND item_type = 'audit_item'
            AND is_active = 1
            AND (exclude_type = 'permanent' OR 
                 (exclude_type = 'temporary' AND CURDATE() BETWEEN start_date AND end_date))
            LIMIT 1
            """,
            (user_id, item_id),
            fetch_one=True,
        )

        if user_extended_exception:
            return {
                "is_excluded": True,
                "exception_type": user_extended_exception["exception_type"],
                "exclude_reason": user_extended_exception["exclude_reason"],
                "exclude_type": user_extended_exception["exclude_type"],
                "start_date": user_extended_exception["start_date"],
                "end_date": user_extended_exception["end_date"],
            }

        # 3. 사용자 부서 정보 조회
        user_dept = execute_query("SELECT department FROM users WHERE uid = %s",
                                  (user_id, ), fetch_one=True)

        if not user_dept:
            return {"is_excluded": False}

        department = user_dept["department"]

        # 4. 부서별 감사 항목 제외 설정 확인
        dept_audit_exception = execute_query(
            """
            SELECT 
                'department' as exception_type,
                exclude_reason,
                exclude_type,
                start_date,
                end_date
            FROM department_item_exceptions
            WHERE department = %s 
            AND item_id = %s 
            AND is_active = 1
            AND (exclude_type = 'permanent' OR 
                 (exclude_type = 'temporary' AND CURDATE() BETWEEN start_date AND end_date))
            LIMIT 1
            """,
            (department, item_id),
            fetch_one=True,
        )

        if dept_audit_exception:
            return {
                "is_excluded": True,
                "exception_type": dept_audit_exception["exception_type"],
                "exclude_reason": dept_audit_exception["exclude_reason"],
                "exclude_type": dept_audit_exception["exclude_type"],
                "start_date": dept_audit_exception["start_date"],
                "end_date": dept_audit_exception["end_date"],
            }

        # 5. 부서별 확장 제외 설정 확인 (교육/훈련)
        dept_extended_exception = execute_query(
            """
            SELECT 
                'department_extended' as exception_type,
                exclude_reason,
                exclude_type,
                start_date,
                end_date
            FROM department_extended_exceptions
            WHERE department = %s 
            AND item_id = CAST(%s AS CHAR)
            AND item_type = 'audit_item'
            AND is_active = 1
            AND (exclude_type = 'permanent' OR 
                 (exclude_type = 'temporary' AND CURDATE() BETWEEN start_date AND end_date))
            LIMIT 1
            """,
            (department, item_id),
            fetch_one=True,
        )

        if dept_extended_exception:
            return {
                "is_excluded": True,
                "exception_type": dept_extended_exception["exception_type"],
                "exclude_reason": dept_extended_exception["exclude_reason"],
                "exclude_type": dept_extended_exception["exclude_type"],
                "start_date": dept_extended_exception["start_date"],
                "end_date": dept_extended_exception["end_date"],
            }

        return {"is_excluded": False}

    def get_user_exceptions(self, user_id: int = None,
                            item_id: int = None) -> List[Dict]:
        """사용자별 제외 설정 조회 (확장된 테이블 포함) - 에러 수정 버전"""
        try:
            # 기존 감사 항목 제외 설정
            audit_conditions = ["uie.is_active = 1"]
            audit_params = []

            if user_id:
                audit_conditions.append("uie.user_id = %s")
                audit_params.append(user_id)

            if item_id:
                audit_conditions.append("uie.item_id = %s")
                audit_params.append(item_id)

            audit_where_clause = " AND ".join(audit_conditions)

            audit_exceptions = execute_query(
                f"""
                SELECT 
                    uie.exception_id,
                    uie.user_id,
                    u.user_id as user_login_id,
                    u.username,
                    u.department,
                    CAST(uie.item_id AS CHAR) as item_id,
                    'audit_item' as item_type,
                    uie.item_name,
                    uie.item_category,
                    uie.exclude_reason,
                    uie.exclude_type,
                    uie.start_date,
                    uie.end_date,
                    uie.created_by,
                    uie.created_at,
                    uie.updated_at
                FROM user_item_exceptions uie
                JOIN users u ON uie.user_id = u.uid
                WHERE {audit_where_clause}
                """,
                audit_params,
                fetch_all=True,
            )

            print(
                f"[DEBUG] audit_exceptions 타입: {type(audit_exceptions)}, 값: {audit_exceptions}"
            )

            # 확장된 제외 설정 (교육/훈련)
            extended_conditions = ["uee.is_active = 1"]
            extended_params = []

            if user_id:
                extended_conditions.append("uee.user_id = %s")
                extended_params.append(user_id)

            extended_where_clause = " AND ".join(extended_conditions)

            extended_exceptions = execute_query(
                f"""
                SELECT 
                    uee.exception_id,
                    uee.user_id,
                    u.user_id as user_login_id,
                    u.username,
                    u.department,
                    uee.item_id,
                    uee.item_type,
                    uee.item_name,
                    uee.item_category,
                    uee.exclude_reason,
                    uee.exclude_type,
                    uee.start_date,
                    uee.end_date,
                    uee.created_by,
                    uee.created_at,
                    uee.updated_at
                FROM user_extended_exceptions uee
                JOIN users u ON uee.user_id = u.uid
                WHERE {extended_where_clause}
                """,
                extended_params,
                fetch_all=True,
            )

            print(
                f"[DEBUG] extended_exceptions 타입: {type(extended_exceptions)}, 값: {extended_exceptions}"
            )

            # 안전한 리스트 변환 및 합치기
            if audit_exceptions is None:
                audit_exceptions = []
            elif not isinstance(audit_exceptions, list):
                audit_exceptions = list(audit_exceptions) if audit_exceptions else []

            if extended_exceptions is None:
                extended_exceptions = []
            elif not isinstance(extended_exceptions, list):
                extended_exceptions = (list(extended_exceptions)
                                       if extended_exceptions else [])

            # 결과 합치기
            all_exceptions = audit_exceptions + extended_exceptions

            # 정렬
            if all_exceptions:
                all_exceptions.sort(key=lambda x: (
                    x.get("username", ""),
                    x.get("item_type", ""),
                    x.get("item_name", ""),
                ))

            print(f"[DEBUG] 최종 결과 - 총 {len(all_exceptions)}건")
            return all_exceptions

        except Exception as e:
            print(f"[ERROR] Error in get_user_exceptions: {str(e)}")
            import traceback

            traceback.print_exc()
            return []  # 에러 발생시 빈 리스트 반환

    def get_department_exceptions(self, department: str = None,
                                  item_id: int = None) -> List[Dict]:
        """부서별 제외 설정 조회 (확장된 테이블 포함) - 에러 수정 버전"""
        try:
            # 기존 감사 항목 제외 설정
            audit_conditions = ["die.is_active = 1"]
            audit_params = []

            if department:
                audit_conditions.append("die.department = %s")
                audit_params.append(department)

            if item_id:
                audit_conditions.append("die.item_id = %s")
                audit_params.append(item_id)

            audit_where_clause = " AND ".join(audit_conditions)

            audit_exceptions = execute_query(
                f"""
                SELECT 
                    die.dept_exception_id,
                    die.department,
                    CAST(die.item_id AS CHAR) as item_id,
                    'audit_item' as item_type,
                    die.item_name,
                    die.item_category,
                    die.exclude_reason,
                    die.exclude_type,
                    die.start_date,
                    die.end_date,
                    die.created_by,
                    die.created_at,
                    die.updated_at,
                    COUNT(u.uid) as affected_users
                FROM department_item_exceptions die
                LEFT JOIN users u ON die.department = u.department
                WHERE {audit_where_clause}
                GROUP BY die.dept_exception_id, die.department, die.item_id,
                        die.item_name, die.item_category, die.exclude_reason, die.exclude_type,
                        die.start_date, die.end_date, die.created_by, die.created_at, die.updated_at
                """,
                audit_params,
                fetch_all=True,
            )

            # 확장된 제외 설정 (교육/훈련)
            extended_conditions = ["dee.is_active = 1"]
            extended_params = []

            if department:
                extended_conditions.append("dee.department = %s")
                extended_params.append(department)

            extended_where_clause = " AND ".join(extended_conditions)

            extended_exceptions = execute_query(
                f"""
                SELECT 
                    dee.dept_exception_id,
                    dee.department,
                    dee.item_id,
                    dee.item_type,
                    dee.item_name,
                    dee.item_category,
                    dee.exclude_reason,
                    dee.exclude_type,
                    dee.start_date,
                    dee.end_date,
                    dee.created_by,
                    dee.created_at,
                    dee.updated_at,
                    COUNT(u.uid) as affected_users
                FROM department_extended_exceptions dee
                LEFT JOIN users u ON dee.department = u.department
                WHERE {extended_where_clause}
                GROUP BY dee.dept_exception_id, dee.department, dee.item_id, dee.item_type,
                        dee.item_name, dee.item_category, dee.exclude_reason, dee.exclude_type,
                        dee.start_date, dee.end_date, dee.created_by, dee.created_at, dee.updated_at
                """,
                extended_params,
                fetch_all=True,
            )

            # 안전한 리스트 변환 및 합치기
            if audit_exceptions is None:
                audit_exceptions = []
            elif not isinstance(audit_exceptions, list):
                audit_exceptions = list(audit_exceptions) if audit_exceptions else []

            if extended_exceptions is None:
                extended_exceptions = []
            elif not isinstance(extended_exceptions, list):
                extended_exceptions = (list(extended_exceptions)
                                       if extended_exceptions else [])

            # 결과 합치기
            all_exceptions = audit_exceptions + extended_exceptions

            # 정렬
            if all_exceptions:
                all_exceptions.sort(key=lambda x: (
                    x.get("department", ""),
                    x.get("item_type", ""),
                    x.get("item_name", ""),
                ))

            return all_exceptions

        except Exception as e:
            print(f"[ERROR] Error in get_department_exceptions: {str(e)}")
            import traceback

            traceback.print_exc()
            return []  # 에러 발생시 빈 리스트 반환

    # 나머지 메서드들은 기존과 동일 (add_user_exception, remove_user_exception 등)
    def search_users(self, search_query: str = "", department: str = "",
                     limit: int = 50) -> List[Dict]:
        """사용자 검색"""
        conditions = []
        params = []

        if search_query:
            conditions.append(
                "(u.username LIKE %s OR u.user_id LIKE %s OR u.mail LIKE %s)")
            search_pattern = f"%{search_query}%"
            params.extend([search_pattern, search_pattern, search_pattern])

        if department:
            conditions.append("u.department = %s")
            params.append(department)

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

        return execute_query(
            f"""
            SELECT uid, user_id, username, department, mail
            FROM users u
            {where_clause}
            ORDER BY u.username
            LIMIT %s
            """,
            params + [limit],
            fetch_all=True,
        )

    def is_training_excluded_for_user(self, user_id: int, year: int,
                                      period: str) -> Dict:
        """특정 사용자의 특정 연도/기간 모의훈련 제외 설정 확인"""
        # 1. 연도별 제외 설정 확인 (우선순위: 높음)
        year_specific_item_id = f"training_{year}_{period}"
        result = self.is_extended_item_excluded_for_user(user_id, year_specific_item_id)

        if result.get("is_excluded", False):
            return result

        # 2. 일반 제외 설정 확인 (하위 호환성)
        general_item_id = f"training_{period}"
        return self.is_extended_item_excluded_for_user(user_id, general_item_id)

    def is_education_excluded_for_user(self, user_id: int, year: int,
                                       period: str) -> Dict:
        """특정 사용자의 특정 연도/기간 교육 제외 설정 확인"""
        # 1. 연도별 제외 설정 확인 (우선순위: 높음)
        year_specific_item_id = f"education_{year}_{period}"
        result = self.is_extended_item_excluded_for_user(user_id, year_specific_item_id)

        if result.get("is_excluded", False):
            return result

        # 2. 일반 제외 설정 확인 (하위 호환성)
        general_item_id = f"education_{period}"
        return self.is_extended_item_excluded_for_user(user_id, general_item_id)

    def is_extended_item_excluded_for_user(self, user_id: int, item_id: str) -> Dict:
        """확장 항목 제외 설정 확인 (교육/훈련)"""
        # 1. 사용자별 확장 제외 설정 확인
        user_extended_exception = execute_query(
            """
            SELECT 
                'user_extended' as exception_type,
                exclude_reason,
                exclude_type,
                start_date,
                end_date
            FROM user_extended_exceptions
            WHERE user_id = %s 
            AND item_id = %s
            AND is_active = 1
            AND (exclude_type = 'permanent' OR 
                 (exclude_type = 'temporary' AND CURDATE() BETWEEN start_date AND end_date))
            LIMIT 1
            """,
            (user_id, item_id),
            fetch_one=True,
        )

        if user_extended_exception:
            return {
                "is_excluded": True,
                "exception_type": user_extended_exception["exception_type"],
                "exclude_reason": user_extended_exception["exclude_reason"],
                "exclude_type": user_extended_exception["exclude_type"],
                "start_date": user_extended_exception["start_date"],
                "end_date": user_extended_exception["end_date"],
            }

        # 2. 사용자 부서 정보 조회
        user_dept = execute_query("SELECT department FROM users WHERE uid = %s",
                                  (user_id, ), fetch_one=True)

        if not user_dept:
            return {"is_excluded": False}

        department = user_dept["department"]

        # 3. 부서별 확장 제외 설정 확인
        dept_extended_exception = execute_query(
            """
            SELECT 
                'department_extended' as exception_type,
                exclude_reason,
                exclude_type,
                start_date,
                end_date
            FROM department_extended_exceptions
            WHERE department = %s 
            AND item_id = %s
            AND is_active = 1
            AND (exclude_type = 'permanent' OR 
                 (exclude_type = 'temporary' AND CURDATE() BETWEEN start_date AND end_date))
            LIMIT 1
            """,
            (department, item_id),
            fetch_one=True,
        )

        if dept_extended_exception:
            return {
                "is_excluded": True,
                "exception_type": dept_extended_exception["exception_type"],
                "exclude_reason": dept_extended_exception["exclude_reason"],
                "exclude_type": dept_extended_exception["exclude_type"],
                "start_date": dept_extended_exception["start_date"],
                "end_date": dept_extended_exception["end_date"],
            }

        return {"is_excluded": False}

    def get_available_items(self) -> Dict[str, List[Dict]]:
        """제외 설정 가능한 항목들 조회 (checklist_items + manual_check_items 통합)"""

        # 1. checklist_items에서 일반 감사 항목들 조회 (is_active 조건 제거)
        audit_items = execute_query(
            """
            SELECT 
                CONCAT('audit_', item_id) as item_id,
                item_name, 
                category, 
                description, 
                check_type, 
                penalty_weight
            FROM checklist_items
            ORDER BY category, item_name
            """,
            fetch_all=True,
        )

        # 2. manual_check_items에서 수시 점검 항목들 조회
        manual_items = execute_query(
            """
            SELECT 
                CONCAT('manual_', item_id) as item_id,
                item_name, 
                item_category as category, 
                description, 
                'manual' as check_type, 
                penalty_weight
            FROM manual_check_items
            WHERE is_active = 1
            ORDER BY item_category, item_name
            """,
            fetch_all=True,
        )

        # 3. 카테고리별로 그룹화
        grouped_items = {}

        # 일반 감사 항목들을 카테고리별로 분류
        for item in audit_items:
            category = item["category"]
            if category not in grouped_items:
                grouped_items[category] = []
            grouped_items[category].append({
                "item_id": item["item_id"],
                "item_name": item["item_name"],
                "description": item["description"],
                "check_type": item["check_type"],
                "penalty_weight": item["penalty_weight"],
                "source": "checklist_items",
            })

        # 수시 점검 항목들을 카테고리별로 분류
        for item in manual_items:
            category = item["category"]
            if category not in grouped_items:
                grouped_items[category] = []
            grouped_items[category].append({
                "item_id": item["item_id"],
                "item_name": item["item_name"],
                "description": item["description"],
                "check_type": item["check_type"],
                "penalty_weight": item["penalty_weight"],
                "source": "manual_check_items",
            })

        # 4. 현재 연도 기준으로 ±2년 범위의 교육/훈련 항목 생성
        current_year = datetime.now().year
        years = range(current_year - 2, current_year + 3)  # 5년 범위

        education_items = []
        training_items = []

        for year in years:
            education_items.extend([
                {
                    "item_id": f"education_{year}_first_half",
                    "item_name": f"{year}년 상반기 정보보호 교육",
                    "description": f"{year}년 상반기 정보보호 교육 이수",
                    "year": year,
                    "period": "first_half",
                    "source": "generated",
                },
                {
                    "item_id": f"education_{year}_second_half",
                    "item_name": f"{year}년 하반기 정보보호 교육",
                    "description": f"{year}년 하반기 정보보호 교육 이수",
                    "year": year,
                    "period": "second_half",
                    "source": "generated",
                },
            ])

            training_items.extend([
                {
                    "item_id": f"training_{year}_first_half",
                    "item_name": f"{year}년 상반기 악성메일 모의훈련",
                    "description": f"{year}년 상반기 악성메일 모의훈련 참여",
                    "year": year,
                    "period": "first_half",
                    "source": "generated",
                },
                {
                    "item_id": f"training_{year}_second_half",
                    "item_name": f"{year}년 하반기 악성메일 모의훈련",
                    "description": f"{year}년 하반기 악성메일 모의훈련 참여",
                    "year": year,
                    "period": "second_half",
                    "source": "generated",
                },
            ])

        # 5. 교육/훈련 항목을 그룹에 추가
        grouped_items["정보보호 교육"] = education_items
        grouped_items["악성메일 모의훈련"] = training_items

        return grouped_items

    def add_user_exception(
        self,
        user_uid: int,  # 파라미터명 수정: user_id -> user_uid
        item_id: str,  # item_type에서 전달받은 값
        item_type: str,  # 'audit_1', 'manual_1', 'training_2025_first_half' 등
        item_name: str,
        item_category: str,
        exclude_reason: str,
        exclude_type: str = "permanent",
        start_date: date = None,
        end_date: date = None,
        created_by: str = "admin",
    ) -> Dict:
        """사용자별 제외 설정 추가 (통합 버전)"""
        try:
            print(
                f"[DEBUG] add_user_exception 호출 - user_uid: {user_uid}, item_type: {item_type}"
            )

            # 사용자 존재 확인
            user = execute_query(
                "SELECT uid, username, department FROM users WHERE uid = %s",
                (user_uid, ),
                fetch_one=True,
            )

            if not user:
                return {"success": False, "message": "존재하지 않는 사용자입니다."}

            if item_type.startswith("audit_"):
                # checklist_items 테이블의 일반 감사 항목
                item_id_int = int(item_type.replace("audit_", ""))
                return self._add_user_audit_exception(
                    user_uid,
                    item_id_int,
                    item_name,
                    exclude_reason,
                    exclude_type,
                    start_date,
                    end_date,
                    created_by,
                )
            elif item_type.startswith("manual_"):
                # manual_check_items 테이블의 수시 점검 항목
                item_id_int = int(item_type.replace("manual_", ""))
                return self._add_user_manual_exception(
                    user_uid,
                    item_id_int,
                    item_name,
                    exclude_reason,
                    exclude_type,
                    start_date,
                    end_date,
                    created_by,
                )
            elif item_type.startswith(("education_", "training_")):
                # 교육/훈련 항목 - 확장 테이블 사용
                return self._add_user_extended_exception(
                    user_uid,
                    item_type,
                    item_name,
                    item_category,
                    exclude_reason,
                    exclude_type,
                    start_date,
                    end_date,
                    created_by,
                )
            else:
                return {
                    "success": False,
                    "message": f"지원하지 않는 항목 유형입니다: {item_type}",
                }

        except Exception as e:
            print(f"[ERROR] add_user_exception 실패: {str(e)}")
            import traceback

            traceback.print_exc()
            return {"success": False, "message": f"제외 설정 추가 실패: {str(e)}"}

    def add_department_exception(
        self,
        department: str,
        item_type: str,  # 'audit_1', 'manual_1', 'training_2025_first_half' 등
        item_name: str,
        exclude_reason: str,
        exclude_type: str = "permanent",
        start_date: date = None,
        end_date: date = None,
        created_by: str = "admin",
    ) -> Dict:
        """부서별 제외 설정 추가 (통합 버전)"""
        try:
            print(
                f"[DEBUG] add_department_exception 호출 - department: {department}, item_type: {item_type}"
            )

            if item_type.startswith("audit_"):
                # checklist_items 테이블의 일반 감사 항목
                item_id = int(item_type.replace("audit_", ""))
                return self._add_department_audit_exception(
                    department,
                    item_id,
                    item_name,
                    exclude_reason,
                    exclude_type,
                    start_date,
                    end_date,
                    created_by,
                )
            elif item_type.startswith("manual_"):
                # manual_check_items 테이블의 수시 점검 항목
                item_id = int(item_type.replace("manual_", ""))
                return self._add_department_manual_exception(
                    department,
                    item_id,
                    item_name,
                    exclude_reason,
                    exclude_type,
                    start_date,
                    end_date,
                    created_by,
                )
            elif item_type.startswith(("education_", "training_")):
                # 교육/훈련 항목 - 확장 테이블 사용
                return self._add_department_extended_exception(
                    department,
                    item_type,
                    item_name,
                    exclude_reason,
                    exclude_type,
                    start_date,
                    end_date,
                    created_by,
                )
            else:
                return {
                    "success": False,
                    "message": f"지원하지 않는 항목 유형입니다: {item_type}",
                }

        except Exception as e:
            print(f"[ERROR] add_department_exception 실패: {str(e)}")
            import traceback

            traceback.print_exc()
            return {
                "success": False,
                "message": f"부서별 제외 설정 추가 실패: {str(e)}",
            }

    def _add_user_audit_exception(
        self,
        user_uid: int,
        item_id: int,
        item_name: str,
        exclude_reason: str,
        exclude_type: str,
        start_date: date,
        end_date: date,
        created_by: str,
    ) -> Dict:
        """checklist_items 감사 항목 사용자별 제외 설정 추가"""
        # 항목 정보 조회
        item_info = execute_query(
            "SELECT item_name, category FROM checklist_items WHERE item_id = %s",
            (item_id, ),
            fetch_one=True,
        )

        if not item_info:
            return {"success": False, "message": "존재하지 않는 감사 항목입니다."}

        try:
            # 기존 설정 확인
            existing = execute_query(
                "SELECT exception_id FROM user_item_exceptions WHERE user_id = %s AND item_id = %s",
                (user_uid, item_id),
                fetch_one=True,
            )

            if existing:
                # 기존 설정 업데이트
                execute_query(
                    """
                    UPDATE user_item_exceptions 
                    SET exclude_reason = %s, exclude_type = %s, start_date = %s, 
                        end_date = %s, created_by = %s, is_active = 1, updated_at = NOW(),
                        item_name = %s, item_category = %s
                    WHERE user_id = %s AND item_id = %s
                    """,
                    (
                        exclude_reason,
                        exclude_type,
                        start_date,
                        end_date,
                        created_by,
                        item_info["item_name"],
                        item_info["category"],
                        user_uid,
                        item_id,
                    ),
                )
                return {
                    "success": True,
                    "message": "기존 제외 설정이 업데이트되었습니다.",
                    "action": "updated",
                }
            else:
                # 새 설정 추가
                execute_query(
                    """
                    INSERT INTO user_item_exceptions 
                    (user_id, item_id, exclude_reason, exclude_type, start_date, end_date, 
                    created_by, is_active, item_type, item_name, item_category)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 1, 'audit', %s, %s)
                    """,
                    (
                        user_uid,
                        item_id,
                        exclude_reason,
                        exclude_type,
                        start_date,
                        end_date,
                        created_by,
                        item_info["item_name"],
                        item_info["category"],
                    ),
                )
                return {
                    "success": True,
                    "message": "새로운 제외 설정이 추가되었습니다.",
                    "action": "created",
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"감사 항목 제외 설정 추가 실패: {str(e)}",
            }

    def _add_user_extended_exception(
        self,
        user_uid: int,
        item_id: str,  # 'education_2025_first_half', 'training_2025_first_half' 등
        item_name: str,
        item_category: str,
        exclude_reason: str,
        exclude_type: str,
        start_date: date,
        end_date: date,
        created_by: str,
    ) -> Dict:
        """교육/훈련 항목 사용자별 제외 설정 추가"""
        try:
            # item_type 결정
            if item_id.startswith("education_"):
                db_item_type = "education_period"
            elif item_id.startswith("training_"):
                db_item_type = "training_period"
            else:
                return {"success": False, "message": "알 수 없는 확장 항목 유형입니다."}

            # 기존 설정 확인
            existing = execute_query(
                "SELECT exception_id FROM user_extended_exceptions WHERE user_id = %s AND item_id = %s",
                (user_uid, item_id),
                fetch_one=True,
            )

            if existing:
                # 기존 설정 업데이트
                execute_query(
                    """
                    UPDATE user_extended_exceptions 
                    SET exclude_reason = %s, exclude_type = %s, start_date = %s, 
                        end_date = %s, created_by = %s, is_active = 1, updated_at = NOW()
                    WHERE user_id = %s AND item_id = %s
                    """,
                    (
                        exclude_reason,
                        exclude_type,
                        start_date,
                        end_date,
                        created_by,
                        user_uid,
                        item_id,
                    ),
                )
                return {
                    "success": True,
                    "message": "기존 확장 제외 설정이 업데이트되었습니다.",
                    "action": "updated",
                }
            else:
                # 새 설정 추가
                execute_query(
                    """
                    INSERT INTO user_extended_exceptions 
                    (user_id, item_id, item_type, item_name, item_category, exclude_reason, 
                    exclude_type, start_date, end_date, created_by, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
                    """,
                    (
                        user_uid,
                        item_id,
                        db_item_type,
                        item_name,
                        item_category,
                        exclude_reason,
                        exclude_type,
                        start_date,
                        end_date,
                        created_by,
                    ),
                )
                return {
                    "success": True,
                    "message": "새로운 확장 제외 설정이 추가되었습니다.",
                    "action": "created",
                }

        except Exception as e:
            return {"success": False, "message": f"확장 제외 설정 추가 실패: {str(e)}"}

    def add_department_exception(
        self,
        department: str,
        item_type: str,
        item_name: str,
        exclude_reason: str,
        exclude_type: str = "permanent",
        start_date: date = None,
        end_date: date = None,
        created_by: str = "admin",
    ) -> Dict:
        """부서별 제외 설정 추가 (확장된 버전)"""
        try:
            # item_type에 따라 적절한 테이블과 item_id 결정
            if item_type.startswith("audit_"):
                # 감사 항목 처리
                item_id = int(item_type.replace("audit_", ""))
                return self._add_department_audit_exception(
                    department,
                    item_id,
                    item_name,
                    exclude_reason,
                    exclude_type,
                    start_date,
                    end_date,
                    created_by,
                )
            else:
                # 교육/훈련 항목 처리
                return self._add_department_extended_exception(
                    department,
                    item_type,
                    item_name,
                    exclude_reason,
                    exclude_type,
                    start_date,
                    end_date,
                    created_by,
                )

        except Exception as e:
            return {
                "success": False,
                "message": f"부서별 제외 설정 추가 실패: {str(e)}",
            }

    def _add_department_audit_exception(
        self,
        department: str,
        item_id: int,
        item_name: str,
        exclude_reason: str,
        exclude_type: str,
        start_date: date,
        end_date: date,
        created_by: str,
    ) -> Dict:
        """감사 항목 부서별 제외 설정 추가"""
        # 항목 정보 조회
        item_info = execute_query(
            "SELECT item_name, category FROM checklist_items WHERE item_id = %s",
            (item_id, ),
            fetch_one=True,
        )

        if not item_info:
            return {"success": False, "message": "존재하지 않는 감사 항목입니다."}

        # 기존 설정 확인
        existing = execute_query(
            "SELECT dept_exception_id FROM department_item_exceptions WHERE department = %s AND item_id = %s",
            (department, item_id),
            fetch_one=True,
        )

        if existing:
            # 기존 설정 업데이트
            execute_query(
                """
                UPDATE department_item_exceptions 
                SET exclude_reason = %s, exclude_type = %s, start_date = %s, 
                    end_date = %s, created_by = %s, is_active = 1, updated_at = NOW(),
                    item_name = %s, item_category = %s
                WHERE department = %s AND item_id = %s
                """,
                (
                    exclude_reason,
                    exclude_type,
                    start_date,
                    end_date,
                    created_by,
                    item_info["item_name"],
                    item_info["category"],
                    department,
                    item_id,
                ),
            )
            return {
                "success": True,
                "message": "기존 부서별 제외 설정이 업데이트되었습니다.",
                "action": "updated",
            }
        else:
            # 새 설정 추가
            execute_query(
                """
                INSERT INTO department_item_exceptions 
                (department, item_id, exclude_reason, exclude_type, start_date, end_date, 
                 created_by, item_name, item_category, item_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'audit')
                """,
                (
                    department,
                    item_id,
                    exclude_reason,
                    exclude_type,
                    start_date,
                    end_date,
                    created_by,
                    item_info["item_name"],
                    item_info["category"],
                ),
            )
            return {
                "success": True,
                "message": "새로운 부서별 제외 설정이 추가되었습니다.",
                "action": "created",
            }

    def _add_department_extended_exception(
        self,
        department: str,
        item_type: str,  # 'education_2025_first_half', 'training_2025_first_half' 등
        item_name: str,
        exclude_reason: str,
        exclude_type: str,
        start_date: date,
        end_date: date,
        created_by: str,
    ) -> Dict:
        """교육/훈련 항목 부서별 제외 설정 추가"""
        try:
            # item_type에 따른 카테고리와 DB item_type 결정
            if item_type.startswith("education_"):
                category = "정보보호 교육"
                db_item_type = "education_period"
            elif item_type.startswith("training_"):
                category = "악성메일 모의훈련"
                db_item_type = "training_period"
            else:
                return {"success": False, "message": "알 수 없는 확장 항목 유형입니다."}

            # 기존 설정 확인
            existing = execute_query(
                "SELECT dept_exception_id FROM department_extended_exceptions WHERE department = %s AND item_id = %s",
                (department, item_type),
                fetch_one=True,
            )

            if existing:
                # 기존 설정 업데이트
                execute_query(
                    """
                    UPDATE department_extended_exceptions 
                    SET exclude_reason = %s, exclude_type = %s, start_date = %s, 
                        end_date = %s, created_by = %s, is_active = 1, updated_at = NOW()
                    WHERE department = %s AND item_id = %s
                    """,
                    (
                        exclude_reason,
                        exclude_type,
                        start_date,
                        end_date,
                        created_by,
                        department,
                        item_type,
                    ),
                )
                return {
                    "success": True,
                    "message": "기존 부서별 확장 제외 설정이 업데이트되었습니다.",
                    "action": "updated",
                }
            else:
                # 새 설정 추가
                execute_query(
                    """
                    INSERT INTO department_extended_exceptions 
                    (department, item_id, item_type, item_name, item_category, exclude_reason, 
                    exclude_type, start_date, end_date, created_by, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
                    """,
                    (
                        department,
                        item_type,
                        db_item_type,
                        item_name,
                        category,
                        exclude_reason,
                        exclude_type,
                        start_date,
                        end_date,
                        created_by,
                    ),
                )
                return {
                    "success": True,
                    "message": "새로운 부서별 확장 제외 설정이 추가되었습니다.",
                    "action": "created",
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"부서별 확장 제외 설정 추가 실패: {str(e)}",
            }

    def get_all_departments(self) -> List[str]:
        """시스템에 등록된 모든 부서 목록 조회"""
        departments = execute_query(
            "SELECT DISTINCT department FROM users WHERE department IS NOT NULL ORDER BY department",
            fetch_all=True,
        )
        return [dept["department"] for dept in departments]

    def get_exception_summary(self) -> Dict:
        """제외 설정 요약 통계"""
        with DatabaseManager.get_db_cursor(commit=False) as cursor:
            # 사용자별 제외 설정 통계
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_user_exceptions,
                    COUNT(CASE WHEN exclude_type = 'permanent' THEN 1 END) as permanent_user_exceptions,
                    COUNT(CASE WHEN exclude_type = 'temporary' THEN 1 END) as temporary_user_exceptions
                FROM user_item_exceptions 
                WHERE is_active = 1
                """)
            user_stats = cursor.fetchone()

            # 부서별 제외 설정 통계
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_dept_exceptions,
                    COUNT(CASE WHEN exclude_type = 'permanent' THEN 1 END) as permanent_dept_exceptions,
                    COUNT(CASE WHEN exclude_type = 'temporary' THEN 1 END) as temporary_dept_exceptions,
                    COUNT(DISTINCT department) as affected_departments
                FROM department_item_exceptions 
                WHERE is_active = 1
                """)
            dept_stats = cursor.fetchone()

            # 가장 많이 제외된 항목들
            cursor.execute("""
                SELECT 
                    ci.item_name,
                    ci.category,
                    COUNT(*) as exception_count
                FROM (
                    SELECT item_id FROM user_item_exceptions WHERE is_active = 1
                    UNION ALL
                    SELECT die.item_id 
                    FROM department_item_exceptions die
                    JOIN users u ON die.department = u.department
                    WHERE die.is_active = 1
                ) exceptions
                JOIN checklist_items ci ON exceptions.item_id = ci.item_id
                GROUP BY ci.item_id, ci.item_name, ci.category
                ORDER BY exception_count DESC
                LIMIT 5
                """)
            top_excluded_items = cursor.fetchall()

        return {
            "user_exceptions": user_stats,
            "department_exceptions": dept_stats,
            "top_excluded_items": top_excluded_items,
        }

    # app/services/admin_exception_service.py 수정사항

    def _add_user_manual_exception(
        self,
        user_uid: int,
        item_id: int,
        item_name: str,
        exclude_reason: str,
        exclude_type: str,
        start_date: date,
        end_date: date,
        created_by: str,
    ) -> Dict:
        """manual_check_items 수시 점검 항목 사용자별 제외 설정 추가 + 기존 결과 동기화"""
        # 항목 정보 조회
        item_info = execute_query(
            "SELECT item_name, item_category, item_code FROM manual_check_items WHERE item_id = %s",
            (item_id, ),
            fetch_one=True,
        )

        if not item_info:
            return {"success": False, "message": "존재하지 않는 수시 점검 항목입니다."}

        try:
            # 기존 설정 확인 (manual_check_items 항목은 user_item_exceptions 테이블 사용)
            existing = execute_query(
                "SELECT exception_id FROM user_item_exceptions WHERE user_id = %s AND item_id = %s AND item_type = 'manual'",
                (user_uid, item_id),
                fetch_one=True,
            )

            if existing:
                # 기존 설정 업데이트
                execute_query(
                    """
                    UPDATE user_item_exceptions 
                    SET exclude_reason = %s, exclude_type = %s, start_date = %s, 
                        end_date = %s, created_by = %s, is_active = 1, updated_at = NOW(),
                        item_name = %s, item_category = %s
                    WHERE user_id = %s AND item_id = %s AND item_type = 'manual'
                    """,
                    (
                        exclude_reason,
                        exclude_type,
                        start_date,
                        end_date,
                        created_by,
                        item_info["item_name"],
                        item_info["item_category"],
                        user_uid,
                        item_id,
                    ),
                )
                action_msg = "기존 수시 점검 제외 설정이 업데이트되었습니다."
                action = "updated"
            else:
                # 새 설정 추가
                execute_query(
                    """
                    INSERT INTO user_item_exceptions 
                    (user_id, item_id, exclude_reason, exclude_type, start_date, end_date, 
                    created_by, is_active, item_type, item_name, item_category)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 1, 'manual', %s, %s)
                    """,
                    (
                        user_uid,
                        item_id,
                        exclude_reason,
                        exclude_type,
                        start_date,
                        end_date,
                        created_by,
                        item_info["item_name"],
                        item_info["item_category"],
                    ),
                )
                action_msg = "새로운 수시 점검 제외 설정이 추가되었습니다."
                action = "created"

            # ★★★ 핵심: 기존 manual_check_results 데이터 동기화 ★★★
            sync_result = self._sync_manual_check_results_exclusion(
                user_uid, item_info["item_code"], exclude_reason, is_excluded=True)

            final_message = f"{action_msg} {sync_result['message']}"

            return {
                "success": True,
                "message": final_message,
                "action": action,
                "sync_details": sync_result,
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"수시 점검 제외 설정 추가 실패: {str(e)}",
            }

    # _sync_manual_check_results_exclusion 메서드도 확인 (이미 올바르게 구현되어 있음)
    def _sync_manual_check_results_exclusion(
        self,
        user_id: int,
        item_code: str,
        exclude_reason: str,
        is_excluded: bool = True,
    ) -> Dict:
        """manual_check_results 테이블의 기존 데이터와 제외 설정 동기화"""
        try:
            if is_excluded:
                # 제외 설정 시: exclude_from_scoring = 1, exclude_reason 설정
                result = execute_query(
                    """
                    UPDATE manual_check_results 
                    SET exclude_from_scoring = 1, 
                        exclude_reason = %s,
                        updated_at = NOW()
                    WHERE user_id = %s AND check_item_code = %s AND exclude_from_scoring = 0
                    """,
                    (exclude_reason, user_id, item_code),
                )

                if result > 0:
                    return {
                        "success": True,
                        "message": f"기존 {result}건의 수시점검 결과가 제외 처리되었습니다.",
                        "updated_count": result,
                    }
                else:
                    return {
                        "success": True,
                        "message": "동기화할 기존 결과가 없습니다.",
                        "updated_count": 0,
                    }
            else:
                # ★★★ 제외 해제 시: exclude_from_scoring = 0, exclude_reason 초기화 ★★★
                result = execute_query(
                    """
                    UPDATE manual_check_results 
                    SET exclude_from_scoring = 0, 
                        exclude_reason = NULL,
                        updated_at = NOW()
                    WHERE user_id = %s AND check_item_code = %s AND exclude_from_scoring = 1
                    """,
                    (user_id, item_code),
                )

                if result > 0:
                    return {
                        "success": True,
                        "message": f"기존 {result}건의 수시점검 결과가 포함 처리되었습니다.",
                        "updated_count": result,
                    }
                else:
                    return {
                        "success": True,
                        "message": "동기화할 기존 결과가 없습니다.",
                        "updated_count": 0,
                    }

        except Exception as e:
            return {
                "success": False,
                "message": f"기존 결과 동기화 실패: {str(e)}",
                "updated_count": 0,
            }

    def remove_user_exception(self, user_id: int, item_type: str) -> Dict:
        """사용자별 제외 설정 제거 (수정된 버전) + 기존 결과 동기화"""
        try:
            print(
                f"[DEBUG] remove_user_exception 호출 - user_id: {user_id}, item_type: {item_type}"
            )

            # item_type이 숫자인지 확인 (감사 항목)
            if item_type.isdigit():
                # 숫자 item_type은 감사 항목으로 처리
                item_id = int(item_type)
                print(f"[DEBUG] 감사 항목 처리 (숫자) - item_id: {item_id}")
                result = execute_query(
                    "UPDATE user_item_exceptions SET is_active = 0 WHERE user_id = %s AND item_id = %s",
                    (user_id, item_id),
                )
                print(f"[DEBUG] user_item_exceptions 업데이트 결과: {result}")

            elif item_type.startswith("audit_"):
                # audit_ 접두사가 있는 감사 항목
                item_id = int(item_type.replace("audit_", ""))
                print(f"[DEBUG] 감사 항목 처리 (audit_ 접두사) - item_id: {item_id}")
                result = execute_query(
                    "UPDATE user_item_exceptions SET is_active = 0 WHERE user_id = %s AND item_id = %s",
                    (user_id, item_id),
                )
                print(f"[DEBUG] user_item_exceptions 업데이트 결과: {result}")

            elif item_type.startswith("manual_"):
                # ★★★ 수시 점검 항목 제거 시 동기화 수정 ★★★
                item_id = int(item_type.replace("manual_", ""))
                print(f"[DEBUG] 수시 점검 항목 처리 (manual_ 접두사) - item_id: {item_id}")

                # 1. 먼저 item_code 조회
                item_info = execute_query(
                    "SELECT item_code FROM manual_check_items WHERE item_id = %s",
                    (item_id, ),
                    fetch_one=True,
                )

                if not item_info:
                    return {"success": False, "message": "수시 점검 항목을 찾을 수 없습니다."}

                # 2. user_item_exceptions에서 제외 설정 비활성화
                result = execute_query(
                    """UPDATE user_item_exceptions 
                    SET is_active = 0, updated_at = NOW() 
                    WHERE user_id = %s AND item_id = %s AND item_type = 'manual'""",
                    (user_id, item_id),
                )
                print(f"[DEBUG] user_item_exceptions 업데이트 결과: {result}")

                # 3. ★★★ 핵심: manual_check_results 동기화 (제외 해제) ★★★
                if result > 0:
                    sync_result = self._sync_manual_check_results_exclusion(
                        user_id,
                        item_info["item_code"],
                        "",
                        is_excluded=False  # False로 설정하여 제외 해제
                    )
                    print(f"[DEBUG] 동기화 결과: {sync_result}")

                    final_message = f"제외 설정이 비활성화되었습니다. {sync_result['message']}"
                    return {
                        "success": True,
                        "message": final_message,
                        "sync_details": sync_result,
                    }
                else:
                    return {"success": False, "message": "해당 제외 설정을 찾을 수 없습니다."}

            else:
                # 교육/훈련 항목 제외 설정 제거
                print(f"[DEBUG] 교육/훈련 항목 처리 - item_type: {item_type}")
                result = execute_query(
                    "UPDATE user_extended_exceptions SET is_active = 0 WHERE user_id = %s AND item_id = %s",
                    (user_id, item_type),
                )
                print(f"[DEBUG] user_extended_exceptions 업데이트 결과: {result}")

            print(f"[DEBUG] 최종 결과: {result}")

            if result > 0:
                return {"success": True, "message": "제외 설정이 비활성화되었습니다."}
            else:
                return {
                    "success": False,
                    "message": "해당 제외 설정을 찾을 수 없습니다.",
                }

        except Exception as e:
            print(f"[ERROR] 제외 설정 제거 중 예외 발생: {str(e)}")
            return {"success": False, "message": f"제외 설정 제거 실패: {str(e)}"}

    def _add_department_manual_exception(
        self,
        department: str,
        item_id: int,
        item_name: str,
        exclude_reason: str,
        exclude_type: str,
        start_date: date,
        end_date: date,
        created_by: str,
    ) -> Dict:
        """manual_check_items 수시 점검 항목 부서별 제외 설정 추가 + 부서 사용자 동기화"""
        # 항목 정보 조회
        item_info = execute_query(
            "SELECT item_name, item_category, item_code FROM manual_check_items WHERE item_id = %s",
            (item_id, ),
            fetch_one=True,
        )

        if not item_info:
            return {"success": False, "message": "존재하지 않는 수시 점검 항목입니다."}

        try:
            # 기존 설정 확인
            existing = execute_query(
                "SELECT dept_exception_id FROM department_item_exceptions WHERE department = %s AND item_id = %s AND item_type = 'manual'",
                (department, item_id),
                fetch_one=True,
            )

            if existing:
                # 기존 설정 업데이트
                execute_query(
                    """
                    UPDATE department_item_exceptions 
                    SET exclude_reason = %s, exclude_type = %s, start_date = %s, 
                        end_date = %s, created_by = %s, is_active = 1, updated_at = NOW(),
                        item_name = %s, item_category = %s
                    WHERE department = %s AND item_id = %s AND item_type = 'manual'
                    """,
                    (
                        exclude_reason,
                        exclude_type,
                        start_date,
                        end_date,
                        created_by,
                        item_info["item_name"],
                        item_info["item_category"],
                        department,
                        item_id,
                    ),
                )
                action_msg = "기존 부서별 수시 점검 제외 설정이 업데이트되었습니다."
                action = "updated"
            else:
                # 새 설정 추가
                execute_query(
                    """
                    INSERT INTO department_item_exceptions 
                    (department, item_id, exclude_reason, exclude_type, start_date, end_date, 
                    created_by, item_name, item_category, item_type)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'manual')
                    """,
                    (
                        department,
                        item_id,
                        exclude_reason,
                        exclude_type,
                        start_date,
                        end_date,
                        created_by,
                        item_info["item_name"],
                        item_info["item_category"],
                    ),
                )
                action_msg = "새로운 부서별 수시 점검 제외 설정이 추가되었습니다."
                action = "created"

            # ★★★ 부서 소속 전체 사용자의 기존 결과 동기화 ★★★
            sync_result = self._sync_department_manual_check_results_exclusion(
                department, item_info["item_code"], exclude_reason, is_excluded=True)

            final_message = f"{action_msg} {sync_result['message']}"

            return {
                "success": True,
                "message": final_message,
                "action": action,
                "sync_details": sync_result,
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"부서별 수시 점검 제외 설정 추가 실패: {str(e)}",
            }

    def _sync_department_manual_check_results_exclusion(
        self,
        department: str,
        item_code: str,
        exclude_reason: str,
        is_excluded: bool = True,
    ) -> Dict:
        """부서별 manual_check_results 테이블의 기존 데이터와 제외 설정 동기화"""
        try:
            if is_excluded:
                # 제외 설정 시: 해당 부서 사용자들의 결과를 제외 처리
                result = execute_query(
                    """
                    UPDATE manual_check_results mcr
                    JOIN users u ON mcr.user_id = u.uid
                    SET mcr.exclude_from_scoring = 1, 
                        mcr.exclude_reason = %s,
                        mcr.updated_at = NOW()
                    WHERE u.department = %s 
                      AND mcr.check_item_code = %s 
                      AND mcr.exclude_from_scoring = 0
                    """,
                    (exclude_reason, department, item_code),
                )

                if result > 0:
                    return {
                        "success": True,
                        "message": f"부서 소속 사용자들의 기존 {result}건 상시점검 결과가 제외 처리되었습니다.",
                        "updated_count": result,
                    }
                else:
                    return {
                        "success": True,
                        "message": "부서 소속 사용자들의 동기화할 기존 결과가 없습니다.",
                        "updated_count": 0,
                    }
            else:
                # 제외 해제 시
                result = execute_query(
                    """
                    UPDATE manual_check_results mcr
                    JOIN users u ON mcr.user_id = u.uid
                    SET mcr.exclude_from_scoring = 0, 
                        mcr.exclude_reason = NULL,
                        mcr.updated_at = NOW()
                    WHERE u.department = %s 
                      AND mcr.check_item_code = %s 
                      AND mcr.exclude_from_scoring = 1
                    """,
                    (department, item_code),
                )

                if result > 0:
                    return {
                        "success": True,
                        "message": f"부서 소속 사용자들의 기존 {result}건 상시점검 결과가 포함 처리되었습니다.",
                        "updated_count": result,
                    }
                else:
                    return {
                        "success": True,
                        "message": "부서 소속 사용자들의 동기화할 기존 결과가 없습니다.",
                        "updated_count": 0,
                    }

        except Exception as e:
            return {
                "success": False,
                "message": f"부서별 기존 결과 동기화 실패: {str(e)}",
                "updated_count": 0,
            }

    # remove_department_exception 메서드도 수정 필요
    def remove_department_exception(self, department: str, item_type: str) -> Dict:
        """부서별 제외 설정 제거 (수정된 버전) + 기존 결과 동기화"""
        try:
            print(
                f"[DEBUG] remove_department_exception 호출 - department: {department}, item_type: {item_type}"
            )

            # item_type이 숫자인지 확인 (감사 항목)
            if item_type.isdigit():
                # 숫자 item_type은 감사 항목으로 처리
                item_id = int(item_type)
                print(f"[DEBUG] 부서별 감사 항목 처리 (숫자) - item_id: {item_id}")
                result = execute_query(
                    "UPDATE department_item_exceptions SET is_active = 0 WHERE department = %s AND item_id = %s",
                    (department, item_id),
                )
            elif item_type.startswith("audit_"):
                # audit_ 접두사가 있는 감사 항목
                item_id = int(item_type.replace("audit_", ""))
                print(f"[DEBUG] 부서별 감사 항목 처리 (audit_ 접두사) - item_id: {item_id}")
                result = execute_query(
                    "UPDATE department_item_exceptions SET is_active = 0 WHERE department = %s AND item_id = %s",
                    (department, item_id),
                )
            elif item_type.startswith("manual_"):
                # ★★★ manual_ 접두사가 있는 수시 점검 항목 - 동기화 추가 ★★★
                item_id = int(item_type.replace("manual_", ""))
                print(f"[DEBUG] 부서별 수시 점검 항목 처리 (manual_ 접두사) - item_id: {item_id}")

                # 먼저 item_code 조회
                item_info = execute_query(
                    "SELECT item_code FROM manual_check_items WHERE item_id = %s",
                    (item_id, ),
                    fetch_one=True,
                )

                result = execute_query(
                    "UPDATE department_item_exceptions SET is_active = 0 WHERE department = %s AND item_id = %s AND item_type = 'manual'",
                    (department, item_id),
                )
                print(f"[DEBUG] department_item_exceptions 업데이트 결과: {result}")

                # 기존 manual_check_results 동기화
                if item_info and result > 0:
                    sync_result = self._sync_department_manual_check_results_exclusion(
                        department, item_info["item_code"], "", is_excluded=False)
                    final_message = f"부서별 제외 설정이 비활성화되었습니다. {sync_result['message']}"
                    return {
                        "success": True,
                        "message": final_message,
                        "sync_details": sync_result,
                    }

            else:
                # 교육/훈련 항목 제외 설정 제거
                print(f"[DEBUG] 부서별 교육/훈련 항목 처리 - item_type: {item_type}")
                result = execute_query(
                    "UPDATE department_extended_exceptions SET is_active = 0 WHERE department = %s AND item_id = %s",
                    (department, item_type),
                )

            print(f"[DEBUG] 부서별 제외 설정 제거 결과: {result}")

            if result > 0:
                return {
                    "success": True,
                    "message": "부서별 제외 설정이 비활성화되었습니다.",
                }
            else:
                return {
                    "success": False,
                    "message": "해당 부서별 제외 설정을 찾을 수 없습니다.",
                }

        except Exception as e:
            print(f"[ERROR] 부서별 제외 설정 제거 중 예외 발생: {str(e)}")
            return {
                "success": False,
                "message": f"부서별 제외 설정 제거 실패: {str(e)}",
            }
