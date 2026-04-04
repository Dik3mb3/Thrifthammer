"""
Management command: seed_mm_sm_phase2_prices

Seeds Miniature Market CurrentPrice entries for Space Marines phase-2 and
phase-3 products (from populate_sm_phase2_products, populate_sm_phase3_products,
and populate_successor_chapters_products).

Prices sourced from Octoparse MM scrape (xlsx 2026-04-04) plus direct MM
site lookups for codexes. Shared-kit products (Storm Speeders, Gladiators,
Stormtalon/Stormhawk, Bjorn/Murderfang/SW Ven. Dread, Centurion variants,
Rhino/Razorback, Wulfen Dreadnought) all share their kit's MM listing URL.

Products with not_available=True are seeded with no URL — MM does not list
them, but the row is created so Miniature Market appears in the price table.

Safe to run repeatedly (idempotent via update_or_create).

Usage:
    python manage.py seed_mm_sm_phase2_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

# ── Miniature Market SM phase-2 / phase-3 price data ─────────────────────────
# (slug, listing_title, price, url, in_stock, not_available)
MM_PRICES = [
    # ── Generic Space Marines (phase-2) ──────────────────────────────────────
    # Characters
    (
        'space-marine-techmarine',
        'Space Marines - Primaris Techmarine',
        35.99,
        'https://www.miniaturemarket.com/gw-48-39-270130.html',
        False, False,
    ),
    (
        'space-marine-captain-in-gravis-armour',
        'Space Marines - Captain in Gravis Armour',
        35.99,
        'https://www.miniaturemarket.com/gw-48-70-2022.html',
        False, False,
    ),
    (
        'space-marine-captain-in-phobos-armour',
        'Space Marines - Primaris Captain in Phobos Armour',
        35.99,
        'https://www.miniaturemarket.com/gw-48-68.html',
        False, False,
    ),
    (
        'space-marine-captain-with-jump-pack',
        'Space Marines - Captain with Jump Pack',
        35.99,
        'https://www.miniaturemarket.com/warhammer-40k-space-marines-captain-with-jump-pack-gw-48-17-2023.html',
        False, False,
    ),
    # MM does not stock this variant — row seeded as not available
    (
        'space-marine-captain-jump-pack-relic-shield',
        'Space Marines - Captain with Jump Pack and Relic Shield',
        0.00,
        '',
        False, True,
    ),
    # MM does not stock this variant — row seeded as not available
    (
        'space-marine-captain-with-relic-shield',
        'Space Marines - Captain with Relic Shield',
        0.00,
        '',
        False, True,
    ),
    (
        'space-marine-captain-in-terminator-armour',
        'Space Marines - Captain in Terminator Armor',
        37.99,
        'https://www.miniaturemarket.com/warhammer-40k-space-marines-captain-terminator-armor-gw-48-92-2024.html',
        False, False,
    ),
    (
        'space-marine-lieutenant-in-phobos-armour',
        'Space Marines - Primaris Lieutenant in Phobos Armour',
        31.99,
        'https://www.miniaturemarket.com/gw-48-64.html',
        False, False,
    ),
    (
        'space-marine-lieutenant-with-power-sword',
        'Space Marines - Primaris Lieutenant with Power Sword',
        31.99,
        'https://www.miniaturemarket.com/gw-48-84.html',
        False, False,
    ),
    # MM does not stock this variant — row seeded as not available
    (
        'space-marine-lieutenant-with-storm-shield',
        'Space Marines - Lieutenant with Storm Shield',
        0.00,
        '',
        False, True,
    ),
    (
        'space-marine-librarian-in-phobos-armour',
        'Space Marines - Primaris Librarian in Phobos Armour',
        31.99,
        'https://www.miniaturemarket.com/gw-48-67.html',
        False, False,
    ),
    (
        'space-marine-librarian-in-terminator-armour',
        'Space Marines - Librarian in Terminator Armour',
        33.99,
        'https://www.miniaturemarket.com/warhammer-40k-space-marines-librarian-in-terminator-armour-gw-48-06.html',
        False, False,
    ),
    (
        'space-marine-ancient-in-terminator-armour',
        'Space Marines - Ancient in Terminator Armour',
        39.99,
        'https://www.miniaturemarket.com/Warhammer-40K-Space-Marines-Ancient-in-Terminator-Armour/GW-48-104-2025',
        False, False,
    ),
    # Infantry
    (
        'space-marine-hellblaster-squad',
        'Space Marine Primaris Hellblasters',
        53.99,
        'https://www.miniaturemarket.com/gw-48-76.html',
        False, False,
    ),
    (
        'space-marine-reiver-squad',
        'Space Marines Primaris Reivers',
        53.99,
        'https://www.miniaturemarket.com/gw-48-71.html',
        False, False,
    ),
    (
        'space-marine-heavy-intercessor-squad',
        'Space Marines - Heavy Intercessors',
        55.99,
        'https://www.miniaturemarket.com/gw-48-95.html',
        False, False,
    ),
    (
        'space-marine-terminator-assault-squad',
        'Space Marines - Terminator Assault Squad',
        58.99,
        'https://www.miniaturemarket.com/Warhammer-40K-Space-Marines-Terminator-Assault-Squad/GW-48-34-2025',
        False, False,
    ),
    (
        'space-marine-centurion-devastator-squad',
        'Space Marine Centurion Devastator Squad',
        68.00,
        'https://www.miniaturemarket.com/gw-48-24.html',
        False, False,
    ),
    # Centurion Assault Squad — same physical kit as Devastator; MM lists one SKU
    (
        'space-marine-centurion-assault-squad',
        'Space Marine Centurion Devastator Squad',
        68.00,
        'https://www.miniaturemarket.com/gw-48-24.html',
        False, False,
    ),
    (
        'space-marine-assault-intercessors-jump-packs',
        'Space Marines - Jump Pack Intercessors',
        51.00,
        'https://www.miniaturemarket.com/warhammer-40k-space-marines-jump-pack-intercessors-gw-48-13-2023.html',
        False, False,
    ),
    (
        'space-marine-desolation-squad',
        'Space Marines - Desolation Squad',
        51.00,
        'https://www.miniaturemarket.com/warhammer-40k-space-marines-desolation-squad-gw-48-74-2023.html',
        False, False,
    ),
    # Vehicles
    (
        'space-marine-chaplain-on-bike',
        'Space Marines - Primaris Chaplain on Bike',
        49.99,
        'https://www.miniaturemarket.com/gw-48-31-269962.html',
        False, False,
    ),
    (
        'space-marine-venerable-dreadnought',
        'Space Marine Venerable Dreadnought',
        53.99,
        'https://www.miniaturemarket.com/gw-48-32.html',
        False, False,
    ),
    (
        'space-marine-invictor-tactical-warsuit',
        'Space Marines - Primaris Invictor Tactical Warsuit',
        59.99,
        'https://www.miniaturemarket.com/gw-48-98.html',
        False, False,
    ),
    # Rhino — same physical kit as Razorback; MM lists one SKU
    (
        'space-marine-rhino',
        'Space Marine Razorback',
        50.99,
        'https://www.miniaturemarket.com/gw-48-21.html',
        False, False,
    ),
    (
        'space-marine-razorback',
        'Space Marine Razorback',
        50.99,
        'https://www.miniaturemarket.com/gw-48-21.html',
        False, False,
    ),
    (
        'space-marine-drop-pods',
        'Space Marines - Drop Pods',
        68.00,
        'https://www.miniaturemarket.com/warhammer-40k-space-marines-drop-pods-gw-48-101.html',
        False, False,
    ),
    # Predator Destructor — MM lists a generic "Space Marine Predator" covering
    # both Annihilator and Destructor build options
    (
        'space-marine-predator-destructor',
        'Space Marine Predator',
        63.99,
        'https://www.miniaturemarket.com/gw-48-23.html',
        False, False,
    ),
    # Land Raider Redeemer — MM lists "Land Raider Crusader" which is the same
    # physical dual-build kit (Crusader/Redeemer)
    (
        'space-marine-land-raider-redeemer',
        'Space Marine Land Raider Crusader',
        97.99,
        'https://www.miniaturemarket.com/gw-48-30.html',
        False, False,
    ),
    # Storm Speeders — MM lists all 3 build options under a single SKU
    (
        'space-marine-storm-speeder-thunderstrike',
        'Space Marines - Storm Speeder',
        67.99,
        'https://www.miniaturemarket.com/gw-48-45.html',
        False, False,
    ),
    (
        'space-marine-storm-speeder-hammerstrike',
        'Space Marines - Storm Speeder',
        67.99,
        'https://www.miniaturemarket.com/gw-48-45.html',
        False, False,
    ),
    (
        'space-marine-storm-speeder-hailstrike',
        'Space Marines - Storm Speeder',
        67.99,
        'https://www.miniaturemarket.com/gw-48-45.html',
        False, False,
    ),
    # Gladiators — MM lists all 3 build options under a single SKU
    (
        'space-marine-gladiator-lancer',
        'Space Marines - Gladiator',
        78.99,
        'https://www.miniaturemarket.com/gw-48-37.html',
        False, False,
    ),
    (
        'space-marine-gladiator-reaper',
        'Space Marines - Gladiator',
        78.99,
        'https://www.miniaturemarket.com/gw-48-37.html',
        False, False,
    ),
    (
        'space-marine-gladiator-valiant',
        'Space Marines - Gladiator',
        78.99,
        'https://www.miniaturemarket.com/gw-48-37.html',
        False, False,
    ),
    # Stormtalon/Stormhawk — MM lists both build options under one SKU
    (
        'space-marine-stormtalon-gunship',
        'Space Marine Stormhawk Interceptor/Stormtalon Gunship',
        55.99,
        'https://www.miniaturemarket.com/gw-48-42.html',
        False, False,
    ),
    (
        'space-marine-stormhawk-interceptor',
        'Space Marine Stormhawk Interceptor/Stormtalon Gunship',
        55.99,
        'https://www.miniaturemarket.com/gw-48-42.html',
        False, False,
    ),
    # Stormraven — MM uses BA product code gw-41-10 but it's the same kit
    (
        'space-marine-stormraven-gunship',
        'Stormraven Gunship',
        106.99,
        'https://www.miniaturemarket.com/gw-41-10.html',
        False, False,
    ),
    # Codex
    (
        'codex-space-marines',
        'Warhammer 40K: Codex - Space Marines (10th Edition)',
        51.00,
        'https://www.miniaturemarket.com/warhammer-40k-codex-space-marines-10th-edition-gw-48-01-2023.html',
        False, False,
    ),

    # ── Blood Angels (phase-3) ────────────────────────────────────────────────
    (
        'blood-angels-chaplain-jump-pack',
        'Blood Angels Chaplain with Jump Pack',
        31.99,
        'https://www.miniaturemarket.com/gw-41-17.html',
        False, False,
    ),
    # MM does not stock this model — row seeded as not available
    (
        'blood-angels-librarian-terminator-armour',
        'Blood Angels Librarian in Terminator Armour',
        0.00,
        '',
        False, True,
    ),
    (
        'blood-angels-captain',
        'Blood Angels - Captain',
        35.99,
        'https://www.miniaturemarket.com/warhammer-40k-blood-angels-captain-gw-41-23-2024.html',
        False, False,
    ),
    (
        'codex-supplement-blood-angels',
        'Warhammer 40K: Codex Supplement - Blood Angels',
        29.99,
        'https://www.miniaturemarket.com/warhammer-40k-codex-supplement-blood-angels-gw-41-01-2024.html',
        False, False,
    ),

    # ── Black Templars (phase-3) ──────────────────────────────────────────────
    (
        'codex-supplement-black-templars',
        'Warhammer 40k: Codex - Black Templars',
        29.99,
        'https://www.miniaturemarket.com/warhammer-40k-codex-black-templars-gw-55-01.html',
        False, False,
    ),

    # ── Dark Angels (phase-3) ─────────────────────────────────────────────────
    # MM does not stock this model — row seeded as not available
    (
        'dark-angels-interrogator-chaplain',
        'Dark Angels Interrogator-Chaplain',
        0.00,
        '',
        False, True,
    ),
    # MM does not stock Ravenwing Bike Squadron (has Black Knights, not Bike
    # Squadron) — row seeded as not available
    (
        'dark-angels-ravenwing-bike-squadron',
        'Ravenwing Bike Squadron',
        0.00,
        '',
        False, True,
    ),
    (
        'codex-supplement-dark-angels',
        'Warhammer 40K: Codex Supplement - Dark Angels',
        29.99,
        'https://www.miniaturemarket.com/warhammer-40k-codex-supplement-dark-angels-gw-44-01-2024.html',
        False, False,
    ),

    # ── Grey Knights (phase-3) ────────────────────────────────────────────────
    (
        'grey-knights-castellan-crowe',
        'Grey Knights - Castellan Crowe',
        38.99,
        'https://www.miniaturemarket.com/gw-57-12.html',
        False, False,
    ),
    # MM does not stock Purifier/Purgation/Interceptor Squads separately
    (
        'grey-knights-purifier-squad',
        'Grey Knights Purifier Squad',
        0.00,
        '',
        False, True,
    ),
    (
        'grey-knights-purgation-squad',
        'Grey Knights Purgation Squad',
        0.00,
        '',
        False, True,
    ),
    (
        'grey-knights-interceptor-squad',
        'Grey Knights Interceptor Squad',
        0.00,
        '',
        False, True,
    ),
    # Paladins — MM lists Paladins and Terminators under a combined SKU
    (
        'grey-knights-paladins',
        'Grey Knights Paladin/Terminator Squad',
        51.00,
        'https://www.miniaturemarket.com/gw-57-09.html',
        False, False,
    ),
    (
        'grey-knights-grand-master-nemesis-dreadknight',
        'Grey Knights - Grandmaster In Nemesis Dreadknight',
        68.00,
        'https://www.miniaturemarket.com/Warhammer-40K-Grey-Knights-Grandmaster-In-Nemesis-Dreadknight/GW-57-05',
        False, False,
    ),
    (
        'codex-grey-knights',
        'Warhammer 40k: Codex - Grey Knights',
        51.00,
        'https://www.miniaturemarket.com/warhammer-40k-codex-grey-knights-gw-57-01.html',
        False, False,
    ),

    # ── Space Wolves (phase-3) ────────────────────────────────────────────────
    (
        'space-wolves-ulrik-the-slayer',
        'Space Wolves Ulrik the Slayer',
        31.99,
        'https://www.miniaturemarket.com/gw-53-17.html',
        False, False,
    ),
    (
        'space-wolves-iron-priest',
        'Space Wolves Iron Priest',
        31.99,
        'https://www.miniaturemarket.com/gw-53-19.html',
        False, False,
    ),
    (
        'space-wolves-wulfen',
        'Space Wolves Wulfen',
        53.99,
        'https://www.miniaturemarket.com/gw-53-16.html',
        False, False,
    ),
    # SW Venerable Dread / Bjorn / Murderfang / Wulfen Dreadnought — all are
    # the same dual-kit box; MM lists them under one SKU (gw-53-12)
    (
        'space-wolves-venerable-dreadnought',
        'Space Wolves Venerable Dreadnought/Bjorn the Fell-Handed/Murderfang',
        53.99,
        'https://www.miniaturemarket.com/gw-53-12.html',
        False, False,
    ),
    (
        'space-wolves-bjorn-fell-handed',
        'Space Wolves Venerable Dreadnought/Bjorn the Fell-Handed/Murderfang',
        53.99,
        'https://www.miniaturemarket.com/gw-53-12.html',
        False, False,
    ),
    (
        'space-wolves-murderfang',
        'Space Wolves Venerable Dreadnought/Bjorn the Fell-Handed/Murderfang',
        53.99,
        'https://www.miniaturemarket.com/gw-53-12.html',
        False, False,
    ),
    (
        'space-wolves-wulfen-dreadnought',
        'Space Wolves Venerable Dreadnought/Bjorn the Fell-Handed/Murderfang',
        53.99,
        'https://www.miniaturemarket.com/gw-53-12.html',
        False, False,
    ),
    (
        'space-wolves-fenrisian-wolves',
        'Space Wolves - Fenrisian Wolves',
        35.99,
        'https://www.miniaturemarket.com/gw-53-10.html',
        False, False,
    ),
    (
        'space-wolves-wolf-priest',
        'Space Wolves - Wolf Priest',
        34.00,
        'https://www.miniaturemarket.com/warhammer-40k-space-wolves-wolf-priest-gw-53-32.html',
        False, False,
    ),
    (
        'space-wolves-wolf-guard-battle-leader',
        'Space Wolves - Wolf Guard Battle Leader',
        35.99,
        'https://www.miniaturemarket.com/warhammer-40k-space-wolves-wolf-guard-battle-leader-gw-53-31.html',
        False, False,
    ),
    (
        'space-wolves-blood-claws',
        'Space Wolves - Blood Claws',
        53.99,
        'https://www.miniaturemarket.com/warhammer-40k-space-wolves-blood-claws-gw-53-08.html',
        False, False,
    ),
    (
        'space-wolves-arjac-rockfist',
        'Space Wolves - Arjac Rockfist',
        38.99,
        'https://www.miniaturemarket.com/warhammer-40k-space-wolves-arjac-rockfist-gw-53-38.html',
        False, False,
    ),
    (
        'space-wolves-njal-stormcaller',
        'Space Wolves - Njal Stormcaller',
        38.99,
        'https://www.miniaturemarket.com/warhammer-40k-space-wolves-njal-stormcaller-gw-53-35.html',
        False, False,
    ),
    (
        'space-wolves-wolf-guard-headtakers',
        'Space Wolves - Wolf Guard Headtakers',
        55.99,
        'https://www.miniaturemarket.com/warhammer-40k-space-wolves-wolf-guard-headtakers-gw-53-29.html',
        False, False,
    ),
    (
        'space-wolves-logan-grimnar',
        'Space Wolves - Logan Grimnar',
        59.99,
        'https://www.miniaturemarket.com/warhammer-40k-space-wolves-logan-grimnar-gw-53-28.html',
        False, False,
    ),
    (
        'codex-supplement-space-wolves',
        'Warhammer 40k: Codex - Space Wolves',
        29.99,
        'https://www.miniaturemarket.com/warhammer-40k-codex-space-wolves-gw-53-01.html',
        False, False,
    ),

    # ── Successor Chapters (populate_successor_chapters_products) ─────────────
    # Iron Hands
    (
        'iron-hands-iron-father-feirros',
        'Iron Hands - Iron Father Feirros',
        38.99,
        'https://www.miniaturemarket.com/gw-55-10.html',
        False, False,
    ),
    # MM does not stock this model — row seeded as not available
    (
        'iron-hands-caanok-var',
        'Caanok Var',
        0.00,
        '',
        False, True,
    ),
    # Salamanders — MM does not stock either model
    (
        'salamanders-adrax-agatone',
        'Adrax Agatone',
        0.00,
        '',
        False, True,
    ),
    (
        'salamanders-vulkan-hestan',
        "Vulkan He'stan",
        0.00,
        '',
        False, True,
    ),
    # Imperial Fists
    (
        'imperial-fists-tor-garadon',
        'Imperial Fists - Tor Garadon',
        38.99,
        'https://www.miniaturemarket.com/gw-55-25.html',
        False, False,
    ),
    # Note: MM title has a typo — "Lysande" instead of "Lysander" — confirmed
    # correct by GW product code GW-55-61
    (
        'imperial-fists-darnath-lysander',
        'Imperial Fists - Darnath Lysande',
        38.99,
        'https://www.miniaturemarket.com/Warhammer-40K-Imperial-Fists-Darnath-Lysande/GW-55-61',
        False, False,
    ),
    # White Scars — Kor'sarro Khan not stocked by MM
    (
        'white-scars-korsarro-khan',
        "Kor'sarro Khan",
        0.00,
        '',
        False, True,
    ),
    (
        'white-scars-suboden-khan',
        'White Scars - Suboden Khan',
        55.99,
        'https://www.miniaturemarket.com/Warhammer-40K-White-Scars-Suboden-Khan/GW-55-71-2025',
        False, False,
    ),
    # Raven Guard
    (
        'raven-guard-kayvaan-shrike',
        'Raven Guard - Kayvaan Shrike',
        38.99,
        'https://www.miniaturemarket.com/gw-55-15.html',
        False, False,
    ),
    (
        'raven-guard-aethon-shaan',
        'Raven Guard - Aethon Shaan, Master of Shadows',
        38.99,
        'https://www.miniaturemarket.com/Warhammer-40K-Raven-Guard-Aethon-Shaan-Master-of-Shadows/GW-55-60',
        False, False,
    ),
]


class Command(BaseCommand):
    """Seed Miniature Market prices for SM phase-2 and phase-3 products."""

    help = (
        'Seeds Miniature Market CurrentPrice entries for Space Marines phase-2 and '
        'phase-3 products. Sourced from Octoparse MM scrape 2026-04-04 + site '
        'lookups for codexes. Idempotent.'
    )

    def handle(self, *args, **options):
        """Run the command."""
        mm = Retailer.objects.filter(name='Miniature Market').first()
        if not mm:
            self.stderr.write(self.style.ERROR(
                'Miniature Market retailer not found — run populate_products first.'
            ))
            return

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for (slug, listing_title, price, url, in_stock, not_available) in MM_PRICES:
            product = Product.objects.filter(slug=slug, is_active=True).first()
            if not product:
                self.stdout.write(self.style.WARNING(
                    f'  Skipped (product not found/inactive): {slug}'
                ))
                skipped_count += 1
                continue

            _, created = CurrentPrice.objects.update_or_create(
                product=product,
                retailer=mm,
                defaults={
                    'price': price,
                    'url': url,
                    'listing_title': listing_title,
                    'in_stock': in_stock,
                    'not_available': not_available,
                },
            )
            status = 'Created' if created else 'Updated'
            if not_available:
                label = 'Not Available'
            elif in_stock:
                label = 'In Stock'
            else:
                label = 'Out of Stock'
            self.stdout.write(
                self.style.SUCCESS(f'  {status}: {product.name} — {label}')
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nseed_mm_sm_phase2_prices complete. '
            f'{created_count} created, {updated_count} updated, {skipped_count} skipped.'
        ))
