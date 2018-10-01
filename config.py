import os


class BaseConfig(object):
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    FILE_UPLOAD_DIRECTORY = os.path.join(BASE_DIR, 'file_uploads')
    SQLALCHEMY_ECHO = False
    WTF_CSRF_ENABLED = True
    SECURITY_TRACKABLE = 'True'
    SMTP_SERVER = 'localhost'
    APPLICATION_EMAIL_ADDRESS = "lcbruit@leicester.le.ac.uk"
    ADMIN_EMAIL_ADDRESSES = "rab63@le.ac.uk"
    ERROR_EMAIL_SUBJECT = 'LBRC Study Data Upload Error'
    SECURITY_CHANGEABLE = True
    SECURITY_RECOVERABLE = True


class DevConfig(BaseConfig):
    """Standard configuration options"""
    DEBUG = True
    DB_FILE = os.path.join(BaseConfig.BASE_DIR, 'database.sqlite3')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + DB_FILE
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SECRET_KEY = "secret"
    SECURITY_PASSWORD_SALT = "sale"


class LiveConfig(BaseConfig):
    """Standard configuration options"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', '')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', '')
    SECURITY_PASSWORD_SALT = os.getenv('FLASK_SALT', '')

class TestConfig(DevConfig):
    """Configuration for general testing"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    WTF_CSRF_ENABLED = False


class TestConfigCRSF(TestConfig):
    WTF_CSRF_ENABLED = True
