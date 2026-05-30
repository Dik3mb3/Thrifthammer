"""
Management command: populate_chaos_knights_products

Creates / updates all Chaos Knights product entries for ThriftHammer,
seeds GW CurrentPrice records at MSRP.

Covers 18 products from Chaos Knights - GW, NK, MM.xlsx (2026-05-29).

Category: Warhammer 40,000
Faction:  Chaos Knights  (already exists in DB — fetched via get())

Shared-listing products (same physical kit, multiple build options):
  CK-003 / CK-004  — War Dog Huntsmen / Executioners   (share MM + NK listing)
  CK-005 / CK-006 / CK-007  — War Dog Stalkers / Brigands / Karnivores (share MM + NK)
  CK-008 / CK-009  — Knight Tyrant / Despoiler          (share MM listing; separate NK)

No MM listing (8 products):
  CK-011, CK-012, CK-013, CK-014, CK-016, CK-017, CK-018

No NK listing (5 products):
  CK-013, CK-014, CK-016, CK-017, CK-018

Images are baked in as one-off GW CDN URLs -- never auto-refreshed.

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_chaos_knights_products
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

_IMG = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{filename}'

# ── Per-SKU eBay negative keywords (space-separated, shlex-parsed) ────────────
_NEGATIVE_KEYWORDS = {
    'chaos-knight-questoris': 'elbows',  # CK-010 — filter partial/stripped kits
}

# ── Product definitions ───────────────────────────────────────────────────────
# (slug, gw_sku, name, msrp, image_filename, gw_url, ebay_search_name)
#
# msrp is USD price from GW en-US storefront as of 2026-05-29.
# ebay_search_name set per Excel 'Ebay Search Name' column.
PRODUCTS = [

    # ── Codex ─────────────────────────────────────────────────────────────────
    (
        'codex-chaos-knights',
        'CK-001',
        'Codex: Chaos Knights',
        60.00,
        '60030102031_ENGChaosKnightsHBCodex1.jpg',
        'https://www.warhammer.com/en-US/shop/codex-chaos-knights-2025-eng',
        'Codex: Chaos Knights Warhammer 40K',
    ),

    # ── Knights (large) ───────────────────────────────────────────────────────
    (
        'chaos-knight-ruinator',
        'CK-002',
        'Chaos Knight Ruinator',
        200.00,
        '99120102191_CKKnightRuinator01.jpg',
        'https://www.warhammer.com/en-US/shop/chaos-knights-chaos-knight-ruinator-2025',
        'Knight Ruinator Warhammer 40K',
    ),
    (
        'chaos-knight-tyrant',
        'CK-008',
        'Chaos Knight Tyrant',
        195.00,
        '99120108016_KnightTyrant.jpg',
        'https://www.warhammer.com/en-US/shop/imperial-knights-knight-dominus-knight-tyrant-2022',
        'Knight Tyrant Warhammer 40K',
    ),
    # ⚠ Dual kit: Questoris Despoiler / Defender share MM URL (gw-54-21)
    (
        'chaos-knight-despoiler',
        'CK-009',
        'Chaos Knight Despoiler',
        194.00,
        '99120108105_IKKnightQuestorisLEADDespoiler.jpg',
        'https://www.warhammer.com/en-US/shop/knight-questoris-despoiler-2025',
        'Knight Valiant Warhammer 40K',
    ),
    (
        'chaos-knight-questoris',
        'CK-010',
        'Chaos Knight Questoris',
        194.00,
        '99120108105_IKKnightQuestorisLEADDefender.jpg',
        'https://www.warhammer.com/en-US/shop/imperial-knights-knight-questoris-2025',
        'Knight Questoris Warhammer 40K',
    ),

    # ── War Dogs ──────────────────────────────────────────────────────────────
    # ⚠ Dual kit: Huntsmen / Executioners share MM URL (gw-54-20) + NK listing
    (
        'chaos-war-dog-huntsmen',
        'CK-003',
        'Chaos War Dog Huntsmen',
        100.00,
        '99120108080_CKWardogHuntsmanLead.jpg',
        'https://www.warhammer.com/en-US/shop/war-dog-huntsman-2022',
        'Imperial Knight Armigers Warhammer 40K',
    ),
    (
        'chaos-war-dog-executioners',
        'CK-004',
        'Chaos War Dog Executioners',
        100.00,
        '99120108080_CKWardogExecutionerLead.jpg',
        'https://www.warhammer.com/en-US/shop/war-dog-executioner-2022',
        'Imperial Knight Armigers Warhammer 40K',
    ),
    # ⚠ Triple kit: Stalkers / Brigands / Karnivores share MM URL (gw-43-64-2022) + NK listing
    (
        'chaos-war-dog-stalkers',
        'CK-005',
        'Chaos War Dog Stalkers',
        100.00,
        '99120102139_CKWarDogStalkerLead.jpg',
        'https://www.warhammer.com/en-US/shop/chaos-knights-war-dog-stalker-2022',
        'War Dogs Warhammer 40K',
    ),
    (
        'chaos-war-dog-brigands',
        'CK-006',
        'Chaos War Dog Brigands',
        100.00,
        '99120102139_CKWarDogBrigandLead.jpg',
        'https://www.warhammer.com/en-US/shop/chaos-knights-war-dog-brigand-2022',
        'War Dogs Warhammer 40K',
    ),
    (
        'chaos-war-dog-karnivores',
        'CK-007',
        'Chaos War Dog Karnivores',
        100.00,
        '99120102139_CKWarDogKarnivoreLead.jpg',
        'https://www.warhammer.com/en-US/shop/chaos-knights-war-dog-karnivore-2022',
        'War Dogs Warhammer 40K',
    ),

    # ── Cerastus Knights ──────────────────────────────────────────────────────
    (
        'chaos-cerastus-knight-acheron',
        'CK-011',
        'Chaos Cerastus Knight Acheron',
        215.00,
        '99123008006_HHCerastusKnightAcheron01.jpg',
        'https://www.warhammer.com/en-US/shop/horus-heresy-cerastus-knight-acheron-2023',
        'Cerastus Knight Acheron Warhammer 40K',
    ),
    (
        'chaos-cerastus-knight-castigator',
        'CK-012',
        'Chaos Cerastus Knight Castigator',
        215.00,
        '99123008005_HHCerastusKnightCastigator01.jpg',
        'https://www.warhammer.com/en-US/shop/horus-heresy-cerastus-knight-castigator-2023',
        'Cerastus Knight Castigator Warhammer 40K',
    ),
    (
        'chaos-cerastus-knight-lancer',
        'CK-015',
        'Chaos Cerastus Knight Lancer',
        215.00,
        '99123008004_HHCerastusKnightLancer01.jpg',
        'https://www.warhammer.com/en-US/shop/horus-heresy-cerastus-knight-lancer-2023',
        'Cerastus Knight Lancer Warhammer 40K',
    ),
    (
        'chaos-cerastus-knight-atrapos',
        'CK-018',
        'Chaos Cerastus Knight Atrapos',
        370.00,
        '99560108146_MechanicumCerastusKnightAtrapos01.jpg',
        'https://www.warhammer.com/en-US/shop/Mechanicum-Cerastus-Knight-Atrapos',
        'Cerastus Knight Atrapos Warhammer 40K',
    ),

    # ── Questoris Knights ─────────────────────────────────────────────────────
    (
        'chaos-questoris-knight-magaera',
        'CK-013',
        'Chaos Questoris Knight Magaera',
        250.00,
        '99590108120_QuestorisKnightMagaera01.jpg',
        'https://www.warhammer.com/en-US/shop/Questoris-Knight-Magaera',
        'Questoris Knight Magaera Warhammer 40K',
    ),
    (
        'chaos-questoris-knight-styrix',
        'CK-014',
        'Chaos Questoris Knight Styrix',
        250.00,
        '99590108122_QuestorisKnightStyrix01.jpg',
        'https://www.warhammer.com/en-US/shop/Questoris-Knight-Styrix',
        'Questoris Knight Styrix Warhammer 40K',
    ),

    # ── Acastus Knights ───────────────────────────────────────────────────────
    (
        'chaos-acastus-knight-asterius',
        'CK-016',
        'Chaos Acastus Knight Asterius',
        660.00,
        '99560108209_AcastusKnightAsterius01.jpg',
        'https://www.warhammer.com/en-US/shop/Mechanicum-Acastus-Knight-Asterius-2019',
        'Acastus Knight Asterius Warhammer 40K',
    ),
    (
        'chaos-acastus-knight-porphyrion',
        'CK-017',
        'Chaos Acastus Knight Porphyrion',
        710.00,
        '99560108172_AcastusKnightPorphyrion01.jpg',
        'https://www.warhammer.com/en-US/shop/Acastus-Knight-Porphyrion',
        'Acastus Knight Porphyrion Warhammer 40K',
    ),
]


class Command(BaseCommand):
    """Populate Chaos Knights products (CK-001 to CK-018)."""

    help = (
        'Creates / updates 18 Chaos Knights products and seeds GW prices at MSRP. '
        'Idempotent.'
    )

    def handle(self, *args, **options):
        """Run the command."""
        try:
            category_40k = Category.objects.get(slug='warhammer-40000')
        except Category.DoesNotExist:
            self.stderr.write(self.style.ERROR(
                'Warhammer 40,000 category not found — run populate_products first.'
            ))
            return

        try:
            ck_faction = Faction.objects.get(slug='chaos-knights')
        except Faction.DoesNotExist:
            self.stderr.write(self.style.ERROR(
                'Chaos Knights faction not found — run populate_products first.'
            ))
            return

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
                    'ebay_negative_keywords': _NEGATIVE_KEYWORDS.get(slug, ''),
                    'category': category_40k,
                    'faction': ck_faction,
                    'is_active': True,
                    'batch_tag': 'chaos-knights',
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
            f'\npopulate_chaos_knights_products complete. '
            f'Products: {product_created} created, {product_updated} updated. '
            f'GW prices: {price_created} created, {price_updated} updated.'
        ))
