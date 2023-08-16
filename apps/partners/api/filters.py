from django_filters import rest_framework as filters

from django_filters.filters import OrderingFilter
from apps.booking.models import Order
from apps.request.models import Request


class OrdersWeekFilter(filters.FilterSet):
    # paid = filters.CharFilter(field_name='transactions__status', lookup_expr='exact')
    paid = filters.CharFilter(method='paid_filter')

    order_by_field = 'ordering'
    ordering = OrderingFilter(
        fields=('id', 'created_at', 'date_at', 'price', 'prepayment',)
    )
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        DATE_FORMAT = ['%d/%m/%Y %I:%M %p', '%d/%m/%Y']
        self.form.fields['created_at__gte'].input_formats = DATE_FORMAT
        self.form.fields['created_at__lte'].input_formats = DATE_FORMAT
        self.form.fields['date_at__gte'].input_formats = DATE_FORMAT
        self.form.fields['date_at__lte'].input_formats = DATE_FORMAT

    class Meta:
        model = Order
        fields = {
            'created_at': ['gte', 'lte'],
            'date_at': ['gte', 'lte'],
        }


    def paid_filter(self, queryset, name, value):
        if (value == 'paid'):
            return queryset.filter(status_paid=True)
        
        if (value == 'no_paid'):
            return queryset.filter(status_paid=False)


class StatisticRequestFilter(filters.FilterSet):
    manufacturer = filters.CharFilter(field_name='car__manufacturer', lookup_expr='iexact')
    model = filters.CharFilter(field_name='car__car_model', lookup_expr='iexact')
 

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        DATE_FORMAT = ['%d/%m/%Y %I:%M %p', '%d/%m/%Y']
        self.form.fields['created_at__gte'].input_formats = DATE_FORMAT
        self.form.fields['created_at__lte'].input_formats = DATE_FORMAT
        
   
    ordering = OrderingFilter(
        fields={
            'car__manufacturer': 'manufacturer',
            'car__car_model': 'model',
            'car_year': 'year',
        },
    )

    class Meta:
        model = Request
        fields = {
            'created_at': ['gte', 'lte'],
            'service': ['exact'],
            'car_year': ['gte', 'lte'],
        }
