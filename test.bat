@echo off
setlocal enabledelayedexpansion

:: ===================================================================
:: Windows Security Audit Script - Final Fixed Version
:: ===================================================================

:: === 숨김 모드 실행 체크 ===
if "%~1"=="HIDDEN" goto :main_execution

:: 자기 자신을 숨김 모드로 재실행
powershell -Command "Start-Process -FilePath 'cmd.exe' -ArgumentList '/c \"%~f0\" HIDDEN' -WindowStyle Hidden"
exit /b

:main_execution
:: === Environment Setup ===
REM UTF-8 encoding setup
chcp 65001 > nul

:: === API Server Configuration ===
set SERVER_URL=http://localhost:5000


:: Log directory setup
set "LOG_DIR=%TEMP%\security_audit"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

:: Temporary file setup
set "TEMP_RESPONSE=%LOG_DIR%\response.json"
set "TEMP_BODY=%LOG_DIR%\body.json"

echo ===================================================================
echo                    Windows Security Audit Tool
echo ===================================================================
echo.

:: === Main Execution ===
:main
    call :authenticate_user
    if !ERRORLEVEL! neq 0 goto :cleanup
    
    echo.
    echo Starting security audit...
    echo.
    
    :: Perform security checks
    call :check_antivirus
    call :check_screensaver
    call :check_password_policy
    call :check_shared_folders
    call :check_remote_desktop
    
    echo.
    echo ===================================================================
    echo All security checks completed successfully.
    echo ===================================================================
    
:cleanup
    :: Clean up temporary files
    if exist "%TEMP_RESPONSE%" del "%TEMP_RESPONSE%" > nul 2>&1
    if exist "%TEMP_BODY%" del "%TEMP_BODY%" > nul 2>&1
    if exist "%LOG_DIR%\security.inf" del "%LOG_DIR%\security.inf" > nul 2>&1

    exit /b

:: ===================================================================
:: User Authentication Function
:: ===================================================================
:authenticate_user
    echo User information retrieval started...
    
    :: 1. Get IP information
    echo Retrieving IP-based user information...
    curl -s -X GET "%SERVER_URL%/api/auth/ip-info" -H "Content-Type: application/json; charset=utf-8" -o "%TEMP_RESPONSE%"
    if %ERRORLEVEL% neq 0 (
        echo [CONNECTION FAILED] Cannot connect to API server.
        exit /b 1
    )
    
    :: Extract IP
    for /f "tokens=2 delims=:," %%a in ('type "%TEMP_RESPONSE%" ^| findstr /i "client_ip"') do (
        set CLIENT_IP=%%~a
        set CLIENT_IP=!CLIENT_IP:"=!
        set CLIENT_IP=!CLIENT_IP: =!
    )
    echo Client IP: !CLIENT_IP!
    
    :: 2. IP check API call
    echo {} > "%TEMP_BODY%"
    curl -s -X POST "%SERVER_URL%/api/auth/check-ip" -H "Content-Type: application/json; charset=utf-8" -d @"%TEMP_BODY%" -o "%TEMP_RESPONSE%"
    if %ERRORLEVEL% neq 0 (
        echo IP check failed
        exit /b 1
    )
    
    :: Check success and get username
    set USERNAME=DefaultUser
    for /f "tokens=2 delims=:," %%a in ('type "%TEMP_RESPONSE%" ^| findstr /i "success"') do (
        set SUCCESS=%%~a
        set SUCCESS=!SUCCESS:"=!
        set SUCCESS=!SUCCESS: =!
    )
    
    if "!SUCCESS!"=="true" (
        for /f "tokens=2 delims=:," %%a in ('type "%TEMP_RESPONSE%" ^| findstr /i "\"username\""') do (
            set USERNAME=%%~a
            set USERNAME=!USERNAME:"=!
            set USERNAME=!USERNAME: =!
            set USERNAME=!USERNAME:}=!
        )
        echo User setup completed: !USERNAME!
    ) else (
        echo User setup failed. Using default user.
    )
    
    :: 3. User authentication API call
    echo Initializing audit log...
    echo {"username": "!USERNAME!"} > "%TEMP_BODY%"
    
    curl -s -X POST "%SERVER_URL%/api/auth/authenticate" -H "Content-Type: application/json; charset=utf-8" -d @"%TEMP_BODY%" -o "%TEMP_RESPONSE%"
    if %ERRORLEVEL% neq 0 (
        echo User authentication API call failed
        exit /b 1
    )
    
    :: Check authentication status and get user_id
    for /f "tokens=2 delims=:," %%a in ('type "%TEMP_RESPONSE%" ^| findstr /i "status"') do (
        set AUTH_STATUS=%%~a
        set AUTH_STATUS=!AUTH_STATUS:"=!
        set AUTH_STATUS=!AUTH_STATUS: =!
    )
    
    if "!AUTH_STATUS!"=="failed" (
        echo User verification failed. Please contact operations.
        exit /b 1
    )
    
    :: Extract user_id
    for /f "tokens=2 delims=:," %%a in ('type "%TEMP_RESPONSE%" ^| findstr /i "user_id"') do (
        set USER_ID=%%~a
        set USER_ID=!USER_ID:"=!
        set USER_ID=!USER_ID: =!
        set USER_ID=!USER_ID:}=!
    )
    
    echo User verification and audit log initialization successful
    echo Username: !USERNAME!
    echo User ID: !USER_ID!
    exit /b 0

