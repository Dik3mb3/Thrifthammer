"""
Django settings for Thrifthammer — a Warhammer price tracker.
"""

import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-change-me-in-production'
)

DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',')
    if origin.strip()
]

INSTALLED_APPS = [
    'debug_toolbar',  # For development debugging; auto-disabled in production
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Thrifthammer apps
    'accounts',
    'products',
    'prices',
    'scrapers',
    'collections_app',
    'calculators',
]

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',  # For development; auto-disabled in production
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

Internal_IPS = ['127.0.0.1']  # Required for django-debug-toolbar to work

ROOT_URLCONF = 'thrifthammer.urls'

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

WSGI_APPLICATION = 'thrifthammer.wsgi.application'

# Database — Railway provides DATABASE_URL; falls back to SQLite locally
DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STORAGES = {
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Auth
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = '/accounts/login/'

# ---------------------------------------------------------------------------
# Caching
# ---------------------------------------------------------------------------
# DatabaseCache requires no extra services — works out of the box with SQLite
# and PostgreSQL. Run `python manage.py createcachetable` once after setup.
# In production, swap to Redis by setting CACHE_BACKEND and CACHE_LOCATION
# environment variables.
CACHES = {
    'default': {
        'BACKEND': os.environ.get(
            'CACHE_BACKEND',
            'django.core.cache.backends.db.DatabaseCache',
        ),
        'LOCATION': os.environ.get('CACHE_LOCATION', 'django_cache'),
    }
}

# ---------------------------------------------------------------------------
# Database query logging (development only)
# ---------------------------------------------------------------------------
# Logs every SQL query to the console when DEBUG=True.
# Helps catch N+1 queries without needing django-debug-toolbar.
if DEBUG:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {'class': 'logging.StreamHandler'},
        },
        'loggers': {
            'django.db.backends': {
                'handlers': ['console'],
                # Set to WARNING in dev to silence query noise; change to DEBUG
                # when actively investigating query counts.
                'level': 'WARNING',
                'propagate': False,
            },
        },
    }

# Scraper settings
SCRAPER_USER_AGENT = os.environ.get(
    'SCRAPER_USER_AGENT',
    'Thrifthammer/1.0 (Warhammer Price Tracker)'
)
SCRAPER_REQUEST_DELAY = int(os.environ.get('SCRAPER_REQUEST_DELAY', '2'))
