from django.contrib import admin
from .models import Category, Product, ProductVariant, ProductImage

# This allows you to add variants and images directly on the Product page


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductVariantInline, ProductImageInline]
    list_display = ['name', 'base_price', 'category']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    pass
