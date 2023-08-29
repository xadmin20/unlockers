# payments/urls.py

from django.urls import path

from .views import ExecutePaymentView
from .views import initiate_payment

urlpatterns = [
    path('execute/', ExecutePaymentView.as_view(), name='execute_payment'),
    path('<str:unique_path_field>/', initiate_payment, name='initiate_payment'),
    ]
