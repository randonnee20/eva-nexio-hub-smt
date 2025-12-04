@echo off
chcp 65001 > nul
echo ========================================
echo SMT AI Factory - 실행 파일 빌드
echo ========================================
echo.

cd /d %~dp0

echo [1/5] 환경 확인...
call conda activate tf210
if %ERRORLEVEL% NEQ 0 (
    echo ❌ tf210 환경을 찾을 수 없습니다.
    pause
    exit
)

echo [2/5] PyInstaller 설치...
pip install pyinstaller

echo.
echo [3/5] 백엔드 실행 파일 생성 중...
cd backend

pyinstaller --name=SMT_Backend ^
    --onefile ^
    --add-data="app;app" ^
    --hidden-import=fastapi ^
    --hidden-import=uvicorn ^
    --hidden-import=sqlalchemy ^
    --hidden-import=pandas ^
    --hidden-import=numpy ^
    --hidden-import=sklearn ^
    --hidden-import=joblib ^
    --hidden-import=pydantic ^
    --hidden-import=httpx ^
    --hidden-import=chromadb ^
    --hidden-import=sentence_transformers ^
    --hidden-import=uvicorn.logging ^
    --hidden-import=uvicorn.loops ^
    --hidden-import=uvicorn.loops.auto ^
    --hidden-import=uvicorn.protocols ^
    --hidden-import=uvicorn.protocols.http ^
    --hidden-import=uvicorn.protocols.http.auto ^
    --hidden-import=uvicorn.protocols.websockets ^
    --hidden-import=uvicorn.protocols.websockets.auto ^
    --hidden-import=uvicorn.lifespan ^
    --hidden-import=uvicorn.lifespan.on ^
    --collect-all=chromadb ^
    --collect-all=sentence_transformers ^
    app/main.py

echo.
echo [4/5] 프론트엔드 빌드...
cd ..\frontend
call npm install
call npm run build

echo.
echo [5/5] 배포 패키지 생성...
cd ..
mkdir deploy 2>nul
mkdir deploy\backend 2>nul
mkdir deploy\frontend 2>nul
mkdir deploy\data 2>nul
mkdir deploy\models 2>nul
mkdir deploy\rag_documents 2>nul

REM 백엔드 실행 파일 복사
copy backend\dist\SMT_Backend.exe deploy\backend\

REM 프론트엔드 빌드 파일 복사
xcopy /E /I /Y frontend\dist deploy\frontend\dist

REM 실행 스크립트 생성
echo @echo off > deploy\start.bat
echo title SMT AI Factory >> deploy\start.bat
echo. >> deploy\start.bat
echo echo SMT AI Factory 시작 중... >> deploy\start.bat
echo. >> deploy\start.bat
echo start "Backend" cmd /k "cd backend && SMT_Backend.exe" >> deploy\start.bat
echo timeout /t 10 >> deploy\start.bat
echo start "Frontend" cmd /k "cd frontend\dist && python -m http.server 3000" >> deploy\start.bat
echo timeout /t 5 >> deploy\start.bat
echo start http://localhost:3000 >> deploy\start.bat
echo. >> deploy\start.bat
echo pause >> deploy\start.bat

REM README 생성
echo SMT AI Factory - 배포 패키지 > deploy\README.txt
echo. >> deploy\README.txt
echo 실행 방법: >> deploy\README.txt
echo 1. start.bat 실행 >> deploy\README.txt
echo 2. 브라우저 자동 실행 (또는 http://localhost:3000 접속) >> deploy\README.txt
echo. >> deploy\README.txt
echo 필수 요구사항: >> deploy\README.txt
echo - Ollama 설치 및 모델 다운로드 >> deploy\README.txt
echo - Python 3.10+ 설치 (프론트엔드 서버용) >> deploy\README.txt
echo. >> deploy\README.txt

echo.
echo ========================================
echo ✅ 빌드 완료!
echo ========================================
echo.
echo 배포 파일 위치: deploy 폴더
echo.
echo 배포 패키지 내용:
echo - backend\SMT_Backend.exe (백엔드 실행 파일)
echo - frontend\dist\ (프론트엔드 파일)
echo - data\ (데이터 폴더)
echo - models\ (AI 모델 폴더)
echo - rag_documents\ (문서 폴더)
echo - start.bat (실행 스크립트)
echo - README.txt (사용 설명서)
echo.
echo 고객 배포 시:
echo 1. deploy 폴더 전체를 ZIP으로 압축
echo 2. 고객에게 전달
echo 3. Ollama 설치 가이드 제공
echo.
pause