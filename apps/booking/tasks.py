from app.celery import app
from .models import Transaction
from apps.sms.models import is_phone_mechanic
from .senders import order_after_pay_sms


@app.task
def notifications(transaction_id):
    transaction = Transaction.objects.filter(id=transaction_id).first()
    if transaction:
        transaction.order.send_message()
        print("after send")
        if is_phone_mechanic():
            order_after_pay_sms(transaction.order)
