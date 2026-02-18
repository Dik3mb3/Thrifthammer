from django.contrib import admin

from .models import CurrentPrice, PriceHistory


@admin.register(CurrentPrice)
class CurrentPriceAdmin(admin.ModelAdmin):
    list_display = ('product', 'retailer', 'price', 'in_stock', 'last_seen')
    list_filter = ('retailer', 'in_stock')
    raw_id_fields = ('product', 'retailer')


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'retailer', 'price', 'in_stock', 'recorded_at')
    list_filter = ('retailer',)
    raw_id_fields = ('product', 'retailer')
    date_hierarchy = 'recorded_at'
