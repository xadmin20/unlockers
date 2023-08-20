import random
import string

from constance import config
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils.choices import Choices
from postie.shortcuts import send_mail

from apps.booking.const import ORDER_STATUS_WORK
from apps.booking.senders import Sender

PAYMENT_STATUSES = Choices(
    ("paid", _("Paid")),
    ("no_paid", _("Not paid")),
    ("part payment", _("Part payment")),
    )

template_choice = ''


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

    def has_confirm_work_changed(self):
        """Проверка изменился ли статус заказа"""
        if self.pk:
            orig = Order.objects.get(pk=self.pk)
            return orig.confirm_work != self.confirm_work
        return False

    def has_partner_changed(self):
        """Проверка изменился ли партнер заказа"""
        if self.pk:
            orig = Order.objects.get(pk=self.pk)
            return orig.partner_id != self.partner_id
        return False

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

        is_new = self._state.adding
        global template_choice
        confirm_work_changed = self.has_confirm_work_changed()
        partner_changed = self.has_partner_changed()
        super(Order, self).save(*args, **kwargs)

        # Теперь, после сохранения, проверяем изменились ли наши интересующие поля:
        if self.confirm_work == ORDER_STATUS_WORK.new:
            template_choice = settings.POSTIE_TEMPLATE_CHOICES.created_request
        else:
            template_choice = settings.POSTIE_TEMPLATE_CHOICES.employee_order

        if confirm_work_changed:
            print("Confirm work changed")
            template_choice = settings.POSTIE_TEMPLATE_CHOICES.employee_order

        if partner_changed:
            print("Partner changed")
            template_choice = settings.POSTIE_TEMPLATE_CHOICES.employee_order

        self.send_notification_email()

    def send_message(self):
        Sender(self).push()

    def send_message_admin(self):
        Sender(self).push_in_admin()

    def send_notification_email(self):
        # Функция отправки сообщения
        print("Try to send message")
        recipients = []
        # Если config.ADMIN_EMAIL это строка
        if isinstance(config.ADMIN_EMAIL, str):
            recipients.append(config.ADMIN_EMAIL)
        # Если config.ADMIN_EMAIL это список
        else:
            recipients.extend(config.ADMIN_EMAIL)

        if self.partner:
            recipients.append(self.partner.email)
        current_site = Site.objects.first()
        try:
            send_mail(
                template_choice,
                recipients,
                {
                    "id": str(self.id),
                    "date_at": self.date_at.strftime("%d.%m.%Y %H:%M"),
                    "name": self.name,
                    "contacts": self.phone,
                    "email": self.partner.email if self.partner else None,
                    "phone": self.phone,
                    "car_registration": self.car_registration,
                    "manufacture": self.car.manufacturer if self.car else None,
                    "car_model": self.car.car_model if self.car else None,
                    "car_year": self.car_year,
                    "distance": self.distance,
                    "service": self.service.title if self.service else None,
                    "price": self.price,
                    "post_code": self.post_code,
                    "link": f"{current_site}/link/{self.unique_path_field}",
                    "link_auto": f"{current_site}/link/{self.unique_path_field}"
                    }
                )
            print("Message sent successfully!")
        except Exception as e:
            print(f"Failed to send message: {e}")  # TODO: сделать отправку сообщения в СМС админу


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
