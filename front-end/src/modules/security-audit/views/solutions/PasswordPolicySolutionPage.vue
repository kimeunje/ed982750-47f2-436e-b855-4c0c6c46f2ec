<!-- Template 부분 -->
<template>
  <div class="security-audit-layout">
    <!-- 모바일 메뉴 토글 버튼 -->
    <button
      v-if="sidebarRef?.isMobile"
      @click="sidebarRef?.toggleSidebar()"
      class="mobile-menu-toggle"
    >
      <svg width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
        <path
          fill-rule="evenodd"
          d="M2.5 12a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5zm0-4a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5zm0-4a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5z"
        />
      </svg>
    </button>

    <!-- 사이드바 -->
    <Sidebar ref="sidebarRef" />

    <!-- 메인 콘텐츠 -->
    <main class="main-content">
      <div v-if="!authStore.user" class="not-authenticated">
        <div class="auth-warning">
          <div class="warning-icon">
            <svg width="48" height="48" fill="currentColor" viewBox="0 0 16 16">
              <path
                d="M8.982 1.566a1.13 1.13 0 0 0-1.96 0L.165 13.233c-.457.778.091 1.767.98 1.767h13.713c.889 0 1.438-.99.98-1.767L8.982 1.566zM8 5c.535 0 .954.462.9.995l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 5.995A.905.905 0 0 1 8 5zm.002 6a1 1 0 1 1 0 2 1 1 0 0 1 0-2z"
              />
            </svg>
          </div>
          <h2>인증이 필요합니다</h2>
          <p>패스워드 정책 점검 가이드를 확인하려면 로그인이 필요합니다.</p>
          <div class="auth-actions">
            <RouterLink to="/login" class="login-button">
              <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                <path
                  fill-rule="evenodd"
                  d="M6 12.5a.5.5 0 0 0 .5.5h8a.5.5 0 0 0 .5-.5v-9a.5.5 0 0 0-.5-.5h-8a.5.5 0 0 0-.5.5v2a.5.5 0 0 1-1 0v-2A1.5 1.5 0 0 1 6.5 2h8A1.5 1.5 0 0 1 16 3.5v9a1.5 1.5 0 0 1-1.5 1.5h-8A1.5 1.5 0 0 1 5 12.5v-2a.5.5 0 0 1 1 0v2z"
                />
                <path
                  fill-rule="evenodd"
                  d="M.146 8.354a.5.5 0 0 1 0-.708l3-3a.5.5 0 1 1 .708.708L1.707 7.5H10.5a.5.5 0 0 1 0 1H1.707l2.147 2.146a.5.5 0 0 1-.708.708l-3-3z"
                />
              </svg>
              로그인하기
            </RouterLink>
          </div>
        </div>
      </div>

      <!-- 인증된 사용자용 콘텐츠 -->
      <div v-else>
        <h1 class="page-title">패스워드 정책 점검</h1>

        <!-- 개요 -->
        <div class="section">
          <h2 class="section-title">개요</h2>
          <p>
            강력한 패스워드 정책은 무단 접근을 방지하는 가장 기본적이고 중요한 보안 수단입니다.
            패스워드 길이, 복잡도, 변경 주기, 재사용 제한 등의 정책을 적절히 설정하여 계정 보안을
            강화해야 합니다.
          </p>
        </div>

        <!-- 패스워드 정책 요구사항 -->
        <div class="section">
          <h2 class="section-title">패스워드 정책 요구사항</h2>
          <div class="requirements-grid">
            <div class="requirement-card">
              <div class="requirement-icon length">
                <svg width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
                  <path
                    d="M8 1a2.5 2.5 0 0 1 2.5 2.5V4h-5v-.5A2.5 2.5 0 0 1 8 1zm3.5 3v-.5a3.5 3.5 0 1 0-7 0V4H1v10a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V4h-3.5zM2 5h12v9a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V5z"
                  />
                </svg>
              </div>
              <h3>최소 길이 8자 이상</h3>
              <p>패스워드는 최소 8자 이상으로 설정되어야 하며, 더 긴 패스워드를 권장합니다.</p>
            </div>
            <div class="requirement-card">
              <div class="requirement-icon complexity">
                <svg width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
                  <path
                    d="M6 10.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 0 1h-3a.5.5 0 0 1-.5-.5zm-2-3a.5.5 0 0 1 .5-.5h7a.5.5 0 0 1 0 1h-7a.5.5 0 0 1-.5-.5zm-2-3a.5.5 0 0 1 .5-.5h11a.5.5 0 0 1 0 1h-11a.5.5 0 0 1-.5-.5z"
                  />
                </svg>
              </div>
              <h3>복잡도 설정</h3>
              <p>대문자, 소문자, 숫자, 특수문자를 포함한 복합적인 패스워드 구성이 필요합니다.</p>
            </div>
            <div class="requirement-card">
              <div class="requirement-icon period">
                <svg width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
                  <path
                    d="M6 .5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 0 1H9v1.07a7.001 7.001 0 0 1 3.274 12.474l-.81.81a.5.5 0 0 1-.708-.708l.81-.81A6.001 6.001 0 0 0 2.49 3.174a.5.5 0 0 1-.566-.832 7.001 7.001 0 0 1 4.076-1.334V1H6.5a.5.5 0 0 1-.5-.5z"
                  />
                  <path
                    d="M4.5 5.5a.5.5 0 0 1 .5.5v5.293l4.146-4.147a.5.5 0 0 1 .708.708L5.707 12H11a.5.5 0 0 1 0 1H4.5a.5.5 0 0 1-.5-.5V6a.5.5 0 0 1 .5-.5z"
                  />
                </svg>
              </div>
              <h3>주기적 변경 (90일)</h3>
              <p>패스워드는 최대 90일마다 변경되도록 설정하여 보안을 유지해야 합니다.</p>
            </div>
            <div class="requirement-card">
              <div class="requirement-icon history">
                <svg width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
                  <path d="M11 6a3 3 0 1 1-6 0 3 3 0 0 1 6 0z" />
                  <path
                    fill-rule="evenodd"
                    d="M0 8a8 8 0 1 1 16 0A8 8 0 0 1 0 8zm8-7a7 7 0 0 0-5.468 11.37C3.242 11.226 4.805 10 8 10s4.757 1.225 5.468 2.37A7 7 0 0 0 8 1z"
                  />
                </svg>
              </div>
              <h3>재사용 제한 (5회)</h3>
              <p>이전에 사용했던 패스워드 5개는 재사용할 수 없도록 제한해야 합니다.</p>
            </div>
          </div>
        </div>

        <!-- 수동 설정 방법 -->
        <div class="section">
          <h2 class="section-title">수동 설정 방법</h2>

          <ol>
            <li><kbd>Windows</kbd> + <kbd>R</kbd> 키를 눌러 실행 창 열기</li>
            <li><code>secpol.msc</code> 입력 후 <kbd>Enter</kbd> (관리자 권한 필요)</li>
            <li>좌측 트리에서 <strong>[계정 정책]</strong> → <strong>[암호 정책]</strong> 선택</li>
            <li>각 정책을 더블클릭하여 다음과 같이 설정:</li>
          </ol>

          <div class="policy-table">
            <table>
              <thead>
                <tr>
                  <th>정책 이름</th>
                  <th>권장 설정값</th>
                  <th>설명</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>암호는 복잡성을 만족해야 함</td>
                  <td><span class="setting-value">사용</span></td>
                  <td>대/소문자, 숫자, 특수문자 포함</td>
                </tr>
                <tr>
                  <td>최대 암호 사용 기간</td>
                  <td><span class="setting-value">90일</span></td>
                  <td>90일마다 패스워드 변경 필요</td>
                </tr>
                <tr>
                  <td>최소 암호 길이</td>
                  <td><span class="setting-value">8자</span></td>
                  <td>최소 8자 이상의 패스워드</td>
                </tr>
                <tr>
                  <td>암호 기록 저장</td>
                  <td><span class="setting-value">5개</span></td>
                  <td>이전 5개 패스워드 재사용 금지</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- 스크립트 다운로드 섹션 -->
        <div class="section">
          <h2 class="section-title">자동화 스크립트</h2>
          <div class="script-download-section">
            <div class="script-card">
              <div class="script-icon setup">
                <svg width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
                  <path
                    d="M8 4.754a3.246 3.246 0 1 0 0 6.492 3.246 3.246 0 0 0 0-6.492zM5.754 8a2.246 2.246 0 1 1 4.492 0 2.246 2.246 0 0 1-4.492 0z"
                  />
                  <path
                    d="M9.796 1.343c-.527-1.79-3.065-1.79-3.592 0l-.094.319a.873.873 0 0 1-1.255.52l-.292-.16c-1.64-.892-3.433.902-2.54 2.541l.159.292a.873.873 0 0 1-.52 1.255l-.319.094c-1.79.527-1.79 3.065 0 3.592l.319.094a.873.873 0 0 1 .52 1.255l-.16.292c-.892 1.64.901 3.434 2.541 2.54l.292-.159a.873.873 0 0 1 1.255.52l.094.319c.527 1.79 3.065 1.79 3.592 0l.094-.319a.873.873 0 0 1 1.255-.52l.292.16c1.64.893 3.434-.902 2.54-2.541l-.159-.292a.873.873 0 0 1 .52-1.255l.319-.094c1.79-.527 1.79-3.065 0-3.592l-.319-.094a.873.873 0 0 1-.52-1.255l.16-.292c.893-1.64-.902-3.433-2.541-2.54l-.292.159a.873.873 0 0 1-1.255-.52l-.094-.319zm-2.633.283c.246-.835 1.428-.835 1.674 0l.094.319a1.873 1.873 0 0 0 2.693 1.115l.291-.16c.764-.415 1.6.42 1.184 1.185l-.159.292a1.873 1.873 0 0 0 1.116 2.692l.318.094c.835.246.835 1.428 0 1.674l-.319.094a1.873 1.873 0 0 0-1.115 2.693l.16.291c.415.764-.42 1.6-1.185 1.184l-.291-.159a1.873 1.873 0 0 0-2.693 1.116l-.094.318c-.246.835-1.428.835-1.674 0l-.094-.319a1.873 1.873 0 0 0-2.692-1.115l-.292.16c-.764.415-1.6-.42-1.184-1.185l.159-.291A1.873 1.873 0 0 0 1.945 8.93l-.319-.094c-.835-.246-.835-1.428 0-1.674l.319-.094A1.873 1.873 0 0 0 3.06 4.377l-.16-.292c-.415-.764.42-1.6 1.185-1.184l.292.159a1.873 1.873 0 0 0 2.692-1.115l.094-.319z"
                  />
                </svg>
              </div>
              <div class="script-content">
                <h3>패스워드 정책 설정 스크립트</h3>
                <p>권장 패스워드 정책을 자동으로 적용하는 배치 스크립트입니다.</p>
                <button @click="downloadConfigScript" class="download-button primary">
                  <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                    <path
                      d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"
                    />
                    <path
                      d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"
                    />
                  </svg>
                  다운로드
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- 페이지 네비게이션 -->
        <PageNavigation :current-path="route.path" />
      </div>
    </main>
  </div>
