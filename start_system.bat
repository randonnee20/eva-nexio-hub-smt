@echo off
title SMT AI Factory - System Launcher
color 0A

echo.
echo  ╔═══════════════════════════════════════════════╗
echo  ║                                               ║
echo  ║                 NEXIO.HUB                     ║
echo  ║                                               ║
echo  ╚═══════════════════════════════════════════════╝
echo.

cd /d %~dp0

echo  [1/4] Conda 환경 확인...
call conda activate tf210
if %ERRORLEVEL% NEQ 0 (
    echo  ❌ tf210 환경을 찾을 수 없습니다.
    pause
    exit
)

echo  [2/4] Ollama 확인...
where ollama >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo  ❌ Ollama가 설치되지 않았습니다.
    pause
    exit
)
echo  ✅ Ollama 확인 완료

echo  [3/4] 백엔드 서버 시작...
start "SMT Backend" cmd /k "conda activate tf210 && cd /d %~dp0\backend\app && python -m uvicorn main:app --host 0.0.0.0 --port 8000"

echo  백엔드 로딩 중... (10초 대기)
timeout /t 10 >nul

echo  [4/4] 프론트엔드 서버 시작...
start "SMT Frontend" cmd /k "cd /d %~dp0\frontend && npm run dev"

echo  프론트엔드 로딩 중... (10초 대기)
timeout /t 10 >nul

echo.
echo  ╔═══════════════════════════════════════════════╗
echo  ║                                               ║
echo  ║            🚀 시스템 시작 완료!                 ║
echo  ║                                               ║
echo  ║   브라우저를 자동으로 엽니다...                 ║
echo  ║                                               ║
echo  ╚═══════════════════════════════════════════════╝
echo.

REM 브라우저 자동 열기
start http://localhost:3000

echo  브라우저가 자동으로 열립니다.
echo  열리지 않으면 수동으로 http://localhost:3000 접속하세요.
echo.
echo  종료하려면 이 창을 닫으세요.
echo.
pause