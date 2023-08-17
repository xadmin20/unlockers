from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.booking.const import ORDER_STATUS_WORK
from apps.booking.models import Order
from unlockers import settings

print("Signal module imported!")


@receiver(post_save, sender=Order)
def post_save_order(sender, instance, created, **kwargs):
    print("post_save_order triggered!")
    if instance.pk:  # Это не новый объект, значит, это обновление
        old_instance = Order.objects.get(pk=instance.pk)

    if created:  # Если это новый объект
        instance.send_notification_email(template_choice=settings.POSTIE_TEMPLATE_CHOICES.created_request)
        print("post_save_order created!")
    else:  # Это обновление
        old_instance = Order.objects.get(pk=instance.pk)

        # Проверяем, изменилось ли поле Partner
        if old_instance.partner != instance.partner:
            if instance.partner:
                instance.send_notification_email(template_choice=settings.POSTIE_TEMPLATE_CHOICES.employee_order)
                print("post_save_order employee_order!")

        # Проверяем, изменилось ли поле confirm_work
        if old_instance.confirm_work != instance.confirm_work:
            if instance.confirm_work == ORDER_STATUS_WORK.confirm:
                instance.send_notification_email(template_choice=settings.POSTIE_TEMPLATE_CHOICES.confirm_order)

        # Добавьте здесь другие условия для проверки других полей и отправки соответствующих уведомлений.

        # Например, если у вас есть поле `address` и вы хотите проверить его создание:
        if not old_instance.address and instance.address:
            instance.send_notification_email(template_choice=settings.POSTIE_TEMPLATE_CHOICES.quote_created)

        # По аналогии можно добавить другие условия для других шаблонов.
