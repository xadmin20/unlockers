import random
import string
from decimal import Decimal

import googlemaps
from constance import config
from django.utils.translation import gettext_lazy as _

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
    import urllib3
    urllib3.disable_warnings()
    print(f"create_request_for_unregistered_car: {validated_data}")
    request = None

    # Check for existing Request object
    if is_session:
        request = Request.objects.filter(id=wsgi_request.session.get("request")).first()

    # If Request object already exists, update it
    if request:
        for key, value in validated_data.items():
            setattr(request, key, value)
        request.save()
    else:
        request = Request.objects.create(**validated_data)

    id_quote = get_session(wsgi_request, 'id_quote', crypt=True)
    drop_session(wsgi_request, 'id_quote')
    obj_quote = Quote.objects.filter(id=id_quote).first()
    if obj_quote:
        obj_quote.request = request
        obj_quote.save()

    return request
