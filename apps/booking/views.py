from decimal import Decimal
from uuid import UUID

from constance import config
from django.conf import settings
from django.contrib.sites.models import Site
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView
from django.views.generic.detail import DetailView
from seo.mixins.views import ModelInstanceViewSeoMixin

from apps.booking.forms import ClientOrderForm
from apps.booking.forms import OrderForm
from apps.booking.models import Order
from apps.sms.logic import _send_sms
from apps.sms.logic import send_custom_mail
from markup.utils import decrypt_str


def validate_uuid(uuid_str):
    val_uuid = ''
    try:
        val_uuid = UUID(uuid_str, version=4)
    except ValueError:
        return False

    return val_uuid


class OrderConfirmTempaliteView(TemplateView):
    template_name = "payment_message_success.jinja"

    def get_context_data(self, **kwargs):

        u_str = validate_uuid(decrypt_str(self.kwargs.get("unique_path_field")))
        empl_id = decrypt_str(self.kwargs.get("empl_id"))
        status_work = decrypt_str(self.kwargs.get("status"))
        order = False
        if u_str:
            order = Order.objects.filter(unique_path_field=u_str).select_related('responsible').first()

        if order and (
                order.responsible.pk == int(empl_id)
                if order.responsible
                else empl_id == "admin"
        ):
            link_order = "{}://{}{}".format(
                (
                    'https'
                    if hasattr(settings, "IS_SSL") and getattr(settings, "IS_SSL")
                    else "http"
                ),
                Site.objects.last().domain,
                reverse(
                    "admin:booking_order_change",
                    kwargs={"object_id": order.id}
                    ),
                )
            order.confirm_work = status_work
            order.save()
            kwargs["message"] = _(f"Set status on order - {status_work}")
        else:
            kwargs["message"] = _("no valid link")
        return super().get_context_data(**kwargs)


class OrderDetailView(ModelInstanceViewSeoMixin, DetailView, TemplateView):
    """Просмотр заказа"""
    model = Order
    template_name = 'order.html'
    context_object_name = 'object'

    def get_success_url(self):
        return self.request.path

    def get_object(self, queryset=None):
        unique_link = self.kwargs.get('unique_path')
        return get_object_or_404(Order, unique_path_field=unique_link)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        if 'form' in context and context['form'].is_valid():
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        # Этот код гарантирует, что self.object установлен перед вызовом родительского метода
        if not hasattr(self, 'object'):
            self.object = self.get_object()

        context = super().get_context_data(**kwargs)
        payment_status = self.request.GET.get('payment_status', None)
        context['is_paid'] = self.object.is_paid()
        if payment_status == 'success':
            context['payment_message'] = 'Payment was successful.'
        elif payment_status == 'failure':
            context['payment_message'] = 'Payment failed.'

        if self.object.status != 'paid':
            if self.request.user.groups.filter(name='Worker').exists() or self.request.user.is_staff:
                context['is_executive'] = True
                form_class = OrderForm
            else:
                context['is_executive'] = False
                form_class = ClientOrderForm

            if self.request.method == "POST" and (context['is_executive'] or not context['is_executive']):
                form = form_class(self.request.POST, instance=self.object)
                if form.is_valid():
                    form.save()
            else:
                form = form_class(instance=self.object)
            context['prepayment_amount'] = self.object.price * Decimal("0.5")
            context['form'] = form
            print(
                f"User: {self.request.user}, Is executive: {context['is_executive']}, Form used: {form_class.__name__}"
                )

            # Проверяем, больше ли цена нуля и не оплачен ли заказ
            if self.object.price > Decimal("0.0") and self.object.prepayment < self.object.price:
                context['show_save_button'] = True
            else:
                context['show_save_button'] = False

            context["site"] = Site.objects.last()
            return context
        else:
            context['show_save_button'] = False
            return context


def confirm_order(request, order_id):
    """Подтверждение заказа"""
    order = get_object_or_404(Order, pk=order_id)
    order.status = "confirmed"
    order.save()
    send_custom_mail(
        order=order,
        recipient_type="Worker",
        template_choice="confirmed"
        )
    _send_sms(
        phone=order.phone,
        message=f"The worker is appointed, wait for a call from him"
        )

    return redirect('unique_path', unique_path=order.unique_path_field)


def decline_order(request, order_id):
    """Отказ воркера от выполнения заказа"""
    order = get_object_or_404(Order, pk=order_id)
    order.partner = None
    order.save()
    site = Site.objects.last()
    link_order = order.unique_path_field
    _send_sms(phone=config.PHONE, message=f"Refusal to fulfill an order http://{site}/link/{link_order}")
    return redirect('unique_path', unique_path=order.unique_path_field)
