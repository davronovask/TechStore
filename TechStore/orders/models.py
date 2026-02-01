from django.db import models
from TechStore import settings
from django.db import models
from django.utils import timezone
from decimal import Decimal
import uuid

# Create your models here.
def generate_order_number():
    """Генерация уникального номера заказа."""
    return uuid.uuid4().hex[:10].upper()  # 10 символов, например: A3F5D8B2C1


class Order(models.Model):
    """
    Заказ пользователя.
    Хранит общую информацию о заказе и данные покупателя.
    """
    STATUS_CHOICES = [
        ('pending', 'Ожидает обработки'),
        ('confirmed', 'Подтвержден'),
        ('processing', 'В обработке'),
        ('waiting_payment', 'Ожидает оплаты'),  # Новый статус
        ('paid', 'Оплачен'),
        ('shipped', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменен'),
    ]

    # Связь с пользователем
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name="Пользователь"
    )

    # Уникальный номер заказа
    order_number = models.CharField(
        max_length=10,
        unique=True,
        editable=False,
        default=generate_order_number,
        verbose_name='Номер заказа'
    )
    payment_id = models.CharField(max_length=100, null=True, blank=True, verbose_name="ID платежа FreedomPay")
    # Данные покупателя (сохраняем на момент заказа)
    customer_first_name = models.CharField(null=True, blank=True, max_length=255, verbose_name="Имя покупателя")
    customer_last_name = models.CharField(null=True, blank=True, max_length=255, verbose_name="Фамилия покупателя")
    customer_phone = models.CharField(null=True, blank=True, max_length=20, verbose_name="Телефон")
    customer_email = models.EmailField(blank=True, verbose_name="Email")

    # Адрес доставки
    delivery_address = models.TextField(null=True, blank=True, verbose_name="Адрес доставки")

    # Информация о заказе
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Статус заказа"
    )

    # Финансовая информация
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Общая сумма заказа"
    )

    # Комментарий к заказу
    comment = models.TextField(blank=True, verbose_name="Комментарий к заказу")

    # Временные метки
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ['-created_at']

    def __str__(self):
        return f"Заказ #{self.order_number} от {self.created_at.strftime('%d.%m.%Y')}"

    def get_items_count(self):
        """Количество позиций в заказе"""
        return self.items.count()

    def get_total_quantity(self):
        """Общее количество товаров"""
        return sum(item.quantity for item in self.items.all())


class OrderItem(models.Model):
    """
    Позиция заказа - конкретный товар в заказе.
    Минимальный набор данных для обработки заказа администратором.
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Заказ"
    )

    # Основная информация о товаре
    product_sku = models.CharField(max_length=12, verbose_name="Артикул товара")
    product_name = models.CharField(max_length=255, verbose_name="Название товара")

    # Характеристики выбранного варианта
    color_name = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Цвет"
    )
    memory_size = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Память"
    )

    # Ценовая информация
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Цена за единицу"
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")

    # Итоговая стоимость позиции
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Итого"
    )

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"

    def save(self, *args, **kwargs):
        """Автоматически рассчитываем итоговую стоимость"""
        self.total_price = self.price * self.quantity
        super().save(*args, **kwargs)