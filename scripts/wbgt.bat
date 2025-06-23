@echo off
chcp 65001 > nul
REM WBGT熱中症警戒キオスク 統合ランチャー (Windows)
REM WBGT Heat Stroke Warning Kiosk Unified Launcher (Windows)

setlocal EnableDelayedExpansion
set "SCRIPT_DIR=%~dp0"
set "LANGUAGE="
set "OPTIONS="

goto main

:print_colored
REM Windows環境では色付き表示をシンプルに
echo %~2
exit /b

:show_help
call :print_colored cyan "🌡️  WBGT熱中症警戒キオスク 統合ランチャー"
call :print_colored cyan "🌡️  WBGT Heat Stroke Warning Kiosk Unified Launcher"
echo ============================================================
echo.
echo 使用方法 / Usage:
echo   %~nx0 [言語/language] [オプション/options]
echo.
echo 言語選択 / Language Selection:
echo   ja, jp, japanese    日本語版を起動 / Launch Japanese version
echo   en, english         英語版を起動 / Launch English version
echo   auto                システム言語を自動検出 / Auto-detect system language
echo.
echo オプション / Options:
echo   --demo              デモモード / Demo mode
echo   --gui               GUI版 / GUI version
echo   --help, -h          このヘルプを表示 / Show this help
echo.
echo 例 / Examples:
echo   %~nx0 ja --demo     日本語版デモモード / Japanese demo mode
echo   %~nx0 en --gui      英語版GUI / English GUI version
echo   %~nx0 auto          自動言語検出 / Auto language detection
echo.
echo 仮想環境使用時 / With Virtual Environment:
echo   事前にsetup_venv.batを実行してください
echo   Run setup_venv.bat first if using virtual environment
echo ============================================================
exit /b

:detect_language
REM システム言語検出（Windows）
for /f "tokens=*" %%i in ('echo %LANG%') do set "DETECTED_LANG=%%i"

REM LANGが設定されていない場合はWindowsのロケールを確認
if "%DETECTED_LANG%"=="" (
    for /f "tokens=1 delims=;" %%i in ('wmic os get locale /value ^| find "Locale="') do (
        set "LOCALE_LINE=%%i"
        for /f "tokens=2 delims==" %%j in ("!LOCALE_LINE!") do set "DETECTED_LANG=%%j"
    )
)

REM 日本語ロケールの場合
if "%DETECTED_LANG:~0,2%"=="ja" (
    set "AUTO_LANGUAGE=ja"
) else if "%DETECTED_LANG%"=="0411" (
    REM Windows日本語ロケールコード
    set "AUTO_LANGUAGE=ja"
) else (
    REM デフォルトは英語
    set "AUTO_LANGUAGE=en"
)
exit /b

:setup_virtual_env
if exist "%SCRIPT_DIR%..\venv\Scripts\activate.bat" (
    call :print_colored blue "📦 仮想環境をアクティベート中... / Activating virtual environment..."
    call "%SCRIPT_DIR%..\venv\Scripts\activate.bat"
    set "VENV_ACTIVE=1"
) else (
    call :print_colored yellow "⚠️  仮想環境が見つかりません / Virtual environment not found"
    call :print_colored yellow "   システムのPythonを使用します / Using system Python"
    set "VENV_ACTIVE=0"
)
exit /b

:main
REM 引数解析
:parse_args
if "%1"=="" goto end_parse

if /i "%1"=="ja" (
    set "LANGUAGE=ja"
    shift
    goto parse_args
) else if /i "%1"=="jp" (
    set "LANGUAGE=ja"
    shift
    goto parse_args
) else if /i "%1"=="japanese" (
    set "LANGUAGE=ja"
    shift
    goto parse_args
) else if /i "%1"=="en" (
    set "LANGUAGE=en"
    shift
    goto parse_args
) else if /i "%1"=="english" (
    set "LANGUAGE=en"
    shift
    goto parse_args
) else if /i "%1"=="auto" (
    set "LANGUAGE=auto"
    shift
    goto parse_args
) else if /i "%1"=="--help" (
    call :show_help
    exit /b 0
) else if /i "%1"=="-h" (
    call :show_help
    exit /b 0
) else if /i "%1"=="--demo" (
    set "OPTIONS=!OPTIONS! %1"
    shift
    goto parse_args
) else if /i "%1"=="--gui" (
    set "OPTIONS=!OPTIONS! %1"
    shift
    goto parse_args
) else (
    REM 最初の未知の引数を言語として扱う
    if "%LANGUAGE%"=="" (
        echo %1 | findstr /i "ja jp" >nul
        if !errorlevel! equ 0 (
            set "LANGUAGE=ja"
        ) else (
            echo %1 | findstr /i "en" >nul
            if !errorlevel! equ 0 (
                set "LANGUAGE=en"
            ) else (
                call :print_colored red "❌ 不明なオプション / Unknown option: %1"
                call :show_help
                exit /b 1
            )
        )
    ) else (
        call :print_colored red "❌ 不明なオプション / Unknown option: %1"
        call :show_help
        exit /b 1
    )
    shift
    goto parse_args
)

:end_parse
REM 言語が指定されていない場合は自動検出
if "%LANGUAGE%"=="" set "LANGUAGE=auto"

REM auto の場合は実際の言語を検出
if "%LANGUAGE%"=="auto" (
    call :detect_language
    set "LANGUAGE=!AUTO_LANGUAGE!"
    call :print_colored cyan "🔍 システム言語を検出 / Detected system language: !LANGUAGE!"
)

REM 仮想環境のセットアップ
call :setup_virtual_env

REM 言語に応じたアプリケーションを起動
if "%LANGUAGE%"=="ja" (
    call :print_colored green "🇯🇵 日本語版を起動 / Starting Japanese version..."
    if exist "%SCRIPT_DIR%..\src\wbgt_kiosk.py" (
        python "%SCRIPT_DIR%..\src\wbgt_kiosk.py" %OPTIONS%
    ) else (
        call :print_colored red "❌ 日本語版が見つかりません / Japanese version not found: src/wbgt_kiosk.py"
        exit /b 1
    )
) else if "%LANGUAGE%"=="en" (
    call :print_colored green "🇺🇸 英語版を起動 / Starting English version..."
    if exist "%SCRIPT_DIR%..\src\wbgt_kiosk_en.py" (
        python "%SCRIPT_DIR%..\src\wbgt_kiosk_en.py" %OPTIONS%
    ) else (
        call :print_colored red "❌ 英語版が見つかりません / English version not found: src/wbgt_kiosk_en.py"
        exit /b 1
    )
) else (
    call :print_colored red "❌ サポートされていない言語 / Unsupported language: %LANGUAGE%"
    call :show_help
    exit /b 1
)