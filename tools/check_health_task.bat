@echo off
REM HXO task health check runner (called by Windows Task Scheduler HXO_TaskHealthCheck).
REM Runs tools/check_tasks_health.py from the repo root; appends output to logs\task_health_run.log.
setlocal
set "REPO=%~dp0.."
set "PY=C:\Users\Administrator\AppData\Local\Python\pythoncore-3.14-64\python.exe"
if not exist "%REPO%\logs" mkdir "%REPO%\logs"
cd /d "%REPO%"
"%PY%" tools\check_tasks_health.py --json >> "%REPO%\logs\task_health_run.log" 2>&1
exit /b %ERRORLEVEL%
