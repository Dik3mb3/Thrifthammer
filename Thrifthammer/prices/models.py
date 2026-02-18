from django.db import models


class CurrentPrice(models.Model):
    """The latest known price for a product at a specific retailer."""
    product = models.ForeignKey(
        'products.Product', on_delete=models.CASCADE, related_name='current_prices',
    )
    retailer = models.ForeignKey(
        'products.Retailer', on_delete=models.CASCADE, related_name='current_prices',
    )
    price = models.DecimalField(max_digits=8, decimal_places=2)
    url = models.URLField(help_text='Direct link to buy')
    in_stock = models.BooleanField(default=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'retailer')
        ordering = ['price']

    def __str__(self):
        return f"{self.product.name} @ {self.retailer.name}: ${self.price:.2f}"

    @property
    def discount_pct(self):
        if self.product.msrp and self.product.msrp > 0:
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
