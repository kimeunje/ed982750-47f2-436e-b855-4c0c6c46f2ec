# back-end/app/services/auth_service.py - IP 인증으로 수정

import jwt
import ipaddress
from datetime import datetime, timedelta
from flask import current_app
from app.utils.constants import (
    TEST_USERS,
    ALLOWED_IP_RANGES,
    IP_AUTH_CONFIG,
    DEFAULT_VERIFICATION_CODE,
)
from app.utils.database import execute_query


class AuthService:
    """인증 관련 서비스 - IP 기반 인증"""

    def __init__(self):
        self.verification_codes = {}  # 실제 환경에서는 Redis 등 사용 권장


    def authenticate_by_ip(self, client_ip):
        """IP 기반 사용자 인증 (비활성 사용자 체크 추가)"""
        try:
            # 로그 시작
            current_app.logger.info(f"IP 기반 인증 시작: IP={client_ip}")

            if not client_ip:
                return {
                    "success": False,
                    "message": "클라이언트 IP를 확인할 수 없습니다.",
                }

            # IP 주소로 사용자 조회 (✅ is_active 필드 추가)
            user_query = """
                SELECT uid, user_id, username, mail, department, role, is_active
                FROM users 
                WHERE FIND_IN_SET(%s, REPLACE(ip, ' ', '')) > 0
            """

            user = execute_query(user_query, (client_ip,), fetch_one=True)

            if not user:
                current_app.logger.warning(f"등록되지 않은 IP: {client_ip}")
                return {
                    "success": False,
                    "message": f"등록되지 않은 IP 주소입니다: {client_ip}",
                }

            # ✅ 비활성 사용자 체크 추가
            if user.get("is_active") == 0:
                current_app.logger.warning(
                    f"비활성화된 사용자 로그인 시도: {user['username']} ({client_ip})"
                )
                return {
                    "success": False,
                    "message": "비활성화된 계정입니다. 관리자에게 문의하세요.",
                }

            current_app.logger.info(f"IP 인증 성공: {user['username']} from {client_ip}")

            return {
                "success": True,
                "username": user["user_id"],
                "name": user["username"],
                "email": user["mail"],
                "dept": user["department"],
                "role": user.get("role", "user"),
            }

        except Exception as e:
            current_app.logger.error(f"IP 인증 오류: {str(e)}")
            return {
                "success": False,
                "message": f"인증 처리 중 오류가 발생했습니다: {str(e)}",
            }


    def _find_user_by_ip_from_db(self, client_ip: str) -> dict:
        """users 테이블에서 IP로 사용자 찾기 (상세 디버깅 추가)"""
        try:
            current_app.logger.info(f"[USER_LOOKUP_DETAIL] === 사용자 조회 시작 ===")
            current_app.logger.info(f"[USER_LOOKUP_DETAIL] 조회 대상 IP: {client_ip}")

            # SQL 쿼리 실행
            current_app.logger.info(f"[USER_LOOKUP_DETAIL] SQL 쿼리 실행")
            users = execute_query(
                """
                SELECT uid, user_id, username, mail, department, ip, role
                FROM users 
                WHERE ip IS NOT NULL 
                AND ip != ''
                AND (
                    FIND_IN_SET(%s, REPLACE(ip, ' ', '')) > 0
                    OR ip = %s
                )
                """,
                (client_ip, client_ip),
                fetch_all=True,
            )

            current_app.logger.info(
                f"[USER_LOOKUP_DETAIL] 조회된 사용자 수: {len(users) if users else 0}")

            if users:
                for i, user in enumerate(users):
                    current_app.logger.info(
                        f"[USER_LOOKUP_DETAIL] 사용자 {i+1}: uid={user['uid']}, user_id={user['user_id']}, username={user['username']}, ip={user['ip']}"
                    )

            if not users:
                current_app.logger.warning(
                    f"[USER_LOOKUP_DETAIL] IP {client_ip}에 매칭되는 사용자가 없습니다.")
                return None

            # 정확한 IP 매칭 검증
            current_app.logger.info(f"[USER_LOOKUP_DETAIL] IP 매칭 검증 시작")
            for user in users:
                current_app.logger.info(
                    f"[USER_LOOKUP_DETAIL] 검증 대상: {user['user_id']} (저장된 IP: {user['ip']})"
                )

                if self._verify_ip_match(client_ip, user["ip"]):
                    current_app.logger.info(
                        f"[USER_LOOKUP_DETAIL] IP 매칭 성공: {user['user_id']} <- {client_ip}"
                    )

                    # DB의 role 컬럼 사용 (기본값: 'user')
                    role = user.get("role", "user") or "user"

                    result = {
                        "uid": user["uid"],
                        "user_id": user["user_id"],
                        "username": user["username"],
                        "mail": user["mail"],
                        "department": user["department"],
                        "role": role,
                    }

                    current_app.logger.info(
                        f"[USER_LOOKUP_DETAIL] 반환할 사용자 정보: {result}")
                    current_app.logger.info(f"[USER_LOOKUP_DETAIL] === 사용자 조회 성공 ===")
                    return result
                else:
                    current_app.logger.warning(
                        f"[USER_LOOKUP_DETAIL] IP 매칭 실패: {user['user_id']} (저장된 IP: {user['ip']})"
                    )

            current_app.logger.warning(f"[USER_LOOKUP_DETAIL] 모든 사용자에 대해 IP 매칭 실패")
            current_app.logger.warning(f"[USER_LOOKUP_DETAIL] === 사용자 조회 실패 ===")
            return None

        except Exception as e:
            current_app.logger.error(f"[USER_LOOKUP_DETAIL] 사용자 조회 중 예외: {str(e)}")
            import traceback
            current_app.logger.error(
                f"[USER_LOOKUP_DETAIL] 스택 트레이스: {traceback.format_exc()}")
            current_app.logger.error(f"[USER_LOOKUP_DETAIL] === 사용자 조회 예외 ===")
            return None

    def _verify_ip_match(self, client_ip: str, stored_ips: str) -> bool:
        """저장된 IP 목록과 클라이언트 IP 정확히 매칭 확인 - 강화된 버전"""
        if not stored_ips:
            return False

        # 쉼표와 공백으로 분리하여 정확한 IP 목록 생성
        ip_list = []
        for ip in stored_ips.replace(" ", "").split(","):
            ip = ip.strip()
            if ip:  # 빈 문자열 제외
                ip_list.append(ip)

        # 정확한 매칭만 허용
        match_found = client_ip in ip_list

        current_app.logger.info(f"IP 매칭 검증: {client_ip} in {ip_list} = {match_found}")

        return match_found

    def _check_business_hours(self) -> bool:
        """업무시간 체크"""
        if not IP_AUTH_CONFIG.get("enable_time_restriction", False):
            return True

        now = datetime.now()
        business_hours = IP_AUTH_CONFIG["business_hours"]

        # 주말 체크
        if business_hours.get("weekdays_only", False) and now.weekday() >= 5:
            current_app.logger.info("주말 접근 시도")
            return False

        # 시간 체크
        current_hour = now.hour
        if (current_hour < business_hours["start"]
                or current_hour >= business_hours["end"]):
            current_app.logger.info(f"업무시간 외 접근 시도: {current_hour}시")
            return False

        return True

    def _is_ip_in_allowed_ranges(self, client_ip: str) -> bool:
        """허용된 IP 대역 체크"""
        if not IP_AUTH_CONFIG.get("enable_range_check", False):
            return True

        try:
            client_ip_obj = ipaddress.IPv4Address(client_ip)

            for ip_range in ALLOWED_IP_RANGES:
                network = ipaddress.IPv4Network(ip_range, strict=False)
                if client_ip_obj in network:
                    current_app.logger.info(f"IP 대역 매칭: {client_ip} in {ip_range}")
                    return True

            current_app.logger.warning(f"허용되지 않은 IP 대역: {client_ip}")
            return False

        except ipaddress.AddressValueError:
            current_app.logger.warning(f"잘못된 IP 주소 형식: {client_ip}")
            return False

    def _find_user_by_ip(self, client_ip: str) -> dict:
        """IP로 사용자 찾기"""
        for username, user_data in TEST_USERS.items():
            allowed_ips = user_data.get("allowed_ips", [])

            if client_ip in allowed_ips:
                current_app.logger.info(f"사용자 매칭: {username} <- {client_ip}")
                return {
                    "username": username,
                    "email": user_data["email"],
                    "name": user_data["name"],
                    "dept": user_data["dept"],
                    "role": user_data.get("role", "user"),
                }

        current_app.logger.warning(f"매칭되지 않은 IP: {client_ip}")
        return None

    # 기존 이메일 인증 관련 메서드들은 그대로 유지
    def send_verification_code(self, email: str) -> dict:
        """이메일 인증 코드 발송 (기존 유지)"""
        if not email:
            return {"success": False, "message": "이메일 주소가 필요합니다."}

        verification_code = DEFAULT_VERIFICATION_CODE
        expiry = datetime.now() + timedelta(minutes=15)
        self.verification_codes[email] = {"code": verification_code, "expiry": expiry}

        print(f"[이메일 인증] 인증 코드: {verification_code} (수신자: {email})")
        return {"success": True, "message": "인증 코드가 발송되었습니다."}

    def verify_code(self, email: str, code: str) -> bool:
        """인증 코드 확인 (기존 유지)"""
        is_valid_code = code == DEFAULT_VERIFICATION_CODE

        if email in self.verification_codes:
            verification_info = self.verification_codes[email]
            is_valid_code = is_valid_code or (verification_info["code"] == code
                                              and datetime.now()
                                              <= verification_info["expiry"])

        return is_valid_code

    def generate_token(self, username: str, user_info: dict, client_ip: str) -> str:
        """JWT 토큰 생성 (IP 정보 포함)"""
        token_payload = {
            "username": username,
            "name": user_info.get("name"),
            "dept": user_info.get("dept"),
            "role": user_info.get("role", "user"),
            "client_ip": client_ip,  # IP 정보 추가
            "exp": datetime.now() +
            timedelta(seconds=current_app.config["TOKEN_EXPIRATION"]),
        }

        return jwt.encode(token_payload, current_app.config["JWT_SECRET"],
                          algorithm="HS256")

    def verify_token(self, token: str, client_ip: str = None) -> dict:
        """JWT 토큰 검증 (IP 검증 포함)"""
        try:
            payload = jwt.decode(token, current_app.config["JWT_SECRET"],
                                 algorithms=["HS256"])

            # IP 검증 (옵션 - 경고만 기록)
            if client_ip and payload.get("client_ip"):
                if payload["client_ip"] != client_ip:
                    current_app.logger.warning(
                        f"토큰 IP 불일치: 토큰={payload['client_ip']}, 현재={client_ip}")
                    # DHCP 환경을 고려해 경고만 기록하고 통과

            return {"valid": True, "payload": payload}

        except jwt.ExpiredSignatureError:
            return {"valid": False, "error": "토큰이 만료되었습니다."}
        except jwt.InvalidTokenError:
            return {"valid": False, "error": "유효하지 않은 토큰입니다."}

    def clear_verification_code(self, email: str):
        """인증 코드 삭제 (기존 유지)"""
        if email in self.verification_codes:
            del self.verification_codes[email]

    def get_client_ip(self, request) -> str:
        """클라이언트 실제 IP 추출 (프록시/로드밸런서 고려) - 강화된 디버깅"""
        current_app.logger.info(f"[IP_EXTRACT_DEBUG] === IP 추출 시작 ===")

        # 우선순위에 따른 IP 추출
        ip_sources = [
            ("X-Forwarded-For", request.headers.get("X-Forwarded-For")),
            ("X-Real-IP", request.headers.get("X-Real-IP")),
            ("X-Client-IP", request.headers.get("X-Client-IP")),
            ("CF-Connecting-IP", request.headers.get("CF-Connecting-IP")),  # Cloudflare
            ("Remote-Addr", request.remote_addr),
        ]

        current_app.logger.info(f"[IP_EXTRACT_DEBUG] 모든 IP 소스:")
        for source_name, source_value in ip_sources:
            current_app.logger.info(
                f"[IP_EXTRACT_DEBUG]   {source_name}: {source_value}")

        # X-Forwarded-For 우선 처리 (쉼표로 구분된 첫 번째 IP)
        x_forwarded_for = request.headers.get("X-Forwarded-For")
        if x_forwarded_for:
            # 첫 번째 IP가 실제 클라이언트 IP
            client_ip = x_forwarded_for.split(",")[0].strip()
            current_app.logger.info(
                f"[IP_EXTRACT_DEBUG] X-Forwarded-For에서 추출: {client_ip}")
            current_app.logger.info(f"[IP_EXTRACT_DEBUG] === IP 추출 완료 ===")
            return client_ip

        # X-Real-IP 확인
        x_real_ip = request.headers.get("X-Real-IP")
        if x_real_ip:
            current_app.logger.info(f"[IP_EXTRACT_DEBUG] X-Real-IP에서 추출: {x_real_ip}")
            current_app.logger.info(f"[IP_EXTRACT_DEBUG] === IP 추출 완료 ===")
            return x_real_ip

        # 기타 헤더들 확인
        for header_name in ["X-Client-IP", "CF-Connecting-IP"]:
            header_value = request.headers.get(header_name)
            if header_value:
                current_app.logger.info(
                    f"[IP_EXTRACT_DEBUG] {header_name}에서 추출: {header_value}")
                current_app.logger.info(f"[IP_EXTRACT_DEBUG] === IP 추출 완료 ===")
                return header_value

        # 최종적으로 remote_addr 사용
        final_ip = request.remote_addr
        current_app.logger.info(f"[IP_EXTRACT_DEBUG] Remote-Addr 사용: {final_ip}")
        current_app.logger.info(f"[IP_EXTRACT_DEBUG] === IP 추출 완료 ===")
        return final_ip


    def authenticate_user_in_db(self, username):
        """사용자명으로 DB 인증 (비활성 사용자 체크 추가)"""
        try:
            current_app.logger.info(f"[USER_AUTH_DETAIL] === 사용자 인증 시작: '{username}' ===")

            if not username:
                return {
                    "success": False,
                    "message": "사용자명이 필요합니다.",
                }

            # user_id 컬럼으로 조회 (✅ is_active 필드 추가)
            current_app.logger.info(f"[USER_AUTH_DETAIL] 1단계: user_id로 사용자 조회")
            user = execute_query(
                "SELECT uid, user_id, username, is_active FROM users WHERE user_id = %s",
                (username,), 
                fetch_one=True
            )
            current_app.logger.info(f"[USER_AUTH_DETAIL] 사용자 조회 결과: {user}")

            if not user:
                current_app.logger.warning(
                    f"[USER_AUTH_DETAIL] user_id로 사용자를 찾을 수 없음: '{username}'"
                )
                return {
                    "success": False,
                    "message": f"사용자 '{username}'을(를) 찾을 수 없습니다. 운영실에 문의해주세요.",
                }

            # ✅ 비활성 사용자 체크 추가
            if user.get("is_active") == 0:
                current_app.logger.warning(
                    f"[USER_AUTH_DETAIL] 비활성화된 사용자 로그인 시도: {user['username']}"
                )
                return {
                    "success": False,
                    "message": "비활성화된 계정입니다. 관리자에게 문의하세요.",
                }

            user_id = user["uid"]
            login_id = user["user_id"]
            real_name = user["username"]

            current_app.logger.info(
                f"[USER_AUTH_DETAIL] 사용자 정보: uid={user_id}, user_id={login_id}, username={real_name}"
            )

            # 기존 감사 로그 확인
            current_app.logger.info(f"[USER_AUTH_DETAIL] 2단계: 기존 감사 로그 확인")
            existing_logs = execute_query(
                """
                SELECT COUNT(*) as log_count
                FROM audit_log
                WHERE user_id = %s AND DATE(checked_at) = DATE(NOW())
                """,
                (user_id,),
                fetch_one=True,
            )["log_count"]

            current_app.logger.info(f"[USER_AUTH_DETAIL] 기존 감사 로그 개수: {existing_logs}")

            if existing_logs == 0:
                current_app.logger.info(f"[USER_AUTH_DETAIL] 3단계: 감사 로그 생성 시작")

                try:
                    self._create_initial_audit_logs(user_id)
                    current_app.logger.info(
                        f"[USER_AUTH_DETAIL] 감사 로그 생성 성공: uid={user_id}"
                    )
                except Exception as log_error:
                    current_app.logger.error(
                        f"[USER_AUTH_DETAIL] 감사 로그 생성 실패: {str(log_error)}"
                    )
                    import traceback
                    current_app.logger.error(
                        f"[USER_AUTH_DETAIL] 로그 생성 스택 트레이스: {traceback.format_exc()}"
                    )
                    return {
                        "success": False,
                        "message": f"감사 로그 생성에 실패했습니다: {str(log_error)}",
                    }
            else:
                current_app.logger.info(f"[USER_AUTH_DETAIL] 기존 감사 로그 존재, 생성 건너뜀")

            result = {"success": True, "user_id": user_id}
            current_app.logger.info(f"[USER_AUTH_DETAIL] 최종 결과: {result}")
            current_app.logger.info(f"[USER_AUTH_DETAIL] === 사용자 인증 성공 ===")

            return result

        except Exception as e:
            current_app.logger.error(f"[USER_AUTH_DETAIL] 사용자 인증 중 예외: {str(e)}")
            import traceback
            current_app.logger.error(
                f"[USER_AUTH_DETAIL] 스택 트레이스: {traceback.format_exc()}"
            )
            return {
                "success": False,
                "message": f"인증 처리 중 오류가 발생했습니다: {str(e)}",
            }


    def _create_initial_audit_logs(self, user_id: int):
        """초기 감사 로그 생성 (디버깅 강화)"""
        try:
            current_app.logger.info(
                f"[AUDIT_DEBUG] _create_initial_audit_logs 시작: user_id={user_id}")

            # 체크리스트 항목 조회
            checklist_items = execute_query(
                """
                SELECT item_id, item_name, category, description
                FROM checklist_items
                WHERE check_type = 'daily'
                ORDER BY item_id
                """,
                fetch_all=True,
            )

            current_app.logger.info(
                f"[AUDIT_DEBUG] 체크리스트 항목 개수: {len(checklist_items) if checklist_items else 0}"
            )

            if not checklist_items:
                raise Exception("체크리스트 항목을 찾을 수 없습니다.")

            import json
            default_actual_value = json.dumps(
                {
                    "status": "pending",
                    "message": "검사 대기 중"
                }, ensure_ascii=False)

            # 각 항목별로 감사 로그 생성
            created_count = 0
            for item in checklist_items:
                try:
                    current_app.logger.debug(
                        f"[AUDIT_DEBUG] 감사 로그 생성: item_id={item['item_id']}, item_name={item['item_name']}"
                    )

                    execute_query(
                        """
                        INSERT INTO audit_log (user_id, item_id, actual_value, passed, notes, checked_at)
                        VALUES (%s, %s, %s, 1, 'pending 상태 자동 통과 처리', NOW())
                        """,
                        (user_id, item["item_id"], default_actual_value),
                    )
                    created_count += 1

                except Exception as item_error:
                    current_app.logger.error(
                        f"[AUDIT_DEBUG] 개별 감사 로그 생성 실패: item_id={item['item_id']}, error={str(item_error)}"
                    )
                    continue

            current_app.logger.info(
                f"[AUDIT_DEBUG] 감사 로그 생성 완료: user_id={user_id}, 생성된 개수={created_count}/{len(checklist_items)}"
            )

            if created_count == 0:
                raise Exception("감사 로그가 하나도 생성되지 않았습니다.")

        except Exception as e:
            current_app.logger.error(
                f"[AUDIT_DEBUG] _create_initial_audit_logs 실패: user_id={user_id}, error={str(e)}"
            )
            import traceback
            current_app.logger.error(f"[AUDIT_DEBUG] 스택 트레이스: {traceback.format_exc()}")
            raise
