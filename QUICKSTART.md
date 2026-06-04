# Infolectric - Quick Start Guide

Welcome to Infolectric! This guide will help you get started with the project in just a few minutes.

## What is Infolectric?

Infolectric is a comprehensive Django web application for:
- ⚡ Electrical component education and reference
- 📊 Wire size calculations and recommendations
- 🔧 Electrical data management
- 🌐 RESTful API for programmatic access

## System Requirements

- Python 3.8 or higher
- pip package manager
- 100 MB free disk space

## Installation (5 minutes)

### Option 1: Automated Setup (Recommended)

**Windows:**
```bash
cd infolectric
setup_windows.bat
```

**macOS/Linux:**
```bash
cd infolectric
chmod +x setup.sh
./setup.sh
```

### Option 2: Manual Setup

```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up database
python manage.py migrate

# 5. Load sample data
python manage.py seed_data

# 6. Create admin account
python manage.py createsuperuser

# 7. Run server
python manage.py runserver
```

## First Steps

### 1. Access the Application
- **Website:** http://127.0.0.1:8000/
- **Admin Panel:** http://127.0.0.1:8000/admin/

### 2. Login to Admin
- Username: whatever you created in setup
- Password: whatever you created in setup

### 3. Explore Features

#### Components
- Browse electrical components
- View detailed specifications
- Search and filter by category

#### Wire Calculator
- Enter required current (amps)
- Get wire size recommendations
- View ampacity ratings

#### Wire Reference
- Complete wire size database
- Ampacity specifications
- Application guidelines

## Main Features

### 📚 Component Library
Browse and search 10+ electrical component categories including:
- Resistors
- Capacitors
- Diodes
- Transistors
- Transformers
- And more!

### 🧮 Wire Calculator
Get instant wire recommendations:
1. Enter required current (amps)
2. Click "Calculate"
3. View all suitable wire sizes
4. See applications and safety ratings

### 🔌 Admin Management
Manage all data through the admin interface:
- Add/edit/delete components
- Manage categories
- Configure wire sizes
- View statistics

### 📡 RESTful API
Access data programmatically:

```bash
# Get all components
curl http://localhost:8000/api/components/

# Search components
curl http://localhost:8000/api/components/?search=resistor

# Get wire recommendations
curl -X POST http://localhost:8000/api/wire-recommendation/recommend/ \
  -H "Content-Type: application/json" \
  -d '{"required_current": 15.5}'
```

## Project Structure

```
infolectric/
├── core/                    # Main app
│   ├── models.py           # Database models
│   ├── views.py            # Web views
│   ├── api_views.py        # API endpoints
│   ├── forms.py            # Form classes
│   ├── templates/          # HTML templates
│   ├── management/
│   │   └── commands/
│   │       └── seed_data.py # Data seeding
│   └── migrations/         # Database changes
├── infolectric/            # Project settings
│   ├── settings.py         # Configuration
│   ├── urls.py             # URL routing
│   └── wsgi.py             # Production server
├── README.md               # Full documentation
├── API_DOCUMENTATION.md    # API reference
└── manage.py              # Django CLI
```

## Common Commands

```bash
# Run development server
python manage.py runserver

# Create admin account
python manage.py createsuperuser

# Load sample data
python manage.py seed_data

# Access interactive shell
python manage.py shell

# Check for issues
python manage.py check

# Create database backups
python manage.py dumpdata > backup.json

# Restore from backup
python manage.py loaddata backup.json

# Run tests
python manage.py test
```

## Making Changes

### Add a New Component

1. Go to http://127.0.0.1:8000/admin/
2. Click "Components"
3. Click "Add Component"
4. Fill in the form
5. Click "Save"

### Modify Wire Sizes

1. Go to http://127.0.0.1:8000/admin/
2. Click "Wire Sizes"
3. Select the wire size to edit
4. Make changes
5. Click "Save"

### Create New Categories

1. Go to http://127.0.0.1:8000/admin/
2. Click "Categories"
3. Click "Add Category"
4. Enter name and description
5. Click "Save"

## Troubleshooting

### "ModuleNotFoundError: No module named 'django'"
**Solution:** Install dependencies
```bash
pip install -r requirements.txt
```

### Database locked error
**Solution:** Delete `db.sqlite3` and run migrations again
```bash
rm db.sqlite3
python manage.py migrate
python manage.py seed_data
```

### Port 8000 already in use
**Solution:** Use a different port
```bash
python manage.py runserver 8001
```

### Admin login not working
**Solution:** Create a new superuser
```bash
python manage.py createsuperuser
```

## Sample Data

The project includes 10 pre-loaded categories and components:

**Categories:**
- Resistors
- Capacitors
- Inductors
- Diodes
- Transistors
- Transformers
- Relays
- Switches
- Circuit Breakers
- Fuses

**Wire Sizes:** 14 standard wire sizes (0.75mm² to 120mm²)

## API Quick Reference

### Get all components
```bash
curl http://localhost:8000/api/components/
```

### Search components
```bash
curl "http://localhost:8000/api/components/?search=resistor"
```

### Get all categories
```bash
curl http://localhost:8000/api/categories/
```

### Get all wire sizes
```bash
curl http://localhost:8000/api/wire-sizes/
```

### Calculate wire size
```bash
curl -X POST http://localhost:8000/api/wire-recommendation/recommend/ \
  -H "Content-Type: application/json" \
  -d '{"required_current": 15}'
```

## Next Steps

1. **Explore the Interface**
   - Browse components
   - Try the calculator
   - View wire reference

2. **Add Your Data**
   - Create custom components
   - Manage categories
   - Configure wire sizes

3. **Use the API**
   - Integrate with other applications
   - Build mobile apps
   - Create dashboards

4. **Deploy to Production**
   - Follow the README for PythonAnywhere deployment
   - Configure security settings
   - Set up backups

## Resources

- 📖 [Full Documentation](README.md)
- 📡 [API Documentation](API_DOCUMENTATION.md)
- 🐍 [Django Documentation](https://docs.djangoproject.com/)
- 🚀 [PythonAnywhere Hosting](https://www.pythonanywhere.com/)

## Security Tips

1. **Change Secret Key:** Edit `infolectric/settings.py`
   ```python
   SECRET_KEY = 'your-long-random-secret-key'
   ```

2. **Use Strong Passwords:** For admin accounts and database

3. **Enable HTTPS:** Required for production deployments

4. **Regular Backups:** Backup your database regularly
   ```bash
   python manage.py dumpdata > backup.json
   ```

5. **Update Dependencies:** Keep packages current
   ```bash
   pip install --upgrade -r requirements.txt
   ```

## Support

For help or questions:
1. Check the [README.md](README.md)
2. Review [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
3. Check Django documentation
4. Open an issue on GitHub

## Happy Coding! ⚡

Infolectric is designed to be beginner-friendly while being powerful enough for real-world use. 

Start exploring and building today!
