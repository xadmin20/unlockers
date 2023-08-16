from django.db import models

from apps.partners.models import Partner
from apps.booking.models import Order


# создаем заказ через form
def create_order(**kwargs):
    return Order.objects.create(**kwargs)

