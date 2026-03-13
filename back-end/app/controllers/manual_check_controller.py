# app/controllers/manual_check_controller.py
import io
import pandas as pd
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from app.services.manual_check_service import ManualCheckService
from app.utils.decorators import token_required, handle_exceptions
from app.utils.constants import HTTP_STATUS

manual_check_bp = Blueprint("manual_check", __name__)
manual_check_service = ManualCheckService()


@manual_check_bp.route("/upload/preview", methods=["POST"])
@token_required
@handle_exceptions
def preview_upload():
    """업로드 파일 미리보기"""
    if "file" not in request.files:
        return (
            jsonify({"error": "파일이 업로드되지 않았습니다."}),
            HTTP_STATUS["BAD_REQUEST"],
        )

    file = request.files["file"]
    if file.filename == "":
        return (
            jsonify({"error": "파일이 선택되지 않았습니다."}),
            HTTP_STATUS["BAD_REQUEST"],
        )

    try:
        result = manual_check_service.preview_file(file)
        
        # ✅ check_type 추가
        preview_data = {
            "success": True,
            "data": {
                **result,
                "check_type": result.get("file_type"),  # ✅ 점검 유형 코드 추가
            }
        }
        
        return jsonify(preview_data)

    except Exception as e:
        return (
            jsonify({
                "success": False,
                "error": str(e)
            }),
            HTTP_STATUS["BAD_REQUEST"],
        )

