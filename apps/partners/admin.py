from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from apps.partners.const import TRANSACTIONS_STATUS, WITHDRAW_STATUS
from apps.partners.transactions import create_transaction
from .models import (
    Partner,
    Withdraw,
    Transactions,
)
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .forms import MyUserCreationForm


class PartnerInline(admin.StackedInline):
    model = Partner
    can_delete = False
    verbose_name_plural = _("Partner")
    # readonly_fields = ('balance', 'change_email')

# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = (PartnerInline,)
    # fieldsets = (
    #     (None, {
    #         'fields': (
    #             'username', 'password', 'first_name',
    #             'last_name', 'email',
    #             )
    #         }
    #     ),
    # )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'email')}
        ),
    )

    add_form = MyUserCreationForm
# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Withdraw)
class WithdrawAdmin(admin.ModelAdmin):
    list_display = (
        "id", "created_at", "amount", "status", "partner",
    )
    list_filter = ('status', 'partner', 'created_at')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        refund = Transactions.objects.filter(
            partner=obj.partner,
            withdraw=obj,
            type_transactions=TRANSACTIONS_STATUS.refund
        ).exists()
        if obj.status == WITHDRAW_STATUS.declined and not refund:
            balance = obj.partner.partner.balance + obj.amount
            data = {
                'partner': obj.partner,
                'amount': obj.amount,
                'balance': balance,
                'type_transactions': TRANSACTIONS_STATUS.refund,
                'withdraw': obj
            }
            
            create_transaction(**data)
            obj.partner.partner.balance = balance
            obj.partner.partner.save()



@admin.register(Transactions)
class TransactionsAdmin(admin.ModelAdmin):
    list_display = (
        "id", "created_at", "amount", "type_transactions", "partner",
    )
    list_filter = ('type_transactions', 'partner', 'created_at')
