import datetime

from constance import config
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.db.models import Exists
from django.db.models import OuterRef
from django.db.models import Q
from django.db.models import Sum
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_filters import rest_framework as filters
from rest_auth.views import LoginView
from rest_auth.views import LogoutView
from rest_auth.views import PasswordChangeView
from rest_auth.views import PasswordResetConfirmView
from rest_auth.views import PasswordResetView
from rest_framework import generics
from rest_framework import status
from rest_framework.filters import OrderingFilter
from rest_framework.filters import SearchFilter
from rest_framework.generics import CreateAPIView
from rest_framework.generics import GenericAPIView
from rest_framework.generics import ListAPIView
from rest_framework.generics import RetrieveAPIView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import BasePermission
from rest_framework.permissions import IsAdminUser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.booking.models import Employee
from apps.booking.models import Order
from apps.booking.models import PAYMENT_STATUSES
from apps.booking.models import Transaction
from apps.booking.senders import _send_sms
from apps.cars.models import Car
from apps.partners.api.filters import OrdersWeekFilter
from apps.partners.api.filters import StatisticRequestFilter
from apps.partners.const import WITHDRAW_STATUS
from apps.partners.models import Transactions
from apps.partners.models import Withdraw
from apps.request.models import Request
from .serializers import BalanceHistorySerializer
from .serializers import CreateOrderSerializer
from .serializers import CreateRequestSerializer
from .serializers import EmailChangeSerializer
from .serializers import GetCarManufacturerSerializer
from .serializers import GetCarModelSerializer
from .serializers import OrderDetailSerializer
from .serializers import OrdersHistorySerializer
from .serializers import PasswordResetSerializerApi
from .serializers import ProfileInfoSerializer
from .serializers import ProfileUpdateSerializer
from .serializers import SendSMSSerializer
from .serializers import StatisticNotFitPriceSerializer
from .serializers import WithdrawCreateSerializer
from .serializers import WithdrawHistorySerializer

UserModel = get_user_model()


# Определите новые классы пагинации
class CustomLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 10  # Измените это на то, что вы использовали ранее
    max_limit = 100  # Измените это на то, что вы использовали ранее


class CustomPageNumberPagination(PageNumberPagination):
    page_size = 10  # Измените это на то, что вы использовали ранее


class IsNotAuthenticated(BasePermission):
    """
    Allows access only to not authenticated users.
    """

    def has_permission(self, request, view):
        return bool(not request.user.is_authenticated)


class LoginApi(LoginView):
    permission_classes = (IsNotAuthenticated,)


class LogoutApi(LogoutView):
    permission_classes = (IsAuthenticated,)


class PasswordResetViewApi(PasswordResetView):
    serializer_class = PasswordResetSerializerApi


class PasswordResetConfirmViewApi(PasswordResetConfirmView):

    def post(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)

        return Response(
            {
                "detail": _("Password reset e-mail has been sent."),
                "redirect": reverse('login')
                },
            status=status.HTTP_200_OK
            )


class PasswordChangeViewApi(PasswordChangeView):
    pass


