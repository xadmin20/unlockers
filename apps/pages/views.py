from constance import config
from django.http import Http404
from django.shortcuts import render
from django.utils.timezone import datetime
from django.utils.timezone import timedelta
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView
from django.views.generic import TemplateView
from seo.mixins.views import ModelInstanceViewSeoMixin

from apps.booking.location import get_time_to
from apps.booking.models import Order
from apps.request.models import Request
from apps.request.models import ServiceVariation
from apps.sms.models import is_phone_mechanic
from markup.utils import drop_session
from markup.utils import get_session
from .models import MainPage
from .models import Review
from .models import Typical


def not_found(request, *args, **kwargs):
    return render(
        request, "404.jinja",
        {'request': request, 'config': config}
        )


class IndexPageView(ModelInstanceViewSeoMixin, TemplateView):
    template_name = "index.jinja"

    def get_context_data(self, **kwargs):
        main_page = MainPage.objects.first()
        if main_page:
            self.object = kwargs["page"] = main_page
            kwargs["services"] = ServiceVariation.objects.filter(is_display=True)
            kwargs["reviews"] = Review.objects.all()
        return super().get_context_data(**kwargs)



class TypicalPageView(ModelInstanceViewSeoMixin, DetailView):
    template_name = "typical.jinja"
    model = Typical
    queryset = Typical.objects.all()


class SuccessPaymentView(TemplateView):
    template_name = "payment_message_success.jinja"

    def get_context_data(self, **kwargs):
        kwargs["message"] = (
            _("Success message")
            if self.is_valid_transaction
            else _("Something wrong while transaction approving.")
        )
        return super().get_context_data(**kwargs)

    def get(self, request, *args, **kwargs):
        id_order = get_session(request, 'id_order', crypt=True)
        drop_session(request, 'id_order')
        order = Order.objects.get(pk=id_order)
        self.is_valid_transaction = order.is_paid()

        # self.is_valid_transaction = confirm_payment(
        #     payer_id=request.GET.get("PayerID", None),
        #     payment_id=request.GET.get("paymentId", None),
        #     token=request.GET.get("token", None)
        # )
        return super().get(request, *args, **kwargs)


class InvalidPaymentView(TemplateView):
    template_name = "payment_message_invalid.jinja"

    def get_context_data(self, **kwargs):
        kwargs["message"] = _("Payment fail.")
        return super().get_context_data(**kwargs)


class OrderCreateView(TemplateView):
    template_name = "order.jinja"

    def get(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated or not self.request.user.is_staff:
            raise Http404
        return super().get(self, request, *args, **kwargs)


class UserOrderCreateView(DetailView):
    template_name = "user_order.jinja"
    queryset = Request.objects.exclude(status=Request._STATUSES.done)

    def get(self, request, *args, **kwargs):
        if not is_phone_mechanic():
            raise Http404
        return super().get(self, request, *args, **kwargs)


class OrderPayView(TemplateView):
    """Страница оплаты заказа"""
    template_name = "checkout.jinja"

    def get_context_data(self, **kwargs):
        uuid = self.kwargs.get("unique_path")
        order = Order.objects.filter(unique_path_field=uuid).first()
        print("UUID:", uuid)
        print("Order:", order)
        # if not order or order.created_at.replace(tzinfo=None) < (datetime.now() - timedelta(hours=2)):
        #     raise Http404
        kwargs["unique_path"] = uuid
        kwargs["order"] = order

        kwargs["client-id"] = config.PAYPAL_CLIENT_ID
        kwargs["currency"] = "GBP"
        kwargs["form"] = {
            'name': getattr(order, 'name') or '',
            'car_registration': getattr(order, 'car_registration') or '',
            'phone': getattr(order, 'phone') or '',
            'address': getattr(order, 'address') or '',
            'post_code': getattr(order, 'post_code') or '',
            }
        print(kwargs)
        return super().get_context_data(**kwargs)


class OrderDetailView(TemplateView):
    template_name = "order_detail.jinja"

    def get_context_data(self, **kwargs):
        uuid = self.kwargs.get("unique_path")
        order = Order.objects.filter(unique_path_field=uuid).first()
        if not order:
            print("Order not found")
            raise Http404
        kwargs["uuid"] = uuid
        kwargs["order"] = order
        valid_time = datetime.now() - timedelta(hours=1)
        order_native_date_at = order.date_at.replace(tzinfo=None)
        # if order_native_date_at <= valid_time:
        kwargs["arrival_duration_value"], kwargs["arrival_duration_text"] = get_time_to(
            order.post_code or order.request.post_code
            ) or (None, None)

        # time_to_result = get_time_to(order.post_code or order.request.post_code)
        # if time_to_result:
        #     kwargs["arrival_duration_value"], kwargs["arrival_duration_text"] = time_to_result
        # else:
        #     kwargs["arrival_duration_value"], kwargs["arrival_duration_text"] = None, None
        return super().get_context_data(**kwargs)