</template>

<script setup>
// Script 부분
import { ref } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import JSZip from 'jszip'
import Sidebar from '@/components/Sidebar.vue'
import PageNavigation from '@/components/PageNavigation.vue'

const route = useRoute()
const authStore = useAuthStore()
const sidebarRef = ref(null)

// ZIP 파일 다운로드 함수 (JSZip 사용)
const downloadZipWithJSZip = async (files, zipFilename) => {
  try {
    const zip = new JSZip()

    files.forEach((file) => {
      zip.file(file.name, file.content)
    })

    const zipBlob = await zip.generateAsync({ type: 'blob' })
    const url = window.URL.createObjectURL(zipBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = zipFilename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (err) {
    console.error('ZIP 파일 다운로드 실패:', err)
  }
}

// 사용법
const downloadConfigScript = async () => {
  const files = [
    {
      name: '조치 스크립트.bat',
      content: SetupScript,
    },
  ]
  await downloadZipWithJSZip(files, '조치 스크립트.zip')
}

// Windows CRLF 줄바꿈으로 변환하는 함수
const convertToWindowsLineEndings = (content) => {
  return content.replace(/\r?\n/g, '\r\n')
}

// 1. 조치 스크립트.bat 내용을 포함한 변수 추가
const SetupScript = convertToWindowsLineEndings(`@echo off

::  --> 관리자 권한 실행 코드
:-------------------------------------
>nul 2>&1 "%SYSTEMROOT%\\system32\\cacls.exe" "%SYSTEMROOT%\\system32\\config\\system"

if '%errorlevel%' NEQ '0' (
 goto UACPrompt
) else ( goto gotAdmin )

:UACPrompt
 echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\\getadmin.vbs"
 echo UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\\getadmin.vbs"

"%temp%\\getadmin.vbs"
 exit /B

:gotAdmin
 if exist "%temp%\\getadmin.vbs" ( del "%temp%\\getadmin.vbs" )
 pushd "%CD%"
 CD /D "%~dp0"
:--------------------------------------


::  --> UTF-8 인코딩 설정
:-------------------------------------
chcp 65001 > nul

::  --> 배치 파일 기본 설정
:-------------------------------------
TITLE %~n0
SETLOCAL enabledelayedexpansion

::  --> 특정 IP 설정 (여기에 원격데스크톱을 유지할 IP 주소들을 입력하세요)
:-------------------------------------
set ALLOWED_IPS=10.106.15.100 10.106.15.101 10.106.15.102 10.106.15.103 10.106.15.104 10.106.15.105 10.106.15.114 10.106.15.115 10.106.15.117 10.106.15.125
set SKIP_RDP_DISABLE=0

::  --> 현재 컴퓨터의 IP 주소 확인
:-------------------------------------
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    set IP=%%a
    set IP=!IP: =!
    for %%b in (%ALLOWED_IPS%) do (
        if "!IP!"=="%%b" (
            set SKIP_RDP_DISABLE=1
        )
    )
)
:-------------------------------------

::  --> 검사 후 조치
:-------------------------------------
CLS
ECHO.
ECHO * 주의사항 - 조치 중에는 키보드, 마우스를 움직이지 말아주세요.

ECHO.
echo ※ 윈도우 시스템 설정값 변경 ※
echo.

echo 1.1 화면보호기 설정, 잠금 설정, 10분 설정 완료
Reg add "HKEY_CURRENT_USER\\Control Panel\\Desktop" /v SCRNSAVE.EXE /t REG_SZ /d C:\\Windows\\System32\\scrnsave.scr /f | find /v "success"
Reg add "HKEY_CURRENT_USER\\Control Panel\\Desktop" /v ScreenSaveActive /t REG_SZ /d 1 /f | find /v "success"
Reg add "HKEY_CURRENT_USER\\Control Panel\\Desktop" /v ScreenSaverIsSecure /t REG_SZ /d 1 /f | find /v "success"
Reg add "HKEY_CURRENT_USER\\Control Panel\\Desktop" /v ScreenSaveTimeOut /t REG_SZ /d 600 /f | find /v "success"
echo.

echo 2.1 암호 복잡도 설정 완료
secedit /export /cfg "%temp%\\secpol.cfg" > nul
powershell -Command "(Get-Content '%temp%\\secpol.cfg') -replace 'PasswordComplexity = 0', 'PasswordComplexity = 1' | Set-Content '%temp%\\secpol.cfg'"
secedit /configure /db %windir%\\security\\local.sdb /cfg "%temp%\secpol.cfg" /areas SECURITYPOLICY > nul
del "%temp%\\secpol.cfg" > nul
echo.

echo 2.3 최소 암호 길이 8자리로 변경 완료
net accounts /minpwlen:8 | find /v "success"

echo 2.4 암호 복잡도 요구사항 활성화 완료
Reg add "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\Lsa" /v NoLMHash /t REG_DWORD /d 0x00000001 /f | find /v "success"

echo 2.5 최대 암호 사용 기간 90일로 변경 완료
net accounts /maxpwage:90 | find /v "success"

echo 2.7 최근 암호 기억 5개로 변경 완료
net accounts /uniquepw:5 | find /v "success"

echo 3.1 불필요한 공유폴더 삭제 완료 ^(IPC$ 제외한 모든 공유폴더 제거^)
:: 모든 공유폴더 목록을 가져와서 IPC$를 제외하고 삭제
for /f "skip=1 tokens=1" %%s in ('net share ^| findstr /v "^$" ^| findstr /v "명령을 잘못" ^| findstr /v "The command completed"') do (
    if /i not "%%s"=="IPC$" (
        net share "%%s" /delete /y > nul 2>&1
    )
)
Reg add "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\Lsa" /v restrictanonymous /t REG_DWORD /d 0x00000001 /f | find /v "success"
Reg add "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\LanmanServer\\Parameters" /v AutoShareServer /t REG_DWORD /d 0x00000000 /f | find /v "success"
Reg add "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\LanmanServer\\Parameters" /v AutoShareWks /t REG_DWORD /d 0x00000000 /f | find /v "success"
echo.

:: IP 조건에 따라 원격데스크톱 설정 처리
if %SKIP_RDP_DISABLE%==1 (
    echo 3.3 원격데스크톱 설정 유지 ^(허용된 IP 주소^)
) else (
    echo 3.3 원격데스크톱 해제 완료
    Reg add "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server" /v fDenyTSConnections /t REG_DWORD /d 0x00000001 /f | find /v "success"
    Reg add "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server\\WinStations\\RDP-Tcp" /v UserAuthentication /t REG_DWORD /d 0x00000001 /f | find /v "success"
)
echo.

TIMEOUT /t 2 > NUL
echo.
echo ※ 모든 보안 조치가 완료되었습니다. ※
echo.
echo ※ 시스템 재시작을 권장합니다. ※
:-------------------------------------

pause`)
</script>

<style scoped>
.security-audit-layout {
  display: flex;
  background-color: var(--bright-bg);
  min-height: calc(100vh - 114px);
}

.main-content {
  flex: 1;
  padding: 30px;
  background-color: var(--content-bg);
  border-radius: 8px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  margin: 20px;
}

/* 모바일 메뉴 토글 */
.mobile-menu-toggle {
  display: none;
  position: fixed;
  top: 20px;
  left: 20px;
  z-index: 1001;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 12px;
  cursor: pointer;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

@media (max-width: 768px) {
  .mobile-menu-toggle {
    display: block;
  }
}

/* 인증 관련 스타일 */
.not-authenticated {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 60vh;
}

.auth-warning {
  text-align: center;
  padding: 40px;
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  border: 1px solid #fee2e2;
}

.warning-icon {
  color: #f59e0b;
  margin-bottom: 20px;
}

.auth-warning h2 {
  color: var(--dark-blue);
  margin-bottom: 12px;
  font-size: 1.5rem;
}

.auth-warning p {
  color: #6b7280;
  margin-bottom: 24px;
  font-size: 1rem;
}

.login-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background-color: var(--primary-color);
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.3s ease;
}

.login-button:hover {
  background-color: var(--dark-blue);
  transform: translateY(-2px);
}

/* 페이지 타이틀 */
.page-title {
  font-size: 2rem;
  font-weight: 700;
  color: var(--dark-blue);
  margin-bottom: 2rem;
  border-bottom: 3px solid var(--primary-blue);
  padding-bottom: 0.5rem;
}

/* 섹션 스타일 */

.section ol {
  margin-left: 20px;
  margin-bottom: 16px;
}

.section ol li {
  margin-bottom: 8px;
  line-height: 1.5;
  color: #374151;
}

.section h3 {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--dark-blue);
  margin: 24px 0 12px 0;
}

/* 요구사항 그리드 */
.requirements-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  margin: 20px 0;
}

