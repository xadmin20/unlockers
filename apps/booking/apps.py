from django.apps import AppConfig


class BookingConfig(AppConfig):
    name = 'apps.booking'

    def ready(self):
        # Указание на ваш модуль как на комментарий
        # module_name = "apps.booking.signals"
        # importlib.import_module(module_name)
        pass
