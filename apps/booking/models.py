import random
import string

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils.choices import Choices

from apps.booking.const import ORDER_STATUS_WORK
from .senders import Sender

PAYMENT_STATUSES = Choices(
    ("paid", _("Paid")),
    ("no_paid", _("Not paid")),
)


class Order(models.Model):
    """Модель заказа"""
    unique_path_field = models.CharField(max_length=12, unique=True)  # Изменяем поле

    date_at = models.DateTimeField(
        verbose_name=_("Date at")
    )
    price = models.DecimalField(
        verbose_name=_("Price"),
        max_digits=10,
        decimal_places=2,
    )
    prepayment = models.DecimalField(
        verbose_name=_("Prepayment"),
        max_digits=10,
        decimal_places=2,
    )
    comment = models.TextField(
        verbose_name=_("Comment_"),
        null=True,
        blank=True,
    )
    responsible = models.ForeignKey(
        "booking.Employee",
        verbose_name=_("Responsible"),
        on_delete=models.SET_NULL,
        related_name="order",
        null=True,
        blank=True,
    )
    confirm_work = models.CharField(
        _("Confirm on work"), max_length=255,
        choices=ORDER_STATUS_WORK,
        default=ORDER_STATUS_WORK.new
    )
    name = models.CharField(
        verbose_name=_("Full name"),
        max_length=255,
        null=True,
        blank=True
    )
    car_registration = models.CharField(
        verbose_name=_('Car registration'),
        max_length=255,
        null=True,
        blank=True
    )
    ######
    car_year = models.IntegerField(
        verbose_name=_('Car year'),
        null=True,
        blank=True
    )
    car = models.ForeignKey(
        "cars.Car",
        verbose_name=_('Car'),
        on_delete=models.CASCADE,
        related_name='order_car',
        null=True,
        blank=True
    )

    service = models.ForeignKey(
        "request.ServiceVariation",
        verbose_name=_("Service"),
        on_delete=models.SET_NULL,
        null=True
    )
    ######
    phone = models.CharField(
        verbose_name=_("Phone"),
        max_length=255,
        null=True,
        blank=True,
    )
    address = models.CharField(
        verbose_name=_("Address"),
        max_length=255,
        null=True,
        blank=True,
    )
    post_code = models.CharField(
        verbose_name=_('Post code'),
        max_length=255,
        null=True,
        blank=True
    )
    #####
    distance = models.FloatField(
        verbose_name=_('Distance'),
        null=True,
        blank=True
    )
    #####
    # request = models.ForeignKey(
    #     "request.Request",
    #     verbose_name=_("Request"),
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=True
    # )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    partner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='partner_order',
        verbose_name=_("Partner"),
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")

    def __str__(self):
        return str(self.id)

    def is_paid(self):
        return (
            self.transactions
            .all()
            .filter(status=PAYMENT_STATUSES.paid)
            .exists()
        )

    def generate_unique_path(self):
        chars = string.ascii_letters + string.digits
        while True:
            unique_path = ''.join(random.choice(chars) for i in range(12))
            if not Order.objects.filter(unique_path_field=unique_path).exists():
                return unique_path

    def save(self, *args, **kwargs):
        # Если путь еще не создан, то генерируем его
        if not self.unique_path_field:
            self.unique_path_field = self.generate_unique_path()
        super().save(*args, **kwargs)

    def send_message(self):
        Sender(self).push()

    def send_message_admin(self):
        Sender(self).push_in_admin()


class Employee(models.Model):
    name = models.CharField(
        verbose_name=_("Name"),
        max_length=255,
    )
    email = models.CharField(
        verbose_name=_("Email"),
        max_length=255
    )

    default = models.BooleanField(
        verbose_name=_("Default"),
        default=False,
    )

    class Meta:
        verbose_name = _("Employee")
        verbose_name_plural = _("Employees")

    def __str__(self):
        return self.name

    def save(self, **kwargs):
        if self.default == True:
            Employee.objects.filter(default=True).update(default=False)
        super().save(**kwargs)


class OrderAttachments(models.Model):
    file = models.FileField(
        verbose_name=_("File"),
    )
    order = models.ForeignKey(
        "booking.Order",
        verbose_name=_("Order"),
        on_delete=models.CASCADE,
        related_name="attachments"
    )

    class Meta:
        verbose_name = _("Order attachment")
        verbose_name_plural = _("Order attachments")

    def __str__(self):
        return str(self.order)


class Transaction(models.Model):
    ref = models.CharField(
        verbose_name=_("Paypal ref id"),
        max_length=255,
    )
    status = models.CharField(
        verbose_name=_("Status"),
        choices=PAYMENT_STATUSES,
        default=PAYMENT_STATUSES.no_paid,
        max_length=255,
    )
    order = models.ForeignKey(
        "booking.Order",
        verbose_name=_("Order"),
        on_delete=models.CASCADE,
        related_name="transactions"
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = _("Transaction")
        verbose_name_plural = _("Transactions")
