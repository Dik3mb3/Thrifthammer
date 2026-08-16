"""
Management command: apply_batch_fixes_aug2026r

Targeted eBay negative-keyword corrections for 7 SKUs across multiple
factions, per user-confirmed match/mismatch review 2026-08-14.

- 43-50 (Death Guard Plague Marines), 48-37 (Space Marine Company Heroes),
  DR-014 (Drukhari Hand of the Archon), P-KHORNE-BLOODCRUSHERS
  (Bloodcrushers of Khorne), prod4870189 (Dark Reapers): new text keywords
  appended to the existing ebay_negative_keywords value (values below are
  the complete desired string, not additive deltas).
- 48-75 (Space Marine Intercessors) and 53-21 (Arjac Rockfist): the
  confirmed-wrong listing has no blockable title keyword, so the eBay
  numeric item ID is appended instead (pure-digit tokens in
  ebay_negative_keywords are matched against the listing's legacy item ID,
  not title text -- see ebay_api_client.py's negative-keyword item-ID check).
  53-21 already had "finecast" excluded; this blocks a second, different
  wrong listing (title has no "finecast").

Usage:
    python manage.py apply_batch_fixes_aug2026r
"""

from django.core.management.base import BaseCommand

from products.models import Product

FIXES = [
    # (gw_sku, new_ebay_negative_keywords)
    # "kill team" dropped to fit the 200-char column limit alongside Mace/Axe -- was already at the cap.
    ('43-50', 'belcher spewer Plaguecaster launcher magazine issue x5 5x x10 10x Icon Despair Flail Corruption Character Heavy Warrior Fighter Bearer Gunner Bombardier Champion plaguespitter heroes Space Mace Axe'),
    ('48-37', 'champion bolter fist legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x Armageddon rifle bionics veteran'),
    ('48-75', 'jump pack legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x Armageddon 307121461112'),
    ('DR-014', 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x Dice'),
    ('P-KHORNE-BLOODCRUSHERS', 'Sealed legions imperialis Resin 04-113 D&D 5e 100th 1926 TShirt Plushie Plush Proxies Foil 164558591084 magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x 3'),
    ('prod4870189', 'legions imperialis Resin 04-113 D&D 5e 100th 1926 TShirt Plushie Plush Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x Operation recall'),
    ('53-21', 'NIB Proxies Foil finecast magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x 256911693800'),
]


class Command(BaseCommand):
    """Apply targeted eBay negative-keyword corrections for 7 SKUs."""

    help = 'apply_batch_fixes_aug2026r — eBay negative-keyword corrections (7 SKUs)'

    def handle(self, *args, **options):
        """Run the command."""
        updated = 0
        for gw_sku, new_value in FIXES:
            count = Product.objects.filter(gw_sku=gw_sku).update(
                ebay_negative_keywords=new_value,
            )
            if count:
                self.stdout.write(f'  updated: {gw_sku}')
                updated += 1
            else:
                self.stdout.write(self.style.WARNING(f'  NOT FOUND: {gw_sku}'))

        self.stdout.write(self.style.SUCCESS(
            f'apply_batch_fixes_aug2026r complete. {updated} product(s) updated.'
        ))
