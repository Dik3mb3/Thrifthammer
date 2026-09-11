"""
Management command: populate_warmachine_menoth_products

Creates the "Protectorate of Menoth" Faction (under the existing Warmachine
Category) and its 18 products, SKUs WMH-349..WMH-366 -- the first genuinely
new addition to the Warmachine product line since the original flat
348-product `populate_warmachine_products` batch, rather than a
reassignment of an existing product like the prior 7 faction splits
(Crucible Guard through Khymaera). None of the 19 rows in the user-supplied
"Menoth - Warmachine - Steamforged.xlsx" matched any existing product by
name -- confirmed via a full cross-check before writing this command.

19th row, "Protectorate of Menoth Covenant of the Flame Bundle" ($672.94),
is a discounted repackaging of the other 18 individual items already listed
separately on the same sheet -- excluded per user confirmation 2026-09-09,
same convention as Special/Limited editions and box-set bundles in prior
book/faction batches.

MSRP/images/URLs come from Steamforged Games' own store (warmachine.gg),
mirroring `populate_warmachine_products.py` exactly (same Retailer row,
same CurrentPrice-at-MSRP seeding, same ebay_search_name = name
convention). Unlike the original bulk import, faction is set directly at
creation time here since it's already known.

Slug collision check run against the full Product table before writing --
none of the 18 slugs used here already exist.

Usage:
    python manage.py populate_warmachine_menoth_products
"""

import decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

