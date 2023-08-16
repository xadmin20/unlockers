from django.views.generic import TemplateView, RedirectView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect

from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode as uid_decoder
from django.contrib.auth.tokens import default_token_generator
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model 
from django.core.validators import validate_email
from django.urls import reverse, reverse_lazy

UserModel = get_user_model()


class LoginView(TemplateView):
    template_name = 'login.jinja'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            # return redirect(reverse('cabinet'))
            return redirect('/cabinet/statistics/')
        return super().dispatch(request, *args, **kwargs)
    

class RestorePasswordView(TemplateView):
    template_name = 'create-password.jinja'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['uid'] = kwargs.get('uid')
        context['token'] = kwargs.get('token')
        
        return context


class CabinetView(LoginRequiredMixin, TemplateView):
    template_name = 'cabinet.jinja'
    login_url = reverse_lazy('login')
    redirect_field_name=None


class ChangeEmailView(RedirectView):
    pattern_name = 'login'
    url = '/cabinet/settings/'

    def get_redirect_url(self, *args, **kwargs):
        uid = force_str(uid_decoder(kwargs.get('uid')))
        email = force_str(uid_decoder(kwargs.get('email')))
        token = kwargs.get('token')

        try:
            user = UserModel._default_manager.get(pk=uid)
            validate_email(email)
            if (default_token_generator.check_token(user, token)
                and email != user.email
                and email == user.partner.change_email):
                user.email = user.username = email
                user.partner.change_email = ''
                user.partner.save()
                user.save()
                
            # raise ValidationError({'token': ['Invalid value']})
            
        except:
            pass
        # print(email)
        # return super().get_redirect_url(*args, **kwargs)
        return reverse(self.pattern_name)
