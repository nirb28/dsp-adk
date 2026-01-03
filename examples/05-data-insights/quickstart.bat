@echo off
REM Quick start script for Data Insights Agent example

echo ========================================
echo Data Insights Agent - Quick Start
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
        pause
        exit /b 1
    )
)

REM Create visualizations directory
if not exist "..\..\data\visualizations" (
    mkdir "..\..\data\visualizations"
)

echo Starting Data Insights Agent...
echo Visualizations will be saved to: data\visualizations\
echo.
python run.py --mode interactive

pause
