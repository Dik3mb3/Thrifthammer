"""
Management command: populate_armageddon_splits_products

Adds the Warhammer 40K: Armageddon 11th Edition box split SKUs to the
Discount Box Splits category. Seeds GW CurrentPrice at MSRP.

Category: Discount Box Splits (created if absent)
Faction:  Warhammer 40K: Armageddon 11th Edition (created if absent)
Prefix:   AGA-001 – AGA-024
batch_tag: armageddon-splits

No NK or MM seed commands exist for this faction (GW + eBay only).
Idempotent — safe to re-run (update_or_create keyed on slug).

Usage:
    python manage.py populate_armageddon_splits_products
"""

import decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

_IMG = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{filename}'

# (slug, gw_sku, name, msrp, img_filename, gw_url, ebay_search_name, ebay_negative_keywords, description)
#
# gw_url notes:
#   AGA-001: GW URL column contained an image URL — set blank (no buy button).
#   AGA-003: GW URL column was a ThriftHammer URL — set blank (no buy button).
#   AGA-006/007/008/009-013/015-023/024/025: no GW URL available — set blank.
#   AGA-014/015: ?queryID= param stripped from GW URLs.
#
# ebay_negative_keywords notes:
#   AGA-010/011/012: Bannernob, Big Boss, and Painboy share a sprue.
#     Each excludes the other two by name so eBay results target the right model.
#   AGA-022/023: Box half SKUs exclude the opposing faction name.
#
# description: stores the footnote text shown below the retailer price table.
PRODUCTS = [
    # ── Space Marines ──────────────────────────────────────────────────────────
    (
        'armageddon-captain-with-relic-shield',
        'AGA-001',
        'Captain with Relic Shield',
        decimal.Decimal('43.50'),
        '60010199080_ArmageddonCoreGame04.jpg',
        '',
        'Armageddon Captain with Relic Shield Warhammer 40K',
        '',
        '',
    ),
    (
        'armageddon-librarian',
        'AGA-002',
        'Librarian',
        decimal.Decimal('42.00'),
        '60010199080_ArmageddonCoreGame06.jpg',
        'https://www.warhammer.com/en-US/shop/Space-Marines-Primaris-Librarian-2020',
        'Armageddon Librarian Warhammer 40K',
        '',
        '',
    ),
    (
        'armageddon-chaplain-with-jump-pack',
        'AGA-003',
        'Chaplain with Jump Pack',
        decimal.Decimal('42.00'),
        '60010199080_ArmageddonCoreGame05.jpg',
        '',
        'Armageddon Chaplain with Jump Pack Warhammer 40K',
        '',
        '',
    ),
    (
        'armageddon-ancient',
        'AGA-004',
        'Ancient',
        decimal.Decimal('43.50'),
        '60010199080_ArmageddonCoreGame07.jpg',
        'https://www.warhammer.com/en-US/shop/space-marines-primaris-ancient-2022',
        'Armageddon Ancient Warhammer 40K',
        '',
        '',
    ),
    (
        'armageddon-intercessors',
        'AGA-005',
        'Intercessors',
        decimal.Decimal('65.00'),
        '60010199080_ArmageddonCoreGame08.jpg',
        'https://www.warhammer.com/en-US/shop/Space-Marines-Primaris-Intercessors-2020',
        'Armageddon Intercessors Warhammer 40K',
        '',
        '',
    ),
    (
        'armageddon-vanguard-veterans-with-jump-packs',
        'AGA-006',
        'Vanguard Veterans with Jump Packs',
        decimal.Decimal('65.00'),
        '60010199080_ArmageddonCoreGame09.jpg',
        '',
        'Armageddon Vanguard Veterans with Jump Packs Warhammer 40K',
        '',
        '*Estimate based on previous vanguard veteran kit',
    ),
    (
        'armageddon-eradicators-with-heavy-bolters',
        'AGA-007',
        'Eradicators with Heavy Bolters',
        decimal.Decimal('60.00'),
        '60010199080_ArmageddonCoreGame10.jpg',
        'https://www.warhammer.com/en-US/shop/Space-Marines-Primaris-Eradicators-2020',
        'Armageddon Eradicators with Heavy Bolters Warhammer 40K',
        '',
        '',
    ),
    (
        'armageddon-land-speeder',
        'AGA-008',
        'Land Speeder',
        decimal.Decimal('82.00'),
        '60010199080_ArmageddonCoreGame11.jpg',
        '',
        'Armageddon Land Speeder Warhammer 40K',
        '',
        '*Estimate based on similar SKUs',
    ),
    # ── Orks ───────────────────────────────────────────────────────────────────
    (
        'armageddon-warboss',
        'AGA-009',
        'Warboss',
        decimal.Decimal('43.50'),
        '60010199080_ArmageddonCoreGame12.jpg',
        'https://www.warhammer.com/en-US/shop/ork-warboss-in-mega-armour-2022',
        'Armageddon Warboss Warhammer 40K',
        '',
        '',
    ),
    (
        'armageddon-bannernob',
        'AGA-010',
        'Bannernob',
        decimal.Decimal('43.50'),
        '60010199080_ArmageddonCoreGame14.jpg',
        '',
        'Armageddon Bannernob Warhammer 40K',
        "Painboy 'Big Boss'",
        '*Estimate based on similar SKUs',
    ),
    (
        'armageddon-big-boss',
        'AGA-011',
        'Big Boss',
        decimal.Decimal('43.50'),
        '60010199080_ArmageddonCoreGame13.jpg',
        '',
        'Armageddon Big Boss Warhammer 40K',
        'Painboy Bannernob',
        '*Estimate based on similar SKUs',
    ),
    (
        'armageddon-painboy',
        'AGA-012',
        'Painboy',
        decimal.Decimal('43.50'),
        '60010199080_ArmageddonCoreGame15.jpg',
        '',
        'Armageddon Painboy Warhammer 40K',
        "Bannernob 'Big Boss'",
        '*Estimate based on similar SKUs',
    ),
    (
        'armageddon-weirdboy',
        'AGA-013',
        'Weirdboy',
        decimal.Decimal('43.50'),
        '60010199080_ArmageddonCoreGame16.jpg',
        '',
        'Armageddon Weirdboy Warhammer 40K',
        '',
        '*Estimate based on similar SKUs',
    ),
    (
        'armageddon-ork-boyz',
        'AGA-014',
        'Ork Boyz',
        decimal.Decimal('48.00'),
        '60010199080_ArmageddonCoreGame17.jpg',
        'https://www.warhammer.com/en-US/shop/Ork-Boyz-2018',
        'Armageddon Ork Boyz Warhammer 40K',
        '',
        '',
    ),
    (
        'armageddon-gretchin',
        'AGA-015',
        'Gretchin',
        decimal.Decimal('27.00'),
        '60010199080_ArmageddonCoreGame18.jpg',
        'https://www.warhammer.com/en-US/shop/Ork-Gretchin-2018',
        'Armageddon Gretchin Warhammer 40K',
        '',
        '',
    ),
    (
        'armageddon-wartrakk',
        'AGA-016',
        'Wartrakk',
        decimal.Decimal('60.00'),
        '60010199080_ArmageddonCoreGame19.jpg',
        '',
        'Armageddon Wartrakk Warhammer 40K',
        '',
        '*Estimate based on similar SKUs',
    ),
    (
        'armageddon-big-mek-dakkarig',
        'AGA-017',
        'Big Mek Dakkarig',
        decimal.Decimal('65.00'),
        '60010199080_ArmageddonCoreGame20.jpg',
        '',
        'Armageddon Big Mek Dakkarig Warhammer 40K',
        '',
        '*Estimate based on similar SKUs',
    ),
    # ── Books & Decks ──────────────────────────────────────────────────────────
    (
        'armageddon-operation-imperator-book',
        'AGA-018',
        'Armageddon Operation Imperator Book',
        decimal.Decimal('20.00'),
        '60010199080_engArmageddon01.jpg',
        '',
        'Armageddon Operation Imperator Book',
        '',
        '*Estimate based off paperback Warhammer novels',
    ),
    (
        'armageddon-warhammer-40k-11th-edition-core-rulebook',
        'AGA-019',
        'Warhammer 40K 11th Edition Core Rulebook',
        decimal.Decimal('69.00'),
        '60010199080_engArmageddon01.jpg',
        '',
        'Armageddon Warhammer 40K Core Rulebook',
        '',
        '*Estimate based on 10th Edition Rule Book',
    ),
    (
        'armageddon-chapter-approved-2026-2027-mission-deck',
        'AGA-020',
        'Chapter Approved 2026-2027: Mission Deck',
        decimal.Decimal('35.00'),
        '60010199080_engArmageddon01.jpg',
        '',
        'Armageddon Chapter Approved 2026-2027: Mission Deck Warhammer 40K',
        '',
        '',
    ),
    (
        'armageddon-dominatus-narrative-campaign-deck',
        'AGA-021',
        'Dominatus Narrative Campaign Deck',
        decimal.Decimal('35.00'),
        '60010199080_engArmageddon01.jpg',
        '',
        'Armageddon Dominatus Narrative Campaign Deck Warhammer 40K',
        '',
        '*Estimate based on Mission Deck',
    ),
    # ── Combo / Half-box SKUs ─────────────────────────────────────────────────
    (
        'armageddon-box-ork-half',
        'AGA-022',
        'Armageddon Box Ork Half',
        decimal.Decimal('147.50'),
        '60010199080_engArmageddon01.jpg',
        '',
        'Armageddon Box Ork Half Warhammer 40K',
        "'Space Marine'",
        '*Estimates based on 50% of box MSRP',
    ),
    (
        'armageddon-box-space-marine-half',
        'AGA-023',
        'Armageddon Box Space Marine Half',
        decimal.Decimal('147.50'),
        '60010199080_engArmageddon01.jpg',
        '',
        'Armageddon Box Space Marine Half Warhammer 40K',
        'Ork',
        '*Estimates based on 50% of box MSRP',
    ),
    (
        'armageddon-big-boss-painboy-bannernob',
        'AGA-024',
        'Big Boss + Painboy + Bannernob',
        decimal.Decimal('130.50'),
        '60010199080_engArmageddon01.jpg',
        '',
        'Armageddon Big Boss Painboy Bannernob Warhammer 40K',
        '',
        '*Estimate based on similar SKUs',
    ),
]


