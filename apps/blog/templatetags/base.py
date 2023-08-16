from django_jinja.library import global_function
from constance import config

from apps.sms.models import is_phone_mechanic as _is_phone_mechanic


@global_function
def add_get_param(request, key, value):
    params = request.GET.copy()
    params[key] = value
    return params.urlencode()


@global_function
def is_phone_mechanic():
    return _is_phone_mechanic()

@global_function
def get_google_api_key():
    return config.GOOGLE_API_KEY

@global_function
def get_prepayment():
    return config.PREPAYMENT


@global_function
def get_user_role(user):
    if user.is_authenticated:
        if user.is_staff:
            return 'administrator'
        return 'user'
    return
