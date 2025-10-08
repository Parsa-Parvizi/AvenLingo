import os
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
load_dotenv(os.path.join(BASE_DIR, '.env'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
# DEBUG = True

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Academy Apps
    'core',
    'account',
    'course',
    'teacher',
    'enrollment',
    'dashboard',
]

# Conditionally add performance & debugging tools if available
try:
    import debug_toolbar
    INSTALLED_APPS.append('debug_toolbar')
    HAS_DEBUG_TOOLBAR = True
except ImportError:
    HAS_DEBUG_TOOLBAR = False

try:
    import django_extensions
    INSTALLED_APPS.append('django_extensions')
except ImportError:
    pass

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'account.middleware.SecurityHeadersMiddleware',  # هدرهای امنیتی
    # 'whitenoise.middleware.WhiteNoiseMiddleware',  # Temporarily disabled
    # 'core.middleware.QueryCountMiddleware',  # Query count monitoring - Disabled
    'core.middleware.URLSecurityMiddleware',  # URL security and validation
    'core.middleware.URLValidationMiddleware',  # External URL validation
    'core.middleware.BrokenURLMiddleware',  # Handle broken URLs
    'account.middleware.SecurityMiddleware',  # Custom security middleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'account.middleware.SessionSecurityMiddleware',  # بررسی امنیت session
    'account.middleware.LoginHistoryMiddleware',  # ثبت تاریخچه ورود
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'account.middleware.ErrorHandlingMiddleware',  # مدیریت امن خطاها
]

# Conditionally add debug toolbar middleware if available
if DEBUG and HAS_DEBUG_TOOLBAR:
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')

# Security settings - HTTPS/SSL disabled
SECURE_SSL_REDIRECT = False # Should be True in production
SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False
X_FRAME_OPTIONS = 'SAMEORIGIN'
SECURE_HSTS_SECONDS = 0
# SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = False # Should be True in production
SECURE_HSTS_PRELOAD = False # Should be True in production

ROOT_URLCONF = 'EnglishTeacher.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                ],
        },
    },
]

WSGI_APPLICATION = 'EnglishTeacher.wsgi.application'

# Database configuration with environment variables
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'englishteacher_db'),
        'USER': os.getenv('DB_USER', 'englishteacher_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'password'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': {
            'connect_timeout': 5,  # Reduced from 60 to 5 seconds
        },
    }
}

# No caching configuration needed

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},

]

# Internationalization
LANGUAGE_CODE = 'fa-ir'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = os.getenv('STATIC_URL', '/static/')
STATIC_ROOT = os.getenv('STATIC_ROOT', BASE_DIR / 'staticfiles')

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = os.getenv('MEDIA_URL', '/media/')
MEDIA_ROOT = os.getenv('MEDIA_ROOT', BASE_DIR / 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'account.User'

# Email configuration
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
if not DEBUG:
    EMAIL_HOST = os.getenv('EMAIL_HOST')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
    EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
    EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')

# Admin email for notifications
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@academy.com')

# Logs directory creation disabled for development speed

# Enhanced Logging Configuration
# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'formatters': {
#         'detailed': {
#             'format': '{levelname} {asctime} [{name}] {process:d} {thread:d} {message}',
#             'style': '{',
#         },
#         'simple': {
#             'format': '{levelname} {message}',
#             'style': '{',
#         },
#     },
#     'handlers': {
#         'console': {
#             'class': 'logging.StreamHandler',
#             'formatter': 'simple',
#         },
#         # File logging disabled for development speed
#     },
#     'loggers': {
#         'security': {
#             'handlers': ['security_file', 'console'],
#             'level': 'WARNING',
#             'propagate': False,
#         },
#         'account.login': {
#             'handlers': ['account_file', 'console'],
#             'level': 'INFO',
#             'propagate': False,
#         },
#         'account.logout': {
#             'handlers': ['account_file', 'console'],
#             'level': 'INFO',
#             'propagate': False,
#         },
#         'account.registration': {
#             'handlers': ['account_file', 'console'],
#             'level': 'INFO',
#             'propagate': False,
#         },
#         'account.forms': {
#             'handlers': ['account_file', 'console'],
#             'level': 'WARNING',
#             'propagate': False,
#         },
#         'django': {
#             'handlers': ['console'],
#             'level': 'WARNING',  # Only warnings and errors
#             'propagate': False,
#         },
#     },
#     'root': {
#         'handlers': ['console'],
#         'level': 'WARNING',
#     },
# }

# Additional Security Settings
MAX_REQUEST_SIZE = 5 * 1024 * 1024  # 5MB max request size
CHECK_SESSION_IP = True  # بررسی IP برای امنیت بیشتر

# Session Security Settings (استانداردهای امنیتی)
SESSION_COOKIE_SECURE = not DEBUG  # فقط HTTPS در production
SESSION_COOKIE_HTTPONLY = True  # جلوگیری از دسترسی JavaScript
SESSION_COOKIE_SAMESITE = 'Strict'  # محافظت قوی‌تر در برابر CSRF
SESSION_COOKIE_AGE = 3600  # 1 ساعت
SESSION_SAVE_EVERY_REQUEST = True  # بروزرسانی session در هر درخواست
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # session بعد از بستن مرورگر منقضی می‌شود

# CSRF Security (امنیت در برابر حملات CSRF)
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'
CSRF_USE_SESSIONS = True  # ذخیره CSRF token در session به جای cookie

# Security Headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'  # جلوگیری از clickjacking

# Content Security Policy - HTTP only
CSP_DEFAULT_SRC = ("'self'", "http:", "https:")
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "'unsafe-eval'", "http:", "https:", "cdnjs.cloudflare.com", "code.jquery.com", "cdn.jsdelivr.net", "unpkg.com")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "http:", "https:", "fonts.googleapis.com", "cdn.jsdelivr.net", "unpkg.com")
CSP_FONT_SRC = ("'self'", "http:", "https:", "fonts.gstatic.com")
CSP_IMG_SRC = ("'self'", "http:", "https:", "data:")
CSP_CONNECT_SRC = ("'self'", "http:", "https:")

