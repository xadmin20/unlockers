from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User

from apps.booking.models import Order
from apps.partners.models import Withdraw
from apps.partners.const import TRANSACTIONS_STATUS


class Transactions(models.Model):

    partner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='partner_transactions',
        verbose_name=_("Partner"),
    )

    amount = models.DecimalField(
        verbose_name=_("Transaction amount"),
        max_digits=10,
        decimal_places=2,
    )

    balance = models.DecimalField(
        verbose_name=_("Balance after transactions"),
        max_digits=10,
        decimal_places=2,
    )
    
    type_transactions = models.PositiveSmallIntegerField(
        verbose_name=_("Type transactions"),
        choices=TRANSACTIONS_STATUS,
    )

    created_at = models.DateTimeField(
        verbose_name=_("Date create"),
        auto_now_add=True,
    )

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='order_income',
        verbose_name=_("Order"),
        blank=True,
        null=True,
    )

    withdraw = models.ForeignKey(
        Withdraw,
        on_delete=models.CASCADE,
        related_name='withdraw_invoice',
        verbose_name=_("Withdraw"),
        blank=True,
        null=True,
    )

    def __str__(self):
        return str(self.id)
    
    class Meta:
        verbose_name = _("Transaction")
        verbose_name_plural = _("Transactions")
