from datetime import datetime

from django import forms

from .models import Order


class OrderForm(forms.ModelForm):
    """Order форма для создания и редактирования заказа"""
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}))

    class Meta:
        model = Order
        fields = [
            'unique_path_field', 'date', 'time', 'price', 'prepayment', 'comment', 'responsible',
            'confirm_work', 'name', 'car_registration', 'car_year', 'car', 'service', 'phone',
            'address', 'post_code', 'distance', 'partner'
        ]
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 3}),
            # ... Добавьте другие виджеты по мере необходимости
        }

    def __init__(self, *args, **kwargs):
        super(OrderForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.date_at:
            self.fields['date'].initial = self.instance.date_at.date()
            self.fields['time'].initial = self.instance.date_at.time()

    def save(self, commit=True):
        instance = super(OrderForm, self).save(commit=False)
        date = self.cleaned_data.get('date')
        time = self.cleaned_data.get('time')
        if date and time:
            instance.date_at = datetime.combine(date, time)
        if commit:
            instance.save()
        return instance


from django import forms
from .models import Order


class ClientOrderForm(forms.ModelForm):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}))

    class Meta:
        model = Order
        fields = ['date', 'time', 'address']

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        time = cleaned_data.get('time')

        if date and time:
            # Объедините дату и время в одно значение datetime
            cleaned_data['date_at'] = datetime.combine(date, time)
        return cleaned_data
