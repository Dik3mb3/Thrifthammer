"""
Django admin configuration for the prices app.

Provides admin interfaces for CurrentPrice and PriceHistory, with
search, filtering, and inline editing support.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import CurrentPrice, PriceHistory


@admin.register(CurrentPrice)
class CurrentPriceAdmin(admin.ModelAdmin):
    """
    Admin for the latest known prices per retailer.

    Staff can quickly see all prices for a product, filter by stock
    status or retailer, and search by product name.
    """

    list_display = ('product', 'retailer', 'formatted_price', 'discount_badge', 'in_stock', 'last_seen')
    list_filter = ('retailer', 'in_stock', 'last_seen')
    search_fields = ('product__name', 'product__gw_sku', 'retailer__name')
    raw_id_fields = ('product', 'retailer')
    list_per_page = 50
    date_hierarchy = 'last_seen'

    @admin.display(description='Price')
    def formatted_price(self, obj):
        """Highlight the price in the theme teal colour for quick scanning."""
        return format_html('<strong style="color:#03dac6">${}</strong>', obj.price)

    @admin.display(description='Discount')
    def discount_badge(self, obj):
        """Show the discount percentage vs MSRP, or a dash if not available."""
        pct = obj.discount_pct
        if pct and pct > 0:
            return format_html(
                '<span style="color:#a5d6a7">{}% off</span>', pct,
            )
        return '—'


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    """Admin for historical price records (read-only; populated by scrapers)."""

    list_display = ('product', 'retailer', 'price', 'in_stock', 'recorded_at')
    list_filter = ('retailer', 'in_stock')
    search_fields = ('product__name', 'retailer__name')
    raw_id_fields = ('product', 'retailer')
    date_hierarchy = 'recorded_at'
    # History is append-only — no editing from admin
    readonly_fields = ('product', 'retailer', 'price', 'in_stock', 'recorded_at')

    def has_add_permission(self, request):
        """Prevent manual creation — history is written by scrapers only."""
        return False

    def has_change_permission(self, request, obj=None):
        """History records are immutable."""
        return False
