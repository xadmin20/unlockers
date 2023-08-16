from django.utils.translation import get_language
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings
from postie.shortcuts import send_mail
from django.urls import reverse
from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import gettext as _
from rest_auth import serializers as rest_auth_serializers
from rest_framework import serializers
from standards.drf.serializers import ModelSerializer, Serializer

from apps.partners.api.forms import MPasswordResetForm
from apps.partners.models import Partner

UserModel = get_user_model()


class PasswordResetSerializerApi(rest_auth_serializers.PasswordResetSerializer):
    password_reset_form_class = MPasswordResetForm


class ProfileInfoSerializer(ModelSerializer):
    company_name = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()

    class Meta:
        model = UserModel
        fields = [
            'first_name', 'last_name', 'email',
            'company_name', 'phone',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_partner = Partner.objects.filter(user=self.request.user).exists()
    
    def get_company_name(self, obj):
        if self.is_partner:
            return obj.partner.company_name
        return None

    def get_phone(self, obj):
        if self.is_partner:
            return obj.partner.phone
        return None

# class PartnerSerializer(ModelSerializer):

#     class Meta:
#         model = Partner
#         fields = ['phone', 'company_name']


# class ProfileUpdateSerializer(ModelSerializer):
#     partner = PartnerSerializer()

#     class Meta:
#         model = UserModel
#         fields = ['first_name', 'last_name', 'partner']

#     def update(self, instance, validated_data):
#         partner_data = validated_data.pop('partner')
        
#         instance.first_name = validated_data.get(
#             'first_name', instance.first_name)
#         instance.last_name = validated_data.get(
#             'last_name', instance.last_name)

#         instance.save()
        
#         if Partner.objects.filter(user=instance):
#             instance.partner.company_name = partner_data.get(
#             'company_name', instance.partner.company_name)
#             instance.partner.phone = partner_data.get(
#             'phone', instance.partner.phone)
#             instance.partner.save()
#         else:
#             Partner.objects.create(
#                 user=instance,
#                 **partner_data
#             )

#         return instance

class ProfileUpdateSerializer(Serializer):  
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    phone = serializers.CharField(required=False)
    company_name = serializers.CharField(required=False)

    def save(self):
        first_name = self.validated_data.get('first_name', '')
        last_name = self.validated_data.get('last_name', '')
        phone = self.validated_data.get('phone', '')
        company_name = self.validated_data.get('company_name', '')
        user = self.request.user
        user.first_name = first_name
        user.last_name = last_name
        user.save()

        if partner := Partner.objects.filter(user=user).first():
            partner.company_name = company_name
            partner.phone = phone
            partner.save()
        else:
            Partner.objects.create(
                user=user,
                phone=phone,
                company_name=company_name,
            )
    

class EmailChangeSerializer(Serializer):
    email = serializers.EmailField()

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.request = self.context.get('request')
        
    def send_mail(self, context, email):
        link = 'https://{}{}'.format(
            context["domain"],
            reverse(
                'change-email',
                kwargs={
                    'uid': context['uid'],
                    'token': context['token'],
                    'email': urlsafe_base64_encode(force_bytes(email)),
                }
            )
        )
        
        send_mail(
            event=settings.POSTIE_TEMPLATE_CHOICES.change_email,
            recipients=[email],
            context={
                'var_url_recovery': link
            },
            language=get_language()
        )

    def save(self):
        email = self.validated_data['email']
        user = self.request.user

        if partner := Partner.objects.filter(user=user).first():
            partner.change_email = email
            partner.save()
        else:
            Partner.objects.create(
                user=user,
                change_email=email,
            )


        current_site = get_current_site(self.request)
        site_name = current_site.name
        domain = current_site.domain
        context = {
            'email': email,
            'domain': domain,
            'site_name': site_name,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'user': user,
            'token': default_token_generator.make_token(user),
        }
        
        self.send_mail(context, email)