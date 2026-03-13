# app/controllers/exception_controller.py
from datetime import datetime, date
from flask import Blueprint, request, jsonify
from app.services.admin_exception_service import ExceptionService
from app.utils.decorators import admin_required, validate_json, handle_exceptions
from app.utils.constants import HTTP_STATUS
from app.utils.database import execute_query

exception_bp = Blueprint("exception", __name__)
exception_service = ExceptionService()


@exception_bp.route("/summary", methods=["GET"])
@admin_required
@handle_exceptions
def get_exception_summary():
    """제외 설정 요약 통계"""
    summary = exception_service.get_exception_summary()
    return jsonify(summary)


@exception_bp.route("/search-users", methods=["GET"])
@admin_required
@handle_exceptions
def search_users():
    """사용자 검색 (새로운 엔드포인트)"""
    search_query = request.args.get("q", "")
    department = request.args.get("department", "")
    limit = request.args.get("limit", 50, type=int)

    users = exception_service.search_users(search_query, department, limit)
    return jsonify(users)


@exception_bp.route("/available-items", methods=["GET"])
@admin_required
@handle_exceptions
def get_available_items():
    """제외 설정 가능한 항목들 조회 (카테고리별)"""
    items = exception_service.get_available_items()
    return jsonify(items)


@exception_bp.route(
    "/check-user-training/<int:user_id>/<int:year>/<string:training_period>",
    methods=["GET"],
)
@admin_required
@handle_exceptions
def check_user_training_exception_by_year(user_id, year, training_period):
    """특정 사용자의 특정 연도/기간 모의훈련 제외 설정 확인"""
    result = exception_service.is_training_excluded_for_user(user_id, year,
                                                             training_period)
    return jsonify(result)


@exception_bp.route(
    "/check-user-education/<int:user_id>/<int:year>",
    methods=["GET"],
)
@admin_required
@handle_exceptions
def check_user_education_exception_by_year(user_id, year):
    """특정 사용자의 특정 연도/기간 교육 제외 설정 확인"""
    result = exception_service.is_education_excluded_for_user(user_id, year)
    return jsonify(result)


@exception_bp.route("/check-user-item-by-year", methods=["GET"])
@admin_required
@handle_exceptions
def check_user_item_exception_by_year():
    """특정 사용자의 특정 연도 항목 제외 설정 확인 (다중 조회)"""
    user_id = request.args.get("user_id", type=int)
    year = request.args.get("year", type=int)
    item_type = request.args.get("item_type")  # 'training' 또는 'education'

    if not all([user_id, year, item_type]):
        return jsonify({"error": "user_id, year, item_type이 모두 필요합니다."}), 400

    results = {}

    if item_type == "training":
        for period in ["first_half", "second_half"]:
            result = exception_service.is_training_excluded_for_user(
                user_id, year, period)
            results[period] = result
    elif item_type == "education":
        for period in ["first_half", "second_half"]:
            result = exception_service.is_education_excluded_for_user(
                user_id, year, period)
            results[period] = result
    else:
        return (
            jsonify({"error": "item_type은 'training' 또는 'education'이어야 합니다."}),
            400,
        )

    return jsonify({
        "user_id": user_id,
        "year": year,
        "item_type": item_type,
        "results": results
    })


@exception_bp.route("/available-items-by-year", methods=["GET"])
@admin_required
@handle_exceptions
def get_available_items_by_year():
    """연도별 제외 설정 가능한 항목들 조회"""
    year = request.args.get("year", datetime.now().year, type=int)

    # 특정 연도의 항목만 반환
    items = exception_service.get_available_items()

    # 연도 필터링
    filtered_items = {}

    # 정보보안 감사는 연도와 무관
    filtered_items["정보보안 감사"] = items.get("정보보안 감사", [])

    # 교육과 훈련은 해당 연도만 필터링
    filtered_items["정보보호 교육"] = [
        item for item in items.get("정보보호 교육", []) if item.get("year") == year
    ]

    filtered_items["악성메일 모의훈련"] = [
        item for item in items.get("악성메일 모의훈련", []) if item.get("year") == year
    ]

    return jsonify(filtered_items)


@exception_bp.route("/check-user-training/<int:user_id>/<string:training_period>",
                    methods=["GET"])
@admin_required
@handle_exceptions
def check_user_training_exception(user_id, training_period):
    """특정 사용자-모의훈련 기간의 제외 설정 확인"""
    item_id = f"training_{training_period}"
    result = exception_service.is_item_excluded_for_user(user_id, item_id)
    return jsonify(result)


