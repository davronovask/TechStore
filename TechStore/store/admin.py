from django.contrib import admin
from solo.admin import SingletonModelAdmin

from .models import ProductCategory, ProductAttribute, Product, ProductDiscount, ProductColorAngle, SocialLink, \
    Contacts, ProductMemoryOption, Banner, Brand
from django.utils.html import format_html
from django.urls import reverse


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'edit_button')
    search_fields = ('name',)
    prepopulated_fields = {"slug": ("name",)}

    def edit_button(self, obj):
        url = reverse('admin:store_productcategory_change', args=[obj.id])
        return format_html('<a class="button" href="{}">Изменить</a>', url)


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ('categories',)


class ProductAttributeInline(admin.TabularInline):
    model = ProductAttribute
    extra = 1
    max_num = 25
    verbose_name = "Характеристика"
    verbose_name_plural = "Характеристики"


class ProductDiscountInline(admin.TabularInline):
    model = ProductDiscount
    extra = 1
    max_num = 1
    verbose_name = "Скидка"
    verbose_name_plural = "Скидки"


class ProductColorAngleInline(admin.StackedInline):
    model = ProductColorAngle
    extra = 1
    max_num = 12
    fieldsets = [
        (None, {
            'fields': ['name', 'color'],
        }),
        ('None)', {
            'fields': [f'image_{i}' for i in range(1, 7)],
        }),
        (None, {
            'fields': ['is_available'],
        }),
    ]


class ProductMemoryOptionInline(admin.TabularInline):
    model = ProductMemoryOption.colors.through  # промежуточная таблица ManyToMany
    extra = 1
    verbose_name = "Вариант памяти"
    verbose_name_plural = "Варианты памяти"


class ProductMemoryOptionInlineStacked(admin.StackedInline):
    model = ProductMemoryOption
    extra = 1
    max_num = 12
    verbose_name = "Вариант памяти"
    verbose_name_plural = "Варианты памяти"
    filter_horizontal = ('colors', )  # галочки для выбора цветов


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'sku', 'price', 'get_discounted_price',
                    'stock_status', 'is_active', 'created_at', 'edit_button')
    search_fields = ('name', 'sku', 'description')
    list_filter = ('category', 'stock_status', 'is_active', 'created_at')
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ('sku',)
    inlines = [
        ProductColorAngleInline,
        ProductAttributeInline,
        ProductDiscountInline,
        ProductMemoryOptionInlineStacked,
    ]
    filter_horizontal = ('brands',)

    def get_discounted_price(self, obj):
        old, new = obj.price_display()
        if old:
            return f"{new}"
        return f"{new}"
    get_discounted_price.short_description = "Цена с учетом скидки"

    def edit_button(self, obj):
        url = reverse('admin:store_product_change', args=[obj.id])
        return format_html('<a class="button" href="{}">Изменить</a>', url)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'brands':
            if hasattr(request, '_obj_') and request._obj_:
                # Показываем бренды, связанные с выбранной категорией
                kwargs["queryset"] = Brand.objects.filter(categories=request._obj_.category)
            else:
                # Если категория ещё не выбрана, поле пустое
                kwargs["queryset"] = Brand.objects.none()
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def get_form(self, request, obj=None, **kwargs):
        request._obj_ = obj
        return super().get_form(request, obj, **kwargs)


class SocialLinkInline(admin.StackedInline):
    model = SocialLink
    can_delete = False
    verbose_name = "Социальные сети"
    verbose_name_plural = "Социальные сети"
    fk_name = None
    max_num = 1
    extra = 0


# ------------------------------
# Контакты + inline SocialLink
# ------------------------------
@admin.register(Contacts)
class ContactsAdmin(SingletonModelAdmin):
    """Админка для контактных данных + соцсетей"""

    fieldsets = (
        ("Адрес", {
            'fields': ('city', 'street'),
        }),
        ("Время работы", {
            'fields': ('work_time',),
            'description': "Время работы будут показаны на сайте",
        }),
    )

    inlines = [SocialLinkInline]

    # Для отображения в списке
    def whatsapp(self, obj):
        sl = obj.social_links.first()
        return sl.whatsapp if sl else "-"
    whatsapp.short_description = "WhatsApp"

    def telegram(self, obj):
        sl = obj.social_links.first()
        return sl.telegram if sl else "-"
    telegram.short_description = "Telegram"

    list_display = ('city', 'street', 'work_time', 'whatsapp', 'telegram')

# ------------------------------
# Баннер
# ------------------------------
from django.utils.safestring import mark_safe


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('get_image', 'title', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    search_fields = ('title',)

    # Метод для вывода миниатюры картинки в списке
    def get_image(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="100" height="auto" style="border-radius: 5px;" />')
        return "Нет изображения"

    get_image.short_description = "Превью"

    fieldsets = (
        (None, {
            'fields': ('title', 'image', 'is_active', 'order')
        }),
    )

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        active_count = Banner.objects.filter(is_active=True).count()
        if active_count > 3:
            self.message_user(request,
                              f"Внимание: у вас активно {active_count} баннеров. На сайте отобразятся только первые 3.",
                              level='WARNING')
        return super().changelist_view(request, extra_context=extra_context)