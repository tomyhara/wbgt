@echo off
chcp 65001 > nul
REM WBGT CSV Mode Runner - Windows版
REM WBGT CSV Mode Runner - Windows Version

setlocal EnableDelayedExpansion
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
set "LOG_FILE=%PROJECT_ROOT%\wbgt_csv_runner.log"

REM Initialize variables
set "DOWNLOAD_ONLY=false"
set "RUN_ONLY=false"
set "ENGLISH=false"
set "GUI=false"
set "VERBOSE=false"

goto main

:print_colored
REM Windows環境では色付き表示をシンプルに
echo %~2
exit /b

:show_usage
call :print_colored cyan "=================================================================="
call :print_colored white " 🌡️  WBGT CSV Mode Runner / WBGT CSV モード実行"
call :print_colored cyan " Version 2.0.0 - 2025-07-24"
call :print_colored cyan "=================================================================="
echo.
call :print_colored white "使用方法 / Usage:"
echo   %~nx0 [OPTIONS]
echo.
call :print_colored yellow "オプション / Options:"
echo   -d, --download-only    CSVデータのみダウンロード / Only download CSV data
echo   -r, --run-only         既存CSVデータで実行 / Run with existing CSV data
echo   -e, --english          英語版を実行 / Run English version
echo   -g, --gui              GUI版で実行 / Run in GUI mode
echo   -h, --help             ヘルプ表示 / Show this help
echo   -v, --verbose          詳細ログ / Verbose logging
echo.
call :print_colored yellow "例 / Examples:"
echo   %~nx0                     CSVダウンロード後、日本語版実行
echo   %~nx0 --download-only     CSVデータのみダウンロード
echo   %~nx0 --run-only --english 既存CSVで英語版実行
echo   %~nx0 --english --gui     CSVダウンロード後、英語版GUI実行
echo.
call :print_colored green "データソース / Data Sources:"
echo   • 環境省熱中症予防情報サイト / Ministry of Environment WBGT
echo   • 気象庁API / Japan Meteorological Agency API
echo   設定: setup\config.json
exit /b

:log_message
REM %1=message, %2=level
echo [%date% %time%] %~2: %~1
echo [%date% %time%] %~2: %~1 >> "%LOG_FILE%"
exit /b

:check_python
python --version >nul 2>&1
if !errorlevel! neq 0 (
    call :print_colored red "❌ Pythonが見つかりません / Python not found"
    exit /b 1
)
call :log_message "Python is available" "INFO"
exit /b 0

:setup_virtual_env
if exist "%PROJECT_ROOT%\venv\Scripts\activate.bat" (
    call :print_colored blue "📦 仮想環境をアクティベート中... / Activating virtual environment..."
    call "%PROJECT_ROOT%\venv\Scripts\activate.bat"
    call :log_message "Virtual environment activated" "INFO"
) else (
    call :print_colored yellow "⚠️  仮想環境が見つかりません / Virtual environment not found"
    call :log_message "Using system Python" "WARN"
)
exit /b

:main
REM Parse command line arguments
:parse_args
if "%1"=="" goto end_parse

if /i "%1"=="-d" (
    set "DOWNLOAD_ONLY=true"
    shift
    goto parse_args
) else if /i "%1"=="--download-only" (
    set "DOWNLOAD_ONLY=true"
    shift
    goto parse_args
) else if /i "%1"=="-r" (
    set "RUN_ONLY=true"
    shift
    goto parse_args
) else if /i "%1"=="--run-only" (
    set "RUN_ONLY=true"
    shift
    goto parse_args
) else if /i "%1"=="-e" (
    set "ENGLISH=true"
    shift
    goto parse_args
) else if /i "%1"=="--english" (
    set "ENGLISH=true"
    shift
    goto parse_args
) else if /i "%1"=="-g" (
    set "GUI=true"
    shift
    goto parse_args
) else if /i "%1"=="--gui" (
    set "GUI=true"
    shift
    goto parse_args
) else if /i "%1"=="-v" (
    set "VERBOSE=true"
    shift
    goto parse_args
) else if /i "%1"=="--verbose" (
    set "VERBOSE=true"
    shift
    goto parse_args
) else if /i "%1"=="-h" (
    call :show_usage
    exit /b 0
) else if /i "%1"=="--help" (
    call :show_usage
    exit /b 0
) else (
    call :print_colored red "❌ 不明なオプション / Unknown option: %1"
    call :show_usage
    exit /b 1
)

