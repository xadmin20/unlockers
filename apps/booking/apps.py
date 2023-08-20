from django.apps import AppConfig


class BookingConfig(AppConfig):
    name = 'apps.booking'

    def ready(self):
        # Указание на ваш модуль как на комментарий
        # print("BookingConfig ready")
        pass
