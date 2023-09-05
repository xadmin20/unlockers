import time

from constance import config
from django.db import models

from apps.booking.models import Order
from apps.sms.logic import _send_sms


class Payment(models.Model):
    """Модель для хранения платежей"""
    order_id = models.ForeignKey(Order, related_name='payments', on_delete=models.CASCADE)
    payment_id = models.CharField(max_length=100)
    payer_id = models.CharField(max_length=100)
    status = models.CharField(
        max_length=50, choices=[('unpaid', 'Не оплачено'), ('partial', 'Частично оплачено'),
                                ('paid', 'Оплачено')], default='unpaid'
        )
    created_at = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)  # поле для хранения суммы платежа

    def __str__(self):
        return self.order_id.unique_path_field

    def save(self, *args, **kwargs):
        # Если это новый объект, self.pk будет None
        if self.pk is not None:
            orig = Payment.objects.get(pk=self.pk)
            if orig.status != self.status:
                if self.status in ['partial', 'paid']:
                    _send_sms(
                        config.PHONE, f'sms_payment_success '
                                      f'{self.order_id.unique_path_field} {self.amount}'
                        )
                    time.sleep(5)
                    _send_sms(phone=self.order_id.phone, message='sms_payment_success_customer')

        super(Payment, self).save(*args, **kwargs)
