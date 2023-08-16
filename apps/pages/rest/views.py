from rest_framework.generics import CreateAPIView

from apps.pages.models import Review
from .serializers import ReviewSerializer


class ReviewCreateAPIView(CreateAPIView):
    serializer_class = ReviewSerializer
    queryset = Review.objects.all()
