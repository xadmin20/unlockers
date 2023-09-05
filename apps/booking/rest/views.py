from django.db.models import F
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import pgettext_lazy
from rest_framework import exceptions
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.exceptions import NotFound
from rest_framework.generics import CreateAPIView
from rest_framework.generics import GenericAPIView
from rest_framework.generics import ListAPIView
from rest_framework.generics import RetrieveAPIView
from rest_framework.generics import UpdateAPIView
from rest_framework.permissions import IsAdminUser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.booking.models import Employee
from apps.booking.models import Order
from apps.booking.models import PAYMENT_STATUSES
from apps.booking.models import Transaction
from apps.partners.const import TRANSACTIONS_STATUS
from apps.partners.models import Partner
from apps.partners.transactions import create_transaction
from apps.request.models import Request
from apps.sms.models import is_phone_mechanic
from markup.utils import get_session
from .serializers import EmployeeSerializer
from .serializers import OrderCreateSerializer
from .serializers import OrderSerializer
from .serializers import OrderUserUpdateSerializer
from .serializers import TransCrtSerializer
from .serializers import UserOrderCreateSerializer
from ...sms.logic import _send_sms


class OrderCreateAPIView(CreateAPIView):
    serializer_class = OrderCreateSerializer
    permission_classes = (IsAdminUser,)
    queryset = Order.objects.all()


class UserOrderCreateAPIView(CreateAPIView):
    serializer_class = UserOrderCreateSerializer
    queryset = Order.objects.all()

    def get_serializer(self, *args, **kwargs):
        kwargs["request"] = _request = Request.objects.filter(
            id=self.kwargs.get("pk")
            ).first()
        if not _request or _request.status == Request._STATUSES.done:
            raise NotFound
        return super().get_serializer(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        if not is_phone_mechanic():
            raise NotFound
        return super().post(request, *args, **kwargs)


class OrderReceiveAPIView(RetrieveAPIView):
    serializer_class = OrderCreateSerializer

    def get_object(self):
        order = Order.objects.filter(unique_path_field=self.kwargs.get("unique_path")).first()
        if not order:
            raise NotFound
        return order


class OrderUserUpdateAPIView(UpdateAPIView):
    serializer_class = OrderUserUpdateSerializer
    queryset = Order.objects.all()

    def get_object(self):
        order = Order.objects.filter(unique_path_field=self.kwargs.get("unique_path")).first()
        if not order:
            raise NotFound

        if order.is_paid():
            raise exceptions.ValidationError({"detail": [pgettext_lazy("ValidationError", "allredy Pay")]})

        return order


class EmployeeListAPIView(ListAPIView):
    serializer_class = EmployeeSerializer
    permission_classes = (IsAuthenticated,)
    queryset = Employee.objects.all()


class TransCrtAPIView(GenericAPIView):
    # permission_classes = [permissions.IsAuthenticated,]
    serializer_class = TransCrtSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order_pp = serializer.validated_data['id']
        print(order_pp)
        id_order = get_session(request, 'id_order', crypt=True)  # TODO: Проверить работу сессии id_order
        print(f"id_order: {id_order}")
        # drop_session(request, 'id_order')
        try:
            order = Order.objects.get(pk=order_pp)
            print(order)
        except Order.DoesNotExist:
            # Обработайте ошибку, например, верните HTTP 404
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
        obj_transaction = Transaction.objects.create(
            ref=order_pp,
            order=order
            )

        return Response(
            data={"any": "result"},
            )


class TransUptAPIView(GenericAPIView):
    serializer_class = TransCrtSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order_pp = serializer.validated_data['id']

        transaction = Transaction.objects.filter(ref=order_pp).first()

        if transaction:
            transaction.status = PAYMENT_STATUSES.paid
            transaction.save()

            order = transaction.order
            if user := transaction.order.partner:

                if partner := Partner.objects.filter(user=user).first():
                    partner.balance = F('balance') + order.prepayment
                    partner.save()
                    partner.refresh_from_db()
                    balance = partner.balance

                else:
                    balance = order.prepayment
                    Partner.objects.create(
                        user=user,
                        balance=balance,
                        )

                data = {
                    'partner': user,
                    'amount': order.prepayment,
                    'balance': balance,
                    'type_transactions': TRANSACTIONS_STATUS.income,
                    'order': order
                    }

                create_transaction(**data)

            from ..tasks import notifications
            notifications.delay(transaction.id)
            # print("before send")
            # transaction.order.send_message()
            # print("after send")
            # if is_phone_mechanic():
            #     order_after_pay_sms(transaction.order)

        return Response(data={"any": "result"})


class IsCustomGroup(IsAuthenticated):
    """ Проверка на группу Custom и на is_staff """

    def has_permission(self, request, view):
        return (super().has_permission(request, view) and
                (request.user.groups.filter(name='Custom').exists() or request.user.is_superuser))


class OrderApiView(RetrieveAPIView):
    """API для получения заказа по уникальному пути"""
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    lookup_url_kwarg = 'unique_path'
    lookup_field = 'unique_path_field'
    permission_classes = (IsCustomGroup,)


@api_view(['GET'])  # Изменили метод на GET, так как кнопки будут отправлять GET запрос
def update_order_status(request, unique_path):
    """API для обновления статуса заказа"""
    print("update_order_status")
    order = get_object_or_404(Order, unique_path_field=unique_path)
    new_status = request.GET.get('status')  # Получаем статус из параметров URL

    if not new_status:
        return Response({'error': 'No status provided'}, status=status.HTTP_400_BAD_REQUEST)

    # Логика для изменения статуса
    if new_status == 'en_route':
        order.status = 'en_route'
        order.save()
        print("Отправляем СМС Клиенту об выезде мастера")
        _send_sms(phone=order.phone, message="Your master has already left. 7.1.4")

    elif new_status == 'arrived':
        order.status = 'arrived'
        order.save()
        _send_sms(phone=order.phone, message="Your master has already arrived.7.1.6")
        print("Отправляем СМС Клиенту об приезде мастера. 7.1.6")

    elif new_status == 'completed':
        order.status = 'completed'
        order.save()
        print("Заказ выполнен, отправляем СМС Клиенту об окончании работ.")
        _send_sms(phone=order.phone, message="The master has completed the order, please pay for the work. 7.1.7")

    elif new_status == 'paid':
        order.status = 'paid'
        order.save()
        print("Оплату получил.")
        # todo сделать страницу подтверждения оплаты


    else:
        return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)

    redirect_url = reverse('unique_path', kwargs={'unique_path': order.unique_path_field})
    return HttpResponseRedirect(redirect_url)
