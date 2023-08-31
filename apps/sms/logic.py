from django.contrib.sites.models import Site
from django.core.mail import send_mail
from jinja2 import Environment

from .models import EmailTemplate


def send_custom_mail(order, from_send, to_send, template_choice, unique_path, changes=None):
    """Отправка email"""
    print(f"send_custom_mail: {order.id} - {order.car_registration} {template_choice}")
    try:
        change_keys = list(changes.keys()) if changes is not None else []
        print("change_keys: ", change_keys)
        context = {
            "order": {
                "id": str(order.id),
                "name": order.name,
                "phone": order.phone,
                "comment": order.comment,
                "car_registration": order.car_registration,
                "manufacture": order.car.manufacturer if order.car else None,
                "confirm_work": order.confirm_work,
                "partner": order.partner.username if order.partner else None,
                "car_model": order.car.car_model if order.car else None,
                "car_year": order.car_year,
                "distance": order.distance,
                "service": order.service.title if order.service else None,
                "price": order.price,
                "prepayment": order.prepayment,
                "post_code": order.post_code,
                "link": f"http://{Site.objects.first().domain}/link/{order.unique_path_field}/",
                },
            "changes": change_keys,
            }
        current_site = Site.objects.first()
        email_template = EmailTemplate.objects.get(subject=f'{template_choice}')
        jinja_env = Environment()
        template = jinja_env.from_string(email_template.html_content)
        print("Rendering template with context:", context)
        rendered_template = template.render(context)

        # отправка email
        send_mail(
            email_template.subject,
            'Here is the message.',  # Это поле text_content
            f'{from_send}',
            [f'{to_send}'],
            html_message=rendered_template,
            )
    except Exception as e:
        print(f"Error occurred: {e}")
        # TODO: сделать отправку сообщения в СМС админу
