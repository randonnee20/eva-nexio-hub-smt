@echo off
:: ========================================
:: SMT AI Factory - Frontend Server
:: ========================================

:: 한글 깨짐 방지
chcp 65001 > nul
cls

echo ========================================
echo          SMT AX Factory - Frontend Server
echo ========================================
echo.

:: 현재 배치파일 위치로 이동
cd /d %~dp0

:: 의존성 설치 확인
echo [1/2] 의존성 설치 확인...
if not exist node_modules (
    echo node_modules 폴더가 없어 의존성을 설치합니다...
    call npm install
    echo 설치 완료!
) else (
    echo node_modules 존재, 설치 생략
)

:: 개발 서버 실행
echo.
echo [2/2] 개발 서버 시작...
echo ========================================
echo 프론트엔드 서버:  http://localhost:3000
echo ========================================
echo.

call npm run dev

:: 종료 후 화면 유지
pause
