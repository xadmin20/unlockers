from constance import config
from django.conf import settings
from django.contrib.sites.models import Site
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from postie.shortcuts import send_mail
from rest_framework import serializers

from apps.booking.senders import request_sms
from apps.cars.contrib import Car as CarEntity
from apps.cars.contrib import CarParsingException
from apps.cars.contrib import get_car
from apps.cars.contrib import register_car
from apps.request.contrib import DistanceGetterException
from apps.request.contrib import calculate_distance_price
from apps.request.contrib import calculate_price
from apps.request.contrib import create_request_for_unregistered_car
from apps.request.models import Quote
from apps.request.models import Request
from apps.request.models import ServiceVariation
from apps.sms.models import is_phone_mechanic
from markup.utils import create_session


def validate_phone(phone):
    if (short := (len(phone) == 11 and phone.startswith("0"))) or (len(phone) == 13 and phone.startswith("+44")):
        return "+44" + phone[1:] if short else phone
    raise serializers.ValidationError(_("Invalid phone format"))


def add_quote(
        car_registration, service, post_code, price=None, car_model=None, manufacturer=None, phone=None, mailing=False
        ):
    quote = Quote.objects.create(
        car_registration=car_registration,
        service=service,
        post_code=post_code,
        price=price,
        car_model=car_model,
        manufacturer=manufacturer,
        phone=phone,
        )
    # Send admin mail notification
    # if not is_phone_mechanic() and phone:
    if phone and mailing:
        base_link = "{}://{}".format(
            (
                'https'
                if hasattr(settings, "IS_SSL") and getattr(settings, "IS_SSL")
                else "http"
            ),
            Site.objects.first().domain
            )
        send_mail(
            settings.POSTIE_TEMPLATE_CHOICES.quote_created,
            config.ADMIN_EMAIL.split(","),
            context={
                "car_registration": quote.car_registration,
                "service": quote.service.title,
                "post_code": quote.post_code,
                "price": str(quote.price),
                "car_model": quote.car_model,
                "manufacturer": quote.manufacturer,
                "request_link": (
                    f"{base_link}/admin/request/request/{quote.request_id}/change/"
                    if quote.request_id else None
                ),
                "quote_link": f"{base_link}/admin/request/quote/{quote.id}/change/",
                "request_id": quote.request_id,
                "phone": phone,
                "created_at": quote.created_at,
                "id": quote.id,
                }
            )
    return quote