:end_parse
REM Start logging
call :log_message "WBGT CSV Runner Started" "INFO"

REM Check Python environment
call :check_python
if !errorlevel! neq 0 exit /b 1

REM Setup virtual environment
call :setup_virtual_env

REM Download CSV data if not run-only mode
if "%RUN_ONLY%"=="false" (
    call :log_message "Starting CSV data download..." "INFO"
    call :print_colored cyan "📡 CSVデータをダウンロード中... / Downloading CSV data..."
    
    call "%SCRIPT_DIR%download_all_data.sh"
    if !errorlevel! equ 0 (
        call :log_message "CSV data download completed successfully" "SUCCESS"
        call :print_colored green "✅ CSVデータのダウンロードが完了しました / CSV data download completed"
    ) else (
        call :log_message "CSV data download failed, but will try to use existing data" "WARN"
        call :print_colored yellow "⚠️  ダウンロードに失敗しましたが、既存データで続行します / Download failed, continuing with existing data"
    )
) else (
    call :log_message "Skipping download, using existing CSV data" "INFO"
)

REM Stop here if download-only mode
if "%DOWNLOAD_ONLY%"=="true" (
    call :log_message "Download-only mode: Stopping here" "INFO"
    call :print_colored green "✅ ダウンロードが完了しました / Download completed"
    exit /b 0
)

REM Check if CSV data exists
set "CSV_DIR=%PROJECT_ROOT%\data\csv"
if not exist "%CSV_DIR%" (
    call :log_message "No CSV data found in %CSV_DIR%" "ERROR"
    call :print_colored red "❌ CSVデータが見つかりません / No CSV data found: %CSV_DIR%"
    call :print_colored yellow "   --download-onlyを使用してデータをダウンロードしてください / Please run with --download-only first"
    exit /b 1
)

REM Set environment variable to force CSV usage
set "FORCE_CSV_MODE=1"

REM Determine which application to run
if "%ENGLISH%"=="true" (
    set "APP_PATH=%PROJECT_ROOT%\src\wbgt_kiosk_en.py"
    call :log_message "Starting English version with CSV data..." "INFO"
) else (
    set "APP_PATH=%PROJECT_ROOT%\src\wbgt_kiosk.py"
    call :log_message "Starting Japanese version with CSV data..." "INFO"
)

REM Check if application exists
if not exist "%APP_PATH%" (
    call :log_message "Application not found: %APP_PATH%" "ERROR"
    call :print_colored red "❌ アプリケーションが見つかりません / Application not found: %APP_PATH%"
    exit /b 1
)

REM Prepare application arguments
set "APP_ARGS="
if "%GUI%"=="true" (
    set "APP_ARGS=--gui"
)

REM Run the application
call :log_message "Running WBGT system with CSV data..." "INFO"
if "%VERBOSE%"=="true" (
    python "%APP_PATH%" %APP_ARGS%
    set "app_exit_code=!errorlevel!"
) else (
    python "%APP_PATH%" %APP_ARGS% >> "%LOG_FILE%" 2>&1
    set "app_exit_code=!errorlevel!"
)

REM Report completion
if !app_exit_code! equ 0 (
    call :log_message "WBGT CSV Runner completed successfully" "SUCCESS"
    call :print_colored green "✅ CSVモード実行が正常に完了しました / CSV mode execution completed successfully"
) else (
    call :log_message "WBGT CSV Runner completed with errors (exit code: !app_exit_code!)" "ERROR"
    call :print_colored red "❌ CSVモード実行でエラーが発生しました / CSV mode execution failed"
)

exit /b !app_exit_code!