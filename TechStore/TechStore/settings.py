import os
from pathlib import Path
from decouple import config, Csv

# Основная директория проекта
BASE_DIR = Path(__file__).resolve().parent.parent

# --- БЕЗОПАСНОСТЬ (из md_smart) ---
# Пытаемся импортировать из config.py, если его нет — берем из .env или окружения
try:
    from .config import SECRET_KEY, ALLOWED_HOSTS, DEBUG
except ImportError:
    SECRET_KEY = config('SECRET_KEY', default='django-insecure-default-key')
    DEBUG = config('DEBUG', default=True, cast=bool)
    ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='', cast=Csv())

# Настройка CSRF
raw_csrf = config("CSRF_TRUSTED_ORIGINS", default="")
CSRF_TRUSTED_ORIGINS = [
    origin.strip() for origin in raw_csrf.split(",") if origin.strip()
]

# --- ПРИЛОЖЕНИЯ ---
INSTALLED_APPS = [
    'jazzmin',  # Интерфейс админки
    'colorfield',
    'solo',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Google/Social Authentication
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',

    # Твои приложения
    'users',
    'store',
    'orders'
]

# --- МОДЕЛЬ ПОЛЬЗОВАТЕЛЯ (Исправлено под твой файл users/models.py) ---
AUTH_USER_MODEL = 'users.User'

# --- AUTHENTICATION CONFIG ---
SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'APP': {
            'client_id': config("GOOGLE_CLIENT_ID", default=""),
            'secret': config("GOOGLE_CLIENT_SECRET", default=""),
            'key': ''
        }
    }
}

# Формы и редиректы
SOCIALACCOUNT_FORMS = {'signup': 'users.forms.CustomSocialSignupForm'}
LOGIN_REDIRECT_URL = '/users/profile'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = 'login'

# --- MIDDLEWARE ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Для статики
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'TechStore.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # Сюда можно добавить 'store.context_processors.layout_data' если создашь его
            ],
        },
    },
]

WSGI_APPLICATION = 'TechStore.wsgi.application'

# --- DATABASE ---
if os.path.exists('/app/data'):
    DB_PATH = Path('/app/data/db.sqlite3')
else:
    DB_PATH = BASE_DIR / 'db.sqlite3'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': DB_PATH,
    }
}

# --- ВАЛИДАЦИЯ ПАРОЛЕЙ ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- ЯЗЫК И ВРЕМЯ ---
LANGUAGE_CODE = 'ru-Ru'
TIME_ZONE = 'Asia/Bishkek'
USE_I18N = True
USE_TZ = True

# --- СТАТИКА И МЕДИА ---
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'assets']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# --- ПОЧТА (Brevo) ---
EMAIL_BACKEND = config("EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = config("EMAIL_HOST", default="smtp-relay.brevo.com")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="no-reply@mdsmart.kg")
EMAIL_TIMEOUT = 5

# --- ALLAUTH / GOOGLE SETTINGS ---
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_EMAIL_VERIFICATION = 'none'
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True

# --- ПЛАТЕЖИ ---
FREEDOM_PAY_MERCHANT_ID = config("FREEDOM_PAY_MERCHANT_ID", default="")
FREEDOM_PAY_SECRET_KEY = config("FREEDOM_PAY_SECRET_KEY", default="")

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'