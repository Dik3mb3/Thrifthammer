"""
Seed Games Workshop UK prices for Slaves to Darkness.

Creates the `games-workshop-uk` Retailer if it does not exist, sets
msrp_gbp on each matched Product, and creates/updates a CurrentPrice
record pointing at the GW UK product page.

Run once on Railway startup via Procfile.  Safe to re-run — idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_GW_UK_SLUG = 'games-workshop-uk'

# (gw_sku, label, gbp_price, gw_uk_url)
_PRICES = [
    ('70-04', 'Spearhead: Slaves to Darkness', Decimal('91.00'),
     'https://www.warhammer.com/en-GB/shop/spearhead-slaves-to-darkness-2024'),
    ('83-14', 'Slaves to Darkness Varanguard', Decimal('65.00'),
     'https://www.warhammer.com/en-GB/shop/Varanguard-Knights-of-Ruin'),
    ('83-18', 'Slaves to Darkness Chaos Warriors', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/slaves-to-darkness-chaos-warriors-2023'),
    ('S2D-002', 'Warcry: Centaurion Marshal', Decimal('27.00'),
     'https://www.warhammer.com/en-GB/shop/slaves-to-darkness-centaurion-marshal-2025'),
    ('S2D-003', 'Chaos Lord on Daemonic Mount', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/slaves-to-darkness-chaos-lord-on-daemonic-mount-2023'),
    ('S2D-004', 'Exalted Hero of Chaos', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/slaves-to-darkness-exalted-hero-of-chaos-2023'),
    ('S2D-005', 'Eternus, Blade of The First Prince', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/slaves-to-darkness-eternus-blade-of-the-first-prince-2023'),
    ('S2D-006', 'Chaos Lord on Karkadrak', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/slaves-to-darkness-lord-on-karkadrak-2023'),
    ('S2D-007', 'Ogroid Myrmidon', Decimal('29.50'),
     'https://www.warhammer.com/en-GB/shop/ogroid-myrmidon-champion-2022'),
    ('S2D-008', 'Darkoath Warqueen', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/Darkoath-Warqueen-Marakarr-Blood-Sky-2018'),
    ('S2D-009', 'Gaunt Summoner', Decimal('20.50'),
     'https://www.warhammer.com/en-GB/shop/Gaunt-Summoner'),
    ('S2D-010', 'Darkoath Chieftain', Decimal('20.50'),
     'https://www.warhammer.com/en-GB/shop/darkoath-chieftain'),
    ('S2D-011', 'Archaon Everchosen', Decimal('118.00'),
     'https://www.warhammer.com/en-GB/shop/Archaon-Exalted'),
    ('S2D-012', 'Chaos Lord', Decimal('19.00'),
     'https://www.warhammer.com/en-GB/shop/Chaos-Lord'),
    ('S2D-013', 'Centaurion Marshal', Decimal('27.00'),
     'https://www.warhammer.com/en-GB/shop/slaves-to-darkness-centaurion-marshal-2025'),
    ('S2D-014', 'Chaos Sorcerer Lord', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/slaves-to-darkness-chaos-sorcerer-lord-2024'),
    ('S2D-015', 'Abraxia, Spear of the Everchosen', Decimal('69.50'),
     'https://www.warhammer.com/en-GB/shop/slaves-to-darkness-abraxia-spear-of-the-everchosen-2024'),
    ('S2D-016', 'Brand\'s Oathbound', Decimal('49.50'),
     'https://www.warhammer.com/en-GB/shop/darkoath-brands-oathbound-2024'),
    ('S2D-018', 'Ogroid Theridons', Decimal('42.50'),
     'https://www.warhammer.com/en-GB/shop/slaves-to-darkness-ogroid-theridons-2023'),
    ('S2D-019', 'Chaos Knights', Decimal('42.50'),
     'https://www.warhammer.com/en-GB/shop/slaves-to-darkness-chaos-knights-2023'),
    ('S2D-020', 'Mindstealer Sphiranx', Decimal('29.50'),
     'https://www.warhammer.com/en-GB/shop/mindstealer-sphiranx-2022'),
    ('S2D-021', 'Fomoroid Crusher', Decimal('29.50'),
     'https://www.warhammer.com/en-GB/shop/fomoroid-crusher-2022'),
    ('S2D-022', 'Chaotic Beasts', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/chaotic-beasts-2022'),
    ('S2D-023', 'Gorebeast Chariot', Decimal('29.50'),
     'https://www.warhammer.com/en-GB/shop/Gorebeast-Chariot-2019'),
    ('S2D-024', 'Endless Spells: Slaves to Darkness', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Endless-Spells-Slaves-To-Darkness-2019'),
    ('S2D-025', 'Chaos Chariot', Decimal('29.50'),
     'https://www.warhammer.com/en-GB/shop/Chaos-Chariot-2016'),
    ('S2D-027', 'Slaughterbrute', Decimal('58.00'),
     'https://www.warhammer.com/en-GB/shop/slaughterbrute-2025'),
    ('S2D-028', 'Nexus Chaotica', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/slaves-to-darkness-nexus-chaotica-2024'),
    ('S2D-029', 'Darkoath Fellriders', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/slaves-to-darkness-darkoath-fellriders-2024'),
    ('S2D-030', 'Darkoath Marauders', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/slaves-to-darkness-darkoath-marauders-2024'),
    ('S2D-031', 'Chaos Battletome: Slaves to Darkness', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/battletome-slaves-to-darkness-2024-eng'),
    ('S2D-032', 'Darkoath Chieftain on Warsteed', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/slaves-to-darkness-darkoath-chieftain-on-warsteed-2024'),
    ('S2D-033', 'Chaos Chosen', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/slaves-to-darkness-chaos-chosen-2023'),
    ('S2D-034', 'Chaos Legionnaires', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/slaves-to-darkness-chaos-legionaires-2025'),
    ('S2D-035', 'Darkoath Wilderfiend', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/slaves-to-darkness-darkoath-wilderfiend-2024'),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Slaves to Darkness. Idempotent.'

    def handle(self, *args, **options):
        retailer, created = Retailer.objects.get_or_create(
            slug=_GW_UK_SLUG,
            defaults={
                'name': 'Games Workshop UK',
                'website': 'https://www.warhammer.com/en-GB/',
                'country': 'UK',
                'is_active': True,
                'is_uk': True,
            },
        )
        if created:
            self.stdout.write(f'Created retailer: {retailer.name}')

        seeded = 0
        skipped = 0
        for gw_sku, label, gbp_price, url in _PRICES:
            try:
                product = Product.objects.get(gw_sku=gw_sku)
            except Product.DoesNotExist:
                self.stderr.write(f'SKIP — SKU {gw_sku} ({label}) not in DB')
                skipped += 1
                continue

            if product.msrp_gbp != gbp_price:
                product.msrp_gbp = gbp_price
                product.save(update_fields=['msrp_gbp'])

            CurrentPrice.objects.update_or_create(
                product=product,
                retailer=retailer,
                defaults={
                    'price': gbp_price,
                    'url': url,
                    'in_stock': True,
                    'not_available': False,
                },
            )
            seeded += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded {seeded} Slaves to Darkness GW UK prices. Skipped: {skipped}.'
            )
        )
