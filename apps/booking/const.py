from django.utils.translation import gettext_lazy as _
from model_utils import Choices


ORDER_STATUS_WORK = Choices(
    ("new", _("New")),
    ("confirm", _("Confirm")),
    ("refused", _("Refused")),
)
