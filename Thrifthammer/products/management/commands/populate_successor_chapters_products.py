"""
Management command: populate_successor_chapters_products

Creates five brand-new Space Marine successor chapter factions and seeds their
faction-specific characters. Each faction is created with parent_faction=Space Marines
so they inherit generic SM products via the parent FK.

  Iron Hands    — 2 products: Iron Father Feirros, Caanok Var
  Salamanders   — 2 products: Adrax Agatone, Vulkan He'stan
  Imperial Fists — 2 products: Tor Garadon, Darnath Lysander
  White Scars   — 2 products: Kor'sarro Khan, Suboden Khan
  Raven Guard   — 2 products: Kayvaan Shrike, Aethon Shaan

All products are tagged batch_tag='phase-2'. GW CurrentPrice seeded at MSRP.
Idempotent (update_or_create keyed on slug/faction name).

Sourced from GW en-US all-SM scrape — 2026-04-04.

Usage:
    python manage.py populate_successor_chapters_products
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

_IMG = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{filename}'

# (faction_name, slug, name, msrp, img_filename, gw_url)
PRODUCTS = [
    # ── Iron Hands ────────────────────────────────────────────────────────────
    (
        'Iron Hands',
        'iron-hands-iron-father-feirros',
        'Iron Father Feirros',
        47.00,
        '99120101257_SMIHFeirros01.jpg',
        'https://www.warhammer.com/en-US/shop/Iron-Hands-Feirros-2020',
    ),
    (
        'Iron Hands',
        'iron-hands-caanok-var',
        'Caanok Var',
        47.00,
        '99120101447_SpaceMarinesIronHandsCaanokVar01.jpg',
        'https://www.warhammer.com/en-US/shop/iron-hands-caanok-var-2025',
    ),
    # ── Salamanders ───────────────────────────────────────────────────────────
    (
        'Salamanders',
        'salamanders-adrax-agatone',
        'Adrax Agatone',
        47.00,
        '99120101259_SALAdraxAgatone01.jpg',
        'https://www.warhammer.com/en-US/shop/Salamanders-Adrax-Agatone-2020',
    ),
    (
        'Salamanders',
        'salamanders-vulkan-hestan',
        "Vulkan He'stan",
        47.00,
        '99120101444_SpaceMarinesSalamandersVulkanHestan1.jpg',
        'https://www.warhammer.com/en-US/shop/salamanders-vulkan-hestan-2025',
    ),
    # ── Imperial Fists ────────────────────────────────────────────────────────
    (
        'Imperial Fists',
        'imperial-fists-tor-garadon',
        'Tor Garadon',
        47.00,
        '99120101258_SMIFTorGaradon01.jpg',
        'https://www.warhammer.com/en-US/shop/Imperial-Fists-Tor-Garadon-2020',
    ),
    (
        'Imperial Fists',
        'imperial-fists-darnath-lysander',
        'Darnath Lysander',
        47.00,
        '99120101446_SpaceMarinesImperialFistsDarnathLysander1.jpg',
        'https://www.warhammer.com/en-US/shop/imperial-fists-darnath-lysander-2025',
    ),
    # ── White Scars ───────────────────────────────────────────────────────────
    (
        'White Scars',
        'white-scars-korsarro-khan',
        "Kor'sarro Khan",
        47.00,
        '99120101255_WSKorsarroKhan01.jpg',
        'https://www.warhammer.com/en-US/shop/White-Scars-KorSarro-Khan-2020',
    ),
    (
        'White Scars',
        'white-scars-suboden-khan',
        'Suboden Khan',
        65.00,
        '99120101448_SPACEMARINESWhiteScarsSubodenKhan01.jpg',
        'https://www.warhammer.com/en-US/shop/white-scars-suboden-khan-2025',
    ),
    # ── Raven Guard ───────────────────────────────────────────────────────────
    (
        'Raven Guard',
        'raven-guard-kayvaan-shrike',
        'Kayvaan Shrike',
        47.00,
        '99120101256_SMRGKayvaanShrike01.jpg',
        'https://www.warhammer.com/en-US/shop/Raven-Guard-Kayvaan-Shrike-2020',
    ),
    (
        'Raven Guard',
        'raven-guard-aethon-shaan',
        'Aethon Shaan',
        47.00,
        '99120101445_RavenGuardAethonShaan01.jpg',
        'https://www.warhammer.com/en-US/shop/raven-guard-aethon-shaan-2025',
    ),
]

# New factions to create — (name, slug)
NEW_FACTIONS = [
    ('Iron Hands', 'iron-hands'),
    ('Salamanders', 'salamanders'),
    ('Imperial Fists', 'imperial-fists'),
    ('White Scars', 'white-scars'),
    ('Raven Guard', 'raven-guard'),
]


class Command(BaseCommand):
    """Create Iron Hands, Salamanders, Imperial Fists, White Scars, Raven Guard + their products."""

    help = (
        'Creates 5 successor chapter factions (Iron Hands, Salamanders, Imperial Fists, '
        'White Scars, Raven Guard) as children of Space Marines, then seeds 10 faction-specific '
        'character models. Tagged phase-2. Seeds GW CurrentPrice. Idempotent.'
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

        gw_retailer = Retailer.objects.filter(name='Games Workshop').first()
        if not gw_retailer:
            self.stdout.write(self.style.WARNING(
                'Games Workshop retailer not found — GW prices will not be seeded.'
            ))

        # ── Create/update factions ────────────────────────────────────────────
        self.stdout.write(self.style.MIGRATE_HEADING('\n  ── Factions ──'))
        faction_cache = {}
        for faction_name, faction_slug in NEW_FACTIONS:
            faction, created = Faction.objects.update_or_create(
                name=faction_name,
                defaults={
                    'slug': faction_slug,
                    'parent_faction': sm_faction,
                },
            )
            status = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(
                f'    {status} faction: {faction_name} (parent: Space Marines)'
            ))
            faction_cache[faction_name] = faction

        # ── Create/update products ─────────────────────────────────────────────
        total_created = 0
        total_updated = 0
        total_price_created = 0
        total_price_updated = 0

        current_faction_name = None
        for (faction_name, slug, name, msrp, img_filename, gw_url) in PRODUCTS:
            if faction_name != current_faction_name:
                self.stdout.write(self.style.MIGRATE_HEADING(f'\n  ── {faction_name} ──'))
                current_faction_name = faction_name

            faction = faction_cache[faction_name]
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
                    'faction': faction,
                    'is_active': True,
                    'batch_tag': 'phase-2',
                },
            )
            status = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'    {status}: {name} — ${msrp:.2f}'))
            if created:
                total_created += 1
            else:
                total_updated += 1

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
                    total_price_created += 1
                else:
                    total_price_updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'\npopulate_successor_chapters_products complete.\n'
            f'  Products: {total_created} created, {total_updated} updated.\n'
            f'  GW prices: {total_price_created} created, {total_price_updated} updated.'
        ))
