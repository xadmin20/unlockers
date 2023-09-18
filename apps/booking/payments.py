from dataclasses import dataclass

import paypalrestsdk
from constance import config
from django.contrib.sites.models import Site
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.sms.models import is_phone_mechanic
from .models import Order, Transaction, PAYMENT_STATUSES
from .senders import order_after_pay_sms


class PaymentGenerationException(Exception):
    pass


@dataclass
class Payment:
    ref: int
    is_valid: bool
    approval_url: str


def configure_paypal():
    paypalrestsdk.configure({
        'mode': config.PAYPAL_MODE,
        'client_id': config.PAYPAL_CLIENT_ID,
        'client_secret': config.PAYPAL_SECRET,
    })


def generate_payment(order: Order) -> Payment:
    configure_paypal()
    domain = Site.objects.get_current().domain
    request_data = {
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"
        },
        "redirect_urls": {
            "return_url": f'https://{domain}{reverse("paypal_confirm")}',
            "cancel_url": f'https://{domain}{reverse("paypal_cancel")}',
        },
        "transactions": [{
            "item_list": {
                "items": [{
                    "name": str(_("Order payment")),
                    "sku": "item",
                    "price": str(order.prepayment),
                    "currency": "GBP",
                    "quantity": 1
                }]
            },
            "amount": {
                "total": str(order.prepayment),
                "currency": "GBP",
            },
            "description": str(_("This payment transaction description."))
        }]
    }
    payment = paypalrestsdk.Payment(request_data)

    is_valid = False
    approval_url = None

    if payment.create():
        is_valid = True
        for link in payment.links:
            if link.rel == "approval_url":
                approval_url = str(link.href)

    return Payment(
        ref=payment.id if is_valid else None,
        approval_url=approval_url,
        is_valid=is_valid
    )


def make_transaction(order: Order):
    payment = generate_payment(order)
    if not payment.is_valid:
        raise PaymentGenerationException("Payment generation error")
    Transaction.objects.create(ref=payment.ref, order=order)
    return payment.approval_url


def confirm_payment(payment_id, payer_id, token):
    transaction = Transaction.objects.filter(ref=payment_id).first()
    if not transaction:
        return False

    configure_paypal()
    payment = paypalrestsdk.Payment.find(payment_id)
    is_success = payment.execute({'payer_id': payer_id})

    if is_success:
        transaction.status = PAYMENT_STATUSES.paid
        transaction.save()
        transaction.order.send_message()
        if is_phone_mechanic():
            order_after_pay_sms(transaction.order)

    return is_success
