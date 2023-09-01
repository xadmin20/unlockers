from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils.choices import Choices
from solo.models import SingletonModel

REQUEST = "request"
ORDER_PAYED = "order_payed"
TEMPLATES = Choices(
    (REQUEST, _("After request")),
    (ORDER_PAYED, _("After order payed")),

    )

CONTEXT = {
    REQUEST: {
        "car_registration": _("Car registration"),
        "post_code": _("Post code"),
        "service": _("Service name"),
        "price": _("Price"),
        "prepayment": _("Prepayment"),
        "link": _("Link to order creation"),
        },
    ORDER_PAYED: {
        "car_registration": _("Car registration"),
        "post_code": _("Post code"),
        "service": _("Service name"),
        "price": _("Price"),
        "prepayment": _("Prepayment"),
        "link": _("Link to order detail page"),
        }
    }


class Config(SingletonModel):
    is_phone_mechanic = models.BooleanField(
        verbose_name=_("Is phone mechanic"),
        default=True
        )
    timeout = models.IntegerField(
        verbose_name=_("Timeout"),
        default=10
        )

    class Meta:
        verbose_name = _("Config")
        verbose_name_plural = _("Config")

    def __str__(self):
        return str(_("Config"))


class SmsTemplate(models.Model):
    template = models.CharField(
        verbose_name=_("Template"),
        max_length=255,
        choices=TEMPLATES
        )
    message = models.TextField(
        verbose_name=_("Message 1")
        )
    message2 = models.TextField(
        verbose_name=_("Message 2"),
        default="",
        blank=True
        )
    message3 = models.TextField(
        verbose_name=_("Message 3"),
        default="",
        blank=True
        )

    class Meta:
        verbose_name = _("Sms template")
        verbose_name_plural = _("Sms templates")

    def __str__(self):
        return self.template


class SmsMessage(models.Model):
    message = models.TextField(
        verbose_name=_("Message")
        )
    message2 = models.TextField(
        verbose_name=_("Message"),
        default=""
        )
    message3 = models.TextField(
        verbose_name=_("Message"),
        default=""
        )
    to_phone = models.CharField(
        verbose_name=_("To phone"),
        max_length=255,
        )
    created_at = models.DateTimeField(
        verbose_name=_("Created at"),
        auto_now_add=True,
        )
    log = models.TextField(
        verbose_name=_("Log")
        )
    template = models.CharField(
        verbose_name=_("Template"),
        max_length=255,
        choices=TEMPLATES
        )
    is_success = models.BooleanField(
        verbose_name=_("Is success"),
        default=False
        )

    class Meta:
        verbose_name = _("Sms message")
        verbose_name_plural = _("Sms messages")

    def __str__(self):
        return self.template


def is_phone_mechanic():
    return config.is_phone_mechanic if (config := Config.objects.first()) else False


def get_timeout_amount():
    return config.timeout if (config := Config.objects.first()) else False


class EmailTemplate(models.Model):
    name = models.CharField(max_length=100)
    subject = models.CharField(max_length=200)
    html_content = models.TextField()

    def __str__(self):
        return self.name


class SMSSendHistory(models.Model):
    phone_number = models.CharField(max_length=20)
    message = models.TextField()
    sent_datetime = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=False)  # Добавленное поле

    def __str__(self):
        return f"{self.phone_number} - {self.sent_datetime}"
