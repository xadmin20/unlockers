from django.urls import path, include, re_path

from . import views


urlpatterns = [
    path(
        "api/v1/request/",
        include(((
            path("create/", views.RequestPreCreateAPIView.as_view(), name="create"),
            path("addcar/", views.AddCarAPIView.as_view(), name="add_car"),
            path("unregistered/create/", views.UnregisteredCardRequestCreateAPIView.as_view(),
                name="unregistered_create"
            ),
            path("<int:pk>/receive/", views.RequestReceiveAPIView.as_view(), name="receive"),
            path("<int:pk>/update/", views.RequestUpdateAPIView.as_view(), name="update"),
            path("services/", views.ServicesListAPIView.as_view(), name="services"),
        ), "request_api"))
    ),
    path('change/status/<int:pk>/', views.change_status, name="change_status"),
]
