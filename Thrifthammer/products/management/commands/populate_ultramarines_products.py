"""
Management command: populate_ultramarines_products

Creates the Ultramarines faction and seeds Ultramarines-specific products
with GW CurrentPrice at MSRP. Sets parent_faction to Space Marines so
Ultramarines inherit generic SM products on their faction page and Army
Calculator.

Ultramarines-SPECIFIC products (tagged faction=Ultramarines):
  - Captain Titus and The Wardens of Ultramar
  - Roboute Guilliman
  - Marneus Calgar in Armour of Antilochus
  - Chief Librarian Tigurius
  - Cato Sicarius
  - Victrix Honour Guard  (if already exists as ultramarines-honour-guard, updates it)
  - Ultramarines Upgrades and Transfers

Generic SM products are seeded separately via populate_sm_phase2_products
and tagged to the Space Marines faction — Ultramarines inherits them via
parent_faction.

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_ultramarines_products
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

_IMG = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{filename}'

# (slug, name, msrp, image_filename, gw_url)
PRODUCTS = [
    (
        'ultramarines-captain-titus-wardens',
        'Captain Titus and The Wardens of Ultramar',
        94.00,
        '99120101459_SpaceMarinesTitusWardens1.jpg',
        'https://www.warhammer.com/en-US/shop/captain-titus-and-the-wardens-of-ultramar-2026',
    ),
    (
        'ultramarines-roboute-guilliman',
        'Roboute Guilliman',
        73.50,
        '99120101177_TriumvirateofthePrimarch02.jpg',
        'https://www.warhammer.com/en-US/shop/Roboute-Guilliman-Ultramarines-Primarch-2020',
    ),
    (
        'ultramarines-marneus-calgar',
        'Marneus Calgar in Armour of Antilochus',
        55.50,
        '99120101450_UltramarinesMarneusCalgarArmourAntilochus1.jpg',
        'https://www.warhammer.com/en-US/shop/marneus-calgar-in-armour-of-antilochus-2025',
    ),
    (
        'ultramarines-chief-librarian-tigurius',
        'Chief Librarian Tigurius',
        48.00,
        '99120101254_UMChiefLibrarian01.jpg',
        'https://www.warhammer.com/en-US/shop/Ultramarines-Chief-Librarian-Tigurius-2020',
    ),
    (
        'ultramarines-cato-sicarius',
        'Cato Sicarius',
        48.00,
        '99120101452_UltramarinesCatoSicarius1.jpg',
        'https://www.warhammer.com/en-US/shop/ultramarines-cato-sicarius-2025',
    ),
    (
        'ultramarines-honour-guard',
        'Victrix Honour Guard',
        65.00,
        '99120101453_UltramarinesVictrixHonourGuard1.jpg',
        'https://www.warhammer.com/en-US/shop/ultramarines-victrix-honour-guard-2025',
    ),
    (
        'ultramarines-upgrades-and-transfers',
        'Ultramarines Upgrades and Transfers',
        35.00,
        '99120101451_SpaceMarineUltramarinesUpgradesTransfers1.jpg',
        'https://www.warhammer.com/en-US/shop/ultramarines-upgrades-and-transfers-2025',
    ),
]


class Command(BaseCommand):
    """Create Ultramarines faction and seed UM-specific products with GW prices."""

    help = (
        'Creates Ultramarines faction (parent=Space Marines) and seeds 7 UM-specific '
        'products with GW CurrentPrice at MSRP. Sourced from GW en-US scrape 2026-04-03. '
        'Generic SM products are handled by populate_sm_phase2_products. Idempotent.'
    )

    def handle(self, *args, **options):
        """Run the command."""
        category_40k = Category.objects.filter(name='Warhammer 40,000').first()
        if not category_40k:
            self.stderr.write(self.style.ERROR(
                'Warhammer 40,000 category not found — run populate_products first.'
            ))
            return

        sm_faction = Faction.objects.filter(name='Space Marines').first()
        if not sm_faction:
            self.stderr.write(self.style.ERROR(
                'Space Marines faction not found — run populate_products first.'
            ))
            return

        # ── Create / update Ultramarines faction ──────────────────────────────
        um_faction, um_created = Faction.objects.get_or_create(
            name='Ultramarines',
            defaults={
                'slug': 'ultramarines',
                'category': category_40k,
                'display_name': 'Ultramarines',
                'hero_tagline': 'The XIII Legion: Courage and Honour',
                'synopsis': (
                    'The Ultramarines are the poster-chapter of Warhammer 40,000 — '
                    'disciplined, tactically versatile, and led by the returned Primarch '
                    'Roboute Guilliman. As authors of the Codex Astartes, the Ultramarines '
                    'exemplify balanced Space Marine warfare: strong infantry, flexible '
                    'vehicles, and elite characters. Their blue-and-gold heraldry is '
                    'iconic across the hobby. On the battlefield they reward players who '
                    'follow the Codex doctrine: layered gunlines, strong objective play, '
                    'and well-coordinated combined arms. A fantastic choice for beginners '
                    'and veterans alike, with one of the largest model ranges in the game.'
                ),
                'difficulty': 'Beginner',
                'model_count_rating': 'Medium (30-60 models)',
                'painting_complexity': 'Easy-Medium',
                'playstyle': 'Balanced Combined Arms',
                'price_range_display': '$$$',
                'parent_faction': sm_faction,
            },
        )
        if um_created:
            self.stdout.write(self.style.SUCCESS('Created faction: Ultramarines'))
        else:
            if um_faction.parent_faction != sm_faction:
                um_faction.parent_faction = sm_faction
                um_faction.save()
            self.stdout.write(f'Found faction: Ultramarines (pk={um_faction.pk})')

        gw_retailer = Retailer.objects.filter(name='Games Workshop').first()
        if not gw_retailer:
            self.stdout.write(self.style.WARNING(
                'Games Workshop retailer not found — GW prices will not be seeded.'
            ))

        created_count = 0
        updated_count = 0
        price_created = 0
        price_updated = 0

        for (slug, name, msrp, img_filename, gw_url) in PRODUCTS:
            image_url = _IMG.format(filename=img_filename)

            product, created = Product.objects.update_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'gw_sku': '',
                    'msrp': msrp,
                    'image_url': image_url,
                    'gw_url': gw_url,
                    'category': category_40k,
                    'faction': um_faction,
                    'is_active': True,
                    'batch_tag': 'phase-2',
                },
            )
            status = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'  {status}: {name} — ${msrp:.2f}'))
            if created:
                created_count += 1
            else:
                updated_count += 1

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
                    price_created += 1
                else:
                    price_updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'\npopulate_ultramarines_products complete.\n'
            f'  Products: {created_count} created, {updated_count} updated.\n'
            f'  GW prices: {price_created} created, {price_updated} updated.'
        ))
