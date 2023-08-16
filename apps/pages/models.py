from django.db import models
from django.utils.timezone import datetime
from django.utils.translation import gettext_lazy as _
from django.core.validators import MaxValueValidator
from django.urls import reverse_lazy
from django.utils import timezone

from ckeditor.fields import RichTextField
from solo.models import SingletonModel


class Typical(models.Model):
    title = models.CharField(
        verbose_name=_("Title"),
        max_length=255,
    )
    image = models.ImageField(
        verbose_name=_("Banner image"),
        null=True,
        blank=True
    )
    content = RichTextField(
        verbose_name=_("Content")
    )
    slug = models.CharField(
        verbose_name=_("Slug"),
        max_length=255,
    )
    updated_at = models.DateTimeField(
        _("Updated at"), default=timezone.now
    )

    class Meta:
        verbose_name = _("Typical")
        verbose_name_plural = _("Typical")

    def __str__(self):
        return self.title

    def save(self, **kwargs):
        self.updated_at = timezone.now()
        super().save(**kwargs)

    def get_absolute_url(self):
        return reverse_lazy("typical", args=[self.slug])



class MainPage(SingletonModel):
    image = models.ImageField(
        verbose_name=_("Banner image")
    )
    text = RichTextField(
        verbose_name=_("Text"),
    )
    bottom_image = models.ImageField(
        verbose_name=_("Bottom image"),
        null=True
    )
    rating = models.PositiveIntegerField(
        verbose_name=_("Review rating"),
        default=0
    )
    reviews_amount = models.PositiveIntegerField(
        verbose_name=_("Reviews amount"),
        default=0
    )
    reviews_link = models.CharField(
        verbose_name=_("Review link"),
        max_length=255,
        default="/"
    )

    class Meta:
        verbose_name = _("Main page")
        verbose_name_plural = _("Main page")


class MainPageItems(models.Model):
    image = models.ImageField(
        verbose_name=_("Image")
    )
    title = models.CharField(
        verbose_name=_("Title"),
        max_length=255
    )
    order = models.PositiveIntegerField(
        verbose_name=_("Order"),
        default=0
    )
    page = models.ForeignKey(
        MainPage,
        on_delete=models.CASCADE,
        related_name="items",
    )

    class Meta:
        ordering = ("order", )

    def __str__(self):
        return self.title


class Review(models.Model):
    title = models.CharField(
        verbose_name=_("Title"),
        max_length=255
    )
    review = RichTextField(
        verbose_name=_("Review")
    )
    stars = models.PositiveIntegerField(
        verbose_name=_("Stars amount"),
        default=5,
        validators=[MaxValueValidator(5)]
    )
    order = models.PositiveIntegerField(
        verbose_name=_("Ordering"),
        default=0
    )
    author = models.CharField(
        verbose_name=_("Author"),
        max_length=255,
        default="",
    )
    date = models.DateTimeField(
        verbose_name=_("Date"),
        auto_now_add=True,
    )

    class Meta:
        verbose_name = _("Review")
        verbose_name_plural = _("Reviews")
        ordering = ("-date", )

    def __str__(self):
        return self.title

    @property
    def published_at(self):
        return self.date.strftime("%d %B %Y")
