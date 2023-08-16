from django.http.response import HttpResponseRedirect

from rest_framework.generics import (
    RetrieveAPIView, CreateAPIView, UpdateAPIView, ListAPIView, GenericAPIView,
)
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import NotFound

from rest_framework.response import Response

from apps.cars.contrib import register_car

from .serializers import (
    RequestPreCreateSerializer,
    RequestUpdateSerializer,
    RequestSerializer,
    ServiceVariatioSerializer,
    UnregisteredCarRequestSerializer,
    AddCarSerializer,

)

from apps.cars.models import Car, CarYears

from ..models import Request, ServiceVariation, STATUSES


class RequestPreCreateAPIView(CreateAPIView):
    serializer_class = RequestPreCreateSerializer
    queryset = Request.objects.all()


class UnregisteredCardRequestCreateAPIView(CreateAPIView):
    serializer_class = UnregisteredCarRequestSerializer
    queryset = Request.objects.all()


class RequestUpdateAPIView(UpdateAPIView):
    serializer_class = RequestUpdateSerializer
    queryset = Request.objects.all()


class RequestReceiveAPIView(RetrieveAPIView):
    serializer_class = RequestSerializer
    queryset = Request.objects.all()


class ServicesListAPIView(ListAPIView):
    serializer_class = ServiceVariatioSerializer
    queryset = ServiceVariation.objects.all()


def change_status(request, *args, **kwargs):
    tel_response_klass = HttpResponseRedirect
    tel_response_klass.allowed_schemes = ['tel']
    request_obj = Request.objects.filter(id=kwargs.get('pk')).first()
    if request_obj and request_obj.phone:
        if request_obj.status != STATUSES.done:
            request_obj.status = STATUSES.is_work
            request_obj.save(False)
        return tel_response_klass('tel:{}'.format(request_obj.phone))
    return HttpResponseRedirect('/')


class AddCarAPIView(GenericAPIView):
    serializer_class = AddCarSerializer

    def post(self, request, *args, **kwargs):
        car_obj, is_create = Car.objects.get_or_create(
            car_model=request.data.get("car_model"),
            manufacturer=request.data.get("manufacturer")
        )

        manufactured = request.data.get("manufactured")
        if not CarYears.objects.filter(
                year_to__gte=manufactured,
                year_from__lte=manufactured,
                car=car_obj
        ).exists():
            car_years = CarYears.objects.create(
                year_to=manufactured,
                year_from=manufactured,
                car=car_obj
            )
            car_obj.is_appreciated = False
            car_obj.save()

        return Response(
            data={"Car update": "True"},
        )

# def register_car(car: Car) -> (CarYears, bool):
#     if (car_years := CarYears.objects.filter(
#         year_from__lte=car.manufactured, 
#         year_to__gte=car.manufactured,
#         car__manufacturer=car.manufacturer.split(' ', 1)[0],
#         car__car_model=car.car_model,
#     ).first()):
#         return car_years

#     car_kw = dict(
#         manufacturer=car.manufacturer.split(' ', 1)[0],
#         car_model=car.car_model,
#     )
#     car_object = CarModel.objects.filter(**car_kw).first()
#     if not car_object:
#         car_object = CarModel.objects.create(**car_kw)
#     car_years = CarYears.objects.create(
#         year_to=car.manufactured,
#         year_from=car.manufactured,
#         car=car_object
#     )
#     return car_years
