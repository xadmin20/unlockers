from django.db.models.signals import post_save
from django.db.models.signals import pre_save
from django.dispatch import receiver

from apps.booking.models import Order
from apps.sms.logic import send_custom_mail


@receiver(pre_save, sender=Order)
def pre_save_order(sender, instance, **kwargs):
    try:
        obj = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        pass
    else:
        instance._loaded_values = {}
        for field in instance._meta.fields:
            instance._loaded_values[field.name] = getattr(obj, field.name)


@receiver(post_save, sender=Order)
def send_email_after_order_change(sender, instance, **kwargs):
    """Отправка письма при изменении ордера"""
    print("SIGNAL: send_email_after_order_change")
    try:
        if not instance._state.adding:  # Это не новый объект
            if hasattr(instance, '_loaded_values'):  # Проверяем, что pre_save_order сработал

                original_status = instance._loaded_values['status']
                original_partner = instance._loaded_values['partner']

                # Проверка на изменение поля partner
                if original_partner != instance.partner:
                    print("SIGNAL: Partner changed")
                    recipient_type = "Worker" if instance.partner else "Customer"
                    template_choice = 'send_worker_new'

                    print(f"SIGNAL: Sending email to {recipient_type}")
                    send_custom_mail(
                        order=instance,
                        recipient_type=recipient_type,
                        template_choice=template_choice,
                        action='send_worker_new',
                        )

                # Проверка на изменение поля status
                if original_status != instance.status:
                    print(f"SIGNAL: Status changed to {instance.status}")

                    # Находим соответствующий шаблон для нового статуса
                    template_choice_for_status = {
                        'new': 'new_order',
                        'accepted': 'confirmed',
                        'en_route': 'template_for_en_route',
                        'arrived': 'template_for_arrived',
                        'completed': 'template_for_completed',
                        'paid': 'template_for_paid',
                        }.get(instance.status, 'default_template')

                    print(f"SIGNAL: Sending email for new status {instance.status}")

                    # Добавьте проверку, чтобы избежать повторной отправки писем
                    if not getattr(instance, '_email_sent_for_status_change', False):
                        send_custom_mail(
                            order=instance,
                            recipient_type='Worker',  # или другой тип получателя
                            template_choice=template_choice_for_status,
                            )
                        instance._email_sent_for_status_change = True  # Установите флаг

    except Exception as e:
        print(f"!!!Error occurred: {e}")
