import os
from datetime import timedelta
from pathlib import Path

import jinja2
from decouple import config
from django.contrib import sessions
from django.utils.translation import gettext_lazy as _
from django_jinja.builtins import DEFAULT_EXTENSIONS
from dotenv import load_dotenv

from .constance import *

# Build paths inside the project like this: BASE_DIR / 'subdir'.

BASE_DIR = Path(__file__).resolve().parent.parent

BASE_ROOT = BASE_DIR.parent.parent

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = 'django-insecure-^wza)-hfx%mnd))%#vcav#vomn-59ma_qvk8%^slg!eg__f^j!'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '138.68.160.203', 'carkeysstudio.co.uk']
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django_celery_beat',
    'django_celery_results',

    'constance',
    'seo',
    'ckeditor',
    'rangefilter',
    'solo',
    'rest_framework',
    'rest_framework.authtoken',
    # 'rest_auth',
    'parler',
    'django_jinja',
    'rosetta',
    'script_pattern',
    'vuejs_translate',
    'des',
    'filer',
    'robots',
    'easy_thumbnails',

    'apps.proxy',
    'apps.cars',
    'apps.request',
    'apps.booking.apps.BookingConfig',
    'apps.pages',
    'apps.blog',
    'apps.sms',
    'apps.partners',
    'apps.worker',
    'apps.payments',

]

# Application definition


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'unlockers.urls'

TEMPLATES = [
    {
        'BACKEND': 'django_jinja.backend.Jinja2',
        'NAME': 'jinja2',
        'APP_DIRS': True,
        'DIRS': ['markup/templates'],
        'OPTIONS': {
            'environment': 'shared.env.jinja2.environment',
            'match_extension': '.jinja',
            'newstyle_gettext': True,
            'auto_reload': True,
            'undefined': jinja2.Undefined,
            'debug': True,
            'filters': {},
            'globals': {},
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'constance.context_processors.config',
            ],
            'extensions': DEFAULT_EXTENSIONS,
            "bytecode_cache": {
                "name": "default",
                "backend": "django_jinja.cache.BytecodeCache",
                "enabled": True,
            },
        },
    },
    {
        'DIRS': ['markup/templates'],
        'APP_DIRS': True,
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
                'django.contrib.auth.context_processors.auth',
            ],
        },
    },

]

WSGI_APPLICATION = 'unlockers.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
#
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'ublockers',
#         'USER': 'clinic_user_db',
#         'PASSWORD': 'ublockers_pass',
#         'HOST': '138.68.160.203',  # Может потребоваться изменить, если база данных находится на другом сервере
#         'PORT': '',  # По умолчанию используется порт PostgreSQL (5432)
#     }
# }
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'clinic',
#         'USER': 'clinic_user_db',
#         'PASSWORD': 'clinic_pass',
#         'HOST': 'localhost',
#         'PORT': '5432',
#     }
# }


CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',  # Указывается адрес Redis
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Если вы хотите использовать Redis для хранения сессий:
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
SITE_ID = 1

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'markup/static')
]
MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

customColorPalette = [
    {
        'color': 'hsl(4, 90%, 58%)',
        'label': 'Red'
    },
    {
        'color': 'hsl(340, 82%, 52%)',
        'label': 'Pink'
    },
    {
        'color': 'hsl(291, 64%, 42%)',
        'label': 'Purple'
    },
    {
        'color': 'hsl(262, 52%, 47%)',
        'label': 'Deep Purple'
    },
    {
        'color': 'hsl(231, 48%, 48%)',
        'label': 'Indigo'
    },
    {
        'color': 'hsl(207, 90%, 54%)',
        'label': 'Blue'
    },
]

SEO_MODELS = [
    'pages.mainPage',
    'pages.typical',
    'blog.post',
]

SEO_VIEWS_CHOICES = (
    ('blog', 'Blog page'),
)

THUMBNAIL_HIGH_RESOLUTION = True

CKEDITOR_CONFIGS = {
    'default': {
        'allowedContent': True,  # Это позволит вставлять любой HTML-контент
        'toolbar': 'Custom',
        'toolbar_Custom': [
            [
                "Styles",
                "Format",
                "Bold",
                "Italic",
                "Underline",
                "Strike",
                "SpellChecker",
                "Undo",
                "Redo",
            ],
            ["Link", "Unlink", "Anchor"],
            ["Blockquote", "Image", "Flash", "Table", "HorizontalRule"],
            ["TextColor", "BGColor"],
            ["Smiley", "SpecialChar"],
            ["Source"],
        ]
    },
}

SEO_DEBUG_MODE = False
ROBOTS_USE_SCHEME_IN_HOST = True

STATICFILES_STORAGE = 'markup.storages.DjsManifestStaticFilesStorage'

