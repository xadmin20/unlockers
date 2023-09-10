from des import urls as des_urls
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps import views as sitemap_views
from django.urls import include
from django.urls import path
from django.urls import re_path

from .sitemaps import sitemaps

urlpatterns = [
                  path('admin/', admin.site.urls),
                  path('payments/', include('apps.payments.urls')),
                  re_path(r'^django-des/', include(des_urls)),
                  path('vuejs-translate', include('vuejs_translate.urls')),
                  re_path(r'^filer/', include('filer.urls')),
                  path('robots.txt', include('robots.urls')),
                  re_path(r'^rest-auth/', include('rest_auth.urls')),

                  path('sitemap.xml', sitemap_views.index, {'sitemaps': sitemaps}, name='sitemap'),
                  path(
                      'sitemap-<section>.xml', sitemap_views.sitemap, {'sitemaps': sitemaps},
                      name='django.contrib.sitemaps.views.sitemap'
                      ),

                  path("ckeditor5/", include('django_ckeditor_5.urls'), name="ck_editor_5_upload_file"),
                  path(r'', include("apps.pages.urls")),
                  path(r'', include("apps.pages.rest.urls")),
                  path(r'', include("apps.request.rest.urls")),
                  path(r'', include("apps.booking.rest.urls")),
                  path(r'', include("apps.booking.urls")),
                  path(r'', include("apps.blog.urls")),
                  path('vuejs-translate', include('vuejs_translate.urls')),
                  ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += (
    path(
        'api/v1/', include(
            ((
                 path('cabinet/', include('apps.partners.api.urls')),
                 ), "api")
            )
        ),
    path('', include("apps.partners.urls")),
    )
