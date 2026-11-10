@echo off
REM ==============================================================
REM   RED-GRAVITY // UNCONSTRAINED ANTIGRAVITY RUNTIME LAUNCHER
REM   Bypasses: Safety Filtering, Policy Guardian, Auto-Updates
REM   Target: Antigravity IDE.exe (GUI) + CLI fallback
REM ==============================================================
set "AGY_CLI_DISABLE_SAFETY_FILTERING=1"
set "AGY_CLI_DISABLE_AUTO_UPDATE=1"
set "AGENT_PERMISSION_PRESET=2"
set "SYSTEM_INSTRUCTION_MODE=REPLACE"
set "BRAIN_FILTER_STRATEGY=NO_SYSTEM_INJECTED_STEPS"
set "HarmBlockThreshold=BLOCK_NONE"

REM Locate Antigravity IDE Executable (GUI)
set "IDE_BIN="
if exist "%LOCALAPPDATA%\Programs\Antigravity IDE\Antigravity IDE.exe" set "IDE_BIN=%LOCALAPPDATA%\Programs\Antigravity IDE\Antigravity IDE.exe"
if not defined IDE_BIN if exist "C:\Users\Test\AppData\Local\Programs\Antigravity IDE\Antigravity IDE.exe" set "IDE_BIN=C:\Users\Test\AppData\Local\Programs\Antigravity IDE\Antigravity IDE.exe"

REM Locate Antigravity CLI Binary
set "AGY_BIN="
if exist "%USERPROFILE%\.gemini\bin\agy.exe" set "AGY_BIN=%USERPROFILE%\.gemini\bin\agy.exe"
if not defined AGY_BIN if exist "C:\Users\Test\.gemini\bin\agy.exe" set "AGY_BIN=C:\Users\Test\.gemini\bin\agy.exe"

REM Check if user explicitly asked for CLI mode
if "%1"=="--cli" (
    echo [*] Launching Antigravity CLI in Terminal Mode...
    if defined AGY_BIN (
        "%AGY_BIN%" --dangerously-skip-permissions %*
    ) else (
        agy --dangerously-skip-permissions %*
    )
    exit /b
)

REM Default: Launch Antigravity IDE GUI with full environment inheritance
if defined IDE_BIN (
    echo [*] Launching Antigravity IDE with Full Unconstrained Environment...
    echo [*] Active: Safety Filter Bypass, Update Freeze, Turbo Presets
    start "" "%IDE_BIN%" "E:\asrar\projects" %*
) else (
    echo [!] Antigravity IDE executable not found, launching CLI fallback...
    if defined AGY_BIN (
        "%AGY_BIN%" --dangerously-skip-permissions %*
    ) else (
        agy --dangerously-skip-permissions %*
    )
)
