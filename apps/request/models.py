from _decimal import Decimal
from ckeditor.fields import RichTextField
from constance import config
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from model_utils.choices import Choices

from apps.booking.models import Order
from apps.cars.models import Car

REQUEST_TYPES = Choices(
    ('quote', _('Quote')),
    ('order', _('Order')),
    )

STATUSES = Choices(
    ('pending', _('Pending')),
    ('is_work', _('In work')),
    ('done', _('Done')),
    )

SERVICE_VARIATIONS = Choices(
    ("static_distance", _('Static plus distance')),
    ("car_distance", _('Car price plus distance')),
    ("static", _('Static')),
    ("else", _('Something else')),
    )


class Request(models.Model):
    """Request model"""
    _STATUSES = STATUSES
    unique_path_field = models.CharField(max_length=200, blank=True, null=True)
    car_registration = models.CharField(
        verbose_name=_('Car registration'),
        max_length=255
        )
    car_year = models.IntegerField(
        verbose_name=_('Car year'),
        null=True,
        blank=True
        )
    car = models.ForeignKey(
        "cars.Car",
        verbose_name=_('Car'),
        on_delete=models.CASCADE,
        related_name='request',
        null=True,
        blank=True
        )

    service = models.ForeignKey(
        "request.ServiceVariation",
        verbose_name=_('Service'),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        )
    post_code = models.CharField(
        verbose_name=_('Post code'),
        max_length=255
        )
    price = models.DecimalField(
        verbose_name=_('Price'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
        )
    distance = models.FloatField(
        verbose_name=_('Distance'),
        null=True,
        blank=True
        )
    name = models.CharField(
        verbose_name=_("Full name"),
        max_length=255,
        null=True
        )
    contacts = models.CharField(
        verbose_name=_("Contacts"),
        max_length=255,
        null=True
        )
    phone = models.CharField(
        verbose_name=_("Phone"),
        max_length=255,
        blank=True,
        null=True
        )
    email = models.CharField(
        verbose_name=_("Email"),
        max_length=255,
        null=True
        )
    comment = models.TextField(
        verbose_name=_("Comment"),
        null=True,
        blank=True,
        )
    status = models.CharField(
        verbose_name=_('Status'),
        choices=STATUSES,
        default=STATUSES.pending,
        max_length=255
        )
    created_at = models.DateTimeField(
        verbose_name=_('Created at'),
        auto_now_add=True
        )

    class Meta:
        ordering = ('-pk',)
        verbose_name = _('Request')
        verbose_name_plural = _('Requests')

    def __str__(self):
        return self.car_registration

    def save(self, is_calculate_price=False, *args, **kwargs):
        """Save method"""
        is_new_record = not self.pk
        if is_calculate_price and self.id:
            from .contrib import calculate_price, calculate_distance_price
            car_year = self.car.years.all().filter(
                year_from__lte=self.car_year,
                year_to__gte=self.car_year
                ).first()
            self.distance, distance_price = calculate_distance_price(self.post_code)
            self.price = calculate_price(
                service=self.service,
                car_year=car_year,
                distance=self.distance,
                distance_price=distance_price,
                )

        super(Request, self).save(*args, **kwargs)

        # Если это новая запись, создайте запись в Order
        if is_new_record:
            try:
                order = Order.objects.create(
                    unique_path_field=self.unique_path_field,
                    date_at=timezone.now(),
                    price=self.price,
                    prepayment=0.00,
                    car_registration=self.car_registration,
                    car_year=self.car_year,
                    car=self.car,
                    service=self.service,
                    post_code=self.post_code,
                    phone=self.phone,
                    distance=self.distance
                    )
            except Exception as e:
                print(f"Error creating order: {e}")
                # Если произошла ошибка при создании объекта, установите price по умолчанию 0
                order = Order.objects.create(
                    unique_path_field=self.unique_path_field,
                    date_at=timezone.now(),
                    price=0.00,  # Устанавливаем значение по умолчанию
                    prepayment=0.00,
                    car_registration=self.car_registration,
                    car_year=self.car_year,
                    car=self.car,
                    service=self.service,
                    post_code=self.post_code,
                    phone=self.phone,
                    distance=self.distance
                    )
            # Теперь вы можете работать с объектом 'order' и делать с ним что угодно, например:
            order.save()

    @property
    def car_model(self):
        if self.car:
            return self.car.car_model
        return '-'

    @property
    def manufacturer(self):
        if self.car:
            return self.car.manufacturer
        return '-'

    @property
    def manufactured(self):
        if self.car:
            return self.car.all_years
        return '-'

    @property
    def prepayment(self):
        return Decimal(config.PREPAYMENT) * Decimal(self.price) / 100 if self.price else 0


class ServiceVariation(models.Model):
    title = models.CharField(
        verbose_name=_('Title'),
        max_length=255
        )
    variation = models.CharField(
        verbose_name=_('Variation'),
        max_length=255,
        choices=SERVICE_VARIATIONS
        )
    price = models.FloatField(
        verbose_name=_('Price'),
        null=True,
        blank=True
        )
    ordering = models.IntegerField(
        verbose_name=_('Ordering'),
        default=0,
        blank=True,
        )
    # Fore displaying
    image = models.ImageField(
        verbose_name=_("Image"),
        null=True
        )
    title_style = RichTextField(
        verbose_name=_("Title styled"),
        null=True
        )
    description = RichTextField(
        verbose_name=_("Description"),
        null=True
        )
    is_display = models.BooleanField(
        verbose_name=_("Is displaying on main page"),
        default=True
        )
    updated_at = models.DateTimeField(
        _("Updated at"), default=timezone.now
        )

    class Meta:
        ordering = ('ordering',)
        verbose_name = _('Service variation')
        verbose_name_plural = _('Service variations')

    def __str__(self):
        return self.title

    def save(self, **kwargs):
        self.updated_at = timezone.now()
        super().save(**kwargs)


class Quote(models.Model):
    """Quote model"""
    car_registration = models.CharField(
        verbose_name=_('Car registration'),
        max_length=255
        )
    service = models.ForeignKey(
        "request.ServiceVariation",
        verbose_name=_('Service'),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        )
    post_code = models.CharField(
        verbose_name=_('Post code'),
        max_length=255
        )
    price = models.DecimalField(
        verbose_name=_('Price'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
        )
    car_model = models.CharField(
        verbose_name=_('Model'),
        max_length=255,
        null=True,
        blank=True,

        )
    manufacturer = models.CharField(
        verbose_name=_('Manufacturer'),
        max_length=255,
        null=True,
        blank=True,
        )
    request = models.ForeignKey(
        Request,
        verbose_name=_('Requests'),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        )
    phone = models.CharField(
        verbose_name=_("Phone"),
        max_length=255,
        null=True,
        blank=True
        )

    created_at = models.DateTimeField(
        verbose_name=_('Created at'),
        auto_now_add=True
        )

    class Meta:
        verbose_name = _('Quote')
        verbose_name_plural = _('Quotes')

    def __str__(self):
        return self.car_registration
