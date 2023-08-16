from django.views.generic import DetailView, TemplateView
from django.shortcuts import render
from django.http import Http404
from django.utils.timezone import datetime, timedelta
from django.utils.translation import gettext_lazy as _

from constance import config
from seo.mixins.views import ModelInstanceViewSeoMixin

from apps.booking.models import Order
from apps.request.models import ServiceVariation, Request
from apps.sms.models import is_phone_mechanic
from apps.booking.location import get_time_to

from .models import Typical, MainPage, Review

from markup.utils import get_session, drop_session


def not_found(request, *args, **kwargs):
    return render(
        request, "404.jinja", 
        {'request': request, 'config': config}
    )


class IndexPageView(ModelInstanceViewSeoMixin, TemplateView):
    template_name = "index.jinja"

    def get_context_data(self, **kwargs):
        self.object = kwargs["page"] = MainPage.objects.first()
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
    template_name = "checkout.jinja"

    def get_context_data(self, **kwargs):
        uuid = self.kwargs.get("uuid")
        order = Order.objects.filter(uuid=uuid).first()
        if not order or order.created_at.replace(tzinfo=None) < (datetime.now() - timedelta(hours=2)):
            raise Http404
        kwargs["uuid"] = uuid
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

        return super().get_context_data(**kwargs)


class OrderDetailView(TemplateView):
    template_name = "order_detail.jinja"

    def get_context_data(self, **kwargs):
        uuid = self.kwargs.get("uuid")
        order = Order.objects.filter(uuid=uuid).first()
        if not order:
            raise Http404
        kwargs["uuid"] = uuid
        kwargs["order"] = order
        valid_time = datetime.now() - timedelta(hours=1)
        order_native_date_at = order.date_at.replace(tzinfo=None)
        # if order_native_date_at <= valid_time:
        kwargs["arrival_duration_value"], kwargs["arrival_duration_text"] = get_time_to(
            order.post_code or order.request.post_code) or (None, None)

        # time_to_result = get_time_to(order.post_code or order.request.post_code)
        # if time_to_result:
        #     kwargs["arrival_duration_value"], kwargs["arrival_duration_text"] = time_to_result
        # else:
        #     kwargs["arrival_duration_value"], kwargs["arrival_duration_text"] = None, None
        return super().get_context_data(**kwargs)
