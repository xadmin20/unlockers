from datetime import datetime

from _decimal import Decimal
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.booking.models import Order  # Импортируйте вашу модель Order


class OrderStatusUpdateTestCase(APITestCase):

    def setUp(self):
        # Здесь вы можете создать объект Order, который будет использоваться в тестах
        self.partner = User.objects.create_user(
            username='testuser', password='12345',
            is_staff=True, is_superuser=True,
            email="a@b.ru"
            )
        self.order = Order.objects.create(
            unique_path_field='unique_path_',
            status='new',
            date_at=datetime.now(),
            price=Decimal('100.00'),
            prepayment=Decimal('50.00'),
            comment='Test Comment',
            confirm_work='new',
            name='Test Name',
            car_registration='XYZ 123',
            car_year=2020,
            phone='1234567890',
            address='123 Test St, Test City',
            post_code='12345',
            distance=10.0,
            partner=self.partner

            )
        self.url = reverse('update_order_status', kwargs={'unique_path': self.order.unique_path_field})

    def test_update_status_en_route(self):
        response = self.client.get(f"{self.url}?status=en_route")
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'en_route')

    def test_update_status_arrived(self):
        response = self.client.get(f"{self.url}?status=arrived")
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'arrived')

    def test_update_status_completed(self):
        response = self.client.get(f"{self.url}?status=completed")
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'completed')

    def test_update_status_paid(self):
        response = self.client.get(f"{self.url}?status=paid")
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'paid')

    def test_update_status_invalid(self):
        response = self.client.get(f"{self.url}?status=invalid")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
