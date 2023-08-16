

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unlockers.settings')
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unlockers.settings.base')


application = get_wsgi_application()
