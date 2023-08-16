from django.urls import path

from . import views


urlpatterns = (
    path("api/v1/review/create/", views.ReviewCreateAPIView.as_view(), name="review_create"),
)