# (slug, gw_sku, name, msrp, image_url, product_url)
PRODUCTS = [
    ('protectorate-of-menoth-covenant-of-the-flame-defenders-of-the-flame', 'WMH-349', 'Warmachine: Protectorate of Menoth Covenant of the Flame – Defenders of the Flame', decimal.Decimal('79.99'), 'https://warmachine.gg/cdn/shop/files/WM-ProductImage-Menoth-DefendersOfTheFlame-Box.png?v=1787827436&width=2000', 'https://warmachine.gg/products/warmachine-protectorate-of-menoth-covenant-of-the-flame-defenders-of-the-flame'),
    ('protectorate-of-menoth-covenant-of-the-flame-scourge-of-the-unbeliever', 'WMH-350', 'Warmachine: Protectorate of Menoth Covenant of the Flame - Scourge of the Unbeliever', decimal.Decimal('169.99'), 'https://warmachine.gg/cdn/shop/files/WM-ProductImage-Menoth-ScourgeOfTheUnbeliever-Box.png?v=1787827680&width=2000', 'https://warmachine.gg/products/warmachine-protectorate-of-menoth-covenant-of-the-flame-scourge-of-the-unbeliever'),
    ('protectorate-of-menoth-covenant-of-the-flame-bastions-of-faith', 'WMH-351', 'Warmachine: Protectorate of Menoth Covenant of the Flame - Bastions of Faith', decimal.Decimal('169.99'), 'https://warmachine.gg/cdn/shop/files/WM-ProductImage-Menoth-BastionsOfFaith-Box.png?v=1787828024&width=2000', 'https://warmachine.gg/products/warmachine-protectorate-of-menoth-covenant-of-the-flame-bastions-of-faith'),
    ('protectorate-of-menoth-covenant-of-the-flame-heralds-of-perdition', 'WMH-352', 'Warmachine: Protectorate of Menoth Covenant of the Flame - Heralds of Perdition', decimal.Decimal('169.99'), 'https://warmachine.gg/cdn/shop/files/WM-ProductImage-Menoth-HeralsOfPerdition-Box_05f1abfc-d0a5-4f2f-aeee-56a86ed3b93f.png?v=1787842221&width=2000', 'https://warmachine.gg/products/warmachine-protectorate-of-menoth-covenant-of-the-flame-heralds-of-perdition'),
    ('revenger-light-warjack', 'WMH-353', 'Warmachine: Revenger Light Warjack', decimal.Decimal('37.99'), 'https://warmachine.gg/cdn/shop/files/WM-ProductImage-Menoth-Warjack-Light-Box.png?v=1787829507&width=2000', 'https://warmachine.gg/products/warmachine-revenger-light-warjack'),
    ('crusader-heavy-warjack', 'WMH-354', 'Warmachine: Crusader Heavy Warjack', decimal.Decimal('44.99'), 'https://warmachine.gg/cdn/shop/files/WM-ProductImage-Menoth-Warjack-Heavy-Box.png?v=1787829458&width=2000', 'https://warmachine.gg/products/warmachine-crusader-heavy-warjack'),
    ('protectorate-of-menoth-covenant-of-the-flame-flameguard-defenders', 'WMH-355', 'Warmachine: Protectorate of Menoth Covenant of the Flame - Flameguard Defenders', decimal.Decimal('37.99'), 'https://warmachine.gg/cdn/shop/files/WM-ProductImage-Menoth-DefendersOfTheFlame-FlameguardDefenders.png?v=1787827437&width=2000', 'https://warmachine.gg/products/warmachine-protectorate-of-menoth-covenant-of-the-flame-flameguard-defenders'),
    ('protectorate-of-menoth-covenant-of-the-flame-cleanser-sanctifiers', 'WMH-356', 'Warmachine: Protectorate of Menoth Covenant of the Flame - Cleanser Sanctifiers', decimal.Decimal('32.99'), 'https://warmachine.gg/cdn/shop/files/WM-ProductImage-Menoth-BastionsOfFaith-CleanserSanctifiers.png?v=1787828024&width=2000', 'https://warmachine.gg/products/warmachine-protectorate-of-menoth-covenant-of-the-flame-cleanser-sanctifiers'),
    ('protectorate-of-menoth-covenant-of-the-flame-cleanser-skyhammers', 'WMH-357', 'Warmachine: Protectorate of Menoth Covenant of the Flame - Cleanser Skyhammers', decimal.Decimal('37.99'), 'https://warmachine.gg/cdn/shop/files/WM-ProductImage-Menoth-BastionsOfFaith-Skyhammers.png?v=1787828024&width=2000', 'https://warmachine.gg/products/warmachine-protectorate-of-menoth-covenant-of-the-flame-cleanser-skyhammers'),
    ('protectorate-of-menoth-covenant-of-the-flame-cleanser-purifiers', 'WMH-358', 'Warmachine: Protectorate of Menoth Covenant of the Flame - Cleanser Purifiers', decimal.Decimal('37.99'), 'https://warmachine.gg/cdn/shop/files/WM-ProductImage-Menoth-ScourgeOfTheUnbeliever-CleanserPurifiers.png?v=1787827680&width=2000', 'https://warmachine.gg/products/warmachine-protectorate-of-menoth-covenant-of-the-flame-cleanser-purifiers'),
    ('protectorate-of-menoth-covenant-of-the-flame-vassals-of-menoth', 'WMH-359', 'Warmachine: Protectorate of Menoth Covenant of the Flame - Vassals of Menoth', decimal.Decimal('24.99'), 'https://warmachine.gg/cdn/shop/files/WM-ProductImage-Menoth-ScourgeOfTheUnbeliever-Vassals.png?v=1787827680&width=2000', 'https://warmachine.gg/products/warmachine-protectorate-of-menoth-covenant-of-the-flame-vassals-of-menoth'),
    ('protectorate-of-menoth-covenant-of-the-flame-cleanser-preceptor', 'WMH-360', 'Warmachine: Protectorate of Menoth Covenant of the Flame - Cleanser Preceptor', decimal.Decimal('19.99'), 'https://warmachine.gg/cdn/shop/files/WM-ProductImage-Menoth-BastionsOfFaith-CleanserPerceptor.png?v=1787828024&width=2000', 'https://warmachine.gg/products/warmachine-protectorate-of-menoth-covenant-of-the-flame-cleanser-preceptor'),
    ('protectorate-of-menoth-covenant-of-the-flame-reclaimer', 'WMH-361', 'Warmachine: Protectorate of Menoth Covenant of the Flame - Reclaimer', decimal.Decimal('19.99'), 'https://warmachine.gg/cdn/shop/files/WM-ProductImage-Menoth-ScourgeOfTheUnbeliever-Reclaimer.png?v=1787827680&width=2000', 'https://warmachine.gg/products/warmachine-protectorate-of-menoth-covenant-of-the-flame-reclaimer'),
    ('protectorate-of-menoth-covenant-of-the-flame-flameguard-defender-standard', 'WMH-362', 'Warmachine: Protectorate of Menoth Covenant of the Flame - Flameguard Defender Standard', decimal.Decimal('19.99'), 'https://warmachine.gg/cdn/shop/files/WM-ProductImage-Menoth-ScourgeOfTheUnbeliever-FlameguardDefender.png?v=1787827680&width=2000', 'https://warmachine.gg/products/warmachine-protectorate-of-menoth-covenant-of-the-flame-flameguard-defender-standard'),
    ('protectorate-of-menoth-covenant-of-the-flame-cleanser-purifier-officer', 'WMH-363', 'Warmachine: Protectorate of Menoth Covenant of the Flame - Cleanser Purifier Officer', decimal.Decimal('19.99'), 'https://warmachine.gg/cdn/shop/files/WM-ProductImage-Menoth-HeralsOfPerdition-PurifierOfficer.png?v=1787842129&width=2000', 'https://warmachine.gg/products/warmachine-protectorate-of-menoth-covenant-of-the-flame-cleanser-purifier-officer'),
    ('protectorate-of-menoth-covenant-of-the-flame-cleanser-sunburst-crew', 'WMH-364', 'Warmachine: Protectorate of Menoth Covenant of the Flame - Cleanser Sunburst Crew', decimal.Decimal('59.99'), 'https://warmachine.gg/cdn/shop/files/WM-ProductImage-Menoth-HeralsOfPerdition-SunburstCrew_fcdfb6f8-c66a-4f58-99b4-55d412ae7324.png?v=1787842221&width=2000', 'https://warmachine.gg/products/warmachine-protectorate-of-menoth-covenant-of-the-flame-cleanser-sunburst-crew'),
    ('revenger-light-warjack-options', 'WMH-365', 'Warmachine: Revenger Light Warjack Options', decimal.Decimal('19.99'), 'https://warmachine.gg/cdn/shop/files/WM-ProductImage-Menoth-Warjack-Revenger-Parts-2_98e819c5-ce0b-45e2-8a71-242afd1d9a20.png?v=1787926475&width=2000', 'https://warmachine.gg/products/warmachine-revenger-light-warjack-options'),
    ('crusader-heavy-warjack-options', 'WMH-366', 'Warmachine: Crusader Heavy Warjack Options', decimal.Decimal('19.99'), 'https://warmachine.gg/cdn/shop/files/WM-ProductImage-Menoth-Warjack-Crusader-Parts-2_78536ffb-967b-45ae-b07a-0e1c482623c0.png?v=1787926502&width=2000', 'https://warmachine.gg/products/warmachine-crusader-heavy-warjack-options'),
]


