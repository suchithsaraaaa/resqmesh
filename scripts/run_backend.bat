@echo off
echo ========================================================
echo Starting ResQMesh AI Local Backend Service (FastAPI)
echo ========================================================

cd /d "%~dp0\..\backend"
call .\venv\Scripts\activate 2>nul
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause
