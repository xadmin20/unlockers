from django.contrib import admin
from solo.admin import SingletonModelAdmin

from .models import CONTEXT
from .models import Config
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


# @admin.register(EmailTemplate)
# class EmailTemplateAdmin(admin.ModelAdmin):
#     list_display = ('name', 'subject', 'preview_html_content')
#     search_fields = ('name', 'subject')
#     readonly_fields = ('preview_html_content',)
#
#     def preview_html_content(self, obj):
#         return obj.html_content[:50] + '...' if len(obj.html_content) > 50 else obj.html_content
#
#     preview_html_content.short_description = "HTML Content Preview"
#
#     fieldsets = (
#         ('Basic Information', {
#             'fields': ('name', 'subject')
#             }),
#         ('Content', {
#             'fields': ('html_content', 'preview_html_content')
#             })
#         )


admin.site.register(Config, SingletonModelAdmin)

from django.contrib import admin
from django.core.exceptions import ValidationError
from jinja2 import Environment, TemplateSyntaxError
from .models import EmailTemplate


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


admin.site.register(EmailTemplate, EmailTemplateAdmin)
