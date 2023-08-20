from unlockers.celery import app

from .contrib import proxy_getter
from .models import Proxy


@app.task
def update_proxies():
    proxy_getter.update_proxies()


@app.task
def remove_proxies():
    Proxy.objects.auto().filter(is_valid=False).delete()
