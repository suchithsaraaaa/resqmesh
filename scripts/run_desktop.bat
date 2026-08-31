@echo off
echo ========================================================
echo Starting ResQMesh AI Desktop Command Center (Electron)
echo ========================================================

cd /d "%~dp0\..\desktop"
npm run electron-dev
pause
