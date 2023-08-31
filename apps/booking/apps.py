from django.apps import AppConfig
from django.db.models.signals import post_save


class BookingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.booking'

    def ready(self):
        # Импорт внутри метода, чтобы избежать циклического импорта
        from . import signals
        from apps.booking.models import Order
        # Подключение сигнала
        post_save.connect(signals.send_email_after_order_change, sender=Order)
