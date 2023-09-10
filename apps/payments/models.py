import logging
import time

from django.db import models

from apps.booking.models import Order
from apps.sms.logic import _send_sms
from apps.sms.logic import send_custom_mail


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
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.order_id.unique_path_field

    def save(self, *args, **kwargs):
        try:
            if self.pk is not None:
                orig = Payment.objects.get(pk=self.pk)
                if orig.status != self.status:
                    total_paid = Payment.objects.filter(order_id=self.order_id).aggregate(models.Sum('amount'))[
                                     'amount__sum'] or 0
                    total_paid += float(self.amount)  # Добавляем текущий платеж к общей сумме платежей
                    order_price = self.order_id.price  # Общая стоимость заказа из модели Order
                    if total_paid == order_price / 2:
                        # Это предоплата
                        send_custom_mail(
                            order=self.order_id,
                            recipient_type='Customer',
                            template_choice='add_pay'
                            )
                        if self.order_id.partner:
                            time.sleep(2)
                            send_custom_mail(
                                order=self.order_id,
                                recipient_type='Worker',
                                template_choice='send_worker_new'
                                )
                            print('send_worker_new 6.6')
                        _send_sms(
                            phone=self.order_id.phone,
                            message='New payment received. Prepayment.'
                                    f' {self.order_id.unique_path_field} {self.amount}'
                            )

                    elif total_paid == order_price:
                        # Окончательный платеж
                        send_custom_mail(
                            order=self.order_id,
                            recipient_type='Customer',
                            template_choice='add_pay'
                            )
                        time.sleep(1)
                        _send_sms(
                            phone=self.order_id.phone, message='New payment received. Full payment.'
                                                               f'{self.order_id.unique_path_field} {self.amount}'
                            )

                        if self.order_id.partner:
                            time.sleep(1)
                            send_custom_mail(
                                order=self.order_id,
                                recipient_type='Worker',
                                template_choice='add_pay'
                                )

                    if self.status in ['partial', 'paid']:
                        # Отправляем смс клиенту
                        time.sleep(1)
                        _send_sms(
                            phone=self.order_id.phone,
                            message='The payment for the amount has arrived {self.amount},'
                                    f'by order: {self.order_id.unique_path_field}'
                            )
            super(Payment, self).save(*args, **kwargs)
        except Exception as e:
            print(e)
            logging.error(e)
