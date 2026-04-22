import os
from datetime import timedelta

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-this-in-production'
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # File upload configurations
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    DOWNLOAD_FOLDER = os.path.join(BASE_DIR, 'downloads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
    
    # Database configuration
    DATABASE_PROVIDER = 'supabase'
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Program levels
    PROGRAM_LEVELS = ['UG', 'PG', 'PhD']
    
    # Semester types
    SEMESTER_TYPES = ['monsoon', 'winter']
    
    # Exam types
    EXAM_TYPES = ['midsem', 'endsem']
    
    # Sheet types
    SHEET_TYPES = ['UG', 'PG', 'PhD', 'combined']

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    DATABASE_PROVIDER = 'supabase'


class VercelConfig(Config):
    """Vercel serverless configuration"""
    DEBUG = False
    TESTING = False
    # Use None for folder paths on Vercel (read-only filesystem)
    UPLOAD_FOLDER = None
    DOWNLOAD_FOLDER = None
    DATABASE_PROVIDER = 'supabase'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'vercel': VercelConfig,
    'default': DevelopmentConfig
}
