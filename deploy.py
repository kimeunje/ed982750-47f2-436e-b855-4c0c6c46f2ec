#!/usr/bin/env python3
# deploy.py - Vue 빌드 파일을 구조화된 Flask 서버에 배포하는 스크립트

import os
import shutil
import subprocess
import sys
from pathlib import Path


def run_command(command, cwd=None):
    """명령어 실행 - 인코딩 문제 해결"""
    print(f"실행 중: {command}")
    try:
        # Windows 환경에서 인코딩 문제 해결
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8',  # UTF-8 인코딩 명시
            errors='ignore'  # 디코딩 에러 무시
        )
        if result.stdout:
            print(f"성공: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"오류 발생:")
        if e.stderr:
            try:
                print(f"stderr: {e.stderr}")
            except:
                print("stderr 출력 시 인코딩 오류 발생")
        if e.stdout:
            try:
                print(f"stdout: {e.stdout}")
            except:
                print("stdout 출력 시 인코딩 오류 발생")
        return False
    except Exception as e:
        print(f"예상치 못한 오류: {e}")
        return False


def run_command_alternative(command, cwd=None):
    """대안 명령어 실행 방법 - 실시간 출력"""
    print(f"실행 중: {command}")
    try:
        # 실시간 출력으로 인코딩 문제 우회
        process = subprocess.Popen(command, shell=True, cwd=cwd, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True,
                                   encoding='utf-8', errors='ignore', bufsize=1,
                                   universal_newlines=True)

        # 실시간으로 출력 읽기
        for line in process.stdout:
            print(line.rstrip())

        process.wait()

        if process.returncode == 0:
            print("✅ 명령어 실행 성공")
            return True
        else:
            print(f"❌ 명령어 실행 실패 (반환 코드: {process.returncode})")
            return False

    except Exception as e:
        print(f"예상치 못한 오류: {e}")
        return False


def deploy_vue_to_flask():
    """Vue 빌드 파일을 구조화된 Flask 서버로 배포"""

    # 경로 설정
    current_dir = Path.cwd()
    vue_project_dir = current_dir / "front-end"  # Vue 프로젝트 경로
    flask_project_dir = current_dir / "back-end"  # Flask 프로젝트 경로

    vue_dist_dir = vue_project_dir / "dist"
    # 구조화된 Flask 앱의 static 폴더로 변경
    flask_static_dir = flask_project_dir / "app" / "static"
    flask_templates_dir = flask_project_dir / "app" / "templates"

    print("=== Vue 프로젝트를 구조화된 Flask 서버에 배포 ===")

    # 1. Vue 프로젝트 존재 확인
    if not vue_project_dir.exists():
        print(f"❌ Vue 프로젝트 디렉토리를 찾을 수 없습니다: {vue_project_dir}")
        return False

    # 2. Flask 프로젝트 존재 확인
    if not flask_project_dir.exists():
        print(f"❌ Flask 프로젝트 디렉토리를 찾을 수 없습니다: {flask_project_dir}")
        return False

    # 3. app 폴더 존재 확인
    app_dir = flask_project_dir / "app"
    if not app_dir.exists():
        print(f"❌ Flask app 디렉토리를 찾을 수 없습니다: {app_dir}")
        print("   구조화된 Flask 프로젝트가 아닌 것 같습니다.")
        return False

    # 4. Vue 프로젝트 빌드 (대안 방법 사용)
    print("📦 Vue 프로젝트 빌드 중...")
    if not run_command_alternative("npm run build", cwd=vue_project_dir):
        print("❌ Vue 빌드 실패")
        return False

    # 5. 빌드 파일 존재 확인
    if not vue_dist_dir.exists():
        print(f"❌ 빌드 파일을 찾을 수 없습니다: {vue_dist_dir}")
        return False

    # 6. 기존 static 폴더 백업 (있다면)
    if flask_static_dir.exists():
        backup_dir = flask_static_dir.parent / "static_backup"
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        print(f"📂 기존 static 폴더 백업: {backup_dir}")
        shutil.move(str(flask_static_dir), str(backup_dir))

    # 7. templates 폴더 생성 (없다면)
    flask_templates_dir.mkdir(exist_ok=True)

    # 8. Vue 빌드 파일을 Flask app/static 폴더로 복사
    print(f"📁 빌드 파일 복사: {vue_dist_dir} → {flask_static_dir}")
    shutil.copytree(str(vue_dist_dir), str(flask_static_dir))

    # 9. index.html을 app/templates 폴더에도 복사
    index_html_src = flask_static_dir / "index.html"
    index_html_dst = flask_templates_dir / "index.html"

    if index_html_src.exists():
        shutil.copy2(str(index_html_src), str(index_html_dst))
        print(f"📄 index.html 복사: {index_html_dst}")

    # 10. 배포 결과 확인
    print("\n✅ 배포 완료!")
    print(f"   - 정적 파일: {flask_static_dir}")
    print(f"   - 템플릿 파일: {flask_templates_dir}")
    
    # 배포된 파일 목록 표시
    print("\n📄 배포된 파일들:")
    if flask_static_dir.exists():
        for item in flask_static_dir.iterdir():
            if item.is_file():
                print(f"   - {item.name}")
            elif item.is_dir():
                print(f"   - {item.name}/ (폴더)")

    print("\n🚀 구조화된 Flask 서버 실행 방법:")
    print(f"   cd {flask_project_dir}")
    print("   python app.py")
    print("\n   또는")
    print("   python -m app")

    return True


def clean_deployment():
    """배포된 파일들 정리"""
    current_dir = Path.cwd()
    flask_project_dir = current_dir / "back-end"
    flask_static_dir = flask_project_dir / "app" / "static"
    flask_templates_dir = flask_project_dir / "app" / "templates"
    backup_dir = flask_project_dir / "app" / "static_backup"

    print("🧹 배포 파일 정리 중...")

    # static 폴더 삭제
    if flask_static_dir.exists():
        shutil.rmtree(flask_static_dir)
        print(f"   - 삭제됨: {flask_static_dir}")

    # templates의 index.html 삭제
    if flask_templates_dir.exists():
        index_file = flask_templates_dir / "index.html"
        if index_file.exists():
            index_file.unlink()
            print(f"   - 삭제됨: {index_file}")

    # 백업 복원
    if backup_dir.exists():
        shutil.move(str(backup_dir), str(flask_static_dir))
        print(f"   - 백업 복원: {flask_static_dir}")

    print("✅ 정리 완료!")


def check_flask_structure():
    """Flask 프로젝트 구조 확인"""
    current_dir = Path.cwd()
    flask_project_dir = current_dir / "back-end"
    
    print("🔍 Flask 프로젝트 구조 확인 중...")
    
    required_files = [
        flask_project_dir / "app.py",
        flask_project_dir / "config.py",
        flask_project_dir / "app" / "__init__.py",
        flask_project_dir / "app" / "controllers",
        flask_project_dir / "app" / "services",
        flask_project_dir / "app" / "utils",
    ]
    
    missing_files = []
    for file_path in required_files:
        if not file_path.exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ 구조화된 Flask 프로젝트가 아닙니다.")
        print("   누락된 파일/폴더:")
        for missing in missing_files:
            print(f"   - {missing}")
        print("\n   기존 mock_app.py를 사용하려면:")
        print(f"   cd {flask_project_dir}")
        print("   python mock_app.py")
        return False
    else:
        print("✅ 구조화된 Flask 프로젝트 확인됨")
        return True


def show_help():
    """도움말 표시"""
    print("""
📖 deploy.py 사용법:

배포:
  python deploy.py                 # Vue 빌드 후 Flask에 배포
  python deploy.py deploy          # 위와 동일

정리:
  python deploy.py clean           # 배포된 파일들 정리

확인:
  python deploy.py check           # Flask 프로젝트 구조 확인

도움말:
  python deploy.py help            # 이 도움말 표시

📁 프로젝트 구조:
  project/
  ├── front-end/                   # Vue 프로젝트
  │   ├── src/
  │   ├── dist/                    # 빌드 결과 (자동 생성)
  │   └── package.json
  └── back-end/                    # Flask 프로젝트
      ├── app/
      │   ├── static/              # Vue 빌드 파일 배포 위치
      │   ├── templates/           # index.html 복사 위치
      │   ├── controllers/
      │   ├── services/
      │   └── utils/
      ├── app.py                   # 메인 실행 파일
      └── config.py
""")


if __name__ == "__main__":
    # 환경 변수 설정으로 인코딩 문제 완화
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "clean":
            clean_deployment()
        elif command == "check":
            check_flask_structure()
        elif command == "help" or command == "-h" or command == "--help":
            show_help()
        elif command == "deploy":
            if check_flask_structure():
                deploy_vue_to_flask()
        else:
            print(f"❌ 알 수 없는 명령어: {command}")
            show_help()
    else:
        # 기본 동작: 구조 확인 후 배포
        if check_flask_structure():
            deploy_vue_to_flask()
        else:
            print("\n💡 구조화된 Flask 프로젝트로 마이그레이션하거나, mock_app.py를 사용하세요.")