"""
Management command: apply_batch_fixes_aug2026u

Targeted eBay search-name/keyword corrections for 8 Khador SKUs, per
user-confirmed real listings and root-cause diagnosis 2026-08-15.

Diagnosed via direct query/validation testing against the confirmed real
listing for each SKU (see diagnose_khador_6.py in session scratchpad):

- WMH-039: found only via the CALCULATED-shipping fallback (seller
  dreaming_city_games_001), but rejected by the bits/parts filter on
  "exclusive" -- the real title is "...(Exclusive Variant)", a genuine
  Steamforged variant name, not a bits/parts listing. Allowed.
- WMH-043: query "Warmachine Behemoth, Spirit of Imperial Khador" never
  surfaces the real listing (titled just "Behemoth II") in eBay's top
  results at all -- shortened search name to match.
- WMH-057: only real eBay listing found is a discontinued Mk II metal
  miniature (PIP33005), same issue as the NK listing already rejected for
  this SKU. Blocked by item ID rather than left to keyword luck.
- WMH-058: real listing found and title-matches, but rejected by the
  standalone-digit filter on the "2" in "AC-2" (a model designation, not a
  partial-set count). Allowed.
- WMH-072: same standalone-digit false positive on the "6" in "SKS-6".
  Allowed.
- WMH-177: query "...Great Bear Heavy Warjack" never surfaces the real
  listing (titled just "Great Bear") -- shortened search name.
- WMH-178: query "...Dire Wolf Heavy Warjack" never surfaces the real
  listing (titled "Dire Wolf WarJack", no "Heavy") -- shortened search name.
- WMH-331: was sharing WMH-333's "...Ursine Shifted Variant..." listing.
  User confirmed 2026-08-15 that's wrong for the base (non-variant) SKU --
  "Variant" excluded so WMH-331 no longer matches it.

All 3 shortened search names verified to surface their target listing in
the top-10 Best Match results before being applied here.

Usage:
    python manage.py apply_batch_fixes_aug2026u
"""

from django.core.management.base import BaseCommand

from products.models import Product

SEARCH_NAME_FIXES = [
    # (gw_sku, new_ebay_search_name)
    ('WMH-043', 'Warmachine Khador Behemoth'),
    ('WMH-177', 'Warmachine Khador Great Bear'),
    ('WMH-178', 'Warmachine Khador Dire Wolf'),
]

ALLOWED_WORDS_FIXES = [
    # (gw_sku, new_ebay_allowed_title_words)
    ('WMH-039', '& exclusive'),
    ('WMH-058', '& 2'),
    ('WMH-072', '& 6'),
]

NEGATIVE_KEYWORD_FIXES = [
    # (gw_sku, new_ebay_negative_keywords)
    ('WMH-057', '306854629332'),  # blocked item ID -- confirmed Mk II listing
    ('WMH-331', 'Variant'),
    # blocked item IDs -- all 3 are old-edition/generic resellers that kept
    # outranking the user-confirmed current $85 listing (item 177884363999,
    # "...Behemoth II kdr208", the only candidate with the "kdr###" code
    # convention shared by every other confirmed-current Khador listing
    # this session) on price once the WMH-043 search name was shortened.
    # 128004432903: "...New Complete Rare 2005" (Mk I era).
    # 188132128067: "...PIP 33036 - NIB - OOP" (same old PIP-code pattern
    #   as the rejected WMH-057 listing, explicitly Out Of Print).
    # 177977425131 / 177589939405: generic "Privateer Press" resellers,
    #   no kdr-code, no confirming info either way -- excluded for
    #   consistency with the other two rather than risk a wrong edition.
    ('WMH-043', '128004432903 188132128067 177977425131 177589939405'),
]


class Command(BaseCommand):
    """Apply targeted eBay search-name/keyword corrections for 8 Khador SKUs."""

    help = 'apply_batch_fixes_aug2026u — eBay search-name/keyword corrections (8 SKUs)'

    def handle(self, *args, **options):
        """Run the command."""
        updated = 0

        for gw_sku, new_value in SEARCH_NAME_FIXES:
            count = Product.objects.filter(gw_sku=gw_sku).update(ebay_search_name=new_value)
            self.stdout.write(f'  {"updated" if count else "NOT FOUND"}: {gw_sku} (search_name)')
            updated += count

        for gw_sku, new_value in ALLOWED_WORDS_FIXES:
            count = Product.objects.filter(gw_sku=gw_sku).update(ebay_allowed_title_words=new_value)
            self.stdout.write(f'  {"updated" if count else "NOT FOUND"}: {gw_sku} (allowed_words)')
            updated += count

        for gw_sku, new_value in NEGATIVE_KEYWORD_FIXES:
            count = Product.objects.filter(gw_sku=gw_sku).update(ebay_negative_keywords=new_value)
            self.stdout.write(f'  {"updated" if count else "NOT FOUND"}: {gw_sku} (negative_keywords)')
            updated += count

        self.stdout.write(self.style.SUCCESS(
            f'apply_batch_fixes_aug2026u complete. {updated} field(s) updated.'
        ))
