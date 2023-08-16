from django.urls import include, re_path

from . import views

urlpatterns = [
    re_path('^', include(([
        *views.PageTemplate.as_urls(),
    ], 'markup')))
]
