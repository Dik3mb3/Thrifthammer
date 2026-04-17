"""
Management command: populate_ork_phase2_products

Adds new Ork products scraped from the GW en-US Ork category page.
Tagged batch_tag='phase-2'. Seeds GW CurrentPrice at MSRP.

SKIPPED (already exist in DB):
  - Combat Patrol: Orks        → exists as 'Ork Combat Patrol'      (slug: ork-combat-patrol)
  - Killa Kans                 → exists as 'Ork Killa Kans'          (slug: ork-killa-kans)
  - Ork Nobz                   → exists as 'Ork Nobz'                (slug: ork-nobz)
  - Ork Boyz ($48, 2018 kit)   → exists as 'Ork Boyz'               (slug: ork-boyz)

UNCERTAIN (excluded — user to confirm):
  - 'Boyz' ($60, 2022 kit, URL: ork-boyz-combat-patrol-2022)
    May be a different/newer plastic Boyz box from the 2021 Beastsnagga
    Combat Patrol rerelease. Name overlaps with existing 'Ork Boyz'.
    Not added to avoid overwriting. Confirm separately.

Safe to run repeatedly (idempotent via update_or_create keyed on gw_sku).

Usage:
    python manage.py populate_ork_phase2_products
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

_IMG = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{filename}'

# (slug, name, msrp, image_filename, gw_url, gw_sku)
PRODUCTS = [
    # ── Characters ────────────────────────────────────────────────────────────
    (
        'ork-boss-snikrot',
        'Boss Snikrot',
        43.50,
        '99120103114_Snikrot1.jpg',
        'https://www.warhammer.com/en-US/shop/orks-boss-snikrot-2023',
        '50-32',
    ),
    (
        'ork-ghazghkull-thraka',
        'Ghazghkull Thraka',
        82.00,
        '99120103079_ThrakaLead.jpg',
        'https://www.warhammer.com/en-US/shop/Ghazghkull-Thraka-2020',
        '50-38',
    ),
    (
        'ork-beastboss',
        'Beastboss',
        43.50,
        '99120103078_BeastbossLead.jpg',
        'https://www.warhammer.com/en-US/shop/orks-beastboss-2021',
        '50-23',
    ),
    (
        'ork-beastboss-on-squigosaur',
        'Beastboss on Squigosaur',
        60.00,
        '99120103075_BeastbossSquigasaurLead.jpg',
        'https://www.warhammer.com/en-US/shop/beastboss-on-squigosaur-2021',
        '50-24',
    ),
    (
        'ork-mozrog-skragbad',
        'Mozrog Skragbad',
        60.00,
        '99120103075_MozrogLead.jpg',
        'https://www.warhammer.com/en-US/shop/orks-mozrog-skragbad-2021',
        '50-51',
    ),
    (
        'ork-painboss',
        'Painboss',
        43.50,
        '99070103006_ORKSPainBossLead.jpg',
        'https://www.warhammer.com/en-US/shop/orks-painboss-2021',
        '50-60',
    ),
    (
        'ork-zodgrod-wortsnagga',
        'Zodgrod Wortsnagga',
        48.00,
        '60010103001_BeastsnaggaZodGroup1.jpg',
        'https://www.warhammer.com/en-US/shop/orks-zodgrod-wortsnagga-2021',
        '50-67',
    ),
    (
        'ork-big-mek-shokk-attack-gun',
        'Big Mek with Shokk Attack Gun',
        43.50,
        '99120103031_ShokkAttackGun01.jpg',
        'https://www.warhammer.com/en-US/shop/Big-Mek-with-Shokk-Attack-Gun',
        '50-28',
    ),
    (
        'ork-mek',
        'Ork Mek',
        32.00,
        '99070103004_OrkMek01.jpg',
        'https://www.warhammer.com/en-US/shop/Ork-Mek-2018',
        '50-55',
    ),
    (
        'ork-painboy',
        'Ork Painboy',
        35.00,
        '99070103003_Painboy01.jpg',
        'https://www.warhammer.com/en-US/shop/Ork-Painboy-2018',
        '50-56',
    ),
    # ── Infantry ──────────────────────────────────────────────────────────────
    (
        'ork-beast-snagga-boyz',
        'Ork Beast Snagga Boyz',
        60.00,
        '99120103073_ORKSnaggaBoyzLead.jpg',
        'https://www.warhammer.com/en-US/shop/orks-beast-snagga-boyz-2021',
        '50-52',
    ),
    (
        'ork-squighog-boyz',
        'Squighog Boyz',
        69.00,
        '60010103001_BeastsnaggaHogzGroup2.jpg',
        'https://www.warhammer.com/en-US/shop/orks-squighog-boyz-2021',
        '50-63',
    ),
    (
        'ork-stormboyz',
        'Ork Stormboyz',
        42.00,
        '99120103056_Stormboyz01.jpg',
        'https://www.warhammer.com/en-US/shop/Ork-Stormboyz-2018',
        '50-57',
    ),
    (
        'ork-gretchin',
        'Ork Gretchin',
        27.00,
        '99120103053_OrkGretchin01.jpg',
        'https://www.warhammer.com/en-US/shop/Ork-Gretchin-2018',
        '50-54',
    ),
    (
        'ork-deffkoptas',
        'Deffkoptas',
        69.00,
        '99120103107_DeffkoptasLead.jpg',
        'https://www.warhammer.com/en-US/shop/deffkoptas-2022',
        '50-37',
    ),
    # ── Vehicles ──────────────────────────────────────────────────────────────
    (
        'ork-hunta-rig',
        'Hunta Rig',
        145.00,
        '99120103072_ORKSKillRigHuntaRigLeadAlt.jpg',
        'https://www.warhammer.com/en-US/shop/hunta-rig-2021',
        '50-41',
    ),
    (
        'ork-kill-rig',
        'Kill Rig',
        145.00,
        '99120103072_ORKSKillRigHuntaRigLead.jpg',
        'https://www.warhammer.com/en-US/shop/orks-kill-rig-2021',
        '50-42',
    ),
    (
        'ork-shokkjump-dragsta',
        'Shokkjump Dragsta',
        60.00,
        '99120103067_ShokkjumpDragsta01.jpg',
        'https://www.warhammer.com/en-US/shop/Orks-Shokkjump-Dragsta-2019',
        '50-62',
    ),
    (
        'ork-kustom-boosta-blasta',
        'Kustom Boosta-blasta',
        60.00,
        '99120103064_BoostaBlasta01.jpg',
        'https://www.warhammer.com/en-US/shop/Orks-Kustom-Boosta-Blasta-2019',
        '50-44',
    ),
    (
        'ork-rukkatrukk-squigbuggy',
        'Rukkatrukk Squigbuggy',
        60.00,
        '99120103066_RukkatrukkSquigbuggy01.jpg',
        'https://www.warhammer.com/en-US/shop/Orks-Rukkatrukk-Squigbuggy-2018',
        '50-61',
    ),
    (
        'ork-megatrakk-scrapjet',
        'Megatrakk Scrapjet',
        60.00,
        '99120103065_MegatrakScrapjet01.jpg',
        'https://www.warhammer.com/en-US/shop/Orks-Megatrakk-Scrapjet-2018',
        '50-45',
    ),
    (
        'ork-deffkilla-wartrike',
        'Deffkilla Wartrike',
        60.00,
        '99120103063_DeffkillaWartrike01.jpg',
        'https://www.warhammer.com/en-US/shop/Orks-Deffkilla-Wartrike-2018',
        '50-36',
    ),
    (
        'ork-boomdakka-snazzwagon',
        'Boomdakka Snazzwagon',
        60.00,
        '99120103062_BoomdakkaSnazzwagon01.jpg',
        'https://www.warhammer.com/en-US/shop/Orks-Boomdakka-Snazzwagon-2018',
        '50-31',
    ),
    # ── Aircraft (all share the same physical kit — 4 build options) ──────────
    (
        'ork-burna-bommer',
        'Burna-Bommer',
        90.00,
        '99120103043_OrkBurnaBommer01.jpg',
        'https://www.warhammer.com/en-US/shop/Ork-Burna-Bommer-NEW',
        '50-33',
    ),
    (
        'ork-blitza-bommer',
        'Blitza-Bommer',
        90.00,
        '99120103043_OrkBlitzaBommer01.jpg',
        'https://www.warhammer.com/en-US/shop/Ork-Blitza-Bommer-NEW',
        '50-29',
    ),
    (
        'ork-dakkajet',
        'Dakkajet',
        90.00,
        '99120103043_OrkDakkajet01.jpg',
        'https://www.warhammer.com/en-US/shop/Ork-Dakkajet-NEW',
        '50-35',
    ),
    (
        'ork-wazbom-blastajet',
        'Wazbom Blastajet',
        90.00,
        '99120103043_WazbomBlastajet01.jpg',
        'https://www.warhammer.com/en-US/shop/Ork-Wazbom-Blastajet',
        '50-65',
    ),
    # ── Artillery (all share the same physical kit — 3 build options) ─────────
    (
        'ork-mek-gunz-traktor-kannon',
        'Mek Gunz: Traktor Kannon',
        60.00,
        '99120103029_OrkTraktorCannon01.jpg',
        'https://www.warhammer.com/en-US/shop/Mek-Gunz-Traktor-Kannon',
        '50-49',
    ),
    (
        'ork-mek-gunz-kustom-mega-kannon',
        'Mek Gunz: Kustom Mega-kannon',
        60.00,
        '99120103029_OrkKustomCannon01.jpg',
        'https://www.warhammer.com/en-US/shop/Mek-Gunz-Kustom-Mega-kannon',
        '50-47',
    ),
    (
        'ork-mek-gunz-smasha-gun',
        'Mek Gunz: Smasha Gun',
        60.00,
        '99120103029_OrkSmashaGun01.jpg',
        'https://www.warhammer.com/en-US/shop/Mek-Gunz-Smasha-Gun',
        '50-48',
    ),
    # ── Codex ─────────────────────────────────────────────────────────────────
    (
        'codex-orks',
        'Codex: Orks',
        60.00,
        '60030103013_ENGOrkCodex1.jpg',
        'https://www.warhammer.com/en-US/shop/codex-orks-hb-english-2024',
        '50-34',
    ),
]


class Command(BaseCommand):
    """Add new phase-2 Ork products from GW category page. Does not touch existing Ork SKUs."""

    help = (
        'Adds new Ork products scraped from GW en-US Ork page (2026-04-03). '
        'Tagged phase-2. Seeds GW CurrentPrice at MSRP. '
        'Skips: Ork Combat Patrol, Ork Killa Kans, Ork Nobz, Ork Boyz (all already exist). '
        'Idempotent — keyed on slug, never overwrites existing slugs that are not in this list.'
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
                    'batch_tag': 'phase-2',
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
            f'\npopulate_ork_phase2_products complete.\n'
            f'  Products: {created_count} created, {updated_count} updated.\n'
            f'  GW prices: {price_created} created, {price_updated} updated.\n'
            f'\nUNCERTAIN (not added — confirm with user):\n'
            f'  "Boyz" $60 (2022 kit, URL: ork-boyz-combat-patrol-2022)\n'
            f'  May be a different kit from existing "Ork Boyz" (slug: ork-boyz).\n'
            f'  Check before adding to avoid duplicate.'
        ))
