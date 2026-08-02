"""
Seed Firestorm Games UK prices for Malifaux, and derive a UK-side Wyrd
Games GBP reference price from Firestorm's RRP.

SPECIAL CASE (explicit one-time user instruction, UK side only, not a
pattern for future categories): Malifaux has no GW-style UK MSRP source,
so this command additionally writes:
  - product.msrp_gbp, set from Firestorm's RRP (the higher,
    struck-through price on each listing)
  - a SEPARATE new UK-flagged retailer, wyrd-games-uk, priced at that
    same Firestorm RRP in GBP, using the URL already stored on the
    existing US `wyrd-games` retailer's CurrentPrice row (manufacturer
    product pages have no separate UK storefront)

This command NEVER touches the existing `wyrd-games` (US, is_uk=False,
USD) retailer or its CurrentPrice rows -- those are read-only here, only
used as a URL source. It also never touches populate_malifaux_products.py,
seed_mm_malifaux_prices.py, seed_nk_malifaux_prices.py, or any other
existing Malifaux file. This is additive only.

The `firestorm-games` CurrentPrice row follows the normal pattern used
for every other category this session: the lower (sale) price, GBP,
linking to Firestorm's own product page with the affiliate code.

https://www.firestormgames.co.uk/wargames-miniatures/malifaux
50/51 active DB MAL-XXX SKUs matched (msrp_gbp was null for all 51
going in, so matching was done entirely by name -- Malifaux's DB
catalog is the current 4th Edition lineup, which maps almost 1:1 to
Firestorm's listings). Several matches used a distinctive surname/title
as the sole candidate rather than an exact full-title match (e.g.
MAL-050 "Damian Ravencroft, Aspirant" matched to Firestorm's generically
named "Arcanists - Ravencroft Core Box" -- confirmed correct via the
existing Wyrd Games URL slug, which is literally
".../damian-ravencroft-aspirant"). MAL-002 required picking the correct
of two "Gaining Grounds" listings ("Season Zero" vs the current "Season
4") by name, not price alone.

Gap (1): MAL-016 "Seamus, AKA Sebastian Baker" -- Firestorm's only
"Seamus" listings are the already-matched "Seamus, The Last Breath"
(4th Edition) and a generically-named "Resurrectionists - Seamus Core
Box" of uncertain edition/title -- left unmatched rather than guessed.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_FIRESTORM_SLUG = 'firestorm-games'
_WYRD_UK_SLUG = 'wyrd-games-uk'
_FS_BASE = 'https://www.firestormgames.co.uk'
_FS_AFF = '?aff=6a4ab07d1c6f9'

# (gw_sku, label, firestorm_sale_gbp, firestorm_rrp_gbp, firestorm_path, wyrd_us_url)
_PRICES = [
    ('MAL-001', 'Malifaux - Two‑Player Starter - 4th Edition', Decimal('96.16'), Decimal('106.85'),
     '/malifaux---twoplayer-starter---4th-edition',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-two-player-starter'),
    ('MAL-002', 'Malifaux - Gaining Grounds Fourth - Season Zero - 4th Edition', Decimal('9.22'), Decimal('10.25'),
     '/malifaux---gaining-grounds-fourth---season-zero---4th-edition',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-gaining-grounds-season-zero'),
    ('MAL-003', 'Malifaux - Rules Manual - 4th Edition', Decimal('12.06'), Decimal('13.40'),
     '/malifaux---rules-manual---4th-edition',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-rules-manual'),
    ('MAL-004', 'Malifaux - Pandora, Despair’s Desire - 4th Edition', Decimal('44.10'), Decimal('49.00'),
     '/malifaux---pandora-despairs-desire---4th-edition',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-pandora-despairs-desire'),
    ('MAL-005', 'Malifaux - Seamus, The Last Breath - 4th Edition', Decimal('46.08'), Decimal('51.20'),
     '/malifaux---seamus-the-last-breath---4th-edition',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-seamus-the-last-breath'),
    ('MAL-006', 'Malifaux - Sandeep Desai, The Quiet Flame - 4th Edition', Decimal('46.08'), Decimal('51.20'),
     '/malifaux---sandeep-desai-the-quiet-flame---4th-edition',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-sandeep-desai-the-quiet-flame'),
    ('MAL-007', 'Malifaux - Yan Lo, The Spirit Walker - 4th Edition', Decimal('47.07'), Decimal('52.30'),
     '/malifaux---yan-lo-the-spirit-walker---4th-edition',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-yan-lo-the-spirit-walker'),
    ('MAL-008', 'Malifaux - Wong, The Wonderful - 4th Edition', Decimal('44.10'), Decimal('49.00'),
     '/malifaux---wong-the-wonderful---4th-edition',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-wong-the-wonderful'),
    ('MAL-009', 'Malifaux - Pandora, Tyrant Torn - 4th Edition', Decimal('47.07'), Decimal('52.30'),
     '/malifaux---pandora-tyrant-torn---4th-edition',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-pandora-tyrant-torn'),
    ('MAL-010', 'Malifaux - The Dreamer, Fast Asleep - 4th Edition', Decimal('50.09'), Decimal('55.65'),
     '/malifaux---the-dreamer-fast-asleep---4th-edition',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-the-dreamer-fast-asleep'),
    ('MAL-011', 'Malifaux - Ana Lycarayen, The Resolute - 4th Edition', Decimal('46.08'), Decimal('51.20'),
     '/malifaux---ana-lycarayen-the-resolute---4th-edition',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-anya-lycarayen-the-resolute'),
    ('MAL-012', 'Malifaux - Viktoria Chambers, Ashes and Blood - 4th Edition', Decimal('44.10'), Decimal('49.00'),
     '/malifaux---viktoria-chambers-ashes-and-blood---4th-edition',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-viktoria-chambers-ashes-and-blood'),
    ('MAL-013', 'Malifaux - The Clampetts, Fisherfolk - 4th Edition', Decimal('44.10'), Decimal('49.00'),
     '/malifaux---the-clampetts-fisherfolk---4th-edition',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-the-clampetts-fisherfolk'),
    ('MAL-014', 'Malifaux - Dr. McMourning, Malpractitioner - 4th Edition', Decimal('47.07'), Decimal('52.30'),
     '/malifaux---dr-mcmourning-malpractitioner---4th-edition',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-dr-mcmourning-malpractitioner'),
    ('MAL-015', 'Malifaux - Dr. McMourning, Insanitary - 4th Edition', Decimal('50.49'), Decimal('56.10'),
     '/malifaux---dr-mcmourning-insanitary---4th-edition',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-dr-mcmourning-insanitary'),
    ('MAL-017', 'Malifaux - Jack Daw, Spirit of Betrayal - 4th Edition', Decimal('44.10'), Decimal('49.00'),
     '/malifaux---jack-daw-spirit-of-betrayal---4th-edition',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-jack-daw-spirit-of-betrayal'),
    ('MAL-018', 'Malifaux - Nellie Cochrane, Voice of Disorder - 4th Edition', Decimal('50.09'), Decimal('55.65'),
     '/malifaux---nellie-cochrane-voice-of-disorder---4th-edition',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-nellie-cochrane-voice-of-disorder'),
    ('MAL-019', 'Malifaux - Lucius Mattheson, In Plain Sight - 4th Edition', Decimal('44.10'), Decimal('49.00'),
     '/malifaux---lucius-mattheson-in-plain-sight---4th-edition',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-lucius-mattheson-in-plain-sight'),
    ('MAL-020', 'Malifaux - Guild Faction Pack', Decimal('31.14'), Decimal('34.60'),
     '/malifaux---guild-faction-pack',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-guild-faction-pack'),
    ('MAL-021', 'Malifaux - Arcanist Faction Pack', Decimal('31.14'), Decimal('34.60'),
     '/malifaux---arcanist-faction-pack',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-arcanist-faction-pack'),
    ('MAL-022', 'Malifaux - Resurrectionist Faction Pack', Decimal('31.14'), Decimal('34.60'),
     '/malifaux---resurrectionist-faction-pack',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-resurrectionist-faction-pack'),
    ('MAL-023', 'Malifaux - Neverborn Faction Pack', Decimal('31.14'), Decimal('34.60'),
     '/malifaux---neverborn-faction-pack',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-neverborn-faction-pack'),
    ('MAL-024', 'Malifaux - Ten Thunders Faction Pack', Decimal('31.14'), Decimal('34.60'),
     '/malifaux---ten-thunders-faction-pack',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-ten-thunders-faction-pack'),
    ('MAL-025', 'Malifaux - Outcast Faction Pack', Decimal('31.14'), Decimal('34.60'),
     '/malifaux---outcast-faction-pack',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-outcast-faction-pack'),
    ('MAL-026', 'Malifaux - Bayou Faction Pack', Decimal('31.14'), Decimal('34.60'),
     '/malifaux---bayou-faction-pack',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-bayou-faction-pack'),
    ('MAL-027', 'Malifaux - Explorer Society Faction Pack', Decimal('31.14'), Decimal('34.60'),
     '/malifaux---explorer-society-faction-pack',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-explorer-s-society-faction-pack'),
    ('MAL-028', 'Malifaux - Guild Faction Book - 4th Edition', Decimal('20.07'), Decimal('22.30'),
     '/malifaux---guild-faction-book---4th-edition',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-guild-faction-book'),
    ('MAL-029', 'Malifaux - Resurrectionist Faction Book - 4th Edition', Decimal('20.07'), Decimal('22.30'),
     '/malifaux---resurrectionist-faction-book---4th-edition',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-resurrectionist-faction-book'),
    ('MAL-030', 'Malifaux - Arcanists Faction Book - 4th Edition', Decimal('20.07'), Decimal('22.30'),
     '/malifaux---arcanists-faction-book---4th-edition',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-arcanist-faction-book'),
    ('MAL-031', 'Malifaux - Neverborn Faction Book - 4th Edition', Decimal('20.07'), Decimal('22.30'),
     '/malifaux---neverborn-faction-book---4th-edition',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-neverborn-faction-book'),
    ('MAL-032', 'Malifaux - Ten Thunders Faction Book - 4th Edition', Decimal('20.07'), Decimal('22.30'),
     '/malifaux---ten-thunders-faction-book---4th-edition',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-ten-thunders-faction-book'),
    ('MAL-033', 'Malifaux - Outcast Faction Book - 4th Edition', Decimal('22.95'), Decimal('25.50'),
     '/malifaux---outcast-faction-book---4th-edition',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-outcast-faction-book'),
    ('MAL-034', 'Malifaux - Bayou Faction Book - 4th Edition', Decimal('20.07'), Decimal('22.30'),
     '/malifaux---bayou-faction-book---4th-edition',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-bayou-faction-book'),
    ('MAL-035', 'Malifaux - Explorer’s Society Faction Book - 4th Edition', Decimal('20.07'), Decimal('22.30'),
     '/malifaux---explorers-society-faction-book---4th-edition',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-explorer-s-society-faction-book'),
    ('MAL-036', 'Malifaux - Tara, Voidcaller - 4th Edition', Decimal('44.10'), Decimal('49.00'),
     '/malifaux---tara-voidcaller---4th-edition',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/tara-voidcaller'),
    ('MAL-037', 'Malifaux - Nexus, Heart of the Hive - 4th Edition', Decimal('46.08'), Decimal('51.20'),
     '/malifaux---nexus-heart-of-the-hive---4th-edition',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/nexus-heart-of-the-hive'),
    ('MAL-038', 'Malifaux - Iconic - Haunted Harmony - 4th Edition', Decimal('52.11'), Decimal('57.90'),
     '/malifaux---iconic---haunted-harmony---4th-edition',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/iconic-haunted-harmony-molly-and-kirai'),
    ('MAL-039', 'Malifaux - Colette Du Bois, Star of the Show - 4th Edition', Decimal('44.10'), Decimal('49.00'),
     '/malifaux---colette-du-bois-star-of-the-show---4th-edition',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-colette-du-bois-star-of-the-show'),
    ('MAL-040', 'Malifaux - Jakob Lynch, Wild Card - 4th Edition', Decimal('50.09'), Decimal('55.65'),
     '/malifaux---jakob-lynch-wild-card---4th-edition',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-jakob-lynch-wild-card'),
    ('MAL-041', 'Malifaux - Tara, Timeless - 4th Edition', Decimal('48.11'), Decimal('53.45'),
     '/malifaux---tara-timeless---4th-edition',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-tara-timeless'),
    ('MAL-042', 'Malifaux - Sonnia Criid, Unrelenting - 4th Edition', Decimal('44.10'), Decimal('49.00'),
     '/malifaux---sonnia-criid-unrelenting---4th-edition',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-sonnia-criid-unrelenting'),
    ('MAL-043', 'Malifaux - Sandeep Desai, Font of Magic - 4th Edition', Decimal('58.09'), Decimal('64.55'),
     '/malifaux---sandeep-desai-font-of-magic---4th-edition',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-sandeep-desai-font-of-magic'),
    ('MAL-044', 'The Guild - Dashel Barker, The Old Guard', Decimal('48.06'), Decimal('53.40'),
     '/the-guild---dashel-barker-the-old-guard',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-dashel-barker-the-old-guard'),
    ('MAL-045', 'Outcasts - Viktoria, Twin Blades', Decimal('44.05'), Decimal('48.95'),
     '/outcasts---viktoria-twin-blades',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-viktoria-chambers-twin-blades'),
    ('MAL-046', 'Explorer’s Society - Intrepid Fate', Decimal('32.85'), Decimal('36.50'),
     '/explorers-society---intrepid-fate',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-intrepid-fate'),
    ('MAL-047', 'Bayou - Clampetts, Bally Hoo Bucket', Decimal('59.26'), Decimal('65.85'),
     '/bayou---clampetts-bally-hoo-bucket',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-the-clampetts-bally-hoo-bucket'),
    ('MAL-048', 'Resurrectionists - Carrion Fate', Decimal('33.62'), Decimal('37.35'),
     '/resurrectionists---carrion-fate',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-carrion-fate'),
    ('MAL-049', 'Arcanists - Arcane Fate', Decimal('33.62'), Decimal('37.35'),
     '/arcanists---arcane-fate',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-arcane-fate'),
    ('MAL-050', 'Arcanists - Ravencroft Core Box', Decimal('40.95'), Decimal('45.50'),
     '/arcanists---ravencroft-core-box',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/damian-ravencroft-aspirant'),
    ('MAL-051', 'Malifaux - Index of the Untold', Decimal('28.03'), Decimal('31.15'),
     '/malifaux---index-of-the-untold',
     'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-index-of-the-untold-campaign-book'),
]


class Command(BaseCommand):
    help = (
        'Seed Firestorm Games UK prices for Malifaux and a UK-side Wyrd Games '
        'GBP reference price derived from Firestorm RRP. Idempotent.'
    )

    def handle(self, *args, **options):
        firestorm, created = Retailer.objects.get_or_create(
            slug=_FIRESTORM_SLUG,
            defaults={
                'name': 'Firestorm Games',
                'website': f'{_FS_BASE}/{_FS_AFF}',
                'country': 'UK',
                'is_active': True,
                'is_uk': True,
            },
        )
        if created:
            self.stdout.write(f'Created retailer: {firestorm.name}')

        wyrd_uk, created = Retailer.objects.get_or_create(
            slug=_WYRD_UK_SLUG,
            defaults={
                'name': 'Wyrd Games UK',
                'website': 'https://giveusyourmoneypleasethankyou-wyrd.com',
                'country': 'UK',
                'is_active': True,
                'is_uk': True,
            },
        )
        if created:
            self.stdout.write(f'Created retailer: {wyrd_uk.name} (UK)')

        seeded = 0
        skipped = 0
        for sku, label, sale_gbp, rrp_gbp, fs_path, wyrd_url in _PRICES:
            products = list(Product.objects.filter(gw_sku=sku))
            if not products:
                self.stderr.write(f'SKIP — SKU {sku} ({label}) not in DB')
                skipped += 1
                continue

            fs_url = f'{_FS_BASE}{fs_path}{_FS_AFF}'

            for product in products:
                if product.msrp_gbp != rrp_gbp:
                    product.msrp_gbp = rrp_gbp
                    product.save(update_fields=['msrp_gbp'])

                CurrentPrice.objects.update_or_create(
                    product=product,
                    retailer=firestorm,
                    defaults={
                        'price': sale_gbp,
                        'currency': 'GBP',
                        'url': fs_url,
                        'in_stock': True,
                        'not_available': False,
                    },
                )
                CurrentPrice.objects.update_or_create(
                    product=product,
                    retailer=wyrd_uk,
                    defaults={
                        'price': rrp_gbp,
                        'currency': 'GBP',
                        'url': wyrd_url,
                        'in_stock': True,
                        'not_available': False,
                    },
                )
                seeded += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded {seeded} Malifaux UK prices (Firestorm + Wyrd Games UK). Skipped: {skipped}.'
            )
        )
