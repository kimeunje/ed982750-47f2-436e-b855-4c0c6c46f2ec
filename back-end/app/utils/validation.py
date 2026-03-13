# app/utils/validation.py
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict


class ValidationStrategy(ABC):
    """검증 전략 추상 클래스"""

    @abstractmethod
    def validate(self, actual_value: dict) -> bool:
        pass


class DefaultValidation(ValidationStrategy):
    """기본 검증 (항상 False 반환)"""

    def validate(self, actual_value: dict) -> bool:
        return False


class 화면보호기_사용(ValidationStrategy):

    def validate(self, actual_value: dict) -> bool:
        return (str(actual_value.get("screenSaverEnabled")) == "1"
                and int(actual_value.get("screenSaverTime", 0)) <= 600
                and str(actual_value.get("screenSaverSecure")) == "1")


class 사용자_계정명의_적정성(ValidationStrategy):

    def validate(self, actual_value: dict) -> bool:
        computer_name = actual_value.get("computer_name")
        user_name = actual_value.get("user_name")
        return str(computer_name) == str(user_name)


class 불필요한_계정_사용(ValidationStrategy):

    def validate(self, actual_value: dict) -> bool:
        actual_folders = actual_value.get("accounts", [])
        username = actual_value.get("user_name")
        required_folders = [
            "Administrator",
            "DefaultAccount",
            "Guest",
            "WDAGUtilityAccount",
            username,
        ]
        return set(actual_folders) == set(required_folders)


class 패스워드_길이의_적정성(ValidationStrategy):

    def validate(self, actual_value: dict) -> bool:
        return int(actual_value.get("minimumPasswordLength", 0)) >= 8


class 패스워드_복잡도_설정(ValidationStrategy):

    def validate(self, actual_value: dict) -> bool:
        return int(actual_value.get("passwordComplexity")) == 1


class 패스워드_주기적_변경(ValidationStrategy):

    def validate(self, actual_value: dict) -> bool:
        return int(actual_value.get("maximumPasswordAge", 0)) <= 90


class 동일_패스워드_설정_제한(ValidationStrategy):

    def validate(self, actual_value: dict) -> bool:
        return int(actual_value.get("passwordHistorySize")) >= 5


class 공유폴더_확인(ValidationStrategy):
    def validate(self, actual_value: dict) -> bool:
        actual_folders = actual_value.get("folders", [])
        
        # 공유 폴더가 없는 경우 패스 (보안상 안전함)
        if not actual_folders:
            return True
        
        # null이 포함된 경우 필터링 (실제로는 공유 폴더 없음)
        actual_folders = [folder for folder in actual_folders if folder is not None]
        
        # 필터링 후 빈 배열이면 패스
        if not actual_folders:
            return True
        
        # IPC$, C$, D$만 있는 경우 패스 (시스템 기본 공유)
        allowed_system_shares = {"IPC$", "C$", "D$", "ADMIN$", "E$", "F$", "HP LaserJet Pro M501 PCL 6", "print$"}
        if set(actual_folders).issubset(allowed_system_shares):
            return True
        
        # IPC$만 있는 경우 패스 (시스템 기본 공유)
        # if set(actual_folders) == {"IPC$"}:
        #     return True
        
        # 다른 불필요한 폴더가 있는 경우 실패
        return False


class 불분명_프린터_확인(ValidationStrategy):

    def validate(self, actual_value: dict) -> bool:
        actual_folders = actual_value.get("printers", [])
        required_folders = [
            "Sindoh uPrint Driver",
            "OneNote 2013으로 보내기",
            "Microsoft XPS Document Writer",
            "Microsoft Print to PDF",
        ]
        return set(actual_folders) == set(required_folders)


class 원격데스크톱_제한(ValidationStrategy):

    def validate(self, actual_value: dict) -> bool:
        return str(actual_value.get("fDenyTSConnections")) == "1"


class 불특정_소프트웨어_확인(ValidationStrategy):

    def validate(self, actual_value: dict) -> bool:
        min_office_version = "15.0.5589.1001"
        min_ahnlab_version = "1.13.0.1914"

        office_valid = False
        ahnlab_valid = False

        for component in actual_value:
            name = component.get("Name", "")
            version = component.get("Version", "0.0.0.0")

            if "Office 16" in name and version >= min_office_version:
                office_valid = True

            if "AhnLab Safe Transaction" in name and version >= min_ahnlab_version:
                ahnlab_valid = True

        return office_valid and ahnlab_valid