.requirement-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 24px;
  text-align: center;
  transition: all 0.3s ease;
}

.requirement-card:hover {
  border-color: var(--primary-color);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.requirement-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
  color: white;
}

.requirement-icon.length {
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
}

.requirement-icon.complexity {
  background: linear-gradient(135deg, #10b981, #059669);
}

.requirement-icon.period {
  background: linear-gradient(135deg, #f59e0b, #d97706);
}

.requirement-icon.history {
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
}

.requirement-card h3 {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--dark-blue);
  margin: 0 0 8px 0;
}

.requirement-card p {
  color: #6b7280;
  font-size: 0.9rem;
  line-height: 1.5;
  margin: 0;
}

/* 정책 테이블 */
.policy-table {
  margin: 20px 0;
  overflow-x: auto;
}

.policy-table table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.policy-table th {
  background: var(--primary-color);
  color: white;
  padding: 12px 16px;
  text-align: left;
  font-weight: 600;
}

.policy-table td {
  padding: 12px 16px;
  border-bottom: 1px solid #e5e7eb;
}

.policy-table tr:last-child td {
  border-bottom: none;
}

.policy-table tr:nth-child(even) {
  background: #f9fafb;
}

.setting-value {
  background: #dbeafe;
  color: #1d4ed8;
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: 600;
  font-size: 0.875rem;
}

/* 코드 블록 스타일 */
.code-block {
  background-color: #1f2937;
  border-radius: 8px;
  padding: 20px;
  margin: 20px 0;
}

.code-block h3 {
  color: #e5e7eb;
  margin: 0 0 16px 0;
  font-size: 1rem;
  font-weight: 600;
}

.code-container {
  position: relative;
}

.code-container pre {
  background-color: transparent;
  color: #e5e7eb;
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
  line-height: 1.5;
  margin: 0;
  padding: 0;
  overflow-x: auto;
}

.code-container code {
  background-color: transparent;
  color: inherit;
  padding: 0;
}

.copy-button {
  position: absolute;
  top: 8px;
  right: 8px;
  background-color: #374151;
  color: #e5e7eb;
  border: none;
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 0.875rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: background-color 0.2s ease;
}

.copy-button:hover {
  background-color: #4b5563;
}

/* 스크립트 다운로드 섹션 */
.script-download-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin: 20px 0;
}

