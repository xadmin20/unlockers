import logging

import requests
from django.core.mail import send_mail

from apps.booking.celery import app
from .models import Transaction
from .senders import order_after_pay_sms

logger = logging.getLogger(__name__)


@shared_task
def send_sms_task(phone, message):
    """Отправка СМС"""
    _send_sms(phone, message)
    logger.info(f"SMS sent to {phone}")
    