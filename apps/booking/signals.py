from constance import config
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
    print("signal send_email_after_order_change")
    try:
        if instance._state.adding is False:  # Это не новый объект
            if hasattr(instance, '_loaded_values'):  # проверяем, что pre_save_order сработал
                original_partner = instance._loaded_values['partner']
                if original_partner != instance.partner:
                    print("Partner changed")
                    if instance.partner:
                        print("Sending email to partner")
                        print(instance, config.ADMIN_EMAIL, instance.partner.email, instance.unique_path_field)

                        try:
                            send = send_custom_mail(
                                order=instance,
                                from_send=config.ADMIN_EMAIL,
                                to_send=instance.partner.email,
                                template_choice='send_partner',
                                unique_path=instance.unique_path_field
                                )
                            print(f"Send result: {send}")
                        except Exception as e:
                            print(f"Error occurred: {e}")
                    else:
                        print("Sending email to admin")
                        send_custom_mail(
                            order=instance,
                            from_send=config.ADMIN_EMAIL,
                            to_send=config.ADMIN_EMAIL,
                            template_choice='send_partner',
                            unique_path=instance.unique_path_field
                            )
    except Exception as e:
        print(f"Error occurred: {e}")
