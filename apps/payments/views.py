import paypalrestsdk
import rest_framework
from constance import config
from django.contrib.sites.models import Site
from django.db.models import Sum
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from rest_framework import status
from rest_framework import views
from rest_framework.response import Response

from apps.booking.models import Order
from apps.booking.senders import send_sms_admin
from apps.payments.models import Payment

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
                    amount=payment.transactions[0].amount.total,  # предположим, что у модели Payment есть поле amount
                    status=status
                    )

                # Обновляем поле prepayment в модели Order
                order.prepayment = new_total_paid
                order.save()
                print(order.unique_path_field + " " + status)
                # Здесь можно добавить функцию отправки СМС
                send_sms_admin(order, action=status)

                return Response({"status": "Payment executed successfully"}, status=rest_framework.status.HTTP_200_OK)
            else:
                return Response(
                    {"error": "Payment could not be executed"},
                    status=rest_framework.status.HTTP_400_BAD_REQUEST
                    )
        except Exception as e:
            print(e)
            return Response(
                {"erro1r": str(e)},
                status=rest_framework.status.HTTP_400_BAD_REQUEST
                )


def initiate_payment(request, unique_path_field):
    # Получите объект заказа из модели Order по unique_path_field
    order = Order.objects.get(unique_path_field=unique_path_field)
    site = Site.objects.get_current().domain
    # Вычисляем сумму оплаты, либо предоплата, либо полная цена
    if order.prepayment == 0:
        amount_to_pay = order.price / 2
    else:
        amount_to_pay = order.price - order.prepayment

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
                        "name": "Order",
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


def send_sms(order):
    print("SMS sent")
    # код для отправки СМС
