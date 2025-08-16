# ALX Travel App

A Django-based travel listing platform API with comprehensive documentation and modern development practices.

## Project Overview

The ALX Travel App is a RESTful API built with Django and Django REST Framework that serves as the foundation for a travel listing platform. This project demonstrates industry-standard best practices for Django application development, including proper configuration management, API documentation, and database setup.

## Features

- **Django REST Framework**: Full-featured REST API with browsable interface
- **Swagger/OpenAPI Documentation**: Auto-generated API documentation available at `/swagger/`
- **MySQL Database Integration**: Production-ready database configuration
- **Environment Variable Management**: Secure configuration using django-environ
- **CORS Support**: Cross-Origin Resource Sharing for frontend integration
- **Celery Integration**: Background task processing capability
- **Admin Interface**: Django admin with custom model configuration
- **Version Control**: Git repository with proper .gitignore

## Tech Stack

- **Backend**: Django 5.2.4, Django REST Framework 3.16.0
- **Database**: MySQL (configured via environment variables)
- **API Documentation**: drf-yasg (Swagger/OpenAPI)
- **Task Queue**: Celery with RabbitMQ
- **Environment Management**: django-environ
- **CORS**: django-cors-headers

## Installation & Setup

### Prerequisites

- Python 3.8+
- MySQL Server
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/codexoft-ke/alx_travel_app
cd alx_travel_app
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the project root and configure your environment variables:

```env
# Database Configuration
DB_NAME=alx_travel_app_db
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
DB_PORT=3306

# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Celery Configuration
CELERY_BROKER_URL=pyamqp://guest@localhost//
CELERY_RESULT_BACKEND=rpc://

# CORS Settings
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### 5. Database Setup

Make sure MySQL is running and create the database:

```sql
CREATE DATABASE alx_travel_app_db;
```

Run migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser

```bash
python manage.py createsuperuser
```

### 7. Run Development Server

```bash
python manage.py runserver
```

## API Documentation

The API documentation is automatically generated and available at:

- **Swagger UI**: [http://localhost:8000/swagger/](http://localhost:8000/swagger/)
- **ReDoc**: [http://localhost:8000/redoc/](http://localhost:8000/redoc/)
- **Admin Interface**: [http://localhost:8000/admin/](http://localhost:8000/admin/)

## API Endpoints

### Current Endpoints

- `GET /api/v1/listings/welcome/` - Welcome endpoint with API information
- `GET /admin/` - Django admin interface
- `GET /swagger/` - Swagger API documentation
- `GET /redoc/` - ReDoc API documentation

### Future Endpoints (To be implemented)

- `GET /api/v1/listings/` - List all travel listings
- `POST /api/v1/listings/` - Create a new listing
- `GET /api/v1/listings/{id}/` - Retrieve a specific listing
- `PUT /api/v1/listings/{id}/` - Update a listing
- `DELETE /api/v1/listings/{id}/` - Delete a listing

## Project Structure

```
alx_travel_app/
├── alx_travel_app/          # Main project directory
│   ├── __init__.py          # Celery integration
│   ├── settings.py          # Django settings with environment variables
│   ├── urls.py              # Main URL configuration with Swagger
│   ├── wsgi.py              # WSGI application
│   └── celery.py            # Celery configuration
├── listings/                # Listings app
│   ├── migrations/          # Database migrations
│   ├── __init__.py
│   ├── admin.py             # Admin configuration
│   ├── apps.py              # App configuration
│   ├── models.py            # Database models
│   ├── urls.py              # App URL patterns
│   └── views.py             # API views
├── requirements.txt         # Project dependencies
├── .env                     # Environment variables (not in repo)
├── .gitignore              # Git ignore file
├── manage.py               # Django management script
└── README.md               # This file
```

## Configuration Details

### Django REST Framework

The project is configured with:
- Session-based authentication
- Read-only permissions for unauthenticated users
- JSON and browsable API renderers
- Pagination (20 items per page)

### CORS Configuration

CORS is configured to allow requests from:
- `http://localhost:3000` (React development server)
- `http://127.0.0.1:3000`

### Swagger Configuration

API documentation includes:
- Basic and Bearer authentication support
- Interactive API testing interface
- Comprehensive endpoint documentation
- Request/response schema definitions

## Development Guidelines

### Adding New Models

1. Define models in `listings/models.py`
2. Create and run migrations: `python manage.py makemigrations && python manage.py migrate`
3. Register models in `listings/admin.py`
4. Create serializers in `listings/serializers.py`
5. Add views in `listings/views.py`
6. Configure URLs in `listings/urls.py`

### Environment Variables

Always use environment variables for:
- Database credentials
- Secret keys
- Debug settings
- Third-party API keys
- CORS origins

### Git Workflow

1. Create feature branches for new development
2. Make atomic commits with descriptive messages
3. Test changes locally before committing
4. Update documentation as needed

## Testing

```bash
# Run Django tests
python manage.py test

# Check for issues
python manage.py check
```

## Background Tasks (Celery)

Start Celery worker:

```bash
celery -A alx_travel_app worker --loglevel=info
```

Start Celery beat (for scheduled tasks):

```bash
celery -A alx_travel_app beat --loglevel=info
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Update documentation
6. Submit a pull request

## License

This project is developed as part of the ALX Software Engineering program.

## Contact

For questions or support, please contact the development team.
