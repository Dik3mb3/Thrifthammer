"""
Management command: seed_nk_stormcast_prices

Seeds Noble Knight Games CurrentPrice entries for all 46 Stormcast Eternals
products (SE-001 to SE-046).

Source: AOS Stormcasts - GW, NK, MM, AMAZON.xlsx (2026-05-13).
Affiliate parameter ?awid=1576 appended to all URLs.

Dual-kit notes (same physical box — same NK URL):
  Karazai the Scarred / Krondys, Son of Dracothion     (SE-007 / SE-008)
    → https://www.nobleknight.com/P/2147944072/Krondys-Son-of-Dracothion
  Annihilators / Annihilators with Meteoric Grandhammers (SE-004 / SE-009)
    → https://www.nobleknight.com/P/2147934893/Annihilators
  Drakesworn Templar / Lord-Celestant on Stardrake      (SE-021 / SE-022)
    → https://www.nobleknight.com/P/2147620085/Stardrake
  Knight-Draconis / Stormdrake Guard                    (SE-037 / SE-038)
    → https://www.nobleknight.com/P/2147944069/Stormdrake-Guard
  Vanguard-Raptors Longstrike / Hurricane               (SE-040 / SE-043)
    → https://www.nobleknight.com/P/2147936361/Vanguard-Raptors
  Tempestors / Lord-Celestant on Dracoth / Desolators /
    Concussors / Fulminators                            (SE-041/042/044/045/046)
    → https://www.nobleknight.com/P/2147985845/Dracothian-Guard

Products not on NK (marked not_available=True):
  SE-006  Stormcast Eternals Stormcoven
  SE-014  Stormcast Eternals Gardus Steel Soul
  SE-016  Stormcast Eternals Vandus Hammerhand
  SE-027  Stormcast Eternals Knight-Arcanum
  SE-028  Stormcast Eternals Prosecutors
  SE-029  Stormcast Eternals Iridan the Witness
  SE-032  Stormcast Eternals Lord-Relictor
  SE-033  Stormcast Eternals Tornus the Redeemed

Prices are left as None — the scraper will populate actual prices on its next
Mon/Wed/Sat run.

Safe to run repeatedly (idempotent via update_or_create).

Usage:
    python manage.py seed_nk_stormcast_prices
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

    # SE-001  Order Battletome: Stormcast Eternals
    (
        'stormcast-eternals-battletome',
        'Order Battletome - Stormcast Eternals 2024 Edition',
        None,
        _NK + '/P/2148304082/Order-Battletome---Stormcast-Eternals-2024-Edition' + _AFF,
        False, False,
    ),
    # SE-002  Warhammer Age of Sigmar: Introductory Set
    (
        'age-of-sigmar-introductory-set',
        'Age of Sigmar Introductory Set',
        None,
        _NK + '/P/2148179065/Age-of-Sigmar-Introductory-Set' + _AFF,
        False, False,
    ),
    # SE-003  Warhammer Age of Sigmar: Starter Set
    (
        'age-of-sigmar-starter-set',
        'Age of Sigmar - Skaventide Starter Set',
        None,
        _NK + '/P/2148169698/Age-of-Sigmar---Skaventide-Starter-Set' + _AFF,
        False, False,
    ),
    # SE-004  Stormcast Eternals Annihilators
    # ⚠ Dual kit with SE-009 (Annihilators with Meteoric Grandhammers)
    (
        'stormcast-eternals-annihilators',
        'Annihilators',
        None,
        _NK + '/P/2147934893/Annihilators' + _AFF,
        False, False,
    ),
    # SE-005  Stormcast Eternals Vanguard-Hunters
    (
        'stormcast-eternals-vanguard-hunters',
        'Vanguard Hunters 2017 Edition',
        None,
        _NK + '/P/2147655483/Vanguard-Hunters-2017-Edition' + _AFF,
        False, False,
    ),
    # SE-006  Stormcast Eternals Stormcoven — NOT on NK
    ('stormcast-eternals-stormcoven', '', None, '', False, True),
    # SE-007  Stormcast Eternals Karazai the Scarred
    # ⚠ Dual kit with SE-008 (Krondys, Son of Dracothion)
    (
        'stormcast-eternals-karazai-the-scarred',
        'Krondys Son of Dracothion',
        None,
        _NK + '/P/2147944072/Krondys-Son-of-Dracothion' + _AFF,
        False, False,
    ),
    # SE-008  Stormcast Eternals Krondys, Son of Dracothion
    # ⚠ Dual kit with SE-007 (Karazai the Scarred)
    (
        'stormcast-eternals-krondys-son-of-dracothion',
        'Krondys Son of Dracothion',
        None,
        _NK + '/P/2147944072/Krondys-Son-of-Dracothion' + _AFF,
        False, False,
    ),
    # SE-009  Stormcast Eternals Annihilators with Meteoric Grandhammers
    # ⚠ Dual kit with SE-004 (Annihilators)
    (
        'stormcast-eternals-annihilators-with-meteoric-grandhammers',
        'Annihilators',
        None,
        _NK + '/P/2147934893/Annihilators' + _AFF,
        False, False,
    ),
    # SE-010  Stormcast Eternals Vanquishers
    (
        'stormcast-eternals-vanquishers',
        'Vanquishers',
        None,
        _NK + '/P/2147934895/Vanquishers' + _AFF,
        False, False,
    ),
    # SE-011  Stormcast Eternals Vigilors
    (
        'stormcast-eternals-vigilors',
        'Vigilors',
        None,
        _NK + '/P/2147934896/Vigilors' + _AFF,
        False, False,
    ),
    # SE-012  Stormcast Eternals Lord-Commander Bastian Carthalos
    (
        'stormcast-eternals-lord-commander-bastian-carthalos',
        'Lord-Commander Bastian Carthalos',
        None,
        _NK + '/P/2147934901/Lord-Commander-Bastian-Carthalos' + _AFF,
        False, False,
    ),
    # SE-013  Stormcast Eternals Stormstrike Chariot
    (
        'stormcast-eternals-stormstrike-chariot',
        'Stormstrike Chariot',
        None,
        _NK + '/P/2147926816/Stormstrike-Chariot' + _AFF,
        False, False,
    ),
    # SE-014  Stormcast Eternals Gardus Steel Soul — NOT on NK
    ('stormcast-eternals-gardus-steel-soul', '', None, '', False, True),
    # SE-015  Stormcast Eternals Endless Spells: Stormcast Eternals
    (
        'stormcast-eternals-endless-spells',
        'Stormcast Eternals - Endless Spells',
        None,
        _NK + '/P/2147708107/Stormcast-Eternals---Endless-Spells' + _AFF,
        False, False,
    ),
    # SE-016  Stormcast Eternals Vandus Hammerhand — NOT on NK
    ('stormcast-eternals-vandus-hammerhand', '', None, '', False, True),
    # SE-017  Stormcast Eternals Vanguard-Palladors
    (
        'stormcast-eternals-vanguard-palladors',
        'Vanguard-Palladors',
        None,
        _NK + '/P/2147655759/Vanguard-Palladors' + _AFF,
        False, False,
    ),
    # SE-018  Stormcast Eternals Lord-Aquilor
    (
        'stormcast-eternals-lord-aquilor',
        'Lord-Aquilor',
        None,
        _NK + '/P/2147655761/Lord-Aquilor' + _AFF,
        False, False,
    ),
    # SE-019  Stormcast Eternals Gryph-hounds
    (
        'stormcast-eternals-gryph-hounds',
        'Gryph-Hounds',
        None,
        _NK + '/P/2147655581/Gryph-Hounds' + _AFF,
        False, False,
    ),
    # SE-020  Stormcast Eternals Knight-Questor
    (
        'stormcast-eternals-knight-questor',
        'Knight Questor Dacian Anvil',
        None,
        _NK + '/P/2147862326/Knight-Questor-Dacian-Anvil' + _AFF,
        False, False,
    ),
    # SE-021  Stormcast Eternals Drakesworn Templar
    # ⚠ Dual kit with SE-022 (Lord-Celestant on Stardrake)
    (
        'stormcast-eternals-drakesworn-templar',
        'Stardrake',
        None,
        _NK + '/P/2147620085/Stardrake' + _AFF,
        False, False,
    ),
    # SE-022  Stormcast Eternals Lord-Celestant on Stardrake
    # ⚠ Dual kit with SE-021 (Drakesworn Templar)
    (
        'stormcast-eternals-lord-celestant-on-stardrake',
        'Stardrake',
        None,
        _NK + '/P/2147620085/Stardrake' + _AFF,
        False, False,
    ),
    # SE-023  Stormcast Eternals Celestant-Prime, Hammer of Sigmar
    (
        'stormcast-eternals-celestant-prime',
        'Celestant-Prime',
        None,
        _NK + '/P/2147594595/Celestant-Prime' + _AFF,
        False, False,
    ),
    # SE-024  Stormcast Eternals Questor Soulsworn
    (
        'stormcast-eternals-questor-soulsworn',
        'Questor Soulsworn',
        None,
        _NK + '/P/2148070749/Questor-Soulsworn' + _AFF,
        False, False,
    ),
    # SE-025  Stormcast Eternals Stormreach Portal
    (
        'stormcast-eternals-stormreach-portal',
        'Stormreach Portal',
        None,
        _NK + '/P/2148320469/Stormreach-Portal' + _AFF,
        False, False,
    ),
    # SE-026  Stormcast Eternals Lord-Imperatant
    (
        'stormcast-eternals-lord-imperatant',
        'Lord-Imperitant Webstore Edition',
        None,
        _NK + '/P/2148217569/Lord-Imperitant-Webstore-Edition' + _AFF,
        False, False,
    ),
    # SE-027  Stormcast Eternals Knight-Arcanum — NOT on NK
    ('stormcast-eternals-knight-arcanum', '', None, '', False, True),
    # SE-028  Stormcast Eternals Prosecutors — NOT on NK
    ('stormcast-eternals-prosecutors', '', None, '', False, True),
    # SE-029  Stormcast Eternals Iridan the Witness — NOT on NK
    ('stormcast-eternals-iridan-the-witness', '', None, '', False, True),
    # SE-030  Stormcast Eternals Reclusians
    (
        'stormcast-eternals-reclusians',
        'Reclusians',
        None,
        _NK + '/P/2148238304/Reclusians' + _AFF,
        False, False,
    ),
    # SE-031  Stormcast Eternals Lord-Terminos
    (
        'stormcast-eternals-lord-terminos',
        'Lord-Terminos',
        None,
        _NK + '/P/2148238331/Lord-Terminos' + _AFF,
        False, False,
    ),
    # SE-032  Stormcast Eternals Lord-Relictor — NOT on NK
    ('stormcast-eternals-lord-relictor', '', None, '', False, True),
    # SE-033  Stormcast Eternals Tornus the Redeemed — NOT on NK
    ('stormcast-eternals-tornus-the-redeemed', '', None, '', False, True),
    # SE-034  Stormcast Eternals Stormstrike Palladors
    (
        'stormcast-eternals-stormstrike-palladors',
        'Stormstrike Palladors',
        None,
        _NK + '/P/2148320463/Stormstrike-Palladors' + _AFF,
        False, False,
    ),
    # SE-035  Stormcast Eternals Ionus Cryptborn, Warden of Lost Souls
    (
        'stormcast-eternals-ionus-cryptborn',
        'Ionus Cryptborn Warden of Lost Souls',
        None,
        _NK + '/P/2148112910/Ionus-Cryptborn-Warden-of-Lost-Souls' + _AFF,
        False, False,
    ),
    # SE-036  Stormcast Eternals The Blacktalons
    (
        'stormcast-eternals-the-blacktalons',
        'Blacktalons, The',
        None,
        _NK + '/P/2148095134/Blacktalons-The' + _AFF,
        False, False,
    ),
    # SE-037  Stormcast Eternals Knight-Draconis
    # ⚠ Dual kit with SE-038 (Stormdrake Guard)
    (
        'stormcast-eternals-knight-draconis',
        'Stormdrake Guard',
        None,
        _NK + '/P/2147944069/Stormdrake-Guard' + _AFF,
        False, False,
    ),
    # SE-038  Stormcast Eternals Stormdrake Guard
    # ⚠ Dual kit with SE-037 (Knight-Draconis)
    (
        'stormcast-eternals-stormdrake-guard',
        'Stormdrake Guard',
        None,
        _NK + '/P/2147944069/Stormdrake-Guard' + _AFF,
        False, False,
    ),
    # SE-039  Stormcast Eternals Knight-Relictor
    (
        'stormcast-eternals-knight-relictor',
        'Knight-Relictor',
        None,
        _NK + '/P/2147934902/Knight-Relictor' + _AFF,
        False, False,
    ),
    # SE-040  Stormcast Eternals Vanguard-Raptors With Longstrike Crossbows & Aetherwings
    # ⚠ Dual kit with SE-043 (Hurricane Crossbows variant)
    (
        'stormcast-eternals-vanguard-raptors-longstrike',
        'Vanguard-Raptors',
        None,
        _NK + '/P/2147936361/Vanguard-Raptors' + _AFF,
        False, False,
    ),
    # SE-041  Stormcast Eternals Tempestors
    # ⚠ Multi-kit: Dracothian Guard box (SE-041/042/044/045/046)
    (
        'stormcast-eternals-tempestors',
        'Dracothian Guard',
        None,
        _NK + '/P/2147985845/Dracothian-Guard' + _AFF,
        False, False,
    ),
    # SE-042  Stormcast Eternals Lord-Celestant on Dracoth
    # ⚠ Multi-kit: Dracothian Guard box (SE-041/042/044/045/046)
    (
        'stormcast-eternals-lord-celestant-on-dracoth',
        'Dracothian Guard',
        None,
        _NK + '/P/2147985845/Dracothian-Guard' + _AFF,
        False, False,
    ),
    # SE-043  Stormcast Eternals Vanguard-Raptors With Hurricane Crossbows & Aetherwings
    # ⚠ Dual kit with SE-040 (Longstrike Crossbows variant)
    (
        'stormcast-eternals-vanguard-raptors-hurricane',
        'Vanguard-Raptors',
        None,
        _NK + '/P/2147936361/Vanguard-Raptors' + _AFF,
        False, False,
    ),
    # SE-044  Stormcast Eternals Desolators
    # ⚠ Multi-kit: Dracothian Guard box (SE-041/042/044/045/046)
    (
        'stormcast-eternals-desolators',
        'Dracothian Guard',
        None,
        _NK + '/P/2147985845/Dracothian-Guard' + _AFF,
        False, False,
    ),
    # SE-045  Stormcast Eternals Concussors
    # ⚠ Multi-kit: Dracothian Guard box (SE-041/042/044/045/046)
    (
        'stormcast-eternals-concussors',
        'Dracothian Guard',
        None,
        _NK + '/P/2147985845/Dracothian-Guard' + _AFF,
        False, False,
    ),
    # SE-046  Stormcast Eternals Fulminators
    # ⚠ Multi-kit: Dracothian Guard box (SE-041/042/044/045/046)
    (
        'stormcast-eternals-fulminators',
        'Dracothian Guard',
        None,
        _NK + '/P/2147985845/Dracothian-Guard' + _AFF,
        False, False,
    ),
]


class Command(BaseCommand):
    """Seed Noble Knight Games prices for all Stormcast Eternals products."""

    help = (
        'Seeds Noble Knight Games CurrentPrice entries for 46 Stormcast Eternals '
        'products (SE-001 to SE-046). Source: AOS Stormcasts spreadsheet 2026-05-13. '
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

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for (slug, listing_title, price, url, in_stock, not_available) in NK_PRICES:
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
            f'\nseed_nk_stormcast_prices complete. '
            f'{created_count} created, {updated_count} updated, {skipped_count} skipped.'
        ))
