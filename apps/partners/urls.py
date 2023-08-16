from django.urls import path, re_path
from .views import (
    LoginView,
    RestorePasswordView,
    ChangeEmailView,
    CabinetView,
)


urlpatterns = [
    path('auth/login/',  LoginView.as_view(), name='login'),
    path('auth/restore-password/confirm/<uid>/<token>/', RestorePasswordView.as_view(), name='restore-password-confirm'),
    path('cabinet/profile/<uid>/<token>/<email>/', ChangeEmailView.as_view(), name='change-email'),
    re_path(r'cabinet/', CabinetView.as_view(), name='cabinet'),
]
