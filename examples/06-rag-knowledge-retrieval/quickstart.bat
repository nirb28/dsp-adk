@echo off
REM Quick start script for RAG Knowledge Retrieval example

echo ========================================
echo RAG Knowledge Retrieval - Quick Start
echo ========================================
echo.

REM Check for API key
if "%NVAPI_KEY%"=="" (
    if "%OPENAI_API_KEY%"=="" (
        echo WARNING: No API key found!
        echo Please set NVAPI_KEY or OPENAI_API_KEY environment variable
        echo.
        pause
        exit /b 1
    )
)

REM Set RAG endpoint if not already set
if "%RAG_ENDPOINT%"=="" (
    set RAG_ENDPOINT=http://localhost:8000
)

echo RAG Endpoint: %RAG_ENDPOINT%
echo.
echo NOTE: Make sure dsp-rag service is running at %RAG_ENDPOINT%
echo   cd dsp_ai_rag2
echo   python app/main.py
echo.
pause

echo Starting Knowledge Assistant Agent...
echo.
python run.py --mode interactive

pause
