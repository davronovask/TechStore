from django.urls import path
from .views import OrderCheckView, CreateOrderView, InitPaymentView, PaymentResultView

urlpatterns = [
    path('order-check/<str:order_number>/', OrderCheckView.as_view(), name='order_check'),
    path('create-order/', CreateOrderView.as_view(), name='create_order'),
    path('pay/<str:order_number>/', InitPaymentView.as_view(), name='init_payment'),
    path('payment-result', PaymentResultView.as_view(), name='payment_result'),
]