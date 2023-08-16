from django.utils.translation import gettext_lazy as _
from model_utils import Choices


WITHDRAW_STATUS = Choices(
    (1, 'not_paid', _("Not Paid")),
    (2, 'paid', _("Paid")),
    (3, 'declined', _("Declined")),
)

TRANSACTIONS_STATUS = Choices(
    (1, 'income', _("INCOME")),
    (2, 'withdraw', _("WITHDRAW")),
    (3, 'refund', _("REFUND")),
    (4, 'cancellation', _("CANCELLATION")),
)

