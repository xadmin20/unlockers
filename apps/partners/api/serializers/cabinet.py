import os
import math
from datetime import datetime, timedelta
from django.db.models import Exists, OuterRef, Q, F
from django.urls import reverse
from django.utils.translation import gettext as _
from django.contrib.sites.models import Site
from django.utils.translation import get_language
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings
from rest_framework import serializers
from standards.drf.serializers import ModelSerializer, Serializer
from rest_framework.exceptions import ValidationError
from postie.shortcuts import send_mail
from constance import config

from apps.booking.models import Order, PAYMENT_STATUSES, Employee
from apps.request.models import Request, SERVICE_VARIATIONS
from apps.cars.models import Car
from apps.request.rest.serializers import validate_phone 
from apps.cars.contrib import (
    get_car, Car as CarEntity, register_car
)

from apps.request.contrib import (
    calculate_distance_price,
    calculate_price,
    create_request_for_unregistered_car,
)
from apps.partners.models import Transactions, Withdraw, Partner
from apps.partners.const import TRANSACTIONS_STATUS
from apps.partners.transactions import create_transaction
from .custom_fields import Base64FileSerializerField


def convert_size(size_bytes): 
    if size_bytes == 0: 
        return "0B" 
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB") 
    i = int(math.floor(math.log(size_bytes, 1024)))
    power = math.pow(1024, i) 
    size = round(size_bytes / power, 2) 
    return "{} {}".format(size, size_name[i])


class OrdersHistorySerializer(ModelSerializer):
    created_at = serializers.DateTimeField(format='%d/%m/%Y %I:%M %p')
    date_at = serializers.DateTimeField(format='%d/%m/%Y %I:%M %p')
    paid = serializers.SerializerMethodField()
    link = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'created_at', 'date_at', 'price',
            'prepayment', 'paid', 'phone', 'link',
        ]

    def get_paid(self, obj):
        if obj.status_paid:
            return PAYMENT_STATUSES._display_map.get(PAYMENT_STATUSES.paid)
        return PAYMENT_STATUSES._display_map.get(PAYMENT_STATUSES.no_paid)

    def get_link(self, obj):
        now = datetime.now()
        limit = timedelta(hours=2)
        actual = now - limit
        link_is_active = datetime.timestamp(actual) <= datetime.timestamp(obj.created_at)
        if not obj.status_paid and link_is_active:
            current_site = Site.objects.first()
            return "https://{}{}".format(
                current_site.domain, 
                reverse("order_pay", kwargs={"uuid": obj.uuid})
            )
        return None


class SendSMSSerializer(serializers.Serializer):
    phone = serializers.CharField(write_only=True)
    message = serializers.CharField(write_only=True)


class OrderDetailSerializer(ModelSerializer):
    responsible_name = serializers.SerializerMethodField()
    service_name = serializers.SerializerMethodField()
    booking_date = serializers.SerializerMethodField()
    booking_time = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'uuid', 'price', 
            'prepayment', 'responsible_name', 'name',
            'car_registration', 'phone', 'address',
            'post_code', 'service_name', 'is_paid',
            'booking_date', 'booking_time'
        ]

    def get_responsible_name(self, obj):
        if obj.responsible:
            return obj.responsible.name
        return
        
    def get_service_name(self, obj):
        return obj.service.title
    
    def get_booking_date(self, obj):
        return obj.date_at.strftime("%d/%m/%Y")

    def get_booking_time(self, obj):
        return obj.date_at.strftime("%I:%M %p")


class BalanceHistorySerializer(ModelSerializer):
    created_at = serializers.DateTimeField(format='%d/%m/%Y %I:%M %p')
    transactions_type = serializers.SerializerMethodField()
    summ = serializers.DecimalField(source='amount', max_digits=10, decimal_places=2)

    class Meta:
        model = Transactions
        fields = [
            'id', 'created_at', 'transactions_type',
            'withdraw', 'order', 'summ', 'balance',
        ]

    def get_transactions_type(self, obj):
        return obj.get_type_transactions_display()


