@echo off
title ResQMesh AI - Package Standalone Windows Distribution
color 0A

echo ======================================================================
echo           [*] ResQMesh AI: Packaging Windows x64 Standalone Release
echo ======================================================================
echo.

set RELEASE_DIR=%~dp0..\dist\ResQMesh-AI-Windows-x64
if exist "%RELEASE_DIR%" rmdir /s /q "%RELEASE_DIR%"
mkdir "%RELEASE_DIR%"
mkdir "%RELEASE_DIR%\server"
mkdir "%RELEASE_DIR%\app"

echo [+] Copying Standalone Backend Binary...
xcopy /E /I /Y "%~dp0..\backend\dist\resqmesh-server" "%RELEASE_DIR%\server"

echo [+] Copying Desktop Launcher...
copy /Y "%~dp0..\ResQMesh-Command-Center.bat" "%RELEASE_DIR%\Launch-ResQMesh.bat"

echo [+] Creating README for Offline Field Deployment...
(
echo # ResQMesh AI - Standalone Offline Emergency Command Center
echo.
echo ## Quick Start
echo Double-click `Launch-ResQMesh.bat` to launch the offline command center.
echo Zero installation or internet required.
echo.
echo ## Ports
echo - Dashboard UI: http://localhost:8080
echo - Backend API: http://localhost:8000
) > "%RELEASE_DIR%\README.txt"

echo.
echo ======================================================================
echo   [SUCCESS] Standalone Package Created at:
echo   %RELEASE_DIR%
echo ======================================================================
echo.
pause