class OS_패치_확인(ValidationStrategy):

    # 지원되는 Windows 버전 정의
    supported_versions = [
        {
            "version": "Windows 10",
            "build": "20H2",
            "build_number": 19042,
            "end_date": datetime(2022, 5, 11),
        },
        {
            "version": "Windows 10",
            "build": "21H1",
            "build_number": 19043,
            "end_date": datetime(2022, 12, 14),
        },
        {
            "version": "Windows 10",
            "build": "21H2",
            "build_number": 19044,
            "end_date": datetime(2023, 6, 14),
        },
        {
            "version": "Windows 10",
            "build": "22H2",
            "build_number": 19045,
            "end_date": datetime(2025, 10, 15),
        },
        {
            "version": "Windows 11",
            "build": "22H2",
            "build_number": 22621,
            "end_date": datetime(2025, 10, 15),
        },
        {
            "version": "Windows 11",
            "build": "23H2",
            "build_number": 22631,
            "end_date": datetime(2026, 11, 11),
        },
        {
            "version": "Windows 11",
            "build": "24H2",
            "build_number": 26100,
            "end_date": datetime(2027, 10, 13),
        },
    ]

    def validate(self, actual_value: dict) -> bool:
        windows_version = actual_value.get("windowsVersion", "")
        build_number = int(actual_value.get("windowsBuildNumber", 0))

        current_date = datetime.now()

        for entry in self.supported_versions:
            if (entry["version"] in windows_version
                    and build_number == entry["build_number"]):
                return current_date <= entry["end_date"]

        return False


class 방화벽_활성화_확인(ValidationStrategy):

    def validate(self, actual_value: dict) -> bool:
        required_profiles = ["Domain", "Private", "Public"]

        for profile in required_profiles:
            if profile not in actual_value or actual_value.get(profile) != 1:
                return False

        return True


class 이동매체_자동실행_제한(ValidationStrategy):

    def validate(self, actual_value: dict) -> bool:
        value = actual_value.get("Value")

        if isinstance(value, str) and value.isdigit():
            value = int(value)

        if isinstance(value, int):
            return value >= 255 or value == 95

        return False


# 검증 전략 매핑
VALIDATION_STRATEGIES: Dict[str, ValidationStrategy] = {
    "화면보호기 사용": 화면보호기_사용(),
    "사용자 계정명의 적정성": 사용자_계정명의_적정성(),
    "불필요한 계정 사용": 불필요한_계정_사용(),
    "패스워드 길이의 적정성": 패스워드_길이의_적정성(),
    "패스워드 복잡도 설정": 패스워드_복잡도_설정(),
    "패스워드 주기적 변경": 패스워드_주기적_변경(),
    "동일 패스워드 설정 제한": 동일_패스워드_설정_제한(),
    "공유폴더 확인": 공유폴더_확인(),
    "불분명 프린터 확인": 불분명_프린터_확인(),
    "방화벽 활성화 확인": 방화벽_활성화_확인(),
    "원격데스크톱 제한": 원격데스크톱_제한(),
    "소프트웨어 패치 관리": DefaultValidation(),
    "불특정 소프트웨어 확인": 불특정_소프트웨어_확인(),
    "이동매체 자동실행 제한": 이동매체_자동실행_제한(),
    "OS 패치 확인": OS_패치_확인(),
}


def validate_security_item(item_name: str, actual_value: dict) -> bool:
    """보안 항목 검증"""
    strategy = VALIDATION_STRATEGIES.get(item_name, DefaultValidation())
    return strategy.validate(actual_value)


def generate_notes(item_name: str, passed: int, actual_value: dict) -> str:
    """검증 결과에 따라 자동으로 notes를 생성하는 함수"""
    if passed == 1:
        return _get_success_message(item_name)
    else:
        return _get_failure_message(item_name, actual_value)


