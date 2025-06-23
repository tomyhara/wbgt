@echo off
chcp 65001 > nul
REM WBGT熱中症警戒キオスク 自動起動スクリプト Windows版

setlocal
set "SCRIPT_DIR=%~dp0"
set "LOG_FILE=%SCRIPT_DIR%autostart.log"

REM ログファイルに開始メッセージ
echo %date% %time%: 🌡️ WBGT熱中症警戒キオスク 自動起動開始 >> "%LOG_FILE%"

REM 作業ディレクトリに移動
cd /d "%SCRIPT_DIR%"

REM 設定ファイルの存在確認
if not exist "..\setup\config.py" (
    echo %date% %time%: ❌ エラー - config.py が見つかりません >> "%LOG_FILE%"
    echo %date% %time%: setup\config.sample.py をコピーして setup\config.py を作成してください >> "%LOG_FILE%"
    exit /b 1
)

REM ネットワーク接続待機
echo %date% %time%: 🌐 ネットワーク接続を待機中... >> "%LOG_FILE%"
timeout /t 15 /nobreak > nul

REM Python環境の確認
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo %date% %time%: ❌ Pythonが見つかりません >> "%LOG_FILE%"
    exit /b 1
)

REM 依存関係の確認
python -c "import requests" > nul 2>&1
if %errorlevel% neq 0 (
    echo %date% %time%: ⚠️ 依存関係をインストール中... >> "%LOG_FILE%"
    pip install -r "..\setup\requirements.txt" >> "%LOG_FILE%" 2>&1
)

REM アプリケーション開始
echo %date% %time%: 🚀 WBGTキオスクアプリケーション開始 >> "%LOG_FILE%"

REM 通常モードで起動（GUI版を使いたい場合は --gui を追加）
python "..\src\wbgt_kiosk.py" >> "%LOG_FILE%" 2>&1

REM 終了ログ
echo %date% %time%: 🛑 WBGTキオスクアプリケーション終了 >> "%LOG_FILE%"