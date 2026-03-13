# app/controllers/admin_user_controller.py
"""
관리자 사용자 CRUD API 컨트롤러
- 사용자 생성, 조회, 수정, 삭제
- 사용자 계정 관리
- 사용자 권한 관리
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
from app.utils.decorators import token_required, handle_exceptions, admin_required
from app.utils.constants import HTTP_STATUS
from app.utils.database import execute_query, DatabaseManager
import logging
import re
import time

# 블루프린트 생성
admin_user_bp = Blueprint("admin_user", __name__, url_prefix="/api/admin")


@admin_user_bp.route("/users", methods=["POST"])
@token_required
@admin_required
@handle_exceptions
def create_user():
    """새 사용자 생성"""
    # JSON 요청 검증
    if not request.is_json:
        return (
            jsonify({
                "success": False,
                "message": "Content-Type은 application/json이어야 합니다.",
            }),
            HTTP_STATUS["BAD_REQUEST"],
        )

    data = request.json
    if not data:
        return (
            jsonify({
                "success": False,
                "message": "요청 본문이 필요합니다."
            }),
            HTTP_STATUS["BAD_REQUEST"],
        )

    try:
        logging.info(f"새 사용자 생성 요청: {data.get('name', 'Unknown')}")

        # 필수 필드 검증 (IP 주소 포함, 사번 제외)
        required_fields = ["name", "email", "ip", "department"]
        missing_fields = [
            field for field in required_fields if not data.get(field, "").strip()
        ]

        if missing_fields:
            return (
                jsonify({
                    "success": False,
                    "message": f"필수 필드가 누락되었습니다: {', '.join(missing_fields)}",
                }),
                HTTP_STATUS["BAD_REQUEST"],
            )

        # 데이터 검증
        validation_result = _validate_user_data(data)
        if not validation_result["valid"]:
            return (
                jsonify({
                    "success": False,
                    "message": validation_result["message"]
                }),
                HTTP_STATUS["BAD_REQUEST"],
            )

        # 중복 검사 (이메일만 검사, 사번은 자동 생성)
        duplicate_check = _check_duplicates(data["email"])
        if not duplicate_check["valid"]:
            return (
                jsonify({
                    "success": False,
                    "message": duplicate_check["message"]
                }),
                HTTP_STATUS["CONFLICT"],
            )

        # 사번 자동 생성
        generated_uid = _generate_user_id(data["name"], data["department"],
                                          data["email"])

        # 사용자 생성 (생성된 사번 포함)
        user_id = _create_user_record(data, generated_uid)

        # 생성된 사용자 정보 조회
        created_user = _get_user_by_id(user_id)

        logging.info(f"사용자 생성 완료: {data['name']} (ID: {user_id})")

        return (
            jsonify({
                "success": True,
                "message": f"사용자 '{data['name']}'가 성공적으로 생성되었습니다.",
                "user": created_user,
            }),
            HTTP_STATUS["CREATED"],
        )

    except Exception as e:
        logging.error(f"사용자 생성 실패: {str(e)}")
        return (
            jsonify({
                "success": False,
                "message": "사용자 생성 중 오류가 발생했습니다.",
                "details": str(e),
            }),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@admin_user_bp.route("/users/<int:user_id>", methods=["GET"])
@token_required
@admin_required
@handle_exceptions
def get_user(user_id):
    """특정 사용자 정보 조회"""
    try:
        user = _get_user_by_id(user_id)

        if not user:
            return (
                jsonify({
                    "success": False,
                    "message": "사용자를 찾을 수 없습니다."
                }),
                HTTP_STATUS["NOT_FOUND"],
            )

        return jsonify({"success": True, "user": user})

    except Exception as e:
        logging.error(f"사용자 조회 실패: {str(e)}")
        return (
            jsonify({
                "success": False,
                "message": "사용자 조회 중 오류가 발생했습니다.",
                "details": str(e),
            }),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@admin_user_bp.route("/users/<int:user_id>", methods=["PUT"])
@token_required
@admin_required
@handle_exceptions
def update_user(user_id):
    """사용자 정보 수정"""
    # JSON 요청 검증
    if not request.is_json:
        return (
            jsonify({
                "success": False,
                "message": "Content-Type은 application/json이어야 합니다.",
            }),
            HTTP_STATUS["BAD_REQUEST"],
        )

    data = request.json
    if not data:
        return (
            jsonify({
                "success": False,
                "message": "요청 본문이 필요합니다."
            }),
            HTTP_STATUS["BAD_REQUEST"],
        )

    try:
        # 사용자 존재 확인
        existing_user = _get_user_by_id(user_id)
        if not existing_user:
            return (
                jsonify({
                    "success": False,
                    "message": "사용자를 찾을 수 없습니다."
                }),
                HTTP_STATUS["NOT_FOUND"],
            )

        # 데이터 검증 (수정 시에는 선택적 검증)
        if any(field in data for field in ["email", "ip"]):
            validation_result = _validate_user_data(data, is_update=True)
            if not validation_result["valid"]:
                return (
                    jsonify({
                        "success": False,
                        "message": validation_result["message"]
                    }),
                    HTTP_STATUS["BAD_REQUEST"],
                )

        # 중복 검사 (수정하려는 필드가 있을 경우)
        if "email" in data:
            duplicate_check = _check_duplicates(
                data.get("email", existing_user["email"]), exclude_user_id=user_id)
            if not duplicate_check["valid"]:
                return (
                    jsonify({
                        "success": False,
                        "message": duplicate_check["message"]
                    }),
                    HTTP_STATUS["CONFLICT"],
                )

        # 사용자 정보 업데이트
        _update_user_record(user_id, data)

        # 업데이트된 사용자 정보 조회
        updated_user = _get_user_by_id(user_id)

        logging.info(f"사용자 수정 완료: {updated_user['name']} (ID: {user_id})")

        return jsonify({
            "success": True,
            "message": f"사용자 '{updated_user['name']}'의 정보가 성공적으로 수정되었습니다.",
            "user": updated_user,
        })

    except Exception as e:
        logging.error(f"사용자 수정 실패: {str(e)}")
        return (
            jsonify({
                "success": False,
                "message": "사용자 수정 중 오류가 발생했습니다.",
                "details": str(e),
            }),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


@admin_user_bp.route("/users/<int:user_id>", methods=["DELETE"])
@token_required
@admin_required
@handle_exceptions
def delete_user(user_id):
    """사용자 삭제 (실제 삭제)"""
    try:
        # 사용자 존재 확인
        existing_user = _get_user_by_id(user_id)
        if not existing_user:
            return (
                jsonify({
                    "success": False,
                    "message": "사용자를 찾을 수 없습니다."
                }),
                HTTP_STATUS["NOT_FOUND"],
            )

        # 자기 자신 삭제 방지
        current_user = request.current_user
        if existing_user["user_id"] == current_user["username"]:
            return (
                jsonify({
                    "success": False,
                    "message": "자기 자신의 계정은 삭제할 수 없습니다.",
                }),
                HTTP_STATUS["FORBIDDEN"],
            )

        # 사용자 삭제 (실제 삭제)
        _delete_user(user_id)

        logging.info(f"사용자 삭제 완료: {existing_user['name']} (ID: {user_id})")

        return jsonify({
            "success": True,
            "message": f"사용자 '{existing_user['name']}'가 성공적으로 삭제되었습니다.",
        })

    except Exception as e:
        logging.error(f"사용자 삭제 실패: {str(e)}")
        return (
            jsonify({
                "success": False,
                "message": "사용자 삭제 중 오류가 발생했습니다.",
                "details": str(e),
            }),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )


# === 헬퍼 함수들 ===


def _validate_user_data(data, is_update=False):
    """사용자 데이터 유효성 검증 (IP 주소 포함, 사번 제외)"""
    try:
        # 이름 검증
        if "name" in data and not data["name"].strip():
            return {"valid": False, "message": "이름은 필수입니다."}

        # IP 주소 검증
        if "ip" in data:
            ip_input = data["ip"].strip()
            if not ip_input:
                return {"valid": False, "message": "IP 주소는 필수입니다."}

            # 여러 IP 주소 처리 (쉼표로 구분)
            ip_addresses = [ip.strip() for ip in ip_input.split(",")]
            ip_pattern = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"

            for ip in ip_addresses:
                if not re.match(ip_pattern, ip):
                    return {
                        "valid": False,
                        "message": f"올바르지 않은 IP 주소 형식입니다: {ip}",
                    }

        # 이메일 검증
        if "email" in data:
            email = data["email"].strip()
            if not email:
                return {"valid": False, "message": "이메일은 필수입니다."}
            email_pattern = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
            if not re.match(email_pattern, email):
                return {"valid": False, "message": "올바른 이메일 형식을 입력해주세요."}

        # 부서 검증
        if "department" in data and not data["department"].strip():
            return {"valid": False, "message": "부서는 필수입니다."}

        # 역할 검증
        if "role" in data and data["role"] not in ["user", "admin"]:
            return {
                "valid": False,
                "message": "역할은 'user' 또는 'admin'이어야 합니다.",
            }

        return {"valid": True}

    except Exception as e:
        logging.error(f"데이터 검증 오류: {str(e)}")
        return {"valid": False, "message": "데이터 검증 중 오류가 발생했습니다."}


def _check_duplicates(email, exclude_user_id=None):
    """중복 검사 (이메일만 검사, 사번은 자동 생성이므로 제외)"""
    try:
        # 이메일 중복 검사
        email_query = "SELECT uid FROM users WHERE mail = %s"
        email_params = [email]

        if exclude_user_id:
            email_query += " AND uid != %s"
            email_params.append(exclude_user_id)

        existing_email = execute_query(email_query, email_params, fetch_one=True)
        if existing_email:
            return {
                "valid": False,
                "message": f"이메일 '{email}'는 이미 사용 중입니다.",
            }

        return {"valid": True}

    except Exception as e:
        logging.error(f"중복 검사 오류: {str(e)}")
        return {"valid": False, "message": "중복 검사 중 오류가 발생했습니다."}


def _generate_user_id(name, department, email):
    """사번 자동 생성 함수 - 이메일 기반으로 변경"""
    try:
        # 이메일 @ 앞 부분을 기본 user_id로 사용
        if email and '@' in email:
            base_user_id = email.split('@')[0]

            # 특수문자 제거 및 소문자 변환 (선택사항)
            base_user_id = base_user_id.lower().replace('.', '_')

            # 중복 검사
            existing_user = execute_query(
                "SELECT user_id FROM users WHERE user_id = %s",
                (base_user_id, ),
                fetch_one=True,
            )

            if not existing_user:
                # 중복이 없으면 그대로 사용
                generated_uid = base_user_id
            else:
                # 중복이 있으면 숫자를 붙여서 유니크하게 만들기
                counter = 1
                while True:
                    test_uid = f"{base_user_id}_{counter}"
                    existing = execute_query(
                        "SELECT user_id FROM users WHERE user_id = %s",
                        (test_uid, ),
                        fetch_one=True,
                    )
                    if not existing:
                        generated_uid = test_uid
                        break
                    counter += 1
        else:
            # 이메일이 없는 경우 기존 방식 사용 (폴백)
            dept_prefix = (department[:2] if len(department) >= 2 else department.ljust(
                2, "0"))
            name_prefix = name[:2] if len(name) >= 2 else name.ljust(2, "0")

            pattern = f"{dept_prefix}{name_prefix}%"
            existing_count = execute_query(
                "SELECT COUNT(*) as count FROM users WHERE user_id LIKE %s",
                (pattern, ),
                fetch_one=True,
            )

            next_number = (existing_count["count"] if existing_count else 0) + 1
            generated_uid = f"{dept_prefix}{name_prefix}{next_number:03d}"

        logging.info(f"사번 자동 생성: {generated_uid} (이메일: {email})")
        return generated_uid

    except Exception as e:
        logging.error(f"사번 생성 오류: {str(e)}")
        # 오류 시 타임스탬프 기반 사번 생성
        fallback_uid = f"USER{int(time.time() * 1000) % 100000:05d}"
        logging.info(f"대체 사번 생성: {fallback_uid}")
        return fallback_uid


def _create_user_record(data, generated_uid):
    """사용자 레코드 생성 (IP 주소 포함, 자동 생성된 사번 사용)"""
    try:
        insert_query = """
            INSERT INTO users (
                user_id, username, mail, department, role, ip,
                created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s
            )
        """

        current_time = datetime.now()

        params = (
            generated_uid,  # user_id (자동 생성된 사번)
            data["name"].strip(),  # username (실명)
            data["email"].strip(),  # mail (이메일)
            data["department"].strip(),  # department (부서)
            data.get("role", "user"),  # role (역할)
            data["ip"].strip(),  # ip (IP 주소)
            current_time,  # created_at
            current_time,  # updated_at
        )

        # DatabaseManager를 사용하여 직접 커서 접근
        with DatabaseManager.get_db_cursor() as cursor:
            cursor.execute(insert_query, params)
            user_id = cursor.lastrowid  # 새로 생성된 ID 가져오기
            return user_id

    except Exception as e:
        logging.error(f"사용자 레코드 생성 오류: {str(e)}")
        raise


def _get_user_by_id(user_id, include_inactive=False):
    """ID로 사용자 정보 조회 (is_active 포함)"""
    try:
        query = """
            SELECT 
                uid,
                user_id,
                username as name,
                mail as email,
                ip,
                department,
                role,
                is_active,
                created_at,
                updated_at
            FROM users 
            WHERE uid = %s
        """
        
        # 비활성 사용자 제외 옵션
        if not include_inactive:
            query += " AND is_active = 1"

        user = execute_query(query, (user_id,), fetch_one=True)

        if user:
            # datetime 객체를 문자열로 변환
            if user.get("created_at"):
                user["created_at"] = user["created_at"].isoformat()
            if user.get("updated_at"):
                user["updated_at"] = user["updated_at"].isoformat()

        return user

    except Exception as e:
        logging.error(f"사용자 조회 오류: {str(e)}")
        return None


def _update_user_record(user_id, data):
    """사용자 레코드 업데이트 (IP 주소 포함)"""
    try:
        # 업데이트할 필드와 값 준비
        update_fields = []
        params = []

        field_mapping = {
            "name": "username",  # 실명
            "email": "mail",  # 이메일
            "ip": "ip",  # IP 주소
            "department": "department",
            "role": "role",
        }

        for field, db_field in field_mapping.items():
            if field in data:
                value = data[field]
                if field in ["name", "email", "ip", "department"]:
                    value = value.strip() if value else None

                update_fields.append(f"{db_field} = %s")
                params.append(value)

        if not update_fields:
            return

        # updated_at 필드 추가
        update_fields.append("updated_at = %s")
        params.append(datetime.now())

        # user_id 파라미터 추가
        params.append(user_id)

        update_query = f"""
            UPDATE users 
            SET {', '.join(update_fields)}
            WHERE uid = %s
        """

        execute_query(update_query, params)

    except Exception as e:
        logging.error(f"사용자 업데이트 오류: {str(e)}")
        raise


def _delete_user(user_id):
    """사용자 실제 삭제 (현재 DB에는 is_active 필드가 없으므로)"""
    try:
        delete_query = """
            DELETE FROM users 
            WHERE uid = %s
        """

        execute_query(delete_query, (user_id, ))

    except Exception as e:
        logging.error(f"사용자 삭제 오류: {str(e)}")
        raise


# ============================================
# 사용자 활성화/비활성화 토글 API
# ============================================

@admin_user_bp.route("/users/<int:user_id>/toggle-active", methods=["PATCH"])
@token_required
@admin_required
@handle_exceptions
def toggle_user_active(user_id):
    """사용자 활성화/비활성화 토글"""
    try:
        # 사용자 존재 확인 (비활성 사용자 포함)
        user = _get_user_by_id(user_id, include_inactive=True)
        if not user:
            return (
                jsonify({
                    "success": False,
                    "message": "사용자를 찾을 수 없습니다."
                }),
                HTTP_STATUS["NOT_FOUND"],
            )

        # 현재 상태 확인
        current_status = user.get("is_active", 1)
        new_status = 0 if current_status == 1 else 1

        # 자기 자신을 비활성화하려는 경우 방지
        current_user = request.current_user
        if current_user["username"] == user.get("name"):
            return (
                jsonify({
                    "success": False,
                    "message": "자기 자신을 비활성화할 수 없습니다."
                }),
                HTTP_STATUS["BAD_REQUEST"],
            )

        # 상태 업데이트
        update_query = """
            UPDATE users 
            SET is_active = %s, updated_at = %s
            WHERE uid = %s
        """
        execute_query(update_query, (new_status, datetime.now(), user_id))

        status_text = "활성화" if new_status == 1 else "비활성화"
        logging.info(f"사용자 {status_text}: uid={user_id}, name={user.get('name')}, new_is_active={new_status}")

        # ✅ 응답에 명확히 is_active 값 포함
        return jsonify({
            "success": True,
            "message": f"사용자가 {status_text}되었습니다.",
            "is_active": new_status  # 0 또는 1
        })

    except Exception as e:
        logging.error(f"사용자 상태 변경 실패: {str(e)}")
        return (
            jsonify({
                "success": False,
                "message": "사용자 상태 변경 중 오류가 발생했습니다.",
                "details": str(e),
            }),
            HTTP_STATUS["INTERNAL_SERVER_ERROR"],
        )