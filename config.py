import os


class DevConfig(object):
    """Standard configuration options"""
    DEBUG = True
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DB_FILE = os.path.join(BASE_DIR, 'database.sqlite3')
    FILE_UPLOAD_DIRECTORY = os.path.join(BASE_DIR, 'file_uploads')
    print("Database at " + DB_FILE)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + DB_FILE
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    WTF_CSRF_ENABLED = True
    SECRET_KEY = "secret"
    SECURITY_PASSWORD_SALT = "sale"
    SECURITY_TRACKABLE = 'True'
    SMTP_SERVER = 'localhost'
    APPLICATION_EMAIL_ADDRESS = "lcdruit@leicester.le.ac.uk"
    ADMIN_EMAIL_ADDRESSES = "lcdruit@leicester.le.ac.uk"
    ERROR_EMAIL_SUBJECT = 'LBRC Study Data Upload Error'
    SECURITY_CHANGEABLE = True
    SECURITY_RECOVERABLE = True

class TestConfig(DevConfig):
    """Configuration for general testing"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    WTF_CSRF_ENABLED = False


class TestConfigCRSF(TestConfig):
    WTF_CSRF_ENABLED = True