class Command(BaseCommand):
    """Seed Warhammer 40K: Armageddon 11th Edition box split products and GW prices."""

    help = 'populate_armageddon_splits_products — adds AGA-001–AGA-024 to Discount Box Splits'

    def handle(self, *args, **options):
        """Run the command."""
        category, cat_created = Category.objects.get_or_create(
            slug='discount-box-splits',
            defaults={'name': 'Discount Box Splits', 'sort_order': 60},
        )
        if cat_created:
            self.stdout.write(self.style.SUCCESS('Created category: Discount Box Splits'))

        faction, fac_created = Faction.objects.get_or_create(
            slug='warhammer-40k-armageddon-11th-edition',
            defaults={
                'name': 'Warhammer 40K: Armageddon 11th Edition',
                'category': category,
            },
        )
        if fac_created:
            self.stdout.write(self.style.SUCCESS(
                'Created faction: Warhammer 40K: Armageddon 11th Edition'
            ))

        gw_retailer = Retailer.objects.filter(name='Games Workshop').first()
        if not gw_retailer:
            self.stdout.write(self.style.WARNING(
                'Games Workshop retailer not found — GW prices will not be seeded.'
            ))

        products_created = products_updated = prices_created = prices_updated = 0

        for (
            slug, gw_sku, name, msrp,
            img_filename, gw_url,
            ebay_search_name, ebay_negative_keywords,
            description,
        ) in PRODUCTS:
            image_url = _IMG.format(filename=img_filename)

            product, created = Product.objects.update_or_create(
                slug=slug,
                defaults={
                    'gw_sku': gw_sku,
                    'name': name,
                    'msrp': msrp,
                    'image_url': image_url,
                    'gw_url': gw_url,
                    'category': category,
                    'faction': faction,
                    'is_active': True,
                    'batch_tag': 'armageddon-splits',
                    'ebay_search_name': ebay_search_name,
                    'ebay_negative_keywords': ebay_negative_keywords,
                    'description': description,
                },
            )
            status = 'Created' if created else 'Updated'
            self.stdout.write(f'  {status}: {name} ({gw_sku}) — ${msrp}')
            if created:
                products_created += 1
            else:
                products_updated += 1

            if gw_retailer:
                _, p_created = CurrentPrice.objects.update_or_create(
                    product=product,
                    retailer=gw_retailer,
                    defaults={
                        'price': msrp,
                        'url': gw_url,
                        'in_stock': True,
                        'not_available': False,
                        'listing_title': name,
                    },
                )
                if p_created:
                    prices_created += 1
                else:
                    prices_updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'\npopulate_armageddon_splits_products complete.\n'
            f'  Products: {products_created} created, {products_updated} updated.\n'
            f'  GW prices: {prices_created} created, {prices_updated} updated.'
        ))
