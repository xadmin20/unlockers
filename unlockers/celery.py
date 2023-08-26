import os

from celery import Celery, schedules

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")

app = Celery("app")
app.config_from_object("django.conf:settings")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "update-proxies": {
        "task": "apps.proxy.tasks.update_proxies",
        "schedule": schedules.crontab(minute="*/30"),
        # "schedule": schedules.crontab(minute=0, hour="*/1"),
    },
    "remove-proxies": {
        "task": "apps.proxy.tasks.remove_proxies",
        "schedule": schedules.crontab(hour="*/12"),
        # "schedule": schedules.crontab(minute=0, hour="*/1"),
    },
}
app.conf.timezone = "UTC"
