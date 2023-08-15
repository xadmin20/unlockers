from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import datetime, timedelta


class ProxyQuerySet(models.QuerySet):

    def valid(self):
        return self.filter(is_valid=True)

    def auto(self):
        return self.filter(is_manual=False)

    def manual(self):
        return self.filter(is_manual=True)


class Proxy(models.Model):
    host = models.CharField(
        verbose_name=_('Host'),
        max_length=255
    )
    is_valid = models.BooleanField(
        verbose_name=_('Is valid'),
        default=True
    )
    created_at = models.DateTimeField(
        verbose_name=_("Created at"),
        auto_now_add=True
    )
    is_manual = models.BooleanField(
        verbose_name=_("Is manual"),
        default=False
    )

    objects = ProxyQuerySet.as_manager()

    class Meta:
        verbose_name = _("Proxy")
        verbose_name_plural = _("Proxies")

    def __str__(self):
        return self.host

    def check_is_valid(self):
        return (
            self.is_valid 
            and self.created_at.replace(tzinfo=None) >= (datetime.now() - timedelta(hours=2))
        )
