"""
Find and optionally apply Amazon URLs for products that have none stored.

Workflow:
  1. Run without --apply to see what the API would find (nothing written).
  2. Review the output chart. Add overrides to ASIN_OVERRIDES for any wrong results.
  3. Re-run with --apply to write the URLs to the database.

Products that already have an Amazon URL are always skipped — existing data
is never overwritten.

Usage:
    python manage.py find_amazon_asins --faction necrons           # dry run
    python manage.py find_amazon_asins --faction necrons --apply   # write to DB
    python manage.py find_amazon_asins --faction necrons --no-brand-filter
"""

import time

from django.conf import settings
from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer
from scrapers.retailers.amazon_creators import AmazonCreatorsClient

# ─── Manual ASIN overrides ────────────────────────────────────────────────────
# Add entries here when SearchItems returns the wrong product for a SKU.
# Format:  'gw_sku': 'ASIN'
# The override ASIN is used directly — the API search is skipped entirely.
# These are permanent: leave them here so future runs always use the right ASIN.
#
# Example:
#   'prod4390157': 'B08HCL7SFY',   # Ghost Ark — search returned wrong listing
ASIN_OVERRIDES = {
    'MC-001': 'B0899J6L6G',   # Adeptus Mechanicus Archaeopter Fusilave
    'MC-002': 'B0899J6L6G',   # Adeptus Mechanicus Archaeopter Stratoraptor
    'MC-003': 'B0899J6L6G',   # Adeptus Mechanicus Archaeopter Transvector
    'MC-011': 'B0899FYZHD',   # Adeptus Mechanicus Pteraxii Sterylizors
    'MC-019': 'B0965W1ZD8',   # Adeptus Mechanicus Sydonian Dragoon
    # Horus Heresy — Astartes Legions
    'AL-058': 'B0D6RF5M8H',   # MKVI Legion Command Squad — search returned MKIII
    # Horus Heresy — Cult Mechanicum
    'CM-005': 'B0F29MCWW5',   # Ursarax Cohort — search returned Thallax Cohort
    # Horus Heresy — Forces of the Emperor
    'FOE-013': 'B0D2J217CZ',  # Solar Auxilia Basilisk/Medusa — search returned Battle Group
    'FOE-015': 'B0CYCQGBJY',  # Malcador Heavy Tank — search returned Malcador Infernus
    'FOE-018': 'B0CYCSZ4QV',  # Solar Auxilia Tactical Command Section — search returned Lasrifle Section
    'FOE-020': 'B0CYCPJR16',  # Solar Auxilia Leman Russ Strike/Command Tank — search returned Assault Tank
}

# SKUs to explicitly exclude from Amazon URL discovery.
# Add a SKU here if the API returns the wrong product and you have no
# correct ASIN to substitute — the product will simply have no Amazon URL.
SKIP_SKUS = {
    'prod770020a',  # Support Weapon — API returns wrong listing, no correct ASIN
    'AM-004',                       # Astra Militarum Attilan Rough Riders
    '47-17',                        # Astra Militarum Basilisk
    'AM-012',                       # Astra Militarum Catachan Command Squad
    'AM-014',                       # Astra Militarum Catachan Jungle Fighters
    'prod4570149-99120102114',      # Death Guard Chosen of Mortarion
    'P-223010-99120102198',         # Death Guard Lord of Poxes
    '54-15',                        # Imperial Knight Preceptor / Canis Rex
    '50-53',                        # Ork Burna Boyz
    '50-16',                        # Ork Deff Dread
    '50-59',                        # Ork Warboss with Attack Squig
    '62-01',                        # Aethon Shaan
    '48-106',                       # Captain with Relic Shield
    '48-123',                       # Lieutenant with Storm Shield
    'P-MUTALITH-VB',                # Mutalith Vortex Beast
    'P-TZAANGOR-UPG',               # Tzaangor Upgrade Pack
    'TY-036',                       # Tyranid Prime
    'TY-035',                       # Tyranid Hierophant Bio-Titan
    'TY-034',                       # Tyranid Harridan
    'P-WE-LORD-SKULLS',             # Khorne Lord of Skulls
    'SR-017',                       # Seraphon Saurus Scar-Veteran on Carnosaur
    'SR-013',                       # Seraphon Saurus Guard
    'SR-015',                       # Seraphon Saurus Oldblood on Carnosaur
    '90-10',                        # Skaven Clanrats
    'SK-009',                       # Skaven Clawlord
    'SK-026',                       # Skaven Master Moulder
    'BB-037',                       # Blood Bowl Dwarf Deathroller
    'BB-036',                       # Blood Bowl Goblin Secret Weapons
    'BB-032',                       # Blood Bowl Khorne Bloodspawn
    'BB-039',                       # Blood Bowl Kiroth Krakeneye
    'BB-031',                       # Blood Bowl Kroxigor
    'BB-035',                       # Blood Bowl Minotaur
    'BB-063',                       # Blood Bowl Nurgle Rotspawn
    'BB-030',                       # Blood Bowl Rat Ogre
    'BB-040',                       # Blood Bowl Vargheist
    'BB-029',                       # Blood Bowl Yhetee
    'SE-014',                       # Stormcast Eternals Gardus Steel Soul
    'SE-027',                       # Stormcast Eternals Knight-Arcanum
    'SE-020',                       # Stormcast Eternals Knight-Questor
    'SE-026',                       # Stormcast Eternals Lord-Imperatant
    'SE-028',                       # Stormcast Eternals Prosecutors
    'SE-006',                       # Stormcast Eternals Stormcoven
    'SE-010',                       # Stormcast Eternals Vanquishers
    # Horus Heresy — no valid Amazon listing; API returned wrong product
    'AL-002',                       # Legiones Astartes: Maximus Battle Group — matched LI Battle Group
    'AL-020',                       # Saturnine Praetor — matched Saturnine Terminator Squad
    'AL-027',                       # Scimitar Jetbike Squadron — matched Sky-Hunter Squadron
    'AL-037',                       # Contemptor Dreadnought Weapons Frame 1 — matched Frame 2
    'AL-045',                       # Araknae Quad Accelerator Platform — not found
    'AL-046',                       # Disintegrator Weapons Upgrade Set — matched Melee Weapons Set
    'AL-061',                       # Leviathan Siege Dreadnought Close Combat Weapons — matched Ranged Frame
    'CM-003',                       # Vultarax Stratos-Automata — matched Skitarii Corpus
    'CM-016',                       # Age of Darkness Knight Questoris — matched Cerastus Knight Castigator
}
# ─────────────────────────────────────────────────────────────────────────────

