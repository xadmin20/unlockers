# payments/urls.py

from django.urls import path

from .views import ExecutePaymentView
from .views import initiate_payment
from .views import payment_status

urlpatterns = [
    path('execute/', ExecutePaymentView.as_view(), name='execute_payment'),
    path('payment_status/', payment_status, name='payment_status'),
    path('<str:unique_path_field>/', initiate_payment, name='initiate_payment'),
    ]
