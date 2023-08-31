from django.contrib.auth.forms import PasswordResetForm
from django.urls import reverse


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
