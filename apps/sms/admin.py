from django.contrib import admin
from django.core.exceptions import ValidationError
from jinja2 import Environment
from jinja2 import TemplateSyntaxError
from solo.admin import SingletonModelAdmin

from .models import CONTEXT
from .models import Config
from .models import EmailTemplate
from .models import SMSSendHistory
from .models import SmsMessage
from .models import SmsTemplate


@admin.register(SmsMessage)
class SmsMessageAdmin(admin.ModelAdmin):
    list_display = ("__str__", "template", "to_phone", "is_success", "created_at")
    list_filter = ("template", "is_success", "created_at")
    search_fields = ("template", "to_phone", "message")
    readonly_fields = ("created_at",)


@admin.register(SmsTemplate)
class SmsTemplateAdmin(admin.ModelAdmin):
    list_display = ("__str__", "template")
    readonly_fields = ("_context",)

    def _context(self, obj=None):
        if not obj or not obj.template:
            return '-'
        return "\n".join(
            [
                "{{{{ {} }}}} - {}".format(*item)
                for item in CONTEXT[obj.template].items()
                ]
            )


admin.site.register(Config, SingletonModelAdmin)


def validate_jinja2_syntax(modeladmin, request, queryset):
    jinja_env = Environment()
    for obj in queryset:
        try:
            jinja_env.from_string(obj.html_content)
        except TemplateSyntaxError as e:
            raise ValidationError(f"Ошибка синтаксиса Jinja2 в шаблоне {obj.name}: {e}")


validate_jinja2_syntax.short_description = "Проверить синтаксис Jinja2"


class EmailTemplateAdmin(admin.ModelAdmin):
    actions = [validate_jinja2_syntax]


class SMSSendHistoryAdmin(admin.ModelAdmin):
    list_display = ("phone_number", "success", "sent_datetime")
    list_filter = ("phone_number", "success", "sent_datetime")
    search_fields = ("phone_number",)


admin.site.register(SMSSendHistory, SMSSendHistoryAdmin)

admin.site.register(EmailTemplate, EmailTemplateAdmin)
