# back-end/app/controllers/auth_controller.py - IP 인증으로 수정

from flask import Blueprint, request, jsonify, current_app
from app.services.auth_service import AuthService
from app.utils.decorators import token_required, validate_json, handle_exceptions
from app.utils.constants import HTTP_STATUS, MESSAGES

auth_bp = Blueprint('auth', __name__)
auth_service = AuthService()


@auth_bp.route("/check-ip", methods=["POST"])
@handle_exceptions
def check_ip_authentication():
    """IP 기반 인증 확인 (강화된 디버깅)"""
    # 클라이언트 IP 추출
    client_ip = auth_service.get_client_ip(request)

    # 요청 관련 상세 디버깅
    current_app.logger.info(f"[CHECK_IP_DEBUG] === /check-ip 요청 시작 ===")
    current_app.logger.info(f"[CHECK_IP_DEBUG] 클라이언트 IP: {client_ip}")
    current_app.logger.info(f"[CHECK_IP_DEBUG] 요청 메서드: {request.method}")
    current_app.logger.info(f"[CHECK_IP_DEBUG] Content-Type: {request.content_type}")
    current_app.logger.info(
        f"[CHECK_IP_DEBUG] Content-Length: {request.content_length}")
    current_app.logger.info(
        f"[CHECK_IP_DEBUG] User-Agent: {request.headers.get('User-Agent', 'N/A')}")

    # 모든 헤더 로깅
    current_app.logger.info(f"[CHECK_IP_DEBUG] 모든 요청 헤더:")
    for header_name, header_value in request.headers:
        current_app.logger.info(f"[CHECK_IP_DEBUG]   {header_name}: {header_value}")

    # Raw 데이터 확인
    try:
        raw_data = request.get_data()
        current_app.logger.info(
            f"[CHECK_IP_DEBUG] Raw 요청 데이터 길이: {len(raw_data) if raw_data else 0}")
        if raw_data:
            current_app.logger.info(
                f"[CHECK_IP_DEBUG] Raw 데이터: {raw_data.decode('utf-8', errors='ignore')}"
            )
    except Exception as raw_error:
        current_app.logger.error(f"[CHECK_IP_DEBUG] Raw 데이터 읽기 실패: {str(raw_error)}")

    try:
        current_app.logger.info(f"[CHECK_IP_DEBUG] authenticate_by_ip 호출 시작")

        # IP 기반 인증
        result = auth_service.authenticate_by_ip(client_ip)

        current_app.logger.info(f"[CHECK_IP_DEBUG] authenticate_by_ip 완료")
        current_app.logger.info(
            f"[CHECK_IP_DEBUG] 인증 결과: success={result.get('success')}")
        current_app.logger.info(f"[CHECK_IP_DEBUG] 인증 결과 상세: {result}")

        if result["success"]:
            response_data = {
                "success": True,
                "email": result["email"],
                "username": result["username"],
                "name": result["name"],
                "dept": result["dept"],
                "role": result.get("role", "user"),
                "client_ip": client_ip,
            }

            current_app.logger.info(f"[CHECK_IP_DEBUG] 성공 응답 생성: {response_data}")
            current_app.logger.info(f"[CHECK_IP_DEBUG] === /check-ip 성공 완료 ===")

            return jsonify(response_data)
        else:
            current_app.logger.warning(f"[CHECK_IP_DEBUG] 인증 실패: {result}")

            # 에러 코드에 따른 HTTP 상태 코드 설정
            if result.get("code") == "OUTSIDE_BUSINESS_HOURS":
                status_code = HTTP_STATUS["FORBIDDEN"]
            elif result.get("code") in ["IP_RANGE_NOT_ALLOWED", "USER_NOT_FOUND"]:
                status_code = HTTP_STATUS["UNAUTHORIZED"]
            else:
                status_code = HTTP_STATUS["UNAUTHORIZED"]

            error_response = {
                "success": False,
                "message": result["message"],
                "code": result.get("code", "AUTH_FAILED"),
            }

            current_app.logger.warning(
                f"[CHECK_IP_DEBUG] 실패 응답: {error_response}, status={status_code}")
            current_app.logger.info(f"[CHECK_IP_DEBUG] === /check-ip 실패 완료 ===")

            return jsonify(error_response), status_code

    except Exception as e:
        current_app.logger.error(f"[CHECK_IP_DEBUG] /check-ip 예외 발생: {str(e)}")
        import traceback

        current_app.logger.error(f"[CHECK_IP_DEBUG] 스택 트레이스: {traceback.format_exc()}")
        current_app.logger.error(f"[CHECK_IP_DEBUG] === /check-ip 예외 완료 ===")

        return (
            jsonify({
                "success": False,
                "message": "IP 인증 처리 중 오류가 발생했습니다.",
                "code": "AUTH_ERROR",
            }),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@auth_bp.route('/email-verification', methods=['POST'])
@handle_exceptions
@validate_json(['email'])
def send_verification():
    """이메일 인증 코드 발송 (기존 유지)"""
    data = request.json
    email = data.get("email")

    result = auth_service.send_verification_code(email)

    if result["success"]:
        return jsonify(result)
    else:
        return jsonify(result), HTTP_STATUS['BAD_REQUEST']


@auth_bp.route('/verify-and-login', methods=['POST'])
@handle_exceptions
@validate_json(['email', 'code', 'username'])
def verify_and_login():
    """인증 코드 확인 및 로그인 (IP 기반으로 수정)"""
    data = request.json
    email = data.get("email")
    code = data.get("code")
    username = data.get("username")

    # 클라이언트 IP 추출
    client_ip = auth_service.get_client_ip(request)
    current_app.logger.info(f"최종 로그인 시도: {username} ({client_ip})")

    # 1. 인증 코드 확인
    if not auth_service.verify_code(email, code):
        current_app.logger.warning(f"잘못된 인증 코드: {email}")
        return jsonify({
            "success": False,
            "message": MESSAGES['INVALID_VERIFICATION_CODE'],
        }), HTTP_STATUS['BAD_REQUEST']

    # 2. IP 기반 재인증 (보안 강화)
    auth_result = auth_service.authenticate_by_ip(client_ip)

    if not auth_result["success"]:
        current_app.logger.warning(f"IP 재인증 실패: {client_ip}")
        return jsonify({
            "success": False,
            "message": auth_result["message"]
        }), HTTP_STATUS['UNAUTHORIZED']

    # 3. 사용자명 일치 확인
    if auth_result["username"] != username:
        current_app.logger.warning(
            f"사용자명 불일치: 요청={username}, IP인증={auth_result['username']}")
        return jsonify({
            "success": False,
            "message": "인증 정보가 일치하지 않습니다."
        }), HTTP_STATUS['UNAUTHORIZED']

    # 4. JWT 토큰 생성 (IP 정보 포함)
    token = auth_service.generate_token(username, auth_result, client_ip)

    # 5. 인증 코드 삭제 (사용 완료)
    auth_service.clear_verification_code(email)

    # 6. 성공 로그 기록
    current_app.logger.info(
        f"로그인 성공: {username} ({auth_result['name']}) from {client_ip}")

    # 7. 토큰 반환
    response = jsonify({"success": True, "message": MESSAGES['LOGIN_SUCCESS']})
    response.set_cookie(
        "auth_token",
        token,
        httponly=True,
        max_age=current_app.config['TOKEN_EXPIRATION'],
        samesite="Lax",
        domain=None,
        path="/",
    )

    return response


@auth_bp.route('/me', methods=['GET'])
@token_required
@handle_exceptions
def get_user_info():
    """사용자 정보 조회 (IP 정보 추가)"""
    user = request.current_user

    return jsonify({
        "authenticated": True,
        "username": user["username"],
        "name": user.get("name", "사용자"),
        "dept": user.get("dept", "부서없음"),
        "role": user.get("role", "user"),
        "client_ip": user.get("client_ip")
    })


@auth_bp.route('/logout', methods=['POST'])
@handle_exceptions
def logout():
    """로그아웃 (IP 로그 추가)"""
    client_ip = auth_service.get_client_ip(request)
    current_app.logger.info(f"로그아웃: IP {client_ip}")

    response = jsonify({"success": True, "message": MESSAGES['LOGOUT_SUCCESS']})
    response.delete_cookie("auth_token")
    return response


@auth_bp.route("/authenticate", methods=["POST"])
@handle_exceptions
@validate_json(["username"])
def authenticate():
    """사용자 인증 및 감사 로그 초기화 (강화된 디버깅)"""
    client_ip = auth_service.get_client_ip(request)

    # 요청 관련 상세 디버깅
    current_app.logger.info(f"[AUTHENTICATE_DEBUG] === /authenticate 요청 시작 ===")
    current_app.logger.info(f"[AUTHENTICATE_DEBUG] 클라이언트 IP: {client_ip}")
    current_app.logger.info(f"[AUTHENTICATE_DEBUG] 요청 메서드: {request.method}")
    current_app.logger.info(
        f"[AUTHENTICATE_DEBUG] Content-Type: {request.content_type}")
    current_app.logger.info(
        f"[AUTHENTICATE_DEBUG] Content-Length: {request.content_length}")
    current_app.logger.info(
        f"[AUTHENTICATE_DEBUG] User-Agent: {request.headers.get('User-Agent', 'N/A')}")

    # 모든 헤더 로깅
    current_app.logger.info(f"[AUTHENTICATE_DEBUG] 모든 요청 헤더:")
    for header_name, header_value in request.headers:
        current_app.logger.info(f"[AUTHENTICATE_DEBUG]   {header_name}: {header_value}")

    # Raw 데이터 확인
    try:
        raw_data = request.get_data()
        current_app.logger.info(
            f"[AUTHENTICATE_DEBUG] Raw 요청 데이터 길이: {len(raw_data) if raw_data else 0}")
        if raw_data:
            current_app.logger.info(
                f"[AUTHENTICATE_DEBUG] Raw 데이터: {raw_data.decode('utf-8', errors='ignore')}"
            )
    except Exception as raw_error:
        current_app.logger.error(
            f"[AUTHENTICATE_DEBUG] Raw 데이터 읽기 실패: {str(raw_error)}")

    try:
        # JSON 파싱 시도
        current_app.logger.info(f"[AUTHENTICATE_DEBUG] JSON 파싱 시도")
        data = request.json
        current_app.logger.info(f"[AUTHENTICATE_DEBUG] 파싱된 JSON: {data}")

        if data is None:
            current_app.logger.error(f"[AUTHENTICATE_DEBUG] JSON 파싱 결과가 None")
            return (
                jsonify({
                    "status": "failed",
                    "message": "JSON 데이터가 없거나 파싱에 실패했습니다.",
                    "statusCode": HTTP_STATUS["BAD_REQUEST"],
                }),
                HTTP_STATUS["BAD_REQUEST"],
            )

        username = data.get("username")
        current_app.logger.info(
            f"[AUTHENTICATE_DEBUG] username 추출: '{username}' (타입: {type(username)})")

        if not username:
            current_app.logger.error(f"[AUTHENTICATE_DEBUG] username이 비어있습니다")
            return (
                jsonify({
                    "status": "failed",
                    "message": "username이 필요합니다.",
                    "statusCode": HTTP_STATUS["BAD_REQUEST"],
                }),
                HTTP_STATUS["BAD_REQUEST"],
            )

        current_app.logger.info(f"[AUTHENTICATE_DEBUG] authenticate_user_in_db 호출 시작")
        result = auth_service.authenticate_user_in_db(username)
        current_app.logger.info(
            f"[AUTHENTICATE_DEBUG] authenticate_user_in_db 완료: {result}")

        if result["success"]:
            response_data = {"user_id": result["user_id"]}
            current_app.logger.info(f"[AUTHENTICATE_DEBUG] 성공 응답: {response_data}")
            current_app.logger.info(f"[AUTHENTICATE_DEBUG] === /authenticate 성공 완료 ===")
            return jsonify(response_data)
        else:
            current_app.logger.warning(
                f"[AUTHENTICATE_DEBUG] 인증 실패: {result['message']}")
            status_code = (HTTP_STATUS["UNAUTHORIZED"] if "검증에 실패" in result["message"]
                           else HTTP_STATUS["INTERNAL_SERVER_ERROR"])

            error_response = {
                "status": "failed",
                "message": result["message"],
                "statusCode": status_code,
            }

            current_app.logger.warning(f"[AUTHENTICATE_DEBUG] 실패 응답: {error_response}")
            current_app.logger.info(f"[AUTHENTICATE_DEBUG] === /authenticate 실패 완료 ===")
            return jsonify(error_response), status_code

    except Exception as e:
        current_app.logger.error(f"[AUTHENTICATE_DEBUG] /authenticate 예외 발생: {str(e)}")
        import traceback

        current_app.logger.error(
            f"[AUTHENTICATE_DEBUG] 스택 트레이스: {traceback.format_exc()}")
        current_app.logger.error(f"[AUTHENTICATE_DEBUG] === /authenticate 예외 완료 ===")

        return (
            jsonify({
                "status": "failed",
                "message": f"서버 오류가 발생했습니다: {str(e)}",
                "statusCode": HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            }),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@auth_bp.route('/ip-info', methods=['GET'])
@handle_exceptions
def get_ip_info():
    """현재 클라이언트 IP 정보 조회 (디버깅/테스트용)"""
    client_ip = auth_service.get_client_ip(request)

    return jsonify({
        "client_ip": client_ip,
        "headers": {
            "X-Forwarded-For": request.headers.get('X-Forwarded-For'),
            "X-Real-IP": request.headers.get('X-Real-IP'),
            "Remote-Addr": request.remote_addr,
            "User-Agent": request.headers.get('User-Agent')
        },
        "message": "현재 클라이언트 IP 정보입니다."
    })


# 기존 LDAP 인증 엔드포인트는 호환성을 위해 잠시 유지 (향후 제거 예정)
@auth_bp.route('/check-credentials', methods=['POST'])
@handle_exceptions
def check_credentials_deprecated():
    """기존 LDAP 인증 (사용 중단 예정 - IP 인증으로 대체됨)"""
    current_app.logger.warning("Deprecated endpoint accessed: /check-credentials")

    return jsonify({
        "success": False,
        "message": "이 인증 방식은 더 이상 사용되지 않습니다. IP 기반 인증을 사용하세요.",
        "deprecated": True
    }), HTTP_STATUS['BAD_REQUEST']
