from django.urls import path
from .views import (
    LoginApi, LogoutApi,
    PasswordResetViewApi,
    PasswordResetConfirmViewApi,
    PasswordChangeViewApi,
    ProfileInfoViewApi,
    ProfileUpdateViewApi,
    SendTestEmailViewApi,
    EmailChangeViewApi,
    OrdersWeekViewApi,
    InfoWeekViewApi,
    SendSMSViewApi,
    OrdersHistoryViewApi,
    OrderDetailViewApi,
    BalanceHistoryViewApi,
    WithdrawHistoryViewApi,
    WithdrawCreateViewApi,
    GetBalanceApi,
    GetListWithdrawStatusApi,
    CreateOrderViewApi,
    GetListOrderStatusApi,
    CreateRequestViewApi,
    StatisticNotFitPriceViewApi,
    GetEmployeeApi,
    GetCarManufacturerApi,
    GetCarModelApi,
)


urlpatterns = [
    path('login/',  LoginApi.as_view(), name='login_api'),
    path('logout/', LogoutApi.as_view(), name='logout_api'),
    path('password/reset/',  PasswordResetViewApi.as_view(), name='password_reset_api'),
    path('password/reset/confirm/', PasswordResetConfirmViewApi.as_view(), name='password_reset_confirm_api'),
    path('password-change/', PasswordChangeViewApi.as_view(), name='password_change_api'),
    path('profile-info/', ProfileInfoViewApi.as_view(), name='profile_info_api'),
    path('profile-update/', ProfileUpdateViewApi.as_view(), name='profile_update_api'),
    path('send-test-email/', SendTestEmailViewApi.as_view(), name='send_test_email_api'),
    path('change-email/', EmailChangeViewApi.as_view(), name='change_email_api'),
    path('orders-week/', OrdersWeekViewApi.as_view(), name='orders_week'),
    path('orders-history/', OrdersHistoryViewApi.as_view(), name='orders_history'),
    path('info-week/', InfoWeekViewApi.as_view(), name='info_week'),
    path('send-sms/', SendSMSViewApi.as_view(), name='send_sms'),
    path('order-create/', CreateOrderViewApi.as_view(), name='order_create'),
    path('order-detail/<pk>/', OrderDetailViewApi.as_view(), name='order_detail'),
    path('balance-history/', BalanceHistoryViewApi.as_view(), name='balance_history'),
    path('withdraw-history/', WithdrawHistoryViewApi.as_view(), name='withdraw_history'),
    path('withdraw-create/', WithdrawCreateViewApi.as_view(), name='withdraw_create'),
    path('get-balance/', GetBalanceApi.as_view(), name='get_balance'),
    path('get-withdraw-status-list/', GetListWithdrawStatusApi.as_view(), name='get_withdraw_status_list'),
    path('get-order-status-list/', GetListOrderStatusApi.as_view(), name='get_order_status_list'),
    path('create-request/', CreateRequestViewApi.as_view(), name='create_request'),
    path('statistic-not-fit-price/', StatisticNotFitPriceViewApi.as_view(), name='statistic_not_fit_price'),
    path('get-employee/', GetEmployeeApi.as_view(), name='get_employee'),
    path('get-car-manufacturer/', GetCarManufacturerApi.as_view(), name='get_car-manufacturer'),
    path('get-car-model/<manufacturer>/', GetCarModelApi.as_view(), name='get_car-model'),
]