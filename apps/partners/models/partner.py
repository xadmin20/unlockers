from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User


class Partner(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("Partner"),
    )

    company_name = models.CharField(
        verbose_name=_("Company name"),
        max_length=100,
        blank=True,
    )

    phone = models.CharField(
        verbose_name=_("Phone"),
        max_length=255,
        blank=True,
    )

    balance = models.DecimalField(
        verbose_name=_("Balance"),
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    change_email = models.EmailField(
        verbose_name=_("Change email"),
        blank=True,
    )

    class Meta:
        verbose_name = _("Partner")
        verbose_name_plural = _("Partners")

    def __str__(self):
        return str(self.id)