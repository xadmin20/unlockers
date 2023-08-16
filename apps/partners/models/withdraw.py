from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User

from apps.partners.const import WITHDRAW_STATUS


class Withdraw(models.Model):

    partner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='partner_withdraw',
        verbose_name=_("Partner"),
    )

    amount = models.DecimalField(
        verbose_name=_("Withdraw amount"),
        max_digits=10,
        decimal_places=2,
    )

    attachment_file = models.FileField(
        verbose_name=_("Attachment file"),
        upload_to='invoices/%Y/%m/%d/'
    )

    created_at = models.DateTimeField(
        verbose_name=_("Date create"),
        auto_now_add=True,
    )

    status = models.PositiveSmallIntegerField(
        verbose_name=_("Status"),
        choices=WITHDRAW_STATUS,
        default=WITHDRAW_STATUS.not_paid,
    )

    comment = models.TextField(
        verbose_name=_("Comment"),
        blank=True,
        null=True,
    )

    def __str__(self):
        return str(self.id)
    
    class Meta:
        verbose_name = _("Withdraw")
        verbose_name_plural = _("Withdraws")
