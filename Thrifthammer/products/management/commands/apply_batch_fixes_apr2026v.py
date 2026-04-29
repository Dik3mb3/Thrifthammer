"""
Management command: apply_batch_fixes_apr2026v

Fixes: ebay_search_name for four Nurgle AoS/40K crossover products that
       currently return no valid eBay listings.

ROOT CAUSE (internalized lesson — apply to all future AoS/40K crossover seeds):
  The old search names used the pattern '[Unit] Nurgle Daemon Warhammer'.
  This produces 4 keywords in the local validator: ['nurglings', 'nurgle',
  'daemon', 'warhammer'] requiring ceil(4 * 0.65) = 3 matches.
  AoS-style eBay listing titles — e.g. "Maggotkin of Nurgle Nurglings NIB" —
  only contain 'nurglings' + 'nurgle' = 2 matches → rejected.  The unit-suffix
  fallback checks the last 2 keywords ['daemon', 'warhammer']; neither appears
  in AoS-style titles → also rejected.  Every listing in the top-10 Best Match
  results is rejected → not_available.

  Note: eBay does relevance-based (not strict AND) matching, so it DOES return
  these listings.  The failure is in our local validator, not the eBay query.

CORRECT PATTERN FOR AoS/40K CROSSOVER PRODUCTS:
  Use exactly 3 keywords: '[Unit] [Faction-word] Warhammer'.
  This requires ceil(3 * 0.65) = 2 matches.  AoS-style titles contain
  [Unit] + [Faction-word] → 2/3 → passes.  40K-style titles contain all
  3 → also passes.  This pattern must be used for all future crossover seeds.

Products updated:
  nurgle-nurglings       'Nurglings Nurgle Daemon Warhammer'
                       → 'Nurglings Nurgle Warhammer'
  nurgle-plaguebearers   'Plaguebearers Nurgle Daemon Warhammer'
                       → 'Plaguebearers Nurgle Warhammer'
  nurgle-plague-drones   'Plague Drones Nurgle Daemon Warhammer'
                       → 'Plague Drones Nurgle Warhammer'
  nurgle-rotigus         'Rotigus Nurgle Daemon Warhammer'
                       → 'Rotigus Nurgle Warhammer'

Idempotent — safe to re-run.
"""

from django.core.management.base import BaseCommand

from products.models import Product


FIXES = [
    # (slug, new_ebay_search_name)
    #
    # Pattern: '[Unit] Nurgle Warhammer' gives 3 keywords → needs 2 matches.
    # AoS titles ("Maggotkin of Nurgle Nurglings NIB") match on 'nurglings'
    # + 'nurgle' = 2/3 → passes.  40K titles ("Chaos Daemons Nurglings
    # Warhammer 40K") match all 3 → also passes.
    ('nurgle-nurglings',     'Nurglings Nurgle Warhammer'),
    ('nurgle-plaguebearers', 'Plaguebearers Nurgle Warhammer'),
    ('nurgle-plague-drones', 'Plague Drones Nurgle Warhammer'),
    ('nurgle-rotigus',       'Rotigus Nurgle Warhammer'),
]


class Command(BaseCommand):
    """Fix ebay_search_name for four Nurgle AoS/40K crossover products."""

    help = 'Fix missing eBay listings: correct ebay_search_name for 4 Nurgle crossover products.'

    def handle(self, *args, **options):
        """Run the fix."""
        changed = 0
        for slug, new_name in FIXES:
            try:
                product = Product.objects.get(slug=slug)
            except Product.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                    f'  [{slug}] not found — skipping.'
                ))
                continue

            if product.ebay_search_name == new_name:
                self.stdout.write(
                    f'  [{slug}] already "{new_name}" — no change.'
                )
                continue

            old_name = product.ebay_search_name or '(none)'
            product.ebay_search_name = new_name
            product.save(update_fields=['ebay_search_name'])
            self.stdout.write(self.style.SUCCESS(
                f'  [{slug}] "{old_name}" → "{new_name}"'
            ))
            changed += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. {changed} product(s) updated.'
        ))
