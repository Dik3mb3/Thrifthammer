"""
Management command: populate_units

Auto-generates UnitType entries for every active Warhammer 40,000 product
in the database, grouped by faction and assigned to the correct 10th Edition
battlefield role (Epic Hero, Character, Battleline, Infantry, etc.).

Usage:
    python manage.py populate_units
    python manage.py populate_units --clear    # wipe existing UnitType data first

The command is fully idempotent: running it twice will update existing entries
rather than create duplicates. Products that match the skip list (combat patrols,
multi-army box sets) are excluded automatically.

To change role assignment, edit the ROLE_RULES list — rules are checked in order
and the first match wins.
"""

import re

from django.core.management.base import BaseCommand

from calculators.models import PrebuiltArmy, UnitType
from products.models import Category, Faction, Product

# ---------------------------------------------------------------------------
# Products to skip — box sets containing multiple different units
# ---------------------------------------------------------------------------
SKIP_KEYWORDS = [
    'combat patrol',
    'army set',
    'battleforce',
    'vanguard',       # e.g. "Vanguard: Space Marines" mega-sets
    'boarding patrol',
    'strike force',
    'crusade force',
    'launch box',
    'start collecting',
    'getting started',
]

# ---------------------------------------------------------------------------
# 10th Edition battlefield role assignment rules
# Each entry: (role_key, [keyword_fragments_to_match_in_product_name])
# Rules are checked in order — first match wins.
# Product name comparison is case-insensitive.
# ---------------------------------------------------------------------------
ROLE_RULES = [
    # ── Epic Heroes (named special characters) ──────────────────────────────
    ('epic_hero', [
        'mortarion', 'roboute guilliman', 'guilliman',
        'magnus the red', 'magnus',
        'szarekh', 'the silent king',
        'ghazghkull', 'thraka',
        'be\'lakor', 'be lakor',
        'abaddon',
        'angron',
        'fulgrim',
        'daemon prince',
        'saint celestine',
        'inquisitor',
        'lord discordant',
        'mephiston',
        'astorath',
        'lemartes',
        'sanguinor',
        'belisarius cawl',
        'trajann valoris',
        'imotekh',
        'trazyn',
        'orikan',
        'illuminor szeras',
        'swarmlord',
        'hive tyrant',     # named variant
        'old one eye',
        'deathleaper',
        'ambull',
        'ork warboss',
        'ghazghkull thraka',
        'genestealer patriarch',
        'patriarch',
        'aun\'va', 'aun\'shi',
        'shadowsun',
        'commander farsight',
        'farsight',
        'el\'myamoto',
        'archon',          # drukhari special char
        'urien rakarth',
        'lelith hesperax',
        'succubus',
        'fabius bile',
        'lucius the eternal',
        'huron blackheart',
        'kharn the betrayer',
        'ahriman',
        'lord of contagion',
        'typhus',
        'festus',
        'epidemius',
        'lord of skulls',
        'skarbrand',
        'karanak',
        'kairos fateweaver',
        'lord of change',   # named
        'great unclean one',  # named
        'bloodthirster',    # named
        'keeper of secrets', # named
        'brand of chaos',
    ]),
    # ── Characters (generic HQ / leader units) ──────────────────────────────
    ('character', [
        'captain', 'librarian', 'chaplain', 'techmarine', 'apothecary',
        'lieutenant', 'ancient', 'judiciar', 'company heroes',
        'primaris captain', 'primaris lieutenant',
        'warlord', 'warboss', 'big mek', 'weirdboy', 'painboy',
        'warphead',
        'company commander', 'lord castellan', 'lord solar',
        'ursula creed', 'tank commander',
        'tech-priest', 'tech priest', 'dominus', 'enginseer',
        'magos', 'manipulus',
        'canoness', 'palatine',
        'inquisitor',
        'ethereal', 'commander',
        'autarch', 'farseer', 'warlock', 'spiritseer',
        'shaper', 'avatar of khaine',
        'herald',
        'sorcerer', 'lord',
        'dark apostle',
        'master of possession',
        'sorcerer in terminator',
        'exalted',
        'plague surgeon', 'biologus putrifier',
        'noxious blightbringer',
        'skull champion', 'world eaters lord',
        'grand master', 'brother-captain',
        'interrogator-chaplain', 'company ancient',
        'shield-captain',
        'allarus',         # custodes character pattern
        'terminator captain',
        'lord of the hunt',
        'iron father',
        'wolf lord', 'rune priest', 'iron priest',
        'council of the forge',
        'chapter master',
        'iron hands',
        'kroot shaper', 'riptide', 'commander',
        'haemonculus', 'succubus',
        'magus',           # gsc
        'primus',
        'acolyte iconward',
        'votann kinfather', 'kâhl', 'einhyr champion',
        'talos pain engine',  # this is character-ish for drukhari
    ]),
    # ── Battleline ───────────────────────────────────────────────────────────
    ('battleline', [
        'intercessors',
        'tactical squad',
        'scouts',
        'ork boyz', 'gretchin',
        'necron warriors',
        'termagants', 'hormagaunts',
        'guardsmen', 'infantry squad',
        'battle sisters', 'sisters of battle',
        'kabalite warriors',
        'hearthkyn warriors',
        'tzaangors',
        'chaos cultists', 'cultists',
        'plague marines',          # battleline for death guard
        'rubric marines',
        'berzerkers', 'world eaters',
        'noise marines',
        'skitarii rangers', 'skitarii vanguard',
        'fire warriors',
        'pathfinders',
        'dire avengers',
        'guardian defenders', 'storm guardians',
        'rangers',               # craftworlds
        'genestealers',
        'neophyte hybrids',
        'acolyte hybrids',
        'blood claws', 'grey hunters',
        'assault intercessors',
        'infernus squad',
    ]),
    # ── Transport ────────────────────────────────────────────────────────────
    ('transport', [
        'rhino', 'razorback', 'impulsor', 'repulsor',
        'land raider crusader', 'land raider redeemer',
        'chimera', 'taurox', 'valkyrie',
        'trukk', 'battlewagon',
        'ghost ark',
        'terrorfex',
        'devilfish',
        'wave serpent',
        'raider',           # drukhari transport
        'venom',
        'hammerfall bunker',  # technically fortification but treated here
        'transport',
        'spartan',
        'drop pod',
        'stormraven',
        'stormhawk',
        'stormtalon',
        'land speeder storm',
        'boarding craft',
    ]),
    # ── Fortification ────────────────────────────────────────────────────────
    ('fortification', [
        'bunker', 'bastian', 'defense line', 'fortification',
        'hammerfall bunker',
        'aegis', 'void shield',
        'firestrike servo-turret',
        'servo-turret',
        'emplacement',
    ]),
    # ── Mounted ──────────────────────────────────────────────────────────────
    ('mounted', [
        'outriders', 'bikers', 'bike squad', 'invader atv',
        'vertus praetors',
        'rough riders',
        'sentinel',         # astra militarum walker (mounted-style)
        'kâhl on bike',
        'kroot cavalry',
        'shining spears',
        'swooping hawks',   # jump-pack eldar
        'warp spiders',
        'jetbikes',
        'windriders',
        'warbikers',
        'nob bikers',
        'deff koptas',
        'cavalry',
        'cavalry squad',
        'rough riders',
        'canoptek scarabs',
        'tomb blades',
        'wraiths',
        'destroyer',        # necron fast cavalry-style
        'suppressors',
        'inceptors',
        'raptors',
        'warp talons',
        'chaos bikers',
        'plague drones',
        'flesh hounds',
        'screamers',
        'seekers',
    ]),
    # ── Vehicle ──────────────────────────────────────────────────────────────
    ('vehicle', [
        'dreadnought', 'redemptor', 'brutalis', 'ballistus',
        'contemptor', 'leviathan',
        'predator', 'vindicator', 'whirlwind', 'land raider',
        'repulsor executioner',
        'leman russ', 'baneblade', 'shadowsword',
        'basilisk', 'wyvern', 'manticore', 'hydra', 'ordnance',
        'hellhound',
        'looted wagon', 'gorkanaut', 'morkanaut', 'stompa',
        'deff dread', 'killa kans',
        'monolith', 'doomsday ark', 'annihilation barge',
        'triarch stalker',
        'canoptek reanimator',
        'wraithlord', 'wraithknight', 'war walker', 'falcon',
        'fire prism', 'night spinner', 'nightwing', 'crimson hunter',
        'riptide', 'stormsurge', 'coldstar',
        'piranha',
        'ravager', 'cronos',
        'talos',
        'hive crone', 'haruspex', 'tervigon', 'tyrannofex',
        'maleceptor', 'toxicrene',
        'leman russ',
        'deff', 'stompa',
        'dunecrawler', 'archaeopter',
        'armiger', 'knight',
        'repressor',
        'immolator', 'exorcist',
        'rhino',             # also a vehicle for chaos
        'plagueburst crawler',
        'maulerfiend', 'forgefiend', 'heldrake',
        'defiler',
        'sicaran',
        'caladius',
        'pallas',
        'coronus',
        'venerable',
        'gladiator',
        'tank',
        'speeder',
        'atv',
        'walker',
        'crawler',
        'cannon',
        'artillery',
    ]),
    # ── Infantry (catch-all for anything not matched above) ──────────────────
    ('infantry', [
        # Deliberately broad — matches almost everything remaining
        'marines', 'warriors', 'guard', 'squad', 'veterans',
        'terminators', 'hellblasters', 'eradicators',
        'devastators', 'aggressors', 'eliminators',
        'incursors', 'infiltrators', 'inceptors',
        'sternguard', 'vanguard veteran',
        'bladeguard',
        'sanguinary guard', 'death company',
        'wolf guard', 'long fangs',
        'deathwatch',
        'immortals', 'lychguard', 'praetorians', 'triarch',
        'flayed ones', 'deathmarks',
        'ork', 'nobz', 'flash gitz', 'kommandos', 'burna',
        'tankbusta', 'lootas', 'storm boyz',
        'gargoyles', 'zoanthropes', 'neurothropes',
        'tyrant guard', 'warriors', 'raveners',
        'genestealers',
        'gants', 'stealers',
        'skaven',             # unlikely but safe
        'rangers',
        'vanguard',
        'voidsmen',
        'sisters',
        'repentia',
        'arcos',
        'celestians',
        'seraphim',
        'zephyrim',
        'retributor',
        'dominion',
        'obsec',
        'rubric',
        'tzaangor',
        'chaos spawn',
        'mutilators', 'obliterators',
        'blightlord', 'deathshroud',
        'plague',
        'legionaries',
        'chosen',
        'havocs',
        'raptors',
        'possessed',
        'accursed cultists',
        'exalted',
        'hounds',
        'bloodletters', 'plaguebearers', 'daemonettes', 'horrors',
        'nurglings',
        'grey knight',
        'purifiers', 'purgation',
        'paladins',
        'interceptors',
        'strike',
        'acolytes',
        'hybrids',
        'aberrants',
        'clamavus', 'nexos', 'jackal alphus',
        'cognis', 'sydonian', 'ironstrider',
        'electro-priests', 'fulgurites', 'corpuscarii',
        'sicarians',
        'kastelans',
        'onager',
        'custodian',
        'vertus',
        'witchseekers',
        'prosecutor',
        'vigilators',
        'stone',
        'brethren',
        'berserkers',
        'einhyr hearthguard',
        'cthonian',
        'sagitaur',
        'hernkyn',
        'brokhyr',
        'ymyr',
        'kin',
        'kroot', 'krootox',
        'fire warrior',
        'strike team',
        'breacher',
        'hammerhead',
        'sky ray',
        'ghostkeel',
        'stealth',
        'crisis',
        'broadside',
        'dragon',
        'scorpion',
        'banshees',
        'howling',
        'shadow spectres',
        'striking scorpions',
        'wraithblades', 'wraithguard',
        'harlequin',
        'troupe',
        'death jester',
        'solitaire',
    ]),
]


