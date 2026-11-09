@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title Xploit Antigravity Hub // Silk Edition
color 0F
cls
echo =======================================================
echo        XPLOIT ANTIGRAVITY HUB // SILK EDITION
echo   Universal Plugin Orchestrator ^& System Pathfinder
echo =======================================================
echo.

REM Verify Node.js presence
where node >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not found in PATH!
    echo Please install Node.js from https://nodejs.org
    echo.
    pause
    exit /b 1
)

echo [*] Initializing Xploit Hub background service...
start "Xploit Daemon" /min node server.js

REM Short delay for daemon startup
ping 127.0.0.1 -n 3 >nul

echo [*] Launching UI Window...
set "LAUNCHED="

if exist "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" (
    start "" "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" --app=http://127.0.0.1:4242 --window-size=1200,850
    set "LAUNCHED=1"
)

if not defined LAUNCHED if exist "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" (
    start "" "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" --app=http://127.0.0.1:4242 --window-size=1200,850
    set "LAUNCHED=1"
)

if not defined LAUNCHED if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (
    start "" "%ProgramFiles%\Google\Chrome\Application\chrome.exe" --app=http://127.0.0.1:4242 --window-size=1200,850
    set "LAUNCHED=1"
)

if not defined LAUNCHED (
    start http://127.0.0.1:4242
)

echo.
echo =======================================================
echo  [SUCCESS] Xploit Antigravity Hub is now running!
echo  URL: http://127.0.0.1:4242
echo =======================================================
echo.
echo Press any key to stop the hub daemon and exit.
pause >nul

REM Cleanup daemon on exit
taskkill /F /FI "WINDOWTITLE eq Xploit Daemon*" >nul 2>&1
exit /b 0
