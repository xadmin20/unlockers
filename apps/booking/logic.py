import time
from typing import Dict

from apps.booking.senders import _send_sms
from apps.booking.senders import generate_message
from apps.booking.senders import send_notification_to_admin
from apps.sms.models import SmsMessage
from apps.sms.models import TEMPLATES
from apps.sms.models import get_timeout_amount


def send_sms(template: TEMPLATES, context: Dict, phone: str):
    """Send a message to the phone number"""
    try:
        msg = SmsMessage(
            to_phone=phone,
            template=template,
            )

        # Теперь generate_message возвращает список SMS-сообщений
        message_texts = generate_message(context, template)
        all_valid = True

        # Сохранить сообщения в объекте msg
        if len(message_texts) > 0:
            msg.message = message_texts[0]
        if len(message_texts) > 1:
            msg.message2 = message_texts[1]
        if len(message_texts) > 2:
            msg.message3 = message_texts[2]
        print(f"send_sms: {phone} - {message_texts}")
        for message_text in message_texts:
            try:
                print(message_text)
                time.sleep(get_timeout_amount())
                status_code, msg.log = _send_sms(phone, message_text)
            except Exception as e:
                print(e)
                msg.log = msg.log or "" + f"\n{str(e)}"
                status_code = None
            if status_code != 200:
                all_valid = False
                send_notification_to_admin(msg, "sms_error")
                print("SMS ERROR")
            print(status_code)

        msg.is_success = all_valid
        msg.save()
        return msg
    except Exception as e:
        print(e)
        return None
