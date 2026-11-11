"""
Management command: seed_mm_asoiaf_neutrals_prices

Seeds Miniature Market URLs for A Song of Ice and Fire: Neutrals products. The
master "ASOIAF Miniature Market.xlsx" sheet (Title, Title_URL, Price; 40 rows
spanning every house) had 3 kits that match an existing Neutrals SKU; each match
is confirmed by the manufacturer part number in the Miniature Market URL, which
is CMON's own SKU (CMNSIF1505-ML = SIF505 Neutral Heroes 1, CMNSIF1501-ML =
SIF501 Bolton Cutthroats, CMNSIF1511-ML = SIF511 Stormcrow Mercenaries; the
leading "1" and the "-ML" suffix mark Miniature Market's multilingual printing of
the same CMON box). Every row was also read live on miniaturemarket.com on
2026-11-11 with the Miniature Market scraper's own page reader: price, stock
state and part number all match the sheet (3 of 3).

The sheet's "House Bolton - Heroes 1" (CMNSIF506) is a Bolton house kit that is
not part of the Neutrals collection and has no product yet: not seeded (it
belongs to the future House Bolton build).

The other 15 catalog SKUs are not in the sheet. They were searched for: the
product pages a web search returned (Neutral Heroes 3, Bloody Mummer
Skirmishers, Stormcrow Dervishes, Bolton Blackguards, Stormcrow Archers,
Golden Company Crossbowmen) all answer 404 on miniaturemarket.com today (stale
search-engine copies), so no row is created for them.

Stock on 2026-11-11: Neutral Heroes 1 and Bolton Cutthroats were in stock;
Stormcrow Mercenaries was out of stock and keeps its real price with
in_stock=False. Stock self-heals when the scheduled Miniature Market refresh
runs.

create_defaults pattern: price, in_stock, last_seen are set only on creation so
scraper-set prices survive later runs. url, listing_title, not_available are in
defaults (always updated) and are also repeated in create_defaults, because
Django 5 uses create_defaults INSTEAD of defaults when the row does not exist
yet, as is the case for these new SKUs. Run ONCE by hand; it is not in the
Procfile.

Usage:
    python manage.py seed_mm_asoiaf_neutrals_prices
"""

from django.core.management.base import BaseCommand

MM_PRICES = [
    # (gw_sku, listing_title, price, url, in_stock, not_available)
    ('NEUTRALS-002', 'A Song of Ice & Fire: Neutral - Bolton Cutthroats (Multilingual)', 30.99, 'https://www.miniaturemarket.com/song-ice-fire-neutral-bolton-cutthroats-multilingual-cmnsif1501-ml.html', True, False),  # CMNSIF1501-ML
    ('NEUTRALS-006', 'A Song of Ice & Fire: Neutral - Heroes #1 (Multilingual)', 35.99, 'https://www.miniaturemarket.com/song-ice-fire-neutral-heroes-1-multilingual-cmnsif1505-ml.html', True, False),  # CMNSIF1505-ML
    ('NEUTRALS-011', 'A Song of Ice & Fire: Neutral - Stormcrow Mercenaries (Multilingual)', 30.99, 'https://www.miniaturemarket.com/song-ice-fire-neutral-stormcrow-mercenaries-multilingual-cmnsif1511-ml.html', False, False),  # CMNSIF1511-ML
]


class Command(BaseCommand):
    """Seed Miniature Market URLs for A Song of Ice and Fire: Neutrals products."""

    help = 'seed_mm_asoiaf_neutrals_prices: MM URLs for Neutrals (3 of 18 SKUs confirmed)'

    def handle(self, *args, **options):
        """Create or update the Miniature Market price row for each confirmed SKU."""
        from django.utils import timezone

        from prices.models import CurrentPrice
        from products.models import Product, Retailer

        mm_retailer = Retailer.objects.get(slug='miniature-market')
        seeded = 0

        for (gw_sku, listing_title, price, url, in_stock, not_available) in MM_PRICES:
            product = Product.objects.get(gw_sku=gw_sku, category__slug='asoiaf')
            CurrentPrice.objects.update_or_create(
                product=product,
                retailer=mm_retailer,
                defaults={
                    'listing_title': listing_title,
                    'url': url,
                    'not_available': not_available,
                },
                # create_defaults REPLACES defaults when the row does not exist
                # yet (Django 5), and Neutrals has no Miniature Market rows to
                # update, so the link fields must be repeated here.
                create_defaults={
                    'listing_title': listing_title,
                    'url': url,
                    'not_available': not_available,
                    'price': price,
                    'in_stock': in_stock,
                    'last_seen': timezone.now(),
                },
            )
            self.stdout.write(f'  seeded MM: {gw_sku}')
            seeded += 1

        self.stdout.write(self.style.SUCCESS(
            f'seed_mm_asoiaf_neutrals_prices complete. {seeded} record(s) seeded.'
        ))