def _assign_role(product_name: str) -> str:
    """
    Assign a 10th Edition battlefield role to a product based on its name.

    Returns the role key string. Falls back to 'infantry' if no rule matches.
    """
    name_lower = product_name.lower()
    for role_key, keywords in ROLE_RULES:
        for kw in keywords:
            if kw.lower() in name_lower:
                return role_key
    return 'infantry'


def _should_skip(product_name: str) -> bool:
    """Return True if this product should be excluded from the calculator."""
    name_lower = product_name.lower()
    return any(kw in name_lower for kw in SKIP_KEYWORDS)


class Command(BaseCommand):
    """
    Populate UnitType entries for all active Warhammer 40,000 products.

    Each active 40K product becomes one UnitType, assigned to its faction
    and given a 10th Edition battlefield role based on keyword matching.
    """

    help = 'Populate the Army Calculator from all active 40K product SKUs.'

    def add_arguments(self, parser):
        """Register command-line arguments."""
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete all existing UnitType and PrebuiltArmy data first.',
        )

    def handle(self, *args, **options):
        """Entry point."""
        if options['clear']:
            self.stdout.write('Clearing existing calculator data…')
            PrebuiltArmy.objects.all().delete()
            UnitType.objects.all().delete()
            self.stdout.write(self.style.WARNING('Cleared.'))

        self._create_unit_types()

        created = UnitType.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f'\nDone! {created} unit types now in the calculator.'
        ))

    def _create_unit_types(self):
        """
        Create or update one UnitType per active 40K product.

        Skips multi-unit box sets. Assigns 10th Ed role via keyword rules.
        """
        self.stdout.write('Scanning 40K products…')

        cat = Category.objects.filter(slug='warhammer-40000').first()
        if not cat:
            self.stdout.write(self.style.ERROR(
                'Warhammer 40,000 category not found. Run populate_products first.'
            ))
            return

        products = (
            Product.objects
            .filter(category=cat, is_active=True)
            .select_related('faction')
            .order_by('faction__name', 'name')
        )

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for product in products:
            if _should_skip(product.name):
                self.stdout.write(f'  [skip]  {product.name}')
                skipped_count += 1
                continue

            role = _assign_role(product.name)

            unit, created = UnitType.objects.update_or_create(
                product=product,
                defaults={
                    'name': product.name,
                    'category': role,
                    'faction': product.faction,
                    'points_cost': 0,       # points to be set manually in admin
                    'typical_quantity': 1,
                    'description': '',
                    'is_active': True,
                },
            )

            if created:
                created_count += 1
                self.stdout.write(
                    f'  [new]   [{role:15}] '
                    f'{product.faction.name if product.faction else "—":20} '
                    f'{product.name}'
                )
            else:
                updated_count += 1

        self.stdout.write(
            f'\n  Created: {created_count}  |  '
            f'Updated: {updated_count}  |  '
            f'Skipped (box sets): {skipped_count}'
        )
