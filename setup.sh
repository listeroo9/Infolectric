#!/bin/bash

# Setup script for Infolectric on macOS/Linux

echo "========================================"
echo "Infolectric Setup Script"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH"
    exit 1
fi

echo "[1/5] Creating virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "Error: Failed to create virtual environment"
    exit 1
fi

echo "[2/5] Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "Error: Failed to activate virtual environment"
    exit 1
fi

echo "[3/5] Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies"
    exit 1
fi

echo "[4/5] Setting up database..."
python manage.py migrate
if [ $? -ne 0 ]; then
    echo "Error: Failed to run migrations"
    exit 1
fi

echo "[5/5] Loading sample data..."
python manage.py seed_data
if [ $? -ne 0 ]; then
    echo "Error: Failed to load sample data"
    exit 1
fi

echo ""
echo "========================================"
echo "Setup completed successfully!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Create a superuser:"
echo "   python manage.py createsuperuser"
echo ""
echo "3. Run the development server:"
echo "   python manage.py runserver"
echo ""
echo "4. Access the application:"
echo "   http://127.0.0.1:8000/"
echo ""
echo "5. Access the admin panel:"
echo "   http://127.0.0.1:8000/admin/"
echo ""
