# Infolectric - Electrical Information & Calculation Platform

A comprehensive Django web application for electrical education, component reference, and calculations.

## Features

✨ **Component Management**
- Browse and search electrical components
- Categorized component library
- Detailed component specifications
- Image support for components

📊 **Wire Size Reference**
- Complete wire size database with ampacity ratings
- Wire selection guidelines
- Safety information

🔧 **Wire Calculator**
- Input required current (amps)
- Get recommended wire sizes
- See applications and safety ratings

🛡️ **Authentication & Authorization**
- Django authentication system
- Admin interface for data management
- Role-based access control

🌐 **API**
- RESTful API endpoints for all data
- JSON responses
- Filterable and searchable endpoints

## Technology Stack

- **Backend:** Django 4.2
- **API:** Django REST Framework
- **Frontend:** Bootstrap 5
- **Database:** SQLite (development)
- **Deployment:** PythonAnywhere (recommended)

## Project Structure

```
infolectric/
├── infolectric/              # Project settings
│   ├── settings.py           # Django settings
│   ├── urls.py              # Main URL routing
│   ├── wsgi.py              # WSGI application
│   └── asgi.py              # ASGI application
├── core/                     # Main application
│   ├── models.py            # Database models
│   ├── views.py             # View logic
│   ├── api_views.py         # API endpoints
│   ├── forms.py             # Form classes
│   ├── serializers.py       # DRF serializers
│   ├── urls.py              # App URL routing
│   ├── admin.py             # Admin configuration
│   ├── templates/core/      # HTML templates
│   ├── static/              # CSS, JS, images
│   ├── migrations/          # Database migrations
│   └── management/commands/
│       └── seed_data.py     # Data seeding command
├── media/                    # User-uploaded files
├── templates/              # Project templates
├── static/                 # Project-wide static files
├── manage.py              # Django management script
└── requirements.txt       # Python dependencies
```

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Virtual environment (recommended)

### Step 1: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Configure Database

```bash
# Create database tables
python manage.py migrate

# Create superuser (admin account)
python manage.py createsuperuser
# Follow the prompts to create your admin account
```

### Step 4: Load Sample Data

```bash
python manage.py seed_data
```

This will populate the database with:
- 10 electrical component categories
- 10 sample components
- 14 wire size specifications with ampacity ratings

### Step 5: Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### Step 6: Run Development Server

```bash
python manage.py runserver
```

Access the application at: `http://127.0.0.1:8000/`

Admin interface: `http://127.0.0.1:8000/admin/`

## Usage

### Public Features
- **Home Page:** Overview of the platform
- **Components:** Browse all components with search and filtering
- **Categories:** View component categories
- **Wire Sizes:** Reference all available wire sizes
- **Calculator:** Calculate wire recommendations based on current

### Admin Features (Login Required)
- Create, edit, delete components
- Manage categories
- Add wire sizes
- View all data in admin interface

## API Endpoints

### Components
- `GET /api/components/` - List all components
- `GET /api/components/{id}/` - Get specific component
- `POST /api/components/` - Create component (admin only)
- `PUT /api/components/{id}/` - Update component (admin only)
- `DELETE /api/components/{id}/` - Delete component (admin only)
- `GET /api/components/by_category/?category_id={id}` - Filter by category

### Categories
- `GET /api/categories/` - List all categories
- `GET /api/categories/{id}/` - Get specific category
- `GET /api/categories/{id}/components/` - Get category's components
- `POST /api/categories/` - Create category (admin only)
- `PUT /api/categories/{id}/` - Update category (admin only)
- `DELETE /api/categories/{id}/` - Delete category (admin only)

### Wire Sizes
- `GET /api/wire-sizes/` - List all wire sizes
- `GET /api/wire-sizes/{id}/` - Get specific wire size
- `POST /api/wire-sizes/` - Create wire size (admin only)
- `PUT /api/wire-sizes/{id}/` - Update wire size (admin only)
- `DELETE /api/wire-sizes/{id}/` - Delete wire size (admin only)

### Wire Calculator
- `POST /api/wire-recommendation/recommend/` - Get wire recommendations
  ```json
  {
    "required_current": 15.5
  }
  ```

## Deployment to PythonAnywhere

### Step 1: Create PythonAnywhere Account
Visit https://www.pythonanywhere.com and create a free account.

### Step 2: Clone Repository
```bash
git clone <your-repo-url>
cd infolectric
```

### Step 3: Set Up Virtual Environment
```bash
mkvirtualenv --python=/usr/bin/python3.9 infolectric
pip install -r requirements.txt
```

### Step 4: Configure Django Settings
Edit `infolectric/settings.py`:
```python
DEBUG = False
ALLOWED_HOSTS = ['yourusername.pythonanywhere.com']
SECRET_KEY = 'your-secret-key-change-this'

# Database configuration for production
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/home/yourusername/infolectric/db.sqlite3',
    }
}
```

### Step 5: Set Up Web App
- In PythonAnywhere, add a new web app
- Select "Manual configuration" and Python 3.9
- Configure WSGI file to point to `infolectric/wsgi.py`

### Step 6: Database & Static Files
```bash
python manage.py migrate
python manage.py collectstatic
python manage.py seed_data
```

### Step 7: Reload Web App
Reload your web app in PythonAnywhere dashboard.

## Security Considerations

1. **Change Secret Key:** Generate a new SECRET_KEY in production
2. **HTTPS:** Enable HTTPS in PythonAnywhere settings
3. **DEBUG Mode:** Set `DEBUG = False` in production
4. **Admin Panel:** Use strong passwords for admin accounts
5. **CORS:** Configure CORS if accessing API from different domain
6. **Environment Variables:** Use environment variables for sensitive data

## Database Models

### Category
- `name` - Category name (unique)
- `description` - Optional description
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

### Component
- `name` - Component name (unique)
- `description` - Detailed description
- `category` - Foreign key to Category
- `image` - Optional image file
- `date_created` - Creation timestamp
- `updated_at` - Last update timestamp

### WireSize
- `wire_size_mm2` - Wire cross-section in mm² (unique)
- `max_ampacity` - Maximum safe current in amps
- `description` - Application and description
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

## Forms & Validation

### ComponentForm
- Validates component name is not empty
- Validates description is provided
- Supports image uploads

### CategoryForm
- Validates unique category names
- Optional description

### WireSizeForm
- Validates ampacity is greater than 0
- Validates wire size is positive
- Supports decimal wire sizes

### WireCalculatorForm
- Validates required current is positive
- Accepts decimal values

## Common Commands

```bash
# Run development server
python manage.py runserver

# Create database migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load sample data
python manage.py seed_data

# Access Django shell
python manage.py shell

# Collect static files
python manage.py collectstatic

# Run tests
python manage.py test
```

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'django'"
**Solution:** Activate virtual environment and install requirements
```bash
pip install -r requirements.txt
```

### Issue: Database errors after model changes
**Solution:** Create and apply migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Issue: Static files not loading
**Solution:** Collect static files
```bash
python manage.py collectstatic --noinput
```

### Issue: Admin login not working
**Solution:** Create superuser
```bash
python manage.py createsuperuser
```

## Contributing

Contributions are welcome! Please follow these guidelines:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or suggestions, please open an issue on the repository.

## Changelog

### Version 1.0.0 (Initial Release)
- Complete component management system
- Wire size reference database
- Wire recommendation calculator
- RESTful API
- Bootstrap 5 responsive design
- Django admin interface
- Sample seed data
- Comprehensive documentation

---

**Note:** This is an educational project designed for students, electricians, and electronics enthusiasts. Always follow local electrical codes and safety regulations in your jurisdiction.
