import datetime

from django.test import TestCase

from apps.booking.models import Order
from apps.sms.models import SmsMessage


class TestSms(TestCase):
    def setUp(self):
        self.order = Order.objects.create(
            date_at=datetime.datetime.now(),
            price=1000,
            prepayment=500,
            comment="test",
            name="test",
            car_registration="test",
        )

    def test_send_sms(self):
        """Test send sms"""
        self.order.send_message()
        self.assertEqual(SmsMessage.objects.count(), 1)
        self.assertEqual(SmsMessage.objects.first().status, SmsMessage.STATUS_SENT)
        self.assertEqual(SmsMessage.objects.first().template, SmsMessage.TEMPLATES["request"])
        self.assertEqual(SmsMessage.objects.first().order, self.order)

    def test_send_sms_payed(self):
        """Test send sms payed"""
        self.order.send_sms_payed()
        self.assertEqual(SmsMessage.objects.count(), 1)
        self.assertEqual(SmsMessage.objects.first().status, SmsMessage.STATUS_SENT)
        self.assertEqual(SmsMessage.objects.first().template, SmsMessage.TEMPLATES["order_payed"])
        self.assertEqual(SmsMessage.objects.first().order, self.order)


