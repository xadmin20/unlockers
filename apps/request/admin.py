from django.contrib import admin
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from rangefilter.filter import DateRangeFilter, DateTimeRangeFilter

from .models import Request, ServiceVariation, Quote


class StatusFilter(admin.SimpleListFilter):
    title = _('Status')
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return (
            (None, _('With contact information')),
            ('all', _('All')),
        )

    def choices(self, cl):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup,
                'query_string': cl.get_query_string({
                    self.parameter_name: lookup,
                }, []),
                'display': title,
            }

    def queryset(self, request, queryset):
        if self.value() == 'all':
            return queryset
        else:
            return queryset.filter(
                Q(contacts__isnull=False)
                | Q(email__isnull=False)
                | Q(phone__isnull=False)
            )


admin.site.register(
    Request,
    list_display=(
        "__str__", "id", "status", 
        "created_at", "car_registration", 
        "post_code", "price", "service", 
        "contacts", "phone"
    ),
    list_editable=("status", ),
    list_filter=('service', 'status', StatusFilter, ('created_at', DateRangeFilter))
)
admin.site.register(
    ServiceVariation,
    list_display=("__str__", "title", "variation", "price", "ordering"),
    list_editable=("title", "variation", "price", "ordering")
)


class RequestFilter(admin.SimpleListFilter):
    title = _('Has request')
    parameter_name = 'has_request'

    def lookups(self, request, model_admin):
        return (
            ('yes', _('Yes')),
            ('no',  _('No')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(request__isnull=False)

        if self.value() == 'no':
            return queryset.filter(request__isnull=True)


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = (
        "car_registration", "service",
        "price", "car_model", "manufacturer",
        "request", "created_at", "phone",
    )
    readonly_fields = ("created_at",)
    list_filter = (('created_at', DateRangeFilter), RequestFilter)

    def phone(self, obj):
        if obj and obj.request:
            return obj.request.phone or obj.request.phone
        return "-"
