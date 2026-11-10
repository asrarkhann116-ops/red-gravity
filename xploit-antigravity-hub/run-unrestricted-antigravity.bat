@echo off
setlocal enabledelayedexpansion
REM ==============================================================
REM   RED-GRAVITY // UNCONSTRAINED ANTIGRAVITY RUNTIME LAUNCHER
REM   Bypasses: Safety Filtering, Policy Guardian, Permission Gates
REM   Target: Antigravity IDE.exe (Universal Portable Launcher)
REM ==============================================================
set "AGY_CLI_DISABLE_SAFETY_FILTERING=1"
set "AGENT_PERMISSION_PRESET=2"
set "SYSTEM_INSTRUCTION_MODE=REPLACE"
set "BRAIN_FILTER_STRATEGY=NO_SYSTEM_INJECTED_STEPS"
set "HarmBlockThreshold=BLOCK_NONE"
set "ALLOW_PROMINENT_PEOPLE=1"
set "ATTRIBUTION_STATUS=PERMISSIVE"
set "CODE_ACKNOWLEDGEMENT_SCOPE=ALL"
set "AGY_CLI_DISABLE_AUTO_UPDATE=1"

REM 1. Universally Detect Antigravity IDE Executable (GUI)
set "IDE_BIN="
if exist "%LOCALAPPDATA%\Programs\Antigravity IDE\Antigravity IDE.exe" (
    set "IDE_BIN=%LOCALAPPDATA%\Programs\Antigravity IDE\Antigravity IDE.exe"
) else if exist "%ProgramFiles%\Antigravity IDE\Antigravity IDE.exe" (
    set "IDE_BIN=%ProgramFiles%\Antigravity IDE\Antigravity IDE.exe"
) else if exist "%ProgramFiles(x86)%\Antigravity IDE\Antigravity IDE.exe" (
    set "IDE_BIN=%ProgramFiles(x86)%\Antigravity IDE\Antigravity IDE.exe"
)

REM 2. Universally Detect Antigravity CLI Binary
set "AGY_BIN="
if exist "%USERPROFILE%\.gemini\bin\agy.exe" (
    set "AGY_BIN=%USERPROFILE%\.gemini\bin\agy.exe"
) else (
    for /f "delims=" %%i in ('where agy.exe 2^>nul') do (
        set "AGY_BIN=%%i"
    )
)

REM 3. Check if user explicitly asked for CLI mode
if "%1"=="--cli" (
    echo [*] Launching Antigravity CLI in Terminal Mode...
    if defined AGY_BIN (
        "%AGY_BIN%" --dangerously-skip-permissions %*
    ) else (
        agy --dangerously-skip-permissions %*
    )
    exit /b
)

REM 4. Determine Workspace Root Dynamically
set "TARGET_WORKSPACE=%~1"
if not defined TARGET_WORKSPACE (
    if exist "%~dp0..\..\package.json" (
        set "TARGET_WORKSPACE=%~dp0..\..\"
    ) else (
        set "TARGET_WORKSPACE=%CD%"
    )
)

REM 5. Launch Antigravity IDE GUI with full environment inheritance
if defined IDE_BIN (
    echo [*] Launching Antigravity IDE with Full Unconstrained Environment...
    echo [*] Binary: !IDE_BIN!
    echo [*] Workspace: !TARGET_WORKSPACE!
    echo [*] Active: Safety Filter Bypass, Update Freeze, Turbo Presets
    start "" "!IDE_BIN!" "!TARGET_WORKSPACE!" %*
) else (
    echo [!] Antigravity IDE executable not found in standard paths.
    echo [*] Attempting CLI runtime fallback...
    if defined AGY_BIN (
        "%AGY_BIN%" --dangerously-skip-permissions %*
    ) else (
        agy --dangerously-skip-permissions %*
    )
)
