@echo off
chcp 65001 >nul
cd /d "%~dp0"
call "%CD%\venv\Scripts\activate.bat"
python search_service.py
pause
