"""
Management command: populate_ork_phase3_products

Adds remaining Ork products found on the GW en-US Ork category page
that were missing from the database after phase-1 and phase-2 seeding.

Sourced from live GW page scrape — 2026-04-03.
Tagged batch_tag='phase-3'. Seeds GW CurrentPrice at MSRP.

SKIPPED (already exist in DB):
  - Ork Boyz ($48, 2018 kit)            → slug: ork-boyz
  - Boyz ($60, 2022 kit)                → user confirmed skip (duplicate)
  - Ork Combat Patrol                   → slug: ork-combat-patrol
  - Ork Battlewagon                     → slug: ork-battlewagon
  - All phase-2 products                → already seeded
  - Kill Team: Wrecka Krew              → Kill Team product, not mainline

NOTES:
  - Gorkanaut and Morkanaut share the same physical kit (dual-build).
  - Gunwagon and Bonebreaka are alternate builds of the Battlewagon kit.
  - Big Mek (2024, ork-big-mek-2024) is distinct from the existing
    Big Mek with Shokk Attack Gun (ork-big-mek-shokk-attack-gun).
  - Ork Gargantuan Squiggoth ($530) is a Forge World resin product
    (note 99590103031_ image prefix vs 9912... for plastic kits).

Safe to run repeatedly (idempotent via update_or_create keyed on gw_sku).

Usage:
    python manage.py populate_ork_phase3_products
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

_IMG = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{filename}'

# (slug, name, msrp, image_filename, gw_url, gw_sku)
PRODUCTS = [
    # ── Characters ────────────────────────────────────────────────────────────
    (
        'ork-warboss-with-attack-squig',
        'Ork Warboss with Attack Squig',
        39.00,
        '99120103111_WarbossAttackSquigLead.jpg',
        'https://www.warhammer.com/en-US/shop/ork-warboss-with-attack-squig-2022',
        '50-59',
    ),
    (
        'ork-big-mek-2024',
        'Big Mek',
        53.00,
        '99120103120_ORKBigMek01.jpg',
        'https://www.warhammer.com/en-US/shop/orks-big-mek-2024',
        '50-26',
    ),
    (
        'ork-big-mek-in-mega-armour',
        'Big Mek in Mega Armour',
        73.50,
        '99120103035_BigMekMega01.jpg',
        'https://www.warhammer.com/en-US/shop/Big-Mek-in-Mega-Armour',
        '50-27',
    ),
    (
        'ork-weirdboy',
        'Weirdboy',
        33.50,
        '99800103004_WeirdboyNEW01.jpg',
        'https://www.warhammer.com/en-US/shop/Ork-Weirdboy',
        '50-66',
    ),
    # ── Infantry ──────────────────────────────────────────────────────────────
    (
        'ork-burna-boyz',
        'Ork Burna Boyz',
        42.00,
        '99120103054_OrkBurnaBoyz01.jpg',
        'https://www.warhammer.com/en-US/shop/Ork-Burna-Boyz-2018',
        '50-53',
    ),
    (
        'ork-kommandos',
        'Kommandos',
        69.00,
        '99120103127_KT2Group2.jpg',
        'https://www.warhammer.com/en-US/shop/orks-kommandos-2025',
        '50-43',
    ),
    # ── Cavalry / Bikes ───────────────────────────────────────────────────────
    (
        'ork-warbiker-mob',
        'Ork Warbiker Mob',
        60.00,
        '99120103057_WarbikerMob01.jpg',
        'https://www.warhammer.com/en-US/shop/Ork-Warbiker-Mob-2018',
        '50-58',
    ),
    # ── Vehicles ──────────────────────────────────────────────────────────────
    (
        'ork-gunwagon',
        'Gunwagon',
        130.00,
        '99120103084_GunwagonLead.jpg',
        'https://www.warhammer.com/en-US/shop/gunwagon-2021',
        '50-40',
    ),
    (
        'ork-bonebreaka',
        'Bonebreaka',
        130.00,
        '99120103084_BonebreakaLead.jpg',
        'https://www.warhammer.com/en-US/shop/bonebreaka-2021',
        '50-30',
    ),
    (
        'ork-big-ed-bossbunka',
        "Big'ed Bossbunka",
        85.00,
        '99120103082_BigEdBossBunkaLead.jpg',
        'https://www.warhammer.com/en-US/shop/orks-big-ed-bossbunka-2021',
        '50-25',
    ),
    # ── Walkers / Super-heavies ───────────────────────────────────────────────
    (
        'ork-gorkanaut',
        'Gorkanaut',
        150.00,
        '99120103034_Gorkanaut01.jpg',
        'https://www.warhammer.com/en-US/shop/Gorkanaut',
        '50-39',
    ),
    (
        'ork-morkanaut',
        'Morkanaut',
        150.00,
        '99120103034_Morkanaut01.jpg',
        'https://www.warhammer.com/en-US/shop/Morkanaut',
        '50-50',
    ),
    (
        'ork-stompa',
        'Stompa',
        150.00,
        '99120103021_StompaNEW01.jpg',
        'https://www.warhammer.com/en-US/shop/Ork-Stompa',
        '50-64',
    ),
    # ── Fortifications ───────────────────────────────────────────────────────
    (
        'ork-mek-gunz-bubblechukka',
        'Mek Gunz: Bubblechukka',
        60.00,
        '99120103029_OrkBubbleChukka01.jpg',
        'https://www.warhammer.com/en-US/shop/Mek-Gunz-Bubblechukka',
        '50-46',
    ),
    # Ork Gargantuan Squiggoth removed 2026-04-04 — Forge World resin product,
    # not stocked by mainstream retailers. User requested removal of all FW products.
]


class Command(BaseCommand):
    """Add remaining Ork products missing after phase-1 and phase-2 seeding."""

    help = (
        'Adds remaining Ork products scraped from GW en-US Ork page (2026-04-03). '
        'Tagged phase-3. Seeds GW CurrentPrice at MSRP. '
        'Skips all products already in the database. Idempotent.'
    )

    def handle(self, *args, **options):
        """Run the command."""
        category_40k = Category.objects.filter(name='Warhammer 40,000').first()
        if not category_40k:
            self.stderr.write(self.style.ERROR(
                'Warhammer 40,000 category not found — run populate_products first.'
            ))
            return

        ork_faction = Faction.objects.filter(name='Orks').first()
        if not ork_faction:
            self.stderr.write(self.style.ERROR(
                'Orks faction not found — run populate_products first.'
            ))
            return

        gw_retailer = Retailer.objects.filter(name='Games Workshop').first()
        if not gw_retailer:
            self.stdout.write(self.style.WARNING(
                'Games Workshop retailer not found — GW prices will not be seeded.'
            ))

        created_count = 0
        updated_count = 0
        price_created = 0
        price_updated = 0

        for (slug, name, msrp, img_filename, gw_url, gw_sku) in PRODUCTS:
            image_url = _IMG.format(filename=img_filename)

            product, created = Product.objects.update_or_create(
                gw_sku=gw_sku,
                defaults={
                    'name': name,
                    'slug': slug,
                    'gw_sku': gw_sku,
                    'msrp': msrp,
                    'image_url': image_url,
                    'gw_url': gw_url,
                    'category': category_40k,
                    'faction': ork_faction,
                    'is_active': True,
                    'batch_tag': 'phase-3',
                },
            )
            status = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'  {status}: {name} — ${msrp:.2f}'))
            if created:
                created_count += 1
            else:
                updated_count += 1

            # Seed GW price at MSRP
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
            f'\npopulate_ork_phase3_products complete.\n'
            f'  Products: {created_count} created, {updated_count} updated.\n'
            f'  GW prices: {price_created} created, {price_updated} updated.'
        ))
