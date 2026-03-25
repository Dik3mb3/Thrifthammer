from django.db import models


class CurrentPrice(models.Model):
    """
    The latest known price for a product at a specific retailer.

    IMPORTANT — cache invalidation:
    prices/signals.py registers post_save and pre_save handlers on this model
    that bust the product detail cache, home page cache, and the list-page
    generation counter automatically whenever a record is saved via .save() or
    update_or_create().

    DO NOT use QuerySet.update() to modify CurrentPrice records in bulk.
    QuerySet.update() bypasses Django signals, which means caches will NOT be
    invalidated and the site will serve stale prices.  Use .save() or
    update_or_create() instead — both trigger the signals correctly.
    """
    product = models.ForeignKey(
        'products.Product', on_delete=models.CASCADE, related_name='current_prices',
    )
    retailer = models.ForeignKey(
        'products.Retailer', on_delete=models.CASCADE, related_name='current_prices',
    )
    price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    url = models.URLField(
        max_length=2000,
        help_text='Direct link to buy (eBay URLs with tracking params can exceed 200 chars)',
        blank=True, default='',
    )
    listing_title = models.CharField(
        max_length=300,
        blank=True,
        default='',
        help_text=(
            "The retailer's own name for this product listing "
            "(e.g. 'Assault Intercessors (2021 Edition)' on Noble Knight). "
            "Populated by import commands; used for display and debugging."
        ),
    )
    in_stock = models.BooleanField(default=True)
    not_available = models.BooleanField(
        default=False,
        help_text='True if this product is not carried by this retailer.',
    )
    manual_url_override = models.BooleanField(
        default=False,
        help_text=(
            'If True, the URL and stock status were set manually and must not be '
            'overwritten by automated scrapers or stock checkers.'
        ),
    )
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'retailer')
        ordering = ['price']

    def __str__(self):
        if self.not_available:
            return f"{self.product.name} @ {self.retailer.name}: NOT AVAILABLE"
        return f"{self.product.name} @ {self.retailer.name}: ${self.price:.2f}"

    @property
    def discount_pct(self):
        if self.price is not None and self.product.msrp and self.product.msrp > 0:
            return round((1 - self.price / self.product.msrp) * 100, 1)
        return None


class PriceHistory(models.Model):
    """Historical price record for charting trends."""
    product = models.ForeignKey(
        'products.Product', on_delete=models.CASCADE, related_name='price_history',
    )
    retailer = models.ForeignKey(
        'products.Retailer', on_delete=models.CASCADE, related_name='price_history',
    )
    price = models.DecimalField(max_digits=8, decimal_places=2)
    in_stock = models.BooleanField(default=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['product', 'retailer', 'recorded_at']),
        ]

    def __str__(self):
        return f"{self.product.name} @ {self.retailer.name}: ${self.price:.2f} ({self.recorded_at:%Y-%m-%d})"
