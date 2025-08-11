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
    'contact',
    'course',
    'teacher',
    'enrollment',
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
    # 'whitenoise.middleware.WhiteNoiseMiddleware',  # Temporarily disabled
    # 'core.middleware.QueryCountMiddleware',  # Query count monitoring - Disabled
    'account.middleware.SecurityMiddleware',  # Custom security middleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'account.middleware.SessionSecurityMiddleware',  # Session security
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Conditionally add debug toolbar middleware if available
if DEBUG and HAS_DEBUG_TOOLBAR:
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')

# Security settings - HTTPS/SSL disabled
SECURE_SSL_REDIRECT = False
SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False
X_FRAME_OPTIONS = 'SAMEORIGIN'
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

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
                # 'core.context_processors.site_data',  # Temporarily disabled for speed
                # 'core.context_processors.footer_data',  # Temporarily disabled for speed
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
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '{levelname} {asctime} [{name}] {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        # File logging disabled for development speed
    },
    'loggers': {
        'security': {
            'handlers': ['security_file', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'account.login': {
            'handlers': ['account_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'account.logout': {
            'handlers': ['account_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'account.registration': {
            'handlers': ['account_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'account.forms': {
            'handlers': ['account_file', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',  # Only warnings and errors
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}

# Additional Security Settings
MAX_REQUEST_SIZE = 5 * 1024 * 1024  # 5MB max request size
CHECK_SESSION_IP = False  # Set to True in production for stricter security

# Session Security Settings
SESSION_COOKIE_SECURE = False  # Allow cookies over HTTP
SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access to session cookies
SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
SESSION_COOKIE_AGE = 3600  # 1 hour default session timeout

# CSRF Security
CSRF_COOKIE_SECURE = False  # Allow CSRF cookies over HTTP
CSRF_COOKIE_HTTPONLY = True  # Prevent JavaScript access to CSRF cookies
CSRF_COOKIE_SAMESITE = 'Lax'

# Content Security Policy - HTTP only
CSP_DEFAULT_SRC = ("'self'", "http:", "https:")
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "http:", "https:", "cdnjs.cloudflare.com")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "http:", "https:", "fonts.googleapis.com")
CSP_FONT_SRC = ("'self'", "http:", "https:", "fonts.gstatic.com")
CSP_IMG_SRC = ("'self'", "http:", "https:", "data:")
CSP_CONNECT_SRC = ("'self'", "http:", "https:")

# =============================================================================
# PERFORMANCE OPTIMIZATION SETTINGS
# =============================================================================

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

print("ℹ️  Caching disabled - using dummy cache")
print("🚀 ULTRA-FAST DEVELOPMENT MODE:")
print("   • Database query logging disabled")
print("   • Query count monitoring disabled")
print("   • Caching disabled")
print("   • Connection pooling disabled")
print("   • Context processors disabled")
print("   • Heavy logging disabled")
print("   • File logging disabled")
print("   • Fast database timeouts (5s)")
print("   • Minimal overhead for speed")

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
