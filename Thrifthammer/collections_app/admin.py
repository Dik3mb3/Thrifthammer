from django.contrib import admin

from .models import CollectionItem


@admin.register(CollectionItem)
class CollectionItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'status', 'quantity', 'price_paid', 'added_at')
    list_filter = ('status',)
    raw_id_fields = ('user', 'product')