.script-card {
  background-color: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 24px;
  transition: all 0.3s ease;
}

.script-card:hover {
  border-color: var(--primary-color);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.script-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  margin-bottom: 16px;
}

.script-icon.setup {
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
}

.script-icon.check {
  background: linear-gradient(135deg, #10b981, #059669);
}

.script-content h3 {
  margin: 0 0 8px 0;
  color: var(--dark-blue);
  font-size: 1.125rem;
  font-weight: 600;
}

.script-content p {
  margin: 0 0 16px 0;
  color: #6b7280;
  font-size: 0.9rem;
  line-height: 1.5;
}

.download-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  text-decoration: none;
}

.download-button.primary {
  background-color: var(--primary-color);
  color: white;
}

.download-button.primary:hover {
  background-color: var(--dark-blue);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(64, 86, 183, 0.3);
}

.download-button.secondary {
  background-color: #10b981;
  color: white;
}

.download-button.secondary:hover {
  background-color: #059669;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(16, 185, 129, 0.3);
}

/* 사용법 정보 */
.usage-info {
  background-color: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 20px;
  margin-top: 24px;
}

.usage-info h4 {
  margin: 0 0 12px 0;
  color: var(--dark-blue);
  font-size: 1rem;
  font-weight: 600;
}

.usage-info ol {
  margin: 0;
  padding-left: 20px;
}

