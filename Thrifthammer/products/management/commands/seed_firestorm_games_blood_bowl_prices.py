"""
Seed Firestorm Games UK prices for Blood Bowl.

Idempotent -- CurrentPrice rows are written via update_or_create keyed on
(product, retailer), so re-running is always safe. NEVER writes msrp_gbp --
Firestorm is a discount competitor, not the MSRP source. Only
games-workshop-uk writes msrp_gbp.

Price parsing rule: Firestorm shows two numbers per listing (struck-through
RRP, then sale price). ALWAYS use the lower (sale) price, never the RRP.
RRP is only used as a matching aid to confirm which DB SKU a listing
corresponds to (it should equal Product.msrp_gbp for the matched SKU).

Blood Bowl products in the DB have no faction FK (faction=None); matching
was done against the full flat BB-XXX product list in one pass.

https://www.firestormgames.co.uk/wargames-miniatures/blood-bowl
37/100 matched. Firestorm's Blood Bowl catalog only carries full team
boxes, the two rulebook/starter products, and a handful of "Big Guy"
models and iconic star players (Ogre, Troll, Griff Oberwald, Varag
Ghoul-Chewer, Elf and Dwarf Biased Referees) -- it does not carry the
~60 individual star player blister packs that make up most of the DB's
Blood Bowl catalog (Skrorg Snowpelt, Kiroth Krakeneye, Dribl & Drull,
etc.). Confirmed no pagination/hidden section on the page. Flagged to
the user rather than assumed.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_FIRESTORM_SLUG = 'firestorm-games'

_PRICES = [
    ('BB-025', 'Blood Bowl: Bretonnian Team', Decimal('29.92'),
     'https://www.firestormgames.co.uk/blood-bowl:-bretonnian-team?aff=6a4ab07d1c6f9'),
    ('BB-002', 'Blood Bowl: Official Rulebook (Third Season)', Decimal('31.68'),
     'https://www.firestormgames.co.uk/blood-bowl:-official-rulebook-third-season?aff=6a4ab07d1c6f9'),
    ('BB-001', 'Blood Bowl: Third Season Edition', Decimal('77.44'),
     'https://www.firestormgames.co.uk/blood-bowl:-third-season-edition?aff=6a4ab07d1c6f9'),
    ('BB-023', 'Blood Bowl: High Elf Blood Bowl Team', Decimal('29.92'),
     'https://www.firestormgames.co.uk/blood-bowl:-high-elf-blood-bowl-team?aff=6a4ab07d1c6f9'),
    ('BB-024', 'Blood Bowl: Tomb Kings Team', Decimal('29.92'),
     'https://www.firestormgames.co.uk/blood-bowl:-tomb-kings-team?aff=6a4ab07d1c6f9'),
    ('BB-026', 'Blood Bowl: Chaos Dwarf Team', Decimal('29.92'),
     'https://www.firestormgames.co.uk/blood-bowl:-chaos-dwarf-team?aff=6a4ab07d1c6f9'),
    ('BB-009', 'Blood Bowl: Gnome Team', Decimal('29.92'),
     'https://www.firestormgames.co.uk/blood-bowl:-gnome-team?aff=6a4ab07d1c6f9'),
    ('BB-027', 'Blood Bowl - Vampire Team', Decimal('29.92'),
     'https://www.firestormgames.co.uk/blood-bowl---vampire-team?aff=6a4ab07d1c6f9'),
    ('BB-091', 'Blood Bowl: Underworld Denizens Team - The Underworld Creepers', Decimal('29.92'),
     'https://www.firestormgames.co.uk/blood-bowl:-underworld-denizens-team---the-underworld-creepers?aff=6a4ab07d1c6f9'),
    ('BB-010', 'Blood Bowl: Old World Alliance Team - The Middenheim Maulers', Decimal('29.92'),
     'https://www.firestormgames.co.uk/blood-bowl:-old-world-alliance-team---the-middenheim-maulers?aff=6a4ab07d1c6f9'),
    ('BB-003', 'Blood Bowl - Amazon Team', Decimal('29.92'),
     'https://www.firestormgames.co.uk/blood-bowl---amazon-team?aff=6a4ab07d1c6f9'),
    ('BB-004', 'Blood Bowl - Norse Team', Decimal('29.92'),
     'https://www.firestormgames.co.uk/blood-bowl---norse-team?aff=6a4ab07d1c6f9'),
    ('BB-005', 'Blood Bowl: Khorne Team', Decimal('29.92'),
     'https://www.firestormgames.co.uk/blood-bowl:-khorne-team?aff=6a4ab07d1c6f9'),
    ('BB-056', 'Blood Bowl - Elf and Dwarf Biased Referees', Decimal('12.32'),
     'https://www.firestormgames.co.uk/blood-bowl---elf-and-dwarf-biased-referees?aff=6a4ab07d1c6f9'),
    ('BB-057', 'Blood Bowl - Varag Ghoul-Chewer', Decimal('13.30'),
     'https://www.firestormgames.co.uk/blood-bowl---varag-ghoul-chewer?aff=6a4ab07d1c6f9'),
    ('BB-099', 'Blood Bowl - Griff Oberwald', Decimal('13.30'),
     'https://www.firestormgames.co.uk/blood-bowl---griff-oberwald?aff=6a4ab07d1c6f9'),
    ('BB-011', 'Blood Bowl - Imperial Nobility Team - The Bögenhafen Barons', Decimal('29.92'),
     'https://www.firestormgames.co.uk/blood-bowl---imperial-nobility-team---the-bgenhafen-barons?aff=6a4ab07d1c6f9'),
    ('BB-092', 'Blood Bowl - Black Orc Team - The Thunder Valley Greenskins', Decimal('29.92'),
     'https://www.firestormgames.co.uk/blood-bowl---black-orc-team---the-thunder-valley-greenskins?aff=6a4ab07d1c6f9'),
    ('BB-006', 'Blood Bowl - Gwaka\'moli Crater Gators: Lizardmen Blood Bowl Team', Decimal('29.92'),
     'https://www.firestormgames.co.uk/blood-bowl---gwakamoli-crater-gators:-lizardmen-blood-bowl-team?aff=6a4ab07d1c6f9'),
    ('BB-008', 'Blood Bowl - Nurgle\'s Rotters - Nurgle Blood Bowl Team', Decimal('29.92'),
     'https://www.firestormgames.co.uk/blood-bowl---nurgles-rotters---nurgle-blood-bowl-team?aff=6a4ab07d1c6f9'),
    ('BB-017', 'Blood Bowl - The Doom Lords - Chaos Chosen Blood Bowl Team', Decimal('29.92'),
     'https://www.firestormgames.co.uk/blood-bowl---the-doom-lords---chaos-chosen-blood-bowl-team?aff=6a4ab07d1c6f9'),
    ('BB-033', 'Blood Bowl - Ogre', Decimal('20.43'),
     'https://www.firestormgames.co.uk/blood-bowl---ogre?aff=6a4ab07d1c6f9'),
    ('BB-022', 'Blood Bowl - The Dwarf Giants - Dwarf Blood Bowl Team', Decimal('29.92'),
     'https://www.firestormgames.co.uk/blood-bowl---the-dwarf-giants---dwarf-blood-bowl-team?aff=6a4ab07d1c6f9'),
    ('BB-016', 'Blood Bowl - The Skavenblight Scramblers - Skaven Blood Bowl Team', Decimal('29.92'),
     'https://www.firestormgames.co.uk/blood-bowl---the-skavenblight-scramblers---skaven-blood-bowl-team?aff=6a4ab07d1c6f9'),
    ('BB-007', 'Blood Bowl - Necromantic Horror Team: The Wolfenburg Crypt-Stealers', Decimal('29.92'),
     'https://www.firestormgames.co.uk/blood-bowl---necromantic-horror-team:-the-wolfenburg-crypt-stealers?aff=6a4ab07d1c6f9'),
    ('BB-034', 'Blood Bowl - Treeman', Decimal('18.92'),
     'https://www.firestormgames.co.uk/blood-bowl---treeman?aff=6a4ab07d1c6f9'),
    ('BB-018', 'Blood Bowl - Crud Creek Nosepickers - Snotling Blood Bowl Team', Decimal('29.92'),
     'https://www.firestormgames.co.uk/blood-bowl---crud-creek-nosepickers---snotling-blood-bowl-team?aff=6a4ab07d1c6f9'),
    ('BB-013', 'Blood Bowl - Fire Mountain Gut Busters', Decimal('29.92'),
     'https://www.firestormgames.co.uk/blood-bowl---fire-mountain-gut-busters?aff=6a4ab07d1c6f9'),
    ('BB-019', 'Blood Bowl - Athelorn Avengers', Decimal('29.92'),
     'https://www.firestormgames.co.uk/blood-bowl---athelorn-avengers?aff=6a4ab07d1c6f9'),
    ('BB-020', 'Blood Bowl - The Greenfield Grasshuggers', Decimal('29.92'),
     'https://www.firestormgames.co.uk/blood-bowl---the-greenfield-grasshuggers?aff=6a4ab07d1c6f9'),
    ('BB-015', 'Blood Bowl - Champions of Death Team', Decimal('29.92'),
     'https://www.firestormgames.co.uk/blood-bowl---champions-of-death-team?aff=6a4ab07d1c6f9'),
    ('BB-014', 'Blood Bowl - The Naggaroth Nightmares', Decimal('29.92'),
     'https://www.firestormgames.co.uk/blood-bowl---the-naggaroth-nightmares?aff=6a4ab07d1c6f9'),
    ('BB-021', 'Blood Bowl - Elfheim Eagles Team', Decimal('29.92'),
     'https://www.firestormgames.co.uk/elfheim-eagles-team?aff=6a4ab07d1c6f9'),
    ('BB-093', 'Blood Bowl - The Scarcrag Snivellers', Decimal('29.92'),
     'https://www.firestormgames.co.uk/blood-bowl---the-scarcrag-snivellers?aff=6a4ab07d1c6f9'),
    ('BB-094', 'Blood Bowl - Orc Blood Bowl Team - Gouged Eye', Decimal('32.31'),
     'https://www.firestormgames.co.uk/blood-bowl---orc-blood-bowl-team---gouged-eye?aff=6a4ab07d1c6f9'),
    ('BB-038', 'Blood Bowl - Troll', Decimal('18.92'),
     'https://www.firestormgames.co.uk/blood-bowl-troll?aff=6a4ab07d1c6f9'),
    ('BB-012', 'Blood Bowl - Human Team: Reikland Reavers', Decimal('32.31'),
     'https://www.firestormgames.co.uk/blood-bowl---human-team:-reikland-reavers?aff=6a4ab07d1c6f9'),
]


class Command(BaseCommand):
    help = 'Seed Firestorm Games UK prices for Blood Bowl. Idempotent.'

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
                f'Seeded {seeded} Firestorm Games Blood Bowl prices. Skipped: {skipped}.'
            )
        )
