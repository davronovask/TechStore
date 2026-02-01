from django.shortcuts import get_object_or_404, render
from django.views.generic import TemplateView, ListView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import redirect
from decimal import Decimal

from .models import (
    Product,
    ProductCategory,
    Contacts,
    SocialLink,
    Banner,
    Brand,
    ProductColorAngle,
    ProductMemoryOption,
    CartItem, FavoriteItem
)



class HomePageView(TemplateView):
    """Главная страница сайта."""
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Получаем максимум 3 активных баннера
        context['banners'] = Banner.objects.filter(is_active=True)[:3]

        # Все категории для главной
        context['categories'] = ProductCategory.objects.all()[:12]

        # Все бренды (например для фильтрации)
        context['brands'] = Brand.objects.all()

        # Активные товары (новинки / популярные)
        context['products'] = Product.objects.filter(is_active=True)[:12]

        # Товары со скидками (по датам действия акции)
        context['discount_products'] = Product.objects.filter(
            discounts__start_date__lte=timezone.now(),
            discounts__end_date__gte=timezone.now(),
            is_active=True
        ).distinct()[:12]

        if self.request.user.is_authenticated:
            # Список id товаров, которые в избранном
            context['favorite_product_ids'] = list(
                FavoriteItem.objects.filter(user=self.request.user).values_list('product_id', flat=True)
            )
        else:
            context['favorite_product_ids'] = []
        return context


class CatalogView(ListView):
    """Страница каталога товаров."""
    model = Product
    template_name = 'catalog.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True)

        category_slug = self.kwargs.get('slug', 'all')
        if category_slug != 'all':
            category = get_object_or_404(ProductCategory, slug=category_slug)
            queryset = queryset.filter(category=category)

        selected_categories = self.request.GET.getlist('category')
        if selected_categories:
            queryset = queryset.filter(category__slug__in=selected_categories)

        selected_brands = self.request.GET.getlist('brand')
        if selected_brands:
            queryset = queryset.filter(brands__slug__in=selected_brands)

        price_min = self.request.GET.get('price_min')
        price_max = self.request.GET.get('price_max')
        if price_min:
            queryset = queryset.filter(price__gte=price_min)
        if price_max:
            queryset = queryset.filter(price__lte=price_max)

        # Поиск
        search_query = self.request.GET.get('q')
        if search_query:
            q = search_query.strip()

            # 1. Находим категории (родительские)
            matched_categories = ProductCategory.objects.filter(
                name__iregex=q
            )

            # 2. Добавляем их подкатегории
            all_categories = list(matched_categories)  # если нужно, сюда можно добавить children

            # 3. Находим бренды, подходящие под поиск
            matched_brands = Brand.objects.filter(name__iregex=q)

            # 4. Основной фильтр
            queryset = queryset.filter(
                Q(sku__iregex=q) |  # SKU
                Q(name__iregex=q) |  # название товара
                Q(category__in=all_categories) |  # категории
                Q(brands__in=matched_brands)  # бренды
            ).distinct()

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = ProductCategory.objects.all()
        context['brands'] = Brand.objects.all()
        context['selected_brands'] = self.request.GET.getlist('brand')
        context['selected_categories'] = self.request.GET.getlist('category')
        # --- ДОБАВЬТЕ ЭТОТ БЛОК ---
        if self.request.user.is_authenticated:
            context['favorite_product_ids'] = list(
                FavoriteItem.objects.filter(user=self.request.user).values_list('product_id', flat=True)
            )
        else:
            context['favorite_product_ids'] = []
        # --------------------------

        return context


