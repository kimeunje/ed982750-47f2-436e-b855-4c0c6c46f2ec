# app.py - 메인 진입점
import os
from app import create_app
from app.utils.constants import TEST_USERS

# 환경 설정
config_name = os.environ.get('FLASK_ENV', 'development')

# Flask 앱 생성
app = create_app(config_name)

if __name__ == "__main__":
    print("============================================================")
    print("   구조화된 Flask 서버가 시작되었습니다!")
    print("============================================================")
    print("테스트 계정 정보:")
    for username, info in TEST_USERS.items():
        print(f"- 사용자명: {username}, 비밀번호: {info['password']}, 이름: {info['name']}")
    print("============================================================")
    print("* 모든 인증 코드는 '123456'으로 설정되어 있습니다.")
    print("* 서버 주소: http://localhost:5000")
    print("============================================================")

    app.run(host="0.0.0.0", port=5000, debug=True)