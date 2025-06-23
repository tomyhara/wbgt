@echo off
REM WBGT Heat Stroke Warning Kiosk Execution Script (English Version) - Virtual Environment Windows

setlocal
set "SCRIPT_DIR=%~dp0"

REM Activate virtual environment
call "%SCRIPT_DIR%..\venv\Scripts\activate.bat"

REM Run application
python "%SCRIPT_DIR%..\src\wbgt_kiosk_en.py" %*