from django.urls import path
from django.urls import re_path

from . import views
from .views import OrderDetailView

# app_name = "order"
urlpatterns = [
    re_path(
        r"^order/confirm/(?P<unique_path>[a-zA-Z0-9,;=\-_]+)/(?P<empl_id>[a-zA-Z0-9,;=\-_]+)/(?P<status>[a-zA-Z0-9,;=\-_]+)/",
        views.OrderConfirmTempaliteView.as_view(), name="confirm_order"
        ),
    path('link/<str:unique_path>/', OrderDetailView.as_view(), name='unique_path'),
    path('order_yes/<int:order_id>/', views.confirm_order, name='confirm_order_'),  # TODO: rename
    path('order_no/<int:order_id>/', views.decline_order, name='decline_order'),
    ]