@manual_check_bp.route("/upload", methods=["POST"])
@token_required
@handle_exceptions
def bulk_upload():
    """점검 결과 일괄 업로드 - 기간 선택 필수"""
    if "file" not in request.files:
        return (
            jsonify({"error": "파일이 업로드되지 않았습니다."}),
            HTTP_STATUS["BAD_REQUEST"],
        )

    file = request.files["file"]
    if file.filename == "":
        return (
            jsonify({"error": "파일이 선택되지 않았습니다."}),
            HTTP_STATUS["BAD_REQUEST"],
        )

    # ✅ period_id 필수 파라미터로 추가
    period_id = request.form.get("period_id", type=int)
    if not period_id:
        return (
            jsonify({"error": "점검 기간을 선택해주세요."}),
            HTTP_STATUS["BAD_REQUEST"],
        )

    try:
        result = manual_check_service.process_bulk_upload(
            file=file, 
            period_id=period_id,  # ✅ period_id 전달
            uploaded_by=request.current_user["username"]
        )

        return jsonify({
            "success": True,
            "message": result["message"],
            "data": {
                "file_type": result["file_type"],
                "total_records": result["total_records"],
                "success_count": result["success_count"],
                "error_count": result["error_count"],
                "errors": (result["errors"][:10]
                           if result["errors"] else []),
            },
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), HTTP_STATUS["BAD_REQUEST"]


@manual_check_bp.route("/results", methods=["GET"])
@token_required
@handle_exceptions
def get_check_results():
    """점검 결과 목록 조회 (기존 유지)"""
    year = request.args.get("year", datetime.now().year, type=int)
    check_type = request.args.get("check_type")
    result_filter = request.args.get("result")
    search = request.args.get("search")
    page = request.args.get("page", 1, type=int)
    size = request.args.get("size", 20, type=int)

    try:
        results = manual_check_service.get_check_results(
            year=year,
            check_type=check_type,
            result_filter=result_filter,
            search=search,
            page=page,
            size=size,
        )

        # 점검 유형 매핑 정보 추가
        type_mapping = manual_check_service.get_check_type_mapping()

        # 결과 데이터 변환
        for result in results["results"]:
            result["check_type_name"] = type_mapping.get(result["check_item_code"],
                                                         result["check_item_code"])
            result["result_id"] = result["check_id"]
            result["check_result"] = result["overall_result"]
            result["user_email"] = result.get("email", "")

        return jsonify({
            "success": True,
            "data": results["results"],
            "pagination": {
                "current_page": results["page"],
                "total_pages": results["total_pages"],
                "page_size": results["size"],
                "total_count": results["total"],
            },
            "type_mapping": type_mapping,
        })

    except Exception as e:
        return (
            jsonify({
                "success": False,
                "error": str(e)
            }),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@manual_check_bp.route("/results/update", methods=["POST"])
@token_required
@handle_exceptions
def update_check_result():
    """점검 결과 수정 (기존 유지)"""
    data = request.json

    if not data or "check_id" not in data:
        return (
            jsonify({"error": "수정할 결과 ID가 필요합니다."}),
            HTTP_STATUS["BAD_REQUEST"],
        )

    try:
        result = manual_check_service.update_check_result(
            check_id=data["check_id"],
            check_result=data.get("check_result"),
            notes=data.get("notes"),
            check_type=data.get("check_type"),
        )

        return jsonify({"success": True, "message": result["message"]})

    except Exception as e:
        return (
            jsonify({
                "success": False,
                "error": str(e)
            }),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@manual_check_bp.route("/results/<int:check_id>", methods=["DELETE"])
@token_required
@handle_exceptions
def delete_check_result(check_id):
    """점검 결과 삭제 (기존 유지)"""
    try:
        result = manual_check_service.delete_check_result(check_id)

        return jsonify({"success": True, "message": result["message"]})

    except Exception as e:
        return (
            jsonify({
                "success": False,
                "error": str(e)
            }),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@manual_check_bp.route("/results/bulk-delete", methods=["POST"])
@token_required
@handle_exceptions
def bulk_delete_results():
    """점검 결과 일괄 삭제"""
    data = request.json

    if not data or "result_ids" not in data:
        return (
            jsonify({"error": "삭제할 결과 ID 목록이 필요합니다."}),
            HTTP_STATUS["BAD_REQUEST"],
        )

    result_ids = data["result_ids"]
    if not isinstance(result_ids, list) or not result_ids:
        return (
            jsonify({"error": "유효한 결과 ID 목록이 필요합니다."}),
            HTTP_STATUS["BAD_REQUEST"],
        )

    try:
        result = manual_check_service.bulk_delete_results(result_ids)

        return jsonify({
            "success": True,
            "message": result["message"],
            "deleted_count": result["deleted_count"],
        })

    except Exception as e:
        return (
            jsonify({
                "success": False,
                "error": str(e)
            }),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@manual_check_bp.route("/template", methods=["GET"])
@token_required
@handle_exceptions
def download_template():
    """업로드 템플릿 다운로드"""
    try:
        template_content = manual_check_service.generate_upload_template()

        # CSV 파일로 반환
        output = io.StringIO()
        output.write(template_content)
        output.seek(0)

        return send_file(
            io.BytesIO(output.getvalue().encode("utf-8-sig")),
            mimetype="text/csv",
            as_attachment=True,
            download_name="manual_check_template.csv",
        )

    except Exception as e:
        return (
            jsonify({
                "success": False,
                "error": f"템플릿 생성 실패: {str(e)}"
            }),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@manual_check_bp.route("/check-types", methods=["GET"])
@handle_exceptions
def get_check_types():
    """점검 유형 목록 조회"""
    try:
        type_mapping = manual_check_service.get_check_type_mapping()

        return jsonify({
            "success": True,
            "data": [{
                "code": code,
                "name": name
            } for code, name in type_mapping.items()],
        })

    except Exception as e:
        return (
            jsonify({
                "success": False,
                "error": str(e)
            }),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@manual_check_bp.route("/periods/status", methods=["GET"])
@token_required
@handle_exceptions
def get_periods_status():
    """점검 기간 현황 조회 (업로드용)"""
    try:
        year = request.args.get("year", datetime.now().year, type=int)
        
        
        # ✅ 직접 데이터베이스 쿼리로 기간 조회
        from app.utils.database import execute_query
        
        query = """
            SELECT 
                period_id,
                check_type,
                period_year,
                period_name,
                start_date,
                end_date,
                is_completed,
                completed_at,
                completed_by,
                description,
                created_at
            FROM manual_check_periods
            WHERE period_year = %s AND is_active = 1
            ORDER BY 
                CASE check_type
                    WHEN 'seal_check' THEN 1
                    WHEN 'malware_scan' THEN 2
                    WHEN 'file_encryption' THEN 3
                    ELSE 4
                END,
                start_date DESC
        """
        
        periods = execute_query(query, (year,))
        
        
        # ✅ 점검 유형별로 그룹화
        check_types = {}
        
        for period in periods:
            check_type = period["check_type"]
            
            if check_type not in check_types:
                check_types[check_type] = {
                    "periods": []
                }
            
            # ✅ 날짜를 문자열로 변환
            period_data = {
                "period_id": period["period_id"],
                "check_type": period["check_type"],
                "period_year": period["period_year"],
                "period_name": period["period_name"],
                "start_date": period["start_date"].strftime('%Y-%m-%d') if period["start_date"] else None,
                "end_date": period["end_date"].strftime('%Y-%m-%d') if period["end_date"] else None,
                "is_completed": bool(period["is_completed"]),
                "completed_at": period["completed_at"].strftime('%Y-%m-%d %H:%M:%S') if period["completed_at"] else None,
                "completed_by": period["completed_by"],
                "description": period["description"],
            }
            
            # ✅ 기간 상태 판단 (타입 통일)
            from datetime import datetime as dt, date
            now = dt.now().date()  # ✅ date 타입으로 변환
            start = period["start_date"]
            end = period["end_date"]
            
            # ✅ date 타입으로 통일
            if isinstance(start, dt):
                start = start.date()
            if isinstance(end, dt):
                end = end.date()
            
            if period["is_completed"]:
                period_data["status"] = "completed"
            elif start and end:
                if now < start:
                    period_data["status"] = "upcoming"
                elif now > end:
                    period_data["status"] = "ended"
                else:
                    period_data["status"] = "active"
            else:
                period_data["status"] = "unknown"
            
            check_types[check_type]["periods"].append(period_data)
        
        
        return jsonify({
            "success": True,
            "data": {
                "check_types": check_types
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return (
            jsonify({
                "success": False,
                "error": str(e)
            }),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )