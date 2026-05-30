"""
Management command: populate_imperial_agents_products

Creates / updates all Agents of the Imperium product entries for ThriftHammer,
seeds GW CurrentPrice records at MSRP.

Covers 14 products from Agents - GW, MM, NK.xlsx (2026-05-29).

Category: Warhammer 40,000
Faction:  Agents of the Imperium  (already exists in DB — fetched via get())

No MM listing (4 products):
  IA-001, IA-003, IA-011, IA-012

No NK listing (1 product):
  IA-012

Images are baked in as one-off GW CDN URLs -- never auto-refreshed.

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_imperial_agents_products
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

_IMG = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{filename}'

# ── Per-SKU eBay allowed title words (exempted from the bits filter) ──────────
# "arms" appears in "Voidsmen-at-Arms" — legitimately part of the product name
# but also in the global bits blocklist. Exempting it allows correct listings
# (e.g. "Rogue Trader Entourage and Voidsmen-at-Arms Warhammer Imperial Agents")
# to pass validation.
_ALLOWED_TITLE_WORDS = {
    'rogue-trader-entourage-and-voidsmen-at-arms': 'arms',
}

# ── Product definitions ───────────────────────────────────────────────────────
# (slug, gw_sku, name, msrp, image_filename, gw_url, ebay_search_name)
#
# msrp is USD price from GW en-US storefront as of 2026-05-29.
# ebay_search_name set per Excel 'Ebay Search Name' column.
PRODUCTS = [

    # ── Combat Patrol ─────────────────────────────────────────────────────────
    (
        'combat-patrol-imperial-agents',
        'IA-001',
        'Combat Patrol: Imperial Agents',
        170.00,
        '99120108101_IACP1.jpg',
        'https://www.warhammer.com/en-US/shop/combat-patrol-imperial-agents-2024',
        'Combat Patrol Imperial Agents',
    ),

    # ── Inquisitors ───────────────────────────────────────────────────────────
    (
        'inquisitor-kroyle',
        'IA-002',
        'Inquisitor Kroyle',
        60.00,
        '99120108124_ImperialAgentsInquisitorKroyleEXTRA.jpg',
        'https://www.warhammer.com/en-US/shop/imperial-agents-inquisitor-kroyle-2026',
        'Inquisitor Kroyle Warhammer',
    ),
    (
        'eisenhorn',
        'IA-003',
        'Eisenhorn',
        39.00,
        '99810181001_Eisenhorn01.jpg',
        'https://www.warhammer.com/en-US/shop/Eisenhorn-2018',
        'Eisenhorn Warhammer',
    ),
    (
        'inquisitor-coteaz',
        'IA-004',
        'Inquisitor Coteaz',
        48.00,
        '99120108087_IAInquisitorCoteazGlodovanEagle1.jpg',
        'https://www.warhammer.com/en-US/shop/inquisitor-coteaz-and-the-glodovan-eagle-2024',
        'Inquisitor Coteaz Warhammer',
    ),
    (
        'inquisitor-greyfax',
        'IA-010',
        'Inquisitor Greyfax',
        35.00,
        '99120108008_TriumvirateoftheImperium04.jpg',
        'https://www.warhammer.com/en-US/shop/imperial-agents-inquisitor-greyfax-2024',
        'Inquisitor Greyfax Warhammer',
    ),
    (
        'lord-inquisitor-kyria-draxus',
        'IA-011',
        'Lord Inquisitor Kyria Draxus',
        39.00,
        '99120108043_INQOXLordInqKyriaDraxusLead.jpg',
        'https://www.warhammer.com/en-US/shop/imperial-agents-inquisitor-draxus-2024',
        'Lord Inquisitor Kyria Draxus Warhammer',
    ),

    # ── Navigator ─────────────────────────────────────────────────────────────
    (
        'navigator',
        'IA-005',
        'Navigator',
        35.00,
        '99070108014_Navigator1.jpg',
        'https://www.warhammer.com/en-US/shop/imperial-agents-navigator-2024',
        'Imperial Agents Navigator Warhammer 40K',
    ),

    # ── Assassins ─────────────────────────────────────────────────────────────
    (
        'callidus-assassin',
        'IA-006',
        'Callidus Assassin',
        36.50,
        '99070108003_CallidusAssassin01.jpg',
        'https://www.warhammer.com/en-US/shop/imperial-agents-callidus-assassin-2024',
        'Callidus Assassin Warhammer',
    ),
    (
        'vindicare-assassin',
        'IA-007',
        'Vindicare Assassin',
        42.00,
        '99070108001_VindicareAssassin01.jpg',
        'https://www.warhammer.com/en-US/shop/imperial-agents-vindicare-assassin-2024',
        'Vindicare Assassin Warhammer',
    ),
    (
        'culexus-assassin',
        'IA-008',
        'Culexus Assassin',
        42.00,
        '99070108002_CulexusAssassin01.jpg',
        'https://www.warhammer.com/en-US/shop/imperial-agents-culexus-assassin-2024',
        'Culexus Assassin Warhammer',
    ),
    (
        'eversor-assassin',
        'IA-009',
        'Eversor Assassin',
        42.00,
        '99070108004_EversorAssassin01.jpg',
        'https://www.warhammer.com/en-US/shop/imperial-agents-eversor-assassin-2024',
        'Eversor Assassin Warhammer',
    ),

    # ── Rogue Trader ──────────────────────────────────────────────────────────
    (
        'rogue-trader-entourage-and-voidsmen-at-arms',
        'IA-012',
        'Rogue Trader Entourage and Voidsmen-at-Arms',
        65.00,
        '99120108113_RTEntourageVoidsmen1.jpg',
        'https://www.warhammer.com/en-US/shop/imperial-agents-rogue-trader-entourage-and-voidsmen-at-arm-2024',
        'Rogue Trader Entourage And Voidsmen At Arms Warhammer Imperial Agents',
    ),

    # ── Units ─────────────────────────────────────────────────────────────────
    (
        'inquisitorial-agents',
        'IA-013',
        'Inquisitorial Agents',
        60.00,
        '99120108112_InquisitorialAgents1.jpg',
        'https://www.warhammer.com/en-US/shop/imperial-agents-inquisitorial-agents-2024',
        'Inquisitorial Agents Warhammer',
    ),

    # ── Codex ─────────────────────────────────────────────────────────────────
    (
        'codex-imperial-agents',
        'IA-014',
        'Codex: Imperial Agents',
        60.00,
        '60030108021_ENGIACodex1.jpg',
        'https://www.warhammer.com/en-US/shop/codex-imperial-agents-2024-eng',
        'Codex Imperial Agents',
    ),
]


class Command(BaseCommand):
    """Populate Agents of the Imperium products (IA-001 to IA-014)."""

    help = (
        'Creates / updates 14 Agents of the Imperium products and seeds GW prices at MSRP. '
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
            ia_faction = Faction.objects.get(slug='agents-of-the-imperium')
        except Faction.DoesNotExist:
            self.stderr.write(self.style.ERROR(
                'Agents of the Imperium faction not found — run populate_products first.'
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
                    'ebay_allowed_title_words': _ALLOWED_TITLE_WORDS.get(slug, ''),
                    'category': category_40k,
                    'faction': ia_faction,
                    'is_active': True,
                    'batch_tag': 'agents-of-the-imperium',
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
            f'\npopulate_imperial_agents_products complete. '
            f'Products: {product_created} created, {product_updated} updated. '
            f'GW prices: {price_created} created, {price_updated} updated.'
        ))