.usage-info li {
  margin-bottom: 8px;
  line-height: 1.5;
  color: #374151;
}

.usage-info code {
  background-color: #1f2937;
  color: #e5e7eb;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.875rem;
}

/* 키보드 키 스타일 */
kbd {
  background-color: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 0.875rem;
  font-family: monospace;
  color: #374151;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

/* 정보 그리드 */
.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin: 20px 0;
}

.info-card {
  border-radius: 12px;
  padding: 24px;
  border-left: 4px solid;
}

.info-card.warning {
  background-color: #fef3c7;
  border-left-color: #f59e0b;
}

.info-card.tip {
  background-color: #dbeafe;
  border-left-color: #3b82f6;
}

.info-icon {
  margin-bottom: 12px;
}

.info-card.warning .info-icon {
  color: #f59e0b;
}

.info-card.tip .info-icon {
  color: #3b82f6;
}

.info-content h3 {
  margin: 0 0 12px 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--dark-blue);
}

.info-content ul {
  margin: 0;
  padding-left: 20px;
}

.info-content li {
  margin-bottom: 8px;
  line-height: 1.5;
  color: #374151;
}

/* 반응형 디자인 */
@media (max-width: 768px) {
  .main-content {
    margin: 10px;
    padding: 20px;
  }

  .page-title {
    font-size: 1.5rem;
  }

  .section-title {
    font-size: 1.25rem;
  }

  .requirements-grid {
    grid-template-columns: 1fr;
  }

  .script-download-section {
    grid-template-columns: 1fr;
  }

  .info-grid {
    grid-template-columns: 1fr;
  }

  .policy-table {
    font-size: 0.875rem;
  }

  .policy-table th,
  .policy-table td {
    padding: 8px 12px;
  }
}

@media (max-width: 480px) {
  .policy-table th,
  .policy-table td {
    padding: 6px 8px;
    font-size: 0.8rem;
  }

  .requirement-icon {
    width: 50px;
    height: 50px;
  }
}
</style>
