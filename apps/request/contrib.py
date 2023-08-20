import random
import string
from decimal import Decimal

import googlemaps
from constance import config
from django.conf import settings
from django.contrib.sites.models import Site
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from postie.shortcuts import send_mail

from apps.request.models import Quote
from apps.request.models import Request
from markup.utils import drop_session
from markup.utils import get_session
from .models import SERVICE_VARIATIONS


def generate_short_url(length=12):
    """Генерирует случайную ссылку из length символов"""
    characters = string.ascii_letters + string.digits
    short_url = ''.join(random.choice(characters) for _ in range(length))
    return short_url


class DistanceGetterException(Exception):
    pass


def calculate_distance_price(post_code):
    """Connect with google api, get distance, calculate price"""
    client = googlemaps.Client(key=config.GOOGLE_API_KEY)
    response = client.distance_matrix(
        **{
            'units': 'metric',
            'mode': 'driving',
            'origins': [config.DEFAULT_POST_CODE],
            'destinations': [post_code],
            }
        )
    if response.get('status', 'failed') != 'OK':
        raise DistanceGetterException(_('Invalid google distance matrix request.'))

    try:
        distance = int(
            min(
                [
                    Decimal(element.get('distance').get('value') / 1000) / Decimal(1.6)  # convert to miles
                    for row in response.get('rows')
                    for element in row.get('elements')
                    ]
                )
            )
    except Exception:
        raise DistanceGetterException(_('Invalid postal code.'))

    if distance < config.MAX_FREE_DISTANCE:
        return distance, 0
    if distance > config.MAX_FIRST_PRICE_DISTANCE:
        return distance, (distance - config.MAX_FREE_DISTANCE) * config.FIRST_DISTANCE_PRICE

    first_price = (config.MAX_FIRST_PRICE_DISTANCE - config.MAX_FREE_DISTANCE) * config.FIRST_DISTANCE_PRICE
    second_price = (distance - config.MAX_FIRST_PRICE_DISTANCE) * config.SECOND_DISTANCE_PRICE
    print(f"First: {first_price},  Second: {second_price}, Distance: {distance}")
    return distance, (first_price + second_price)


def calculate_price(service, car_year, distance_price, distance):
    """Calculate price by service variation"""
    distance_price = distance_price or 0
    if car_year is None:
        car_year_price = 0
    else:
        car_year_price = car_year.price

    if service.variation in [SERVICE_VARIATIONS.car_distance, SERVICE_VARIATIONS.static_distance]:
        price = (
            car_year_price
            if service.variation == SERVICE_VARIATIONS.car_distance
            else service.price
        )
        if price:
            return Decimal(price) + Decimal(distance_price)
    if service.variation == SERVICE_VARIATIONS.static:
        return service.price


def create_request_for_unregistered_car(wsgi_request, validated_data, is_session=False, is_notify=True) -> Request:
    """Create request for unregistered car"""
    request = None
    import urllib3
    urllib3.disable_warnings()
    unique_path = generate_short_url()

    if is_session:
        request = Request.objects.filter(id=wsgi_request.session.get("request")).first()
    if request:
        for key, value in validated_data.items():
            setattr(request, key, value)
        request.save()
    else:
        request = Request.objects.create(**validated_data)
    # Add relation to quote (id_quote get from session)
    id_quote = get_session(wsgi_request, 'id_quote', crypt=True)
    drop_session(wsgi_request, 'id_quote')
    obj_quote = Quote.objects.filter(id=id_quote).first()
    if obj_quote:
        obj_quote.request = request
        obj_quote.save()
    # Send email notification to admin
    if is_notify:
        if request.car:
            admin_link_car = reverse(
                "admin:cars_car_change",
                kwargs={"object_id": request.car.id}
                )
        else:
            admin_link_car = reverse("admin:cars_car_changelist")

        current_site = Site.objects.first()
        send_mail(
            settings.POSTIE_TEMPLATE_CHOICES.created_request,
            config.ADMIN_EMAIL.split(","),
            {
                "id": str(request.id),
                "name": request.name,
                "contacts": request.contacts,
                "email": request.email,
                "phone": request.phone,
                "car_registration": request.car_registration,
                "manufacture": request.car.manufacturer if request.car else None,
                "car_model": request.car.car_model if request.car else None,
                "car_year": request.car_year,
                "distance": request.distance,
                "service": request.service.title if request.service else None,
                "price": request.price,
                "post_code": request.post_code,
                "link": "{}://{}{}".format(
                    (
                        'https'
                        if hasattr(settings, "IS_SSL") and getattr(settings, "IS_SSL")
                        else "http"
                    ),
                    current_site.domain,
                    reverse("unique_path", kwargs={"unique_path": unique_path})
                    ),
                "link_auto": "{}://{}{}".format(
                    (
                        'https'
                        if hasattr(settings, "IS_SSL") and getattr(settings, "IS_SSL")
                        else "http"
                    ),
                    current_site.domain,
                    reverse("unique_path", kwargs={"unique_path": unique_path})
                    # admin_link_car, # reverse("link_path", kwargs={"unique": unique_path})
                    )
                }
            )
        print(
            f"Contrib.py: {request.id} - {request.car_registration}"
            f" - {request.car.manufacturer if request.car else None}"
            f" - {request.car.car_model if request.car else None}"
            f" - {request.car_year}"
            f" - {request.distance}"
            f" - {request.service.title if request.service else None}"
            f" - {request.price}"
            f" - {request.post_code}"
            f" - {unique_path}"
            )
        # order = Order.objects.create( # TODO: Удалить после тестирования
        #     unique_path_field=unique_path,
        #     date_at=request.created_at,
        #     price=request.price,
        #     prepayment=0.00,
        #     car_registration=request.car_registration,
        #     car_year=request.car_year,
        #     car=request.car,
        #     service=request.service,
        #     post_code=request.post_code,
        #     phone=request.phone,
        #     distance=request.distance
        #     )
        # order.save()

    return request
