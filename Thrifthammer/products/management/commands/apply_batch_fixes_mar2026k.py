"""
Management command: apply_batch_fixes_mar2026k

Eleventh wave of March 2026 batch corrections for ThriftHammer.
Run after apply_batch_fixes_mar2026j.

Changes covered:
  Section 1  - Miniature Market mass OOS correction
               Manual browser verification (fetch-based, same-origin) of every
               active MM CurrentPrice confirmed that ~121 products are Out of
               Stock on MM's website but are still flagged in_stock=True in the
               DB.  This section sets in_stock=False on every confirmed OOS
               entry so the product detail pages show correct stock status.

               The 11 products still genuinely In Stock at MM are left
               unchanged:
                 41-03  Blood Angels Astorath
                 41-04  Blood Angels Commander Dante
                 41-05  Blood Angels Lemartes
                 41-06  Blood Angels Sanguinary Guard
                 48-28  Space Marine Firestrike Servo-Turrets
                 73-12  Leagues of Votann Hernkyn Pioneers
                 73-14  Leagues of Votann Einhyr Hearthguard
                 94-10  Ossiarch Bonereapers Mortek Guard
                 96-14  Stormcast Eternals Lord-Celestant
                 96-50  Stormcast Eternals Vindictors
                 HA-020 Solar Auxilia Lasrifle Section

  Section 2  - 55-16 Ultramarines Honour Guard MM fix
               The existing MM URL (gw-55-21.html) is the Marneus Calgar with
               Victrix Honour Guard combined box — wrong product.
               The new 2025 standalone Honour Guard kit (B0FXNDT7XR) has no
               MM listing yet.  Setting not_available=True on the MM row so
               the product page no longer shows a broken link.

Usage:
    python manage.py apply_batch_fixes_mar2026k
    python manage.py apply_batch_fixes_mar2026k --dry-run
"""

import decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer


# ===========================================================================
# SKUs confirmed OOS at Miniature Market via browser fetch (2026-03-17)
# — in_stock should be False; prices and URLs kept for reference
# ===========================================================================
MM_OOS_SKUS = [
    # Adeptus Custodes
    '01-02',    # Trajann Valoris
    '01-08',    # Custodian Guard Squad
    '01-10',    # Custodian Wardens
    '01-11',    # Vertus Praetors

    # Deathwatch
    '39-01',    # Watch Captain Artemis
    '39-02',    # Deathwatch Watch Master
    '39-04',    # Corvus Blackstar

    # Blood Angels
    '41-02',    # Mephiston
    '41-08',    # The Sanguinor
    '41-09',    # Sanguinary Priest

    # Chaos / Traitor Legions
    '43-02',    # Thousand Sons Magnus the Red
    '43-04',    # World Eaters Angron
    '43-08',    # Death Guard Typhus
    '43-30',    # Thousand Sons Ahriman
    '43-35',    # Thousand Sons Rubric Marines
    '43-36',    # Thousand Sons Scarab Occult Terminators
    '43-38',    # Thousand Sons Exalted Sorcerers
    '43-50',    # Death Guard Plague Marines
    '43-54',    # Death Guard Blightlord Terminators
    '43-55',    # Death Guard Foetid Bloat-drone
    '43-56',    # Death Guard Deathshroud Bodyguard
    '43-62',    # World Eaters Eightbound

    # Dark Angels
    '44-03',    # Asmodai
    '44-04',    # Azrael
    '44-05',    # Belial
    '44-06',    # Lion El'Jonson
    '44-09',    # Ravenwing Command Squad
    '44-10',    # Deathwing Knights
    '44-12',    # Ravenwing Black Knights
    '44-13',    # Inner Circle Companions

    # Drukhari
    '45-02',    # Archon
    '45-10',    # Raider

    # Craftworlds / Aeldari
    '46-06',    # Dire Avengers
    '46-09',    # Guardians
    '46-14',    # Fire Dragons
    '46-29',    # Wave Serpent

    # Astra Militarum
    '47-05',    # Chimera
    '47-08',    # Commissar
    '47-30',    # Cadian Shock Troops

    # Space Marines
    '48-06',    # Terminator Squad
    '48-07',    # Tactical Squad
    '48-08',    # Vanguard Veteran Squad
    '48-15',    # Devastator Squad
    '48-22',    # Land Raider Crusader
    '48-23',    # Predator
    '48-26',    # Vindicator
    '48-27',    # Hammerfall Bunker
    '48-30',    # Librarian
    '48-32',    # Chaplain
    '48-34',    # Ancient
    '48-37',    # Company Heroes
    '48-38',    # Bladeguard Veterans
    '48-39',    # Eradicators
    '48-40',    # Outriders
    '48-41',    # Infiltrators
    '48-42',    # Invader ATV
    '48-43',    # Sternguard Veteran Squad
    '48-44',    # Brutalis Dreadnought
    '48-45',    # Infernus Squad
    '48-46',    # Ballistus Dreadnought
    '48-61',    # Primaris Lieutenant
    '48-62',    # Primaris Captain
    '48-75',    # Intercessors
    '48-76',    # Assault Intercessors
    '48-92',    # Aggressors
    '48-93',    # Redemptor Dreadnought
    '48-94',    # Impulsor
    '48-95',    # Repulsor Executioner
    '48-97',    # Inceptors
    '48-98',    # Primaris Eliminators

    # Necrons
    '49-03',    # Overlord
    '49-06',    # Warriors
    '49-08',    # Monolith
    '49-10',    # Immortals
    '49-11',    # Lychguard
    '49-14',    # Canoptek Spyder
    '49-17',    # Flayed Ones
    '49-20',    # C'tan Shard of the Void Dragon
    '49-21',    # Psychomancer

    # Orks
    '50-02',    # Warboss in Mega Armour
    '50-09',    # Nobz
    '50-10',    # Boyz
    '50-11',    # Trukk
    '50-12',    # Meganobz
    '50-14',    # Lootas
    '50-15',    # Killa Kans
    '50-20',    # Flash Gitz
    '50-22',    # Battlewagon

    # Tyranids / Genestealer Cults
    '51-04',    # Hive Tyrant
    '51-08',    # Tyranid Warriors
    '51-16',    # Termagants
    '51-40',    # Neophyte Hybrids
    '51-41',    # Acolyte Hybrids
    '51-43',    # Magus
    '51-44',    # Aberrants

    # Adepta Sororitas
    '52-02',    # Morvenn Vahl
    '52-08',    # Exorcist
    '52-09',    # Immolator
    '52-12',    # Seraphim Squad
    '52-15',    # Retributor Squad
    '52-20',    # Battle Sisters Squad
    '52-22',    # Celestian Sacresants

    # Space Wolves
    '53-02',    # Ragnar Blackmane
    '53-06',    # Grey Hunters
    '53-08',    # Wolf Guard Terminators
    '53-10',    # Thunderwolf Cavalry

    # Imperial Knights
    '54-20',    # Armigers
    '54-21',    # Knight Dominus

    # Ultramarines / Black Templars
    '55-02',    # Roboute Guilliman
    '55-12',    # Marneus Calgar (with Victrix Honour Guard box — OOS at MM)
    '55-21',    # Black Templars Helbrecht
    '55-23',    # Black Templars Sword Brethren
    '55-24',    # Black Templars Chaplain Grimaldus
    '55-26',    # Black Templars Execrator
    '55-27',    # Black Templars Crusade Ancient

    # T'au
    '56-06',    # Fire Warriors
    '56-10',    # Hammerhead Gunship
    '56-13',    # Broadside Battlesuit
    '56-14',    # T'au Stealth Battlesuits
    '56-16',    # Riptide Battlesuit
    '56-22',    # Ethereal

    # Grey Knights
    '57-06',    # Strike Squad
    '57-08',    # Terminators
    '57-14',    # Dreadknight
    '57-20',    # Combat Patrol

    # Adeptus Mechanicus
    '59-06',    # Tech-Priest Dominus
    '59-10',    # Skitarii Rangers
    '59-11',    # Skitarii Vanguard
    '59-16',    # Dunecrawler

    # Age of Sigmar — Spearhead
    '70-832',   # Spearhead: Maggotkin of Nurgle

    # Leagues of Votann
    '73-10',    # Hearthkyn Warriors

    # AoS Chaos
    '83-14',    # Slaves to Darkness Varanguard
    '83-18',    # Slaves to Darkness Chaos Warriors
    '83-20',    # Maggotkin of Nurgle Plaguebearers

    # AoS Order
    '85-06',    # Daughters of Khaine Witch Aelves
    '86-15',    # Cities of Sigmar Freeguild Fusiliers
    '87-08',    # Lumineth Realm-lords Alarith Stoneguard
    '87-10',    # Lumineth Realm-lords Vanari Auralan Wardens

    # AoS Destruction
    '89-10',    # Gloomspite Gitz Squig Herd
    '89-11',    # Gloomspite Gitz Squig Hoppers
    '89-30',    # Orruk Warclans Ardboys

    # AoS Death / Chaos
    '90-12',    # Skaven Plague Monks
    '90-17',    # Skaven Stormfiends
    '91-02',    # Nighthaunt Lady Olynder
    '91-07',    # Flesh-Eater Courts Crypt Horrors
    '91-12',    # Nighthaunt Grimghast Reapers
    '91-14',    # Nighthaunt Bladegheist Revenants

    # Ossiarch Bonereapers
    '94-12',    # Necropolis Stalkers

    # AoS Daemons
    '97-08',    # Blades of Khorne Bloodletters
    '97-11',    # Disciples of Tzeentch Pink Horrors

    # Horus Heresy
    'HA-001',   # MKVI Tactical Squad
    'HA-002',   # Contemptor Dreadnought
    'HA-010',   # MKIII Tactical Squad
    'HA-012',   # Legiones Astartes Predator
    'HA-021',   # Leviathan Dreadnought
    'HA-030',   # Cataphractii Terminators
    'HA-040',   # Spartan Assault Tank
    'HA-041',   # Sicaran Battle Tank
    'HA-051',   # Chaplain in Terminator Armour

    # Horus Heresy Starter
    'HH-001',   # Age of Darkness
]