# Debug Toolbar Configuration (only if available)
if HAS_DEBUG_TOOLBAR:
    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG and request.META.get('REMOTE_ADDR') in INTERNAL_IPS,
        'SHOW_TEMPLATE_CONTEXT': True,
        'ENABLE_STACKTRACES': True,
    }

INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
    '0.0.0.0',

]

# Caching Disabled
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Session Configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 3600  # 1 hour

# Database Connection - Basic Settings
if 'default' in DATABASES:
    DATABASES['default']['CONN_MAX_AGE'] = 0  # No connection pooling
    
    # Basic PostgreSQL settings
    if DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql':
        DATABASES['default']['OPTIONS'] = DATABASES['default'].get('OPTIONS', {})
        DATABASES['default']['OPTIONS'].update({
            'application_name': 'EnglishTeacher',
        })
    
    # Basic MySQL settings
    elif DATABASES['default']['ENGINE'] == 'django.db.backends.mysql':
        DATABASES['default']['OPTIONS'] = DATABASES['default'].get('OPTIONS', {})
        DATABASES['default']['OPTIONS'].update({
            'charset': 'utf8mb4',
        })

# Performance Settings
DEBUG_PROPAGATE_EXCEPTIONS = False
# USE_ETAGS = True  # Disabled since caching is disabled

# Django Basic Settings
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'  # Standard ID generation

# Database Query - Basic Settings
CONN_MAX_AGE = 0  # No connection pooling
OPTIMIZE_TABLE_SCANS = False  # Disable table scan optimization

# Basic Upload Settings
DATA_UPLOAD_MAX_MEMORY_SIZE = 2621440  # 2.5MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 2621440  # 2.5MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000  # Basic limit

# Database Performance - Disabled
DB_OPTIMIZE_QUERIES = False
DB_OPTIMIZE_JOINS = False

# Query Optimization - Clean Console Output
if DEBUG:
    # Clean, minimal logging for development
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'clean': {
                'format': '{levelname:8} {message}',
                'style': '{',
            },
            'performance': {
                'format': '⚡ {message}',
                'style': '{',
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'clean',
            },
            'performance': {
                'class': 'logging.StreamHandler',
                'formatter': 'performance',
            },
        },
        'loggers': {
            'django.db.backends': {
                'level': 'WARNING',  # Only show warnings, not every query
                'handlers': ['console'],
                'propagate': False,
            },
            'django.utils': {
                'level': 'WARNING',  # Reduce utility logging
                'handlers': ['console'],
                'propagate': False,
            },
            'core.middleware': {
                'level': 'INFO',
                'handlers': ['performance'],
                'propagate': False,
            },
        },
        'root': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    }

