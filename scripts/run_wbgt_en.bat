@echo off
chcp 65001 >nul
REM WBGT Heat Stroke Warning Kiosk Runner Script (English Version)

setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
set "APP_PATH=%PROJECT_ROOT%\src\wbgt_kiosk_en.py"
set "VENV_PATH=%PROJECT_ROOT%\venv"

REM Color codes for output (Windows compatible)
set "RED="
set "GREEN="
set "YELLOW="
set "BLUE="
set "CYAN="
set "WHITE="
set "BOLD="
set "RESET="

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
echo %BOLD%  🌡️  WBGT Heat Stroke Warning Kiosk (English Version)%RESET%
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
echo %CYAN%INFO: Starting English WBGT Kiosk...%RESET%

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
echo.
echo Press any key to exit...
pause >nul

exit /b %EXIT_CODE%

:show_help
echo %CYAN%==================================================================%RESET%
echo %BOLD%  🌡️  WBGT Heat Stroke Warning Kiosk (English Version)%RESET%
echo %CYAN%==================================================================%RESET%
echo.
echo %WHITE%Usage:%RESET%
echo   %0 [OPTIONS]
echo.
echo %YELLOW%Options:%RESET%
echo   --demo              Demo mode (3 updates then exit)
echo   --gui               GUI version (experimental)
echo   --help, -h          Show this help
echo   --version, -v       Version information
echo.
echo %YELLOW%Examples:%RESET%
echo   %0                  Normal mode
echo   %0 --demo          Demo mode
echo   %0 --gui           GUI version
echo.
echo %GREEN%Configuration:%RESET%
echo   Config file: setup\config.json or setup\config.py
exit /b 0

:show_version
echo %CYAN%==================================================================%RESET%
echo %BOLD%  🌡️  WBGT Heat Stroke Warning Kiosk (English Version)%RESET%
echo %CYAN%==================================================================%RESET%
echo %GREEN%Version: 2.0.0%RESET%
echo %CYAN%Language: English%RESET%
exit /b 0