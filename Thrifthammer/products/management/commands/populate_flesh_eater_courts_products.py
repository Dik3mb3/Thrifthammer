"""
Management command: populate_flesh_eater_courts_products

Creates / updates all Flesh-Eater Courts product entries for ThriftHammer,
seeds GW CurrentPrice records at MSRP, and uses the existing Flesh-Eater Courts
faction (slug=flesh-eater-courts, already in DB).

Covers 21 products (FEC-001 to FEC-021) from the
AOS Flesh Eater Courts - GW, NK, MM.xlsx (2026-06-10).

Category: Age of Sigmar
Faction:  Flesh-Eater Courts (existing — get_or_create is safe/idempotent)

Dual-tag product (NOT created here — handled by add_fec_secondary_faction):
  - Nagash, Supreme Lord of the Undead (SG-016) — already in DB under
    Soulblight Gravelords; secondary_factions.add() surfaces it on FEC page.

Triple-kit products (same physical box, multiple build options):
  - Abhorrant Ghoul King on Royal Zombie Dragon /
    Abhorrant Ghoul King on Royal Terrorgheist /
    Royal Zombie Dragon                                (FEC-002 / FEC-003 / FEC-014)
  - Crypt Infernal Courtier /
    Crypt Haunter Courtier /
    Crypt Flayers                                      (FEC-004 / FEC-005 / FEC-015)

Images are baked in as one-off GW CDN URLs — never auto-refreshed.

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_flesh_eater_courts_products
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

_IMG = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{filename}'
_GW = 'https://www.warhammer.com/en-US/shop/'

# ── Product definitions ───────────────────────────────────────────────────────
# (slug, gw_sku, name, msrp, image_filename, gw_url, ebay_search_name)
#
# msrp is USD price from GW en-US storefront as of 2026-06-10.
# ebay_search_name is set directly — single source of truth for eBay search.
PRODUCTS = [

    # ── Heroes ────────────────────────────────────────────────────────────────
    (
        'abhorrant-archregent',
        'FEC-001',
        'Abhorrant Archregent',
        35.00,
        '99070207009_AbhorrantArchregent01.jpg',
        f'{_GW}Flesh-Eater-Courts-Abhorrant-Archregent-2020',
        'Abhorrant Archregent flesh eater courts',
    ),
    # ⚠ Triple kit: Abhorrant Ghoul King on Royal Zombie Dragon /
    #   Abhorrant Ghoul King on Royal Terrorgheist / Royal Zombie Dragon
    #   (FEC-002 / FEC-003 / FEC-014) — share NK URL
    (
        'abhorrant-ghoul-king-on-royal-zombie-dragon',
        'FEC-002',
        'Abhorrant Ghoul King on Royal Zombie Dragon',
        77.00,
        '99120207035_FleshEatersKingonDragon01.jpg',
        f'{_GW}Abhorrant-Ghoul-King-on-Zombie-Dragon-2016',
        'Terrorgheist Age of Sigmar',
    ),
    # ⚠ Triple kit: Abhorrant Ghoul King on Royal Terrorgheist /
    #   Abhorrant Ghoul King on Royal Zombie Dragon / Royal Zombie Dragon
    #   (FEC-003 / FEC-002 / FEC-014) — share NK URL
    (
        'abhorrant-ghoul-king-on-royal-terrorgheist',
        'FEC-003',
        'Abhorrant Ghoul King on Royal Terrorgheist',
        77.00,
        '99120207035_FleshEatersKingonTerrorgheist01.jpg',
        f'{_GW}Flesh-Eaters-Courts-Abhorrant-Ghoul-King-on-Terrorgheist',
        'Terrorgheist Age of Sigmar',
    ),
    # ⚠ Triple kit: Crypt Infernal Courtier / Crypt Haunter Courtier / Crypt Flayers
    #   (FEC-004 / FEC-005 / FEC-015) — share NK URL; Courtiers also share MM URL
    (
        'crypt-infernal-courtier',
        'FEC-004',
        'Crypt Infernal Courtier',
        60.00,
        '99120207033_FleshEaterCryptFlayerCourtier01.jpg',
        f'{_GW}Flesh-Eater-Courts-Crypt-Infernal-Courtier',
        'Crypt Flayers Age of Sigmar',
    ),
    # ⚠ Triple kit: Crypt Haunter Courtier / Crypt Infernal Courtier / Crypt Flayers
    #   (FEC-005 / FEC-004 / FEC-015) — share NK URL; Courtiers also share MM URL
    (
        'crypt-haunter-courtier',
        'FEC-005',
        'Crypt Haunter Courtier',
        60.00,
        '99120207033_FleshEaterCryptHaunterCourtier01.jpg',
        f'{_GW}Flesh-Eater-Courts-Crypt-Haunter-Courtier',
        'Crypt Flayers Age of Sigmar',
    ),
    (
        'high-falconer-felgryn',
        'FEC-006',
        'High Falconer Felgryn',
        42.00,
        '99120207190_FleshEaterCourtsHighFalconerFelgryn1.jpg',
        f'{_GW}flesh-eater-courts-high-falconer-felgryn-2025',
        'High Falconer Felgryn flesh eater courts',
    ),
    (
        'marrowscroll-herald',
        'FEC-007',
        'Marrowscroll Herald',
        39.00,
        '99070207023_FECMarrowscrollHerald01.jpg',
        f'{_GW}flesh-eater-courts-marrowscroll-herald-2024',
        'Marrowscroll Herald flesh eater courts',
    ),
    (
        'abhorrant-gorewarden',
        'FEC-008',
        'Abhorrant Gorewarden',
        48.00,
        '99120207150_FECAbhorrentGorewarden01.jpg',
        f'{_GW}flesh-eater-courts-abhorrant-gorewarden-2024',
        'Abhorrant Gorewarden flesh eater courts',
    ),
    (
        'abhorrant-cardinal',
        'FEC-009',
        'Abhorrant Cardinal',
        42.00,
        '99120207155_FECAbhorrentCardinal01.jpg',
        f'{_GW}flesh-eater-courts-abhorrant-cardinal-2024',
        'Abhorrant Cardinal flesh eater courts',
    ),
    (
        'grand-justice-gormayne',
        'FEC-010',
        'Grand Justice Gormayne',
        43.50,
        '99120207154_FECGrandJusticeGormayne01.jpg',
        f'{_GW}flesh-eater-courts-grand-justice-gormayne-2024',
        'Grand Justice Gormayne flesh eater courts',
    ),
    (
        'royal-decapitator',
        'FEC-011',
        'Royal Decapitator',
        39.00,
        '99070207022_FECRoyalDecapitator01.jpg',
        f'{_GW}flesh-eater-courts-royal-decapitator-2024',
        'Royal Decapitator flesh eater courts',
    ),
    (
        'ushoran-mortarch-of-delusion',
        'FEC-012',
        'Ushoran, Mortarch of Delusion',
        122.00,
        '99120207149_UshoranMortarchDelusion1.jpg',
        f'{_GW}flesh-eater-courts-ushoran-mortarch-of-delusion-2024',
        'Ushoran, Mortarch of Delusion flesh eater courts',
    ),
    (
        'varghulf-courtier',
        'FEC-013',
        'Varghulf Courtier',
        48.00,
        '99120207153_FECVarghulfCourtier01.jpg',
        f'{_GW}flesh-eater-courts-varghulf-courtier-2024',
        'Varghulf Courtier flesh eater courts',
    ),
    # ⚠ Triple kit: Royal Zombie Dragon /
    #   Abhorrant Ghoul King on Royal Zombie Dragon / on Royal Terrorgheist
    #   (FEC-014 / FEC-002 / FEC-003) — share NK URL
    (
        'royal-zombie-dragon',
        'FEC-014',
        'Royal Zombie Dragon',
        77.00,
        '99120207035_FleshEatersZombieDragon01.jpg',
        f'{_GW}Royal-Zombie-Dragon-2019',
        'Terrorgheist Age of Sigmar',
    ),

    # ── Units ─────────────────────────────────────────────────────────────────
    # ⚠ Triple kit: Crypt Flayers / Crypt Infernal Courtier / Crypt Haunter Courtier
    #   (FEC-015 / FEC-004 / FEC-005) — share NK URL
    (
        'crypt-flayers',
        'FEC-015',
        'Crypt Flayers',
        60.00,
        '99120207033_FleshEaterCryptFlayers01.jpg',
        f'{_GW}Flesh-Eater-Courts-Crypt-Flayers',
        'Crypt Flayers Age of Sigmar',
    ),
    (
        'morbheg-knights',
        'FEC-016',
        'Morbheg Knights',
        60.00,
        '99120207152_FECMorbhegKnights02.jpg',
        f'{_GW}flesh-eater-courts-morbheg-knights-2024',
        'Morbheg Knights flesh eater courts',
    ),
    (
        'cryptguard',
        'FEC-017',
        'Cryptguard',
        53.00,
        '99120207151_FECCryptguard02.jpg',
        f'{_GW}flesh-eater-courts-cryptguard-2024',
        'Cryptguard flesh eater courts',
    ),
    (
        'royal-beastflayers',
        'FEC-018',
        'Royal Beastflayers',
        60.00,
        '60010299040_ENGWCNMQuest4.jpg',
        f'{_GW}flesh-eater-courts-royal-beastflayers-warband-2025',
        'Royal Beastflayers Warcry',
    ),

    # ── Terrain / Scenery ─────────────────────────────────────────────────────
    (
        'charnel-throne',
        'FEC-019',
        'Charnel Throne',
        53.00,
        '99120207070_CharnelThrone01.jpg',
        f'{_GW}Flesh-Eater-Courts-Charnel-Throne-2019',
        'Charnel Throne flesh eater courts',
    ),

    # ── Spells / Endless ──────────────────────────────────────────────────────
    (
        'endless-spells-flesh-eater-courts',
        'FEC-020',
        'Endless Spells: Flesh-eater Courts',
        48.00,
        '99120207071_FECEndlessSpells01.jpg',
        f'{_GW}Endless-Spells-Flesh-Eater-Courts-2019',
        'Endless Spells: Flesh-eater Courts',
    ),

    # ── Battletome ────────────────────────────────────────────────────────────
    (
        'death-battletome-flesh-eater-courts',
        'FEC-021',
        'Death Battletome: Flesh-eater Courts',
        60.00,
        '60030207021_FlesheaterCourtsBattletomeHB1.jpg',
        f'{_GW}battletome-flesh-eater-courts-2025-eng',
        'Death Battletome: Flesh-eater Courts',
    ),
]


class Command(BaseCommand):
    """Populate Flesh-Eater Courts products (FEC-001 to FEC-021)."""

    help = (
        'Creates / updates 21 Flesh-Eater Courts products and seeds GW prices at MSRP. '
        'Uses existing Flesh-Eater Courts faction. Idempotent.'
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

        fec_faction, faction_created = Faction.objects.get_or_create(
            slug='flesh-eater-courts',
            defaults={'name': 'Flesh-Eater Courts', 'category': category_aos},
        )
        if faction_created:
            self.stdout.write('  Created Flesh-Eater Courts faction.')

        gw = Retailer.objects.filter(name='Games Workshop').first()

        products_created = 0
        products_updated = 0
        prices_created = 0
        prices_updated = 0

        for (slug, gw_sku, name, msrp, image_filename, gw_url, ebay_search_name) in PRODUCTS:
            image_url = _IMG.format(filename=image_filename)

            product, created = Product.objects.update_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'gw_sku': gw_sku,
                    'faction': fec_faction,
                    'category': category_aos,
                    'msrp': msrp,
                    'image_url': image_url,
                    'gw_url': gw_url,
                    'ebay_search_name': ebay_search_name,
                    'batch_tag': 'flesh-eater-courts',
                    'is_active': True,
                },
            )
            if created:
                products_created += 1
                self.stdout.write(f'  Created: {name} ({gw_sku})')
            else:
                products_updated += 1
                self.stdout.write(f'  Updated: {name} ({gw_sku})')

            if gw:
                _, price_created = CurrentPrice.objects.update_or_create(
                    product=product,
                    retailer=gw,
                    defaults={'price': msrp, 'in_stock': True},
                )
                if price_created:
                    prices_created += 1
                else:
                    prices_updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'populate_flesh_eater_courts_products complete. '
            f'Products: {products_created} created, {products_updated} updated. '
            f'GW prices: {prices_created} created, {prices_updated} updated.'
        ))
