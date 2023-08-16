from django.urls import path, re_path

from . import views
from .views import OrderDetailView

# app_name = "order"
urlpatterns = [
    re_path(
        r"^order/confirm/(?P<uuid>[a-zA-Z0-9,;=\-_]+)/(?P<empl_id>[a-zA-Z0-9,;=\-_]+)/(?P<status>[a-zA-Z0-9,;=\-_]+)/",
        views.OrderConfirmTempaliteView.as_view(), name="confirm_order"
    ),
    path('link/<str:unique_path>/', OrderDetailView.as_view(), name='unique_path'),
]