@exception_bp.route("/user-exceptions", methods=["GET"])
@admin_required
@handle_exceptions
def get_user_exceptions():
    """사용자별 제외 설정 목록 조회"""
    user_id = request.args.get("user_id", type=int)
    item_id = request.args.get("item_id", type=int)

    exceptions = exception_service.get_user_exceptions(user_id, item_id)
    return jsonify(exceptions)


@exception_bp.route("/department-exceptions", methods=["GET"])
@admin_required
@handle_exceptions
def get_department_exceptions():
    """부서별 제외 설정 목록 조회"""
    department = request.args.get("department")
    item_id = request.args.get("item_id", type=int)

    exceptions = exception_service.get_department_exceptions(department, item_id)
    return jsonify(exceptions)


@exception_bp.route("/user-exceptions", methods=["POST"])
@admin_required
@validate_json(["user_id", "item_type", "exclude_reason"])
@handle_exceptions
def add_user_exception():
    """사용자별 제외 설정 추가 (완전 수정된 버전)"""
    data = request.json
    current_user = request.current_user

    print(f"[DEBUG] 받은 데이터: {data}")

    # 날짜 변환
    start_date = None
    end_date = None

    if data.get("start_date"):
        try:
            start_date = datetime.strptime(data["start_date"], "%Y-%m-%d").date()
        except ValueError:
            return (
                jsonify({"error": "시작일 형식이 올바르지 않습니다. (YYYY-MM-DD)"}),
                HTTP_STATUS["BAD_REQUEST"],
            )

    if data.get("end_date"):
        try:
            end_date = datetime.strptime(data["end_date"], "%Y-%m-%d").date()
        except ValueError:
            return (
                jsonify({"error": "종료일 형식이 올바르지 않습니다. (YYYY-MM-DD)"}),
                HTTP_STATUS["BAD_REQUEST"],
            )

    # 임시 제외의 경우 날짜 검증
    if data.get("exclude_type") == "temporary":
        if not start_date or not end_date:
            return (
                jsonify({"error": "임시 제외의 경우 시작일과 종료일이 필요합니다."}),
                HTTP_STATUS["BAD_REQUEST"],
            )
        if end_date <= start_date:
            return (
                jsonify({"error": "종료일은 시작일보다 늦어야 합니다."}),
                HTTP_STATUS["BAD_REQUEST"],
            )

    # 사용자 존재 확인
    user_exists = execute_query("SELECT uid FROM users WHERE uid = %s",
                                (data["user_id"], ), fetch_one=True)

    if not user_exists:
        return (
            jsonify({"error": "존재하지 않는 사용자입니다."}),
            HTTP_STATUS["BAD_REQUEST"],
        )

    # 서비스 호출 - 올바른 파라미터명 사용
    result = exception_service.add_user_exception(
        user_uid=data["user_id"],  # user_id -> user_uid
        item_id=data["item_type"],  # item_type을 item_id로 전달
        item_type=data["item_type"],
        item_name=data.get("item_name", ""),
        item_category=data.get("item_category", ""),
        exclude_reason=data["exclude_reason"],
        exclude_type=data.get("exclude_type", "permanent"),
        start_date=start_date,
        end_date=end_date,
        created_by=current_user["username"],
    )

    print(f"[DEBUG] 서비스 결과: {result}")

    if result["success"]:
        return jsonify(result)
    else:
        print(f"[ERROR] 제외 설정 추가 실패: {result}")
        return jsonify(result), HTTP_STATUS["BAD_REQUEST"]


# 부서별 제외 설정도 동일하게 수정
@exception_bp.route("/department-exceptions", methods=["POST"])
@admin_required
@validate_json(["department", "item_type", "exclude_reason"])
@handle_exceptions
def add_department_exception():
    """부서별 제외 설정 추가 (완전 수정된 버전)"""
    data = request.json
    current_user = request.current_user

    print(f"[DEBUG] 부서별 제외 설정 - 받은 데이터: {data}")

    # 날짜 변환 로직 (위와 동일)
    start_date = None
    end_date = None

    if data.get("start_date"):
        try:
            start_date = datetime.strptime(data["start_date"], "%Y-%m-%d").date()
        except ValueError:
            return (
                jsonify({"error": "시작일 형식이 올바르지 않습니다. (YYYY-MM-DD)"}),
                HTTP_STATUS["BAD_REQUEST"],
            )

    if data.get("end_date"):
        try:
            end_date = datetime.strptime(data["end_date"], "%Y-%m-%d").date()
        except ValueError:
            return (
                jsonify({"error": "종료일 형식이 올바르지 않습니다. (YYYY-MM-DD)"}),
                HTTP_STATUS["BAD_REQUEST"],
            )

    # 임시 제외의 경우 날짜 검증
    if data.get("exclude_type") == "temporary":
        if not start_date or not end_date:
            return (
                jsonify({"error": "임시 제외의 경우 시작일과 종료일이 필요합니다."}),
                HTTP_STATUS["BAD_REQUEST"],
            )
        if end_date <= start_date:
            return (
                jsonify({"error": "종료일은 시작일보다 늦어야 합니다."}),
                HTTP_STATUS["BAD_REQUEST"],
            )

    result = exception_service.add_department_exception(
        department=data["department"],
        item_type=data["item_type"],
        item_name=data.get("item_name", ""),
        exclude_reason=data["exclude_reason"],
        exclude_type=data.get("exclude_type", "permanent"),
        start_date=start_date,
        end_date=end_date,
        created_by=current_user["username"],
    )

    print(f"[DEBUG] 부서별 제외 설정 서비스 결과: {result}")

    if result["success"]:
        return jsonify(result)
    else:
        return jsonify(result), HTTP_STATUS["BAD_REQUEST"]


