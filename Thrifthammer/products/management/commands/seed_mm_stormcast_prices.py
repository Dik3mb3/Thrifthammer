"""
Management command: seed_mm_stormcast_prices

Seeds Miniature Market CurrentPrice entries for Stormcast Eternals products
that have a confirmed MM listing.

Source: AOS Stormcasts - GW, NK, MM, AMAZON.xlsx (2026-05-13).

Products NOT on MM (no CurrentPrice record created):
  SE-002  Warhammer Age of Sigmar: Introductory Set
  SE-003  Warhammer Age of Sigmar: Starter Set
  SE-006  Stormcast Eternals Stormcoven
  SE-014  Stormcast Eternals Gardus Steel Soul
  SE-015  Stormcast Eternals Endless Spells: Stormcast Eternals
  SE-016  Stormcast Eternals Vandus Hammerhand
  SE-017  Stormcast Eternals Vanguard-Palladors
  SE-018  Stormcast Eternals Lord-Aquilor
  SE-020  Stormcast Eternals Knight-Questor
  SE-023  Stormcast Eternals Celestant-Prime, Hammer of Sigmar
  SE-024  Stormcast Eternals Questor Soulsworn
  SE-026  Stormcast Eternals Lord-Imperatant
  SE-027  Stormcast Eternals Knight-Arcanum
  SE-028  Stormcast Eternals Prosecutors

Dual-kit notes (same MM URL — same physical box):
  SE-007 / SE-008  Karazai / Krondys              → gw-96-50.html
  SE-004 / SE-009  Annihilators variants           → gw-96-55.html
  SE-021 / SE-022  Drakesworn / Lord-Celestant on Stardrake → gw-96-23.html
  SE-037 / SE-038  Knight-Draconis / Stormdrake Guard → gw-96-54.html
  SE-040 / SE-043  Vanguard-Raptors variants       → gw-96-30.html
  SE-041 / SE-042 / SE-044 / SE-045 / SE-046  Dracothian Guard family → gw-96-24.html

Prices are left as None — the scraper will populate on its next Mon/Wed/Sat run.

Safe to run repeatedly (idempotent via update_or_create).

Usage:
    python manage.py seed_mm_stormcast_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_MM = 'https://www.miniaturemarket.com/'

# (slug, listing_title, price, url, in_stock)
# price=None → scraper will update
MM_PRICES = [
    # SE-001  Order Battletome: Stormcast Eternals
    (
        'stormcast-eternals-battletome',
        'Order Battletome: Stormcast Eternals (4th Ed.)',
        None,
        _MM + 'warhammer-age-sigmar-order-battletome-stormcast-eternals-4th-edition-gw-96-01-2024.html',
        False,
    ),
    # SE-004  Stormcast Eternals Annihilators
    # ⚠ Dual kit with SE-009 (Annihilators with Meteoric Grandhammers)
    (
        'stormcast-eternals-annihilators',
        'Stormcast Eternals - Annihilators',
        None,
        _MM + 'gw-96-55.html',
        False,
    ),
    # SE-005  Stormcast Eternals Vanguard-Hunters
    (
        'stormcast-eternals-vanguard-hunters',
        'Stormcast Eternals - Vanguard-Hunters',
        None,
        _MM + 'gw-96-28.html',
        False,
    ),
    # SE-007  Stormcast Eternals Karazai the Scarred
    # ⚠ Dual kit with SE-008 (Krondys, Son of Dracothion)
    (
        'stormcast-eternals-karazai-the-scarred',
        'Stormcast Eternals - Karazai the Scarred / Krondys',
        None,
        _MM + 'gw-96-50.html',
        False,
    ),
    # SE-008  Stormcast Eternals Krondys, Son of Dracothion
    # ⚠ Dual kit with SE-007 (Karazai the Scarred)
    (
        'stormcast-eternals-krondys-son-of-dracothion',
        'Stormcast Eternals - Karazai the Scarred / Krondys',
        None,
        _MM + 'gw-96-50.html',
        False,
    ),
    # SE-009  Stormcast Eternals Annihilators with Meteoric Grandhammers
    # ⚠ Dual kit with SE-004 (Annihilators)
    (
        'stormcast-eternals-annihilators-with-meteoric-grandhammers',
        'Stormcast Eternals - Annihilators',
        None,
        _MM + 'gw-96-55.html',
        False,
    ),
    # SE-010  Stormcast Eternals Vanquishers
    (
        'stormcast-eternals-vanquishers',
        'Stormcast Eternals - Vanquishers',
        None,
        _MM + 'gw-96-51.html',
        False,
    ),
    # SE-011  Stormcast Eternals Vigilors
    (
        'stormcast-eternals-vigilors',
        'Stormcast Eternals - Vigilors',
        None,
        _MM + 'gw-96-53.html',
        False,
    ),
    # SE-012  Stormcast Eternals Lord-Commander Bastian Carthalos
    (
        'stormcast-eternals-lord-commander-bastian-carthalos',
        'Stormcast Eternals - Lord-Commander Bastian Carthalos',
        None,
        _MM + 'gw-96-52.html',
        False,
    ),
    # SE-013  Stormcast Eternals Stormstrike Chariot
    (
        'stormcast-eternals-stormstrike-chariot',
        'Stormcast Eternals - Stormstrike Chariot',
        None,
        _MM + 'gw-96-48.html',
        False,
    ),
    # SE-019  Stormcast Eternals Gryph-hounds
    (
        'stormcast-eternals-gryph-hounds',
        'Stormcast Eternals - Gryph-hounds',
        None,
        _MM + 'gw-96-31.html',
        False,
    ),
    # SE-021  Stormcast Eternals Drakesworn Templar
    # ⚠ Dual kit with SE-022 (Lord-Celestant on Stardrake)
    (
        'stormcast-eternals-drakesworn-templar',
        'Stormcast Eternals - Drakesworn Templar / Lord-Celestant on Stardrake',
        None,
        _MM + 'gw-96-23.html',
        False,
    ),
    # SE-022  Stormcast Eternals Lord-Celestant on Stardrake
    # ⚠ Dual kit with SE-021 (Drakesworn Templar)
    (
        'stormcast-eternals-lord-celestant-on-stardrake',
        'Stormcast Eternals - Drakesworn Templar / Lord-Celestant on Stardrake',
        None,
        _MM + 'gw-96-23.html',
        False,
    ),
    # SE-025  Stormcast Eternals Stormreach Portal
    (
        'stormcast-eternals-stormreach-portal',
        'Stormcast Eternals - Stormreach Portal',
        None,
        _MM + 'warhammer-age-sigmar-stormcast-eternals-stormreach-portal-gw-96-70.html',
        False,
    ),
    # SE-029  Stormcast Eternals Iridan the Witness
    (
        'stormcast-eternals-iridan-the-witness',
        'Stormcast Eternals - Iridan the Witness',
        None,
        _MM + 'warhammer-age-sigmar-stormcast-eternals-iridan-witness-gw-96-71.html',
        False,
    ),
    # SE-030  Stormcast Eternals Reclusians
    (
        'stormcast-eternals-reclusians',
        'Stormcast Eternals - Reclusians',
        None,
        _MM + 'warhammer-age-sigmar-stormcast-eternals-reclusians-gw-96-66.html',
        False,
    ),
    # SE-031  Stormcast Eternals Lord-Terminos
    (
        'stormcast-eternals-lord-terminos',
        'Stormcast Eternals - Lord-Terminos',
        None,
        _MM + 'warhammer-age-sigmar-stormcast-eternals-lord-terminos-gw-96-65.html',
        False,
    ),
    # SE-032  Stormcast Eternals Lord-Relictor
    (
        'stormcast-eternals-lord-relictor',
        'Stormcast Eternals - Lord-Relictor',
        None,
        _MM + 'warhammer-age-sigmar-stormcast-eternals-lord-relictor-gw-96-64.html',
        False,
    ),
    # SE-033  Stormcast Eternals Tornus the Redeemed
    (
        'stormcast-eternals-tornus-the-redeemed',
        'Stormcast Eternals - Tornus the Redeemed',
        None,
        _MM + 'warhammer-age-sigmar-stormcast-eternals-tornus-redeemed-gw-96-69.html',
        False,
    ),
    # SE-034  Stormcast Eternals Stormstrike Palladors
    (
        'stormcast-eternals-stormstrike-palladors',
        'Stormcast Eternals - Stormstrike Palladors',
        None,
        _MM + 'warhammer-age-sigmar-stormcast-eternals-stormstrike-palladors-gw-96-67.html',
        False,
    ),
    # SE-035  Stormcast Eternals Ionus Cryptborn, Warden of Lost Souls
    (
        'stormcast-eternals-ionus-cryptborn',
        'Stormcast Eternals - Ionus Cryptborn',
        None,
        _MM + 'warhammer-age-sigmar-stormcast-eternals-ionus-cryptborn-gw-96-61.html',
        False,
    ),
    # SE-036  Stormcast Eternals The Blacktalons
    (
        'stormcast-eternals-the-blacktalons',
        'Stormcast Eternals - The Blacktalons',
        None,
        _MM + 'warhammer-age-sigmar-stormcast-eternals-the-blacktalons-gw-96-62.html',
        False,
    ),
    # SE-037  Stormcast Eternals Knight-Draconis
    # ⚠ Dual kit with SE-038 (Stormdrake Guard)
    (
        'stormcast-eternals-knight-draconis',
        'Stormcast Eternals - Knight-Draconis / Stormdrake Guard',
        None,
        _MM + 'gw-96-54.html',
        False,
    ),
    # SE-038  Stormcast Eternals Stormdrake Guard
    # ⚠ Dual kit with SE-037 (Knight-Draconis)
    (
        'stormcast-eternals-stormdrake-guard',
        'Stormcast Eternals - Knight-Draconis / Stormdrake Guard',
        None,
        _MM + 'gw-96-54.html',
        False,
    ),
    # SE-039  Stormcast Eternals Knight-Relictor
    (
        'stormcast-eternals-knight-relictor',
        'Stormcast Eternals - Knight-Relictor',
        None,
        _MM + 'gw-96-56.html',
        False,
    ),
    # SE-040  Stormcast Eternals Vanguard-Raptors With Longstrike Crossbows & Aetherwings
    # ⚠ Dual kit with SE-043 (Hurricane Crossbows variant)
    (
        'stormcast-eternals-vanguard-raptors-longstrike',
        'Stormcast Eternals - Vanguard-Raptors',
        None,
        _MM + 'gw-96-30.html',
        False,
    ),
    # SE-041  Stormcast Eternals Tempestors
    # ⚠ Multi-kit: Dracothian Guard box (SE-041/042/044/045/046)
    (
        'stormcast-eternals-tempestors',
        'Stormcast Eternals - Dracothian Guard',
        None,
        _MM + 'gw-96-24.html',
        False,
    ),
    # SE-042  Stormcast Eternals Lord-Celestant on Dracoth
    # ⚠ Multi-kit: Dracothian Guard box (SE-041/042/044/045/046)
    (
        'stormcast-eternals-lord-celestant-on-dracoth',
        'Stormcast Eternals - Dracothian Guard',
        None,
        _MM + 'gw-96-24.html',
        False,
    ),
    # SE-043  Stormcast Eternals Vanguard-Raptors With Hurricane Crossbows & Aetherwings
    # ⚠ Dual kit with SE-040 (Longstrike Crossbows variant)
    (
        'stormcast-eternals-vanguard-raptors-hurricane',
        'Stormcast Eternals - Vanguard-Raptors',
        None,
        _MM + 'gw-96-30.html',
        False,
    ),
    # SE-044  Stormcast Eternals Desolators
    # ⚠ Multi-kit: Dracothian Guard box (SE-041/042/044/045/046)
    (
        'stormcast-eternals-desolators',
        'Stormcast Eternals - Dracothian Guard',
        None,
        _MM + 'gw-96-24.html',
        False,
    ),
    # SE-045  Stormcast Eternals Concussors
    # ⚠ Multi-kit: Dracothian Guard box (SE-041/042/044/045/046)
    (
        'stormcast-eternals-concussors',
        'Stormcast Eternals - Dracothian Guard',
        None,
        _MM + 'gw-96-24.html',
        False,
    ),
    # SE-046  Stormcast Eternals Fulminators
    # ⚠ Multi-kit: Dracothian Guard box (SE-041/042/044/045/046)
    (
        'stormcast-eternals-fulminators',
        'Stormcast Eternals - Dracothian Guard',
        None,
        _MM + 'gw-96-24.html',
        False,
    ),
]


class Command(BaseCommand):
    """Seed Miniature Market prices for Stormcast Eternals products."""

    help = 'Seeds Miniature Market listing URLs for Stormcast Eternals. Idempotent.'

    def handle(self, *args, **options):
        """Run the command."""
        mm = Retailer.objects.filter(name='Miniature Market').first()
        if not mm:
            self.stderr.write(self.style.ERROR(
                'Miniature Market retailer not found -- run populate_products first.'
            ))
            return

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for (slug, listing_title, price, url, in_stock) in MM_PRICES:
            product = Product.objects.filter(slug=slug, is_active=True).first()
            if not product:
                self.stdout.write(self.style.WARNING(
                    f'  Skipped (product not found): {slug}'
                ))
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
            self.stdout.write(
                self.style.SUCCESS(f'  {status}: {product.name} -- Price TBD (scraper will update)')
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. Created={created_count}, Updated={updated_count}, '
            f'Skipped={skipped_count}'
        ))
