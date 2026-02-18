from django.contrib import admin

from .models import Category, Faction, Product, Retailer


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Faction)
class FactionAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'slug')
    list_filter = ('category',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Retailer)
class RetailerAdmin(admin.ModelAdmin):
    list_display = ('name', 'website', 'is_active')
    list_filter = ('is_active',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'faction', 'gw_sku', 'msrp', 'updated_at')
    list_filter = ('category', 'faction')
    search_fields = ('name', 'gw_sku')
    prepopulated_fields = {'slug': ('name',)}
    raw_id_fields = ('category', 'faction')