class ProfileInfoViewApi(RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ProfileInfoSerializer

    def get_object(self):
        return self.request.user


class ProfileUpdateViewApi(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ProfileUpdateSerializer

    def post(self, request, *args, **kwargs):
        # Create a serializer with request.data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save()
        result = serializer.data
        result['detail'] = _('Your data has been changed')
        return Response(result)


class SendTestEmailViewApi(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = self.request.user
        if email := user.email:
            response_messages = {
                'title': _('Success'),
                'message': _('A test letter has been sent to you')
                }
            return Response({"message": response_messages})

        response_messages = {
            'title': _('Failure'),
            'message': _('You do not have an email address')
            }
        return Response({"message": response_messages})


class EmailChangeViewApi(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = EmailChangeSerializer

    def post(self, request, *args, **kwargs):
        # Create a serializer with request.data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save()
        # Return the success message with OK HTTP status
        return Response(
            {"detail": _("An email has been sent to your email.")}
            )


class OrdersWeekViewApi(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrdersHistorySerializer
    filter_backends = [OrderingFilter]
    pagination_class = CustomLimitOffsetPagination
    ordering_fields = ['id', 'created_at', 'date_at', 'price', 'prepayment']

    def get_queryset(self):
        user = self.request.user
        week = datetime.datetime.now().isocalendar()[1]
        paid = self.request.GET.get('ordering')
        query_ordering = '-created_at'

        if paid == 'paid':
            query_ordering = 'transactions__status'
        if paid == '-paid':
            query_ordering = '-transactions__status'

        return Order.objects.filter(
            partner=user,
            created_at__week=week,
            ).order_by(
            query_ordering
            ).annotate(
            status_paid=Exists(
                Transaction.objects.filter(
                    order=OuterRef("pk"),
                    status=PAYMENT_STATUSES.paid
                    )
                )
            )


class InfoWeekViewApi(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = self.request.user
        week = datetime.datetime.now().isocalendar()[1]
        total = Order.objects.filter(
            partner=user,
            created_at__week=week,
            transactions__status=PAYMENT_STATUSES.paid
            ).aggregate(summ=Sum('prepayment'), count=Count('prepayment'))

        balance_week = str(total.get('summ')) if total.get('summ') else '0.00'

        result = {
            'total': balance_week,
            'count': total.get('count'),
            'schedule_technician': config.SCHEDULE_TECHNICIAN,
            'name_technician': config.NAME_TECHNICIAN,
            'contact_technician': config.CONTACT_TECHNICIAN,
            'schedule_office': config.SCHEDULE_OFFICE,
            'contact_office': config.CONTACT_OFFICE,
            }

        return Response(result)


class SendSMSViewApi(GenericAPIView):
    """Отправка SMS сообщения"""
    permission_classes = (IsAuthenticated,)
    serializer_class = SendSMSSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data.get('phone')
        message = serializer.validated_data.get('message')

        status_code, content = _send_sms(phone, message)

        if status_code == 200:
            message = _('Your SMS has been sent.')
        else:
            message = _('Your SMS has not been sent.')

        result = {
            'message': message
            }

        return Response(result)


class OrdersHistoryViewApi(ListAPIView):
    """История заказов"""
    permission_classes = (IsAuthenticated,)
    serializer_class = OrdersHistorySerializer
    filter_backends = (filters.DjangoFilterBackend, SearchFilter)
    filterset_class = OrdersWeekFilter
    pagination_class = CustomLimitOffsetPagination
    search_fields = ['id']

    def get_queryset(self):
        user = self.request.user
        paid = self.request.GET.get('ordering')
        query_ordering = '-created_at'

        # if paid == 'paid':
        #     query_ordering = 'transactions__status'
        # if paid == '-paid':
        #     query_ordering = '-transactions__status'

        return Order.objects.filter(
            partner=user,
            ).order_by(
            query_ordering
            ).annotate(
            status_paid=Exists(
                Transaction.objects.filter(
                    order=OuterRef("pk"),
                    status=PAYMENT_STATUSES.paid
                    )
                )
            )


class OrderDetailViewApi(RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrderDetailSerializer

    def get_queryset(self):
        user = self.request.user
        return Order.objects.filter(partner=user)


class BalanceHistoryViewApi(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = BalanceHistorySerializer
    filter_backends = [OrderingFilter]
    pagination_class = CustomLimitOffsetPagination
    ordering_fields = [
        'id', 'created_at', 'type_transactions', 'order', 'withdraw',
        'amount', 'balance',
        ]

    def get_queryset(self):
        user = self.request.user
        return Transactions.objects.filter(
            partner=user
            ).order_by('-created_at')


class WithdrawHistoryViewApi(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = WithdrawHistorySerializer
    filter_backends = (
        filters.DjangoFilterBackend, OrderingFilter,
        SearchFilter,
        )
    pagination_class = CustomLimitOffsetPagination
    ordering_fields = ['id']
    search_fields = ['id']
    filterset_fields = ('status',)

    def get_queryset(self):
        user = self.request.user
        return Withdraw.objects.filter(
            partner=user
            ).order_by('-created_at')


class WithdrawCreateViewApi(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = WithdrawCreateSerializer


class GetBalanceApi(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = self.request.user
        try:
            balance = user.partner.balance
        except:
            balance = 0.00

        result = {
            'balance': balance,
            }

        return Response(result)


class GetListWithdrawStatusApi(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        result = (
            {
                'id': item[0],
                'label': item[1]
                }
            for item in WITHDRAW_STATUS
            )

        return Response(result)


class GetListOrderStatusApi(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        result = (
            {
                'id': item[0],
                'label': item[1]
                }
            for item in PAYMENT_STATUSES
            )

        return Response(result)


class CreateOrderViewApi(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CreateOrderSerializer


class CreateRequestViewApi(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CreateRequestSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        result = serializer.data

        if not serializer.data.get('id', False):

            result['request'] = False
            return Response(result, status=status.HTTP_200_OK)

        result['request'] = True
        headers = self.get_success_headers(serializer.data)
        return Response(result, status=status.HTTP_201_CREATED, headers=headers)


class StatisticNotFitPriceViewApi(ListAPIView):
    permission_classes = (IsAdminUser,)
    serializer_class = StatisticNotFitPriceSerializer
    filter_backends = (filters.DjangoFilterBackend, SearchFilter)
    pagination_class = CustomLimitOffsetPagination
    filterset_class = StatisticRequestFilter

    def get_queryset(self):
        return Request.objects.annotate(
            order_exists=Exists(Order.objects.filter(request=OuterRef("pk")))
            ).filter(
            price__gt=0
            ).filter(
            Q(order_exists=False) | Q(
                order_exists=True,
                order__transactions__status=PAYMENT_STATUSES.no_paid
                )
            ).order_by(
            "car__manufacturer", "car__car_model", "car_year"
            ).distinct("car__manufacturer", "car__car_model", "car_year")


class GetEmployeeApi(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        employee = False
        result = {
            'message': _('Not employee')
            }
        employees = Employee.objects.all()
        if employees:
            employee = employees.filter(default=True).first()

        if not employee:
            employee = employees.first()
        if employee:
            result = {
                'id': employee.id,
                'name': employee.name
                }

        return Response(result)


class GetCarManufacturerApi(ListAPIView):
    permission_classes = (IsAdminUser,)
    serializer_class = GetCarManufacturerSerializer

    def get_queryset(self):
        return Car.objects.all().order_by('manufacturer').distinct('manufacturer')


class GetCarModelApi(ListAPIView):
    permission_classes = (IsAdminUser,)
    serializer_class = GetCarModelSerializer

    def get_queryset(self):
        manufacturer = self.kwargs.get('manufacturer')
        return Car.objects.filter(manufacturer__iexact=manufacturer).order_by('car_model')
