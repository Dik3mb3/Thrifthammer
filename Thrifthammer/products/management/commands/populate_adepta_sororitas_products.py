"""
Management command: populate_adepta_sororitas_products

Creates / updates all Adepta Sororitas product entries for ThriftHammer,
seeds GW CurrentPrice records at MSRP.

Covers 30 products (AS-001 to AS-030) from the
Adepta Soritas - GW, NK, MM, AMAZON.xlsx spreadsheet (2026-05-15).

Category: Warhammer 40,000
Faction:  Sisters of Battle

Dual-kit products (share retailer URLs — same physical box):
  - Mortifiers / Penitent Engines  (AS-028 / AS-029)
  - Zephyrim Squad / Seraphim Squad  (AS-011 / existing 52-12)
  - Dominion Squad / Battle Sisters Squad  (AS-022 / existing 52-20)

Kill Team / dual-system products:
  - Celestian Insidiants  (AS-002) — Kill Team product under Adepta Sororitas
  - Kill Team: Sanctifiers  (AS-005) — Kill Team product under Adepta Sororitas

Images are baked in as one-off GW CDN URLs — never auto-refreshed.

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_adepta_sororitas_products
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

_IMG = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{filename}'

# ── Per-SKU bits filter exemptions ───────────────────────────────────────────
# Protected list — only edit manually.  Each value is a space-separated string
# of words that should be exempt from the global _BITS_KEYWORDS title check
# for that specific SKU (because the word is part of the real product name,
# not a bits/parts indicator).
#
# This mirrors the _EBAY_NEGATIVE_KEYWORDS pattern: the block in handle() is
# isolated so it never touches SKUs not listed here.
_EBAY_ALLOWED_TITLE_WORDS = {
    # AS-006 "Reliquant at Arms" — 'arms' appears literally in the product
    # name and therefore in every genuine eBay listing title.  Without this
    # exemption the global bits-keyword check rejects all valid listings.
    'AS-006': 'arms',
}

# ── Product definitions ───────────────────────────────────────────────────────
# (slug, gw_sku, name, msrp, image_filename, gw_url, ebay_search_name)
#
# msrp is USD price from GW en-US storefront as of 2026-05-15.
# ebay_search_name is blank unless the default name gives poor eBay results.
PRODUCTS = [

    # ── Bundles ───────────────────────────────────────────────────────────────
    (
        'armageddon-battalion-adepta-sororitas',
        'AS-001',
        'Armageddon Battalion: Adepta Sororitas',
        170.00,
        '99120108120_ArmageddonBattalionAdeptaSororitas01.jpg',
        'https://www.warhammer.com/en-US/shop/armageddon-battalion-adepta-sororitas-2026',
        '',
    ),

    # ── Kill Team (dual-system) ───────────────────────────────────────────────
    (
        'adepta-sororitas-celestian-insidiants',
        'AS-002',
        'Adepta Sororitas Celestian Insidiants',
        69.00,
        '99120108125_KTCelestianInsidiants01.jpg',
        'https://www.warhammer.com/en-US/shop/kill-team-celestian-insidiants-2026',
        'Kill Team Celestian Insidiants',
    ),
    (
        'adepta-sororitas-kill-team-sanctifiers',
        'AS-005',
        'Kill Team: Sanctifiers',
        69.00,
        '99120108116_KillTeamSanctifiers01.jpg',
        'https://www.warhammer.com/en-US/shop/kill-team-sanctifiers-2025',
        '',
    ),

    # ── Characters ───────────────────────────────────────────────────────────
    (
        'adepta-sororitas-intranzia-fraye-dogmata-superior',
        'AS-003',
        'Adepta Sororitas Intranzia Fraye - Dogmata Superior',
        73.50,
        '99120108122_AdeptaSororitasIntranziaFrayeDogmataSuperior1.jpg',
        'https://www.warhammer.com/en-US/shop/adepta-sororitas-intranzia-fraye-dogmata-superior-2026',
        '',
    ),
    (
        'adepta-sororitas-aestred-thurga-reliquant-at-arms',
        'AS-006',
        'Adepta Sororitas Aestred Thurga, Reliquant at Arms',
        43.50,
        '99120108050_SoBAestredThurgaRelinquantatArmsLead.jpg',
        'https://www.warhammer.com/en-US/shop/Aestred-Thurga-Relinquant-At-Arms',
        'Adepta Sororitas Aestred Thurga, Reliquant at Arms',
    ),
    (
        'adepta-sororitas-palatine',
        'AS-009',
        'Adepta Sororitas Palatine',
        39.00,
        '99070108007_PalatineLead.jpg',
        'https://www.warhammer.com/en-US/shop/Adepta-Sororitas-Palatine-2021',
        '',
    ),
    (
        'adepta-sororitas-daemonifuge-ephrael-stern-kyganil',
        'AS-010',
        'Adepta Sororitas Daemonifuge - Ephrael Stern & Kyganil',
        60.00,
        '99120199073_DaemonifugeEphraelSternKyganilLead.jpg',
        'https://www.warhammer.com/en-US/shop/Daemonifuge-Ephrael-Stern-and-Kyganil-2020',
        'Daemonifuge Ephrael Stern Kyganil',  # & stripped by query builder; explicit override avoids ambiguity
    ),
    (
        'adepta-sororitas-canoness',
        'AS-014',
        'Adepta Sororitas Canoness',
        43.50,
        '99120108034_SoBCanonessLead.jpg',
        'https://www.warhammer.com/en-US/shop/Adepta-Sororitas-Canoness-2020',
        '',
    ),
    (
        'adepta-sororitas-dialogus',
        'AS-015',
        'Adepta Sororitas Dialogus',
        43.50,
        '99120108022_SoBDialogusLead.jpg',
        'https://www.warhammer.com/en-US/shop/Adepta-Sororitas-Dialogus-2020',
        '',
    ),
    (
        'adepta-sororitas-imagifier',
        'AS-016',
        'Adepta Sororitas Imagifier',
        35.00,
        '99070108006_SoBImagifierLead.jpg',
        'https://www.warhammer.com/en-US/shop/Adepta-Sororitas-Imagifier-2020',
        '',
    ),
    (
        'adepta-sororitas-junith-eruita',
        'AS-018',
        'Adepta Sororitas Junith Eruita',
        60.00,
        '99120108026_JunithEruita01.jpg',
        'https://www.warhammer.com/en-US/shop/Adepta-Sororitas-Junith-Eruita-2020',
        '',
    ),
    (
        'adepta-sororitas-hospitaller',
        'AS-019',
        'Adepta Sororitas Hospitaller',
        43.50,
        '99120108024_Hospitaller01.jpg',
        'https://www.warhammer.com/en-US/shop/Adepta-Sororitas-Hospitaller-2020',
        '',
    ),
    (
        'adepta-sororitas-celestine-the-living-saint',
        'AS-021',
        'Adepta Sororitas Celestine, the Living Saint',
        65.00,
        '99120108008_TriumvirateoftheImperium06.jpg',
        'https://www.warhammer.com/en-US/shop/Space-Marine-Celestine-The-Living-Saint-2018',
        '',
    ),
    (
        'adepta-sororitas-canoness-with-jump-pack',
        'AS-024',
        'Adepta Sororitas Canoness with Jump Pack',
        47.00,
        '99120108103_ASCanonessJumpPack1.jpg',
        'https://www.warhammer.com/en-US/shop/adepta-sororitas-canoness-with-jump-pack-2024',
        '',
    ),
    (
        'adepta-sororitas-ministorum-priest',
        'AS-025',
        'Adepta Sororitas Ministorum Priest',
        35.00,
        '99070108011_ASMinistorumPriest01.jpg',
        'https://www.warhammer.com/en-US/shop/adepta-sororitas-ministorum-priest-2024',
        '',
    ),
    (
        'adepta-sororitas-ministorum-priest-with-vindictor',
        'AS-026',
        'Adepta Sororitas Ministorum Priest with Vindictor',
        35.00,
        '99070108012_ASMinistorumPriestWithVindictor01.jpg',
        'https://www.warhammer.com/en-US/shop/adepta-sororitas-ministorum-priest-with-vindicator-2024',
        '',
    ),
    (
        'adepta-sororitas-sister-dogmata',
        'AS-027',
        'Adepta Sororitas Sister Dogmata',
        39.00,
        '99070108008_SoBSisterDogmataLead.jpg',
        'https://www.warhammer.com/en-US/shop/Adepta-Sororitas-Sister-Dogmata-2021',
        '',
    ),
    (
        'adepta-sororitas-sister-superior-amalia-novena',
        'AS-030',
        'Adepta Sororitas Sister Superior Amalia Novena',
        39.00,
        '99120108020_SisterAmaliaNovena01.jpg',
        'https://www.warhammer.com/en-US/shop/Sister-Superior-Amalia-Novena-2019',
        '',
    ),

    # ── Infantry ─────────────────────────────────────────────────────────────
    # ⚠ Dual kit: Zephyrim Squad / Seraphim Squad share the same box
    #   Seraphim Squad already exists in DB as 52-12
    (
        'adepta-sororitas-zephyrim-squad',
        'AS-011',
        'Adepta Sororitas Zephyrim Squad',
        65.00,
        '99120108040_SeraphimZephyrimGroup.jpg',
        'https://www.warhammer.com/en-US/shop/Adepta-Sororitas-Zephyrim-Squad-2020',
        '',
    ),
    (
        'adepta-sororitas-repentia-squad',
        'AS-013',
        'Adepta Sororitas Repentia Squad',
        60.00,
        '99120108036_SoBRepSquadLead.jpg',
        'https://www.warhammer.com/en-US/shop/Adepta-Sororitas-Repentia-Squad-2020',
        '',
    ),
    (
        'adepta-sororitas-arco-flagellants',
        'AS-017',
        'Adepta Sororitas Arco-flagellants',
        60.00,
        '99120108032_ArcoFlagellants01.jpg',
        'https://www.warhammer.com/en-US/shop/Adepta-Sororitas-Arco-Flagellants-2020',
        '',
    ),
    (
        'adepta-sororitas-the-triumph-of-saint-katherine',
        'AS-020',
        'Adepta Sororitas The Triumph of Saint Katherine',
        122.00,
        '99120108037_TriumphofKatherine01.jpg',
        'https://www.warhammer.com/en-US/shop/Adepta-Sororitas-The-Triumph-Of-St-Katherine-2020',
        '',
    ),
    # ⚠ Dual kit: Dominion Squad / Battle Sisters Squad share the same box
    #   Battle Sisters Squad already exists in DB as 52-20
    (
        'adepta-sororitas-dominion-squad',
        'AS-022',
        'Adepta Sororitas Dominion Squad',
        65.00,
        '99120108033_SoBDominions1.jpg',
        'https://www.warhammer.com/en-US/shop/Adepta-Sororitas-Dominions-Celestians-2020',
        'Adeptus Sororitas Battle Sisters Squad',  # eBay lists this kit as Battle Sisters Squad
    ),
    (
        'adepta-sororitas-sisters-novitiate-squad',
        'AS-023',
        'Adepta Sororitas Sisters Novitiate Squad',
        64.00,
        '99120108121_CalanathGroup1.jpg',
        'https://www.warhammer.com/en-US/shop/adepta-sororitas-sisters-novitiate-squad-2025',
        '',
    ),

    # ── Vehicles / Walkers ───────────────────────────────────────────────────
    (
        'adepta-sororitas-castigator',
        'AS-007',
        'Adepta Sororitas Castigator',
        92.00,
        '99120108048_SoBCastigatorLead.jpg',
        'https://www.warhammer.com/en-US/shop/Adepta-Sororitas-Castigator',
        '',
    ),
    (
        'adepta-sororitas-paragon-warsuits',
        'AS-008',
        'Adepta Sororitas Paragon Warsuits',
        82.00,
        '99120108046_SoBParagonWarsuitsLead.jpg',
        'https://www.warhammer.com/en-US/shop/Adepta-Sororitas-Paragon-Warsuit-2021',
        '',
    ),
    (
        'adepta-sororitas-rhino',
        'AS-012',
        'Adepta Sororitas Rhino',
        65.00,
        '99120108039_RhinoLead.jpg',
        'https://www.warhammer.com/en-US/shop/Adepta-Sororitas-Rhino-2020',
        '',
    ),
    # ⚠ Dual kit: Mortifiers / Penitent Engines share the same box
    (
        'adepta-sororitas-mortifiers',
        'AS-028',
        'Adepta Sororitas Mortifiers',
        65.00,
        '99120108035_ASMortifierLead.jpg',
        'https://www.warhammer.com/en-US/shop/Adepta-Sororitas-Mortifier-2020',
        '',
    ),
    (
        'adepta-sororitas-penitent-engines',
        'AS-029',
        'Adepta Sororitas Penitent Engines',
        65.00,
        '99120108035_PenitentEngines01.jpg',
        'https://www.warhammer.com/en-US/shop/Adepta-Sororitas-Penitent-Engines-2020',
        '',
    ),

    # ── Codex ─────────────────────────────────────────────────────────────────
    (
        'codex-adepta-sororitas',
        'AS-004',
        'Codex: Adepta Sororitas',
        60.00,
        '60030108020_EngASCodex01.jpg',
        'https://www.warhammer.com/en-US/shop/codex-adepta-sororitas-2024-eng',
        '',
    ),
]


class Command(BaseCommand):
    """Populate Adepta Sororitas products (AS-001 to AS-030)."""

    help = (
        'Creates / updates 30 Adepta Sororitas products and seeds GW prices at MSRP. '
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
            sob_faction = Faction.objects.get(slug='sisters-of-battle')
        except Faction.DoesNotExist:
            self.stderr.write(self.style.ERROR(
                'Sisters of Battle faction not found — run populate_products first.'
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
                    'category': category_40k,
                    'faction': sob_faction,
                    'is_active': True,
                    'batch_tag': 'adepta-sororitas',
                },
            )
            status = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'  {status}: {name} ({gw_sku})'))
            if created:
                product_created += 1
            else:
                product_updated += 1

            # ── Per-SKU bits exemptions (protected list) ──────────────────────
            # Only touches SKUs explicitly listed in _EBAY_ALLOWED_TITLE_WORDS.
            if gw_sku in _EBAY_ALLOWED_TITLE_WORDS:
                Product.objects.filter(gw_sku=gw_sku).update(
                    ebay_allowed_title_words=_EBAY_ALLOWED_TITLE_WORDS[gw_sku],
                )

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
            f'\npopulate_adepta_sororitas_products complete. '
            f'Products: {product_created} created, {product_updated} updated. '
            f'GW prices: {price_created} created, {price_updated} updated.'
        ))
