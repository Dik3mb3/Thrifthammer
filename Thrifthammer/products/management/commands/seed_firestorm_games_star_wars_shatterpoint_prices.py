"""
Seed Firestorm Games UK prices for Star Wars: Shatterpoint.

Idempotent -- CurrentPrice rows are written via update_or_create keyed on
(product, retailer), so re-running is always safe. NEVER writes msrp_gbp --
Firestorm is a discount competitor, not the MSRP source. Only
games-workshop-uk / seed_asmodee_uk_star_wars_shatterpoint_prices write
that field for this category.

Price parsing rule: Firestorm shows two numbers per listing (struck-through
RRP, then sale price). ALWAYS use the lower (sale) price, never the RRP.
RRP is only used as a matching aid to confirm which DB SKU a listing
corresponds to (it should equal Product.msrp_gbp for the matched SKU).

https://www.firestormgames.co.uk/wargames-miniatures/star-wars-shatterpoint
48/52 active DB SWS-XXX SKUs matched -- most Squad Pack names on
Firestorm include the character name in parentheses (e.g. "Hello There
(General Kenobi Squad Pack)") where the DB name uses a colon form
("Hello There: General Obi-Wan Kenobi Squad Pack") -- same products,
matched by the shared unique phrase plus price.

Roughly half the catalog (SWS-001, 002, 007-009, 014, 015, 020, 021,
023-025, 027-030, 038, 041-043, 049-052) has null msrp_gbp in the DB
(not yet synced by GW/Asmodee UK) -- most of these were matched anyway
using the Firestorm listing as the sole confirmation, since the DB name
uniquely identifies the squad pack (flagged here rather than silently
assumed).

Two same-priced "Dice Pack" / "Measuring Tools" listings exist twice on
Firestorm (once as "... OLD" / "Range and Movement Tools", once current)
-- the current-named listing was used for SWS-045 / SWS-048; the stale
duplicates were left unused.

Excluded (no DB counterpart): Triple Bundle - Imperial/Scoundrels
(multi-pack bundles), all "Blotz - Crashed ship" terrain pieces and
"Sci-fi Splinter's Terminal" (third-party terrain, not GW), "Cog'O'Two -
Armada, Command" (accessory, unrelated).

Gaps (4, no Firestorm listing found under any name):
- SWS-001 I Am No Jedi Deluxe Duel Pack (null msrp) -- distinct from
  SWS-019 "I Am No Jedi Duel Pack" (no "Deluxe"), which is matched
- SWS-010 Stronger Than Fear Squad Pack (msrp £49.99)
- SWS-027 Fistful of Credits: Cad Bane Squad Pack (null msrp)
- SWS-052 High Ground Terrain Pack (null msrp)
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_FIRESTORM_SLUG = 'firestorm-games'
_BASE = 'https://www.firestormgames.co.uk'
_AFF = '?aff=6a4ab07d1c6f9'

# (gw_sku, label, gbp_price, path)
_PRICES = [
    ('SWS-002', 'Star Wars Shatterpoint: Fear and Dead Men (Darth Vader Squad Pack)', Decimal('42.49'), '/star-wars-shatterpoint:-fear-and-dead-men-darth-vader-squad-pack-'),
    ('SWS-003', 'Star Wars Shatterpoint: Delta Force Form Up', Decimal('39.99'), '/star-wars-shatterpoint:-delta-force-form-up'),
    ('SWS-004', 'Star Wars Shatterpoint: All The Way Squad Pack', Decimal('42.49'), '/star-wars-shatterpoint:-all-the-way-squad-pack'),
    ('SWS-005', 'Star Wars Shatterpoint: Certified Guild (The Mandalorian Squad Pack)', Decimal('39.99'), '/star-wars-shatterpoint:-certified-guild-the-mandalorian-squad-pack-'),
    ('SWS-006', 'Star Wars Shatterpoint: Deploy the Garrison Squad Pack', Decimal('47.99'), '/star-wars-shatterpoint:-deploy-the-garrison-squad-pack'),
    ('SWS-007', 'Star Wars Shatterpoint: Make The Impossible Possible (Hera Syndulla Squad Pack)', Decimal('42.49'), '/star-wars-shatterpoint:-make-the-impossible-possible-hera-syndulla-squad-pack-'),
    ('SWS-008', 'Star Wars Shatterpoint: Lead by Example (Plo Kloon Squad Pack)', Decimal('50.99'), '/star-wars-shatterpoint:-lead-by-example-plo-kloon-squad-pack-'),
    ('SWS-009', 'Star Wars Shatterpoint: Fearless and Inventive (Jedi Luke Skywalker Squad Pack)', Decimal('34.99'), '/star-wars-shatterpoint:-fearless-and-inventive-jedi-luke-skywalker-squad-pack-'),
    ('SWS-011', 'Star Wars Shatterpoint: First Contact Mission Pack', Decimal('11.24'), '/star-wars-shatterpoint:-first-contact-mission-pack'),
    ('SWS-012', 'Star Wars Shatterpoint: Never Tell Me The Odds Mission Pack', Decimal('16.99'), '/star-wars-shatterpoint:-never-tell-me-the-odds-mission-pack'),
    ('SWS-013', 'Star Wars Shatterpoint: You Have Something I Want (Moff Gideon Squad Pack)', Decimal('42.49'), '/star-wars-shatterpoint:-you-have-something-i-want-moff-gideon-squad-pack-'),
    ('SWS-014', 'Star Wars Shatterpoint: Sabotage Showdown Mission Pack', Decimal('12.74'), '/star-wars-shatterpoint:-sabotage-showdown-mission-pack'),
    ('SWS-015', 'Star Wars Shatterpoint: This is Rogue One', Decimal('42.49'), '/star-wars-shatterpoint:-this-is-rogue-one'),
    ('SWS-016', "Star Wars Shatterpoint: We Don't Need Their Scum Unit Pack", Decimal('42.49'), '/star-wars-shatterpoint:-we-dont-need-their-scum-unit-pack'),
    ('SWS-017', 'Star Wars Shatterpoint: This Is the Way Squad Pack', Decimal('42.49'), '/star-wars-shatterpoint:-this-is-the-way-squad-pack'),
    ('SWS-018', 'Star Wars Shatterpoint: Yub Nub (Logray Squad Pack)', Decimal('47.99'), '/star-wars-shatterpoint:-yub-nub-logray-squad-pack-'),
    ('SWS-019', 'Star Wars Shatterpoint: I am no Jedi Duel Pack', Decimal('33.99'), '/star-wars-shatterpoint:-i-am-no-jedi-duel-pack'),
    ('SWS-020', 'Star Wars Shatterpoint: Today the Rebellion Dies Squad Pack', Decimal('50.99'), '/star-wars-shatterpoint:-today-the-rebellion-dies-squad-pack'),
    ('SWS-021', 'Star Wars Shatterpoint: Hello There (General Kenobi Squad Pack)', Decimal('42.49'), '/star-wars-shatterpoint:-hello-there-general-kenobi-squad-pack'),
    ('SWS-022', 'Star Wars Shatterpoint: Twice the Pride (Count Dooku Squad Pack)', Decimal('42.49'), '/star-wars-shatterpoint:-twice-the-pride-count-dooku-squad-pack'),
    ('SWS-023', "Star Wars Shatterpoint: This Party's Over (Mace Windu)", Decimal('39.99'), '/star-wars-shatterpoint:-this-partys-over-mace-windu-'),
    ('SWS-024', 'Star Wars Shatterpoint: Witches of Dathomir (Mother Talzin) Squad Pack', Decimal('39.99'), '/star-wars-shatterpoint:-witches-of-dathomir-mother-talzin-squad-pack'),
    ('SWS-025', 'Star Wars Shatterpoint: Jedi Hunters (Grand Inquisitor Squad Pack)', Decimal('42.49'), '/star-wars-shatterpoint:-jedi-hunters-grand-inquisitor-squad-pack'),
    ('SWS-026', 'Star Wars Shatterpoint: We Are Brave Squad Pack', Decimal('34.99'), '/star-wars-shatterpoint:-we-are-brave-squad-pack'),
    ('SWS-028', 'Star Wars Shatterpoint: You Cannot Run Duel Pack', Decimal('71.99'), '/star-wars-shatterpoint:-you-cannot-run-duel-pack'),
    ('SWS-029', 'Star Wars Shatterpoint: Plans and Preparations (General Luminara Unduli Squad Pack)', Decimal('42.49'), '/star-wars-shatterpoint:-plans-and-preparations-general-luminara-unduli-squad-pack'),
    ('SWS-030', 'Star Wars Shatterpoint: Take Cover Terrain Pack', Decimal('56.24'), '/star-wars-shatterpoint:-take-cover-terrain-pack'),
    ('SWS-032', 'Star Wars Shatterpoint: Secure The Future Squad Pack', Decimal('42.49'), '/star-wars-shatterpoint:-secure-the-future-squad-pack'),
    ('SWS-033', 'Star Wars Shatterpoint: Requesting Your Surrender', Decimal('47.99'), '/star-wars-shatterpoint:-requesting-your-surrender'),
    ('SWS-034', 'Star Wars Shatterpoint: Wisdom of the Council', Decimal('39.99'), '/star-wars-shatterpoint:-wisdom-of-the-council'),
    ('SWS-035', 'Star Wars Shatterpoint: Real Quiet Like Squad Pack', Decimal('42.49'), '/star-wars-shatterpoint:-real-quiet-like-squad-pack'),
    ('SWS-036', 'Star Wars Shatterpoint: My Loyalty, My Life Squad Pack', Decimal('42.49'), '/star-wars-shatterpoint:-my-loyalty-my-life-squad-pack'),
    ('SWS-037', 'Star Wars Shatterpoint: Terror From Below', Decimal('39.99'), '/star-wars-shatterpoint:-terror-from-below'),
    ('SWS-038', 'Star Wars Shatterpoint: Ee Chee Wa Maa! (Leia and Ewoks Squad Pack)', Decimal('50.99'), '/star-wars-shatterpoint:-ee-chee-wa-maa-leia-and-ewoks-squad-pack-'),
    ('SWS-039', 'Star Wars Shatterpoint: Not Accepting Surrenders Squad Pack', Decimal('42.49'), '/star-wars-shatterpoint:-not-accepting-surrenders-squad-pack'),
    ('SWS-040', 'Star Wars Shatterpoint: This is Some Rescue (Princess Leia Squad Pack)', Decimal('39.99'), '/star-wars-shatterpoint:-this-is-some-rescue-princess-leia-squad-pack-'),
    ('SWS-041', "Star Wars Shatterpoint: That's Good Business Squad Pack", Decimal('32.49'), '/star-wars-shatterpoint:-thats-good-business-squad-pack'),
    ('SWS-042', 'Star Wars Shatterpoint: Strategic Positions Mission Card Pack', Decimal('12.74'), '/star-wars-shatterpoint:-strategic-positions-mission-card-pack'),
    ('SWS-043', 'Star Wars Shatterpoint: Maximum Firepower Squad Pack', Decimal('42.49'), '/star-wars-shatterpoint:-maximum-firepower-squad-pack'),
    ('SWS-044', 'Star Wars Shatterpoint: Core Set', Decimal('131.99'), '/star-wars-shatterpoint:-core-set-'),
    ('SWS-045', 'Star Wars Shatterpoint: Dice Pack', Decimal('7.50'), '/star-wars-shatterpoint:-dice-pack'),
    ('SWS-046', 'Star Wars Shatterpoint: Good Soldiers Follow Orders Squad Pack', Decimal('39.99'), '/star-wars-shatterpoint:-good-soldiers-follow-orders-squad-pack'),
    ('SWS-047', 'Star Wars Shatterpoint: Outer Rim Outpost Terrain Pack', Decimal('39.99'), '/star-wars-shatterpoint:-outer-rim-outpost-terrain-pack'),
    ('SWS-048', 'Star Wars Shatterpoint: Measuring Tools', Decimal('11.24'), '/star-wars-shatterpoint:-measuring-tools'),
    ('SWS-049', 'Star Wars Shatterpoint: Appetite for Destruction (General Grievous Squad Pack)', Decimal('42.49'), '/star-wars-shatterpoint:-appetite-for-destruction-general-grievous-squad-pack'),
    ('SWS-050', 'Star Wars Shatterpoint: What Have We Here Squad Pack', Decimal('39.99'), '/star-wars-shatterpoint:-what-have-we-here-squad-pack'),
    ('SWS-051', 'Star Wars Shatterpoint: Maintenance Bay Terrain Pack', Decimal('63.74'), '/star-wars-shatterpoint:-maintenance-bay-terrain-pack'),
    ('SWS-053', 'Star Wars Shatterpoint: Clone Force 99 (Bad Batch Squad Pack)', Decimal('50.99'), '/star-wars-shatterpoint:-clone-force-99-bad-batch-squad-pack'),
]


class Command(BaseCommand):
    help = 'Seed Firestorm Games UK prices for Star Wars: Shatterpoint. Idempotent.'

    def handle(self, *args, **options):
        retailer, created = Retailer.objects.get_or_create(
            slug=_FIRESTORM_SLUG,
            defaults={
                'name': 'Firestorm Games',
                'website': f'{_BASE}/{_AFF}',
                'country': 'UK',
                'is_active': True,
                'is_uk': True,
            },
        )
        if created:
            self.stdout.write(f'Created retailer: {retailer.name}')

        seeded = 0
        skipped = 0
        for sku, label, gbp_price, path in _PRICES:
            url = f'{_BASE}{path}{_AFF}'
            products = list(Product.objects.filter(gw_sku=sku))
            if not products:
                self.stderr.write(f'SKIP — SKU {sku} ({label}) not in DB')
                skipped += 1
                continue

            for product in products:
                CurrentPrice.objects.update_or_create(
                    product=product,
                    retailer=retailer,
                    defaults={
                        'price': gbp_price,
                        'currency': 'GBP',
                        'url': url,
                        'in_stock': True,
                        'not_available': False,
                    },
                )
                seeded += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded {seeded} Firestorm Games Star Wars: Shatterpoint prices. Skipped: {skipped}.'
            )
        )
