import logging

import requests
from django.core.mail import send_mail

from apps.booking.celery import app
from apps.sms.models import is_phone_mechanic
from .models import Transaction
from .senders import order_after_pay_sms

logger = logging.getLogger(__name__)


@app.task
def notifications(transaction_id):
    transaction = Transaction.objects.filter(id=transaction_id).first()
    if transaction:
        transaction.order.send_message()
        print("after send")
        if is_phone_mechanic():
            order_after_pay_sms(transaction.order)


@app.task
def check_server_task():
    url_to_check = "https://adminton.tu"
    try:
        response = requests.get(url_to_check, timeout=10)
        logger.info(response.status_code)
        print(response.status_code)
        if response.status_code != 200:
            raise Exception(f"Unexpected status code: {response.status_code}")
    except Exception as e:
        logger.error(f"Error while checking SMS server: {e}")
        send_mail(
            'SMS Server is DOWN',
            f'Error while checking SMS server: {e}',
            'nickolayvan@gmail.com',
            ['xadmin@bk.ru'],
            fail_silently=False,
            )
