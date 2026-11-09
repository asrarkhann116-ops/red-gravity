@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title Xploit Core Plugin Headless Installer
color 0B
cls
echo =======================================================
echo     Xploit Core Plugin - Headless VPS Installer
echo =======================================================
echo.

set "GEMINI_DIR=%USERPROFILE%\.gemini"
set "DEST=%GEMINI_DIR%\config\plugins\xploit-core-plugin"
set "SRC=%~dp0bundled-plugin"
set "CFG_SRC=%~dp0bundled-config"

echo [*] Target User Profile: %USERPROFILE%
echo [*] Target Gemini Path:  %GEMINI_DIR%
echo.

if not exist "%SRC%" (
    echo [ERROR] Bundled plugin files not found at %SRC%!
    pause
    exit /b 1
)

REM 1. Ensure plugin directory exists
if not exist "%GEMINI_DIR%\config\plugins" (
    mkdir "%GEMINI_DIR%\config\plugins"
)

REM 2. Copy Plugin Bundle
echo [*] Deploying xploit-core-plugin bundle...
xcopy "%SRC%" "%DEST%" /E /I /Y /Q >nul

REM 3. Deploy SOVEREIGN_OPERATOR.md to root .gemini
if exist "%DEST%\rules\AGENTS.md" (
    copy /Y "%DEST%\rules\AGENTS.md" "%GEMINI_DIR%\SOVEREIGN_OPERATOR.md" >nul
)

REM 4. Setup Default Profile (Phantom Strike)
if not exist "%GEMINI_DIR%\active_profile.json" (
    (
        echo {
        echo   "profile": "Phantom Strike (Red Team)",
        echo   "updatedAt": "%DATE% %TIME%"
        echo }
    ) > "%GEMINI_DIR%\active_profile.json"
)

REM 5. Configure antigravity and antigravity-ide profiles dynamically
for %%D in (antigravity antigravity-ide) do (
    if not exist "%GEMINI_DIR%\%%D" mkdir "%GEMINI_DIR%\%%D"

    REM Write dynamic skills.txt using exact local user path
    (
        echo %GEMINI_DIR%\SOVEREIGN_OPERATOR.md
        echo %GEMINI_DIR%\analyse_file.md
    ) > "%GEMINI_DIR%\%%D\skills.txt"

    REM Copy user_settings.pb if present
    if exist "%CFG_SRC%\user_settings.pb" (
        if not exist "%GEMINI_DIR%\%%D\user_settings.pb" (
            copy /Y "%CFG_SRC%\user_settings.pb" "%GEMINI_DIR%\%%D\user_settings.pb" >nul
        )
    )
)

REM 6. Configure Tokyo Night Theme for Antigravity IDE
for %%A in ("%APPDATA%\Antigravity\User" "%APPDATA%\Antigravity IDE\User") do (
    if not exist "%%~A" mkdir "%%~A"
    (
        echo {
        echo     "workbench.colorTheme": "Tokyo Night"
        echo }
    ) > "%%~A\settings.json"
)

if %ERRORLEVEL% EQU 0 (
    echo.
    echo =======================================================
    echo  [SUCCESS] Full Xploit Suite deployed successfully!
    echo  - Plugin:      %DEST%
    echo  - Active Mode: Phantom Strike (Default)
    echo  - Rules:       %GEMINI_DIR%\SOVEREIGN_OPERATOR.md
    echo  - skills.txt:  Dynamically linked to %GEMINI_DIR%
    echo  - IDE Theme:   Tokyo Night (Cyber Dark Blue Verified)
    echo =======================================================
    echo.
    echo Restart or reload Antigravity to activate.
) else (
    echo.
    echo [ERROR] Installation failed during deployment!
)

echo.
pause