def _get_success_message(item_name: str) -> str:
    """통과한 경우의 메시지"""
    success_messages = {
        "화면보호기 사용": "화면 보호기가 정상적으로 설정되어 있습니다.",
        "사용자 계정명의 적정성": "사용자 계정명이 적절하게 설정되어 있습니다.",
        "불필요한 계정 사용": "불필요한 계정이 없습니다.",
        "패스워드 길이의 적정성": "암호 길이가 정책에 맞게 설정되어 있습니다.",
        "패스워드 복잡도 설정": "암호 복잡도가 적절하게 설정되어 있습니다.",
        "패스워드 주기적 변경": "암호 변경 주기가 적절하게 설정되어 있습니다.",
        "동일 패스워드 설정 제한": "동일 암호 사용 제한이 적절하게 설정되어 있습니다.",
        "방화벽 활성화 확인": "모든 방화벽 프로필(Domain, Private, Public)이 정상적으로 활성화되어 있습니다.",
        "공유폴더 확인": "불필요한 공유 폴더가 없습니다.",
        "불분명 프린터 확인": "인가되지 않은 프린터가 없습니다.",
        "원격데스크톱 제한": "원격 데스크톱이 적절하게 제한되어 있습니다.",
        "이동매체 자동실행 제한": "이동식 미디어 자동실행이 올바르게 제한되어 있습니다.",
        "불특정 소프트웨어 확인": "모든 소프트웨어가 최신 버전으로 업데이트되어 있습니다.",
        "OS 패치 확인": "운영체제가 최신 상태로 업데이트되어 있습니다.",
    }
    return success_messages.get(item_name, "검사 항목이 정상적으로 확인되었습니다.")


def _get_failure_message(item_name: str, actual_value: dict) -> str:
    """실패한 경우의 메시지"""
    if item_name == "방화벽 활성화 확인":
        disabled_profiles = []
        for profile in ["Domain", "Private", "Public"]:
            if profile not in actual_value or actual_value.get(profile) != 1:
                disabled_profiles.append(profile)

        if disabled_profiles:
            disabled_str = ", ".join(disabled_profiles)
            return f"일부 방화벽 프로필({disabled_str})이 비활성화되어 있습니다. 모든 프로필(Domain, Private, Public)을 활성화해주세요."

    failure_messages = {
        "화면보호기 사용": f"화면 보호기 설정이 정책에 맞지 않습니다. 현재 설정: 활성화={actual_value.get('screenSaverEnabled')}, 시간={actual_value.get('screenSaverTime')}초, 암호설정={actual_value.get('screenSaverSecure')}. 화면 보호기 활성화 및 10분(600초) 이내 설정, 재시작 시 암호 필요 옵션을 켜주세요.",
        "사용자 계정명의 적정성": f"사용자 계정명({actual_value.get('computer_name')})이 지정된 이름({actual_value.get('user_name')})과 일치하지 않습니다. 계정명을 수정해주세요.",
        "불필요한 계정 사용": "불필요한 계정이 발견되었습니다. 필요하지 않은 계정을 비활성화하거나 제거해주세요.",
        "패스워드 길이의 적정성": f"암호 길이가 정책(8자 이상)에 맞지 않습니다. 현재 설정: {actual_value.get('minimumPasswordLength')}자. 암호 길이를 8자 이상으로 설정해주세요.",
        "패스워드 복잡도 설정": "암호 복잡도가 설정되어 있지 않습니다. 암호 복잡도 설정을 활성화해주세요.",
        "패스워드 주기적 변경": f"암호 변경 주기가 정책(90일 이내)에 맞지 않습니다. 현재 설정: {actual_value.get('maximumPasswordAge')}일. 90일 이내로 설정해주세요.",
        "동일 패스워드 설정 제한": f"동일 암호 사용 제한이 정책(5회 이상)에 맞지 않습니다. 현재 설정: {actual_value.get('passwordHistorySize')}회. 5회 이상으로 설정해주세요.",
        "공유폴더 확인": "불필요한 공유 폴더가 있습니다. 필요하지 않은 공유 폴더를 제거해주세요.",
        "방화벽 활성화 확인": "일부 방화벽 프로필이 비활성화되어 있습니다. 모든 프로필(Domain, Private, Public)을 활성화해주세요.",
        "불분명 프린터 확인": "인가되지 않은 프린터가 있습니다. 불필요한 프린터를 제거해주세요.",
        "원격데스크톱 제한": "원격 데스크톱이 활성화되어 있습니다. 보안을 위해 비활성화해주세요.",
        "이동매체 자동실행 제한": f"이동식 미디어 자동실행이 제한되어 있지 않습니다. 현재 값: {actual_value.get('Value', '없음')}. 레지스트리 설정(NoDriveTypeAutoRun)을 255 또는 95로 설정하여 자동실행을 제한해주세요.",
        "불특정 소프트웨어 확인": "일부 소프트웨어가 최신 버전이 아닙니다. 소프트웨어를 업데이트해주세요.",
        "OS 패치 확인": f"운영체제({actual_value.get('windowsVersion')}, 빌드:{actual_value.get('windowsBuildNumber')})가 최신 상태가 아닙니다. 윈도우 업데이트를 실행하여 최신 상태로 유지해주세요.",
    }
    return failure_messages.get(item_name, "검사 항목이 정책에 맞지 않습니다. 확인이 필요합니다.")
