# LBRC Upload Application - Copilot Instructions

This is a Flask-based web application for managing file uploads with user authentication and study management features. The application is part of the Leicester Biomedical Research Centre (LBRC) suite of tools.

## Project Structure

- `alembic/` - Database migration scripts
- `lbrc_upload/` - Main application package
  - `admin.py` - Admin interface configuration
  - `model.py` - SQLAlchemy database models
  - `security.py` - Authentication and authorization
  - `ui/` - Web interface components
    - `forms.py` - WTForms definitions
    - `templates/` - Jinja2 templates
- `tests/` - Test suite
  - `ui/` - UI tests
  - `uploads/` - File upload tests

## Key Components

1. **Authentication System**
   - Uses Flask-Security for user management
   - Templates in `lbrc_upload/templates/security/`
   - Password reset and change functionality

2. **File Upload System**
   - Study-based file upload management
   - Size limits per study
   - Upload tracking and management
   - File storage in `file_uploads/` directory

3. **Admin Interface**
   - User management
   - Study configuration
   - Upload monitoring

4. **Database**
   - Uses SQLAlchemy ORM
   - Alembic for migrations
   - Tracks users, studies, and uploads

## Development Guidelines

### Adding New Features

1. **Database Changes**
   - Add models to `lbrc_upload/model.py`
   - Create migration using Alembic
   - Update test fixtures in `tests/conftest.py`

2. **UI Components**
   - Add forms to `lbrc_upload/ui/forms.py`
   - Create templates in `lbrc_upload/ui/templates/ui/`
   - Update routes in relevant UI modules

3. **Security**
   - Use decorators from `lbrc_upload/decorators.py`
   - Follow existing authentication patterns
   - Add appropriate access controls

### Testing

1. **Writing Tests**
   - Place UI tests in `tests/ui/`
   - Use pytest fixtures from `tests/conftest.py`
   - Follow existing test patterns for consistency

2. **Test Categories**
   - UI tests for web interface
   - Upload tests for file handling
   - Security tests for authentication
   - Study management tests

### Dependencies

- Main requirements in `requirements.txt`
- Development requirements in `requirements.dev`
- Uses `lbrc_flask` package for common functionality

## Environment Setup

1. Copy `example.env` to `.env`
2. Configure database and security settings
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements.dev  # for development
   ```
4. Run migrations:
   ```bash
   flask db upgrade
   ```

## Common Tasks

### Creating Database Migrations

```bash
flask db revision -m "description_of_change"
```

### Running Tests

```bash
pytest
```

### Development Server

```bash
flask run
```

## Best Practices

1. Follow Flask application factory pattern
2. Use Flask-Security for authentication
3. Write tests for new features
4. Document API changes
5. Follow existing code style
6. Use appropriate decorators for security
7. Handle file uploads securely
8. Validate study size limits