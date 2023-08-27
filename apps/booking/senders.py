import time
from pathlib import Path
from typing import *

import requests
from constance import config
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import send_mail as django_send_mail
from django.template import Context
from django.template import Template as DjangoTemplate
from django.urls import reverse
from postie.shortcuts import send_mail

from apps.booking.const import ORDER_STATUS_WORK
from apps.cars.contrib import Car as CarEntity
from apps.cars.contrib import get_car
from apps.sms.models import ORDER_PAYED
from apps.sms.models import REQUEST
from apps.sms.models import SmsMessage
from apps.sms.models import SmsTemplate
from apps.sms.models import TEMPLATES
from apps.sms.models import get_timeout_amount
from markup.utils import crypt_str


def split_sms(content: str) -> List[str]:
    max_length = 150  # Количество символов в одном сообщении
    # Если сообщение короткое, возвращаем его как есть
    if len(content) <= max_length:
        return [content]
    words = content.split()
    current_message = ""
    messages = []
    for word in words:
        if len(current_message) + len(word) + 1 > max_length:  # +1 для пробела
            messages.append(current_message.strip())
            current_message = ""
        current_message += word + " "
    if current_message:
        messages.append(current_message.strip())
    return messages


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
    """Отправка СМС"""
    response = requests.get(
        config.SMS_ROUTE, params={
            "input1": phone,
            "input2": message,
            "input3": config.SMS_PASSWORD,
            }
        )
    print(f"_send_sms: {phone}, {message}")
    return response.status_code, response.content


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

        print(f"send_sms: {phone} - {message_texts}")

        for message_text in message_texts:
            try:
                # Вывод сообщения перед его отправкой
                print(f"Sending SMS: {message_text}")
                time.sleep(get_timeout_amount())

                # Раскомментируйте эту строку, чтобы фактически отправить SMS
                status_code, msg.log = _send_sms(phone, message_text)

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


def generate_link(path):
    return "{}://{}{}".format(
        ('https' if hasattr(settings, "IS_SSL") and getattr(settings, "IS_SSL") else "http"),
        Site.objects.first().domain, path
        )


def request_sms(request):
    """Send sms to user after request created"""
    current_site = Site.objects.first()
    unique_path = crypt_str(request.unique_path_field)
    context = {
        "car_registration": request.car_registration,
        "post_code": request.post_code,
        "service": request.service,
        "price": request.price,
        "prepayment": request.prepayment,
        "link": "{}://{}{}".format(
            (
                'https'
                if hasattr(settings, "IS_SSL") and getattr(settings, "IS_SSL")
                else "http"
            ),
            current_site.domain,
            reverse("unique_path", kwargs={"unique_path": unique_path})
            ),
        }
    print("senders/request_sms", context)
    send_sms(template=REQUEST, context=context, phone=request.phone)


def order_after_pay_sms(order):
    """Send sms to user after order payed"""
    if not order.request:
        return
    context = {
        "car_registration": order.request.car_registration,
        "post_code": order.request.post_code,
        "service": order.service,
        "price": order.price,
        "link": generate_link(
            reverse('unique_path', kwargs={'unique_path': order.unique_path_field})
            )
        }
    send_sms(template=ORDER_PAYED, context=context, phone=order.request.phone)


def send_notification_to_admin(order=None, action=""):
    """Функция отправки уведомления админу подтверждение или отказ от заказа"""
    try:
        site = Site.objects.first()
        print("send_notification_to_admin", order, action)
        if action == "confirmed":
            subject = "Воркер подтвердил заказ"
            message = (f"Воркер {order.partner} подтвердил заказ №{order.id}"
                       f" на сумму {order.price} рублей. Перейдите по ссылке, чтобы просмотреть заказ."
                       f" {generate_link(reverse('unique_path', kwargs={'unique_path': order.unique_path_field}))}")
        elif action == "declined":
            subject = "Воркер отказался от заказа"
            message = (f"Воркер отказался от заказа №{order.id}. Назначьте другого исполнителя."
                       f" Перейдите по ссылке, чтобы просмотреть заказ."
                       f" {generate_link(reverse('unique_path', kwargs={'unique_path': order.unique_path_field}))}")
        elif action == "sms_error":
            subject = "Ошибка отправки СМС"
            if order.id is None:
                message = (f"Ошибка отправки СМС на номер {order.to_phone}."
                           f"Пожалуйста перезвоните для уточнения деталей заказа.")
            else:
                message = (f"Ошибка отправки СМС на номер {order.to_phone}."
                           f" Перейдите по ссылке, чтобы просмотреть заказ."
                           f"{site}/{order.id}/change/")  # todo: придумать как получить улр
        elif action == "parser_error":
            subject = "Ошибка парсинга"
            message = (f"Ошибка парсинга номера {order.car_registration}."
                       f" Перейдите по ссылке, чтобы просмотреть заказ. Телефон клиента {order.to_phone}.")
        elif action == "create_order_error":
            subject = "Ошибка создания заказа"
            message = (f"Ошибка создания заказа. {order.car_registration}."
                       f" Перейдите по ссылке, чтобы просмотреть заказ."
                       f"Позвоните клиенту и уточните детали заказа. {order.to_phone}")
        else:
            return
        django_send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=config.ADMIN_EMAIL.split(","),
            fail_silently=False,
            )

        print("send_notification_to_admin", order, action, "success")

    except Exception as e:
        print(e)
        # todo: отправка СМС о неудачной отправке письма
