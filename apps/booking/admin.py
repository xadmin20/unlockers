from django.contrib import admin
from django.db.models import F
from django.db.transaction import atomic
from django.utils.html import mark_safe
from rangefilter.filter import DateRangeFilter

from apps.partners.const import TRANSACTIONS_STATUS
from apps.partners.models import Partner
from apps.partners.models import Transactions
from apps.partners.transactions import create_transaction
from .const import ORDER_STATUS_WORK
from .models import Employee
from .models import Order
from .models import OrderAttachments
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('ref', 'status', 'order', 'created_at', 'updated_at')
    search_fields = ('ref', 'order__id')
    list_filter = ('status',)


class OrderAttachmentsInline(admin.TabularInline):
    model = OrderAttachments
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = (OrderAttachmentsInline,)
    list_display = (
        "id", "date_at", "created_at", "is_paid",
        "price", "prepayment", "responsible", "confirm_work",
        "phone", "order_detail"
        )
    list_filter = (
        "responsible", 'confirm_work',
        ("created_at", DateRangeFilter),
        ("date_at", DateRangeFilter),
        )
    readonly_fields = ("is_paid", "order_detail")
    search_fields = ("request__car__manufacturer", "request__car__car_model",)

    @atomic()
    def save_model(self, request, obj, form, change):
        amount = 0  # значение по умолчанию
        responsible_old = form.initial.get('responsible')
        responsible_new = form.cleaned_data.get('responsible')
        if responsible_old != (responsible_new.id if responsible_new else None):
            obj.confirm_work = ORDER_STATUS_WORK.new
            obj.send_message_admin()
        super().save_model(request, obj, form, change)
        partner_old = form.initial.get('partner')
        partner_new = form.cleaned_data.get('partner')
        if not Partner.objects.filter(user=partner_new).exists() and partner_new:
            Partner.objects.create(user=partner_new)
        if partner_old:
            if partner_new:
                if partner_old != partner_new.id:
                    transaction = Transactions.objects.filter(
                        partner=partner_old,
                        order=obj,
                        type_transactions=TRANSACTIONS_STATUS.income
                        ).last()
                    if transaction:
                        amount = transaction.amount
                        transaction.partner.partner.balance = F('balance') - amount
                        transaction.partner.partner.save()
                        transaction.partner.refresh_from_db()
                        balance = transaction.partner.partner.balance

                        data = {
                            'partner': transaction.partner,
                            'amount': -amount,
                            'balance': balance,
                            'type_transactions': TRANSACTIONS_STATUS.cancellation,
                            'order': obj
                            }
                        create_transaction(**data)
                    partner_new.partner.balance = F('balance') + amount
                    partner_new.partner.save()
                    partner_new.refresh_from_db()
                    balance = partner_new.partner.balance

                    data = {
                        'partner': partner_new,
                        'amount': amount,
                        'balance': balance,
                        'type_transactions': TRANSACTIONS_STATUS.income,
                        'order': obj
                        }

                    create_transaction(**data)
            else:
                transaction = Transactions.objects.filter(
                    partner=partner_old,
                    order=obj,
                    type_transactions=TRANSACTIONS_STATUS.income
                    ).last()
                if transaction:
                    amount = transaction.amount
                    transaction.partner.partner.balance = F('balance') - amount
                    transaction.partner.partner.save()
                    transaction.partner.refresh_from_db()
                    balance = transaction.partner.partner.balance

                    data = {
                        'partner': transaction.partner,
                        'amount': -amount,
                        'balance': balance,
                        'type_transactions': TRANSACTIONS_STATUS.cancellation,
                        'order': obj
                        }

                    create_transaction(**data)

        elif partner_new:
            amount = obj.prepayment
            partner_new.partner.balance = F('balance') + amount
            partner_new.partner.save()
            partner_new.refresh_from_db()
            balance = partner_new.partner.balance

            data = {
                'partner': partner_new,
                'amount': amount,
                'balance': balance,
                'type_transactions': TRANSACTIONS_STATUS.income,
                'order': obj
                }

            create_transaction(**data)

        result = super().save_model(request, obj, form, change)
        return result

    def order_detail(self, obj):
        if not obj:
            return "No obj"
        # if not obj.is_paid(): # TODO: раньше метод срабатывал из-за оплаты, а сейчас всегда показывает ссылку
        #     return f"Object exists but is_paid() is {obj.is_paid()}"
        link = f"/link/{obj.unique_path_field}/"
        return mark_safe(f"<a href='{link}'>{link}</a>")


admin.site.register(Employee)
