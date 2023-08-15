from django.contrib import admin

from .models import Proxy


admin.site.register(
    Proxy, 
    list_display=("__str__", "is_valid", "is_manual", "created_at"), 
    list_filter=("is_valid", "is_manual")
)
