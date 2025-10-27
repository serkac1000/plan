@echo off
title Proteus Connection Editor - Flask Server
color 0A

echo ========================================
echo  Proteus Connection Editor Server
echo ========================================
echo.

echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.7+ and try again
    pause
    exit /b 1
)

echo Checking required packages...
python -c "import flask" 2>nul
if errorlevel 1 (
    echo Flask is not installed. Installing now...
    pip install flask
    if errorlevel 1 (
        echo Error: Failed to install Flask
        pause
        exit /b 1
    )
    echo Flask installed successfully!
)

python -c "import werkzeug" 2>nul
if errorlevel 1 (
    echo Installing Werkzeug for file uploads...
    pip install werkzeug
)

echo.
echo Creating uploads directory...
if not exist "uploads" mkdir uploads

echo.
echo ========================================
echo  Starting Proteus Connection Editor
echo ========================================
echo.
echo Server Features:
echo  - Proteus Project Connection Editor
echo  - Component Analysis and Wiring
echo  - Proteus-Compatible File Generation
echo.
echo Server will be available at:
echo  http://127.0.0.1:5000  (Proteus Connection Editor)
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

python app.py

echo.
echo Server stopped. Press any key to exit...
pause >nul