from collections import OrderedDict
from decimal import Decimal

from django.utils.translation import gettext_lazy as _
from model_utils.choices import Choices

PROXY_TYPE_CHOICES = Choices(
    ("auto", "Auto"),
    ("manual", "Manual"),
    )

CONSTANCE_ADDITIONAL_FIELDS = {
    "decimal": ["django.forms.fields.DecimalField", dict(max_digits=19, decimal_places=2, )],
    "image_field": ["django.forms.ImageField", dict(required=True)],
    "file_field": ["django.forms.FileField", dict(required=True)],
    "choices_field": ["django.forms.ChoiceField", dict(choices=PROXY_TYPE_CHOICES._doubles)],
    }

CONSTANCE_CONFIG = {
    "PHONE": ("07501793857", _("Phone"), str),
    "ADDRESS": ("14 Sybil Road, Leicester, LE32EX", _("Address"), str),
    "LOGO": ("-", _("Site logo"), "image_field"),
    "EMAIL": ("support@anlockers.co", _("Email"), str),
    "ADMIN_EMAIL": ("support@anlockers.co", _("Admin email"), str),
    "FAVICON": ("-", _("Favicon"), "file_field"),
    "REVIEW_LINK": ("/", _("Review.io link"), str),
    "REVIEW_LOGO": ("-", _("Review.io logo "), "image_field"),

    "DEFAULT_POST_CODE": ("-", _("Default post code"), str),
    "GOOGLE_API_KEY": ("-", _("Google API key"), str),
    "MAX_FREE_DISTANCE": (0, _("Maximal free distance"), int),
    "MAX_FIRST_PRICE_DISTANCE": (0, _("Maximal first price distance"), int),
    "FIRST_DISTANCE_PRICE": (Decimal(1), _("First distance price"), "decimal"),
    "PREPAYMENT": (Decimal(20), _("Order prepayment in percent"), "decimal"),
    "SECOND_DISTANCE_PRICE": (Decimal(0), _("Second distance price"), "decimal"),
    "SITE": ("https://thelocksmiths247.co.uk", _("Site"), str),
    "PAYPAL_MODE": ("sandbox", _("PayPal mode"), str),
    "PROXY_TYPE": (PROXY_TYPE_CHOICES.auto, _("Proxy type"), "choices_field"),
    "PAYPAL_SECRET": (
        "EO422dn3gQLgDbuwqTjzrFgFtaRLRR5BdHEESmha49TM",
        _("PayPal client secret"), str
        ),
    "PAYPAL_CLIENT_ID": (
        "EBWKjlELKMYqRNQ6sYvFo64FtaRLRR5BdHEESmha49TM",
        _("PayPal client id"), str
        ),

    "TERMS_LINK": ("/", _("Terms and conditions page link"), str),
    "SITE2": ("-", _("Site2"), str),
    # "IS_PHONE_MECHANIC": (True, _("Is phone mechanic enable"), bool),
    "SMS_ROUTE": ("http://86.2.124.80:8081/get", _("SMS send route"), str),
    "SMS_PASSWORD": ("Phantom", _("SMS send password"), str),
    "GEO_API_KEY": ("D05B2C5BFCE56B8BC1FBB92A0BBE73F7", _("GEO service api key"), str),
    "GEO_ID": ("864894030546775", _("GEO car id"), str),

    'SCHEDULE_TECHNICIAN': ('Main Technician (09:00 - 21:00)', _('Main Technician (09:00 - 21:00)')),
    'NAME_TECHNICIAN': ('Jay', _('Jay')),
    'CONTACT_TECHNICIAN': ('07501793857', _('07501793857')),
    'SCHEDULE_OFFICE': ('Head Office (09:00 - 21:00)', _('Head Office (09:00 - 21:00)')),
    'CONTACT_OFFICE': ('07440964553', _('07440964553')),

    }

CONSTANCE_CONFIG_FIELDSETS = OrderedDict(
    (
        ("General", (
            "PHONE",
            "LOGO",
            "ADDRESS",
            "EMAIL",
            "ADMIN_EMAIL",
            "FAVICON",
            "REVIEW_LINK",
            "REVIEW_LOGO",
            )),
        ("Synchronization", (
            "SITE",
            "TERMS_LINK",
            "SITE2",
            )),
        ("Settings", (
            "DEFAULT_POST_CODE",
            "PROXY_TYPE",
            "MAX_FREE_DISTANCE",
            "MAX_FIRST_PRICE_DISTANCE",
            "FIRST_DISTANCE_PRICE",
            "SECOND_DISTANCE_PRICE",
            "GOOGLE_API_KEY",
            "PREPAYMENT",
            )),
        ("Sms settings", (
            # "IS_PHONE_MECHANIC",
            "SMS_ROUTE",
            "SMS_PASSWORD",
            )),
        ("PayPal", (
            "PAYPAL_MODE",
            "PAYPAL_SECRET",
            "PAYPAL_CLIENT_ID",
            )),
        ("GEO settings", (
            "GEO_API_KEY",
            "GEO_ID",
            )),
        ("Cabinet info", (
            "SCHEDULE_TECHNICIAN",
            "NAME_TECHNICIAN",
            "CONTACT_TECHNICIAN",
            "SCHEDULE_OFFICE",
            "CONTACT_OFFICE",
            )),
        )
    )

CONSTANCE_DATABASE_CACHE_AUTOFILL_TIMEOUT = None
CONSTANCE_REDIS_CONNECTION_CLASS = "django_redis.get_redis_connection"
