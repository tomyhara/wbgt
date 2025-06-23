@echo off
chcp 65001 > nul

echo 🌡️  WBGT熱中症警戒キオスク 仮想環境セットアップ  🌡️
echo ==================================================

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
REM 仮想環境の作成
call :print_info "Python仮想環境を作成中..."
python -m venv "%SCRIPT_DIR%venv"
if %errorlevel% neq 0 (
    call :print_error "仮想環境の作成に失敗しました"
    pause
    exit /b 1
)
call :print_success "仮想環境作成完了"

REM 仮想環境をアクティベート
call :print_info "仮想環境をアクティベート中..."
call "%SCRIPT_DIR%venv\Scripts\activate.bat"

REM pipをアップグレード
call :print_info "pipをアップグレード中..."
python -m pip install --upgrade pip

REM 依存関係のインストール
call :print_info "依存関係をインストール中..."
pip install -r "%SCRIPT_DIR%requirements.txt"
if %errorlevel% neq 0 (
    call :print_error "依存関係のインストールに失敗しました"
    pause
    exit /b 1
)
call :print_success "依存関係のインストール完了"

REM 設定ファイルの作成
call :print_info "設定ファイルを確認中..."
if not exist "%SCRIPT_DIR%config.py" (
    copy "%SCRIPT_DIR%config.sample.py" "%SCRIPT_DIR%config.py"
    call :print_success "config.py を作成しました"
    call :print_info "デフォルト設定（東京）で動作します"
) else (
    call :print_info "config.py は既に存在します"
)

REM 実行スクリプトの作成
call :print_info "実行スクリプトを作成中..."
(
echo @echo off
echo REM WBGT キオスク実行スクリプト（仮想環境用）Windows版
echo.
echo setlocal
echo set "SCRIPT_DIR=%%~dp0"
echo.
echo REM 仮想環境をアクティベート
echo call "%%SCRIPT_DIR%%venv\Scripts\activate.bat"
echo.
echo REM アプリケーションを実行
echo python "%%SCRIPT_DIR%%wbgt_kiosk.py" %%*
) > "%SCRIPT_DIR%run_wbgt.bat"

call :print_success "実行スクリプト作成完了"

REM 動作テスト
call :print_info "動作テストを実行中..."
python "%SCRIPT_DIR%wbgt_kiosk.py" --demo > nul 2>&1
if %errorlevel% neq 0 (
    call :print_warning "動作テストで問題が発生しましたが、継続します"
) else (
    call :print_success "動作テスト成功"
)

echo.
echo ==================================================
call :print_success "🎉 仮想環境セットアップ完了！"
echo.
echo 📱 使用方法：
echo   デモモード:     run_wbgt.bat --demo
echo   通常モード:     run_wbgt.bat
echo   GUI版（実験的）: run_wbgt.bat --gui
echo.
echo 🔧 手動実行の場合：
echo   venv\Scripts\activate.bat
echo   python wbgt_kiosk.py --demo
echo.
echo 🗾 地域設定：
echo   地域を変更する場合は config.py を編集してください
echo.
call :print_info "まずはデモモードで動作確認してみてください："
echo run_wbgt.bat --demo
echo ==================================================
pause