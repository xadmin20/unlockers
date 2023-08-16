from rest_framework import serializers
from .models import Order
from apps.request.models import Request, ServiceVariation


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'

    def create(self, validated_data):
        request = Request.objects.get(id=validated_data['request'])
        service = ServiceVariation.objects.get(id=validated_data['service'])
        order = Order.objects.create(
            request=request,
            service=service,
            **validated_data
        )
        return order
