"""
Gundam/Gunpla catalog models for Thrifthammer.

A separate vertical from the Warhammer catalog (products app), following the
same "price comparison for a model-kit hobby" pattern but with its own
taxonomy: Series (anime/timeline continuity, e.g. Mobile Suit Zeta Gundam)
instead of Faction, and Grade (HG/MG/RG/PG/SD/RE-100/Classic Models/Figure)
as a product-tier filter cutting across every Series.

Retailer and CurrentPrice-style price data reuse products.Retailer (fully
generic, no Warhammer-specific fields) — see gundam.CurrentPrice below for
the Gundam-side price model, which mirrors prices.CurrentPrice's shape.
"""

from django.db import models
from django.utils.text import slugify


class Series(models.Model):
    """
    A Gundam anime/timeline series (e.g. Mobile Suit Zeta Gundam).

    The primary browse/filter axis for the Gundam vertical, analogous to
    Faction on the Warhammer side. A Product can belong to more than one
    Series (see Product.secondary_series) — e.g. a kit released during
    both the Zeta Gundam and Gundam ZZ eras.
    """

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True)

    # ── Series page content (mirrors Faction's hero-page fields) ───────────
    hero_tagline = models.CharField(
        max_length=200, blank=True, default='',
        help_text='Short hero strapline shown on the series page.',
    )
    hero_image_url = models.URLField(
        blank=True, default='',
        help_text='URL to series hero banner image.',
    )
    synopsis = models.TextField(
        blank=True, default='',
        help_text='SEO-optimised series description (~150-200 words) shown on the series page.',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'series'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Auto-generate slug from name if not set."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    """
    A Gunpla kit or Gundam collectible listed in the catalog.

    Products have a canonical MSRP (sourced from Gundam Planet) and are
    linked to CurrentPrice records from various retailers for price
    comparison, mirroring products.Product's role on the Warhammer side.
    """

    GRADE_HG = 'HG'
    GRADE_MG = 'MG'
    GRADE_RG = 'RG'
    GRADE_PG = 'PG'
    GRADE_SD = 'SD'
    GRADE_RE100 = 'RE100'
    GRADE_CLASSIC = 'CLASSIC'
    GRADE_FIGURE = 'FIGURE'
    GRADE_CHOICES = [
        (GRADE_HG, 'High Grade'),
        (GRADE_MG, 'Master Grade'),
        (GRADE_RG, 'Real Grade'),
        (GRADE_PG, 'Perfect Grade'),
        (GRADE_SD, 'Super Deformed'),
        (GRADE_RE100, 'RE/100'),
        (GRADE_CLASSIC, 'Classic Models'),
        (GRADE_FIGURE, 'Figure'),
    ]

    name = models.CharField(max_length=300)
    slug = models.SlugField(max_length=300, unique=True, db_index=True)

    series = models.ForeignKey(
        Series,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='products',
        db_index=True,
        help_text='Primary series this product belongs to.',
    )
    secondary_series = models.ManyToManyField(
        Series,
        blank=True,
        related_name='secondary_products',
        help_text=(
            'Additional series this product should appear under on the site. '
            'The primary series FK above is unchanged. '
            'Use this for kits that span more than one series (e.g. a Zeta '
            'Gundam-era kit also tagged for Gundam ZZ).'
        ),
    )

    grade = models.CharField(
        max_length=10, blank=True, default='', choices=GRADE_CHOICES,
        db_index=True,
        help_text='Product tier filter, cuts across every Series.',
    )
    scale = models.CharField(
        max_length=20, blank=True, default='',
        help_text='Physical build scale (e.g. "1/144", "1/100", "1/60"). '
                  'Verified manually per kit — not auto-derived from Grade.',
    )
    barcode = models.CharField(
        max_length=20, blank=True, default='',
        help_text='Manufacturer JAN barcode, used as a precise eBay/Amazon '
                  'search anchor -- same role as products.Product.isbn plays for books.',
    )
    handle = models.CharField(
        max_length=200, blank=True, default='', db_index=True,
        help_text="Gundam Planet's product URL slug (e.g. "
                  '"hguc-msz-006-zeta-gundam-revive"), used to re-fetch/refresh this exact product.',
    )
    ebay_negative_keywords = models.CharField(
        max_length=400, blank=True, default='',
        help_text=(
            'Space-separated words to exclude from eBay searches (eBay -word syntax). '
            'Use when eBay returns a similar but wrong product -- e.g. a different '
            'colorway/variant Gundam Planet does not carry, or a seller typo. '
            'A pure-digit token is treated as a blocked eBay item ID rather than a '
            'title keyword. Same field/convention as products.Product.ebay_negative_keywords -- '
            'never hardcode per-product exceptions in the matching command itself.'
        ),
    )

    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    msrp = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text='Gundam Planet retail price (reference MSRP for discount comparisons).',
    )

    batch_tag = models.CharField(
        max_length=50, blank=True, default='', db_index=True,
        help_text='Internal label used to group products by the batch they were added in '
                  '(e.g. "zeta-gundam"). Never shown on the site.',
    )
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active', 'series']),
            models.Index(fields=['is_active', 'grade']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Auto-generate slug from name if not set."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_cheapest_price(self):
        """Return the cheapest in-stock CurrentPrice, falling back to cheapest overall."""
        return (
            self.current_prices.filter(in_stock=True).select_related('retailer').order_by('price').first()
            or self.current_prices.select_related('retailer').order_by('price').first()
        )


class CurrentPrice(models.Model):
    """
    The latest known price for a Gundam product at a specific retailer.

    Mirrors prices.CurrentPrice's shape exactly, but points at gundam.Product
    instead of products.Product. Retailer is shared with the Warhammer side
    (products.Retailer is fully generic -- no Warhammer-specific fields).
    """

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='current_prices',
    )
    retailer = models.ForeignKey(
        'products.Retailer', on_delete=models.CASCADE, related_name='gundam_current_prices',
    )
    price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='USD')
    url = models.URLField(
        max_length=2000, blank=True, default='',
        help_text='Direct link to buy.',
    )
    listing_title = models.CharField(max_length=300, blank=True, default='')
    in_stock = models.BooleanField(default=True)
    not_available = models.BooleanField(
        default=False,
        help_text='True if this product is not carried by this retailer.',
    )
    manual_url_override = models.BooleanField(
        default=False,
        help_text='If True, URL and stock status were set manually and must not be '
                  'overwritten by automated scrapers.',
    )
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'retailer')
        ordering = ['price']
        verbose_name_plural = 'current prices'

    def __str__(self):
        if self.not_available:
            return f'{self.product.name} @ {self.retailer.name}: NOT AVAILABLE'
        if self.price is None:
            return f'{self.product.name} @ {self.retailer.name}: no price'
        return f'{self.product.name} @ {self.retailer.name}: ${self.price:.2f}'