:: ===================================================================
:: Antivirus Status Check
:: ===================================================================
:check_antivirus
    echo.
    echo [1/5] Checking antivirus status...
    
    :: Initialize values
    set "AV_NAME=Not Installed"
    set "AV_REALTIME=0"
    set "AV_UPDATE=0"
    
    :: Check for Alyac antivirus using wmic
    set "TEMP_AV=%LOG_DIR%\alyac_info.txt"
    wmic /namespace:\\root\SecurityCenter2 path AntivirusProduct where "DisplayName like '%%알약%%'" get DisplayName,ProductState /format:list > "%TEMP_AV%" 2>nul
    
    :: Parse results
    set "FOUND_ALYAC=0"
    for /f "tokens=1,2 delims==" %%a in ('type "%TEMP_AV%" 2^>nul ^| findstr /v "^$"') do (
        if /i "%%a"=="DisplayName" (
            set "AV_NAME=%%b"
            for /f "tokens=*" %%c in ("!AV_NAME!") do set "AV_NAME=%%c"
            set "FOUND_ALYAC=1"
        )
        
        if /i "%%a"=="ProductState" (
            set "PRODUCT_STATE=%%b"
            for /f "tokens=*" %%c in ("!PRODUCT_STATE!") do set "PRODUCT_STATE=%%c"
            
            :: Interpret ProductState values
            if "!PRODUCT_STATE!"=="397568" (
                set "AV_REALTIME=1"
                set "AV_UPDATE=1"
            ) else if "!PRODUCT_STATE!"=="397584" (
                set "AV_REALTIME=0"
                set "AV_UPDATE=1"
            ) else if "!PRODUCT_STATE!"=="397312" (
                set "AV_REALTIME=1"
                set "AV_UPDATE=0"
            ) else (
                set "AV_REALTIME=1"
                set "AV_UPDATE=1"
            )
        )
    )
    
    :: Clean up temporary file
    if exist "%TEMP_AV%" del "%TEMP_AV%" > nul 2>&1
    
    :: Display results
    if "!FOUND_ALYAC!"=="1" (
        echo    ✓ Alyac antivirus detected: !AV_NAME!
        echo      - Real-time protection: !AV_REALTIME!
        echo      - Update status: !AV_UPDATE!
    ) else (
        echo    ✗ Alyac antivirus not installed
    )
    
    :: Send to server using PowerShell
    powershell -Command "$data = @{user_id='!USER_ID!'; item_type='백신 상태 확인'; actual_value=@{DisplayName='!AV_NAME!'; RealTimeProtection=!AV_REALTIME!; UpToDate=!AV_UPDATE!}}; ConvertTo-Json $data -Depth 3 -Compress | Out-File -FilePath '%TEMP_BODY%' -Encoding UTF8 -NoNewline"
    curl -s -X POST "%SERVER_URL%/api/security-audit/validate_check" -H "Content-Type: application/json; charset=utf-8" -d @"%TEMP_BODY%" -o "%TEMP_RESPONSE%" >nul 2>&1
    goto :eof

