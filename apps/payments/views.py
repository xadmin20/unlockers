import time
from pprint import pprint

import paypalrestsdk
import rest_framework
from constance import config
from django.contrib import messages
from django.contrib.sites.models import Site
from django.db.models import Sum
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from rest_framework import status
from rest_framework import views
from rest_framework.response import Response
from constance import config

from apps.booking.models import Order
from apps.payments.models import Payment
from apps.sms.logic import _send_sms
from apps.sms.logic import send_custom_mail

# Настройка PayPal
paypalrestsdk.configure(
    {
        'mode': config.PAYPAL_MODE,
        'client_id': config.PAYPAL_CLIENT_ID,
        'client_secret': config.PAYPAL_SECRET,
        }
    )


class ExecutePaymentView(views.APIView):
    """Представление для обработки платежа"""

    def get(self, request, *args, **kwargs):
        payment_id = request.GET.get("paymentId")
        payer_id = request.GET.get("PayerID")
        return self.process_payment(payment_id, payer_id)

    def post(self, request, *args, **kwargs):
        payment_id = request.data.get("paymentId")
        payer_id = request.data.get("payerId")
        return self.process_payment(payment_id, payer_id)

    def process_payment(self, payment_id, payer_id):
        """Обработка платежа"""
        payment = paypalrestsdk.Payment.find(payment_id)
        try:
            if payment.execute({"payer_id": payer_id}):
                # Получаем заказ по unique_path_field или id
                order = Order.objects.get(unique_path_field=payment.transactions[0].item_list.items[0].sku)

                # Получаем текущую сумму всех платежей по этому заказу
                total_paid = Payment.objects.filter(order_id=order).aggregate(Sum('amount'))['amount__sum'] or 0

                # Вычисляем новую сумму после текущего платежа
                total_paid = int(total_paid)  # или float(total_paid)
                transaction_amount = float(payment.transactions[0].amount.total)  # или int(...)
                new_total_paid = total_paid + transaction_amount

                # Проверяем, является ли платеж частичным или полным
                if new_total_paid < order.price:
                    status = "partial"
                else:
                    status = "paid"

                # Создаем новый платеж в модели Payment
                Payment.objects.create(
                    order_id=order,
                    payment_id=payment_id,
                    payer_id=payer_id,
                    amount=payment.transactions[0].amount.total,
                    status=status,
                    description=payment.transactions[0].description
                    )

                # Обновляем поле prepayment в модели Order
                order.prepayment = new_total_paid
                order.save()
                print(order.unique_path_field + " " + status)
                # Здесь можно добавить функцию отправки СМС
                _send_sms(
                    phone=order.phone, message=f"Your order {order.unique_path_field}"
                                               f" paid sum {order.prepayment}"
                    )
                # Здесь можно добавить функцию отправки почты
                # Делаем проверку, есть ли у Order partner
                if order.partner:
                    send_custom_mail(order=order, recipient_type='Worker', template_choice='send_worker_new')
                    time.sleep(3)
                send_custom_mail(order=order, recipient_type='Customer', template_choice='add_pay')
                site = Site.objects.last()

                return HttpResponseRedirect(
                    f'//{site}/link/{order.unique_path_field}/?payment_status=success'
                    )
            else:
                return Response(
                    {"error": "Payment could not be executed"},
                    status=rest_framework.status.HTTP_400_BAD_REQUEST
                    )

        except Exception as e:
            print(e)
            return Response(
                {"error": str(e)},
                status=rest_framework.status.HTTP_400_BAD_REQUEST
                )


def initiate_payment(request, unique_path_field):
    """Представление для инициализации платежа"""
    # Получите объект заказа из модели Order по unique_path_field
    print(f"Trying to find an order with unique_path_field: {unique_path_field}")

    order = get_object_or_404(Order, unique_path_field=unique_path_field)
    site = Site.objects.last()
    # Вычисляем сумму оплаты, либо предоплата, либо полная цена
    prepayment_rate = config.PREPAYMENT / 100  #  todo проценты предоплаты
    if order.prepayment == 0:
        amount_to_pay = order.price * prepayment_rate  # 20% предоплаты, если PREPAYMENT = 20
    else:
        amount_to_pay = order.price - order.prepayment
    amount_to_pay = round(amount_to_pay, 2)
    # Создание объекта платежа в PayPal
    payment = paypalrestsdk.Payment(
        {
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
                },
            "redirect_urls": {
                "return_url": f"http://{site}/payments/execute/",
                "cancel_url": f"http://{site}/payments/cancel/"
                },
            "transactions": [{
                "item_list": {
                    "items": [{
                        "name": "Deposit",
                        "sku": str(order.unique_path_field),
                        "price": str(amount_to_pay),
                        "currency": "GBP",
                        "quantity": 1
                        }]
                    },
                "amount": {
                    "total": str(amount_to_pay),
                    "currency": "GBP"
                    },
                "description": f"This is the payment for order with unique path: {order.unique_path_field}"
                }]
            }
        )

    if payment.create():
        # Получите URL для перенаправления пользователя на страницу оплаты PayPal
        for link in payment.links:
            if link.method == "REDIRECT":
                redirect_url = link.href
        return HttpResponseRedirect(redirect_url)
    else:
        return JsonResponse({"error": payment.error})


def payment_status(request):
    """Страница для отображения статуса платежа"""
    print("payment_status")
    pprint(request.GET)
    status = request.GET.get('status')
    unique_path_field = request.GET.get('unique_path_field')

    if status == 'success':
        messages.success(request, 'Платеж успешно прошел!')
    else:
        messages.error(request, 'Платеж не прошел.')

    return render(request, 'payment_status.html')
