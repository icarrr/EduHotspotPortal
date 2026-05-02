import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Database
    DB_PATH = os.environ.get('DB_PATH', os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'eduhotspotportal.db'))

    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_PATH}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # MikroTik
    MIKROTIK_HOST = os.environ.get('MIKROTIK_HOST', '192.168.1.1')
    MIKROTIK_PORT = int(os.environ.get('MIKROTIK_PORT', '8728'))
    MIKROTIK_USER = os.environ.get('MIKROTIK_USER', 'apiuser')
    MIKROTIK_PASSWORD = os.environ.get('MIKROTIK_PASSWORD', 'apipassword')
    MIKROTIK_USE_SSL = os.environ.get('MIKROTIK_USE_SSL', 'false').lower() == 'true'


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
