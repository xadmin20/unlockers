from django.urls import include
from django.urls import path
from django.urls import re_path

from . import views
from .views import OrderApiView

urlpatterns = [
    path(
        "api/v1/order/",
        include(
            ((
                 path("create/", views.OrderCreateAPIView.as_view(), name="create"),
                 path("user/<str:unique_path>/create/", views.UserOrderCreateAPIView.as_view(), name="user_create"),
                 path("employees/", views.EmployeeListAPIView.as_view(), name="employees"),
                 re_path(
                     r"^(?P<unique_path>[a-zA-Z0-9,;=\-_]+)/receive/",
                     views.OrderReceiveAPIView.as_view(),
                     name="receive",
                     ),
                 # re_path(
                 #     r"^(?P<unique_path>[a-zA-Z0-9,;=\-_]+)/pay/",
                 #     views.OrderUserUpdateAPIView.as_view(),
                 #     name="update",
                 #     ),
                 path("create-pay/", views.TransCrtAPIView.as_view(), name="create_pay"),
                 path("check-pay/", views.TransUptAPIView.as_view(), name="check_pay"),
                 path('link/<str:unique_path>/', OrderApiView.as_view(), name='order-detail-api'),

                 ), "order")
            )
        ),
    ]
