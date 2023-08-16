"""
URL configuration for unlockers project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from des import urls as des_urls
from .sitemaps import sitemaps
from django.contrib.sitemaps import views as sitemap_views


urlpatterns = [
    path('admin/', admin.site.urls),
    re_path(r'^django-des/', include(des_urls)),
    path('vuejs-translate', include('vuejs_translate.urls')),
    re_path(r'^filer/', include('filer.urls')),
    path('robots.txt', include('robots.urls')),
    re_path(r'^rest-auth/', include('rest_auth.urls')),

    path('sitemap.xml', sitemap_views.index, {'sitemaps': sitemaps}, name='sitemap'),
    path('sitemap-<section>.xml', sitemap_views.sitemap, {'sitemaps': sitemaps},
         name='django.contrib.sitemaps.views.sitemap'),

    path("ckeditor5/", include('django_ckeditor_5.urls'), name="ck_editor_5_upload_file"),
    path(r'', include("apps.pages.urls")),
    path(r'', include("apps.pages.rest.urls")),
    path(r'', include("apps.request.rest.urls")),
    path(r'', include("apps.booking.rest.urls")),
    path(r'', include("apps.booking.urls")),
    path(r'', include("apps.blog.urls")),
    # path(r'api/v1/cabinet/', include('apps.partners.api.urls')),

    path('vuejs-translate', include('vuejs_translate.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += (
    path('api/v1/', include(((
        path('cabinet/', include('apps.partners.api.urls')),
    ), "api"))),
    path('', include("apps.partners.urls")),
)
