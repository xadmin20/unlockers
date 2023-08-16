from django.views.generic import ListView, DetailView

from seo.mixins.views import ModelInstanceViewSeoMixin, ViewSeoMixin

from .models import Post


def pagination(total: int, current: int):
    to_min, to_max = current, total - current
    center_start, center_end = 1, total
    is_pre, is_post = False, False
    if to_min > 4:
        center_start = _center_start if (_center_start := current-1) > 0 else current
        is_pre = True
    if to_max > 3:
        center_end = _center_end if (_center_end := current+1) < total else total
        is_post = True
    return {
        "pre": [1, 2] if is_pre else None,
        "center": [i for i in range(center_start, center_end+1)],
        "post": [total-1, total] if is_post else None,
    }


class BlogView(ViewSeoMixin, ListView):
    template_name = "blog.jinja"
    queryset = Post.objects.all()
    paginate_by = 6
    seo_view = "blog"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        paginator = context.get("paginator")
        page_obj = context.get("page_obj")
        context["pagination_group"] = pagination(paginator.num_pages, page_obj.number)
        return context


class PostDetailView(ModelInstanceViewSeoMixin, DetailView):
    template_name = "post.jinja"
    queryset = Post.objects.all()

    def get_context_data(self, **kwargs):
        kwargs["same"] = Post.objects.all().order_by("?")[:2]
        return super().get_context_data(**kwargs)
