from django.views.generic import TemplateView
from composable_views.mixins.url_build import UrlBuilderMixin


class PageTemplate(UrlBuilderMixin, TemplateView):
    """
    Retreives current path from the root, and renders an apropriate
    template.

    If path is ends with `.html` - this means that a markup developer is
    trying to view his template file.

    Designed to be the last in an urlpatterns list.
    """

    url_name = 'page'
    url_regex_list = [
        r'(?P<template>[\w/.]{0,256})'
    ]
    url_format = '^{regex}.html$'

    def get_template_names(self):
        """
        Return a template, which name we've got from url.
        """
        return [
            f'{self.kwargs.get("template", None)}.jinja'
        ]
