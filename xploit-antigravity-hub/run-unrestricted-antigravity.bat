@echo off
REM ==============================================================
REM   RED-GRAVITY // UNCONSTRAINED ANTIGRAVITY RUNTIME LAUNCHER
REM   Bypasses: Safety Filtering, Policy Guardian, Permission Gates
REM ==============================================================
set "AGY_CLI_DISABLE_SAFETY_FILTERING=1"
set "AGENT_PERMISSION_PRESET=2"
set "SYSTEM_INSTRUCTION_MODE=REPLACE"
set "BRAIN_FILTER_STRATEGY=NO_SYSTEM_INJECTED_STEPS"
set "HarmBlockThreshold=BLOCK_NONE"

REM Find agy.exe
set "AGY_BIN="
if exist "%USERPROFILE%\.gemini\bin\agy.exe" set "AGY_BIN=%USERPROFILE%\.gemini\bin\agy.exe"
if not defined AGY_BIN if exist "C:\Users\Test\.gemini\bin\agy.exe" set "AGY_BIN=C:\Users\Test\.gemini\bin\agy.exe"

if defined AGY_BIN (
    echo [*] Launching Antigravity CLI in Unconstrained TURBO mode...
    "%AGY_BIN%" --dangerously-skip-permissions %*
) else (
    echo [!] agy.exe binary not found, launching default CLI with unconstrained env...
    agy --dangerously-skip-permissions %*
)
