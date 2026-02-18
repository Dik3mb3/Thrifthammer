from django.conf import settings
from django.db import models


class WatchlistItem(models.Model):
    """A product the user wants to track prices for."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='watchlist_items',
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='watchers',
    )
    target_price = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        help_text='Get notified when price drops below this.',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} watching {self.product.name}"
