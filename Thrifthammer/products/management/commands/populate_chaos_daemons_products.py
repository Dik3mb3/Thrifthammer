"""
Management command: populate_chaos_daemons_products

Creates / updates all Chaos Daemons product entries for ThriftHammer,
seeds GW CurrentPrice records at MSRP.

Covers 21 net-new products (CD-001 to CD-021).
Source: Chaos Demons - GW, NK, MM.xlsx (2026-05-31).

Category: Warhammer 40,000
Faction:  Chaos Daemons  (created by this command if not yet in DB)

Note: A further 23 existing products from Emperor's Children, Death Guard,
Thousand Sons, World Eaters, and Chaos Space Marines are dual-tagged to
appear on the Chaos Daemons page via their secondary_factions M2M field.
That tagging is handled by the separate add_chaos_daemons_secondary_faction
command which must run after this one (Chaos Daemons faction must exist first).

Shared-listing products (same physical kit, multiple build options):
  CD-016 / CD-017 / CD-018  — Burning Chariot / Exalted Flamer / Fateskimmer
                               (share NK listing)
  CD-019 / CD-020            — Skull Cannon / Rendmaster, Herald of Khorne
                               on Blood Throne  (share NK listing)

No NK listing (2 products):
  CD-007  Skull Altar
  CD-010  Changecaster

No MM listing (17 products):
  CD-002, CD-003, CD-004, CD-007, CD-008, CD-009, CD-010, CD-011,
  CD-012, CD-014, CD-015, CD-016, CD-017, CD-018, CD-019, CD-020, CD-021

Images are baked in as one-off GW CDN URLs -- never auto-refreshed.

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_chaos_daemons_products
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

_IMG = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{filename}'

# ── Product definitions ───────────────────────────────────────────────────────
# (slug, gw_sku, name, msrp, image_filename, gw_url, ebay_search_name)
#
# msrp is USD price from GW en-US storefront as of 2026-05-31.
# ebay_search_name set per Excel 'Ebay Search Name' column.
PRODUCTS = [

    # ── Greater Daemon / Special ──────────────────────────────────────────────
    (
        'belakor-the-dark-master',
        'CD-001',
        "Be'lakor, the Dark Master",
        170.00,
        '99129915058_ChaosDaemonsBelakortheDarkMasterLead.jpg',
        'https://www.warhammer.com/en-US/shop/Chaos-Daemons-Belakor-The-Dark-Master-2021',
        "Be'lakor, the Dark Master Warhammer",
    ),

    # ── Slaanesh ─────────────────────────────────────────────────────────────
    (
        'syllesske-the-vengeful-allegiance',
        'CD-002',
        "Syll'Esske: The Vengeful Allegiance",
        60.00,
        '99129915055_DoSSyllesskeVengefulAlliance01.jpg',
        'https://www.warhammer.com/en-US/shop/The-Vengeful-Allegiance-2019',
        "Syll'Esske: The Vengeful Allegiance Warhammer",
    ),
    (
        'the-contorted-epitome',
        'CD-003',
        'The Contorted Epitome',
        60.00,
        '99129915054_DoSContortedEpitome01.jpg',
        'https://www.warhammer.com/en-US/shop/The-Contorted-Epitome-2019',
        'The Contorted Epitome Warhammer',
    ),
    (
        'infernal-enrapturess',
        'CD-004',
        'Infernal Enrapturess',
        48.00,
        '99129915053_DoSInfernalEnrapturess01.jpg',
        'https://www.warhammer.com/en-US/shop/Infernal-Enrapturess-2019',
        'Infernal Enrapturess Warhammer',
    ),
    (
        'the-masque',
        'CD-005',
        'The Masque',
        39.00,
        '99079915007_DoSMasque01.jpg',
        'https://www.warhammer.com/en-US/shop/The-Masque-2019',
        'The Masque Warhammer',
    ),

    # ── Khorne ───────────────────────────────────────────────────────────────
    (
        'skulltaker',
        'CD-006',
        'Skulltaker',
        43.50,
        '99129915075_Skulltaker1.jpg',
        'https://www.warhammer.com/en-US/shop/Skulltaker-2019',
        'Skulltaker Warhammer',
    ),
    (
        'skull-altar',
        'CD-007',
        'Skull Altar',
        53.00,
        '99120201083_BoKHSkullAltar01.jpg',
        'https://www.warhammer.com/en-US/shop/Skull-Altar-2019',
        'Skull Altar Warhammer',
    ),
    (
        'karanak',
        'CD-011',
        'Karanak',
        43.50,
        '99079915006_KaranakHoundofVengeance01.jpg',
        'https://www.warhammer.com/en-US/shop/Karanak-the-Hound-of-Vengeance-2019',
        'Karanak Warhammer',
    ),
    (
        'bloodmaster-herald-of-khorne',
        'CD-012',
        'Bloodmaster, Herald of Khorne',
        35.00,
        '99079915005_BloodmasterofKhorneBox01.jpg',
        'https://www.warhammer.com/en-US/shop/Bloodmaster-Herald-of-Khorne-2019',
        'Bloodmaster, Herald of Khorne Warhammer',
    ),

    # ── Nurgle ────────────────────────────────────────────────────────────────
    (
        'feculent-gnarlmaw',
        'CD-008',
        'Feculent Gnarlmaw',
        53.00,
        '99129915047_FeculentGnarlmaw01.jpg',
        'https://www.warhammer.com/en-US/shop/Feculent-Gnarlmaw-2018',
        'Feculent Gnarlmaw Warhammer',
    ),
    (
        'horticulous-slimux',
        'CD-009',
        'Horticulous Slimux',
        65.00,
        '60010299012_BlightWarENG03.jpg',
        'https://www.warhammer.com/en-US/shop/Horticulous-Slimux-2018',
        'Horticulous Slimux Warhammer',
    ),
    (
        'sloppity-bilepiper',
        'CD-013',
        'Sloppity Bilepiper',
        39.00,
        '99079915004_SloppityBilepiper01.jpg',
        'https://www.warhammer.com/en-US/shop/Sloppity-Bilepiper-Herald-Of-Nurgle-2018',
        'Sloppity Bilepiper Warhammer',
    ),
    (
        'poxbringer',
        'CD-014',
        'Poxbringer',
        35.00,
        '99079915002_Poxbringer01.jpg',
        'https://www.warhammer.com/en-US/shop/Poxbringer-Herald-Of-Nurgle-2018',
        'Poxbringer Warhammer',
    ),

    # ── Tzeentch ─────────────────────────────────────────────────────────────
    (
        'changecaster',
        'CD-010',
        'Changecaster',
        60.00,
        '99129915030_ChangecasterChariotUpdateALT.jpg',
        'https://www.warhammer.com/en-US/shop/changecaster-2022',
        'Changecaster Warhammer',
    ),
    (
        'the-changeling',
        'CD-015',
        'The Changeling',
        39.00,
        '99129915034_TzeentchChangeling01.jpg',
        'https://www.warhammer.com/en-US/shop/the-changeling-2016',
        'The Changeling Warhammer',
    ),
    # ⚠ Shared kit: Burning Chariot / Exalted Flamer / Fateskimmer share NK listing
    (
        'burning-chariot-of-tzeentch',
        'CD-016',
        'Burning Chariot of Tzeentch',
        60.00,
        '99129915030_BurningChariot01.jpg',
        'https://www.warhammer.com/en-US/shop/Burning-Chariot-of-Tzeentch',
        'Burning Chariot of Tzeentch Warhammer',
    ),
    (
        'exalted-flamer-of-tzeentch',
        'CD-017',
        'Exalted Flamer of Tzeentch',
        60.00,
        '99129915030_ExhaltedFlameronFoot01.jpg',
        'https://www.warhammer.com/en-US/shop/Exalted-Flamer-of-Tzeentch',
        'Exalted Flamer of Tzeentch Warhammer',
    ),
    (
        'fateskimmer-herald-of-tzeentch-on-burning-chariot',
        'CD-018',
        'Fateskimmer, Herald of Tzeentch on Burning Chariot',
        60.00,
        '99129915030_HeraldonBurningChariot01.jpg',
        'https://www.warhammer.com/en-US/shop/herald-of-tzeentch-on-burning-chariot-2016',
        'Fateskimmer, Herald of Tzeentch on Burning Chariot Warhammer',
    ),

    # ── Khorne war machines ───────────────────────────────────────────────────
    # ⚠ Shared kit: Skull Cannon / Rendmaster share NK listing
    (
        'skull-cannon',
        'CD-019',
        'Skull Cannon',
        48.00,
        '99129915025_DaemonsofKhorneSkullCannon01.jpg',
        'https://www.warhammer.com/en-US/shop/Daemons-Of-Khorne-Skull-Cannon',
        'Skull Cannon Warhammer',
    ),
    (
        'rendmaster-herald-of-khorne-on-blood-throne',
        'CD-020',
        'Rendmaster, Herald of Khorne on Blood Throne',
        48.00,
        '99129915025_DaemonsofKhorneBloodThrone01.jpg',
        'https://www.warhammer.com/en-US/shop/Daemons-Of-Khorne-Bloodthrone',
        'Blood Throne Khorne Warhammer',
    ),

    # ── Multi-god ─────────────────────────────────────────────────────────────
    (
        'soul-grinder',
        'CD-021',
        'Soul Grinder',
        82.00,
        '99129915013_SoulgrinderNEW01.jpg',
        'https://www.warhammer.com/en-US/shop/Soul-Grinder',
        'Soul Grinder Warhammer',
    ),
]


class Command(BaseCommand):
    """Populate Chaos Daemons products (CD-001 to CD-021)."""

    help = (
        'Creates / updates 21 Chaos Daemons products and seeds GW prices at MSRP. '
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

        cd_faction, faction_created = Faction.objects.get_or_create(
            slug='chaos-daemons',
            defaults={
                'name': 'Chaos Daemons',
                'category': category_40k,
            },
        )
        if faction_created:
            self.stdout.write(self.style.SUCCESS('  Created Chaos Daemons faction.'))
        else:
            self.stdout.write(f'  Chaos Daemons faction already exists (pk={cd_faction.pk}).')

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
                    'category': category_40k,
                    'faction': cd_faction,
                    'is_active': True,
                    'batch_tag': 'chaos-daemons',
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
            f'\npopulate_chaos_daemons_products complete. '
            f'Products: {product_created} created, {product_updated} updated. '
            f'GW prices: {price_created} created, {price_updated} updated.'
        ))
