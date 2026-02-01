from django.utils import timezone
from decimal import Decimal
from django.db import models
from colorfield.fields import ColorField
import uuid
from django.core.validators import MinValueValidator, MaxValueValidator
from solo.models import SingletonModel

from TechStore import settings


def layout_data(request):
    contacts = Contacts.objects.first()
    social = None
    if contacts:
        social = contacts.social_links.first()

    return {
        'menu_categories': ProductCategory.objects.all(),
        'contacts': contacts,
        'social_links': social,
    }

class Banner(models.Model):
    """Баннеры для главной страницы"""
    title = models.CharField(max_length=100, verbose_name="Заголовок (необязательно)", blank=True)
    image = models.ImageField(
        upload_to='banners/',
        verbose_name="Изображение",
        help_text="Рекомендуемый размер: 1920x600"
    )
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок сортировки")

    class Meta:
        verbose_name = "Баннер"
        verbose_name_plural = "Баннеры"
        ordering = ['order']

    def __str__(self):
        return self.title or f"Баннер {self.id}"


class ProductCategory(models.Model):
    """ Категории товаров. """

    image = models.ImageField(
        upload_to='categories/',
        blank=True,
        verbose_name="Изображение категории",
        help_text="Отображается в каталоге и на главной странице"
    )

    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="Название категории",
        help_text="Например: Телефоны, Ноутбуки"
    )

    slug = models.SlugField(
        max_length=200,
        unique=True,
        db_index=True,
        verbose_name="URL-адрес (slug)",
        help_text="Используется в ссылке. Например: phones, laptops"
    )

    class Meta:
        verbose_name = "Категория товара"
        verbose_name_plural = "Категории товаров"
        ordering = ['name']

    def __str__(self):
        return self.name


class Brand(models.Model):
    """ Бренды товаров. """

    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="Название бренда",
        help_text="Например: Apple, Samsung, Xiaomi"
    )

    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name="URL-адрес (slug)",
        help_text="Используется в ссылке. Например: apple, samsung"
    )

    categories = models.ManyToManyField(
        ProductCategory,
        related_name='brands',
        verbose_name="Категории",
        help_text="Выберите категории, к которым относится бренд"
    )

    class Meta:
        verbose_name = "Бренд"
        verbose_name_plural = "Бренды"
        ordering = ['name']

    def __str__(self):
        return self.name


class ProductAttribute(models.Model):
    """Атрибуты товара, например цвет, память, размер."""
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name='attributes',
        verbose_name="Товар"
    )
    name = models.CharField(max_length=255, verbose_name="Название характеристики")
    value = models.CharField(max_length=255, verbose_name="Значение характеристики")

    class Meta:
        verbose_name = "Атрибут товара"
        verbose_name_plural = "Атрибуты товаров"

    def __str__(self):
        return f"{self.name}: {self.value}"

def generate_sku():
    """Генерация уникального артикула на основе UUID."""
    return uuid.uuid4().hex[:12].upper()  # берём первые 12 символов hex и делаем их заглавными


class Product(models.Model):
    """Основная информация о товаре."""
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Категория"
    )
    name = models.CharField(max_length=255, unique=True, verbose_name="Наименование")
    slug = models.SlugField(max_length=200, db_index=True, unique=True, verbose_name="Ссылка (slug)")
    description = models.TextField(blank=True, verbose_name="Описание")
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Цена'
    )
    stock_status = models.CharField(
        max_length=50,
        choices=[
            ('in_stock', 'В наличии'),
            ('out_of_stock', 'Нет в наличии'),
            ('preorder', 'Под заказ')
        ],
        default='in_stock',
        verbose_name="Статус наличия"
    )
    brands = models.ManyToManyField(
        Brand,
        blank=True,
        verbose_name="Бренды"
    )
    is_active = models.BooleanField(default=True, verbose_name='Наличие')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    sku = models.CharField(
        max_length=12,
        unique=True,
        editable=False,
        default=generate_sku,
        verbose_name='Артикул'
    )

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.sku})"

    def main_image(self):
        """Главная картинка продукта берётся из первого варианта цвета и первого ракурса."""
        first_variant = self.variants.first()
        if first_variant:
            return first_variant.main_image()
        return None

    def active_discount(self):
        """Возвращает активную скидку на товар или None."""
        now = timezone.now()
        return self.discounts.filter(start_date__lte=now, end_date__gte=now).first()

    def discounted_price(self):
        discount = self.active_discount()
        if discount:
            return self.price * (Decimal('100') - Decimal(discount.percent)) / Decimal('100')
        return self.price

    def price_display(self):
        """
        Старое цена = price, если есть скидка, иначе None
        Новая цена = discounted_price()
        """
        discount = self.active_discount()
        if discount:
            return (self.price, self.discounted_price())
        return (None, self.price)


class ProductDiscount(models.Model):
    """Скидка на товар с указанием процентов и дат действия."""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='discounts',
        verbose_name="Товар"
    )
    percent = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Процент скидки"
    )
    start_date = models.DateTimeField(verbose_name="Дата начала")
    end_date = models.DateTimeField(verbose_name="Дата окончания")

    class Meta:
        verbose_name = "Скидка"
        verbose_name_plural = "Скидки"
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.product.name} - {self.percent}%"


