from django.utils.translation import gettext_lazy as _
 
from rest_framework.serializers import FileField, ImageField
 
from apps.partners.api.utils import default_base64_file_converter
 
 
class Base64FileFieldMixin:
    message = None
 
    def __init__(self, message=None, **kwargs):
        super().__init__(**kwargs)
        if message:
            self.message = message
 
    def to_internal_value(self, data):
        try:
            data = default_base64_file_converter.convert(data)
        except Exception as ex:
            self.fail(self.message)

        return super().to_internal_value(data)
 
 
class Base64FileSerializerField(Base64FileFieldMixin, FileField):
    message = _("Invalid file was passed")
 
 
class Base64ImageSerializerField(Base64FileFieldMixin, ImageField):
    message = _("Invalid image was passed")