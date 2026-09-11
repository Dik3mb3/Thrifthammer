"""
Management command: seed_nk_warmachine_mercenaries_prices

Seeds Noble Knight URLs for Warmachine: Mercenaries products from the
user-supplied "Mercenaries NK.xlsx" sheet (63 rows). Unlike the smaller
per-faction NK sheets used elsewhere in this rollout, this one is a broad
NK category export spanning every Mercenaries-line product NK carries
across every Warmachine edition (Mk1-Mk4) -- only 7 rows matched an
existing catalog SKU by exact name; the other 56 are old Mk2/Mk3-era
characters, unit boxes, and accessories (Faction Deck, Troop Set, classic
characters like Fiona the Black, Kell Bailoch, Pristinus Silvermane, etc.)
that were never part of our current Mk IV Steamforged catalog -- not
included.

A further 7 rows matched by title/character but with formatting drift from
our own product names (dash vs comma punctuation, e.g. "Alexia - Queen of
the Damned" vs our "Alexia, Queen of the Damned"; or a missing
"(Mercenary)" parenthetical, e.g. "Mind Thief" vs "Mind Thief (Mercenary)")
-- each was fetched and verified live (title, MFG Part #, description)
before being included; all 14 total rows are confirmed genuine, current,
Steamforged Mk IV listings. One title typo caught: NK's own page title says
"Mulgreth" (missing the first 'a') for WMH-059, but the listing's own
description correctly says "Maulgreth, the Charnel Plague" and its MFG
Part # (SFIK-MER087) matches the same code confirmed via Miniature Market
-- treated as an NK data-entry error, not a different product, same
precedent as prior batches.

14 of the 22 Mercenaries products have a confirmed NK listing, all in
stock at verification time.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_nk_warmachine_mercenaries_prices
"""

from django.core.management.base import BaseCommand

NK_PRICES = [
    # (gw_sku, listing_title, price, url, in_stock, not_available)
    ('WMH-001', 'Constance Blaize and Gallant (HIPS)', 72.95, 'https://www.nobleknight.com/P/2148498642/Constance-Blaize-and-Gallant-HIPS?awid=1576', True, False),
    ('WMH-015', 'Gorman di Wolfe, Revolutionary Agent', 18.49, 'https://www.nobleknight.com/P/2148472893/Gorman-di-Wolfe-Revolutionary-Agent?awid=1576', True, False),
    ('WMH-016', 'Eilish Garrity - The Dark Traitor', 14.49, 'https://www.nobleknight.com/P/2148207509/Eilish-Garrity---The-Dark-Traitor?awid=1576', True, False),
    ('WMH-017', 'Alexia - Queen of the Damned', 14.49, 'https://www.nobleknight.com/P/2148207521/Alexia---Queen-of-the-Damned?awid=1576', True, False),
    ('WMH-031', 'Mind Thief', 18.49, 'https://www.nobleknight.com/P/2148494220/Mind-Thief?awid=1576', True, False),
    ('WMH-059', 'Mulgreth - The Charnel Plague', 18.49, 'https://www.nobleknight.com/P/2148207488/Mulgreth---The-Charnel-Plague?awid=1576', True, False),
    ('WMH-060', 'Magnus the Unstoppable and Invictus', 72.95, 'https://www.nobleknight.com/P/2148207478/Magnus-the-Unstoppable-and-Invictus?awid=1576', True, False),
    ('WMH-061', 'Emperor Carver Ultimus Esquire III & War Boar MMD47', 72.95, 'https://www.nobleknight.com/P/2148207481/Emperor-Carver-Ultimus-Esquire-III-and-War-Boar-MMD47?awid=1576', True, False),
    ('WMH-095', 'Hellslinger Phantom', 18.49, 'https://www.nobleknight.com/P/2148498637/Hellslinger-Phantom?awid=1576', True, False),
    ('WMH-188', 'Koldun Lord Damien Korovnik', 14.49, 'https://www.nobleknight.com/P/2148207513/Koldun-Lord-Damien-Korovnik?awid=1576', True, False),
    ('WMH-190', 'Nissak - Totem Huntress Champion', 18.49, 'https://www.nobleknight.com/P/2148207490/Nissak---Totem-Huntress-Champion?awid=1576', True, False),
    ('WMH-191', 'Madam Moriarty', 18.49, 'https://www.nobleknight.com/P/2148207523/Madam-Moriarty?awid=1576', True, False),
    ('WMH-192', 'Bellighul - Master of Pain', 18.49, 'https://www.nobleknight.com/P/2148207525/Bellighul---Master-of-Pain?awid=1576', True, False),
    ('WMH-321', 'Exulon Nostilla and Aberration (HIPS)', 72.95, 'https://www.nobleknight.com/P/2148472875/Exulon-Nostilla-and-Aberration-HIPS?awid=1576', True, False),
]


class Command(BaseCommand):
    """Seed Noble Knight URLs for Warmachine: Mercenaries products."""

    help = 'seed_nk_warmachine_mercenaries_prices — NK URLs for Mercenaries (14 of 22 SKUs confirmed)'

    def handle(self, *args, **options):
        """Run the command."""
        from django.utils import timezone

        from prices.models import CurrentPrice
        from products.models import Product, Retailer

        nk_retailer = Retailer.objects.get(slug='noble-knight-games')
        seeded = 0

        for (gw_sku, listing_title, price, url, in_stock, not_available) in NK_PRICES:
            product = Product.objects.get(gw_sku=gw_sku)
            CurrentPrice.objects.update_or_create(
                product=product,
                retailer=nk_retailer,
                defaults={
                    'listing_title': listing_title,
                    'url': url,
                    'not_available': not_available,
                },
                create_defaults={
                    'price': price,
                    'in_stock': in_stock,
                    'last_seen': timezone.now(),
                },
            )
            self.stdout.write(f'  seeded NK: {gw_sku}')
            seeded += 1

        self.stdout.write(self.style.SUCCESS(
            f'seed_nk_warmachine_mercenaries_prices complete. {seeded} record(s) seeded.'
        ))
