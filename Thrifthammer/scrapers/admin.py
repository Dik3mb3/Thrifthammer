from django.contrib import admin

from .models import ScrapeJob


@admin.register(ScrapeJob)
class ScrapeJobAdmin(admin.ModelAdmin):
    list_display = ('retailer', 'status', 'products_found', 'prices_updated', 'started_at', 'finished_at')
    list_filter = ('status', 'retailer')
    readonly_fields = ('errors',)
