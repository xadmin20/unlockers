from django import forms

from apps.booking.models import Order


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'unique_path_field', 'date_at', 'price', 'prepayment', 'comment', 'responsible',
            'confirm_work', 'name', 'car_registration', 'car_year', 'car', 'service', 'phone',
            'address', 'post_code', 'distance', 'partner'
        ]

        # Если вы хотите добавить какие-либо пользовательские виджеты или атрибуты к полям формы, вы можете сделать это здесь:
        widgets = {
            'date_at': forms.DateInput(attrs={'type': 'date'}),
            'comment': forms.Textarea(attrs={'rows': 3}),
            # ... Добавьте другие виджеты по мере необходимости
        }
