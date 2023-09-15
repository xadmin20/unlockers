import time
from typing import *

from constance import config
from django.conf import settings
from django.contrib.sites.models import Site
from django.template import Context
from django.template import Template as DjangoTemplate
from django.urls import reverse

from apps.booking.const import ORDER_STATUS_WORK
from apps.cars.contrib import Car as CarEntity
from apps.cars.contrib import get_car
from apps.sms.logic import send_custom_mail
from apps.sms.logic import send_notification_to_admin
from apps.sms.models import REQUEST
from apps.sms.models import SmsMessage
from apps.sms.models import SmsTemplate
from apps.sms.models import TEMPLATES
from apps.sms.models import get_timeout_amount
from markup.utils import crypt_str


class Sender:

    def __init__(self, order):
        self.order = order

    def __generate_link(self, path):
        if not hasattr(self, "_current_site") or not getattr(self, "_current_site"):
            self._current_site = Site.objects.last()
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
        """Отправка сообщения в админку"""
        responsible_email, responsible_id = self.responsible
        link_confirm = self.__generate_link(
            reverse(
                "confirm_order", kwargs={
                    "unique_path_field": crypt_str(self.order.unique_path_field),
                    "empl_id": crypt_str(responsible_id),
                    "status": crypt_str(ORDER_STATUS_WORK.confirm)
                    },
                )
            )
        link_refused = self.__generate_link(
            reverse(
                "confirm_order", kwargs={
                    "unique_path_field": crypt_str(self.order.unique_path_field),
                    "empl_id": crypt_str(responsible_id),
                    "status": crypt_str(ORDER_STATUS_WORK.refused)
                    },
                )
            )
        send_custom_mail(
            self,
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
        link_confirm = self.__generate_link(
            reverse(
                "confirm_order", kwargs={
                    "unique_path_field": crypt_str(self.order.unique_path_field),
                    "empl_id": crypt_str(responsible_id),
                    "status": crypt_str(ORDER_STATUS_WORK.confirm)
                    },
                )
            )
        link_refused = self.__generate_link(
            reverse(
                "confirm_order", kwargs={
                    "unique_path_field": crypt_str(self.order.unique_path_field),
                    "empl_id": crypt_str(responsible_id),
                    "status": crypt_str(ORDER_STATUS_WORK.refused)
                    },
                )
            )
        print("Try to send message")

        if self.order.partner and self.order.partner.email:
            responsible_email.append(self.order.partner.email)
        if config.ADMIN_EMAIL:
            admin_emails = config.ADMIN_EMAIL.split(",")
            responsible_email = list(set(admin_emails + responsible_email))


def generate_message(context: Dict, template_name: TEMPLATES) -> List[str]:
    template = SmsTemplate.objects.filter(template=template_name).first()
    context = Context(context)
    full_message = DjangoTemplate(template.message).render(context)

    # Разделить сообщение на несколько SMS, если необходимо
    return split_sms(full_message)
    # return ( # todo: удалить если будет работать разделение сообщений.
    #     DjangoTemplate(template.message).render(context),
    #     DjangoTemplate(template.message2).render(context),
    #     DjangoTemplate(template.message3).render(context)
    #     )


def send_sms(template: TEMPLATES, context: Dict, phone: str):
    """Send a message to the phone number"""
    try:
        msg = SmsMessage(
            to_phone=phone,
            template=template,
            )

        # Теперь generate_message возвращает список SMS-сообщений
        message_texts = generate_message(context, template)
        all_valid = True

        # Сохранить сообщения в объекте msg
        if len(message_texts) > 0:
            msg.message = message_texts[0]
        if len(message_texts) > 1:
            msg.message2 = message_texts[1]
        if len(message_texts) > 2:
            msg.message3 = message_texts[2]

        print(f"send_sms: len: {len(message_texts)} {phone} - {message_texts}")

        for message_text in message_texts:
            try:
                # Вывод сообщения перед его отправкой
                print(f"Sending SMS: {message_text}")
                time.sleep(get_timeout_amount())

                # Раскомментируйте эту строку, чтобы фактически отправить SMS
                # status_code, msg.log = _send_sms(phone, message_text)
                status_code = 200
            except Exception as e:
                print(e)
                msg.log = (msg.log or "") + f"\n{str(e)}"
                status_code = None

            if status_code != 200:
                all_valid = False
                send_notification_to_admin(msg, "sms_error")
                print("SMS ERROR")

            print(status_code)

        msg.is_success = all_valid
        msg.save()
        return msg
    except Exception as e:
        print(e)
        return None


def request_sms(request):
    """Send sms to user after request created"""
    current_site = Site.objects.last()
    unique_path = request.unique_path_field

    # Инициализация пустого контекста
    context = {}

    # Заполняем контекст только теми данными, которые доступны
    if request.car_registration:
        context["car_registration"] = request.car_registration
    if request.post_code:
        context["post_code"] = request.post_code
    if request.service:
        context["service"] = request.service
    if request.price:
        context["price"] = request.price
    if request.prepayment:
        context["prepayment"] = request.prepayment

    try:
        # Если у вас есть все необходимые настройки и данные для создания ссылки
        context["link"] = "{}://{}{}".format(
            (
                'https' if hasattr(settings, "IS_SSL") and getattr(settings, "IS_SSL")
                else 'http'
            ),
            current_site.domain,
            reverse("unique_path", kwargs={"unique_path": unique_path})
            )
    except Exception as e:
        print(f"Could not generate link: {e}")
    print("senders/request_sms", context)
    # Отправляем SMS
    send_sms(template=REQUEST, context=context, phone=request.phone)
