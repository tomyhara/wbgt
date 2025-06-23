@echo off
REM WBGT キオスク実行スクリプト（仮想環境用）Windows版

setlocal
set "SCRIPT_DIR=%~dp0"

REM 仮想環境をアクティベート
call "%SCRIPT_DIR%..\venv\Scripts\activate.bat"

REM アプリケーションを実行
python "%SCRIPT_DIR%..\src\wbgt_kiosk.py" %*