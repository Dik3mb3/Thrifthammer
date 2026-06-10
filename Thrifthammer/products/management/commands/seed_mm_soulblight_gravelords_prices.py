"""
Management command: seed_mm_soulblight_gravelords_prices

Seeds Miniature Market CurrentPrice entries for Soulblight Gravelords products
that have a confirmed MM listing.

Source: AOS Soulblight - GW, NK, MM.xlsx (2026-06-08).

Products NOT on MM (no CurrentPrice record created):
  SG-001  Soulblight Gravelords – The Summons
  SG-002  Soulblight Gravelords – Karlina von Carstein
  SG-005  Lady Annika, the Thirsting Blade
  SG-014  Neferata, Mortarch of Blood
  SG-015  Mannfred von Carstein, Mortarch of Night
  SG-017  Mortis Engine
  SG-018  Coven Throne
  SG-019  Corpse Cart
  SG-020  Askurgan Trueblades
  SG-021  Wight Lord on Skeletal Steed
  SG-022  Soulblight Gravelords: Manifestations
  SG-032  Kritza, the Rat Prince
  SG-033  Radukar the Wolf

Dual-kit notes (same MM URL — same physical box):
  SG-009 / SG-012  Vengorian Lord / Lauka Vai, Mother of Nightmares
    → gw-91-53.html

Prices are left as None — the scraper will populate on its next Mon/Wed/Sat run.

Safe to run repeatedly (idempotent via update_or_create).

Usage:
    python manage.py seed_mm_soulblight_gravelords_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_MM = 'https://www.miniaturemarket.com/'

# ── MM price data ─────────────────────────────────────────────────────────────
# (slug, listing_title, price, url, in_stock)
# price=None → scraper will update
MM_PRICES = [

    # SG-003  Spearhead: Soulblight Gravelords – Deathrattle Tomb Host
    (
        'spearhead-soulblight-gravelords-deathrattle-tomb-host',
        'Spearhead: Soulblight Gravelords - Deathrattle Tomb Host',
        None,
        _MM + 'Age-of-Sigmar-Spearhead-Soulblight-Gravelords-Deathrattle-Tomb-Host/GW-70-916',
        False,
    ),
    # SG-004  Ivya Volga, the Outcast
    (
        'ivya-volga-the-outcast',
        'Soulblight Gravelords: Ivya Volga, the Outcast',
        None,
        _MM + 'warhammer-age-of-sigmar-soulblight-gravelords-ivya-volga-the-outcast-gw-91-17-2023.html',
        False,
    ),
    # SG-006  Dire Wolves
    (
        'dire-wolves',
        'Soulblight Gravelords - Dire Wolves',
        None,
        _MM + 'gw-91-45.html',
        False,
    ),
    # SG-007  Radukar the Beast
    (
        'radukar-the-beast',
        'Soulblight Gravelords - Radukar the Beast',
        None,
        _MM + 'gw-91-56.html',
        False,
    ),
    # SG-008  Belladamma Volga, First of the Vyrkos
    (
        'belladamma-volga-first-of-the-vyrkos',
        'Soulblight Gravelords - Belladamma Volga, First of the Vyrkos',
        None,
        _MM + 'gw-91-55.html',
        False,
    ),
    # SG-009  Vengorian Lord
    # ⚠ Dual kit with SG-012 (Lauka Vai, Mother of Nightmares)
    (
        'vengorian-lord',
        'Soulblight Gravelords - Vengorian Lord / Lauka Vai',
        None,
        _MM + 'gw-91-53.html',
        False,
    ),
    # SG-010  Blood Knights
    (
        'blood-knights',
        'Soulblight Gravelords - Blood Knights',
        None,
        _MM + 'gw-91-41.html',
        False,
    ),
    # SG-011  Fell Bats
    (
        'fell-bats',
        'Soulblight Gravelords - Fell Bats',
        None,
        _MM + 'gw-91-59.html',
        False,
    ),
    # SG-012  Lauka Vai, Mother of Nightmares
    # ⚠ Dual kit with SG-009 (Vengorian Lord)
    (
        'lauka-vai-mother-of-nightmares',
        'Soulblight Gravelords - Vengorian Lord / Lauka Vai',
        None,
        _MM + 'gw-91-53.html',
        False,
    ),
    # SG-013  Vargheists
    (
        'vargheists',
        'Soulblight Gravelords - Vargheists',
        None,
        _MM + 'gw-91-13.html',
        False,
    ),
    # SG-016  Nagash, Supreme Lord of the Undead
    (
        'nagash-supreme-lord-of-the-undead',
        'Nagash, Supreme Lord of the Undead',
        None,
        _MM + 'gw-93-05.html',
        False,
    ),
    # SG-023  Cursed Sepulchre/Nexus of Grief
    (
        'cursed-sepulchrenexus-of-grief',
        'Soulblight Gravelords - Cursed Sepulchre',
        None,
        _MM + 'warhammer-age-sigmar-soulblight-gravelords-cursed-sepulchre-gw-91-88.html',
        False,
    ),
    # SG-024  Deathrattle Skeletons
    (
        'deathrattle-skeletons',
        'Soulblight Gravelords - Deathrattle Skeletons',
        None,
        _MM + 'warhammer-age-sigmar-soulblight-gravelords-deathrattle-skeletons-gw-91-42.html',
        False,
    ),
    # SG-025  Barrow Knights
    (
        'barrow-knights',
        'Soulblight Gravelords - Barrow Knights',
        None,
        _MM + 'warhammer-age-sigmar-soulblight-gravelords-barrow-knights-gw-91-85.html',
        False,
    ),
    # SG-026  Barrow Guard
    (
        'barrow-guard',
        'Soulblight Gravelords - Barrow Guard',
        None,
        _MM + 'warhammer-age-sigmar-soulblight-gravelords-barrow-guard-gw-91-84.html',
        False,
    ),
    # SG-027  Vampire Lord on Nightmare Steed
    (
        'vampire-lord-on-nightmare-steed',
        'Soulblight Gravelords - Vampire Lord on Nightmare Steed',
        None,
        _MM + 'warhammer-age-sigmar-soulblight-gravelords-vampire-lord-on-nightmare-steed-gw-91-82.html',
        False,
    ),
    # SG-028  Prince Vhordrai, Lord of the Crimson Keep
    (
        'prince-vhordrai-lord-of-the-crimson-keep',
        'Soulblight Gravelords - Prince Vhordrai, Lord of the Crimson Keep',
        None,
        _MM + 'warhammer-age-sigmar-soulblight-gravelords-prince-vhordrai-lord-crimson-keep-gw-91-80.html',
        False,
    ),
    # SG-029  Blades of the Hollow King
    (
        'blades-of-the-hollow-king',
        'Soulblight Gravelords - Blades of the Hollow King',
        None,
        _MM + 'warhammer-age-sigmar-soulblight-gravelords-blades-hollow-king-gw-91-76-2025.html',
        False,
    ),
    # SG-030  Sekhar, Fang of Nulahmia
    (
        'sekhar-fang-of-nulahmia',
        'Soulblight Gravelords - Sekhar, Fang of Nulahmia',
        None,
        _MM + 'warhammer-age-sigmar-soulblight-gravelords-sekhar-fang-nulahmia-gw-91-73.html',
        False,
    ),
    # SG-031  Death Battletome: Soulblight Gravelords
    (
        'death-battletome-soulblight-gravelords',
        'Death Battletome: Soulblight Gravelords',
        None,
        _MM + 'warhammer-age-sigmar-death-battletome-soulblight-gravelords-gw-91-04.html',
        False,
    ),
    # SG-034  Deadwalker Zombies
    (
        'deadwalker-zombies',
        'Soulblight Gravelords - Deadwalker Zombies',
        None,
        _MM + 'gw-91-07-2021.html',
        False,
    ),
    # SG-035  Vampire Lord
    (
        'vampire-lord',
        'Soulblight Gravelords - Vampire Lord',
        None,
        _MM + 'gw-91-52.html',
        False,
    ),
    # SG-036  Wight King
    (
        'wight-king',
        'Soulblight Gravelords - Wight King',
        None,
        _MM + 'gw-91-31.html',
        False,
    ),
    # SG-037  Necromancer
    (
        'necromancer',
        'Soulblight Gravelords - Necromancer',
        None,
        _MM + 'gw-91-34.html',
        False,
    ),
]


class Command(BaseCommand):
    """Seed Miniature Market prices for Soulblight Gravelords products."""

    help = (
        'Seeds Miniature Market CurrentPrice entries for 24 Soulblight Gravelords '
        'products that have confirmed MM listings. Source: AOS Soulblight '
        'spreadsheet 2026-06-08. Idempotent.'
    )

    def handle(self, *args, **options):
        """Run the command."""
        mm = Retailer.objects.filter(name='Miniature Market').first()
        if not mm:
            self.stderr.write(self.style.ERROR(
                'Miniature Market retailer not found — run populate_products first.'
            ))
            return

        created_count = updated_count = skipped_count = 0

        for slug, listing_title, price, url, in_stock in MM_PRICES:
            product = Product.objects.filter(slug=slug, is_active=True).first()
            if not product:
                self.stdout.write(self.style.WARNING(f'  Skipped (not found): {slug}'))
                skipped_count += 1
                continue

            _, created = CurrentPrice.objects.update_or_create(
                product=product,
                retailer=mm,
                defaults={
                    'url': url,
                    'listing_title': listing_title,
                    'not_available': False,
                },
                create_defaults={
                    'price': price,
                    'in_stock': in_stock,
                },
            )
            status = 'Created' if created else 'Updated'
            label = f'${price:.2f}' if price else 'Price TBD (scraper will update)'
            self.stdout.write(self.style.SUCCESS(f'  {status}: {product.name} — {label}'))
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nseed_mm_soulblight_gravelords_prices complete. '
            f'{created_count} created, {updated_count} updated, {skipped_count} skipped.'
        ))