class Command(BaseCommand):
    """Create the Protectorate of Menoth faction and its 18 new products."""

    help = 'Populates Warmachine: Protectorate of Menoth (WMH-349 to WMH-366).'

    def handle(self, *args, **options):
        category = Category.objects.get(slug='warmachine')

        faction, faction_created = Faction.objects.get_or_create(
            name='Protectorate of Menoth',
            defaults={'slug': 'warmachine-protectorate-of-menoth', 'category': category},
        )
        if faction_created:
            self.stdout.write(self.style.SUCCESS('Created faction: Protectorate of Menoth'))
        else:
            self.stdout.write(f'Found faction: Protectorate of Menoth (pk={faction.pk})')

        steamforged = Retailer.objects.get(slug='steamforged-games')

        products_created = 0
        products_updated = 0
        prices_created = 0
        prices_updated = 0

        for slug, gw_sku, name, msrp, image_url, product_url in PRODUCTS:
            product, created = Product.objects.update_or_create(
                slug=slug,
                defaults={
                    'gw_sku': gw_sku,
                    'name': name,
                    'category': category,
                    'faction': faction,
                    'msrp': msrp,
                    'image_url': image_url,
                    'gw_url': product_url,
                    'ebay_search_name': name,
                    'batch_tag': 'warmachine-protectorate-of-menoth',
                    'is_active': True,
                },
            )
            if created:
                products_created += 1
            else:
                products_updated += 1

            _, price_created = CurrentPrice.objects.update_or_create(
                product=product,
                retailer=steamforged,
                defaults={
                    'price': msrp,
                    'url': product_url,
                    'in_stock': True,
                    'not_available': False,
                },
            )
            if price_created:
                prices_created += 1
            else:
                prices_updated += 1

            self.stdout.write(f"  {'Created' if created else 'Updated'}: {name} ({gw_sku})")

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. Products: {products_created} created, {products_updated} updated. '
            f'Steamforged Games prices: {prices_created} created, {prices_updated} updated.'
        ))
