import os
from datetime import timedelta
from pathlib import Path

import jinja2
from decouple import config
from django.utils.translation import gettext_lazy as _
from django_jinja.builtins import DEFAULT_EXTENSIONS

from .constance import *

# Build paths inside the project like this: BASE_DIR / 'subdir'.

BASE_DIR = Path(__file__).resolve().parent.parent

BASE_ROOT = BASE_DIR.parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-^wza)-hfx%mnd))%#vcav#vomn-59ma_qvk8%^slg!eg__f^j!'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']
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
    'postie',
    'constance',
    'seo',
    'ckeditor',
    'rangefilter',
    'solo',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_auth',
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
    'order',
    'apps.worker',

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
        'LOCATION': 'redis://adminton.ru:6379/2',  # Указана база данных 1, измените при необходимости
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PASSWORD': 'valenok',  # Ваш пароль от Redis
            'KEY_PREFIX': 'aiogrambot:currency'  # Ваш префикс для ключей
            }
        }
    }

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

# DATABASE_ROUTERS = ['markup.route_db.DemoRouter']
# DATABASE_APPS_MAPPING = {'cars': 'shared_db'}

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

# ROSETTA_SHOW_AT_ADMIN_PANEL = True

# REST_FRAMEWORK = {
#     'DEFAULT_METADATA_CLASS': 'standards.drf.metadata.FieldsetMetadata',
#     'DEFAULT_PARSER_CLASSES': (
#         'standards.drf.parsers.CamelCaseORJSONParser',
#         'djangorestframework_camel_case.parser.CamelCaseFormParser',
#         'djangorestframework_camel_case.parser.CamelCaseMultiPartParser',
#     ),
#     'DEFAULT_RENDERER_CLASSES': (
#         'standards.drf.renderers.CamelCaseORJSONRenderer',
#         'djangorestframework_camel_case.render.CamelCaseBrowsableAPIRenderer',
#     ),
#     'EXCEPTION_HANDLER': 'standards.drf.handlers.exception_handler',
#
# }

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'nickolayvan@gmail.com'
EMAIL_HOST_PASSWORD = 'sjyrxlucgounjnma'
APPEND_SLASH = True
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
            },
        'simple': {
            'format': '{levelname} {message}',
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
            'class': 'logging.FileHandler',
            'filename': os.path.join(os.path.dirname(__file__), 'django.log'),
            'formatter': 'verbose',
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

# CELERY_BROKER_URL = 'redis://:valenok@adminton.ru:6379/1'  # todo заменить на настоящий сервер
CELERY_RESULT_BACKEND = "django-db"
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_BEAT_SCHEDULE = {
    'check_sms_server': {
        'task': 'apps.booking.tasks.check_server_task',
        'schedule': timedelta(minutes=1),
        },
    }
CELERY_BROKER_URL = config('CELERY_BROKER_REDIS_URL', default='redis://:valenok@adminton.ru:6379')
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers.DatabaseScheduler'
