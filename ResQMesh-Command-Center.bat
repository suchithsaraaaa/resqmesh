@echo off
title ResQMesh AI - Offline Emergency Response Command Center
color 0B

echo ======================================================================
echo           [*] ResQMesh AI: Emergency Response Command Center
echo ======================================================================
echo Operational Mode: Fully Offline (P2P Mesh Network Enabled)
echo.

:: 1. Start Standalone Backend Binary if present
if exist "%~dp0backend\dist\resqmesh-server\resqmesh-server.exe" (
    echo [+] Starting Standalone Backend Engine (resqmesh-server.exe)...
    start "ResQMesh Backend Service" /min "%~dp0backend\dist\resqmesh-server\resqmesh-server.exe"
) else if exist "%~dp0server\resqmesh-server.exe" (
    echo [+] Starting Standalone Backend Engine (resqmesh-server.exe)...
    start "ResQMesh Backend Service" /min "%~dp0server\resqmesh-server.exe"
) else (
    echo [+] Starting Python Backend Service...
    start "ResQMesh Backend Service" /min python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
)

:: 2. Wait 2 seconds for server boot
timeout /t 2 /nobreak >nul

:: 3. Launch Frontend in Standalone Native App Window Mode (Edge/Chrome App Mode)
echo [+] Launching Command Center Desktop Interface...
where msedge >nul 2>nul
if %ERRORLEVEL% equ 0 (
    start msedge --app=http://localhost:8080 --window-size=1440,900
) else (
    where chrome >nul 2>nul
    if %ERRORLEVEL% equ 0 (
        start chrome --app=http://localhost:8080 --window-size=1440,900
    ) else (
        start http://localhost:8080
    )
)

echo.
echo ======================================================================
echo   [SUCCESS] ResQMesh AI is running!
echo   - Command Center UI:  http://localhost:8080
echo   - Local REST API:     http://localhost:8000
echo   - Swagger API Docs:   http://localhost:8000/docs
echo ======================================================================
echo.
echo Press any key to exit this launcher (services will keep running in background).
pause >nul
