"""
Management command: populate_units

Creates Space Marine UnitType entries and PrebuiltArmy sample lists
so the Army Cost Calculator has realistic data immediately after setup.

Usage:
    python manage.py populate_units
    python manage.py populate_units --clear    # wipe existing data first

All data is idempotent: running the command twice won't create duplicates.
"""

from django.core.management.base import BaseCommand

from calculators.models import PrebuiltArmy, UnitType
from products.models import Faction, Product


class Command(BaseCommand):
    """Populate UnitType and PrebuiltArmy data for the Space Marine calculator."""

    help = 'Populate the Army Calculator with Space Marine units and sample lists.'

    def add_arguments(self, parser):
        """Register command-line arguments."""
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete all existing UnitType and PrebuiltArmy data first.',
        )

    def handle(self, *args, **options):
        """Entry point: create unit types then prebuilt armies."""
        if options['clear']:
            self.stdout.write('Clearing existing calculator data…')
            PrebuiltArmy.objects.all().delete()
            UnitType.objects.all().delete()
            self.stdout.write(self.style.WARNING('Cleared.'))

        unit_types = self._create_unit_types()
        self._create_prebuilt_armies(unit_types)

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Created/updated:\n'
            f'  {UnitType.objects.count()} unit types\n'
            f'  {PrebuiltArmy.objects.count()} prebuilt armies\n'
        ))

    # -------------------------------------------------------------------------
    # Unit type seed data
    # -------------------------------------------------------------------------

    def _create_unit_types(self):
        """
        Create Space Marine unit types across all battlefield roles.

        Attempts to link each unit to a real Product by name match.
        Returns a dict of {name: UnitType}.
        """
        self.stdout.write('Creating unit types…')

        # (name, category, points_cost, typical_quantity, description, product_name_hint)
        unit_data = [
            # ---- HQ ----
            (
                'Primaris Captain', 'hq', 80, 1,
                'The commander of a Space Marine force. Provides re-rolls to nearby units.',
                'Space Marine Primaris Captain',
            ),
            (
                'Librarian', 'hq', 75, 1,
                'A powerful psyker who can smite enemies and buff friendly units.',
                None,
            ),
            (
                'Chaplain', 'hq', 65, 1,
                'A warrior-priest who raises the fervour of nearby Space Marines.',
                None,
            ),
            (
                'Techmarine', 'hq', 70, 1,
                'Maintains vehicles and can restore wounds to damaged war engines.',
                None,
            ),
            # ---- Troops ----
            (
                'Intercessors', 'troops', 20, 5,
                'Reliable bolt rifle-armed troops. The backbone of most Space Marine forces.',
                'Space Marine Intercessors',
            ),
            (
                'Assault Intercessors', 'troops', 20, 5,
                'Close-quarters specialists with chainswords and heavy bolt pistols.',
                'Space Marine Assault Intercessors',
            ),
            (
                'Incursors', 'troops', 22, 5,
                'Scout infiltrators who can deny the opponent cover bonuses.',
                None,
            ),
            (
                'Infiltrators', 'troops', 24, 5,
                'Phobos-armoured troops who can intercept deep-striking units.',
                None,
            ),
            # ---- Elites ----
            (
                'Sternguard Veterans', 'elites', 25, 5,
                'Veteran warriors with access to special ammunition — flexible threat-removal.',
                None,
            ),
            (
                'Bladeguard Veterans', 'elites', 35, 3,
                'Heavy-bolt pistol and power sword specialists in Mk X Gravis armour.',
                None,
            ),
            (
                'Redemptor Dreadnought', 'elites', 185, 1,
                'A towering walker armed with a macro plasma incinerator or onslaught gatling cannon.',
                None,
            ),
            (
                'Sanguinary Guard', 'elites', 35, 5,
                'Blood Angels elite warriors in Artificer armour with glaives encarmine.',
                'Blood Angels Sanguinary Guard',
            ),
            (
                'Death Company Marines', 'elites', 22, 5,
                'Blood Angels warriors consumed by the Black Rage — fearless and furious.',
                'Blood Angels Death Company Marines',
            ),
            (
                'Contemptor Dreadnought', 'elites', 160, 1,
                'A Horus Heresy-era walker, faster and more reactive than modern patterns.',
                'Contemptor Dreadnought',
            ),
            # ---- Fast Attack ----
            (
                'Outriders', 'fast_attack', 45, 3,
                'Agile Primaris bikers that can advance and still fire their bolt rifles.',
                None,
            ),
            (
                'Inceptors', 'fast_attack', 50, 3,
                'Jump-pack assault troops armed with assault bolters or plasma exterminators.',
                None,
            ),
            (
                'Suppressors', 'fast_attack', 45, 3,
                'Phobos-armoured jet-pack troops that suppress enemy overwatch.',
                None,
            ),
            # ---- Heavy Support ----
            (
                'Hellblasters', 'heavy_support', 30, 5,
                'Plasma incinerator-armed troops — high damage, high risk.',
                None,
            ),
            (
                'Eradicators', 'heavy_support', 45, 3,
                'Devastating melta-weapon specialists — first choice for tank hunting.',
                None,
            ),
            (
                'Predator Annihilator', 'heavy_support', 130, 1,
                'Twin lascannon-armed tank hunter. Excellent against vehicles.',
                'Chaos Predator Annihilator',
            ),
            (
                'Repulsor Executioner', 'heavy_support', 210, 1,
                'Heavy grav-tank armed with a macro plasma incinerator or laser destroyer.',
                None,
            ),
            # ---- Dedicated Transport ----
            (
                'Impulsor', 'dedicated_transport', 75, 1,
                'Fast-moving transport skimmer for up to six Primaris infantry.',
                'Space Marine Impulsor',
            ),
            (
                'Repulsor', 'dedicated_transport', 200, 1,
                'Heavily armed grav-tank that transports ten Primaris Marines.',
                'Space Marine Repulsor',
            ),
            (
                'Rhino', 'dedicated_transport', 70, 1,
                'The classic Space Marine transport. Simple, reliable, and cheap.',
                None,
            ),
            # ---- Lord of War ----
            (
                'Roboute Guilliman', 'lord_of_war', 380, 1,
                'The Primarch of the Ultramarines. An army-wide force multiplier.',
                None,
            ),
        ]

        sm_faction = Faction.objects.filter(name='Space Marines').first()
        if not sm_faction:
            self.stdout.write(self.style.WARNING(
                '  No Space Marines faction found — unit faction will be null. '
                'Run populate_products first.'
            ))

        created_units = {}
        for name, category, points, qty, description, product_hint in unit_data:
            # Try to find a matching product
            product = None
            if product_hint:
                product = Product.objects.filter(name=product_hint, is_active=True).first()

            unit, created = UnitType.objects.update_or_create(
                name=name,
                defaults={
                    'category': category,
                    'faction': sm_faction,
                    'product': product,
                    'points_cost': points,
                    'typical_quantity': qty,
                    'description': description,
                    'is_active': True,
                },
            )
            created_units[name] = unit
            status = 'created' if created else 'updated'
            product_info = f' → {product.name}' if product else ' (no product linked)'
            self.stdout.write(f'  [{status}] {name}{product_info}')

        return created_units

    # -------------------------------------------------------------------------
    # Prebuilt army seed data
    # -------------------------------------------------------------------------

    def _create_prebuilt_armies(self, unit_types):
        """
        Create three sample prebuilt Space Marine armies.

        Args:
            unit_types: dict of {unit name: UnitType} from _create_unit_types.
        """
        self.stdout.write('Creating prebuilt armies…')
        sm_faction = Faction.objects.filter(name='Space Marines').first()

        prebuilt_data = [
            {
                'name': 'Beginner Starter (~500pts)',
                'description': (
                    'A compact force perfect for learning the game. '
                    'One captain, two troop choices, and a transport.'
                ),
                'display_order': 1,
                'units': [
                    ('Primaris Captain', 1),
                    ('Intercessors', 2),
                    ('Impulsor', 1),
                ],
            },
            {
                'name': 'Budget 1000pt List (~$350)',
                'description': (
                    'A solid 1000-point competitive list that won\'t break the bank. '
                    'Strong objective control with elite backline support.'
                ),
                'display_order': 2,
                'units': [
                    ('Primaris Captain', 1),
                    ('Chaplain', 1),
                    ('Intercessors', 2),
                    ('Assault Intercessors', 1),
                    ('Bladeguard Veterans', 1),
                    ('Outriders', 1),
                    ('Eradicators', 1),
                    ('Impulsor', 1),
                ],
            },
            {
                'name': 'Competitive 2000pt List (~$650)',
                'description': (
                    'A full 2000-point list designed for competitive play. '
                    'Balanced between mobile infantry, elite units, and heavy fire support.'
                ),
                'display_order': 3,
                'units': [
                    ('Primaris Captain', 1),
                    ('Librarian', 1),
                    ('Chaplain', 1),
                    ('Intercessors', 3),
                    ('Assault Intercessors', 2),
                    ('Bladeguard Veterans', 2),
                    ('Redemptor Dreadnought', 1),
                    ('Outriders', 2),
                    ('Eradicators', 2),
                    ('Hellblasters', 1),
                    ('Impulsor', 2),
                ],
            },
        ]

        for army_def in prebuilt_data:
            # Build the units_data JSON snapshot
            units_data = []
            points_total = 0
            for unit_name, qty in army_def['units']:
                unit = unit_types.get(unit_name)
                if not unit:
                    self.stdout.write(self.style.WARNING(
                        f'  Unit not found: {unit_name} — skipping.'
                    ))
                    continue
                unit_points = unit.points_cost * unit.typical_quantity * qty
                points_total += unit_points
                units_data.append({
                    'unit_type_id': unit.pk,
                    'name': unit.name,
                    'category': unit.category,
                    'quantity': qty,
                    'points': unit.points_cost * unit.typical_quantity,
                })

            army, created = PrebuiltArmy.objects.update_or_create(
                name=army_def['name'],
                defaults={
                    'faction': sm_faction,
                    'description': army_def['description'],
                    'points_total': points_total,
                    'units_data': units_data,
                    'display_order': army_def['display_order'],
                    'is_active': True,
                },
            )
            status = 'created' if created else 'updated'
            self.stdout.write(f'  [{status}] {army.name} ({points_total}pts)')
