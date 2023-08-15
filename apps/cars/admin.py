from django.contrib import admin

from .models import Car, CarYears


class CarYearsInline(admin.TabularInline):
    model = CarYears
    extra = 0

admin.site.register(
    Car,
    list_display=("__str__", "manufacturer", "car_model", "is_appreciated"),
    inlines=(CarYearsInline, ),
    search_fields=("car_model", "manufacturer")
)