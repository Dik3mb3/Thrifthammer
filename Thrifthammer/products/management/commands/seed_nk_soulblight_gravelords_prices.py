"""
Management command: seed_nk_soulblight_gravelords_prices

Seeds Noble Knight Games CurrentPrice entries for all 37 Soulblight Gravelords
products (SG-001 to SG-037).

Source: AOS Soulblight - GW, NK, MM.xlsx (2026-06-08).
Affiliate parameter ?awid=1576 appended to all URLs.

Dual-kit notes (same physical box — same NK URL):
  Vengorian Lord / Lauka Vai, Mother of Nightmares (SG-009 / SG-012)
    → https://www.nobleknight.com/P/2148067833/Lauka-Vai---Mother-of-Nightmares
  Neferata, Mortarch of Blood / Mannfred von Carstein,
    Mortarch of Night                                (SG-014 / SG-015)
    → https://www.nobleknight.com/P/2147612293/Deathlords-Mortarch
  Mortis Engine / Coven Throne                       (SG-017 / SG-018)
    → https://www.nobleknight.com/P/2147959388/Coven-Throne-Mortis-Engine-2019-Edition

Prices are left as None — the scraper will populate actual prices on its next
Mon/Wed/Sat run.

Safe to run repeatedly (idempotent via update_or_create).

Usage:
    python manage.py seed_nk_soulblight_gravelords_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_NK = 'https://www.nobleknight.com'
_AFF = '?awid=1576'

# ── NK price data ─────────────────────────────────────────────────────────────
# (slug, listing_title, price, url, in_stock, not_available)
# price=None  → NK carries but price unknown; scraper will update
# not_available=True → not carried by NK
NK_PRICES = [

    # SG-001  Soulblight Gravelords – The Summons
    (
        'soulblight-gravelords-the-summons',
        'The Summons',
        None,
        _NK + '/P/2148427155/Summons-The' + _AFF,
        False, False,
    ),
    # SG-002  Soulblight Gravelords – Karlina von Carstein
    (
        'soulblight-gravelords-karlina-von-carstein',
        'Karlina von Carstein',
        None,
        _NK + '/P/2148204597/Karlina-von-Carstein' + _AFF,
        False, False,
    ),
    # SG-003  Spearhead: Soulblight Gravelords – Deathrattle Tomb Host
    (
        'spearhead-soulblight-gravelords-deathrattle-tomb-host',
        'Spearhead - Deathrattle Tomb Host',
        None,
        _NK + '/P/2148375637/Spearhead---Deathrattle-Tomb-Host' + _AFF,
        False, False,
    ),
    # SG-004  Ivya Volga, the Outcast
    (
        'ivya-volga-the-outcast',
        'Ivya Volga - The Outcast',
        None,
        _NK + '/P/2148047470/Ivya-Volga---The-Outcast' + _AFF,
        False, False,
    ),
    # SG-005  Lady Annika, the Thirsting Blade
    (
        'lady-annika-the-thirsting-blade',
        'Lady Annika - The Thirsting Blade',
        None,
        _NK + '/P/2147889366/Lady-Annika---The-Thirsting-Blade' + _AFF,
        False, False,
    ),
    # SG-006  Dire Wolves
    (
        'dire-wolves',
        'Dire Wolves 2023 Edition',
        None,
        _NK + '/P/2148091265/Dire-Wolves-2023-Edition' + _AFF,
        False, False,
    ),
    # SG-007  Radukar the Beast
    (
        'radukar-the-beast',
        'Radukar the Beast',
        None,
        _NK + '/P/2148356778/Radukar-the-Beast' + _AFF,
        False, False,
    ),
    # SG-008  Belladamma Volga, First of the Vyrkos
    (
        'belladamma-volga-first-of-the-vyrkos',
        'Belladamma Volga - First of the Vyrkos',
        None,
        _NK + '/P/2148394760/Belladamma-Volga---First-of-the-Vyrkos' + _AFF,
        False, False,
    ),
    # SG-009  Vengorian Lord
    # ⚠ Dual kit with SG-012 (Lauka Vai, Mother of Nightmares)
    (
        'vengorian-lord',
        'Lauka Vai - Mother of Nightmares',
        None,
        _NK + '/P/2148067833/Lauka-Vai---Mother-of-Nightmares' + _AFF,
        False, False,
    ),
    # SG-010  Blood Knights
    (
        'blood-knights',
        'Blood Knights 2023 Edition',
        None,
        _NK + '/P/2148163288/Blood-Knights-2023-Edition' + _AFF,
        False, False,
    ),
    # SG-011  Fell Bats
    (
        'fell-bats',
        'Fell Bats',
        None,
        _NK + '/P/2147889389/Fell-Bats' + _AFF,
        False, False,
    ),
    # SG-012  Lauka Vai, Mother of Nightmares
    # ⚠ Dual kit with SG-009 (Vengorian Lord)
    (
        'lauka-vai-mother-of-nightmares',
        'Lauka Vai - Mother of Nightmares',
        None,
        _NK + '/P/2148067833/Lauka-Vai---Mother-of-Nightmares' + _AFF,
        False, False,
    ),
    # SG-013  Vargheists
    (
        'vargheists',
        'Vargheists Crypt Horrors',
        None,
        _NK + '/P/2147463975/Vargheists-Crypt-Horrors' + _AFF,
        False, False,
    ),
    # SG-014  Neferata, Mortarch of Blood
    # ⚠ Dual kit with SG-015 (Mannfred von Carstein, Mortarch of Night)
    (
        'neferata-mortarch-of-blood',
        'Deathlords Mortarch',
        None,
        _NK + '/P/2147612293/Deathlords-Mortarch' + _AFF,
        False, False,
    ),
    # SG-015  Mannfred von Carstein, Mortarch of Night
    # ⚠ Dual kit with SG-014 (Neferata, Mortarch of Blood)
    (
        'mannfred-von-carstein-mortarch-of-night',
        'Deathlords Mortarch',
        None,
        _NK + '/P/2147612293/Deathlords-Mortarch' + _AFF,
        False, False,
    ),
    # SG-016  Nagash, Supreme Lord of the Undead
    (
        'nagash-supreme-lord-of-the-undead',
        'Nagash - Supreme Lord of the Undead',
        None,
        _NK + '/P/2148127635/Nagash---Supreme-Lord-of-the-Undead' + _AFF,
        False, False,
    ),
    # SG-017  Mortis Engine
    # ⚠ Dual kit with SG-018 (Coven Throne)
    (
        'mortis-engine',
        'Coven Throne / Mortis Engine 2019 Edition',
        None,
        _NK + '/P/2147959388/Coven-Throne-Mortis-Engine-2019-Edition' + _AFF,
        False, False,
    ),
    # SG-018  Coven Throne
    # ⚠ Dual kit with SG-017 (Mortis Engine)
    (
        'coven-throne',
        'Coven Throne / Mortis Engine 2019 Edition',
        None,
        _NK + '/P/2147959388/Coven-Throne-Mortis-Engine-2019-Edition' + _AFF,
        False, False,
    ),
    # SG-019  Corpse Cart
    (
        'corpse-cart',
        'Corpse Cart Webstore Edition',
        None,
        _NK + '/P/2148187837/Corpse-Cart-Webstore-Edition' + _AFF,
        False, False,
    ),
    # SG-020  Askurgan Trueblades
    (
        'askurgan-trueblades',
        'Askurgan Trueblades',
        None,
        _NK + '/P/2148054126/Askurgan-Trueblades' + _AFF,
        False, False,
    ),
    # SG-021  Wight Lord on Skeletal Steed
    (
        'wight-lord-on-skeletal-steed',
        'Wight King on Skeletal Steed',
        None,
        _NK + '/P/2148047471/Wight-King-on-Skeletal-Steed' + _AFF,
        False, False,
    ),
    # SG-022  Soulblight Gravelords: Manifestations
    (
        'soulblight-gravelords-manifestations',
        'Manifestations',
        None,
        _NK + '/P/2148303443/Manifestations' + _AFF,
        False, False,
    ),
    # SG-023  Cursed Sepulchre/Nexus of Grief
    (
        'cursed-sepulchrenexus-of-grief',
        'Cursed Sepulchre / Nexus of Grief',
        None,
        _NK + '/P/2148303404/Cursed-Sepulchre-Nexus-of-Grief' + _AFF,
        False, False,
    ),
    # SG-024  Deathrattle Skeletons
    (
        'deathrattle-skeletons',
        'Deathrattle Skeletons',
        None,
        _NK + '/P/2148303435/Deathrattle-Skeletons' + _AFF,
        False, False,
    ),
    # SG-025  Barrow Knights
    (
        'barrow-knights',
        'Barrow Knights',
        None,
        _NK + '/P/2148303515/Barrow-Knights' + _AFF,
        False, False,
    ),
    # SG-026  Barrow Guard
    (
        'barrow-guard',
        'Barrow Guard',
        None,
        _NK + '/P/2148303429/Barrow-Guard' + _AFF,
        False, False,
    ),
    # SG-027  Vampire Lord on Nightmare Steed
    (
        'vampire-lord-on-nightmare-steed',
        'Vampire Lord on Nightmare Steed',
        None,
        _NK + '/P/2148303428/Vampire-Lord-on-Nightmare-Steed' + _AFF,
        False, False,
    ),
    # SG-028  Prince Vhordrai, Lord of the Crimson Keep
    (
        'prince-vhordrai-lord-of-the-crimson-keep',
        'Prince Vhordrai, Lord of the Crimson Keep - Revenant Draconith',
        None,
        _NK + '/P/2148303408/Prince-Vhordrai-Lord-of-the-Crimson-Keep-Revenant-Draconith' + _AFF,
        False, False,
    ),
    # SG-029  Blades of the Hollow King
    (
        'blades-of-the-hollow-king',
        'Blades of the Hollow King',
        None,
        _NK + '/P/2148303426/Blades-of-the-Hollow-King' + _AFF,
        False, False,
    ),
    # SG-030  Sekhar, Fang of Nulahmia
    (
        'sekhar-fang-of-nulahmia',
        'Sekhar, Fang of Nulahmia',
        None,
        _NK + '/P/2148145402/Sekhar-Fang-of-Nulahmia' + _AFF,
        False, False,
    ),
    # SG-031  Death Battletome: Soulblight Gravelords
    (
        'death-battletome-soulblight-gravelords',
        'Battletome - Soulblight Gravelords',
        None,
        _NK + '/P/2148303391/Battletome---Soulblight-Gravelords' + _AFF,
        False, False,
    ),
    # SG-032  Kritza, the Rat Prince
    (
        'kritza-the-rat-prince',
        'Kritza - The Rat Prince',
        None,
        _NK + '/P/2147889367/Kritza---The-Rat-Prince' + _AFF,
        False, False,
    ),
    # SG-033  Radukar the Wolf
    (
        'radukar-the-wolf',
        'Radukar the Wolf Webstore Edition',
        None,
        _NK + '/P/2147961305/Radukar-the-Wolf-Webstore-Edition' + _AFF,
        False, False,
    ),
    # SG-034  Deadwalker Zombies
    (
        'deadwalker-zombies',
        'Deadwalker Zombies',
        None,
        _NK + '/P/2147889387/Deadwalker-Zombies' + _AFF,
        False, False,
    ),
    # SG-035  Vampire Lord
    (
        'vampire-lord',
        'Vampire Lord',
        None,
        _NK + '/P/2148390364/Vampire-Lord' + _AFF,
        False, False,
    ),
    # SG-036  Wight King
    (
        'wight-king',
        'Wight King 2017 Edition',
        None,
        _NK + '/P/2147807620/Wight-King-2017-Edition' + _AFF,
        False, False,
    ),
    # SG-037  Necromancer
    (
        'necromancer',
        'Necromancer',
        None,
        _NK + '/P/2148092126/Necromancer' + _AFF,
        False, False,
    ),
]


class Command(BaseCommand):
    """Seed Noble Knight Games prices for all Soulblight Gravelords products."""

    help = (
        'Seeds Noble Knight Games CurrentPrice entries for 37 Soulblight Gravelords '
        'products (SG-001 to SG-037). Source: AOS Soulblight spreadsheet 2026-06-08. '
        'Affiliate links include ?awid=1576. Idempotent.'
    )

    def handle(self, *args, **options):
        """Run the command."""
        nk = Retailer.objects.filter(name='Noble Knight Games').first()
        if not nk:
            self.stderr.write(self.style.ERROR(
                'Noble Knight Games retailer not found — run populate_products first.'
            ))
            return

        created_count = updated_count = skipped_count = 0

        for slug, listing_title, price, url, in_stock, not_available in NK_PRICES:
            product = Product.objects.filter(slug=slug, is_active=True).first()
            if not product:
                self.stdout.write(self.style.WARNING(f'  Skipped (not found): {slug}'))
                skipped_count += 1
                continue

            _, created = CurrentPrice.objects.update_or_create(
                product=product,
                retailer=nk,
                defaults={
                    'url': url,
                    'listing_title': listing_title,
                    'not_available': not_available,
                },
                create_defaults={
                    'price': price,
                    'in_stock': in_stock,
                },
            )
            status = 'Created' if created else 'Updated'
            if not_available:
                label = 'Not Available on NK'
            elif price:
                label = f'${price:.2f}'
            else:
                label = 'Price TBD (scraper will update)'
            self.stdout.write(self.style.SUCCESS(f'  {status}: {product.name} — {label}'))
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nseed_nk_soulblight_gravelords_prices complete. '
            f'{created_count} created, {updated_count} updated, {skipped_count} skipped.'
        ))
