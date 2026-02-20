import hashlib

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