class ProductColorAngle(models.Model):
    """
    Товары с цветом и ракурсами.
    """
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name='variants',
        verbose_name="Товар"
    )
    name = models.CharField(max_length=50, verbose_name="Название цвета")
    color = ColorField(verbose_name="Цвет")

    # Ракурсы (до 6)
    image_1 = models.ImageField(upload_to='products/gallery/', verbose_name="Изображение товара")
    image_2 = models.ImageField(upload_to='products/gallery/', blank=True, null=True, verbose_name="Ракурс 1")
    image_3 = models.ImageField(upload_to='products/gallery/', blank=True, null=True, verbose_name="Ракурс 2")
    image_4 = models.ImageField(upload_to='products/gallery/', blank=True, null=True, verbose_name="Ракурс 3")
    image_5 = models.ImageField(upload_to='products/gallery/', blank=True, null=True, verbose_name="Ракурс 4")
    image_6 = models.ImageField(upload_to='products/gallery/', blank=True, null=True, verbose_name="Ракурс 5")

    is_available = models.BooleanField(
        default=True,
        verbose_name="В наличии",
        help_text="Если цвет есть на складе, оставьте включённым"
    )

    class Meta:
        verbose_name = "Изображение товара и цвет"
        verbose_name_plural = "Изображение товара и цвета"
        constraints = [
            models.UniqueConstraint(fields=['product', 'name'], name='unique_product_color_name')
        ]

    def __str__(self):
        return f"{self.product.name} - {self.name}"

    def main_image(self):
        """Главная картинка берется из первого ракурса, если он есть"""
        return self.image_1 or self.image_2 or self.image_3 or self.image_4 or self.image_5 or self.image_6

    def get_images_list(self):
        """Возвращает список всех непустых изображений для данного цвета"""
        return [img for img in [self.image_1, self.image_2, self.image_3,
                                self.image_4, self.image_5, self.image_6] if img]


class ProductMemoryOption(models.Model):
    """
    Конкретный вариант памяти для конкретного цвета товара.
    """
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name = 'memory_options_all',
        verbose_name="Продукт"
    )
    colors = models.ManyToManyField(
        'ProductColorAngle',
        verbose_name="Доступные цвета",
        related_name='memory_options',
    )
    size = models.CharField(max_length=50, verbose_name="Объем памяти")
    is_available = models.BooleanField(default=True, verbose_name="В наличии")

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Цена для этого объема памяти"
    )

    class Meta:
        verbose_name = "Вариант памяти"
        verbose_name_plural = "Варианты памяти"

    def __str__(self):
        return f"{self.product.name} - {self.size}"


class Contacts(SingletonModel):
    """Контактные данные сайта.Используется в хедере и футере. Хранит адрес, телефон и время работы."""
    city = models.CharField(
        max_length=100,
        verbose_name="Город"
    )
    street = models.CharField(
        max_length=200,
        verbose_name="Улица"
    )

    work_time = models.CharField(
        max_length=100,
        verbose_name="Время работы",
        help_text="Пример: 9:00–22:00 ежедневно"
    )

    def __str__(self):
        return "Контактные данные"

    class Meta:
        verbose_name = "Контактные данные"
        verbose_name_plural = "Контактные данные"


class SocialLink(models.Model):
    """Социальные сети, привязанные к контактам"""
    contacts = models.ForeignKey(
        Contacts,
        on_delete=models.CASCADE,
        related_name='social_links',
        verbose_name="Контакты"
    )
    instagram = models.CharField(max_length=100, verbose_name="Instagram", blank=True, null=True, help_text="Никнейм")
    whatsapp = models.CharField(max_length=100, verbose_name="WhatsApp", blank=True, null=True,help_text="Kод страны без(+) 996 ..." )
    telegram = models.CharField(max_length=100, verbose_name="Telegram", blank=True, null=True, help_text="Никнейм")

    def __str__(self):
        return "Социальные сети"

    class Meta:
        verbose_name = "Социальная сеть"
        verbose_name_plural = "Социальные сети"

class CartItem(models.Model):
    """
    Элемент корзины конкретного пользователя.
    Хранит товар, выбранный цвет и память, количество и цену.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    color = models.ForeignKey(ProductColorAngle, on_delete=models.SET_NULL, null=True, blank=True)
    memory = models.ForeignKey(ProductMemoryOption, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # цена за один товар с учетом варианта памяти

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Элемент корзины"
        verbose_name_plural = "Элементы корзины"
        unique_together = ('user', 'product', 'color', 'memory')  # один товар+вариант памяти+цвет один раз

    def __str__(self):
        return f"{self.user.email} - {self.product.name} x {self.quantity}"

    def total_price(self):
        return self.price * self.quantity


class FavoriteItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorite_items'
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Избранный товар"
        verbose_name_plural = "Избранные товары"
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.email} - {self.product.name}"