from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.db import models
from django.utils.text import slugify
from django.utils.crypto import get_random_string

from ckeditor.fields import RichTextField


class SlugifyMixin(models.Model):
    SLUGIFY_FIELD: str
    slug = models.CharField(
        verbose_name="Slug",
        max_length=255,
        null=True,
        blank=True
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.slug or not self.is_unique_slug(self.slug):
            self.slug = self.generate_slug()
        return super().save(*args, **kwargs)

    def is_unique_slug(self, slug):
        qs = self.__class__.objects.filter(slug=slug)
        if self.id:
            qs = qs.exclude(id=self.id)
        return not qs.exists()

    def generate_slug(self):
        slug = slugify(self.to_slugify)
        while True:
            if self.is_unique_slug(slug):
                break
            slug = f"{slug}-{get_random_string(2)}"

        return slug

    @property
    def to_slugify(self):
        return getattr(self, self.SLUGIFY_FIELD)


class Post(SlugifyMixin):
    SLUGIFY_FIELD = "title"
    preview = models.ImageField(
        verbose_name=_("Preview"),
    )
    video = models.CharField(
        verbose_name=_("Video link"),
        max_length=255,
        null=True,
        blank=True,
    )
    title = models.CharField(
        verbose_name=_("Title"),
        max_length=255
    )
    short_description = RichTextField(
        verbose_name=_("Short description")
    )
    content = RichTextField(
        verbose_name=_("Content"),
    )
    created_at = models.DateTimeField(
        verbose_name=_("Created at"),
        auto_now_add=True,
        editable=True
    )

    class Meta:
        verbose_name = _("Post")
        verbose_name_plural = _("Posts")
        ordering = ("-created_at", )

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("blog_detail", kwargs={"slug": self.slug})