class WithdrawHistorySerializer(ModelSerializer):
    created_at = serializers.DateTimeField(format='%d/%m/%Y')
    withdraw_status = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()

    class Meta:
        model = Withdraw
        fields = [
            'id', 'created_at', 'attachment_file', 'file_name',
            'withdraw_status', 'file_size',
        ]

    def get_withdraw_status(self, obj):
        return obj.get_status_display()

    def get_file_name(self, obj):
        return os.path.basename(obj.attachment_file.name).split('.')[0]

    def get_file_size(self, obj):
        return convert_size(obj.attachment_file.size)


class WithdrawCreateSerializer(ModelSerializer):
    attachment_file = Base64FileSerializerField()
    message = serializers.SerializerMethodField()

    class Meta:
        model = Withdraw
        fields = [
            'attachment_file', 'amount', 'comment', 'message',
        ]
        
    def get_message(self, obj):
        return _('Withdraw request sent')

    def validate_amount(self, amount):
        user = self.request.user

        if amount == 0 or not Partner.objects.filter(user=user).exists():
            raise ValidationError(_('Balance is zero'))

        if user.partner.balance < amount:
            raise ValidationError(_('The withdrawal amount is greater than the balance'))

        return amount

    def create(self, validated_data):
        user = self.request.user
        amount = validated_data.get('amount')
            
        validated_data['partner'] = user
        instance = super().create(validated_data)

        user.partner.balance = F('balance') - amount
        user.partner.save()
        user.refresh_from_db()
        balance = user.partner.balance
        
        data = {
            'partner': user,
            'amount': -instance.amount,
            'balance': balance,
            'type_transactions': TRANSACTIONS_STATUS.withdraw,
            'withdraw': instance
        }

        # Transactions.objects.create(**data)
        create_transaction(**data)

        base_url = str(get_current_site(self.request))

        link_admin = 'https://' + base_url + reverse(
            f"admin:{instance._meta.app_label}_{instance._meta.model_name}_change",
            kwargs={"object_id": instance.id}
        )
        
        email = config.ADMIN_EMAIL
        
        send_mail(
            event=settings.POSTIE_TEMPLATE_CHOICES.send_withdraw_admin,
            recipients=[email],
            context={
                'link_admin': link_admin
            },
            language=get_language()
        )

        return instance


class CreateOrderSerializer(ModelSerializer):
    DATE_FORMAT = ['%d/%m/%Y %I:%M %p', '%d/%m/%Y ']
    link = serializers.SerializerMethodField()
    date_at = serializers.DateTimeField(format='%d/%m/%Y %I:%M %p', input_formats=DATE_FORMAT)

    class Meta:
        model = Order
        fields = [
            'id', 'date_at', 'price', 'prepayment', 'phone', 'service',
            'car_registration', 'responsible', 'link', 'post_code',
            'request',
        ]

    def get_link(self, order):
        current_site = Site.objects.first()
        return "https://{}{}".format(
            current_site.domain, 
            reverse("order_pay", kwargs={"uuid": order.uuid})
        )

    def create(self, validated_data):
        validated_data["partner"] = self.request.user
        return super().create(validated_data)


