from django.conf import settings
from django.db import models


class CollectionItem(models.Model):
    """A Warhammer product the user owns or wants."""
    STATUS_CHOICES = [
        ('owned', 'Owned'),
        ('building', 'Building'),
        ('painted', 'Painted'),
        ('wishlist', 'Wishlist'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='collection_items',
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='in_collections',
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='owned')
    quantity = models.PositiveIntegerField(default=1)
    price_paid = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        help_text='What you actually paid',
    )
    notes = models.TextField(blank=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.user.username}: {self.product.name} ({self.status})"

    @property
    def savings(self):
        """How much the user saved vs MSRP."""
        if self.price_paid and self.product.msrp:
            return (self.product.msrp - self.price_paid) * self.quantity
        return None
