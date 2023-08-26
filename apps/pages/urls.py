from django.urls import path
from django.urls import re_path

from . import views

urlpatterns = [
    path("", views.IndexPageView.as_view(), name="index"),
    path("page/<str:slug>/", views.TypicalPageView.as_view(), name="typical"),
    path("payment/confirm/", views.SuccessPaymentView.as_view(), name="paypal_confirm"),
    path("payment/cancel/", views.InvalidPaymentView.as_view(), name="paypal_cancel"),
    path("order/", views.OrderCreateView.as_view(), name="order_create"),
    path("order/<str:unique_path>/create/", views.UserOrderCreateView.as_view(), name="user_order_create"),
    re_path(
        r'^order/(?P<unique_path>[a-zA-Z0-9,;=\-_]+)/pay/',
        views.OrderPayView.as_view(), name="order_pay"
        ),
    re_path(
        r'^order/(?P<unique_path>[a-zA-Z0-9,;=\-_]+)/detail/',
        views.OrderDetailView.as_view(), name="order_detail"
        ),
    ]
