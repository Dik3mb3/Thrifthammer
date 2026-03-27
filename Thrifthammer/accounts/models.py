import hashlib

from django.conf import settings
from django.db import models


class WatchlistItem(models.Model):
    """A product the user wants to track prices for, with optional email alert."""

    ALERT_NONE = 'none'
    ALERT_PRICE = 'price'
    ALERT_SITE_LOW = 'site_low'
    ALERT_PCT_OFF = 'pct_off'
    ALERT_TYPE_CHOICES = [
        (ALERT_NONE,     'No alert'),
        (ALERT_PRICE,    'Specific price'),
        (ALERT_SITE_LOW, 'Website low'),
        (ALERT_PCT_OFF,  '% off MSRP'),
    ]

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
    # Kept for backwards compatibility; used as the threshold when alert_type='price'
    target_price = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        help_text='Alert when best price drops at or below this value.',
    )
    alert_type = models.CharField(
        max_length=10, choices=ALERT_TYPE_CHOICES, default=ALERT_NONE,
        help_text='Which condition triggers the email alert.',
    )
    alert_percent = models.DecimalField(
        max_digits=5, decimal_places=1, null=True, blank=True,
        help_text='Percentage off MSRP that triggers the alert (1–99).',
    )
    email_alerts = models.BooleanField(
        default=False,
        help_text='Send an email when the alert condition is met.',
    )
    last_alerted_price = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        help_text='The price at which we last sent an alert (kept for backwards compat).',
    )
    last_alerted_at = models.DateTimeField(
        null=True, blank=True,
        help_text='Timestamp of the last alert email sent — drives weekly re-alert logic.',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} watching {self.product.name}"

    def alert_condition_met(self, current_price_obj) -> bool:
        """Return True if the current price satisfies this item's alert condition."""
        if self.alert_type == self.ALERT_NONE or current_price_obj is None:
            return False
        price = current_price_obj.price
        if self.alert_type == self.ALERT_PRICE:
            return self.target_price is not None and price <= self.target_price
        if self.alert_type == self.ALERT_SITE_LOW:
            from prices.models import PriceHistory
            min_ever = (
                PriceHistory.objects
                .filter(product=self.product, price__isnull=False)
                .order_by('price')
                .values_list('price', flat=True)
                .first()
            )
            return min_ever is not None and price <= min_ever
        if self.alert_type == self.ALERT_PCT_OFF:
            msrp = self.product.msrp
            if msrp and self.alert_percent:
                threshold = msrp * (1 - self.alert_percent / 100)
                return price <= threshold
        return False


class SecurityProfile(models.Model):
    """
    Stores a security question and hashed answer for password reset
    without requiring an email backend.

    The answer is stored as a SHA-256 hash (lowercased, stripped) so the
    plain-text answer is never persisted.
    """

    QUESTIONS = [
        ('pet',    "What was the name of your first pet?"),
        ('city',   "What city were you born in?"),
        ('school', "What was the name of your primary school?"),
        ('mother', "What is your mother's maiden name?"),
        ('street', "What street did you grow up on?"),
        ('game',   "What was the first Warhammer army you collected?"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='security_profile',
    )
    question = models.CharField(max_length=20, choices=QUESTIONS)
    answer_hash = models.CharField(max_length=64)  # SHA-256 hex digest

    class Meta:
        verbose_name = 'Security Profile'

    def __str__(self):
        return f"SecurityProfile for {self.user.username}"

    @staticmethod
    def hash_answer(raw_answer: str) -> str:
        """Return the SHA-256 hex digest of the normalised answer."""
        normalised = raw_answer.strip().lower()
        return hashlib.sha256(normalised.encode()).hexdigest()

    def check_answer(self, raw_answer: str) -> bool:
        """Return True if raw_answer (after normalisation) matches the stored hash."""
        return self.answer_hash == self.hash_answer(raw_answer)