class CreateRequestSerializer(ModelSerializer):
    car_model = serializers.CharField(source="car.car_model", read_only=True)
    manufacturer = serializers.CharField(source="car.manufacturer", read_only=True)
    # responsible = serializers.SerializerMethodField()

    class Meta:
        model = Request
        fields = (
            "id", "car_registration", 
            "post_code", "service",
            "car_model", "manufacturer",
            "price", "phone", "car_year",
            # "responsible",
        )
        read_only_fields = (
            "id", "car_model", "manufacturer", "price", "car_year",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.car_entity = None
        self.distance = None
        self.distance_price = None

    def validate_phone(self, phone):
        if phone:
            return validate_phone(phone)
        return
    
    # def get_responsible(self, obj):
    #     if employee := Employee.objects.filter(default=True).first():
    #         return {
    #             'id': employee.id,
    #             'name': employee.name
    #         }
    #     return

    def validate(self, attrs):
        # _request = self.context["request"]
        
        # Try to get car in riester, if car not exists or something else raise validation error
        # If phone mechanic enable, create unregistered car request
        try:
            self.car_entity = get_car(attrs.get("car_registration"))
        except:
            pass

        try:
            self.distance, self.distance_price = calculate_distance_price(attrs.get("post_code"))
        except:
            pass
        
        return attrs

    def create(self, validated_data):
        if self.car_entity is None:
            # result = validated_data
            # result['responsible'] = self.get_responsible(validated_data)
            return validated_data
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

        request_object = create_request_for_unregistered_car(
            self.context["request"], validated_data, is_notify=False
        )
        
        return request_object


class StatisticNotFitPriceSerializer(ModelSerializer):
    service_title = serializers.CharField(source='service.title')
    car_model = serializers.CharField(source="car.car_model")
    manufacturer = serializers.CharField(source="car.manufacturer")
    count_neg = serializers.SerializerMethodField()
    count_pos = serializers.SerializerMethodField()
    current_price = serializers.SerializerMethodField()

    year_period = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        created_at_gte = self.request.GET.get('created_at__gte')
        created_at_lte = self.request.GET.get('created_at__lte')
        self.created = {}
        if created_at_gte:
            self.created['created_at__gte'] = datetime.strptime(created_at_gte, "%d/%m/%Y")
        if created_at_lte:
            self.created['created_at__lte'] = datetime.strptime(created_at_lte, "%d/%m/%Y")

    class Meta:
        model = Request
        fields = [
            'car_year', 'service_title',
            'car_model', 'manufacturer',
            'count_neg', 'count_pos', 'current_price',
            'year_period',
        ]

    def get_count_neg(self, obj):
        return Request.objects.annotate(
            order_exists=Exists(Order.objects.filter(request=OuterRef("pk")))
            ).filter(
                car=obj.car,
                service=obj.service,
                car_year=obj.car_year,
                **self.created
            ).filter(
                Q(order_exists=False) | Q(
                    order_exists=True,
                    order__transactions__status=PAYMENT_STATUSES.no_paid)
            ).count()

    def get_count_pos(self, obj):
        cars = Request.objects.filter(
            car=obj.car,
            car_year=obj.car_year,
            service=obj.service,
            **self.created,
            ).values_list('car_registration').order_by('car_registration').distinct('car_registration')

        orders = Order.objects.filter(
            car_registration__in=cars,
            transactions__status=PAYMENT_STATUSES.paid,
            service=obj.service,
            ).count()
        
        return orders
        
    def get_current_price(self, obj):
        if obj.service.variation == SERVICE_VARIATIONS.car_distance:
            car_year = obj.car.years.filter(
                year_from__lte=obj.car_year, 
                year_to__gte=obj.car_year,
            ).first()
            if car_year:
                return car_year.price
        if service_price := obj.service.price:
            return "{:.2f}".format(service_price)
        return 
    
    def get_year_period(self, obj):
        car_year = obj.car.years.filter(
            year_from__lte=obj.car_year, 
            year_to__gte=obj.car_year,
        ).first()
        if car_year:
            year_from = car_year.year_from
            year_to = car_year.year_to
            return f'{year_from} - {year_to}'
        return


class GetCarManufacturerSerializer(ModelSerializer):
    id = serializers.SerializerMethodField()
    label = serializers.SerializerMethodField()

    class Meta:
        model = Car
        fields = ('id', 'label')

    def get_id(self, obj):
        return obj.manufacturer

    def get_label(self, obj):
        return obj.manufacturer


class GetCarModelSerializer(ModelSerializer):
    id = serializers.SerializerMethodField()
    label = serializers.SerializerMethodField()

    class Meta:
        model = Car
        fields = ('id', 'label')

    def get_id(self, obj):
        return obj.car_model

    def get_label(self, obj):
        return obj.car_model