class Command(BaseCommand):
    """Eleventh wave of March 2026 ThriftHammer DB corrections."""

    help = 'Apply Wave K batch corrections (March 2026) — MM mass OOS update.'

    def add_arguments(self, parser):
        """Add --dry-run flag to preview changes without saving."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print planned changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Execute all Wave K corrections in order."""
        dry = options['dry_run']
        if dry:
            self.stdout.write(self.style.WARNING('DRY RUN — no changes will be saved.\n'))

        self._section_1_mm_oos(dry)
        self._section_2_honour_guard_fix(dry)

        if dry:
            self.stdout.write(self.style.WARNING('\nDRY RUN complete — nothing was saved.'))
        else:
            self.stdout.write(self.style.SUCCESS('\nWave K complete.'))

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _get_product(self, gw_sku):
        """Fetch a product by gw_sku, writing an error and returning None if missing."""
        try:
            return Product.objects.get(gw_sku=gw_sku)
        except Product.DoesNotExist:
            self.stderr.write(self.style.ERROR(f'  ERROR: Product {gw_sku} not found.'))
            return None

    # -----------------------------------------------------------------------
    # Sections
    # -----------------------------------------------------------------------

    def _section_1_mm_oos(self, dry):
        """
        Section 1: Set in_stock=False for all confirmed OOS MM prices.

        Verified by same-origin browser fetch of every active MM URL on
        2026-03-17.  Prices and URLs are kept so the product page still shows
        the MM row with an Out of Stock badge.
        """
        self.stdout.write('\n── Section 1: Miniature Market mass OOS update ──')
        mm = Retailer.objects.get(name='Miniature Market')

        updated = 0
        skipped = 0
        not_found = 0

        for sku in MM_OOS_SKUS:
            p = self._get_product(sku)
            if p is None:
                not_found += 1
                continue
            try:
                cp = CurrentPrice.objects.get(product=p, retailer=mm)
            except CurrentPrice.DoesNotExist:
                self.stdout.write(f'  [skip] {sku} — no MM row')
                skipped += 1
                continue

            if not cp.in_stock:
                # Already correct — skip silently unless dry-run
                if dry:
                    self.stdout.write(f'  [dry-skip] {sku} already OOS')
                skipped += 1
                continue

            if dry:
                self.stdout.write(f'  [dry] {sku} "{p.name[:45]}" → in_stock=False')
                continue

            cp.in_stock = False
            cp.save(update_fields=['in_stock'])
            self.stdout.write(f'  [ok] {sku} → in_stock=False')
            updated += 1

        if not dry:
            self.stdout.write(
                self.style.SUCCESS(
                    f'  Section 1 done: {updated} updated, {skipped} already-correct/skipped.'
                )
            )

    def _section_2_honour_guard_fix(self, dry):
        """
        Section 2: Fix 55-16 Ultramarines Honour Guard MM entry.

        The existing URL (gw-55-21.html) points to the old Marneus Calgar +
        Victrix Honour Guard combined box, not the standalone 2025 kit.
        MM has no listing for the 2025 kit (gw-55-16 returns 404).
        Setting not_available=True removes the misleading link from the
        product page until MM stocks the new kit.
        """
        self.stdout.write('\n── Section 2: 55-16 Honour Guard MM fix ──')
        mm = Retailer.objects.get(name='Miniature Market')

        p = self._get_product('55-16')
        if p is None:
            return

        try:
            cp = CurrentPrice.objects.get(product=p, retailer=mm)
        except CurrentPrice.DoesNotExist:
            self.stdout.write('  [skip] 55-16 / Miniature Market — no row found')
            return

        if dry:
            self.stdout.write(
                f'  [dry] 55-16 / MM → not_available=True, in_stock=False '
                f'(current URL: {cp.url})'
            )
            return

        cp.not_available = True
        cp.in_stock = False
        cp.save(update_fields=['not_available', 'in_stock'])
        self.stdout.write('  [ok] 55-16 / MM → not_available=True, in_stock=False')
