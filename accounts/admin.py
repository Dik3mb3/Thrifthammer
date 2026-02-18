from django.contrib import admin

from .models import WatchlistItem


@admin.register(WatchlistItem)
class WatchlistItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'target_price', 'created_at')
    list_filter = ('created_at',)
    raw_id_fields = ('user', 'product')
