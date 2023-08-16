from django.urls import path
from . import views


urlpatterns = [
    path("blog/", views.BlogView.as_view(), name="blog"),
    path("blog/<str:slug>/detail/", views.PostDetailView.as_view(), name="blog_detail"),
]
