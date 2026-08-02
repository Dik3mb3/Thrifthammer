"""
Seed Firestorm Games UK prices for Warhammer 40,000: Kill Team.

Idempotent -- CurrentPrice rows are written via update_or_create keyed on
(product, retailer), so re-running is always safe. NEVER writes msrp_gbp --
Firestorm is a discount competitor, not the MSRP source. Only
games-workshop-uk writes msrp_gbp.

Price parsing rule: Firestorm shows two numbers per listing (struck-through
RRP, then sale price). ALWAYS use the lower (sale) price, never the RRP.
RRP is only used as a matching aid to confirm which DB SKU a listing
corresponds to (it should equal Product.msrp_gbp for the matched SKU).

https://www.firestormgames.co.uk/wargames-miniatures/warhammer-40-000-kill-team
28/34 active DB Kill Team products matched here. 3 more (KT-009 Exaction
Squad, KT-010 Imperial Navy Breachers, KT-011 Tempestus Aquilons) were
already seeded by seed_firestorm_games_warhammer_40k_prices.py -- not
duplicated here to avoid redundant writes.

Notable: KT-012 Kasrkin was previously an unresolved gap in the 40k file
(only an "Astra Militarum: Kasrkin" listing was found there, which did
not price-match). This page has the correct "Kill Team: Kasrkin" listing
(£37.40/£42.50, exact msrp match) -- gap resolved.

Gaps (3, no Firestorm listing at all, both null msrp_gbp -- not yet
synced by games-workshop-uk either): KT-102 Void-Dancer Troupe, KT-103
Veteran Guardsmen, KT-105 Intercession Squad.

Excluded (no DB counterpart, consistent with other categories' excluded
patterns -- rulebooks/starter sets/datacards/terrain upgrades/new
releases not yet in our catalog): Kill Team: Exodite (pre-order), Kill
Team: Nemesis Operatives, all "Kill Team Datacards: *" card packs, Kill
Team: Starter Set, Kill Team: Core Book, Kill Team - Nachmund Codex, Kill
team Annual 2022, Kill Team: Spectre Squad (pre-order), Kill Team:
Celestian Insidiants, Kill Team: Murderwing, Kill Team: Deathwatch, Kill
Team: Death Korps, Killzone Upgrade: Compound Siege, Killzone Upgrade:
Tyranid Infestation, WH40K: Boarding Actions Terrain Set, Kill Team -
Sector Imperialis: Ruins, Stormvault Skirmish Case.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_FIRESTORM_SLUG = 'firestorm-games'

_PRICES = [
    ('KT-002', 'Killzone: Tomb World', Decimal('86.24'),
     'https://www.firestormgames.co.uk/killzone:-tomb-world?aff=6a4ab07d1c6f9'),
    ('KT-004', 'Kill Team: Battleclade', Decimal('39.16'),
     'https://www.firestormgames.co.uk/kill-team:-battleclade?aff=6a4ab07d1c6f9'),
    ('KT-005', 'Kill Team: Sanctifiers', Decimal('37.40'),
     'https://www.firestormgames.co.uk/kill-team:-sanctifiers?aff=6a4ab07d1c6f9'),
    ('KT-006', 'Kill Team: Goremongers', Decimal('37.40'),
     'https://www.firestormgames.co.uk/kill-team:-goremongers?aff=6a4ab07d1c6f9'),
    ('KT-007', 'Kill Team - Wrecka Krew', Decimal('37.40'),
     'https://www.firestormgames.co.uk/kill-team---wrecka-krew?aff=6a4ab07d1c6f9'),
    ('KT-008', 'Kill Team: Fellgor Ravagers', Decimal('37.40'),
     'https://www.firestormgames.co.uk/kill-team:-fellgor-ravagers?aff=6a4ab07d1c6f9'),
    ('KT-012', 'Kill Team: Kasrkin', Decimal('37.40'),
     'https://www.firestormgames.co.uk/kill-team:-kasrkin?aff=6a4ab07d1c6f9'),
    ('KT-013', 'Killzone: Bheta-Decima', Decimal('74.10'),
     'https://www.firestormgames.co.uk/killzone:-bheta-decima?aff=6a4ab07d1c6f9'),
    ('KT-014', 'Killzone: Gallowdark', Decimal('74.10'),
     'https://www.firestormgames.co.uk/killzone:-gallowdark?aff=6a4ab07d1c6f9'),
    ('KT-015', 'Kill Team: Upgrade Equipment Pack', Decimal('25.52'),
     'https://www.firestormgames.co.uk/kill-team:-upgrade-equipment-pack-?aff=6a4ab07d1c6f9'),
    ('KT-016', 'Kill Team: Brood Brothers', Decimal('37.40'),
     'https://www.firestormgames.co.uk/kill-team:-brood-brothers?aff=6a4ab07d1c6f9'),
    ('KT-017', 'Kill Team: Nemesis Claw', Decimal('41.36'),
     'https://www.firestormgames.co.uk/kill-team:-nemesis-claw?aff=6a4ab07d1c6f9'),
    ('KT-018', 'Kill Team: Scout Squad', Decimal('43.56'),
     'https://www.firestormgames.co.uk/kill-team:-scout-squad?aff=6a4ab07d1c6f9'),
    ('KT-019', 'Kill Team - Ratlings', Decimal('37.40'),
     'https://www.firestormgames.co.uk/kill-team---ratlings-?aff=6a4ab07d1c6f9'),
    ('KT-020', 'Kill Team: Hearthkyn Salvagers', Decimal('37.40'),
     'https://www.firestormgames.co.uk/kill-team:-hearthkyn-salvagers-?aff=6a4ab07d1c6f9'),
    ('KT-021', 'Kill Team: Hand of the Archon', Decimal('31.68'),
     'https://www.firestormgames.co.uk/kill-team:-hand-of-the-archon?aff=6a4ab07d1c6f9'),
    ('KT-022', 'Kill Team: Hierotek Circle', Decimal('41.36'),
     'https://www.firestormgames.co.uk/kill-team:-hierotek-circle?aff=6a4ab07d1c6f9'),
    ('KT-023', 'Kill Team: Farstalker Kinband', Decimal('37.40'),
     'https://www.firestormgames.co.uk/kill-team:-farstalker-kinband?aff=6a4ab07d1c6f9'),
    ('KT-024', "Kill Team: T'au Empire Vespid Stingwings", Decimal('37.40'),
     'https://www.firestormgames.co.uk/kill-team:-tau-empire-vespid-stingwings?aff=6a4ab07d1c6f9'),
    ('KT-025', 'Kill Team: Hernkyn Yaegirs', Decimal('37.40'),
     'https://www.firestormgames.co.uk/kill-team:-hernkyn-yaegirs?aff=6a4ab07d1c6f9'),
    ('KT-026', 'Kill Team - Wolf Scouts', Decimal('38.25'),
     'https://www.firestormgames.co.uk/kill-team---wolf-scouts?aff=6a4ab07d1c6f9'),
    ('KT-027', 'Kill Team: Mandrakes', Decimal('43.56'),
     'https://www.firestormgames.co.uk/kill-team:-mandrakes?aff=6a4ab07d1c6f9'),
    ('KT-028', 'Kill Team - XV26 Stealth Battlesuits', Decimal('38.25'),
     'https://www.firestormgames.co.uk/kill-team---xv26-stealth-battlesuits?aff=6a4ab07d1c6f9'),
    ('KT-029', 'Kill Team: Canoptek Circle', Decimal('41.36'),
     'https://www.firestormgames.co.uk/kill-team:-canoptek-circle?aff=6a4ab07d1c6f9'),
    ('KT-030', 'Kill Team: Raveners', Decimal('37.40'),
     'https://www.firestormgames.co.uk/kill-team:-raveners?aff=6a4ab07d1c6f9'),
    ('KT-031', 'Killzone: Volkus', Decimal('74.80'),
     'https://www.firestormgames.co.uk/killzone:-volkus?aff=6a4ab07d1c6f9'),
    ('KT-032', 'Kill Team: Blades Of Khaine', Decimal('43.56'),
     'https://www.firestormgames.co.uk/kill-team:-blades-of-khaine?aff=6a4ab07d1c6f9'),
    ('KT-033', 'Kill Team: Inquisitorial Agents', Decimal('31.68'),
     'https://www.firestormgames.co.uk/kill-team:-inquisitorial-agents?aff=6a4ab07d1c6f9'),
]


class Command(BaseCommand):
    help = 'Seed Firestorm Games UK prices for Warhammer 40,000: Kill Team. Idempotent.'

    def handle(self, *args, **options):
        retailer, created = Retailer.objects.get_or_create(
            slug=_FIRESTORM_SLUG,
            defaults={
                'name': 'Firestorm Games',
                'website': 'https://www.firestormgames.co.uk/?aff=6a4ab07d1c6f9',
                'country': 'UK',
                'is_active': True,
                'is_uk': True,
            },
        )
        if created:
            self.stdout.write(f'Created retailer: {retailer.name}')

        seeded = 0
        skipped = 0
        for sku, label, gbp_price, url in _PRICES:
            products = list(Product.objects.filter(gw_sku=sku))
            if not products:
                self.stderr.write(f'SKIP — SKU {sku} ({label}) not in DB')
                skipped += 1
                continue

            for product in products:
                CurrentPrice.objects.update_or_create(
                    product=product,
                    retailer=retailer,
                    defaults={
                        'price': gbp_price,
                        'currency': 'GBP',
                        'url': url,
                        'in_stock': True,
                        'not_available': False,
                    },
                )
                seeded += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded {seeded} Firestorm Games Kill Team prices. Skipped: {skipped}.'
            )
        )
