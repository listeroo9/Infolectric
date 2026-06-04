@echo off
REM Setup script for Infolectric on Windows
REM This script sets up the project from scratch

echo ========================================
echo Infolectric Setup Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo [1/5] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo Error: Failed to create virtual environment
    pause
    exit /b 1
)

echo [2/5] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo Error: Failed to activate virtual environment
    pause
    exit /b 1
)

echo [3/5] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)

echo [4/5] Setting up database...
python manage.py migrate
if errorlevel 1 (
    echo Error: Failed to run migrations
    pause
    exit /b 1
)

echo [5/5] Loading sample data...
python manage.py seed_data
if errorlevel 1 (
    echo Error: Failed to load sample data
    pause
    exit /b 1
)

echo.
echo ========================================
echo Setup completed successfully!
echo ========================================
echo.
echo Next steps:
echo 1. Create a superuser:
echo    python manage.py createsuperuser
echo.
echo 2. Run the development server:
echo    python manage.py runserver
echo.
echo 3. Access the application:
echo    http://127.0.0.1:8000/
echo.
echo 4. Access the admin panel:
echo    http://127.0.0.1:8000/admin/
echo.
pause
