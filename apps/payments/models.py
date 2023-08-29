from django.db import models

from apps.booking.models import Order


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
