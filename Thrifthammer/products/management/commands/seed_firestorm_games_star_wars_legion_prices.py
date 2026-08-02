"""
Seed Firestorm Games UK prices for Star Wars: Legion.

Idempotent -- CurrentPrice rows are written via update_or_create keyed on
(product, retailer), so re-running is always safe. NEVER writes msrp_gbp --
Firestorm is a discount competitor, not the MSRP source. Only
games-workshop-uk / seed_asmodee_uk_star_wars_legion_prices write that
field for this category.

Price parsing rule: Firestorm shows two numbers per listing (struck-through
RRP, then sale price). ALWAYS use the lower (sale) price, never the RRP.
RRP is only used as a matching aid to confirm which DB SKU a listing
corresponds to (it should equal Product.msrp_gbp for the matched SKU).

https://www.firestormgames.co.uk/wargames-miniatures/star-wars-legion
101/112 active DB SWL-XXX SKUs matched. This page cross-lists many units
under multiple faction sub-headings (e.g. mercenary units appear under
several factions), so matching was done by deduping Firestorm listings by
URL first, then anchoring on RRP == msrp_gbp per price bucket, verifying
every match by name rather than trusting price alone -- several dense
buckets (29.99, 34.99, 39.99, 49.99) had 15-20+ candidates at the same
price.

Small RRP/msrp flags (matched anyway, Firestorm sale price still used):
SWL-061 Ewok Warriors (RRP £43.99 vs msrp £44.99), SWL-101 Clan Wren
Mandalorians (RRP £47.99 vs msrp £47.49). SWL-004, SWL-008, SWL-042,
SWL-053, SWL-067, SWL-071, SWL-091, SWL-092 matched despite null
msrp_gbp in the DB (not yet synced by the GW/Asmodee UK feed).

User-confirmed matches (initially left unmatched/flagged, then confirmed
via explicit URL): SWL-014 "Bad Batch Operative Expansion" shares the
same Firestorm listing as SWL-078 "Bad Batch" (null msrp_gbp, legacy
duplicate SKU); SWL-059 "AT-ST Walker Expansion" (msrp £64.99) IS the
same product as Firestorm's "AT-ST Walker (New Unit Expansion)" at
£70.99 RRP despite the ~9% mismatch -- user confirmed via URL rather
than the price being close enough to auto-match.

Legacy duplicate-SKU pairs (two DB SKUs for the same physical Firestorm
listing, same pattern seen in Horus Heresy's HA-XXX orphans): SWL-026
"Sun Fac and Poggle the Lesser Operative and Commander Expansion" and
SWL-088 "Poggle the Lesser & Sun Fac" share one listing; SWL-021 and
SWL-092 (both "Fifth Brother and Seventh Sister Operative Expansion")
share another; SWL-014 and SWL-078 (both "Bad Batch") share a third.

Gaps (11, confirmed not available by user, no Firestorm listing at all):
- SWL-001 Mandalorian Special Edition Army Box (msrp £124.99) -- the two
  £124.99 "Special Edition Army Box" listings on Firestorm are "Blizzard
  Force" and "Echo Base Defenders", neither Mandalorian-themed
- SWL-009 Empire Card Pack (£24.99) -- not carried
- SWL-015 Galactic Empire Command Card Pack (£19.99) -- not carried
- SWL-032 B2 Super Rocket Battle Droids (null msrp) -- not carried
- SWL-034 Leaders of the Separatist Alliance (null msrp) -- not carried
- SWL-045 Ahsoka Tano Operative Expansion (£29.99) -- not carried
  (distinct from SWL-012 "Commander & Padawan Ahsoka Tano", matched)
- SWL-054 Sabine Wren (null msrp) -- not carried
- SWL-057 Upgrade Card Pack (£9.99) -- Firestorm only carries "Upgrade
  Card Pack 2" (£12.99), a different/newer product
- SWL-069 Asajj Ventress Operative Expansion (£23.99) -- not carried
- SWL-076 Agents of the Empire (£49.99) -- not carried
- SWL-109 Heroes of the Clone Army (null msrp) -- not carried
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
    ('SWL-002', 'Star Wars: Legion - Mandalorian Leaders', Decimal('38.24'), '/star-wars:-legion---mandalorian-leaders'),
    ('SWL-003', 'Star Wars: Legion - Galactic Republic Starter Set', Decimal('72.24'), '/star-wars:-legion---galactic-republic-starter-set'),
    ('SWL-004', 'Star Wars: Legion - Customisable Jedi & Knight', Decimal('25.49'), '/star-wars:-legion---customisable-jedi--knight'),
    ('SWL-005', 'Star Wars: Legion - Upgrades Card Pack', Decimal('21.24'), '/star-wars:-legion---upgrades-card-pack'),
    ('SWL-006', 'Star Wars: Legion - Galactic Empire Starter Set', Decimal('72.24'), '/star-wars:-legion---galactic-empire-starter-set'),
    ('SWL-007', "Star Wars: Legion - General Grievous' TSMEU-6 Wheel Bike", Decimal('42.49'), '/star-wars:-legion---general-grievous-tsmeu-6-wheel-bike'),
    ('SWL-008', 'Star Wars: Legion - Separatist Alliance Starter Set', Decimal('72.24'), '/star-wars:-legion---separatist-alliance-starter-set'),
    ('SWL-010', 'Star Wars: Legion - Customisable Imperial Officer & Agent', Decimal('25.49'), '/star-wars:-legion---customisable-imperial-officer--agent'),
    ('SWL-011', 'Star Wars: Legion - Customisable Super Tactical Command Droid', Decimal('25.49'), '/star-wars:-legion---customisable-super-tactical-command-droid'),
    ('SWL-012', 'Star Wars Legion: Commander & Padawan Ahsoka Tano', Decimal('25.49'), '/star-wars-legion:-commander--padawan-ahsoka-tano'),
    ('SWL-013', 'Star Wars Legion: Arf Troopers', Decimal('46.74'), '/star-wars-legion:-arf-troopers'),
    ('SWL-016', 'Star Wars: Legion - Imperial High Command', Decimal('50.99'), '/star-wars:-legion---imperial-high-command'),
    ('SWL-017', 'Star Wars Legion: Customisable Mandalorian Leader & Hunter', Decimal('26.99'), '/star-wars-legion:-customisable-mandalorian-leader--hunter'),
    ('SWL-018', 'Star Wars: Legion - Separatist Alliance Card Pack', Decimal('16.99'), '/star-wars:-legion---separatist-alliance-card-pack'),
    ('SWL-019', 'Star Wars: Legion - Galactic Republic Command Card Pack', Decimal('12.74'), '/star-wars:-legion---galactic-republic-command-card-pack'),
    ('SWL-020', 'Star Wars: Legion - Mercenary Card Pack', Decimal('13.99'), '/star-wars:-legion---mercenary-card-pack'),
    ('SWL-021', 'Star Wars Legion: Fifth Brother and Seventh Sister Operative Expansion', Decimal('20.99'), '/star-wars-legion:-fifth-brother-and-seventh-sister-operative-expansion'),
    ('SWL-022', 'Star Wars: Legion - Mandalorian Warriors', Decimal('49.49'), '/star-wars:-legion---mandalorian-warriors'),
    ('SWL-023', 'Star Wars: Legion - Leaders of the Shadow Collective', Decimal('33.99'), '/star-wars:-legion---leaders-of-the-shadow-collective'),
    ('SWL-024', 'Star Wars: Legion - Mandalorian Super Commandos', Decimal('42.49'), '/star-wars:-legion---mandalorian-super-commandos'),
    ('SWL-025', 'Star Wars: Legion Upgrades Card Pack II', Decimal('19.54'), '/star-wars:-legion-upgrades-card-pack-ii'),
    ('SWL-026', 'Star Wars Legion: Poggle The Lesser & Sun Fac', Decimal('25.49'), '/star-wars-legion:-poggle-the-lesser--sun-fac'),
    ('SWL-027', 'Star Wars Legion: Stormtroopers', Decimal('42.49'), '/star-wars-legion:-stormtroopers'),
    ('SWL-028', 'Star Wars Legion: TX-130 Saber Tank', Decimal('59.49'), '/star-wars-legion:-tx-130-saber-tank'),
    ('SWL-029', 'Star Wars: Legion - Heroes of the Rebellion Character Pack', Decimal('50.99'), '/star-wars:-legion---heroes-of-the-rebellion-character-pack'),
    ('SWL-030', 'Star Wars Legion: Rebel Troopers', Decimal('42.49'), '/star-wars-legion:-rebel-troopers'),
    ('SWL-031', 'Star Wars: Legion - 3D Objective Tokens', Decimal('33.99'), '/star-wars:-legion---3d-objective-tokens'),
    ('SWL-033', 'Star Wars: Legion Republic AT-RT', Decimal('29.74'), '/star-wars:-legion-republic-at-rt'),
    ('SWL-035', 'Star Wars: Legion BX-Series Droid Commandos', Decimal('42.49'), '/star-wars:-legion-bx-series-droid-commandos'),
    ('SWL-036', 'Star Wars: Legion - ARC Troopers Unit Expansion', Decimal('46.74'), '/star-wars:-legion---arc-troopers-unit-expansion'),
    ('SWL-037', 'Star Wars: Legion - Imperial Death Troopers', Decimal('29.74'), '/star-wars:-legion---imperial-death-troopers'),
    ('SWL-038', 'Star Wars: Legion - Darth Vader & General Veers Character Expansion', Decimal('25.49'), '/star-wars:-legion---darth-vader--general-veers-character-expansion'),
    ('SWL-039', 'Star Wars Legion: Clone Commander Cody', Decimal('29.74'), '/star-wars-legion:-clone-commander-cody'),
    ('SWL-040', 'Star Wars: Legion - Rogues & Rebels Character Expansion', Decimal('42.49'), '/star-wars:-legion---rogues--rebels-character-expansion'),
    ('SWL-041', 'Star Wars: Legion Outer Rim Outlaws', Decimal('29.74'), '/star-wars:-legion-outer-rim-outlaws'),
    ('SWL-042', 'Star Wars Legion: Scout Troopers', Decimal('42.49'), '/star-wars-legion:-scout-troopers'),
    ('SWL-043', 'Star Wars: Legion - Imperial Shoretroopers', Decimal('44.99'), '/star-wars:-legion---imperial-shoretroopers'),
    ('SWL-044', 'Star Wars Legion: Geonosian Warriors Unit Expansion', Decimal('42.49'), '/star-wars-legion:-geonosian-warriors-unit-expansion-92610'),
    ('SWL-046', 'Star Wars: Legion - Republic Specialists', Decimal('33.99'), '/star-wars:-legion---republic-specialists'),
    ('SWL-047', 'Star Wars Legion: Out Rim Terrain Pack', Decimal('50.99'), '/star-wars-legion:-out-rim-terrain-pack'),
    ('SWL-048', 'Star Wars: Legion Galactic Bounty Hunters', Decimal('42.49'), '/star-wars:-legion-galactic-bounty-hunters'),
    ('SWL-049', 'Star Wars: Legion - DSD1 Dwarf Spider Droid', Decimal('25.49'), '/star-wars:-legion---dsd1-dwarf-spider-droid'),
    ('SWL-050', 'Star Wars Legion: IG-100 Magnaguards', Decimal('33.99'), '/star-wars-legion:-ig-100-magnaguards'),
    ('SWL-051', 'Star Wars: Legion AAT Battle Tank', Decimal('59.49'), '/star-wars:-legion-aat-battle-tank'),
    ('SWL-052', 'Star Wars: Legion - E-Web Heavy Blaster Team', Decimal('25.49'), '/star-wars:-legion---e-web-heavy-blaster-team'),
    ('SWL-055', 'Star Wars: Legion - Clone Troopers Infantry', Decimal('42.49'), '/star-wars:-legion---clone-troopers-infantry'),
    ('SWL-056', 'Star Wars Legion: Rebel Commandos', Decimal('42.49'), '/star-wars-legion:-rebel-commandos'),
    ('SWL-058', 'Star Wars Legion: T-47 Airspeeder', Decimal('33.99'), '/star-wars-legion:-t-47-airspeeder'),
    ('SWL-060', 'Star Wars: Legion Imperial Special Forces', Decimal('33.99'), '/star-wars:-legion-imperial-special-forces'),
    ('SWL-062', 'Star Wars: Legion - Essentials Pack', Decimal('13.99'), '/star-wars:-legion---essentials-pack'),
    ('SWL-064', 'Star Wars: Legion - 74-Z Speeder Bike Unit Expansion', Decimal('25.49'), '/star-wars:-legion---74-z-speeder-bike-unit-expansion'),
    ('SWL-065', 'Star Wars: Legion - Fleet Troopers', Decimal('50.99'), '/star-wars:-legion---fleet-troopers'),
    ('SWL-066', 'Star Wars: Legion A-A5 Speeder Truck', Decimal('59.49'), '/star-wars:-legion-a-a5-speeder-truck'),
    ('SWL-068', 'Star Wars: Legion - B1 Battle Droids', Decimal('42.49'), '/star-wars:-legion---b1-battle-droids'),
    ('SWL-070', 'Star Wars: Legion - Tauntaun Riders', Decimal('33.99'), '/star-wars:-legion---tauntaun-riders'),
    ('SWL-072', 'Star Wars: Legion - Cassian Andor, Jyn Erso & K-2SO', Decimal('29.74'), '/star-wars:-legion---cassian-andor-jyn-erso--k-2so'),
    ('SWL-073', 'Star Wars: Legion - Leaders of the Republic (Padme & Yoda)', Decimal('29.74'), '/star-wars:-legion---leaders-of-the-republic-padme--yoda'),
    ('SWL-074', 'Star Wars: Legion - X-34 Landspeeder', Decimal('25.49'), '/star-wars:-legion---x-34-landspeeder'),
    ('SWL-075', 'Star Wars: Legion - Imperial Specialists', Decimal('33.99'), '/star-wars:-legion---imperial-specialists'),
    ('SWL-077', 'Star Wars: Legion IG Assassin Droids', Decimal('25.49'), '/star-wars:-legion-ig-assassin-droids'),
    ('SWL-078', 'Star Wars: Legion - Bad Batch', Decimal('50.99'), '/star-wars:-legion---bad-batch'),
    ('SWL-079', 'Star Wars: Legion - Separatist Specialists', Decimal('33.99'), '/star-wars:-legion---separatist-specialists'),
    ('SWL-080', 'Star Wars Legion: Super Tactical Droids', Decimal('29.74'), '/star-wars-legion:-super-tactical-droids'),
    ('SWL-081', 'Star Wars: Legion R2-D2 & C-3P0 Operative Expansion', Decimal('26.99'), '/star-wars:-legion-r2-d2--c-3p0-operative-expansion'),
    ('SWL-082', 'Star Wars: Legion - Kashyyyk Wookiee Warriors Unit Expansion', Decimal('33.99'), '/star-wars:-legion---kashyyyk-wookiee-warriors-unit-expansion'),
    ('SWL-083', 'Star Wars: Logray & Wicket Commander Expansion', Decimal('26.99'), '/star-wars:-logray--wicket-commander-expansion'),
    ('SWL-084', 'Star Wars: Legion - Snowtroopers', Decimal('42.49'), '/star-wars:-legion---snowtroopers'),
    ('SWL-085', 'Star Wars: Legion - Rebel Specialists', Decimal('33.99'), '/star-wars:-legion---rebel-specialists'),
    ('SWL-086', 'Star Wars: Legion - Rebel Veterans', Decimal('42.49'), '/star-wars:-legion---rebel-veterans'),
    ('SWL-087', 'Star Wars: Legion - Range Troopers', Decimal('37.49'), '/star-wars:-legion---range-troopers'),
    ('SWL-088', 'Star Wars Legion: Poggle The Lesser & Sun Fac', Decimal('25.49'), '/star-wars-legion:-poggle-the-lesser--sun-fac'),
    ('SWL-089', 'Star Wars Legion: Driodekas', Decimal('29.74'), '/star-wars-legion:-driodekas'),
    ('SWL-090', 'Star Wars: Legion - Rebel AT-RT', Decimal('24.64'), '/star-wars:-legion---rebel-at-rt'),
    ('SWL-091', 'Star Wars Legion: Infantry Support Platform Unit', Decimal('38.24'), '/star-wars-legion:-infantry-support-platform-unit'),
    ('SWL-092', 'Star Wars Legion: Fifth Brother and Seventh Sister Operative Expansion', Decimal('20.99'), '/star-wars-legion:-fifth-brother-and-seventh-sister-operative-expansion'),
    ('SWL-093', 'Star Wars: Legion - Rebel Alliance Starter Set', Decimal('72.24'), '/star-wars:-legion---rebel-alliance-starter-set'),
    ('SWL-094', 'Star Wars: Legion - Separatist Alliance Command Card Pack', Decimal('10.49'), '/star-wars:-legion---separatist-alliance-command-card-pack-94956'),
    ('SWL-095', 'Star Wars: Legion - Rebellion Card Pack', Decimal('17.49'), '/star-wars:-legion---rebellion-card-pack'),
    ('SWL-096', 'Star Wars: Legion - Rebel Alliance Command Card Pack', Decimal('13.99'), '/star-wars:-legion---rebel-alliance-command-card-pack'),
    ('SWL-097', 'Star Wars: Legion - Clone Trooper Marksmen', Decimal('42.49'), '/star-wars:-legion---clone-trooper-marksmen'),
    ('SWL-098', 'Star Wars Legion: Republic Clone Commandos', Decimal('29.74'), '/star-wars-legion:-republic-clone-commandos'),
    ('SWL-099', 'Star Wars: Legion - Customisable Rebel Officer & Agent', Decimal('25.49'), '/star-wars:-legion---customisable-rebel-officer--agent'),
    ('SWL-100', 'Star Wars: Legion - Battle Card Pack', Decimal('17.49'), '/star-wars:-legion---battle-card-pack'),
    ('SWL-101', 'Star Wars: Legion - Clan Wren Mandalorians', Decimal('40.79'), '/star-wars:-legion---clan-wren-mandalorians'),
    ('SWL-102', 'Star Wars: Legion - Battle Deck Card Pack II', Decimal('25.49'), '/star-wars:-legion---battle-deck-card-pack-ii'),
    ('SWL-103', 'Star Wars: Legion - Aqua Droids Expansion', Decimal('50.99'), '/star-wars:-legion---aqua-droids-expansion'),
    ('SWL-104', 'Star Wars: Legion - Captain Solo & Commander Skywalker on Tauntauns', Decimal('42.49'), '/star-wars:-legion--captain-solo--commander-skywalker-on-tauntauns'),
    ('SWL-105', 'Star Wars: Legion - LM-432 Crab Droids Expansion', Decimal('42.49'), '/star-wars:-legion---lm-432-crab-droids-expansion'),
    ('SWL-106', 'Star Wars: Legion - Imperial Probe Droids', Decimal('29.74'), '/star-wars:-legion---imperial-probe-droids'),
    ('SWL-107', 'Star Wars: Legion – Hondo Ohnaka & Weequay Pirates', Decimal('33.99'), '/star-wars:-legion--hondo-ohnaka--weequay-pirates'),
    ('SWL-108', 'Star Wars: Legion TSMEU-6 Personal Wheel Bike', Decimal('50.99'), '/star-wars:-legion-tsmeu-6-personal-wheel-bike'),
    ('SWL-110', 'Star Wars Legion: B2 Super Battle Droids', Decimal('33.99'), '/star-wars-legion:-b2-super-battle-droids'),
    ('SWL-111', 'Star Wars: Legion - Jedi Council Commander Expansion', Decimal('50.99'), '/star-wars:-legion---jedi-council-commander-expansion'),
    ('SWL-112', 'Star Wars: Legion - WL0-5 Speeder Tank', Decimal('72.24'), '/star-wars:-legion---wl0-5-speeder-tank'),
    ('SWL-061', 'Star Wars Legion: Ewok Warriors Expansion Pack', Decimal('37.39'), '/star-wars-legion:-ewok-warriors-expansion-pack'),
    ('SWL-063', 'Star Wars Legion: Imperial Dark Troopers (Unit Expansion)', Decimal('44.54'), '/star-wars-legion:-imperial-dark-troopers-unit-expansion'),
    ('SWL-053', 'Star Wars Legion: Legion Attack Dice Pack', Decimal('12.74'), '/star-wars-legion:-legion-attack-dice-pack'),
    ('SWL-067', 'Star Wars Legion: Legion Defense Dice Pack', Decimal('12.74'), '/star-wars-legion:-legion-defense-dice-pack'),
    ('SWL-071', 'Star Wars Legion: Moff Gideon (Commander Expansion)', Decimal('18.69'), '/star-wars-legion:-moff-gideon-commander-expansion'),
    ('SWL-014', 'Star Wars: Legion - Bad Batch', Decimal('50.99'), '/star-wars:-legion---bad-batch'),
    ('SWL-059', 'Star Wars Legion: AT-ST Walker (New Unit Expansion)', Decimal('60.34'), '/star-wars-legion:-at-st-walker-new-unit-expansion'),
]


class Command(BaseCommand):
    help = 'Seed Firestorm Games UK prices for Star Wars: Legion. Idempotent.'

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
                f'Seeded {seeded} Firestorm Games Star Wars: Legion prices. Skipped: {skipped}.'
            )
        )
