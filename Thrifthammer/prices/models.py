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
    currency = models.CharField(
        max_length=3, default='USD',
        help_text='ISO 4217 currency code. USD for US prices, GBP for UK prices.',
    )
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
    shipping_cost = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        help_text=(
            'eBay only — the shipping component included in the price. '
            'The price field stores the total (item price + shipping).'
        ),
    )
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'retailer')
        ordering = ['price']

    def __str__(self):
        if self.not_available:
            return f"{self.product.name} @ {self.retailer.name}: NOT AVAILABLE"
        if self.price is None:
            return f"{self.product.name} @ {self.retailer.name}: no price"
        return f"{self.product.name} @ {self.retailer.name}: ${self.price:.2f}"

    @property
    def discount_pct(self):
        if self.price is not None and self.product.msrp and self.product.msrp > 0:
            return round((1 - self.price / self.product.msrp) * 100, 1)
        return None


class BookFormatPrice(models.Model):
    """
    Format-specific price for a book product at a specific retailer.

    Unlike CurrentPrice (one row per product+retailer), books need a price
    per format (E-Book, Audio Book, Softback, Hardback) per retailer. This
    is a separate model rather than a field added to CurrentPrice so the
    shared, heavily-used CurrentPrice table used by every other product on
    the site is completely untouched by this feature.

    There is no single Product.msrp for books -- MSRP varies by format and
    even by which retailer sets the reference price for that format (GW for
    Softback/Hardback; Audible/Amazon for Audio Book and E-Book, since GW
    does not sell those). is_msrp_source marks which row is that reference;
    compute "% off MSRP" against it instead of Product.msrp.
    """
    FORMAT_EBOOK = 'ebook'
    FORMAT_AUDIOBOOK = 'audiobook'
    FORMAT_SOFTBACK = 'softback'
    FORMAT_HARDBACK = 'hardback'
    FORMAT_CHOICES = [
        (FORMAT_EBOOK, 'E-Book'),
        (FORMAT_AUDIOBOOK, 'Audio Book'),
        (FORMAT_SOFTBACK, 'Paperback'),
        (FORMAT_HARDBACK, 'Hardback'),
    ]

    product = models.ForeignKey(
        'products.Product', on_delete=models.CASCADE, related_name='book_format_prices',
    )
    retailer = models.ForeignKey(
        'products.Retailer', on_delete=models.CASCADE, related_name='book_format_prices',
    )
    format = models.CharField(max_length=20, choices=FORMAT_CHOICES, db_index=True)
    isbn = models.CharField(
        max_length=20, blank=True, default='',
        help_text=(
            'ISBN-13 (or ISBN-10 for older editions) for this specific format/edition. '
            'Used as the precise search key for retailer lookups (e.g. Amazon) instead '
            'of ambiguous title matching, and displayed on the product page.'
        ),
    )
    price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    currency = models.CharField(
        max_length=3, default='USD',
        help_text='ISO 4217 currency code. USD for US prices, GBP for UK prices.',
    )
    url = models.URLField(max_length=2000, blank=True, default='')
    listing_title = models.CharField(max_length=300, blank=True, default='')
    in_stock = models.BooleanField(default=True)
    not_available = models.BooleanField(
        default=False,
        help_text='True if this retailer does not carry this format.',
    )
    manual_url_override = models.BooleanField(default=False)
    is_msrp_source = models.BooleanField(
        default=False,
        help_text=(
            'True if this row is the MSRP reference for this product+format '
            '(Games Workshop for Softback/Hardback; Audible/Amazon for Audio '
            'Book/E-Book). At most one True row per product+format, enforced '
            'at the database level.'
        ),
    )
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'retailer', 'format')
        ordering = ['format', 'price']
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'format'],
                condition=models.Q(is_msrp_source=True),
                name='unique_msrp_source_per_product_format',
            ),
        ]

    def __str__(self):
        if self.not_available:
            return f"{self.product.name} ({self.get_format_display()}) @ {self.retailer.name}: NOT AVAILABLE"
        if self.price is None:
            return f"{self.product.name} ({self.get_format_display()}) @ {self.retailer.name}: no price"
        return f"{self.product.name} ({self.get_format_display()}) @ {self.retailer.name}: ${self.price:.2f}"


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
