"""
Seed Firestorm Games UK prices for Marvel: Crisis Protocol.

Idempotent -- CurrentPrice rows are written via update_or_create keyed on
(product, retailer), so re-running is always safe. NEVER writes msrp_gbp --
Firestorm is a discount competitor, not the MSRP source. No GBP MSRP
source exists yet for this category (msrp_gbp was null for all 73 DB
SKUs going in), so matching was done entirely by name.

Price parsing rule: Firestorm shows two numbers per listing (struck-through
RRP, then sale price). ALWAYS use the lower (sale) price.

https://www.firestormgames.co.uk/wargames-miniatures/marvel-crisis-protocol
65/73 active DB MCP-XXX SKUs matched.

Legacy duplicate-SKU pair (two DB SKUs for the same physical Firestorm
listing, same pattern seen in Horus Heresy/Star Wars Legion this
session): MCP-036 "Movement & Range Tool Pack" and MCP-048 "Movement &
Range Tools" share the single "Range and Movement Tools" listing.

Matched despite minor name differences (verified by price + distinctive
character/title match, not a literal string match): MCP-057 "Valkyrie
on Elendil & Warriors Three" matched to Firestorm's "Valkyrie on Aragon
& Warriors Three" -- the DB's mount name differs from Firestorm's, but
"Valkyrie ... & Warriors Three" is otherwise unique and price-identical;
MCP-028 "The Galaxy's Deadliest Character Pack" matched to Firestorm's
"Galaxy's Deadliest Affiliation Pack" -- pack-type label differs
(Character vs Affiliation) but the title and price are identical and no
other DB SKU is named "Galaxy's Deadliest".

Gaps (8, no Firestorm listing found under any name):
- MCP-008 Bishop & Nightcrawler
- MCP-013 Monsters Unleashed Character Pack
- MCP-031 Dark Future Terrain Pack
- MCP-032 Shrine to En Sabah Nur Terrain Pack
- MCP-040 Battle for Asgard Terrain Pack
- MCP-045 Icons of Bast Terrain Pack
- MCP-049 Kingdom of Wakanda Terrain Pack
- MCP-067 Onslaught
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
    ('MCP-001', 'Marvel Crisis Protocol: X-Men Starter Set', Decimal('71.99'), '/marvel-crisis-protocol:-x-men-starter-set'),
    ('MCP-002', 'Marvel Crisis Protocol: Bastion, Nimrod & Omega Sentinel', Decimal('51.99'), '/marvel-crisis-protocol:-bastion-nimrod--omega-sentinel'),
    ('MCP-003', 'Marvel Crisis Protocol: Prowler, Spider-Man 2099 & Ultimate Spider-Man', Decimal('39.99'), '/marvel-crisis-protocol:-prowler-spider-man-2099--ultimate-spider-man'),
    ('MCP-004', 'Marvel Crisis Protocol: Phoenix & Phoenix Unleashed', Decimal('43.99'), '/marvel-crisis-protocol:-phoenix--phoenix-unleashed'),
    ('MCP-005', 'Marvel Crisis Protocol: Spider-Foes Starter Set', Decimal('71.99'), '/marvel-crisis-protocol:-spider-foes-starter-set'),
    ('MCP-006', 'Marvel Crisis Protocol: Silk, Spider-Ham & Spider-Noir', Decimal('39.99'), '/marvel-crisis-protocol:-silk-spider-ham--spider-noir'),
    ('MCP-007', 'Marvel Crisis Protocol: Operation: Zero Tolerance Crisis Card Pack', Decimal('35.99'), '/marvel-crisis-protocol:-operation:-zero-tolerance-crisis-card-pack'),
    ('MCP-009', 'Marvel Crisis Protocol: Iron Lad, Iron Monger, Kang The Conqueror & Rescue', Decimal('47.99'), '/marvel-crisis-protocol:-iron-lad-iron-monger-kang-the-conqueror--rescue'),
    ('MCP-010', 'Marvel Crisis Protocol: Iceman & Shadowcat', Decimal('31.99'), '/marvel-crisis-protocol:-iceman--shadowcat'),
    ('MCP-011', 'Marvel Crisis Protocol - Adam Warlock, Moondragon, Quasar Character Pack', Decimal('47.99'), '/marvel-crisis-protocol---adam-warlock-moondragon-quasar-character-pack'),
    ('MCP-012', 'Marvel Crisis Protocol: Apocalypse', Decimal('55.99'), '/marvel-crisis-protocol:-apocalypse'),
    ('MCP-014', 'Marvel Crisis Protocol: War of Kings Crisis Card Pack', Decimal('35.99'), '/marvel-crisis-protocol:-war-of-kings-crisis-card-pack'),
    ('MCP-015', 'Marvel Crisis Protocol: Xavier’s Students Affiliation Pack', Decimal('51.99'), '/marvel-crisis-protocol:-xaviers-students-affiliation-pack'),
    ('MCP-016', 'Marvel Crisis Protocol: Web-Swinging Heroes', Decimal('47.99'), '/marvel-crisis-protocol:-web-swinging-heroes'),
    ('MCP-017', 'Marvel Crisis Protocol: Professor X & Shadow King', Decimal('35.99'), '/marvel-crisis-protocol:-professor-x--shadow-king'),
    ('MCP-018', 'Marvel Crisis Protocol: Angel & Archangel', Decimal('35.99'), '/marvel-crisis-protocol:-angel--archangel'),
    ('MCP-019', 'Marvel Crisis Protocol: Avalanche, Exodus & Lady Mastermind', Decimal('39.99'), '/marvel-crisis-protocol:-avalanche-exodus--lady-mastermind'),
    ('MCP-020', 'Marvel Crisis Protocol: Echo, Ronin & Tigra', Decimal('39.99'), '/marvel-crisis-protocol:-echo-ronin--tigra'),
    ('MCP-021', 'Marvel Crisis Protocol: Abomination & Wrecking Crew', Decimal('47.99'), '/marvel-crisis-protocol:-abomination--wrecking-crew'),
    ('MCP-022', 'Marvel Crisis Protocol: Tomb of Dracula Terrain Pack', Decimal('89.99'), '/marvel-crisis-protocol:-tomb-of-dracula-terrain-pack'),
    ('MCP-023', 'Marvel Crisis Protocol - Uncanny Telepaths & Telekinetics', Decimal('51.99'), '/marvel-crisis-protocol---uncanny-telepaths--telekinetics'),
    ('MCP-024', 'Marvel Crisis Protocol: Guardians of The Galaxy Starter Set', Decimal('79.99'), '/marvel-crisis-protocol:-guardians-of-the-galaxy-starter-set'),
    ('MCP-025', 'Marvel Crisis Protocol: Guardians of The Galaxy Affiliation Pack', Decimal('51.99'), '/marvel-crisis-protocol:-guardians-of-the-galaxy-affiliation-pack'),
    ('MCP-026', 'Marvel Crisis Protocol: Rejuvenation Chamber Ultimate Encounter', Decimal('87.49'), '/marvel-crisis-protocol:-rejuvenation-chamber-ultimate-encounter'),
    ('MCP-027', 'Marvel Crisis Protocol - Asgardians Starter Set', Decimal('106.24'), '/marvel-crisis-protocol---asgardians-starter-set'),
    ('MCP-028', 'Marvel Crisis Protocol: Galaxy’s Deadliest Affiliation Pack', Decimal('47.99'), '/marvel-crisis-protocol:-galaxys-deadliest-affiliation-pack'),
    ('MCP-029', 'Marvel Crisis Protocol: S.H.I.E.L.D Affiliation Pack', Decimal('47.99'), '/marvel-crisis-protocol:-shield-affiliation-pack'),
    ('MCP-030', 'Marvel Crisis Protocol: Criminal Syndicate Affiliation Pack', Decimal('51.99'), '/marvel-crisis-protocol:-criminal-syndicate-affiliation-pack'),
    ('MCP-033', 'Marvel Crisis Protocol: Convocation Affiliation Pack', Decimal('47.99'), '/marvel-crisis-protocol:-convocation-affiliation-pack'),
    ('MCP-034', 'Marvel Crisis Protocol: Rival Panels - Battle for The Throne', Decimal('74.99'), '/marvel-crisis-protocol:-rival-panels---battle-for-the-throne'),
    ('MCP-035', 'Marvel Crisis Protocol - Hard to Hit Character Pack', Decimal('51.99'), '/marvel-crisis-protocol---hard-to-hit-character-pack'),
    ('MCP-036', 'Marvel Crisis Protocol: Range and Movement Tools', Decimal('15.99'), '/marvel-crisis-protocol:-range-and-movement-tools'),
    ('MCP-037', 'Marvel Crisis Protocol: Dice Pack', Decimal('7.99'), '/marvel-crisis-protocol:-dice-pack'),
    ('MCP-038', 'Marvel Crisis Protocol - Asgardian Shrine', Decimal('59.99'), '/marvel-crisis-protocol---asgardian-shrine'),
    ('MCP-039', 'Marvel Crisis Protocol: Dimensional Terror Terrain Pack', Decimal('71.99'), '/marvel-crisis-protocol:-dimensional-terror-terrain-pack'),
    ('MCP-041', 'Marvel Crisis Protocol: Inhumans Affiliation Pack', Decimal('47.99'), '/marvel-crisis-protocol:-inhumans-affiliation-pack'),
    ('MCP-042', 'Marvel Crisis Protocol: Dark Dimension Incursion Terrain Pack', Decimal('63.99'), '/marvel-crisis-protocol:-dark-dimension-incursion-terrain-pack'),
    ('MCP-043', 'Marvel Crisis Protocol: Spider Foes Affiliation Pack', Decimal('47.99'), '/marvel-crisis-protocol:-spider-foes-affiliation-pack'),
    ('MCP-044', 'Marvel Crisis Protocol: Dormammu Ultimate Encounter', Decimal('63.99'), '/marvel-crisis-protocol:-dormammu-ultimate-encounter'),
    ('MCP-046', 'Marvel Crisis Protocol - Winter Guard Affiliation Pack', Decimal('51.99'), '/marvel-crisis-protocol---winter-guard-affiliation-pack'),
    ('MCP-047', 'Marvel Crisis Protocol: Warriors of Asgard', Decimal('51.99'), '/marvel-crisis-protocol:-warriors-of-asgard'),
    ('MCP-048', 'Marvel Crisis Protocol: Range and Movement Tools', Decimal('15.99'), '/marvel-crisis-protocol:-range-and-movement-tools'),
    ('MCP-050', 'Marvel Crisis Protocol - Cosmic Motherlode Terrain Pack', Decimal('67.99'), '/marvel-crisis-protocol---cosmic-motherlode-terrain-pack'),
    ('MCP-051', 'Marvel Crisis Protocol: Avengers Affiliation Pack', Decimal('47.99'), '/marvel-crisis-protocol:-avengers-affiliation-pack'),
    ('MCP-052', 'Marvel Crisis Protocol: Cabal Affiliation Pack', Decimal('47.99'), '/marvel-crisis-protocol:-cabal-affiliation-pack'),
    ('MCP-053', 'Marvel Crisis Protocol: Hydra Tank: Terrain & Ultimate Encounter', Decimal('59.99'), '/marvel-crisis-protocol:-hydra-tank:-terrain--ultimate-encounter'),
    ('MCP-054', 'Marvel Crisis Protocol: Gwenom & Scarlet Spider', Decimal('31.99'), '/marvel-crisis-protocol:-gwenom--scarlet-spider'),
    ('MCP-055', 'Marvel Crisis Protocol: Elsa Bloodstone & Man-Thing', Decimal('35.99'), '/marvel-crisis-protocol:-elsa-bloodstone--man-thing'),
    ('MCP-056', 'Marvel Crisis Protocol: Mighty Thor, Lady Sif, Thor, Hero of Midgard & Loki, Prince of Lies', Decimal('51.99'), '/marvel-crisis-protocol:-mighty-thor-lady-sif-thor-hero-of-midgard--loki-prince-of-lies'),
    ('MCP-057', 'Marvel Crisis Protocol: Valkyrie on Aragon & Warriors Three', Decimal('47.99'), '/marvel-crisis-protocol:-valkyrie-on-aragon--warriors-three'),
    ('MCP-058', 'Marvel Crisis Protocol: Nova & Yondu', Decimal('31.99'), '/marvel-crisis-protocol:-nova--yondu'),
    ('MCP-059', 'Marvel Crisis Protocol: Earth\'s Mightiest Core Set', Decimal('119.99'), '/marvel-crisis-protocol:-earths-mightiest-core-set'),
    ('MCP-060', 'Marvel Crisis Protocol: Black Panther, Chosen of Bast & Namor, The Sub-Mariner', Decimal('39.99'), '/marvel-crisis-protocol:-black-panther-chosen-of-bast--namor-the-sub-mariner'),
    ('MCP-061', 'Marvel Crisis Protocol: Defenders Affiliation Pack', Decimal('51.99'), '/marvel-crisis-protocol:-defenders-affiliation-pack'),
    ('MCP-062', 'Marvel Crisis Protocol - Alliances Night of the Goblin', Decimal('71.99'), '/marvel-crisis-protocol---alliances-night-of-the-goblin'),
    ('MCP-063', 'Marvel Crisis Protocol: Shang Chi & Silver Sable', Decimal('31.99'), '/marvel-crisis-protocol:-shang-chi--silver-sable'),
    ('MCP-064', 'Marvel Crisis Protocol: X-Men Sentinels Affiliation Pack', Decimal('55.99'), '/marvel-crisis-protocol:-x-men-sentinels-affiliation-pack'),
    ('MCP-065', 'Marvel Crisis Protocol: Mojo Ball Scenario Pack', Decimal('11.99'), '/marvel-crisis-protocol:-mojo-ball-scenario-pack'),
    ('MCP-066', 'Marvel Crisis Protocol: X-Force Affiliation Pack', Decimal('47.99'), '/marvel-crisis-protocol:-x-force-affiliation-pack'),
    ('MCP-068', 'Marvel Crisis Protocol: Blue Marvel & Spectrum', Decimal('31.99'), '/marvel-crisis-protocol:-blue-marvel--spectrum'),
    ('MCP-069', 'Marvel Crisis Protocol: Inhuman Royal Court', Decimal('51.99'), '/marvel-crisis-protocol:-inhuman-royal-court'),
    ('MCP-070', 'Marvel Crisis Protocol: Weapon X & Maverick', Decimal('31.99'), '/marvel-crisis-protocol:-weapon-x--maverick'),
    ('MCP-071', 'Marvel Crisis Protocol: NYC City Block Terrain Collection', Decimal('119.99'), '/marvel-crisis-protocol:-nyc-city-block-terrain-collection'),
    ('MCP-072', 'Marvel Crisis Protocol: Sunspot & Warlock', Decimal('31.99'), '/marvel-crisis-protocol:-sunspot--warlock'),
    ('MCP-073', 'Marvel Crisis Protocol: Mephisto', Decimal('27.99'), '/marvel-crisis-protocol:-mephisto'),
]


class Command(BaseCommand):
    help = 'Seed Firestorm Games UK prices for Marvel: Crisis Protocol. Idempotent.'

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
                f'Seeded {seeded} Firestorm Games Marvel Crisis Protocol prices. Skipped: {skipped}.'
            )
        )
