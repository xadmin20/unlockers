from constance import config
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.db import models
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _
from model_utils.choices import Choices

from apps.booking.const import ORDER_STATUS_WORK
from apps.sms.logic import send_custom_mail
from apps.sms.logic import send_sms_admin

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

    def generate_unique_path_field(self):
        unique_path = get_random_string(length=12)
        while Order.objects.filter(unique_path_field=unique_path).exists():
            unique_path = get_random_string(length=12)
        return unique_path

    def save(self, *args, **kwargs):
        # If the unique_path_field is empty, generate a unique value for it
        if not self.unique_path_field:
            self.unique_path_field = self.generate_unique_path_field()

        is_new = self._state.adding

        # Store the original field values
        if not is_new:
            orig = Order.objects.get(pk=self.pk)
            original_fields = {field.name: getattr(orig, field.name) for field in self._meta.fields}

        # Save the current object
        super(Order, self).save(*args, **kwargs)

        # Check if any changes were made
        if not is_new:
            changes = {}
            for field in self._meta.fields:
                old_value = original_fields[field.name]
                new_value = getattr(self, field.name)
                if old_value != new_value:
                    changes[field.name] = {'old': old_value, 'new': new_value}

            changes.pop('partner', None)
            print("Changes after popping 'partner': ", changes)

            # Если после этого остались другие изменения, отправляем письмо
            if changes:
                if (len(changes) == 1 and 'car_year' in changes) or 'unique_path_field' in changes:
                    print("Changes only in 'car_year' or 'unique_path_field', not sending email")
                else:
                    print("Sending email because changes: ", changes)
                    send_custom_mail(
                        order=self,
                        from_send=f'{config.ADMIN_EMAIL}',
                        to_send=f'{config.ADMIN_EMAIL}',
                        template_choice='change_order',
                        unique_path=self.unique_path_field,
                        changes=changes
                        )

        # If the order is new, send an email
        elif is_new:
            try:
                print("booking.models.Order.save() is_new=True")
                send_sms_admin(self, action='created')
                print("Try to send SMS message created")
                send_custom_mail(
                    order=self,
                    from_send=f'{config.ADMIN_EMAIL}',
                    to_send=f'{config.ADMIN_EMAIL}',
                    template_choice='new_order',
                    unique_path=self.unique_path_field
                    )
            except Exception as e:
                print(f"Error occurred: {e}")

    # send_partner
    def send_notification_email(self, changes):
        print("Try to send message")
        site = Site.objects.get_current()
        subject = f"Изменения в заказе {self.id}"
        message = "Изменения: \n"
        for field, values in changes.items():
            message += (f"{field} изменилось с {values['old']} на {values['new']}\n")

        message += f"Ссылка на заказ: http://{site.domain}/admin/booking/order/{self.id}/change/\n" \
                   f"или http://{site.domain}/link/{self.unique_path_field}\n"
        try:
            sent = send_mail(subject, message, "nickolayvan@gmail.com", ["xadmin@bk.ru"])
            print(f"Number of emails sent: {sent}")
        except Exception as e:
            print(f"Error occurred: {e}")  # TODO: сделать отправку сообщения в СМС админу


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
