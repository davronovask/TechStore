from django.shortcuts import render, redirect
from django.views.generic import View
from django.shortcuts import get_object_or_404
from store.models import CartItem
from .models import Order, OrderItem
from decimal import Decimal
import uuid
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponse
from django.conf import settings
from .services import generate_freedom_pay_sig
# 1. View для инициации оплаты (когда нажали кнопку "Оплатить" на странице чека)
# Исправленный InitPaymentView
class InitPaymentView(View):
    def get(self, request, order_number):
        order = get_object_or_404(Order, order_number=order_number)

        merchant_id = settings.FREEDOM_PAY_MERCHANT_ID
        secret_key = settings.FREEDOM_PAY_SECRET_KEY

        params = {
            'pg_merchant_id': merchant_id,
            'pg_amount': str(order.total_amount),
            'pg_order_id': order.order_number,
            'pg_description': f"Order_{order.order_number}",  # Лучше латиницей без пробелов
            'pg_salt': uuid.uuid4().hex,
            'pg_result_url': 'https://mdsmart.kg/orders/payment-result',
            'pg_success_url': 'https://mdsmart.kg/users/profile/',
            # ОБЯЗАТЕЛЬНО: указываем кодировку, чтобы подпись не "летала"
            'pg_encoding': 'UTF-8',
        }

        # Генерируем подпись
        params['pg_sig'] = generate_freedom_pay_sig('init_payment.php', params, secret_key)

        # Собираем URL
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])

        # ВАЖНО: Меняем домен на .kg, как просил менеджер
        payment_url = f"https://api.freedompay.kg/init_payment.php?{query_string}"

        return redirect(payment_url)


# 2. Webhook (сюда FreedomPay будет стучаться сам)
@method_decorator(csrf_exempt, name='dispatch')
class PaymentResultView(View):
    def post(self, request):
        data = request.POST.dict()
        pg_sig = data.pop('pg_sig', None)

        # Согласно правилу менеджера: берем последнее слово из URL нашего обработчика
        # В urls.py это 'payment-result/'
        script_name = 'payment-result'

        # Генерируем подпись для сравнения
        expected_sig = generate_freedom_pay_sig(script_name, data, settings.FREEDOM_PAY_SECRET_KEY)

        if pg_sig != expected_sig:
            print(f"Ошибка подписи! Ожидали {expected_sig}, получили {pg_sig}")
            return HttpResponse("Invalid signature", status=400)

        # Если все Ок — меняем статус
        order_number = data.get('pg_order_id')
        if data.get('pg_result') == '1':
            order = get_object_or_404(Order, order_number=order_number)
            order.status = 'paid'
            order.save()
            return HttpResponse("OK") # Обязательный ответ для FreedomPay

        return HttpResponse("OK") # Все равно отвечаем OK, чтобы они не слали повторы при отказе  # Отвечаем 200, чтобы не слали повторно

class CreateOrderView(View):
    def post(self, request):
        if not(request.user.is_authenticated):
            return redirect('register')

        user = request.user
        user_cart_items = user.cart_items.all()

        order = Order.objects.create(
            user=user,
            customer_first_name=user.first_name,
            customer_last_name=user.last_name,
            customer_phone=user.phone_number,
            delivery_address=user.address,
        )

        total = Decimal('0.00')

        for cart_item in user_cart_items:  # Переименовал, это не product, а cart_item!
            product_sku = cart_item.product.sku
            product_name = cart_item.product.name
            product_color_name = cart_item.color.name if cart_item.color else ""
            product_memory_size = cart_item.memory.size if cart_item.memory else ""
            if cart_item.memory:
                product_price = cart_item.memory.price
            else:
                product_price = cart_item.product.price

            discount = cart_item.product.active_discount()

            if discount:
                product_price = product_price * (Decimal('100') - Decimal(discount.percent)) / Decimal('100')

            product_quantity = cart_item.quantity

            # Создаем позицию заказа
            OrderItem.objects.create(
                order=order,
                product_sku=product_sku,
                product_name=product_name,
                color_name=product_color_name,
                memory_size=product_memory_size,
                price=product_price,
                quantity=product_quantity,
                total_price=product_price * product_quantity
            )

            total += product_price * product_quantity

        # Обновляем общую сумму заказа
        order.total_amount = total
        order.save()

        return redirect('order_check', order_number=order.order_number)


class OrderCheckView(View):
    def get(self, request, order_number):
        # Получаем заказ по номеру или 404
        order = get_object_or_404(Order, order_number=order_number)

        # Получаем все позиции заказа
        order_items = order.items.all()

        context = {
            'order': order,
            'order_items': order_items,
            'order_number': order.order_number,
            'customer_first_name': order.customer_first_name,
            'customer_last_name': order.customer_last_name,
            'customer_phone': order.customer_phone,
            'delivery_address': order.delivery_address,
            'total_price': order.total_amount,
            'created_at': order.created_at,
        }

        return render(request, 'order_check.html', context)
