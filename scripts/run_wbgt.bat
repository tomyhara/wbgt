@echo off
REM WBGT キオスク実行スクリプト（日本語版）
REM WBGT Kiosk Runner Script (Japanese Version)

setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
set "APP_PATH=%PROJECT_ROOT%\src\wbgt_kiosk.py"
set "VENV_PATH=%PROJECT_ROOT%\venv"

REM Color codes for output
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "CYAN=[96m"
set "WHITE=[97m"
set "BOLD=[1m"
set "RESET=[0m"

REM Initialize variables
set "DEMO_MODE="
set "GUI_MODE="
set "SHOW_HELP="
set "SHOW_VERSION="

REM Parse command line arguments
:parse_args
if "%~1"=="" goto end_parse
if "%~1"=="--help" set "SHOW_HELP=1" & goto next_arg
if "%~1"=="-h" set "SHOW_HELP=1" & goto next_arg
if "%~1"=="--version" set "SHOW_VERSION=1" & goto next_arg
if "%~1"=="-v" set "SHOW_VERSION=1" & goto next_arg
if "%~1"=="--demo" set "DEMO_MODE=--demo" & goto next_arg
if "%~1"=="--gui" set "GUI_MODE=--gui" & goto next_arg
echo %RED%Unknown option: %~1%RESET%
goto show_help
:next_arg
shift
goto parse_args
:end_parse

REM Show help if requested
if defined SHOW_HELP goto show_help

REM Show version if requested
if defined SHOW_VERSION goto show_version

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo %RED%ERROR: Python is not installed or not in PATH%RESET%
    exit /b 1
)

REM Check if application exists
if not exist "%APP_PATH%" (
    echo %RED%ERROR: Application not found at %APP_PATH%%RESET%
    exit /b 1
)

REM Header
echo %CYAN%==================================================================%RESET%
echo %BOLD%  🌡️  WBGT熱中症警戒キオスク (日本語版) / WBGT Heat Stroke Warning Kiosk (Japanese)%RESET%
echo %CYAN%  Version 2.0.0 - %DATE%%RESET%
echo %CYAN%==================================================================%RESET%
echo.

REM Activate virtual environment if it exists
if exist "%VENV_PATH%\Scripts\activate.bat" (
    echo %CYAN%INFO: Activating virtual environment...%RESET%
    call "%VENV_PATH%\Scripts\activate.bat"
    echo %GREEN%SUCCESS: Virtual environment activated%RESET%
) else (
    echo %YELLOW%WARN: Virtual environment not found at %VENV_PATH%%RESET%
    echo %CYAN%INFO: Using system Python. Consider running setup script.%RESET%
)

REM Run application
echo %CYAN%INFO: Starting Japanese WBGT Kiosk...%RESET%

REM Build command with proper argument handling
if defined DEMO_MODE if defined GUI_MODE (
    python "%APP_PATH%" --demo --gui
) else if defined DEMO_MODE (
    python "%APP_PATH%" --demo
) else if defined GUI_MODE (
    python "%APP_PATH%" --gui
) else (
    python "%APP_PATH%"
)
set "EXIT_CODE=%ERRORLEVEL%"

REM Show completion message
echo.
echo %CYAN%==================================================================%RESET%
if %EXIT_CODE%==0 (
    echo %GREEN%  ✅ Script completed successfully%RESET%
) else (
    echo %RED%  ❌ Script completed with errors (Exit code: %EXIT_CODE%)%RESET%
)
echo %CYAN%==================================================================%RESET%

exit /b %EXIT_CODE%

:show_help
echo %CYAN%==================================================================%RESET%
echo %BOLD%  🌡️  WBGT熱中症警戒キオスク (日本語版) / WBGT Heat Stroke Warning Kiosk (Japanese)%RESET%
echo %CYAN%==================================================================%RESET%
echo.
echo %WHITE%使用方法 / Usage:%RESET%
echo   %0 [OPTIONS]
echo.
echo %YELLOW%オプション / Options:%RESET%
echo   --demo              デモモード (3回更新で終了) / Demo mode (3 updates then exit)
echo   --gui               GUI版 (実験的) / GUI version (experimental)
echo   --help, -h          ヘルプ表示 / Show this help
echo   --version, -v       バージョン情報 / Version information
echo.
echo %YELLOW%例 / Examples:%RESET%
echo   %0                  通常モード / Normal mode
echo   %0 --demo          デモモード / Demo mode
echo   %0 --gui           GUI版 / GUI version
echo.
echo %GREEN%設定 / Configuration:%RESET%
echo   設定ファイル: setup\config.json または setup\config.py
echo   Config file: setup\config.json or setup\config.py
exit /b 0

:show_version
echo %CYAN%==================================================================%RESET%
echo %BOLD%  🌡️  WBGT熱中症警戒キオスク (日本語版)%RESET%
echo %CYAN%==================================================================%RESET%
echo %GREEN%Version: 2.0.0%RESET%
echo %CYAN%Language: Japanese (日本語)%RESET%
exit /b 0