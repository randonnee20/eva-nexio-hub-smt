@echo off
chcp 65001 > nul
echo ========================================
echo SMT AI Factory - Backend Server
echo ========================================
echo.

cd /d %~dp0

echo [1/1] tf210 환경 활성화...
call conda activate tf210

echo.
echo ========================================
echo 서버 시작 중...
echo API 문서: http://localhost:8000/docs
echo ========================================
echo.

cd app
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

pause