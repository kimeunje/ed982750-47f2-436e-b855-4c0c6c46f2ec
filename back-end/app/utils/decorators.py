# app/utils/decorators.py - 완전 수정된 버전
from functools import wraps
from flask import request, jsonify, current_app
import jwt
from app.utils.constants import HTTP_STATUS, MESSAGES


def token_required(f):
    """JWT 토큰 인증 데코레이터 - role 정보 포함"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get("auth_token")

        if not token:
            return jsonify({"message": MESSAGES['UNAUTHORIZED']
                            }), HTTP_STATUS['UNAUTHORIZED']

        try:
            payload = jwt.decode(token, current_app.config['JWT_SECRET'],
                                 algorithms=["HS256"])

            # current_user에 role 정보도 포함
            request.current_user = {
                'username': payload.get('username'),
                'name': payload.get('name'),
                'dept': payload.get('dept'),
                'role': payload.get('role', 'user'),  # role 정보 추가
                'client_ip': payload.get('client_ip')  # IP 정보도 추가
            }

        except jwt.ExpiredSignatureError:
            return jsonify({"message": MESSAGES['EXPIRED_TOKEN']
                            }), HTTP_STATUS['UNAUTHORIZED']
        except jwt.InvalidTokenError:
            return jsonify({"message": MESSAGES['INVALID_TOKEN']
                            }), HTTP_STATUS['UNAUTHORIZED']

        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """관리자 권한 확인 데코레이터 - role 기반으로 수정"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get("auth_token")

        if not token:
            return jsonify({"message": MESSAGES['UNAUTHORIZED']
                            }), HTTP_STATUS['UNAUTHORIZED']

        try:
            payload = jwt.decode(token, current_app.config['JWT_SECRET'],
                                 algorithms=["HS256"])
            user_name = payload.get("username")
            user_role = payload.get("role", "user")  # 토큰에서 role 정보 가져오기

            # 관리자 권한 확인 (role이 admin인 경우 허용)
            if user_role != 'admin':
                current_app.logger.warning(
                    f"비관리자 접근 시도: {user_name} (role: {user_role})")
                return jsonify({"message": MESSAGES['ADMIN_REQUIRED']
                                }), HTTP_STATUS['FORBIDDEN']

            # 현재 사용자 정보 설정
            request.current_user = {
                'username': payload.get('username'),
                'name': payload.get('name'),
                'dept': payload.get('dept'),
                'role': user_role,
                'client_ip': payload.get('client_ip')
            }

            current_app.logger.info(f"관리자 접근 허용: {user_name} (role: {user_role})")

        except jwt.ExpiredSignatureError:
            return jsonify({"message": MESSAGES['EXPIRED_TOKEN']
                            }), HTTP_STATUS['UNAUTHORIZED']
        except jwt.InvalidTokenError:
            return jsonify({"message": MESSAGES['INVALID_TOKEN']
                            }), HTTP_STATUS['UNAUTHORIZED']

        return f(*args, **kwargs)

    return decorated_function


def validate_json(required_fields):
    """JSON 요청 검증 데코레이터"""

    def decorator(f):

        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({"error": "Content-Type must be application/json"
                                }), HTTP_STATUS['BAD_REQUEST']

            data = request.json
            if not data:
                return jsonify({"error": "Request body is required"
                                }), HTTP_STATUS['BAD_REQUEST']

            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return jsonify({
                    "error": f"Missing required fields: {', '.join(missing_fields)}"
                }), HTTP_STATUS['BAD_REQUEST']

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def handle_exceptions(f):
    """예외 처리 데코레이터"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            current_app.logger.error(f"Error in {f.__name__}: {str(e)}")
            return jsonify({
                "error": MESSAGES['SERVER_ERROR'],
                "details": str(e) if current_app.debug else None
            }), HTTP_STATUS['INTERNAL_SERVER_ERROR']

    return decorated_function