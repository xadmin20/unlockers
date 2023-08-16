from django.contrib.auth.forms import PasswordResetForm
from django.urls import reverse
from django.utils.translation import get_language
from django.conf import settings
from postie.shortcuts import send_mail


class MPasswordResetForm(PasswordResetForm):
    def send_mail(self, stn, etn, context, from_email, email, **kwargs):
        link = 'https://{}{}'.format(
            context["domain"],
            reverse(
                'restore-password-confirm',
                kwargs={
                    'uid': context['uid'],
                    'token': context['token']
                }
            )
        )
        
        send_mail(
            event=settings.POSTIE_TEMPLATE_CHOICES.password_recovery_user,
            recipients=[email],
            context={
                'var_url_recovery': link
            },
            language=get_language()
        )
