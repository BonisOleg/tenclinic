from pathlib import Path

from decouple import Csv, config
from django.templatetags.static import static

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config('SECRET_KEY', default='dev-insecure-key-change-in-production')

INSTALLED_APPS = [
    'unfold',
    'unfold.contrib.filters',
    'unfold.contrib.forms',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'tinymce',
    'django_htmx',
    'clinic',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
]

ROOT_URLCONF = 'config.urls'

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
                'clinic.context_processors.site_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'uk'
TIME_ZONE = 'Europe/Kyiv'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

TINYMCE_DEFAULT_CONFIG = {
    'height': 400,
    'plugins': 'link lists code',
    'toolbar': 'undo redo | bold italic | bullist numlist | link | code',
    'content_css': False,
    'skin': 'oxide',
}

UNFOLD = {
    'SITE_TITLE': 'TEN clinic',
    'SITE_HEADER': 'TEN clinic — Адмінпанель',
    'SITE_SYMBOL': 'local_hospital',
    'SITE_FAVICONS': [
        {
            'rel': 'icon',
            'type': 'image/svg+xml',
            'href': lambda request: static('images/favicon.svg'),
        },
    ],
    'SIDEBAR': {
        'show_search': True,
        'command_search': True,
        'show_all_applications': False,
        'navigation': [],
    },
}

SITE_BLOCKS_CACHE_KEY = 'ten_clinic_site_blocks'
SITE_BLOCKS_CACHE_TIMEOUT = 300

BOOKING_RATE_LIMIT = 3
BOOKING_RATE_WINDOW = 600

KEYCRM_API_URL = config('KEYCRM_API_URL', default='https://openapi.keycrm.app/v1')
KEYCRM_API_KEY = config('KEYCRM_API_KEY', default='')
KEYCRM_PIPELINE_ID = config('KEYCRM_PIPELINE_ID', default='')
KEYCRM_STATUS_NEW = config('KEYCRM_STATUS_NEW', default='')
KEYCRM_STATUS_PROCESSING = config('KEYCRM_STATUS_PROCESSING', default='')
KEYCRM_STATUS_CONFIRMED = config('KEYCRM_STATUS_CONFIRMED', default='')
KEYCRM_STATUS_REJECTED = config('KEYCRM_STATUS_REJECTED', default='')
KEYCRM_SOURCE_ID = config('KEYCRM_SOURCE_ID', default='')
KEYCRM_WEBHOOK_SECRET = config('KEYCRM_WEBHOOK_SECRET', default='')
KEYCRM_FIELD_DIRECTION = config('KEYCRM_FIELD_DIRECTION', default='LD_1001')
KEYCRM_FIELD_DOCTOR = config('KEYCRM_FIELD_DOCTOR', default='LD_1002')
KEYCRM_FIELD_COMMENT = config('KEYCRM_FIELD_COMMENT', default='LD_1004')
KEYCRM_FIELD_CONTACT = config('KEYCRM_FIELD_CONTACT', default='LD_1005')
