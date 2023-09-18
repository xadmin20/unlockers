import logging

from constance import config
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.db import models
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _
from model_utils.choices import Choices

from apps.booking.const import ORDER_STATUS_WORK
from apps.sms.logic import _send_sms
from apps.sms.logic import send_custom_mail

logger = logging.getLogger(__name__)

PAYMENT_STATUSES = Choices(
    ("paid", _("Paid")),
    ("no_paid", _("Not paid")),
    ("part payment", _("Part payment")),
)

STATUS_CHOICES = (
    ('new', 'New'),
    ('accepted', 'Accepted'),
    ('en_route', 'En Route'),
    ('arrived', 'Arrived'),
    ('completed', 'Completed'),
    ('paid', 'Paid'),
)
template_choice = ''


class Order(models.Model):
    """Модель заказа"""
    unique_path_field = models.CharField(max_length=12, unique=True)  # Изменяем поле
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        null=True,
        blank=True
    )
    date_at = models.DateTimeField(
        verbose_name=_("Date at")
    )
    price = models.DecimalField(
        verbose_name=_("Price"),
        max_digits=10,
        decimal_places=2,
        default=0
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
    worker = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='worker_order',
        verbose_name=_("Worker"),
        null=True,
        default=config.MAIN_WORKER_ID,
    )

    partner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='partner_order',
        verbose_name=_("Partner"),
        null=True,
        blank=True
    )

    class Meta:

        verbose_name = _("Order")
        verbose_name_plural = _("Orders")

    def __str__(self):
        return str(self.id)

    def is_paid(self):
        return self.transactions.all().filter(status=PAYMENT_STATUSES.paid).exists()

    def generate_unique_path_field(self):
        unique_path = get_random_string(length=12)
        while Order.objects.filter(unique_path_field=unique_path).exists():
            unique_path = get_random_string(length=12)
        return unique_path

    def save(self, *args, **kwargs):
        original_fields = None
        logger.debug("Method save in Order")
        print(f"Method save in Order: {self.pk}")

        if not self.unique_path_field:
            self.unique_path_field = self.generate_unique_path_field()
            print(f"Method save in Order: {self.pk} unique_path_field: {self.unique_path_field}")

        is_new = self._state.adding
        print(f"Method save in Order: {self.pk} is_new: {is_new}")

        if not is_new:
            logger.debug("Not new Order")
            orig = Order.objects.get(pk=self.pk)
            original_fields = {field.name: getattr(orig, field.name) for field in self._meta.fields}
            print(f"Method save in Order: {self.pk} original_fields: {original_fields}")

        if not is_new:
            logger.debug("Changes in Order not new")
            changes = {field.name: {'old': original_fields[field.name], 'new': getattr(self, field.name)}
                       for field in self._meta.fields if original_fields[field.name] != getattr(self, field.name)}

            changes.pop('partner', None)
            logger.debug(f"Changes after popping 'partner': {changes}")

            recipient_type = 'Worker' if self.partner else 'Customer'
            print(f"Method save in Order: {self.pk} recipient_type: {recipient_type}")

            if changes and not (len(changes) == 1 and 'car_year' in changes) and 'unique_path_field' not in changes:
                logger.debug(f"Sending email because changes: {changes}")
                send_custom_mail(
                    order=self,
                    recipient_type=recipient_type,
                    template_choice='change_order',
                    changes=changes
                )
                print(f"Method save in Order: {self.pk} Sending email because changes: {changes}")
            elif self.status == 'paid':
                _send_sms(
                    phone=config.ADMIN_PHONE,
                    message=f"Order {self.id} is paid "
                            f"https://{Site.objects.last()}/link/{self.unique_path_field}"
                )
                print(f"Method save in Order: {self.pk} Order {self.id} is paid ")

        elif is_new:
            logger.debug("New Order")
            UserModel = get_user_model()
            try:
                self.partner = UserModel.objects.get(pk=config.MAIN_WORKER_ID)
                logger.debug(f"New Order with a partner, sending email to partner: {self.partner}")
                print(f"Method save in Order: {self.pk} New Order with a partner,"
                      f" sending email to partner: {self.partner}")

                send_custom_mail(
                    order=self,
                    template_choice='send_worker_new',
                    recipient_type='Worker',
                    action="new_order",
                )
                print(f"Method save in Order: {self.pk} New Order with a partner,"
                      f" sending email to partner: {self.unique_path_field}")
            except UserModel.DoesNotExist:
                logger.debug("New Order without a partner, sending email to admin")
                print(f"Method save in Order: {self.pk} New Order without a partner,")
                send_custom_mail(
                    order=self,
                    template_choice='new_order',
                    recipient_type='Customer',
                    action='send_worker_new',
                )
                print(f"Method save in Order: {self.pk} New Order without a partner,"
                      f" sending email to admin")
                site = Site.objects.last()
                _send_sms(
                    phone=self.phone,
                    message=f"New Order without a partner, "
                            f"sending email to admin https://{site}/link/{self.unique_path_field}"
                )
        super(Order, self).save(*args, **kwargs)


class Employee(models.Model):
    """Модель сотрудника"""
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
    """Модель вложения к заказу"""
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
