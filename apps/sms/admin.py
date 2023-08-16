from django.contrib import admin
from solo.admin import SingletonModelAdmin
from .models import SmsMessage, SmsTemplate, CONTEXT, Config


@admin.register(SmsMessage)
class SmsMessageAdmin(admin.ModelAdmin):
    list_display = ("__str__", "template", "to_phone", "is_success", "created_at")
    list_filter = ("template", "is_success", "created_at")
    search_fields = ("template", "to_phone", "message")
    readonly_fields = ("created_at", )


@admin.register(SmsTemplate)
class SmsTemplateAdmin(admin.ModelAdmin):
    list_display = ("__str__", "template")
    readonly_fields = ("_context", )

    def _context(self, obj=None):
        if not obj or not obj.template:
            return '-'
        return "\n".join([
            "{{{{ {} }}}} - {}".format(*item)
            for item in CONTEXT[obj.template].items()
        ])


admin.site.register(Config, SingletonModelAdmin)
