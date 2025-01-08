@echo off
SETLOCAL

:: Set working directories
SET BACKEND_DIR=src
SET FRONTEND_DIR=frontend

:: Check if directories exist
IF NOT EXIST %BACKEND_DIR% (
    echo Backend directory not found!
    exit /b 1
)

IF NOT EXIST %FRONTEND_DIR% (
    echo Frontend directory not found!
    exit /b 1
)

:: Run frontend and backend concurrently in foreground
echo Starting services...
cmd /k "cd %FRONTEND_DIR% && start npm run start && cd .. && python src\app.py"

:: Clean up processes on exit
taskkill /F /IM python.exe /IM node.exe
exit /b 0