:: ===================================================================
:: Screen Saver Check
:: ===================================================================
:check_screensaver
    echo.
    echo [2/5] Checking screen saver configuration...
    
    :: Get screen saver settings from registry
    set "SCREENSAVER_ENABLED=0"
    set "SCREENSAVER_TIME=0"
    set "SCREENSAVER_SECURE=0"
    
    :: Extract ScreenSaveActive
    for /f "tokens=3" %%a in ('reg query "HKCU\Control Panel\Desktop" /v ScreenSaveActive 2^>nul ^| findstr ScreenSaveActive') do (
        set "SCREENSAVER_ENABLED=%%a"
    )
    
    :: Extract ScreenSaveTimeOut
    for /f "tokens=3" %%a in ('reg query "HKCU\Control Panel\Desktop" /v ScreenSaveTimeOut 2^>nul ^| findstr ScreenSaveTimeOut') do (
        set "SCREENSAVER_TIME=%%a"
    )
    
    :: Extract ScreenSaverIsSecure
    for /f "tokens=3" %%a in ('reg query "HKCU\Control Panel\Desktop" /v ScreenSaverIsSecure 2^>nul ^| findstr ScreenSaverIsSecure') do (
        set "SCREENSAVER_SECURE=%%a"
    )
    
    :: Convert hex values if needed
    if "!SCREENSAVER_ENABLED!"=="0x0" set "SCREENSAVER_ENABLED=0"
    if "!SCREENSAVER_ENABLED!"=="0x1" set "SCREENSAVER_ENABLED=1"
    if "!SCREENSAVER_SECURE!"=="0x0" set "SCREENSAVER_SECURE=0"
    if "!SCREENSAVER_SECURE!"=="0x1" set "SCREENSAVER_SECURE=1"
    
    :: Display results properly
    if "!SCREENSAVER_ENABLED!"=="1" (
        echo    ✓ Screen saver enabled
        echo      - Timeout: !SCREENSAVER_TIME! seconds
        if "!SCREENSAVER_SECURE!"=="1" (
            echo      - Security: Enabled ^(password required^)
        ) else (
            echo      - Security: Disabled ^(password not required^)
        )
    ) else (
        echo    ✗ Screen saver disabled
    )
    
    :: Send to server using PowerShell
    powershell -Command "$data = @{user_id='!USER_ID!'; item_type='화면보호기 사용'; actual_value=@{screenSaverEnabled='!SCREENSAVER_ENABLED!'; screenSaverTime='!SCREENSAVER_TIME!'; screenSaverSecure='!SCREENSAVER_SECURE!'}}; ConvertTo-Json $data -Depth 3 -Compress | Out-File -FilePath '%TEMP_BODY%' -Encoding UTF8 -NoNewline"
    curl -s -X POST "%SERVER_URL%/api/security-audit/validate_check" -H "Content-Type: application/json; charset=utf-8" -d @"%TEMP_BODY%" -o "%TEMP_RESPONSE%" >nul 2>&1
    goto :eof

:: ===================================================================
:: Password Policy Check
:: ===================================================================
:check_password_policy
    echo.
    echo [3/5] Checking password policy...
    
    :: Export security policy
    secedit /export /cfg "%LOG_DIR%\security.inf" /areas SECURITYPOLICY >nul 2>&1
    
    :: Initialize policy values
    set "MIN_PASSWORD_LENGTH=0"
    set "PASSWORD_COMPLEXITY=null"
    set "MAX_PASSWORD_AGE=0"
    set "PASSWORD_HISTORY=0"
    
    if exist "%LOG_DIR%\security.inf" (
        :: Extract values from security.inf
        for /f "tokens=2 delims==" %%a in ('type "%LOG_DIR%\security.inf" ^| findstr /B /C:"MinimumPasswordLength = "') do (
            set "MIN_PASSWORD_LENGTH=%%a"
        )
        for /f "tokens=2 delims==" %%a in ('type "%LOG_DIR%\security.inf" ^| findstr /B /C:"PasswordComplexity = "') do (
            set "PASSWORD_COMPLEXITY=%%a"
        )
        for /f "tokens=2 delims==" %%a in ('type "%LOG_DIR%\security.inf" ^| findstr /B /C:"MaximumPasswordAge = "') do (
            set "MAX_PASSWORD_AGE=%%a"
        )
        for /f "tokens=2 delims==" %%a in ('type "%LOG_DIR%\security.inf" ^| findstr /B /C:"PasswordHistorySize = "') do (
            set "PASSWORD_HISTORY=%%a"
        )
    )
    
    :: Remove spaces
    set "MIN_PASSWORD_LENGTH=!MIN_PASSWORD_LENGTH: =!"
    set "PASSWORD_COMPLEXITY=!PASSWORD_COMPLEXITY: =!"
    set "MAX_PASSWORD_AGE=!MAX_PASSWORD_AGE: =!"
    set "PASSWORD_HISTORY=!PASSWORD_HISTORY: =!"
    
    :: Display results
    echo    Password Policy Settings:
    echo      - Minimum length: !MIN_PASSWORD_LENGTH! characters
    echo      - Complexity: !PASSWORD_COMPLEXITY!
    echo      - Maximum age: !MAX_PASSWORD_AGE! days
    echo      - History: !PASSWORD_HISTORY! passwords
    
    :: Send each policy to server using PowerShell
    powershell -Command "$data = @{user_id='!USER_ID!'; item_type='패스워드 길이의 적정성'; actual_value=@{minimumPasswordLength='!MIN_PASSWORD_LENGTH!'}}; ConvertTo-Json $data -Depth 3 -Compress | Out-File -FilePath '%TEMP_BODY%' -Encoding UTF8 -NoNewline"
    curl -s -X POST "%SERVER_URL%/api/security-audit/validate_check" -H "Content-Type: application/json; charset=utf-8" -d @"%TEMP_BODY%" -o "%TEMP_RESPONSE%" >nul 2>&1
    
    powershell -Command "$data = @{user_id='!USER_ID!'; item_type='패스워드 복잡도 설정'; actual_value=@{passwordComplexity=!PASSWORD_COMPLEXITY!}}; ConvertTo-Json $data -Depth 3 -Compress | Out-File -FilePath '%TEMP_BODY%' -Encoding UTF8 -NoNewline"
    curl -s -X POST "%SERVER_URL%/api/security-audit/validate_check" -H "Content-Type: application/json; charset=utf-8" -d @"%TEMP_BODY%" -o "%TEMP_RESPONSE%" >nul 2>&1
    
    powershell -Command "$data = @{user_id='!USER_ID!'; item_type='패스워드 주기적 변경'; actual_value=@{maximumPasswordAge='!MAX_PASSWORD_AGE!'}}; ConvertTo-Json $data -Depth 3 -Compress | Out-File -FilePath '%TEMP_BODY%' -Encoding UTF8 -NoNewline"
    curl -s -X POST "%SERVER_URL%/api/security-audit/validate_check" -H "Content-Type: application/json; charset=utf-8" -d @"%TEMP_BODY%" -o "%TEMP_RESPONSE%" >nul 2>&1
    
    powershell -Command "$data = @{user_id='!USER_ID!'; item_type='동일 패스워드 설정 제한'; actual_value=@{passwordHistorySize='!PASSWORD_HISTORY!'}}; ConvertTo-Json $data -Depth 3 -Compress | Out-File -FilePath '%TEMP_BODY%' -Encoding UTF8 -NoNewline"
    curl -s -X POST "%SERVER_URL%/api/security-audit/validate_check" -H "Content-Type: application/json; charset=utf-8" -d @"%TEMP_BODY%" -o "%TEMP_RESPONSE%" >nul 2>&1
    goto :eof

