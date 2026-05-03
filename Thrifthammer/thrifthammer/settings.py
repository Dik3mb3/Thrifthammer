"""
Django settings for Thrifthammer — a Warhammer price tracker.
"""

import os
from pathlib import Path

import dj_database_url

# Load .env in local development (no-op if python-dotenv not installed or file missing)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / '.env')
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-change-me-in-production'
)

DEBUG = os.environ.get('DJANGO_DEBUG', 'False').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',')
    if origin.strip()
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    # Thrifthammer apps
    'accounts',
    'products',
    'prices.apps.PricesConfig',
    'scrapers',
    'collections_app',
    'calculators',
    'blog',
    'factions',
]

if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'thrifthammer.middleware.ContentSecurityPolicyMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

if DEBUG:
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    INTERNAL_IPS = ['127.0.0.1']

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
                'products.context_processors.site_stats',
            ],
        },
    },
]

WSGI_APPLICATION = 'thrifthammer.wsgi.application'

# Database — Railway provides DATABASE_URL; falls back to SQLite locally.
# conn_max_age=0 closes connections immediately after each request so that
# Railway's PostgreSQL connection limit is never exhausted by idle workers.
DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=0,
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

# Allow login with username OR email address
AUTHENTICATION_BACKENDS = [
    'accounts.backends.EmailOrUsernameBackend',
    'django.contrib.auth.backends.ModelBackend',
]

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

# ---------------------------------------------------------------------------
# Security settings (applied in all environments)
# ---------------------------------------------------------------------------
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# ---------------------------------------------------------------------------
# Production security settings
# ---------------------------------------------------------------------------
# Railway terminates SSL at the load balancer, so we trust its forwarded header
# rather than redirecting at the Django level.
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000       # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

# Scraper settings
SCRAPER_USER_AGENT = os.environ.get(
    'SCRAPER_USER_AGENT',
    'Thrifthammer/1.0 (Warhammer Price Tracker)'
)
SCRAPER_REQUEST_DELAY = int(os.environ.get('SCRAPER_REQUEST_DELAY', '2'))

# ---------------------------------------------------------------------------
# eBay Browse API configuration
# ---------------------------------------------------------------------------
# The legacy Finding API was decommissioned in 2024. We now use the
# Browse API v1 with OAuth 2.0 Client Credentials authentication.
#
# Set these in Railway environment variables (never hardcode keys):
#   EBAY_APP_ID_PRODUCTION   — Client ID from developer.ebay.com/my/keys
#   EBAY_CERT_ID_PRODUCTION  — Client Secret (Cert ID) from same page
#   EBAY_APP_ID_SANDBOX      — Sandbox Client ID (for testing)
#   EBAY_CERT_ID_SANDBOX     — Sandbox Client Secret (for testing)
#
# Rate limits (Browse API, standard developer account):
#   - 5,000 calls/day (resets midnight Pacific Time)
#   - Our ~307 products use ~307 calls/run
#
# Usage:
#   python manage.py update_ebay_prices --sandbox --limit 5  (test)
#   python manage.py update_ebay_prices --limit 10 --dry-run (verify)
#   python manage.py update_ebay_prices                      (full run)
EBAY_APP_ID_PRODUCTION  = os.environ.get('EBAY_APP_ID_PRODUCTION', '')
EBAY_CERT_ID_PRODUCTION = os.environ.get('EBAY_CERT_ID_PRODUCTION', '')
EBAY_APP_ID_SANDBOX     = os.environ.get('EBAY_APP_ID_SANDBOX', '')
EBAY_CERT_ID_SANDBOX    = os.environ.get('EBAY_CERT_ID_SANDBOX', '')
EBAY_USE_SANDBOX = os.environ.get('EBAY_USE_SANDBOX', 'False').lower() in ('true', '1', 'yes')
EBAY_CALLS_PER_DAY_LIMIT = 5000
EBAY_DELAY_BETWEEN_CALLS = 0.5

# eBay Partner Network (EPN) affiliate campaign ID.
# Set EBAY_AFFILIATE_CAMPAIGN_ID in Railway environment variables.
# When set, the scraper appends EPN tracking params to every saved eBay URL
# so clicks generate affiliate revenue.
EBAY_AFFILIATE_CAMPAIGN_ID = os.environ.get('EBAY_AFFILIATE_CAMPAIGN_ID', '')

# ---------------------------------------------------------------------------
# Email configuration — for the "Report Issue" feature
# ---------------------------------------------------------------------------
# In production set these Railway environment variables:
#   EMAIL_BACKEND   = django.core.mail.backends.smtp.EmailBackend
#   EMAIL_HOST      = smtp.gmail.com
#   EMAIL_PORT      = 587
#   EMAIL_USE_TLS   = True
#   EMAIL_HOST_USER = Thrifthammer.com@gmail.com
#   EMAIL_HOST_PASSWORD = <Gmail App Password (Settings → Security → App passwords)>
#   DEFAULT_FROM_EMAIL  = Thrifthammer.com@gmail.com
#
# Locally the console backend prints emails to stdout — no config needed.
EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend',
)
EMAIL_HOST          = os.environ.get('EMAIL_HOST',     'smtp.gmail.com')
EMAIL_PORT          = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS       = os.environ.get('EMAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
EMAIL_HOST_USER     = os.environ.get('EMAIL_HOST_USER',     '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL  = os.environ.get('DEFAULT_FROM_EMAIL',  'noreply@thrifthammer.com')
EMAIL_TIMEOUT       = int(os.environ.get('EMAIL_TIMEOUT', '10'))  # seconds; prevents SMTP hangs

# Address that receives "Report Issue" submissions
ISSUE_REPORT_EMAIL = 'Thrifthammer.com@gmail.com'
