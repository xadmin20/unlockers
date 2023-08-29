from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'payment_id', 'payer_id', 'status', 'created_at', 'amount')
    list_filter = ('status',)
    search_fields = ('order_id', 'payment_id', 'payer_id')
    readonly_fields = ('order_id', 'payment_id', 'payer_id', 'status', 'created_at', 'amount')
    fieldsets = (
        (None, {
            'fields': ('order_id', 'payment_id', 'payer_id', 'status', 'created_at', 'amount')
            }),
        )
    ordering = ('-created_at',)