class RequestPreCreateSerializer(serializers.ModelSerializer):
    car_model = serializers.CharField(source="car.car_model", read_only=True)
    manufacturer = serializers.CharField(source="car.manufacturer", read_only=True)

    class Meta:
        model = Request
        fields = (
            "id", "car_registration",
            "post_code", "service",
            "car_model", "manufacturer",
            "price", "phone"
            )
        read_only_fields = (
            "id", "car_model", "manufacturer", "price"
            )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not is_phone_mechanic():
            del self.fields["phone"]
        self.car_entity = None
        self.distance = None
        self.distance_price = None

    def validate_phone(self, phone):
        return validate_phone(phone)

    def validate(self, attrs):
        _request = self.context["request"]

        # Try to get car in register, if car not exists or something else raise validation error
        # If phone mechanic enable, create unregistered car request
        try:
            self.car_entity: CarEntity = get_car(attrs.get("car_registration"))

        except CarParsingException:
            obj_quote = add_quote(
                car_registration=attrs.get("car_registration"),
                service=attrs.get("service"),
                post_code=attrs.get("post_code"),
                phone=attrs.get("phone"),
                mailing=True,
                )
            create_session(_request, 'id_quote', obj_quote.id, crypt=True)

            if is_phone_mechanic():
                attrs["distance"] = self.distance
                create_request_for_unregistered_car(_request, attrs)

            raise serializers.ValidationError(
                _(
                    "Car is not found."
                    )
                )

        # Try to calculate distance and distance price
        # If raise exception create quote and raise validation error that postal code is invalid
        try:
            self.distance, self.distance_price = calculate_distance_price(attrs.get("post_code"))
        except DistanceGetterException:
            obj_quote = add_quote(
                car_registration=attrs.get("car_registration"),
                service=attrs.get("service"),
                post_code=attrs.get("post_code"),
                car_model=self.car_entity.car_model.split(' ', 1)[0],
                manufacturer=self.car_entity.manufacturer,
                phone=attrs.get("phone"),
                mailing=True,
                )
            create_session(_request, 'id_quote', obj_quote.id, crypt=True)

            raise serializers.ValidationError(
                _(
                    "Impossible to calculate distance. Invalid post code."
                    )
                )
        return attrs

    def create(self, validated_data):
        try:
            car_year = register_car(self.car_entity)
        except:
            car_year = None

        if car_year is None:
            validated_data["car"] = None
            validated_data["car_year"] = None
        else:
            validated_data["car"] = car_year.car
            validated_data["car_year"] = self.car_entity.manufactured
        # validated_data["car"] = car_year.car
        # validated_data["car_year"] = self.car_entity.manufactured
        validated_data["distance"] = self.distance
        validated_data["price"] = calculate_price(
            service=validated_data["service"],
            car_year=car_year,
            distance=self.distance,
            distance_price=self.distance_price,
            )
        is_phone = is_phone_mechanic()
        request_object = create_request_for_unregistered_car(
            self.context["request"], validated_data, is_notify=is_phone
            )
        # Write in session
        request = self.context["request"]
        request.session["request"] = request_object.id

        # Add quote, xz what it is
        obj_quote_data = {
            'car_registration': validated_data["car_registration"],
            'service': validated_data["service"],
            'post_code': validated_data["post_code"],
            'price': validated_data["price"],
            'phone': validated_data.get("phone")
            }
        print(obj_quote_data)
        if self.car_entity:
            obj_quote_data['car_model'] = self.car_entity.car_model.split(' ', 1)[0]
            obj_quote_data['manufacturer'] = self.car_entity.manufacturer

        obj_quote = add_quote(**obj_quote_data)
        create_session(request, 'id_quote', obj_quote.id, crypt=True)

        # Send success sms
        if is_phone:
            if request_object:
                print('Request object:', request_object.__dict__)
                request_sms(request_object)  # TODO: раскомментировать в случае необходимости отправки смс
            else:
                print('Request object is None.')

        return request_object


def form_link(_reverse, context):
    return "{}://{}{}".format(
        context.get("protocol"),
        context.get("domain"),
        _reverse
        )


class UnregisteredCarRequestSerializer(serializers.ModelSerializer):
    car_model = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Request
        fields = (
            "car_registration", "post_code",
            "service", "name", "contacts",
            "phone", "email", "car_model"
            )

    def validate_phone(self, phone):
        return validate_phone(phone)

    def validate(self, attrs):
        try:
            self.distance, self.distance_price = calculate_distance_price(attrs.get("post_code"))
        except:
            self.distance = 0
            self.distance_price = 0
            pass
        return attrs

    def get_car_model(self, request: Request):
        return request.car.car_model if request.car else None

    def create(self, validated_data):
        return create_request_for_unregistered_car(self.context["request"], validated_data)


class RequestUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Request
        fields = (
            "name", "contacts", "comment", "phone", "email"
            )

    def update(self, instance, validated_data):
        request = super().update(instance, validated_data)

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
                    reverse(
                        "admin:request_request_change",
                        kwargs={"object_id": request.id}
                        ),
                    ),
                }
            )
        return request


class RequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = Request
        fields = "__all__"


class ServiceVariatioSerializer(serializers.ModelSerializer):

    class Meta:
        model = ServiceVariation
        fields = "__all__"


class AddCarSerializer(serializers.Serializer):
    manufacturer = serializers.CharField()
    car_model = serializers.CharField()
    manufactured = serializers.CharField()