@exception_bp.route("/user-exceptions/<int:user_id>/<string:item_type>",
                    methods=["DELETE"])
@admin_required
@handle_exceptions
def remove_user_exception(user_id, item_type):
    """사용자별 제외 설정 제거 (개선된 버전)"""
    result = exception_service.remove_user_exception(user_id, item_type)

    if result["success"]:
        return jsonify(result)
    else:
        return jsonify(result), HTTP_STATUS["BAD_REQUEST"]


@exception_bp.route("/department-exceptions/<string:department>/<string:item_type>",
                    methods=["DELETE"])
@admin_required
@handle_exceptions
def remove_department_exception(department, item_type):
    """부서별 제외 설정 제거 (개선된 버전)"""
    result = exception_service.remove_department_exception(department, item_type)

    if result["success"]:
        return jsonify(result)
    else:
        return jsonify(result), HTTP_STATUS["BAD_REQUEST"]


@exception_bp.route("/departments", methods=["GET"])
@admin_required
@handle_exceptions
def get_departments():
    """모든 부서 목록 조회"""
    departments = exception_service.get_all_departments()
    return jsonify(departments)


@exception_bp.route("/items", methods=["GET"])
@admin_required
@handle_exceptions
def get_checklist_items():
    """점검 항목 목록 조회 - checklist_items와 manual_check_items 통합"""
    check_type = request.args.get("check_type")  # 'daily', 'manual' 또는 전체

    try:
        items = []

        if check_type != "manual":
            # checklist_items에서 일반 감사 항목 조회
            if check_type:
                condition = "WHERE check_type = %s"
                params = (check_type, )
            else:
                condition = ""
                params = ()

            checklist_items = execute_query(
                f"""
                SELECT 
                    CONCAT('audit_', item_id) as item_id,
                    item_name, 
                    category, 
                    description, 
                    check_type, 
                    penalty_weight,
                    'audit' as source_table
                FROM checklist_items
                {condition}
                ORDER BY check_type, category, item_name
                """,
                params,
                fetch_all=True,
            )
            items.extend(checklist_items)

        if check_type != "daily":
            # manual_check_items에서 수시 점검 항목 조회
            manual_items = execute_query(
                """
                SELECT 
                    CONCAT('manual_', item_id) as item_id,
                    item_name, 
                    item_category as category, 
                    description, 
                    'manual' as check_type, 
                    penalty_weight,
                    'manual' as source_table
                FROM manual_check_items
                WHERE is_active = 1
                ORDER BY item_category, item_name
                """,
                fetch_all=True,
            )
            items.extend(manual_items)

        return jsonify(items)

    except Exception as e:
        return (
            jsonify({"error": f"항목 목록 조회 실패: {str(e)}"}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@exception_bp.route("/users", methods=["GET"])
@admin_required
@handle_exceptions
def get_users():
    """사용자 목록 조회"""
    department = request.args.get("department")

    if department:
        condition = "WHERE department = %s"
        params = (department, )
    else:
        condition = ""
        params = ()

    users = execute_query(
        f"""
        SELECT uid, user_id, username, department, mail
        FROM users
        {condition}
        ORDER BY department, username
        """,
        params,
        fetch_all=True,
    )

    return jsonify(users)


@exception_bp.route("/check-user-item/<int:user_id>/<int:item_id>", methods=["GET"])
@admin_required
@handle_exceptions
def check_user_item_exception(user_id, item_id):
    """특정 사용자-항목의 제외 설정 확인"""
    result = exception_service.is_item_excluded_for_user(user_id, item_id)
    return jsonify(result)


@exception_bp.route("/bulk-add", methods=["POST"])
@admin_required
@validate_json(["exceptions"])
@handle_exceptions
def bulk_add_exceptions():
    """제외 설정 일괄 추가"""
    data = request.json
    exceptions = data["exceptions"]
    current_user = request.current_user

    if not exceptions or len(exceptions) == 0:
        return (
            jsonify({"error": "추가할 제외 설정이 없습니다."}),
            HTTP_STATUS["BAD_REQUEST"],
        )

    success_count = 0
    error_list = []

    for exception in exceptions:
        try:
            # 필수 필드 검증
            required_fields = ["exclude_reason"]
            if "user_id" in exception and "item_id" in exception:
                # 사용자별 제외
                required_fields.extend(["user_id", "item_id"])

                # 날짜 처리
                start_date = None
                end_date = None
                if exception.get("start_date"):
                    start_date = datetime.strptime(exception["start_date"],
                                                   "%Y-%m-%d").date()
                if exception.get("end_date"):
                    end_date = datetime.strptime(exception["end_date"],
                                                 "%Y-%m-%d").date()

                result = exception_service.add_user_exception(
                    user_id=exception["user_id"],
                    item_id=exception["item_id"],
                    exclude_reason=exception["exclude_reason"],
                    exclude_type=exception.get("exclude_type", "permanent"),
                    start_date=start_date,
                    end_date=end_date,
                    created_by=current_user["username"],
                )

            elif "department" in exception and "item_id" in exception:
                # 부서별 제외
                required_fields.extend(["department", "item_id"])

                # 날짜 처리
                start_date = None
                end_date = None
                if exception.get("start_date"):
                    start_date = datetime.strptime(exception["start_date"],
                                                   "%Y-%m-%d").date()
                if exception.get("end_date"):
                    end_date = datetime.strptime(exception["end_date"],
                                                 "%Y-%m-%d").date()

                result = exception_service.add_department_exception(
                    department=exception["department"],
                    item_id=exception["item_id"],
                    exclude_reason=exception["exclude_reason"],
                    exclude_type=exception.get("exclude_type", "permanent"),
                    start_date=start_date,
                    end_date=end_date,
                    created_by=current_user["username"],
                )
            else:
                error_list.append({
                    "exception": exception,
                    "error": "user_id 또는 department 중 하나와 item_id가 필요합니다.",
                })
                continue

            if result["success"]:
                success_count += 1
            else:
                error_list.append({"exception": exception, "error": result["message"]})

        except Exception as e:
            error_list.append({"exception": exception, "error": str(e)})

    return jsonify({
        "success_count": success_count,
        "total_count": len(exceptions),
        "error_count": len(error_list),
        "errors": error_list,
    })


@exception_bp.route("/export", methods=["GET"])
@admin_required
@handle_exceptions
def export_exceptions():
    """제외 설정 내보내기"""
    export_format = request.args.get("format", "json")  # json 또는 csv

    user_exceptions = exception_service.get_user_exceptions()
    dept_exceptions = exception_service.get_department_exceptions()

    if export_format == "csv":
        import csv
        from io import StringIO

        output = StringIO()
        writer = csv.writer(output)

        # 헤더 작성
        writer.writerow([
            "유형",
            "사용자ID",
            "사용자명",
            "부서",
            "항목ID",
            "항목명",
            "카테고리",
            "제외사유",
            "제외유형",
            "시작일",
            "종료일",
            "생성자",
            "생성일",
        ])

        # 사용자별 제외 설정
        for exc in user_exceptions:
            writer.writerow([
                "사용자별",
                exc["user_login_id"],
                exc["username"],
                exc["department"],
                exc["item_id"],
                exc["item_name"],
                exc["category"],
                exc["exclude_reason"],
                exc["exclude_type"],
                exc["start_date"] or "",
                exc["end_date"] or "",
                exc["created_by"],
                exc["created_at"],
            ])

        # 부서별 제외 설정
        for exc in dept_exceptions:
            writer.writerow([
                "부서별",
                "",
                "",
                exc["department"],
                exc["item_id"],
                exc["item_name"],
                exc["category"],
                exc["exclude_reason"],
                exc["exclude_type"],
                exc["start_date"] or "",
                exc["end_date"] or "",
                exc["created_by"],
                exc["created_at"],
            ])

        csv_data = output.getvalue()
        output.close()

        from flask import make_response

        response = make_response(csv_data)
        response.headers["Content-Type"] = "text/csv; charset=utf-8"
        response.headers["Content-Disposition"] = (
            "attachment; filename=exception_settings.csv")
        return response

    else:
        # JSON 형식
        return jsonify({
            "user_exceptions": user_exceptions,
            "department_exceptions": dept_exceptions,
            "export_date": datetime.now().isoformat(),
            "total_user_exceptions": len(user_exceptions),
            "total_department_exceptions": len(dept_exceptions),
        })
