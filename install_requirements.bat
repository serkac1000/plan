@echo off
title Installing Requirements for Proteus Connection Editor
color 0B

echo ========================================
echo  Installing Requirements
echo ========================================
echo.

echo Checking Python installation...
python --version
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.7+ from https://python.org
    pause
    exit /b 1
)

echo.
echo Installing required packages...
echo.

echo Installing Flask...
pip install flask
if errorlevel 1 (
    echo Warning: Flask installation failed
)

echo Installing Werkzeug...
pip install werkzeug
if errorlevel 1 (
    echo Warning: Werkzeug installation failed
)

echo.
echo Creating project directories...
if not exist "uploads" (
    mkdir uploads
    echo Created uploads directory
)

if not exist "templates" (
    mkdir templates
    echo Created templates directory
)

echo.
echo ========================================
echo  Installation Complete!
echo ========================================
echo.
echo You can now run the server using:
echo   start1.bat
echo.
echo Or run directly with:
echo   python app.py
echo.
pause