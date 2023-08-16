from uuid import UUID

from constance import config
from django.conf import settings
from django.contrib.sites.models import Site
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView
from django.views.generic.detail import DetailView
from postie.shortcuts import send_mail

from apps.booking.forms import OrderForm
from apps.booking.models import Order
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
        u_str = validate_uuid(decrypt_str(self.kwargs.get("uuid")))
        empl_id = decrypt_str(self.kwargs.get("empl_id"))
        status_work = decrypt_str(self.kwargs.get("status"))
        order = False
        if u_str:
            order = Order.objects.filter(uuid=u_str).select_related('responsible').first()

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
                Site.objects.first().domain,
                reverse(
                    "admin:booking_order_change",
                    kwargs={"object_id": order.id}
                ),
            )
            order.confirm_work = status_work
            order.save()
            send_mail(
                settings.POSTIE_TEMPLATE_CHOICES.confirm_order,
                config.ADMIN_EMAIL.split(","),
                {
                    "responsible": order.responsible.name if order.responsible else config.ADMIN_EMAIL,
                    "link": link_order,
                    "status_confirm": status_work,
                }
            )
            kwargs["message"] = _(f"Set status on order - {status_work}")
        else:
            kwargs["message"] = _("no valid link")

        return super().get_context_data(**kwargs)


class OrderDetailView(DetailView):
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

        # Если форма в контексте валидна, вам, возможно, захочется перенаправить на другую страницу
        if 'form' in context and context['form'].is_valid():
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Проверяем, является ли пользователь частью группы Custom или admin
        if self.request.user.groups.filter(name='Worker').exists() or self.request.user.is_staff:
            context['is_executive'] = True
        else:
            context['is_executive'] = False
        # Если это POST-запрос и пользователь имеет право на редактирование
        if self.request.method == "POST" and context['is_executive']:
            form = OrderForm(self.request.POST, instance=self.object)
            if form.is_valid():
                form.save()
                # Здесь можно добавить сообщение или другую логику
        else:
            form = OrderForm(instance=self.object)
        context['form'] = form
        return context
