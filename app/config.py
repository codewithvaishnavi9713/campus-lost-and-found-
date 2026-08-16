import os

class Config:
    """Base application configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'smart-campus-lost-found-dev-key')
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() in ['true', '1', 't']
    
    # SQLite Database Configuration
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
    os.makedirs(INSTANCE_DIR, exist_ok=True)
    
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 
        f"sqlite:///{os.path.join(INSTANCE_DIR, 'app.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # File Upload Configuration
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
    # Comma-separated staff accounts. Empty by default: an administrator is an
    # explicit deployment decision, never something inferred from a user name.
    CAMPUS_ADMIN_EMAILS = {
        value.strip().lower() for value in os.environ.get('CAMPUS_ADMIN_EMAILS', '').split(',') if value.strip()
    }
    IMAGE_SIMILARITY_ENABLED = os.environ.get('IMAGE_SIMILARITY_ENABLED', 'false').lower() in {'1', 'true', 'yes'}
    
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
