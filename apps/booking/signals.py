from django.db.models.signals import pre_save
from django.dispatch import Signal
from django.dispatch import receiver

from apps.booking.const import ORDER_STATUS_WORK
from apps.booking.models import Order
from unlockers import settings

# 1. Определение сигналов
confirm_work_changed_signal = Signal()
partner_changed_signal = Signal()

print("Signal module imported!")


# 2. Создание обработчиков для сигналов

@receiver(pre_save, sender=Order)
def check_changes(sender, instance, **kwargs):
    if instance.pk:
        orig = Order.objects.get(pk=instance.pk)

        if orig.confirm_work != instance.confirm_work:
            confirm_work_changed_signal.send(sender=sender, instance=instance)

        if orig.partner_id != instance.partner_id:
            partner_changed_signal.send(sender=sender, instance=instance)


@receiver(confirm_work_changed_signal)
def handle_confirm_work_change(sender, instance, **kwargs):
    # Ваш код для обработки изменений confirm_work
    if instance.confirm_work == ORDER_STATUS_WORK.new:
        template_choice = settings.POSTIE_TEMPLATE_CHOICES.created_request
    else:
        template_choice = settings.POSTIE_TEMPLATE_CHOICES.employee_order

    print("Confirm work changed")
    # instance.send_notification_email_for_confirm_work()


@receiver(partner_changed_signal)
def handle_partner_change(sender, instance, **kwargs):
    # Ваш код для обработки изменений partner
    template_choice = settings.POSTIE_TEMPLATE_CHOICES.employee_order
    instance.send_notification_email()
    print("Partner changed")

# В методе save теперь можно удалить проверки, так как они теперь обрабатываются
