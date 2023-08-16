from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from apps.pages.models import Typical, Review
from apps.request.models import ServiceVariation

from datetime import datetime 


__all__ = (
    'sitemaps',
)
 
class BaseSitemap(Sitemap):
    i18n = True
    protocol = "https"


class IndexSitemap(BaseSitemap):
    changefreq = 'always'
    priority = 1

    def items(self):
        return ['index']

    def location(self, item):
        return reverse(item)

    def lastmod(self, obj):
        date_smap = ServiceVariation.objects.all().order_by("-updated_at").first().updated_at
        rw_obj = Review.objects.all().order_by("-date").first()

        if rw_obj and date_smap < rw_obj.date:
            date_smap = rw_obj.date

        if not date_smap:
            date_smap = datetime.now()
        return date_smap


class PageTypicalSitemap(BaseSitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return Typical.objects.all()

    def lastmod(self, obj):
        return obj.updated_at



sitemaps = {
    'index': IndexSitemap,
    'pages': PageTypicalSitemap,
}
