@echo off
REM HXO dashboard auto-refresh runner (called by Windows Task Scheduler HXO_Dashboard_Refresh).
REM Runs tools/update_dashboard.py from the repo root; appends output to logs\dashboard_run.log.
setlocal
set "REPO=%~dp0.."
set "PY=C:\Users\Administrator\AppData\Local\Python\pythoncore-3.14-64\python.exe"
if not exist "%REPO%\logs" mkdir "%REPO%\logs"
cd /d "%REPO%"
"%PY%" tools\update_dashboard.py >> "%REPO%\logs\dashboard_run.log" 2>&1
exit /b %ERRORLEVEL%
