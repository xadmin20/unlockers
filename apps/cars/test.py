from django.test import TestCase
from apps.cars.contrib import get_car


class CarTestCase(TestCase):

    def test_get_car(self):
        print(get_car("WV57TXH"))
