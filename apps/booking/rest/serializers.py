from django.contrib.sites.models import Site
from django.urls import reverse
from rest_framework import serializers

from apps.booking.models import Order, OrderAttachments, Employee
from apps.cars.models import Car
from markup.utils import create_session


class TransCrtSerializer(serializers.Serializer):
    id = serializers.CharField(write_only=True)


class OrderCreateSerializer(serializers.ModelSerializer):
    link = serializers.SerializerMethodField(read_only=True)
    service_detail = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Order
        fields = (
            "date_at", "price",
            "prepayment", "responsible",
            "comment", "link", "service",
            "service_detail"
        )

    def get_service_detail(self, order):
        if service := order.service:
            return {
                "title": service.title,
                "description": service.description,
            }
        return None

    def get_link(self, order):
        current_site = Site.objects.first()
        return "https://{}{}".format(
            current_site.domain,
            reverse("order_pay", kwargs={"uuid": order.uuid})
        )

    def create(self, validated_data):
        order = super().create(validated_data)
        return order


class UserOrderCreateSerializer(serializers.ModelSerializer):
    link = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Order
        fields = ("date_at", "comment", "link")

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super().__init__(*args, **kwargs)

    def get_link(self, order):
        current_site = Site.objects.first()
        return "https://{}{}".format(
            current_site.domain,
            reverse("order_pay", kwargs={"uuid": order.uuid})
        )

    def create(self, validated_data):
        validated_data["price"] = self.request.price
        validated_data["prepayment"] = self.request.prepayment
        validated_data["service"] = self.request.service
        validated_data["request"] = self.request
        return super().create(validated_data)


class OrderUserUpdateSerializer(serializers.ModelSerializer):
    approve_link = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Order
        fields = (
            "name", "car_registration",
            "phone", "address", "post_code",
            "approve_link", "attachments",
        )

    def get_approve_link(self, order: Order):
        if hasattr(self, "_approve_link") and getattr(self, "_approve_link"):
            return self._approve_link
        return None

    def update(self, instance, validated_data):
        attachments = validated_data.pop("attachments", [])
        file_fields = list(self.context["request"].FILES.keys())
        for file in self.context["request"].FILES.values():
            OrderAttachments.objects.create(
                file=file,
                order=instance,
            )
        order = super().update(instance, validated_data)

        create_session(self.context["request"], 'id_order', order.id, crypt=True)

        # try:
        #     self._approve_link = make_transaction(order)
        # except PaymentGenerationException:
        #     raise serializers.ValidationError("Invalid payment creation")

        return order


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ("id", "name")


class CarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Car
        fields = '__all__'


class ServiceVariationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceVariation
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):
    partner_name = serializers.CharField(source='partner.username', read_only=True)
    confirm_work_display = serializers.CharField(source='get_confirm_work_display', read_only=True)
    service_title = serializers.CharField(source='service.title', read_only=True)
    car = CarSerializer()

    class Meta:
        model = Order
        fields = [
            'unique_path_field', 'date_at', 'price', 'prepayment', 'comment',
            'responsible', 'confirm_work', 'confirm_work_display', 'name',
            'car_registration', 'car_year', 'car', 'service', 'service_title',
            'phone', 'address', 'post_code', 'distance', 'created_at', 'partner_name'
        ]
