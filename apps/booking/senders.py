import time
from pathlib import Path
from typing import *

from constance import config
from django.conf import settings
from django.contrib.sites.models import Site
from django.template import Template as DjangoTemplate, Context
from django.urls import reverse
from postie.shortcuts import send_mail

from apps.booking.const import ORDER_STATUS_WORK
from apps.cars.contrib import get_car, Car as CarEntity
from apps.sms.models import TEMPLATES, REQUEST, ORDER_PAYED, SmsTemplate, SmsMessage
from apps.sms.models import get_timeout_amount
from markup.utils import crypt_str


class Sender:

    def __init__(self, order):
        self.order = order

    def __generate_link(self, path):
        if not hasattr(self, "_current_site") or not getattr(self, "_current_site"):
            self._current_site = Site.objects.first()
        return "{}://{}{}".format(
            ('https' if hasattr(settings, "IS_SSL") and getattr(settings, "IS_SSL") else "http"),
            self._current_site.domain, path
        )

    @property
    def responsible(self):
        return (
            ([self.order.responsible.email], self.order.responsible.id)
            if self.order.responsible else (config.ADMIN_EMAIL.split(","), "admin")
        )

    def push_in_admin(self):
        """Send a message to the admin about the new order"""
        responsible_email, responsible_id = self.responsible
        link_confirm = self.__generate_link(reverse(
            "confirm_order", kwargs={
                "unique_path_field": crypt_str(self.order.unique_path_field),
                "empl_id": crypt_str(responsible_id),
                "status": crypt_str(ORDER_STATUS_WORK.confirm)
            },
        ))
        link_refused = self.__generate_link(reverse(
            "confirm_order", kwargs={
                "unique_path_field": crypt_str(self.order.unique_path_field),
                "empl_id": crypt_str(responsible_id),
                "status": crypt_str(ORDER_STATUS_WORK.refused)
            },
        ))
        send_mail(
            settings.POSTIE_TEMPLATE_CHOICES.employee_order_admin,
            responsible_email,
            {
                "date_at": self.order.date_at,
                "price": self.order.price,
                "prepayment": self.order.prepayment,
                "comment": self.order.comment,
                "responsible": responsible_email,
                "name": self.order.name,
                "car_registration": self.order.car_registration,
                "phone": self.order.phone,
                "address": self.order.address,
                "post_code": self.order.post_code,
                "link": self.__generate_link(
                    reverse("admin:booking_order_change", kwargs={"object_id": self.order.id})
                ),
                "link_confirm": link_confirm,
                "link_refused": link_refused,

            }
        )

    def push(self):
        if self.order.request and self.order.request.car:
            car_entity = CarEntity(
                manufacturer=self.order.request.car.manufacturer,
                car_model=self.order.request.car.car_model,
                manufactured=self.order.request.car_year,
            )
        else:
            try:
                car_entity: CarEntity = get_car(self.order.car_registration)
            except:
                car_entity = CarEntity(
                    manufacturer="",
                    car_model="",
                    manufactured="",
                )
        responsible_email, responsible_id = self.responsible
        link_confirm = self.__generate_link(reverse(
            "confirm_order", kwargs={
                "unique_path_field": crypt_str(self.order.unique_path_field),
                "empl_id": crypt_str(responsible_id),
                "status": crypt_str(ORDER_STATUS_WORK.confirm)
            },
        ))
        link_refused = self.__generate_link(reverse(
            "confirm_order", kwargs={
                "unique_path_field": crypt_str(self.order.unique_path_field),
                "empl_id": crypt_str(responsible_id),
                "status": crypt_str(ORDER_STATUS_WORK.refused)
            },
        ))
        print("Try to send message")

        if self.order.partner and self.order.partner.email:
            responsible_email.append(self.order.partner.email)
        if config.ADMIN_EMAIL:
            admin_emails = config.ADMIN_EMAIL.split(",")
            responsible_email = list(set(admin_emails + responsible_email))

        send_mail(
            settings.POSTIE_TEMPLATE_CHOICES.employee_order,
            responsible_email,
            {
                "date_at": self.order.date_at,
                "price": self.order.price,
                "prepayment": self.order.prepayment,
                "comment": self.order.comment,
                "responsible": responsible_email,
                "name": self.order.name,
                "car_registration": self.order.car_registration,
                "manufacture": car_entity.manufacturer,
                "car_model": car_entity.car_model,
                "car_year": car_entity.manufactured,
                "phone": self.order.phone,
                "address": self.order.address,
                "post_code": self.order.post_code,
                "link": self.__generate_link(
                    reverse("admin:booking_order_change", kwargs={"object_id": self.order.id})
                ),
                "link_confirm": link_confirm,
                "link_refused": link_refused,

            },
            **(dict(
                attachments=[
                    {
                        item.file.url.split("/")[-1]: Path(
                            f"{settings.BASE_ROOT}/{item.file.url}"
                        ).open("rb")
                    }
                    for item in self.order.attachments.all()
                ]
            ) if self.order.attachments.exists() else {})
        )


def _send_sms(phone: str, message: str) -> [int, str]:
    # response = requests.get(config.SMS_ROUTE, params={
    #     "input1": phone,
    #     "input2": message,
    #     "input3": config.SMS_PASSWORD,
    # })
    print(phone, message)  # TODO: uncomment

    # return response.status_code, response.content # TODO: uncomment
    return 200, "response.content"


def generate_message(context: Dict, template_name: TEMPLATES) -> [str, str, str]:
    template = SmsTemplate.objects.filter(template=template_name).first()
    context = Context(context)
    return (
        DjangoTemplate(template.message).render(context),
        DjangoTemplate(template.message2).render(context),
        DjangoTemplate(template.message3).render(context)
    )


def send_sms(template: TEMPLATES, context: Dict, phone: str):
    """Send a message to the phone number"""
    msg = SmsMessage(
        to_phone=phone,
        template=template,
    )
    message_texts = msg.message, msg.message2, msg.message3 = generate_message(context, template)
    all_valid = True
    for message_text in message_texts:
        try:
            print(message_text)
            time.sleep(get_timeout_amount())
            status_code, msg.log = _send_sms(phone, message_text)
        except Exception as e:
            print(e)
            msg.log = msg.log or "" + f"\n{str(e)}"
            status_code = None
        if status_code != 200:
            all_valid = False
        print(status_code)
    msg.is_success = all_valid
    msg.save()
    return msg


def generate_link(path):
    return "{}://{}{}".format(
        ('https' if hasattr(settings, "IS_SSL") and getattr(settings, "IS_SSL") else "http"),
        Site.objects.first().domain, path
    )


def request_sms(request):
    """Send sms to user after request created"""
    context = {
        "car_registration": request.car_registration,
        "post_code": request.post_code,
        "service": request.service,
        "price": request.price,
        "prepayment": request.prepayment,
        "link": generate_link(reverse(
            "user_order_create", kwargs={"pk": request.id}
        ))
    }
    print("senders/request_sms", context)
    send_sms(template=REQUEST, context=context, phone=request.phone)


def order_after_pay_sms(order):
    if not order.request:
        return
    context = {
        "car_registration": order.request.car_registration,
        "post_code": order.request.post_code,
        "service": order.service,
        "price": order.price,
        "link": generate_link(reverse(
            "order_detail", kwargs={"uuid": order.uuid}
        ))
    }
    send_sms(template=ORDER_PAYED, context=context, phone=order.request.phone)
