@echo off
REM Quick start script for Database Analyst Agent example

echo ========================================
echo Database Analyst Agent - Quick Start
echo ========================================
echo.

REM Check if database exists
if not exist "..\..\data\databases\sample.db" (
    echo Creating sample database...
    python ..\..\scripts\setup_sample_database.py
    if errorlevel 1 (
        echo Failed to create database!
        pause
        exit /b 1
    )
    echo.
)

REM Check for API key
if "%NVAPI_KEY%"=="" (
    if "%OPENAI_API_KEY%"=="" (
        echo WARNING: No API key found!
        echo Please set NVAPI_KEY or OPENAI_API_KEY environment variable
        echo.
        echo Example:
        echo   set NVAPI_KEY=your_api_key_here
        echo.
        pause
        exit /b 1
    )
)

echo Starting Database Analyst Agent...
echo.
python run.py --mode interactive

pause
