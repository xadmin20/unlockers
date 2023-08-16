# Create your tests here.
from datetime import datetime
from decimal import Decimal

from django.contrib.auth.models import User, Group
from django.test import TestCase
from django.urls import reverse

from .models import Order, Employee
from ..cars.models import Car
from ..request.models import ServiceVariation


class OrderDetailViewTest(TestCase):
    """Тестирование представления OrderDetailView"""

    @classmethod
    def setUpTestData(cls):
        # Создайте пользователя и добавьте его в группу 'Worker'
        user = User.objects.create_user(username='testuser', password='12345')
        group = Group.objects.create(name='Worker')
        user.groups.add(group)

        # Создадим необходимые зависимые объекты
        employee = Employee.objects.create(name="Test Employee")
        car = Car.objects.create(car_model="Test Car", manufacturer="Test Brand")
        service_variation = ServiceVariation.objects.create(
            title="Test Service",
            variation="test_variation",  # Убедитесь, что это допустимое значение из SERVICE_VARIATIONS
            price=100.0,
            ordering=1,
            is_display=True,
        )

        # Создаем объект Order со всеми полями
        order_date = datetime.now()
        from django.utils.translation import gettext_lazy as _
        from model_utils import Choices
        ORDER_STATUS_WORK = Choices(
            ("new", _("New")),
            ("confirm", _("Confirm")),
            ("refused", _("Refused")),
        )
        Order.objects.create(
            unique_path_field='testpath',
            date_at=order_date,
            price=Decimal('100.00'),
            prepayment=Decimal('50.00'),
            comment='Test Comment',
            responsible=employee,
            confirm_work=ORDER_STATUS_WORK.new,
            name='Test Name',
            car_registration='XYZ 123',
            car_year=2020,
            car=car,
            service=service_variation,
            phone='1234567890',
            address='123 Test St, Test City',
            post_code='12345',
            distance=10.0,
            created_at=order_date,
            partner=user
        )

    def test_view_url_accessible_by_name(self):
        # Аутентификация пользователя
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('unique_path', args=['testpath']))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        """Проверяем, что используется правильный шаблон"""
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('unique_path', args=['testpath']))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'order.html')

    # Дополнительные тесты, такие как проверка контекста, обработка POST-запроса и т. д.
    # могут быть добавлены здесь
    def test_context_data(self):
        """Проверяем, что контекст содержит правильные данные"""
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('unique_path', args=['testpath']))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('is_executive' in response.context)
        self.assertTrue('object' in response.context)
        self.assertTrue(response.context['is_executive'])
        self.assertTrue(isinstance(response.context['object'], Order))

    def test_post(self):
        """Проверяем, что POST-запрос работает правильно"""
        self.client.login(username='testuser', password='12345')
        response = self.client.post(reverse('unique_path', args=['testpath']))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('form' in response.context)
        self.assertFalse(response.context['form'].is_valid())
        self.assertTemplateUsed(response, 'order.html')
        self.assertTrue('is_executive' in response.context)
        self.assertTrue('object' in response.context)
        self.assertTrue(response.context['is_executive'])
        self.assertTrue(isinstance(response.context['object'], Order))
