from django.contrib import admin

from solo.admin import SingletonModelAdmin
from seo.admin import ModelInstanceSeoInline

from .models import Typical, MainPage, MainPageItems, Review


class MainPageItemInline(admin.StackedInline):
    model = MainPageItems
    extra = 0


admin.site.register(
    Typical, inlines=(ModelInstanceSeoInline, )
)
admin.site.register(
    MainPage, 
    SingletonModelAdmin, 
    inlines=(MainPageItemInline, ModelInstanceSeoInline)
)
admin.site.register(
    Review, 
    list_display=("__str__", "title", "stars"), 
    list_editable=("title", "stars")
)
