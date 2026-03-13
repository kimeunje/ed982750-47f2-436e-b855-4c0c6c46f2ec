# app/controllers/phishing_training_controller.py
from flask import Blueprint, request, jsonify, send_file
from datetime import datetime
import io
import csv
import logging
from app.utils.decorators import handle_exceptions, admin_required, token_required
from app.utils.constants import HTTP_STATUS
from app.services.phishing_training_service import PhishingTrainingService

logger = logging.getLogger(__name__)
phishing_bp = Blueprint('phishing', __name__, url_prefix='/api/phishing-training')
phishing_service = PhishingTrainingService()

# ==================== 관리자 API ====================


@phishing_bp.route("/admin/periods", methods=["GET"])
@admin_required
@handle_exceptions
def get_training_periods():
    """훈련 기간 목록 조회"""
    year = request.args.get("year", datetime.now().year, type=int)

    try:
        periods = phishing_service.get_training_periods(year)
        return jsonify({"periods": periods})
    except Exception as e:
        logger.error(f"훈련 기간 조회 오류: {str(e)}")
        return (
            jsonify({"error": f"기간 조회 실패: {str(e)}"}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@phishing_bp.route("/admin/periods", methods=["POST"])
@admin_required
@handle_exceptions
def create_training_period():
    """훈련 기간 생성"""
    try:
        data = request.get_json()

        # 필수 필드 검증
        required_fields = [
            'training_year', 'period_name', 'training_type', 'start_date', 'end_date'
        ]
        missing_fields = [field for field in required_fields if not data.get(field)]

        if missing_fields:
            return (
                jsonify({"error": f"필수 필드가 누락되었습니다: {', '.join(missing_fields)}"}),
                HTTP_STATUS["BAD_REQUEST"],
            )

        # 날짜 형식 검증
        try:
            datetime.strptime(data['start_date'], '%Y-%m-%d')
            datetime.strptime(data['end_date'], '%Y-%m-%d')
        except ValueError:
            return (
                jsonify({"error": "날짜 형식이 올바르지 않습니다 (YYYY-MM-DD)"}),
                HTTP_STATUS["BAD_REQUEST"],
            )

        # 사용자 정보에서 생성자 추출 (실제 구현에서는 세션에서 가져와야 함)
        created_by = request.headers.get('X-User-ID', 'admin')  # 임시 처리

        period_id = phishing_service.create_training_period(data, created_by)

        return jsonify({
            "message": "훈련 기간이 생성되었습니다.",
            "period_id": period_id
        }), HTTP_STATUS["CREATED"]

    except Exception as e:
        logger.error(f"훈련 기간 생성 오류: {str(e)}")
        return (
            jsonify({"error": f"기간 생성 실패: {str(e)}"}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@phishing_bp.route("/admin/periods/<int:period_id>", methods=["PUT"])
@admin_required
@handle_exceptions
def update_training_period(period_id):
    """훈련 기간 수정"""
    try:
        data = request.get_json()

        success = phishing_service.update_training_period(period_id, data)

        if success:
            return jsonify({"message": "훈련 기간이 수정되었습니다."})
        else:
            return (
                jsonify({"error": "훈련 기간을 찾을 수 없습니다."}),
                HTTP_STATUS["NOT_FOUND"],
            )

    except Exception as e:
        logger.error(f"훈련 기간 수정 오류: {str(e)}")
        return (
            jsonify({"error": f"기간 수정 실패: {str(e)}"}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@phishing_bp.route("/admin/periods/<int:period_id>", methods=["DELETE"])
@admin_required
@handle_exceptions
def delete_training_period(period_id):
    """훈련 기간 삭제"""
    try:
        success = phishing_service.delete_training_period(period_id)

        if success:
            return jsonify({"message": "훈련 기간이 삭제되었습니다."})
        else:
            return (
                jsonify({"error": "훈련 기간을 찾을 수 없거나 관련 기록이 있습니다."}),
                HTTP_STATUS["BAD_REQUEST"],
            )

    except ValueError as e:
        return (
            jsonify({"error": str(e)}),
            HTTP_STATUS["BAD_REQUEST"],
        )
    except Exception as e:
        logger.error(f"훈련 기간 삭제 오류: {str(e)}")
        return (
            jsonify({"error": f"기간 삭제 실패: {str(e)}"}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@phishing_bp.route("/admin/upload", methods=["POST"])
@admin_required
@handle_exceptions
def upload_training_data():
    """엑셀 파일 업로드"""
    try:
        if 'file' not in request.files:
            return (
                jsonify({"error": "파일이 업로드되지 않았습니다."}),
                HTTP_STATUS["BAD_REQUEST"],
            )

        file = request.files['file']
        period_id = request.form.get('period_id', type=int)

        if not period_id:
            return (
                jsonify({"error": "훈련 기간을 선택해주세요."}),
                HTTP_STATUS["BAD_REQUEST"],
            )

        if file.filename == '':
            return (
                jsonify({"error": "파일이 선택되지 않았습니다."}),
                HTTP_STATUS["BAD_REQUEST"],
            )

        # 파일 확장자 검증
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            return (
                jsonify({"error": "엑셀 파일만 업로드 가능합니다."}),
                HTTP_STATUS["BAD_REQUEST"],
            )

        # 사용자 정보 추출
        uploaded_by = request.headers.get('X-User-ID', 'admin')  # 임시 처리

        # 파일 처리
        result = phishing_service.upload_training_data(file, period_id, uploaded_by)

        if result['success']:
            return jsonify({
                "message": "데이터 업로드가 완료되었습니다.",
                "total_rows": result['total_rows'],
                "success_count": result['success_count'],
                "error_count": result['error_count'],
                "errors": result['errors']
            })
        else:
            return (
                jsonify({"error": result['error']}),
                HTTP_STATUS["BAD_REQUEST"],
            )

    except Exception as e:
        logger.error(f"파일 업로드 오류: {str(e)}")
        return (
            jsonify({"error": f"업로드 실패: {str(e)}"}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@phishing_bp.route("/admin/records", methods=["GET"])
@admin_required
@handle_exceptions
def get_training_records():
    """훈련 기록 조회"""
    year = request.args.get("year", datetime.now().year, type=int)
    period_id = request.args.get("period_id", type=int)

    try:
        records = phishing_service.get_training_records(year, period_id)
        return jsonify({"records": records})
    except Exception as e:
        logger.error(f"훈련 기록 조회 오류: {str(e)}")
        return (
            jsonify({"error": f"기록 조회 실패: {str(e)}"}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@phishing_bp.route("/admin/records/<int:training_id>", methods=["PUT"])
@admin_required
@handle_exceptions
def update_training_record(training_id):
    """훈련 기록 수정"""
    try:
        data = request.get_json()

        success = phishing_service.update_training_record(training_id, data)

        if success:
            return jsonify({"message": "훈련 기록이 수정되었습니다."})
        else:
            return (
                jsonify({"error": "훈련 기록을 찾을 수 없습니다."}),
                HTTP_STATUS["NOT_FOUND"],
            )

    except Exception as e:
        logger.error(f"훈련 기록 수정 오류: {str(e)}")
        return (
            jsonify({"error": f"기록 수정 실패: {str(e)}"}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@phishing_bp.route("/admin/records/<int:training_id>", methods=["DELETE"])
@admin_required
@handle_exceptions
def delete_training_record(training_id):
    """훈련 기록 삭제"""
    try:
        success = phishing_service.delete_training_record(training_id)

        if success:
            return jsonify({"message": "훈련 기록이 삭제되었습니다."})
        else:
            return (
                jsonify({"error": "훈련 기록을 찾을 수 없습니다."}),
                HTTP_STATUS["NOT_FOUND"],
            )

    except Exception as e:
        logger.error(f"훈련 기록 삭제 오류: {str(e)}")
        return (
            jsonify({"error": f"기록 삭제 실패: {str(e)}"}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@phishing_bp.route("/admin/export", methods=["GET"])
@admin_required
@handle_exceptions
def export_training_data():
    """훈련 데이터 CSV 내보내기"""
    year = request.args.get("year", datetime.now().year, type=int)
    format_type = request.args.get("format", "csv")

    try:
        if format_type != "csv":
            return (
                jsonify({"error": "현재 CSV 형식만 지원됩니다."}),
                HTTP_STATUS["BAD_REQUEST"],
            )

        records = phishing_service.get_training_records(year)

        if not records:
            return (
                jsonify({"error": f"{year}년 훈련 데이터가 없습니다."}),
                HTTP_STATUS["NOT_FOUND"],
            )

        # CSV 생성
        output = io.StringIO()
        writer = csv.writer(output)

        # 헤더 작성
        headers = [
            "사용자ID", "이름", "부서", "이메일", "훈련연도", "기간명", "훈련유형", "메일발송시각", "수행시각", "로그유형",
            "메일유형", "대상이메일", "훈련결과", "응답시간(분)", "상태", "제외여부", "제외사유", "비고"
        ]
        writer.writerow(headers)

        # 데이터 작성
        for record in records:
            row = [
                record["username"],
                record["username"],  # 실제로는 사용자 이름 필드가 필요
                record["department"],
                record["email"],
                record["training_year"],
                record["period_name"],
                record["training_type"],
                record["email_sent_time"],
                record["action_time"],
                record["log_type"],
                record["mail_type"],
                record["target_email"],
                record["training_result"],
                record["response_time_minutes"],
                record["status_text"],
                "예" if record["exclude_from_scoring"] else "아니오",
                record["exclude_reason"] or "",
                record["notes"] or ""
            ]
            writer.writerow(row)

        # 파일 반환
        output.seek(0)
        csv_data = output.getvalue().encode('utf-8-sig')  # BOM 추가
        output.close()

        return send_file(io.BytesIO(csv_data), mimetype='text/csv', as_attachment=True,
                         download_name=f'phishing_training_{year}.csv')

    except Exception as e:
        logger.error(f"데이터 내보내기 오류: {str(e)}")
        return (
            jsonify({"error": f"내보내기 실패: {str(e)}"}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@phishing_bp.route("/admin/statistics", methods=["GET"])
@admin_required
@handle_exceptions
def get_training_statistics():
    """훈련 통계 조회"""
    year = request.args.get("year", datetime.now().year, type=int)

    try:
        stats = phishing_service.get_training_statistics(year)
        return jsonify(stats)
    except Exception as e:
        logger.error(f"통계 조회 오류: {str(e)}")
        return (
            jsonify({"error": f"통계 조회 실패: {str(e)}"}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


# ==================== 사용자 API ====================


@phishing_bp.route("/user/status", methods=["GET"])
@token_required
@handle_exceptions
def get_user_training_status():
    """사용자 훈련 현황 조회"""
    year = request.args.get("year", datetime.now().year, type=int)

    try:
        # 사용자 정보 추출 (실제 구현에서는 세션에서 가져와야 함)
        user_id = request.headers.get('X-User-ID')  # 임시 처리

        if not user_id:
            return (
                jsonify({"error": "사용자 인증이 필요합니다."}),
                HTTP_STATUS["UNAUTHORIZED"],
            )

        # 사용자 훈련 기록 조회
        records = phishing_service.get_training_records(year)
        user_records = [r for r in records if r['username'] == user_id]

        # 사용자별 통계 계산
        total_trainings = len(user_records)
        success_count = len(
            [r for r in user_records if r['training_result'] == 'success'])
        fail_count = len([r for r in user_records if r['training_result'] == 'fail'])
        no_response_count = len(
            [r for r in user_records if r['training_result'] == 'no_response'])

        success_rate = (success_count / total_trainings *
                        100) if total_trainings > 0 else 0

        return jsonify({
            "year": year,
            "total_trainings": total_trainings,
            "success_count": success_count,
            "fail_count": fail_count,
            "no_response_count": no_response_count,
            "success_rate": round(success_rate, 2),
            "records": user_records
        })

    except Exception as e:
        logger.error(f"사용자 훈련 현황 조회 오류: {str(e)}")
        return (
            jsonify({"error": f"현황 조회 실패: {str(e)}"}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@phishing_bp.route("/user/periods", methods=["GET"])
@token_required
@handle_exceptions
def get_active_training_periods():
    """진행중인 훈련 기간 조회 (사용자용)"""
    year = request.args.get("year", datetime.now().year, type=int)

    try:
        periods = phishing_service.get_training_periods(year)

        # 진행중이거나 예정된 기간만 필터링
        active_periods = []
        for period_type in periods:
            active_type_periods = []
            for period in period_type['periods']:
                if period['status'] in ['진행중', '예정됨']:
                    # 사용자에게는 민감한 정보 제외
                    user_period = {
                        'period_id': period['period_id'],
                        'period_name': period['period_name'],
                        'training_type': period['training_type'],
                        'start_date': period['start_date'],
                        'end_date': period['end_date'],
                        'status': period['status'],
                        'description': period['description']
                    }
                    active_type_periods.append(user_period)

            if active_type_periods:
                active_periods.append({
                    'type_name': period_type['type_name'],
                    'periods': active_type_periods
                })

        return jsonify({"periods": active_periods})

    except Exception as e:
        logger.error(f"진행중인 훈련 기간 조회 오류: {str(e)}")
        return (
            jsonify({"error": f"기간 조회 실패: {str(e)}"}),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


# 에러 핸들러 등록
@phishing_bp.errorhandler(404)
def not_found(error):
    return jsonify({"error": "요청한 리소스를 찾을 수 없습니다."}), 404


@phishing_bp.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "서버 내부 오류가 발생했습니다."}), 500