# Template Caching Disabled
# TEMPLATES[0]['OPTIONS']['loaders'] = [
#     ('django.template.loaders.cached.Loader', [
#         'django.template.loaders.filesystem.Loader',
#         'django.template.loaders.app_directories.Loader',
#     ]),
# ]

# Static Files Performance
# Temporarily using Django's default static files storage
# STATICFILES_STORAGE = 'whitenoise.storage.StaticFilesStorage'

# Cache timeouts disabled
# CACHE_TIMEOUTS = {
#     'homepage': 300,      # 5 minutes
#     'course_list': 600,   # 10 minutes  
#     'user_profile': 1800, # 30 minutes
#     'static_content': 3600, # 1 hour
# }

# Rate Limiting Settings
RATELIMIT_ENABLE = False
# RATELIMIT_USE_CACHE = 'default'

# External URLs and Social Media Configuration
EXTERNAL_URLS = {
    # Social Media URLs
    'INSTAGRAM_DEFAULT': 'https://instagram.com/academy',
    'TELEGRAM_DEFAULT': 'https://t.me/academy',
    'LINKEDIN_DEFAULT': 'https://linkedin.com/company/academy',
    'YOUTUBE_DEFAULT': 'https://youtube.com/@academy',
    'WHATSAPP_DEFAULT': 'https://wa.me/989123456789',
    
    # External CDN URLs
    'FONT_AWESOME_CDN': 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css',
    'DARKMODE_JS_CDN': 'https://unpkg.com/darkmode-js/lib/darkmode-js.min.js',
    
    # Development URLs
    'LOCALHOST_DEV': 'http://127.0.0.1:8000',
    'LOCALHOST_PROD': 'http://localhost:8000',
    
    # GitHub URLs
    'GITHUB_DEVELOPER': 'https://github.com/Parsa-Parvizi',
    'GITHUB_REPO': 'https://github.com/Parsa-Parvizi/MobinaGarshasbi.git',
    
    # Docker and deployment URLs
    'DOCKER_COMPOSE_RELEASE': 'https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)',
    'DOCKER_UBUNTU_REPO': 'https://download.docker.com/linux/ubuntu',
}

# URL Validation Settings
URL_VALIDATION = {
    'ENABLE_EXTERNAL_URL_VALIDATION': True,
    'TIMEOUT_SECONDS': 10,
    'MAX_REDIRECTS': 5,
    'ALLOWED_SCHEMES': ['http', 'https'],
    'BLOCKED_DOMAINS': [
        'malicious-site.com',
        'phishing-site.com',
    ],
    # Development overrides
    'SKIP_VALIDATION_IN_DEBUG': True,
    'ALLOW_LOCALHOST_IN_DEBUG': True,
    'DEBUG_LOGGING': True,
}

# Security Settings for URLs
URL_SECURITY = {
    'ENABLE_HTTPS_REDIRECT': not DEBUG,
    'ENABLE_HSTS': not DEBUG,
    'HSTS_SECONDS': 31536000,  # 1 year
    'ENABLE_CONTENT_SECURITY_POLICY': True,
    'CSP_DEFAULT_SRC': ["'self'"],
    'CSP_SCRIPT_SRC': ["'self'", "'unsafe-inline'", "'unsafe-eval'", "https://unpkg.com", "https://cdnjs.cloudflare.com", "https://code.jquery.com", "https://cdn.jsdelivr.net"],
    'CSP_STYLE_SRC': ["'self'", "'unsafe-inline'", "https://cdnjs.cloudflare.com", "https://fonts.googleapis.com", "https://cdn.jsdelivr.net"],
    'CSP_FONT_SRC': ["'self'", "https://cdnjs.cloudflare.com", "https://fonts.gstatic.com"],
    'CSP_IMG_SRC': ["'self'", "data:", "https:"],
    # Development overrides
    'SKIP_SECURITY_IN_DEBUG': True,
    'ALLOW_LOCALHOST_IN_DEBUG': True,
    'DEBUG_LOGGING': True,
}
