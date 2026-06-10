"""
Management command: populate_sylvaneth_products

Creates / updates all Sylvaneth product entries for ThriftHammer,
seeds GW CurrentPrice records at MSRP.

Covers 25 products (SYL-001 to SYL-025).
Source: AOS Sylvaneth - GW, NK, MM.xlsx (2026-06-03)

Category: Age of Sigmar
Faction:  Sylvaneth  (created by this command if not yet in DB)

Shared-listing products (same physical kit, multiple build options):
  SYL-016 / SYL-017          — Revenant Seekers / Spiterider Lancers
                                (share NK + MM listing)
  SYL-022 / SYL-023 / SYL-024 — Spirit of Durthu / Treelord Ancient / Treelord
                                  (share NK listing)

No NK listing (3 products):
  SYL-012  Dryads
  SYL-013  Branchwych
  SYL-019  Spite-Revenants

No MM listing (10 products):
  SYL-001, SYL-005, SYL-009, SYL-012, SYL-013,
  SYL-019, SYL-020, SYL-022, SYL-023, SYL-024

Images are baked in as one-off GW CDN URLs -- never auto-refreshed.

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_sylvaneth_products
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

_IMG = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{filename}'

# ── Product definitions ───────────────────────────────────────────────────────
# (slug, gw_sku, name, msrp, image_filename, gw_url, ebay_search_name)
#
# msrp is USD price from GW en-US storefront as of 2026-06-03.
# ebay_search_name set per Excel 'Ebay Search Name' column.
PRODUCTS = [

    # ── Battleforce / Spearhead ───────────────────────────────────────────────
    (
        'battleforce-sylvaneth-strongroot-grove',
        'SYL-001',
        'Battleforce: Sylvaneth – Strongroot Grove',
        250.00,
        '99120204056_StrongrootGrove1a.jpg',
        'https://www.warhammer.com/en-US/shop/sylvaneth-strongroot-grove-2026',
        'Battleforce: Sylvaneth – Strongroot Grove Warhammer',
    ),
    (
        'spearhead-sylvaneth-spitewing-flight',
        'SYL-002',
        'Spearhead: Sylvaneth – Spitewing Flight',
        150.00,
        '99120204049_SpitewingFlightSpearhead1.jpg',
        'https://www.warhammer.com/en-US/shop/spearhead-spitewing-flight-2026',
        'Spearhead: Sylvaneth – Spitewing Flight Warhammer',
    ),

    # ── Regiments of Renown / Warcry ─────────────────────────────────────────
    (
        'the-twisted-branch',
        'SYL-003',
        'The Twisted Branch',
        77.00,
        '99120204050_TwistedBranch1.jpg',
        'https://www.warhammer.com/en-US/shop/sylvaneth-the-twisted-branch-2026',
        'Regiment of Renown: The Twisted Branch Warhammer',
    ),
    (
        'twistweald',
        'SYL-004',
        'Twistweald',
        65.00,
        '60120299006_ENGWCBriarBone2.jpg',
        'https://www.warhammer.com/en-US/shop/warcry-twistweald-2024',
        'Twistweald Warhammer',
    ),

    # ── Heroes ────────────────────────────────────────────────────────────────
    (
        'the-lady-of-vines',
        'SYL-005',
        'The Lady of Vines',
        60.00,
        '99120204034_SYLLadyofVinesLead.jpg',
        'https://www.warhammer.com/en-US/shop/sylvaneth-lady-of-vines-2022',
        'The Lady of Vines Warhammer',
    ),
    (
        'gossamid-archers',
        'SYL-006',
        'Gossamid Archers',
        62.50,
        '99120204032_GossamidArchersLead.jpg',
        'https://www.warhammer.com/en-US/shop/sylvaneth-gossamid-archers-2022',
        'Gossamid Archers Warhammer',
    ),
    (
        'arch-revenant',
        'SYL-007',
        'Arch-Revenant',
        43.50,
        '99120204021_DruantitheArchRevenant01.jpg',
        'https://www.warhammer.com/en-US/shop/Sylvaneth-Druanti-The-Arch-Revenant-2020',
        'Arch-Revenant Warhammer',
    ),

    # ── Terrain / Endless Spells ─────────────────────────────────────────────
    (
        'awakened-wyldwood',
        'SYL-008',
        'Awakened Wyldwood',
        65.00,
        '99120204023_AwakenedWyldwood01.jpg',
        'https://www.warhammer.com/en-US/shop/Awakened-Wyldwood-2019',
        'Awakened Wyldwood Warhammer',
    ),
    (
        'endless-spells-sylvaneth',
        'SYL-009',
        'Endless Spells: Sylvaneth',
        53.00,
        '99120204024_SYLEndlessSpells01.jpg',
        'https://www.warhammer.com/en-US/shop/Endless-Spells-Sylvaneth-2019',
        'Endless Spells: Sylvaneth Warhammer',
    ),

    # ── Core units ────────────────────────────────────────────────────────────
    (
        'kurnoth-hunters',
        'SYL-010',
        'Kurnoth Hunters',
        65.00,
        '99120204018_KurnothHunters01.jpg',
        'https://www.warhammer.com/en-US/shop/Sylvaneth-Kurnoth-Hunters',
        'Kurnoth Hunters Warhammer',
    ),

    # ── Centrepiece ───────────────────────────────────────────────────────────
    (
        'alarielle-the-everqueen',
        'SYL-011',
        'Alarielle the Everqueen',
        170.00,
        '99120204015_AlarielleEverqueen01.jpg',
        'https://www.warhammer.com/en-US/shop/Sylvaneth-Alarielle-the-Everqueen',
        'Alarielle the Everqueen Warhammer',
    ),

    # ── Infantry ─────────────────────────────────────────────────────────────
    (
        'dryads',
        'SYL-012',
        'Dryads',
        60.00,
        '99120204012_SylvanethDryads01.jpg',
        'https://www.warhammer.com/en-US/shop/Sylvaneth-Dryads',
        'Dryads Warhammer',
    ),

    # ── Heroes (2026 releases) ────────────────────────────────────────────────
    (
        'branchwych',
        'SYL-013',
        'Branchwych',
        36.50,
        '99120204052_Branchwych1.jpg',
        'https://www.warhammer.com/en-US/shop/sylvaneth-branchwych-2026',
        'Branchwych Warhammer',
    ),
    (
        'grove-guardian',
        'SYL-014',
        'Grove Guardian',
        73.50,
        '99120204051_GroveGuardian1.jpg',
        'https://www.warhammer.com/en-US/shop/sylvaneth-grove-guardian-2026',
        'Grove Guardian Warhammer',
    ),

    # ── Battletome ────────────────────────────────────────────────────────────
    (
        'order-battletome-sylvaneth',
        'SYL-015',
        'Order Battletome: Sylvaneth',
        60.00,
        '60030204010_engSylvanethBattletome01.jpg',
        'https://www.warhammer.com/en-US/shop/battletome-sylvaneth-2026-eng',
        'Order Battletome: Sylvaneth',
    ),

    # ── Cavalry ──────────────────────────────────────────────────────────────
    # ⚠ Shared kit: Revenant Seekers / Spiterider Lancers share NK + MM listing
    (
        'revenant-seekers',
        'SYL-016',
        'Revenant Seekers',
        69.00,
        '99120204031_SpiteriderLancersLead2.jpg',
        'https://www.warhammer.com/en-US/shop/sylvaneth-revenant-seekers-2022',
        'Revenant Seekers Warhammer',
    ),
    (
        'spiterider-lancers',
        'SYL-017',
        'Spiterider Lancers',
        69.00,
        '99120204031_SpiteriderLancersLead.jpg',
        'https://www.warhammer.com/en-US/shop/sylvaneth-spiterider-lancers-2022',
        'Spiterider Lancers Warhammer',
    ),

    # ── Heroes ────────────────────────────────────────────────────────────────
    (
        'warsong-revenant',
        'SYL-018',
        'Warsong Revenant',
        65.00,
        '99120204027_WarsongRevLead.jpg',
        'https://www.warhammer.com/en-US/shop/Sylvaneth-Warsong-Revenant-2021',
        'Warsong Revenant Warhammer',
    ),

    # ── Infantry ─────────────────────────────────────────────────────────────
    (
        'spite-revenants',
        'SYL-019',
        'Spite-Revenants',
        60.00,
        '99120204016_SpiteRevenant01.jpg',
        'https://www.warhammer.com/en-US/shop/Sylvaneth-Spite-Revenants',
        'Spite-Revenants Warhammer',
    ),

    # ── Named heroes ──────────────────────────────────────────────────────────
    (
        'drycha-hamadreth',
        'SYL-020',
        'Drycha Hamadreth',
        65.00,
        '99120204017_DrycaHamadreth01.jpg',
        'https://www.warhammer.com/en-US/shop/Sylvaneth-Drycha-Hamadreth',
        'Drycha Hamadreth Warhammer',
    ),

    # ── Infantry ─────────────────────────────────────────────────────────────
    (
        'tree-revenants',
        'SYL-021',
        'Tree-Revenants',
        60.00,
        '99120204016_TreeRevenant01.jpg',
        'https://www.warhammer.com/en-US/shop/Sylvaneth-Tree-Revenants',
        'Tree-Revenants Warhammer',
    ),

    # ── Treelord variants (triple kit — share NK listing) ────────────────────
    # ⚠ Triple kit: Spirit of Durthu / Treelord Ancient / Treelord
    #   all share the same NK listing.  No MM listing for any of the three.
    (
        'spirit-of-durthu',
        'SYL-022',
        'Spirit of Durthu',
        82.00,
        '99120204013_SylvanethDurthu01.jpg',
        'https://www.warhammer.com/en-US/shop/Sylvaneth-Treelord-Durthu',
        'Spirit of Durthu Warhammer',
    ),
    (
        'treelord-ancient',
        'SYL-023',
        'Treelord Ancient',
        82.00,
        '99120204013_SylvanethTreelordAncient01.jpg',
        'https://www.warhammer.com/en-US/shop/Sylvaneth-Treelord-Ancient',
        'Treelord Ancient Warhammer',
    ),
    (
        'treelord',
        'SYL-024',
        'Treelord',
        82.00,
        '99120204013_SylvanethTreelord01.jpg',
        'https://www.warhammer.com/en-US/shop/Sylvaneth-Treelord',
        'Treelord Warhammer',
    ),

    # ── Named character ───────────────────────────────────────────────────────
    (
        'belthanos-first-thorn-of-kurnoth',
        'SYL-025',
        'Belthanos, First Thorn of Kurnoth',
        114.00,
        '99120204044_Belthanos1.jpg',
        'https://www.warhammer.com/en-US/shop/sylvaneth-belthanos-first-thorn-of-kurnoth-2024',
        'Belthanos, First Thorn of Kurnoth Warhammer',
    ),
]


class Command(BaseCommand):
    """Populate Sylvaneth products (SYL-001 to SYL-025)."""

    help = (
        'Creates / updates 25 Sylvaneth products and seeds GW prices at MSRP. '
        'Idempotent.'
    )

    def handle(self, *args, **options):
        """Run the command."""
        try:
            category_aos = Category.objects.get(slug='age-of-sigmar')
        except Category.DoesNotExist:
            self.stderr.write(self.style.ERROR(
                'Age of Sigmar category not found — run populate_products first.'
            ))
            return

        syl_faction, faction_created = Faction.objects.get_or_create(
            slug='sylvaneth',
            defaults={
                'name': 'Sylvaneth',
                'category': category_aos,
            },
        )
        if faction_created:
            self.stdout.write(self.style.SUCCESS('  Created Sylvaneth faction.'))
        else:
            self.stdout.write(f'  Sylvaneth faction already exists (pk={syl_faction.pk}).')

        gw_retailer = Retailer.objects.filter(name='Games Workshop').first()
        if not gw_retailer:
            self.stdout.write(self.style.WARNING(
                'Games Workshop retailer not found — GW prices will not be seeded.'
            ))

        product_created = product_updated = price_created = price_updated = 0

        for (slug, gw_sku, name, msrp, img_filename, gw_url, ebay_name) in PRODUCTS:
            image_url = _IMG.format(filename=img_filename)

            product, created = Product.objects.update_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'gw_sku': gw_sku,
                    'msrp': msrp,
                    'image_url': image_url,
                    'gw_url': gw_url,
                    'ebay_search_name': ebay_name,
                    'category': category_aos,
                    'faction': syl_faction,
                    'is_active': True,
                    'batch_tag': 'sylvaneth',
                },
            )
            status = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'  {status}: {name} ({gw_sku})'))
            if created:
                product_created += 1
            else:
                product_updated += 1

            # ── Seed GW CurrentPrice at MSRP ──────────────────────────────────
            if gw_retailer and gw_url:
                _, p_created = CurrentPrice.objects.update_or_create(
                    product=product,
                    retailer=gw_retailer,
                    defaults={
                        'price': msrp,
                        'url': gw_url,
                        'in_stock': True,
                        'not_available': False,
                    },
                )
                if p_created:
                    price_created += 1
                else:
                    price_updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'\npopulate_sylvaneth_products complete. '
            f'Products: {product_created} created, {product_updated} updated. '
            f'GW prices: {price_created} created, {price_updated} updated.'
        ))
