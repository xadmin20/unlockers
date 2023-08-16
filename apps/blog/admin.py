from django.contrib import admin

from seo.admin import ModelInstanceSeoInline
from .models import Post


admin.site.register(Post, inlines=(ModelInstanceSeoInline, ))
