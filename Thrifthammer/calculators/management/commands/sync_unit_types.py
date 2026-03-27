"""
Management command: sync_unit_types

Ensures every active Product that belongs to a 40K faction has a
corresponding UnitType entry in the Army Calculator.

Run manually after bulk imports, or it is called automatically at the end
of `import_gw_xlsx` so new SKUs appear in the calculator without any
manual admin work.

Category is inferred from the product name using keyword matching.
You can always refine the category afterwards via the Django admin.

Usage:
    python manage.py sync_unit_types          # create missing entries
    python manage.py sync_unit_types --dry-run # preview without saving
"""

import re

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Product


# ── Keyword → category inference rules (checked in order) ──────────────────
# First match wins.  Add keywords here as the catalogue grows.
_CATEGORY_RULES = [
    # Epic Hero — unique named characters with no duplicates in an army
    ('epic_hero', [
        'dante', 'lemartes', 'sanguinor', 'asmodai', 'azrael', 'belial',
        'lazarus', "lion el'jonson", 'lion el jonson', 'sammael',
        'grimaldus', 'abaddon', 'kharn', 'ahriman', 'mortarion', 'roboute',
        'guilliman', 'syll', 'skarbrand', 'be\'lakor', 'belakor',
        'magnus the red', 'angron', 'szarekh', 'ghazghkull',
        'imotekh', 'ra\'alkar', 'broodlord', 'canis rex',
    ]),
    # Named characters / HQ choices
    ('character', [
        'chaplain', 'librarian', 'apothecary', 'ancient', 'techmarine',
        'captain', 'master ', 'commander', 'warlord', 'lord ', 'marshal',
        'castellan', 'archon', 'sorcerer', 'herald', 'inquisitor',
        'canoness', 'priest', 'warsmith', 'autarch', 'farseer',
        'warlock', 'spiritseer', 'warboss', 'mek ', 'painboy',
        'ethereal', 'kor\'sarro', 'sammael', 'execrator', 'lazarus',
    ]),
    # Vehicles / walkers / aircraft
    ('vehicle', [
        'predator', 'dreadnought', 'land raider', 'rhino', 'razorback',
        'repulsor', 'gladiator', 'impulsor', 'storm raven', 'stormraven',
        'storm talon', 'stormtalon', 'storm speeder', 'stormspeeder',
        'land speeder', 'landspeeder', 'vindicator', 'whirlwind',
        'annihilator', 'redemptor', 'brutalis', 'ballistus',
        'heldrake', 'maulerfiend', 'forgefiend', 'defiler',
        'baal predator', 'baal', 'corvus', 'blackstar',
        'nephilim', 'dark talon', 'ravenwing dark', 'vengeance',
        'hammerhead', 'skyray', 'piranha', 'orca',
        'falcon', 'wave serpent', 'fire prism', 'night spinner',
        'trukk', 'battlewagon', 'deff dread', 'killa kan',
        'armiger', 'dominus', 'questoris', 'cerastus',
        'knight ', ' knight', 'sentinel', 'hellhound', 'leman russ',
        'basilisk', 'manticore', 'baneblade', 'shadowsword',
        'leman russ', 'taurox', 'chimera', 'valkyrie',
        'dunecrawler', 'onager', 'crawler',
        'ghost ark', 'doomsday ark', 'doom scythe', 'night scythe',
        'monolith', 'obelisk',
    ]),
    # Monsters / large beasts
    ('monster', [
        'carnifex', 'tyrannofex', 'tervigon', 'trygon', 'mawloc',
        'exocrine', 'haruspex', 'hierodule', 'hive tyrant',
        'screamer killer', 'psychophage', 'norn emissary',
        'bloodthirster', 'lord of change', 'keeper of secrets',
        'great unclean', 'beast of nurgle',
        'daemon prince', 'soul grinder',
        'stompa', 'gorkanaut', 'morkanaut',
        'squiggoth', 'killakroozer',
        'wraithlord', 'wraithknight',
    ]),
    # Transport boxes
    ('transport', [
        'drop pod', 'droppod', 'boarding patrol',
    ]),
]

# Combat Patrol boxes are bundled starter sets — default to 'infantry' bucket
# (They contain mixed units; the user can move to a more accurate bucket via admin)


def _infer_category(name: str) -> str:
    """
    Infer the UnitType category from a product name using keyword rules.

    Returns one of the UnitType.CATEGORY_CHOICES values.
    Default is 'infantry' when no keywords match.
    """
    n = name.lower()
    for category, keywords in _CATEGORY_RULES:
        if any(kw in n for kw in keywords):
            return category
    return 'infantry'


class Command(BaseCommand):
    """Create UnitType entries for active faction products that lack one."""

    help = (
        'Ensure every active 40K product has a UnitType so it appears '
        'in the Army Calculator. Category is inferred from the product name.'
    )

    def add_arguments(self, parser):
        """Add --dry-run option."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview what would be created without saving anything.',
        )

    def handle(self, *args, **options):
        """Main entry point."""
        dry_run = options['dry_run']
        created = skipped = 0

        # Active products with a 40K faction that have no UnitType yet
        missing = (
            Product.objects
            .filter(
                is_active=True,
                faction__isnull=False,
                faction__category__slug='warhammer-40000',
            )
            .exclude(unit_types__isnull=False)
            .select_related('faction')
            .order_by('faction__name', 'name')
        )

        for product in missing:
            category = _infer_category(product.name)
            if dry_run:
                self.stdout.write(
                    f'  [dry-run] Would create: [{product.faction.name}] '
                    f'{product.name}  →  category={category}'
                )
                created += 1
                continue

            UnitType.objects.create(
                name=product.name,
                faction=product.faction,
                product=product,
                category=category,
                is_active=True,
                points_cost=0,
                typical_quantity=1,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'  [created] [{product.faction.name}] {product.name}  (category={category})'
                )
            )
            created += 1

        if created == 0:
            self.stdout.write('  All active faction products already have UnitType entries.')
        else:
            total_label = 'would create' if dry_run else 'created'
            self.stdout.write(
                self.style.SUCCESS(f'\nDone — {total_label}: {created}')
                + ('' if not dry_run else ' (dry run)')
            )