POSTIE_INSTANT_SEND = True
POSTIE_TEMPLATE_CHOICES = Choices(
    ("created_request", _("Created request")),
    ("employee_order", _("Message to employee about order creation")),
    ("employee_order_admin", _("Message to employee about order attach to him(from admin)")),
    ("confirm_order", _("Message to admin about confirm order by employer")),
    ("quote_created", _("Message to admin about quote creation")),
    ("password_recovery_user", _("Message to password recovery")),
    ("send_test_email", _("Message to test email")),
    ("change_email", _("Message to change email")),
    ("send_withdraw_admin", _("Message to admin on withdraw")),
)

POSTIE_TEMPLATE_CONTEXTS = {
    "created_request": {
        "name": _("User name"),
        "contacts": _("Contacts"),
        "email": _("Email"),
        "phone": _("Phone"),
        "link": _("Link to request"),
        "id": _("Request id"),
        "car_registration": _("Car registration"),
        "manufacture": _("Car manufacturer"),
        "car_model": _("Car model"),
        "car_year": _("Car year"),
        "post_code": _("Post code"),
        "distance": _("Distance"),
        "service": _("Service"),
        "price": _("Price"),
        "link_auto": _("Link to auto"),
    },
    "employee_order": {
        "date_at": _("Date at"),
        "price": _("Price"),
        "prepayment": _("Prepayment"),
        "comment": _("Comment"),
        "responsible": _("Responsible"),
        "name": _("Name"),
        "car_registration": _("Car registration"),
        "manufacture": _("Car manufacturer"),
        "car_model": _("Car model"),
        "car_year": _("Car year"),
        "phone": _("Phone"),
        "address": _("Address"),
        "post_code": _("Post code"),
        "link": _("Link to request"),

        "link_confirm": _("Link for confirm order"),
        "link_refused": _("Link for refused order"),
    },
    "employee_order_admin": {
        "date_at": _("Date at"),
        "price": _("Price"),
        "prepayment": _("Prepayment"),
        "comment": _("Comment"),
        "responsible": _("Responsible"),
        "name": _("Name"),
        "car_registration": _("Car registration"),
        "phone": _("Phone"),
        "address": _("Address"),
        "post_code": _("Post code"),
        "link": _("Link to request"),
        "link_confirm": _("Link for confirm order"),
        "link_refused": _("Link for refused order"),
    },
    "confirm_order": {
        "responsible": _("Responsible"),
        "link": _("Link to order"),
        "status_confirm": _("Status confirm order in work"),
    },
    "quote_created": {
        "car_registration": _("Car registration code"),
        "service": _("Service name"),
        "post_code": _("Postal code"),
        "price": _("Price"),
        "phone": _("Phone"),
        "car_model": _("Car model"),
        "manufacturer": _("Manufacturer"),
        "request_link": _("Request link"),
        "quote_link": _("Quote link"),
        "created_at": _("Created at"),
        "id": _("Quote id"),
        "request_id": _("Request id"),
    },
    'password_recovery_user': {
        'var_url_recovery': _("URL Recovery"),
    },
    'change_email': {
        'var_url_recovery': _("URL Change email"),
    },
    'send_withdraw_admin': {
        'link_admin': _("Link to admin"),
    },
}

POSTIE_HTML_ADMIN_WIDGET = {
    "widget": "CKEditorWidget",
    "widget_module": "ckeditor.widgets",
}

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'nickolayvan@gmail.com'
EMAIL_HOST_PASSWORD = 'sjyrxlucgounjnma'

APPEND_SLASH = True

LOGGING_DIR = os.path.join(BASE_DIR, 'logs')  # Путь, где будут храниться лог-файлы

if not os.path.exists(LOGGING_DIR):
    os.makedirs(LOGGING_DIR)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} {levelname} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{asctime} {levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(LOGGING_DIR, 'debug.log'),
            'when': 'midnight',  # Создать новый файл лога каждую полночь
            'interval': 1,  # Интервал в днях
            'backupCount': 30,  # Сколько файлов логов сохранять
            'formatter': 'verbose',  # Используйте verbose форматтер
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# PAYPAL
PAYPAL_CLIENT_ID = 'AZJy7hCDgj4dgdyotn6ZjLQa1Y1LqguLCXoP9Aias72Mkur_EG_pcK6ygIrW'
PAYPAL_CLIENT_SECRET = 'EKopERAVPsd7j4XzZtERxV5l-_7HTSS_UAMjBsVqtIw7jv0x1ySBk_P7TAHX'
PAYPAL_MODE = 'sandbox'  # для тестирования; 'live' для реальных транзакций

SMS_SEND_MODE = 'test'  # todo 'production' or 'test'

# settings.py

# Включите поддержку асинхронных задач
# CELERY_BROKER_URL = 'redis://localhost:6379/0'  # Замените на адрес вашего брокера (Redis, RabbitMQ, и т.д.)
#
# # Настройки Celery
# CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'  # Замените на адрес вашего брокера
#
# # Настройки Celery (по желанию)
# CELERY_TIMEZONE = 'UTC'
