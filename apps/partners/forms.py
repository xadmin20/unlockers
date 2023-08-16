from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import validate_email


class MyUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    