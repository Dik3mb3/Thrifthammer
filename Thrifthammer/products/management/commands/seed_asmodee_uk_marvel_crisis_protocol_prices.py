"""
Seed Asmodee UK MSRP prices for Marvel Crisis Protocol.

Marvel Crisis Protocol is published by Atomic Mass Games (originally Fantasy
Flight Games) -- there is no games-workshop-uk listing for this category at
all, so product_detail's gw_ref_price (the "MSRP" reference line / discount
badge) falls through to product.msrp_gbp, which is None for every MCP-*
product unless set here. Asmodee UK (asmodee.co.uk) is this category's
confirmed MSRP source. So (create-only, same guard as every other UK
retailer) this command sets msrp_gbp from the Asmodee UK RRP the first time
it seeds a product. It never overwrites an already-set msrp_gbp.

Source: https://www.asmodee.co.uk/collections/marvel-crisis-protocol (15
miniatures-category listings, 1 page -- Asmodee UK carries a much smaller
slice of the line than the 73-product US catalog). Each match verified by
pairing product title text with its href directly via JS (not list
position), then cross-checked against Product.name.

10 of 15 Asmodee UK listings matched an existing catalog SKU. 5 did not,
and were NOT added as gaps here:
- "Midnight Sons Affiliation Pack" (GBP 64.99) -- no matching catalog SKU.
- "Marvel Crisis Protocol - Dani Moonstar, Jubilee, Multiple Man and Havok"
  (GBP 64.99) -- no matching catalog SKU.
- "Store Tournament Kit 2025 FOC" (GBP 0.00) -- a free promo item, not a
  real retail SKU, excluded regardless of match.
- "NYC Construction Site Terrain Expansion" (FFGMSG31, GBP 54.99) --
  confirmed via its Asmodee UK product page (construction-equipment
  terrain, released 2020) to be a GENUINELY DIFFERENT product from our
  catalog's MCP-071 "NYC City Block Terrain Collection" (a different
  Asmodee US slug entirely: nyc-city-block-terrain-collection vs
  nyc-construction-site-terrain-expansion). Not a rename -- a real gap.
- The second "Guardians of the Galaxy" listing in our catalog, MCP-024
  "Guardians of the Galaxy Starter Set", is simply not currently stocked
  by Asmodee UK (only the Affiliation Pack, MCP-025, is) -- not a mismatch,
  just no UK listing for that specific SKU.

One resolved ambiguity: Asmodee UK lists TWO separately-coded "Dice Pack"
products (both GBP 9.99) -- FFGMSG02 (2019 release, the original Fantasy
Flight Games-era pack) and AMGCP269 (2025 release, current Atomic Mass
Games-era pack). Our catalog has only one Dice Pack SKU, MCP-037. Matched
it to AMGCP269 as the current/active edition (confirmed via each page's
own Publisher Release Date); FFGMSG02 is the legacy listing and was left
unmatched. Flagged in case this call needs revisiting.

Run once on Railway startup via Procfile. Safe to re-run -- idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_ASMODEE_UK_SLUG = 'asmodee-uk'

# (gw_sku, gbp_price, url, in_stock)
_PRICES = [
    ('MCP-059', Decimal('149.99'), 'https://www.asmodee.co.uk/products/ffgcp143-marvel-crisis-protocol-earths-mightiest-core-set', True),
    ('MCP-010', Decimal('39.99'), 'https://www.asmodee.co.uk/products/ffgcp96-marvel-crisis-protocol-iceman-shadowcat', True),
    ('MCP-055', Decimal('44.99'), 'https://www.asmodee.co.uk/products/amgcp186-marvel-crisis-protocol-elsa-bloodstone-man-thing', True),
    ('MCP-056', Decimal('64.99'), 'https://www.asmodee.co.uk/products/ffgcp91-marvel-crisis-protocol-mighty-thor-lady-sif-thor-hero-of-midgard-loki-prince-of-lies', True),
    ('MCP-008', Decimal('39.99'), 'https://www.asmodee.co.uk/products/ffgcp112-bishop-and-nightcrawler-marvel-crisis-protocol', True),
    ('MCP-014', Decimal('44.99'), 'https://www.asmodee.co.uk/products/amgca13-marvel-crisis-protocol-war-of-kings-crisis-card-pack', True),
    ('MCP-063', Decimal('39.99'), 'https://www.asmodee.co.uk/products/ffgcp69-marvel-crisis-protocol-shang-chi-silver-sable', True),
    ('MCP-037', Decimal('9.99'), 'https://www.asmodee.co.uk/products/amgcp269-marvel-crisis-protocol-dice-pack', True),
    ('MCP-028', Decimal('59.99'), 'https://www.asmodee.co.uk/products/amgcp223-marvel-crisis-protocol-galaxys-deadliest-affiliation-pack', True),
    ('MCP-025', Decimal('64.99'), 'https://www.asmodee.co.uk/products/amgcp222-marvel-crisis-protocol-guardians-of-the-galaxy-affiliation-pack', True),
]


class Command(BaseCommand):
    help = 'Seed Asmodee UK MSRP prices and URLs for Marvel Crisis Protocol. Idempotent.'

    def handle(self, *args, **options):
        retailer, created = Retailer.objects.get_or_create(
            slug=_ASMODEE_UK_SLUG,
            defaults={
                'name': 'Asmodee UK',
                'website': 'https://www.asmodee.co.uk',
                'country': 'UK',
                'is_active': True,
                'is_uk': True,
            },
        )
        if created:
            self.stdout.write(f'Created retailer: {retailer.name}')

        seeded = 0
        skipped = 0
        for gw_sku, gbp_price, url, in_stock in _PRICES:
            try:
                product = Product.objects.get(gw_sku=gw_sku)
            except Product.DoesNotExist:
                self.stderr.write(f'SKIP — SKU {gw_sku} not in DB')
                skipped += 1
                continue

            if product.msrp_gbp is None:
                product.msrp_gbp = gbp_price
                product.save(update_fields=['msrp_gbp'])

            cp_defaults = {'url': url, 'in_stock': in_stock, 'not_available': False, 'currency': 'GBP'}
            CurrentPrice.objects.update_or_create(
                product=product,
                retailer=retailer,
                defaults=cp_defaults,
                create_defaults={**cp_defaults, 'price': gbp_price},
            )
            seeded += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded {seeded} Marvel Crisis Protocol Asmodee UK prices. Skipped: {skipped}.'
            )
        )