class DetailProductView(DetailView):
    model = Product
    template_name = 'single_product.html'
    context_object_name = 'product'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        # Оптимизация: загружаем связанные данные одним запросом, чтобы сайт не тормозил
        return super().get_queryset().prefetch_related(
            'variants',
            'attributes',
            'variants__memory_options'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object

        # 1. Работаем с цветами
        color_variants = product.variants.all()
        context['color_variants'] = color_variants
        context['has_available_colors'] = color_variants.filter(is_available=True).exists()

        # 2. Логика скидки (получаем объект или процент)
        # Предполагаем, что у вас есть метод active_discount() в модели Product
        discount = product.active_discount()
        discount_percent = discount.percent if discount else 0

        # 3. Формируем карту памяти { "ID_цвета": [список опций] }
        memory_map = {}
        for color in color_variants:
            # Получаем варианты памяти, привязанные к конкретному цвету
            memories = color.memory_options.all()

            memory_list = []
            for m in memories:
                # Рассчитываем цены с учетом скидки
                original_price = float(m.price) if m.price else 0

                if discount_percent > 0:
                    current_price_val = original_price * (1 - discount_percent / 100)
                    old_price_str = f"{original_price:,.0f}".replace(',', ' ')
                else:
                    current_price_val = original_price
                    old_price_str = None

                memory_list.append({
                    "id": m.id,
                    "size": m.size,
                    "is_available": m.is_available,
                    "price": f"{current_price_val:,.0f}".replace(',', ' '),  # Цена со скидкой
                    "old_price": old_price_str  # Старая цена для зачеркивания
                })

            # ID обязательно строкой для корректной работы JavaScript JSON
            memory_map[str(color.id)] = memory_list

        # Превращаем в JSON для использования в <script>
        context['memory_map_json'] = json.dumps(memory_map, cls=DjangoJSONEncoder)

        # 4. Характеристики (срезаем для удобного вывода)
        all_attributes = list(product.attributes.all())
        context['main_specs'] = all_attributes[:4]
        context['extra_specs'] = all_attributes[4:]

        # 5. СТАТИЧНЫЕ ДАННЫЕ САЙДБАРА (для первого отображения)
        context['product_sku'] = product.sku
        context['stock_status'] = product.stock_status

        # Начальные цены (берутся из метода модели price_display)
        old_p, new_p = product.price_display()
        context['old_price'] = old_p
        context['current_price'] = new_p
        # Есть ли хотя бы один вариант памяти вообще
        has_memory_options = any(
            len(memory_list) > 0
            for memory_list in memory_map.values()
        )

        context['has_memory_options'] = has_memory_options
        context['brands'] = product.brands.all()
        context['product_category'] = product.category
        return context


class FavoritesView(LoginRequiredMixin, TemplateView):
    template_name = 'favorites.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        favorite_products = Product.objects.filter(favoriteitem__user=self.request.user).distinct()

        context['products'] = favorite_products  # передаем продукты в шаблон
        context['count'] = favorite_products.count()  # количество избранных

        context['favorite_product_ids'] = list(favorite_products.values_list('id', flat=True))

        return context


class ToggleFavoriteView(LoginRequiredMixin, View):
    def post(self, request, product_id):
        return self.toggle(request, product_id)

    def get(self, request, product_id):
        return self.toggle(request, product_id)

    def toggle(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        favorite, created = FavoriteItem.objects.get_or_create(user=request.user, product=product)
        if not created:
            favorite.delete()
        return redirect(request.META.get('HTTP_REFERER', 'home'))


class CartView(LoginRequiredMixin, View):
    """Отображение корзины"""
    login_url = 'login'
    redirect_field_name = 'next'
    def get(self, request):
        cart_items = CartItem.objects.filter(user=request.user).select_related('product', 'color', 'memory')
        total = sum([item.total_price() for item in cart_items])
        context = {
            'cart_items': cart_items,
            'total': total,
        }
        return render(request, 'cart.html', context)


class AddToCartView(LoginRequiredMixin, View):
    """Добавление товара в корзину с учетом скидок"""
    login_url = 'login'
    redirect_field_name = 'next'

    def post(self, request):
        product_id = request.POST.get('product_id')
        color_id = request.POST.get('color_id')
        memory_id = request.POST.get('memory_id')
        quantity = int(request.POST.get('quantity', 1))

        product = get_object_or_404(Product, id=product_id)
        color = ProductColorAngle.objects.filter(id=color_id, product=product).first() if color_id else None
        memory = ProductMemoryOption.objects.filter(id=memory_id, product=product).first() if memory_id else None

        # Скидка
        discount = product.active_discount()
        discount_percent = Decimal(discount.percent) / Decimal('100') if discount else Decimal('0')

        # Цена
        if memory:
            price = memory.price * (Decimal('1') - discount_percent)
        else:
            price = product.discounted_price() * (Decimal('1') - discount_percent) if discount else product.discounted_price()

        cart_item, created = CartItem.objects.get_or_create(
            user=request.user,
            product=product,
            color=color,
            memory=memory,
            defaults={'quantity': quantity, 'price': price}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.price = price
            cart_item.save()

        return redirect('cart')

    def get(self, request):
        return redirect('category', slug='all')


class UpdateCartItemView(LoginRequiredMixin, View):
    """Обновление количества товара с учетом скидок"""
    def post(self, request, pk):
        action = request.POST.get('action')  # 'increase', 'decrease', 'remove'
        cart_item = get_object_or_404(CartItem, pk=pk, user=request.user)

        # Скидка
        discount = cart_item.product.active_discount()
        discount_percent = Decimal(discount.percent) / Decimal('100') if discount else Decimal('0')

        # Цена
        if cart_item.memory:
            price = cart_item.memory.price * (Decimal('1') - discount_percent)
        else:
            price = cart_item.product.discounted_price() * (Decimal('1') - discount_percent) if discount else cart_item.product.discounted_price()

        # Действия
        if action == 'increase':
            cart_item.quantity += 1
        elif action == 'decrease':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
            else:
                cart_item.delete()
                return redirect('cart')
        elif action == 'remove':
            cart_item.delete()
            return redirect('cart')

        cart_item.price = price
        cart_item.save()
        return redirect('cart')


class ClearCartView(LoginRequiredMixin, View):
    login_url = 'login'

    def post(self, request):
        CartItem.objects.filter(user=request.user).delete()
        return redirect('cart')

class OfferView(TemplateView):
    template_name = 'offer.html'

class AboutView(TemplateView):
    template_name = 'about.html'


class PrivacyPolicyView(TemplateView):
    template_name = 'privacy-policy.html'
