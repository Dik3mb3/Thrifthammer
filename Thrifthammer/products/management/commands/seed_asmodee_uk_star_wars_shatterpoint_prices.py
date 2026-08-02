"""
Seed Asmodee UK prices for Star Wars: Shatterpoint.

Reuses the `asmodee-uk` Retailer created by
seed_asmodee_uk_star_wars_legion_prices.py (is_uk=True) -- get_or_create
here is just the standard idempotent guard, not a second onboarding.

Only 27 real product rows existed in the source UK sheet (the rest were
£0.00 store/tournament-kit placeholder rows, excluded). Of those, 25
matched cleanly by name; the sheet's "I am no Jedi Duel Pack" and "This
Is the Way Squad Pack" rows do NOT cover SWS-001 (Deluxe variant) or
SWS-015 (Rogue One variant) -- those remain unmatched, consistent with
populate_star_wars_shatterpoint_products.py's own note that SWS-001 has
no listing on any retailer. 3 further products (SWS-003, SWS-044,
SWS-048) were confirmed via direct user-provided links, one of which
(SWS-044, Core Set) was fetched live since it wasn't in the source sheet.

24 products have no UK price and are intentionally excluded (no
msrp_gbp, no CurrentPrice): SWS-001, SWS-002, SWS-007, SWS-008, SWS-009,
SWS-014, SWS-015, SWS-020, SWS-021, SWS-023, SWS-024, SWS-025, SWS-027,
SWS-028, SWS-029, SWS-030, SWS-038, SWS-041, SWS-042, SWS-043, SWS-049,
SWS-050, SWS-051, SWS-052.

Run once on Railway startup via Procfile. Safe to re-run — idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_ASMODEE_UK_SLUG = 'asmodee-uk'

# (sku, label, gbp_price, uk_url)
_PRICES = [
    ('SWS-003', 'Star Wars: Shatterpoint - Delta Squad, Form Up Squad Pack', Decimal('49.99'),
     'https://www.asmodee.co.uk/products/amgswp62-star-wars-shatterpoint-delta-force-form-up'),
    ('SWS-004', 'Star Wars: Shatterpoint - All the Way Squad Pack', Decimal('49.99'),
     'https://www.asmodee.co.uk/products/amgswp31-star-wars-shatterpoint-all-the-way-squad-pack'),
    ('SWS-005', 'Star Wars: Shatterpoint - Certified Guild Squad Pack', Decimal('49.99'),
     'https://www.asmodee.co.uk/products/ffgswp24-certified-guild-the-mandalorian-squad-pack-star-wars-shatterpoint-certified-guild'),
    ('SWS-006', 'Star Wars: Shatterpoint - Deploy the Garrison Squad Pack', Decimal('59.99'),
     'https://www.asmodee.co.uk/products/amgswp51-star-wars-shatterpoint-deploy-the-garrison-squad-pack'),
    ('SWS-010', 'Star Wars: Shatterpoint - Stronger Than Fear Squad Pack', Decimal('49.99'),
     'https://www.asmodee.co.uk/products/ffgswp29-stronger-than-fear-kanan-jarrus-squad-pack-star-wars-shatterpoint'),
    ('SWS-011', 'Star Wars: Shatterpoint - First Contact Mission Pack', Decimal('14.99'),
     'https://www.asmodee.co.uk/products/amgswp49-star-wars-shatterpoint-first-contact-mission-pack'),
    ('SWS-012', 'Star Wars: Shatterpoint - Never Tell Me the Odds Mission Pack', Decimal('19.99'),
     'https://www.asmodee.co.uk/products/ffgswp48-star-wars-shatterpoint-never-tell-me-the-odds-mission-pack'),
    ('SWS-013', 'Star Wars: Shatterpoint - You Have Something I Want Squad Pack', Decimal('49.99'),
     'https://www.asmodee.co.uk/products/ffgswp26-star-wars-shatterpoint-you-have-something-i-want'),
    ('SWS-016', 'Star Wars: Shatterpoint - We Don\'t Need Their Scum Unit Pack', Decimal('49.99'),
     'https://www.asmodee.co.uk/products/amgswp25-star-wars-shatterpoint-we-don-t-need-their-scum-squad-pack'),
    ('SWS-017', 'Star Wars: Shatterpoint - This Is The Way Squad Pack', Decimal('49.99'),
     'https://www.asmodee.co.uk/products/amgswp16-star-wars-shatterpoint-this-is-the-way-squad-pack'),
    ('SWS-018', 'Star Wars: Shatterpoint - Yub Nub Squad Pack', Decimal('59.99'),
     'https://www.asmodee.co.uk/products/ffgswp39-star-wars-shatterpoint-yub-nub'),
    ('SWS-019', 'Star Wars: Shatterpoint - I Am No Jedi Duel Pack', Decimal('39.99'),
     'https://www.asmodee.co.uk/products/amgswp42-star-wars-shatterpoint-i-am-no-jedi-duel-pack'),
    ('SWS-022', 'Star Wars: Shatterpoint - Twice the Pride: Count Dooku Squad Pack', Decimal('49.99'),
     'https://www.asmodee.co.uk/products/ffgswp03-star-wars-shatterpoint-twice-the-pride-count-dooku-squad-pack'),
    ('SWS-026', 'Star Wars: Shatterpoint - We Are Brave: Squad Pack', Decimal('49.99'),
     'https://www.asmodee.co.uk/products/ffgswp15-star-wars-shatterpoint-we-are-brave-padme-amidala-squad-pack'),
    ('SWS-032', 'Star Wars: Shatterpoint - Secure the Future Squad Pack', Decimal('49.99'),
     'https://www.asmodee.co.uk/products/amgswp82-star-wars-shatterpoint-secure-the-future-squad-pack'),
    ('SWS-033', 'Star Wars: Shatterpoint - Requesting Your Surrender Squad Pack', Decimal('59.99'),
     'https://www.asmodee.co.uk/products/ffgswp37-star-wars-shatterpoint-requesting-your-surrender'),
    ('SWS-034', 'Star Wars: Shatterpoint - Wisdom of the Council Squad Pack', Decimal('49.99'),
     'https://www.asmodee.co.uk/products/ffgswp50-star-wars-shatterpoint-wisdom-of-the-council'),
    ('SWS-035', 'Star Wars: Shatterpoint - Real Quiet Like Squad Pack', Decimal('49.99'),
     'https://www.asmodee.co.uk/products/ffgswp35-star-wars-shatterpoint-real-quiet-like-squad-pack'),
    ('SWS-036', 'Star Wars: Shatterpoint - My Loyalty, My Life Squad Pack', Decimal('49.99'),
     'https://www.asmodee.co.uk/products/amgswp83-star-wars-shatterpoint-my-loyalty-my-life-squad-pack'),
    ('SWS-037', 'Star Wars: Shatterpoint - Terror From Below Squad Pack', Decimal('49.99'),
     'https://www.asmodee.co.uk/products/amgswp63-star-wars-shatterpoint-terror-from-below'),
    ('SWS-039', 'Star Wars: Shatterpoint - Not Accepting Surrenders Squad Pack', Decimal('49.99'),
     'https://www.asmodee.co.uk/products/amgswp28-star-wars-shatterpoint-not-accepting-surrenders-squad-pack'),
    ('SWS-040', 'Star Wars: Shatterpoint - This is Some Rescue! Squad Pack', Decimal('49.99'),
     'https://www.asmodee.co.uk/products/amgswp41-star-wars-shatterpoint-this-is-some-rescue'),
    ('SWS-044', 'Star Wars: Shatterpoint Core Set', Decimal('164.99'),
     'https://www.asmodee.co.uk/products/ffgswp01-star-wars-shatterpoint-core-set'),
    ('SWS-045', 'Star Wars: Shatterpoint - Dice Pack', Decimal('14.99'),
     'https://www.asmodee.co.uk/products/ffgswp99-star-wars-shatterpoint-dice-pack'),
    ('SWS-046', 'Star Wars: Shatterpoint - Good Soldiers Follow Orders Squad Pack', Decimal('49.99'),
     'https://www.asmodee.co.uk/products/amgswp36-star-wars-shatterpoint-good-soldiers-follow-orders-squad-pack'),
    ('SWS-047', 'Star Wars: Shatterpoint - Outer Rim Outpost Terrain Pack', Decimal('49.99'),
     'https://www.asmodee.co.uk/products/amgswp60-star-wars-shatterpoint-outer-rim-outpost-terrain-pack'),
    ('SWS-048', 'Star Wars: Shatterpoint - Measuring Tools', Decimal('14.99'),
     'https://www.asmodee.co.uk/products/ffgswp100-star-wars-shatterpoint-range-and-movement-tools'),
    ('SWS-053', 'Star Wars: Shatterpoint - Clone Force 99 Squad Pack', Decimal('59.99'),
     'https://www.asmodee.co.uk/products/ffgswp38-star-wars-shatterpoint-clone-force-99'),
]


class Command(BaseCommand):
    help = 'Seed Asmodee UK prices and URLs for Star Wars: Shatterpoint. Idempotent.'

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
        for sku, label, gbp_price, url in _PRICES:
            try:
                product = Product.objects.get(gw_sku=sku)
            except Product.DoesNotExist:
                self.stderr.write(f'SKIP — SKU {sku} ({label}) not in DB')
                skipped += 1
                continue

            if product.msrp_gbp != gbp_price:
                product.msrp_gbp = gbp_price
                product.save(update_fields=['msrp_gbp'])

            CurrentPrice.objects.update_or_create(
                product=product,
                retailer=retailer,
                defaults={
                    'price': gbp_price,
                    'url': url,
                    'in_stock': True,
                    'not_available': False,
                },
            )
            seeded += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded {seeded} Star Wars: Shatterpoint Asmodee UK prices. Skipped: {skipped}.'
            )
        )