_CALL_DELAY = 1.1  # seconds between API calls — keeps us under 1 TPS


def _build_url(asin):
    """Build a clean affiliate URL from an ASIN."""
    tag = settings.AMAZON_ASSOCIATE_TAG
    return f'https://www.amazon.com/dp/{asin}?tag={tag}'


def _best_new_price(item):
    """Extract the first new-condition listing price from a SearchItems result."""
    listings = item.get('offersV2', {}).get('listings', [])
    for listing in listings:
        if listing.get('condition', {}).get('value', 'New') != 'New':
            continue
        amount = listing.get('price', {}).get('money', {}).get('amount')
        if amount is not None:
            return float(amount)
    return None


class Command(BaseCommand):
    """Find Amazon URLs for products with no URL. Dry-run by default."""

    help = (
        'Search Amazon for products with no URL. '
        'Shows a chart of findings. Use --apply to write to DB.'
    )

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            '--faction',
            help='Faction slug (e.g. necrons, space-marines)',
        )
        group.add_argument(
            '--category',
            help='Category slug (e.g. horus-heresy, kill-team, blood-bowl)',
        )
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Write found URLs to the database (default: dry run only)',
        )
        parser.add_argument(
            '--no-brand-filter',
            action='store_true',
            help='Search without brand="Games Workshop" filter',
        )

    def handle(self, *args, **options):
        applying = options['apply']
        use_brand = not options['no_brand_filter']

        try:
            amazon_retailer = Retailer.objects.get(slug='amazon')
        except Retailer.DoesNotExist:
            self.stderr.write(self.style.ERROR('Amazon retailer not found in DB.'))
            return

        # ── Resolve faction or category ───────────────────────────────────────
        if options['faction']:
            faction_slug = options['faction'].strip()
            try:
                faction = Faction.objects.get(slug=faction_slug)
            except Faction.DoesNotExist:
                self.stderr.write(self.style.ERROR(f'Faction "{faction_slug}" not found.'))
                return
            scope_label = f'Faction: {faction.name}'
            all_products = list(faction.products.filter(is_active=True).order_by('name'))
            has_url = set(
                CurrentPrice.objects
                .filter(retailer=amazon_retailer, product__faction=faction)
                .exclude(url='').exclude(url__isnull=True)
                .values_list('product_id', flat=True)
            )
        else:
            category_slug = options['category'].strip()
            try:
                category = Category.objects.get(slug=category_slug)
            except Category.DoesNotExist:
                # List available category slugs to help the user
                slugs = list(Category.objects.order_by('name').values_list('slug', 'name'))
                self.stderr.write(self.style.ERROR(f'Category "{category_slug}" not found.'))
                self.stderr.write('Available categories:')
                for slug, name in slugs:
                    self.stderr.write(f'  {slug:<35} ({name})')
                return
            scope_label = f'Category: {category.name}'
            all_products = list(
                Product.objects.filter(category=category, is_active=True).order_by('name')
            )
            has_url = set(
                CurrentPrice.objects
                .filter(retailer=amazon_retailer, product__category=category)
                .exclude(url='').exclude(url__isnull=True)
                .values_list('product_id', flat=True)
            )

        # Candidates: products with no Amazon URL
        candidates = [p for p in all_products if p.id not in has_url]
        skipped_count = len(all_products) - len(candidates)

        self.stdout.write(
            f'\n{scope_label}'
            f'\nMode     : {"APPLY — writing to DB" if applying else "DRY RUN — nothing will be written"}'
            f'\nBrand    : {"Games Workshop" if use_brand else "none"}'
            f'\nHave URL : {skipped_count} (skipped)'
            f'\nNo URL   : {len(candidates)} (will search)'
        )

        if not candidates:
            self.stdout.write(self.style.SUCCESS(
                f'\nAll {len(all_products)} products already have Amazon URLs. Nothing to do.\n'
            ))
            return

        brand = 'Games Workshop' if use_brand else None
        client = AmazonCreatorsClient()

        # ── Search phase ──────────────────────────────────────────────────────
        found = []      # (product, asin, amazon_title, api_price, source)
        not_found = []  # products where search returned nothing

        for idx, product in enumerate(candidates):
            if idx > 0:
                time.sleep(_CALL_DELAY)

            # Explicitly skipped — no Amazon URL wanted for this product
            if product.gw_sku in SKIP_SKUS:
                not_found.append(product)
                continue

            # Check for manual override first
            if product.gw_sku in ASIN_OVERRIDES:
                asin = ASIN_OVERRIDES[product.gw_sku]
                found.append((product, asin, '(override — not searched)', None, 'OVERRIDE'))
                continue

            search_term = product.ebay_search_name or product.name
            try:
                items = client.search_items(
                    keywords=search_term,
                    marketplace='www.amazon.com',
                    brand=brand,
                    item_count=1,
                )
            except Exception as exc:
                detail = ''
                if hasattr(exc, 'response') and exc.response is not None:
                    try:
                        detail = str(exc.response.json())
                    except Exception:
                        detail = exc.response.text[:120]
                self.stderr.write(self.style.ERROR(
                    f'  API error for "{product.name}": {exc}'
                    + (f'\n  Detail: {detail}' if detail else '')
                ))
                not_found.append(product)
                continue

            if not items:
                not_found.append(product)
                continue

            top = items[0]
            asin = top.get('asin', '')
            amazon_title = top.get('itemInfo', {}).get('title', {}).get('displayValue', '—')
            api_price = _best_new_price(top)

            if not asin:
                not_found.append(product)
                continue

            found.append((product, asin, amazon_title, api_price, 'API'))

        # ── Report ────────────────────────────────────────────────────────────
        self.stdout.write('')

        if found:
            self.stdout.write(
                f'{"#":<4} {"Product Name":<45} {"ASIN":<12} {"Price":>8}  {"Src":<8}  Amazon Title'
            )
            self.stdout.write('─' * 145)

            for i, (product, asin, amazon_title, api_price, source) in enumerate(found, 1):
                price_str = f'${api_price:.2f}' if api_price is not None else '—'
                src_style = self.style.WARNING if source == 'OVERRIDE' else self.style.SUCCESS
                self.stdout.write(src_style(
                    f'{i:<4} {product.name[:44]:<45} {asin:<12} {price_str:>8}  {source:<8}  {amazon_title}'
                ))

        # ── Apply ─────────────────────────────────────────────────────────────
        if applying and found:
            self.stdout.write('')
            written = 0
            for product, asin, amazon_title, api_price, source in found:
                url = _build_url(asin)
                cp, created = CurrentPrice.objects.get_or_create(
                    retailer=amazon_retailer,
                    product=product,
                    defaults={
                        'url':           url,
                        'price':         api_price,
                        'in_stock':      api_price is not None,
                        'not_available': api_price is None,
                    },
                )
                if not created:
                    # Record exists but had no URL — update URL only
                    cp.url = url
                    cp.save(update_fields=['url'])
                written += 1
                self.stdout.write(f'  {"Created" if created else "Updated"}: {product.name} → {url}')
            self.stdout.write(self.style.SUCCESS(f'\n{written} URL(s) written to database.'))

        # ── Summary ───────────────────────────────────────────────────────────
        self.stdout.write('\n' + '─' * 50)
        self.stdout.write(self.style.SUCCESS(f'  Found via API    : {sum(1 for *_, s in found if s == "API")}'))
        self.stdout.write(self.style.WARNING(f'  From overrides   : {sum(1 for *_, s in found if s == "OVERRIDE")}'))
        self.stdout.write(self.style.WARNING(f'  Still no URL     : {len(not_found)}'))
        if not_found:
            for p in not_found:
                self.stdout.write(f'    - {p.name}')

        if not applying:
            self.stdout.write(self.style.WARNING(
                '\nDry run complete. Review the chart above, add any overrides to '
                'ASIN_OVERRIDES in this file,\nthen re-run with --apply to write to the database.\n'
            ))
        else:
            self.stdout.write('')
