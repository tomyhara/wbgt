@echo off
chcp 65001 > nul

echo 🌡️  WBGT熱中症警戒キオスク セットアップ  🌡️
echo ==============================================

setlocal EnableDelayedExpansion
set "SCRIPT_DIR=%~dp0"

REM 色付き出力のための関数は echo に置き換え（Windowsバッチファイル制限）
goto main

:print_success
echo ✅ %~1
exit /b

:print_info
echo ℹ️  %~1
exit /b

:print_warning
echo ⚠️  %~1
exit /b

:print_error
echo ❌ %~1
exit /b

:main
REM Pythonバージョンチェック
call :print_info "Pythonバージョンを確認中..."
python --version > nul 2>&1
if %errorlevel% neq 0 (
    call :print_error "Pythonが見つかりません。Pythonをインストールしてください。"
    echo Python公式サイト: https://www.python.org/downloads/
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('python --version 2^>^&1') do set python_version=%%i
    call :print_success "Python確認: !python_version!"
)

REM 依存関係のインストール
call :print_info "Pythonの依存関係をインストール中..."
pip install -r "%SCRIPT_DIR%requirements.txt"
if %errorlevel% neq 0 (
    call :print_warning "依存関係のインストールで問題が発生しました"
) else (
    call :print_success "依存関係のインストール完了"
)

REM 設定ファイルの作成
call :print_info "設定ファイルを確認中..."
if not exist "%SCRIPT_DIR%config.py" (
    copy "%SCRIPT_DIR%config.sample.py" "%SCRIPT_DIR%config.py"
    call :print_success "config.py を作成しました"
    call :print_info "デフォルト設定（東京）で動作します"
) else (
    call :print_info "config.py は既に存在します"
)

REM 動作テスト
call :print_info "動作テストを実行中..."
python "%SCRIPT_DIR%wbgt_kiosk.py" --demo > nul 2>&1
if %errorlevel% neq 0 (
    call :print_warning "動作テストで問題が発生しましたが、継続します"
) else (
    call :print_success "動作テスト成功"
)

echo.
echo ==============================================
call :print_success "🎉 セットアップ完了！"
echo.
echo 📱 使用方法：
echo   デモモード:     python wbgt_kiosk.py --demo
echo   通常モード:     python wbgt_kiosk.py
echo   GUI版（実験的）: python wbgt_kiosk.py --gui
echo.
echo 🗾 地域設定：
echo   地域を変更する場合は config.py を編集してください
echo   例：notepad config.py
echo.
echo 🔧 自動起動設定：
echo   Windowsサービス使用（推奨）:
echo     autostart.bat を参照してください
echo.
echo   タスクスケジューラ使用:
echo     タスクスケジューラで起動時実行を設定してください
echo     プログラム: %SCRIPT_DIR%autostart.bat
echo.
call :print_info "まずはデモモードで動作確認してみてください："
echo python wbgt_kiosk.py --demo
echo ==============================================
pause