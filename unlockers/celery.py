# celery.py

import os

from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unlockers.settings')

app = Celery('unlockers')

app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматическое обнаружение и подключение всех задач приложения Django
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
