from django.db import models
from django.utils.translation import gettext_lazy as _


class Car(models.Model):
    car_model = models.CharField(
        verbose_name=_('Model'),
        max_length=255,
    )
    manufacturer = models.CharField(
        verbose_name=_('Manufacturer'),
        max_length=255,
    )
    is_appreciated = models.BooleanField(
        verbose_name=_('Is appreciated'),
        default=False,
    )
    import_id = models.IntegerField(
        verbose_name=_("Import id"),
        null=True,
        blank=True
    )

    class Meta:
        ordering = ('pk',)
        verbose_name = _('Car')
        verbose_name_plural = _('Cars')

    def __str__(self):
        return f"{self.manufacturer} | {self.car_model}"

    def save(self, *args, **kwargs):
        # First save the object so it gets a primary key
        obj = super(Car, self).save(*args, **kwargs)
        # Then, update the status
        self.update_status(False)
        return obj

    @property
    def all_years(self):
        return ', '.join([
            '{}-{}'.format(
                year.year_from,
                year.year_to
            ) for year in self.years.all()
        ])

    def update_status(self, commit=True):
        self.is_appreciated = all([(year.price or 0) > 0 for year in self.years.all()])
        if commit:
            self.save()


class CarYears(models.Model):
    year_from = models.IntegerField(
        verbose_name=_('Year from'),
        null=True
    )
    year_to = models.IntegerField(
        verbose_name=_('Year to'),
        null=True
    )
    price = models.DecimalField(
        verbose_name=_('Price'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    car = models.ForeignKey(
        Car,
        verbose_name=_('Car'),
        on_delete=models.CASCADE,
        related_name='years'
    )
    import_id = models.IntegerField(
        verbose_name=_("Import id"),
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _("Car year")
        verbose_name_plural = _("Car years")

    def __str__(self):
        return self.car.car_model
