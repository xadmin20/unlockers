from django.db.models import F
from django.utils.translation import pgettext_lazy
from rest_framework import exceptions
from rest_framework.exceptions import NotFound
from rest_framework.generics import (
    CreateAPIView, UpdateAPIView, ListAPIView, RetrieveAPIView, GenericAPIView
)
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from apps.booking.models import Order, Employee, Transaction, PAYMENT_STATUSES
from apps.partners.const import TRANSACTIONS_STATUS
from apps.partners.models import Partner
from apps.partners.transactions import create_transaction
from apps.request.models import Request
from apps.sms.models import is_phone_mechanic
from markup.utils import get_session
from .serializers import (
    OrderCreateSerializer,
    UserOrderCreateSerializer,
    OrderUserUpdateSerializer,
    EmployeeSerializer,

    TransCrtSerializer,
)


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
        order = Order.objects.filter(uuid=self.kwargs.get("uuid")).first()
        if not order:
            raise NotFound
        return order


class OrderUserUpdateAPIView(UpdateAPIView):
    serializer_class = OrderUserUpdateSerializer
    queryset = Order.objects.all()

    def get_object(self):
        order = Order.objects.filter(uuid=self.kwargs.get("uuid")).first()
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
        id_order = get_session(request, 'id_order', crypt=True)
        # drop_session(request, 'id_order')
        order = Order.objects.get(pk=id_order)
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
                request.user.groups.filter(name='Custom').exists() and
                request.user.is_staff)


class OrderApiView(RetrieveAPIView):
    """API для получения заказа по уникальному пути"""
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    lookup_url_kwarg = 'unique_path'
    lookup_field = 'unique_path_field'
    permission_classes = [IsCustomGroup]
