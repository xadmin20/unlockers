from constance import config
from django.contrib.sites.models import Site
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

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
from apps.sms.logic import _send_sms
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
            print("Error: Car is not found.")

            _send_sms(
                config.PHONE, f"Error: {obj_quote.phone} car: {obj_quote.car_registration}"
                              f" {obj_quote.service} Post:{obj_quote.post_code}"
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
