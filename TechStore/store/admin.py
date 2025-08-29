from django.contrib import admin
from .models import Category, Product
from django.utils.html import format_html

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {"slug": ("name",)}  # автоматическое заполнение slug
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'discount_price', 'quantity', 'available', 'image_tag')
    list_filter = ('available', 'category')
    search_fields = ('name', 'description')
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ('image_tag',)

    def image_tag(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />'.format(obj.image.url))
        return "-"
    image_tag.short_description = 'Изображение'