:: ===================================================================
:: Shared Folders Check (FIXED - Always returns array)
:: ===================================================================
:check_shared_folders
    echo.
    echo [4/5] Checking shared folders...
    
    :: Get shared folders using PowerShell - FORCE ARRAY FORMAT
    powershell -Command "$shares = @((Get-WmiObject Win32_Share).Name); $shareData = @{user_id='!USER_ID!'; item_type='공유폴더 확인'; actual_value=@{folders=$shares}}; ConvertTo-Json $shareData -Depth 3 -Compress | Out-File -FilePath '%TEMP_BODY%' -Encoding UTF8 -NoNewline"
    
    :: Display found shares
    echo    Shared folders found:
    for /f "tokens=*" %%a in ('wmic share get name /value 2^>nul ^| findstr "Name=" ^| findstr /v "Name=$"') do (
        set "SHARE_NAME=%%a"
        set "SHARE_NAME=!SHARE_NAME:Name=!"
        echo      - !SHARE_NAME!
    )
    
    :: Send to server
    curl -s -X POST "%SERVER_URL%/api/security-audit/validate_check" -H "Content-Type: application/json; charset=utf-8" -d @"%TEMP_BODY%" -o "%TEMP_RESPONSE%" >nul 2>&1
    goto :eof

:: ===================================================================
:: Remote Desktop Check
:: ===================================================================
:check_remote_desktop
    echo.
    echo [5/5] Checking remote desktop settings...
    
    :: Check remote desktop setting
    set "RDP_DENY=1"
    for /f "tokens=3" %%a in ('reg query "HKLM\System\CurrentControlSet\Control\Terminal Server" /v fDenyTSConnections 2^>nul ^| findstr fDenyTSConnections') do (
        set "RDP_DENY=%%a"
    )
    
    :: Convert hex values
    if "!RDP_DENY!"=="0x0" set "RDP_DENY=0"
    if "!RDP_DENY!"=="0x1" set "RDP_DENY=1"
    
    :: Display result
    if "!RDP_DENY!"=="1" (
        echo    ✓ Remote desktop disabled
    ) else (
        echo    ✗ Remote desktop enabled
    )
    
    :: Send to server using PowerShell
    powershell -Command "$data = @{user_id='!USER_ID!'; item_type='원격데스크톱 제한'; actual_value=@{fDenyTSConnections=!RDP_DENY!}}; ConvertTo-Json $data -Depth 3 -Compress | Out-File -FilePath '%TEMP_BODY%' -Encoding UTF8 -NoNewline"
    curl -s -X POST "%SERVER_URL%/api/security-audit/validate_check" -H "Content-Type: application/json; charset=utf-8" -d @"%TEMP_BODY%" -o "%TEMP_RESPONSE%" >nul 2>&1
    goto :eof