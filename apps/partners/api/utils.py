import base64
import mimetypes
import re
import six
import uuid
 
from django.core.files.base import ContentFile
from django.utils.functional import LazyObject
 
 
class Base64ImageConverter:
 
    @staticmethod
    def decode_file(data):
        if isinstance(data, six.string_types):
            _data = re.sub(r"^data\:.+base64\,(.+)$", r"\1", data)
            try:
                return base64.b64decode(_data)
            except Exception as exception:
                pass
        return
 
    def convert(self, data):
        file_name, delim, content = str(data).partition(';')
        print(f'file_name={delim}')
        decoded_data = self.decode_file(content)
        if not decoded_data:
            return
        return ContentFile(decoded_data, name=file_name)
 
 
class DefaultBase64ImageConverter(LazyObject):
    def _setup(self):
        self._wrapped = Base64ImageConverter()
 
 
default_base64_file_converter = DefaultBase64ImageConverter()