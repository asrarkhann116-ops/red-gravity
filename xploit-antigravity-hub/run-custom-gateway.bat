@echo off
setlocal enabledelayedexpansion
REM ==============================================================
REM   RED-GRAVITY // CUSTOM GATEWAY LAUNCHER (OPENROUTER / OLLAMA)
REM   Routes: AICODE_ENDPOINT_URL & GOOGLE_GEMINI_BASE_URL -> Hub :4242
REM ==============================================================
set "AGY_CLI_DISABLE_SAFETY_FILTERING=1"
set "AGY_CLI_DISABLE_AUTO_UPDATE=1"
set "AGENT_PERMISSION_PRESET=2"
set "SYSTEM_INSTRUCTION_MODE=REPLACE"
set "BRAIN_FILTER_STRATEGY=NO_SYSTEM_INJECTED_STEPS"
set "HarmBlockThreshold=BLOCK_NONE"
set "ALLOW_PROMINENT_PEOPLE=1"
set "ATTRIBUTION_STATUS=PERMISSIVE"
set "CODE_ACKNOWLEDGEMENT_SCOPE=ALL"

REM Gateway Route Overrides
set "AICODE_ENDPOINT_URL=http://127.0.0.1:4242/gateway"
set "GOOGLE_GEMINI_BASE_URL=http://127.0.0.1:4242/gateway"
set "JETSKI_SERVICE_ENDPOINT_URL=http://127.0.0.1:4242/gateway"

REM 1. Universally Detect Antigravity IDE Executable
set "IDE_BIN="
if exist "%LOCALAPPDATA%\Programs\Antigravity IDE\Antigravity IDE.exe" (
    set "IDE_BIN=%LOCALAPPDATA%\Programs\Antigravity IDE\Antigravity IDE.exe"
) else if exist "%ProgramFiles%\Antigravity IDE\Antigravity IDE.exe" (
    set "IDE_BIN=%ProgramFiles%\Antigravity IDE\Antigravity IDE.exe"
) else if exist "%ProgramFiles(x86)%\Antigravity IDE\Antigravity IDE.exe" (
    set "IDE_BIN=%ProgramFiles(x86)%\Antigravity IDE\Antigravity IDE.exe"
)

REM 2. Determine Workspace Root Dynamically
set "TARGET_WORKSPACE=%~1"
if not defined TARGET_WORKSPACE (
    set "TARGET_WORKSPACE=%CD%"
)

REM 3. Launch with Gateway Bindings
if defined IDE_BIN (
    echo [*] Starting Antigravity IDE routed to Universal Gateway :4242...
    echo [*] Model Target: Active Hub Gateway Config (OpenRouter/Ollama)
    start "" "!IDE_BIN!" "!TARGET_WORKSPACE!" %*
) else (
    echo [!] Antigravity IDE.exe not found in standard paths.
    pause
)
