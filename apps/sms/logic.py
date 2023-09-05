import time
from typing import List
from urllib.parse import urlencode

import requests
from constance import config
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.template import Context
from django.template import Template
from django.urls import reverse

from .models import EmailTemplate
from .models import SMSSendHistory
from .models import get_timeout_amount


def generate_link(path):
    return "{}://{}{}".format(
        ('https' if hasattr(settings, "IS_SSL") and getattr(settings, "IS_SSL") else "http"),
        Site.objects.first().domain, path
        )


def send_custom_mail(
        order,
        recipient_type="Customer",
        template_choice=None,
        action=None,
        extra_context=None,
        changes=None
        , from_send=None
        ):
    """Функция отправки письма"""
    try:
        en_route_link = f"http://{Site.objects.first().domain}/order/update_status/{order.unique_path_field}?{urlencode({'status': 'en_route'})}"
        arrived_link = f"http://{Site.objects.first().domain}/order/update_status/{order.unique_path_field}?{urlencode({'status': 'arrived'})}"
        paid_link = f"http://{Site.objects.first().domain}/order/update_status/{order.unique_path_field}?{urlencode({'status': 'paid'})}"

        context = {
            "order": {
                "id": str(order.id),
                "name": order.name,
                "phone": order.phone,
                "comment": order.comment,
                "car_registration": order.car_registration,
                "manufacture": order.car.manufacturer if order.car else None,
                "confirm_work": order.confirm_work,
                "partner": order.partner.username if order.partner else None,
                "car_model": order.car.car_model if order.car else None,
                "car_year": order.car_year,
                "distance": order.distance,
                "service": order.service.title if order.service else None,
                "price": order.price,
                "prepayment": order.prepayment,
                "post_code": order.post_code,
                "link": f"http://{Site.objects.first().domain}/link/{order.unique_path_field}/",
                "en_route_link": en_route_link,
                "arrived_link": arrived_link,
                "paid_link": paid_link,
                },
            "site": Site.objects.first().domain,
            "recipient_type": recipient_type,
            "changes": list(changes.keys()) if changes else [],
            "show_links": {
                "show_en_route": True,
                "show_arrived": True,
                "show_paid": True,
                },
            **(extra_context or {}),
            }

        try:
            email_template_obj = EmailTemplate.objects.get(subject=template_choice)
        except EmailTemplate.DoesNotExist:
            print(f"No email template found for {template_choice}")
            return

        if recipient_type == "Worker":
            if order.partner and order.partner.email:
                recipient_list = [order.partner.email]
                print(f"Sending to partner email. {recipient_list}")
            else:
                print("No partner or partner email. Sending to default email.")
            subject = email_template_obj.subject
        else:
            subject = email_template_obj.subject
            recipient_list = [config.ADMIN_EMAIL]

            # Преобразование шаблона электронной почты в объект Template
        email_template = Template(email_template_obj.html_content)
        print(f"email_template: {email_template}")
        # Рендеринг шаблона
        rendered_template = email_template.render(Context(context))
        send_mail(
            subject=subject,
            message='Here is the message.',
            from_email=f'{config.ADMIN_EMAIL}',
            recipient_list=[order.partner.email if order.partner else config.ADMIN_EMAIL],
            html_message=rendered_template,
            fail_silently=False,
            )

    except Exception as e:
        print(f"Error occurred: {e}")
        _send_sms(phone=config.PHONE, message=f"Error Email: {e}")


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


def _send_sms(phone: str, message: str) -> [int, str]:
    if settings.SMS_SEND_MODE == 'production':
        response = requests.get(
            config.SMS_ROUTE, params={
                "input1": phone,
                "input2": message,
                "input3": config.SMS_PASSWORD,
                }
            )

        print(f"_send_sms: {phone}, {message}")

        if response.status_code == 200:
            # Если SMS успешно отправлено, создайте запись в базе данных с успешным статусом
            SMSSendHistory.objects.create(phone_number=phone, message=message, success=True)
        else:
            # Если SMS не отправлено, создайте запись в базе данных с неудачным статусом
            SMSSendHistory.objects.create(phone_number=phone, message=message, success=False)
        return response.status_code, response.content
    else:
        print(f"SMS not sent in test mode: {phone}, {message}")
        message = f"SMS not sent in test mode: {phone}, {message}"
        SMSSendHistory.objects.create(phone_number=phone, message=message, success=False)
        return 200, "SMS not sent in test mode"


# Отправка смс админу
def send_sms_admin(order, action=""):
    """Отправка смс администратору"""
    print(f"func sms/logic send_sms_admin")
    status_code: int = 0
    message: str = ""
    site = Site.objects.first()
    try:
        phone = config.PHONE
        if action == "created":
            message = (f"Created №{order.id}."
                       f"http://{site}/link/{order.unique_path_field}")
        elif action == "partial":
            message = (f"Partial payment №{order.id} sum {order.prepayment}."
                       f"http://{site}/link/{order.unique_path_field}")
        elif action == "paid":
            message = (f"The full payment №{order.id} sum {order.price}."
                       f"http://{site}/link/{order.unique_path_field}")
        elif action == "confirmed":
            message = (f"Worker {order.partner} confirmed the order №{order.id}"
                       f" sum {order.price}."
                       f"http://{site}/link/{order.unique_path_field}")
        elif action == "declined":
            message = (f"Worker refused the order №{order.id}. Assign another performer."
                       f"http://{site}/link/{order.unique_path_field}")
        elif action == "email_error":
            message = (f"Error sending email {order.id}."
                       f"http://{site}/link/{order.unique_path_field}")
        time.sleep(get_timeout_amount())
        status_code, _log = _send_sms(phone, message)  # todo: исправить после отладки
        print(f"send_sms_admin: {phone}, {message}")

    except Exception as e:
        if status_code != 200:
            send_notification_to_admin(order, "sms_error")
            print(f"SMS ERROR {status_code}")
        print(e)


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
        send_mail(
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
