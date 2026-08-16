"""
Management command: assign_warmachine_crucible_guard

First step of reorganizing the flat 348-product Warmachine category into
per-faction structure (mirrors how every other multi-faction category on
the site works, e.g. Space Marine chapters). Creates the "Crucible Guard"
Faction under the existing Warmachine Category, and reassigns the 22
existing WMH-xxx products that belong to it.

All 22 products from the user-supplied "Crucible Guard.xlsx" already exist
in the original 348-product Warmachine batch (WMH-103, WMH-104, WMH-108,
WMH-109, WMH-110, WMH-124 through WMH-137, WMH-336, WMH-337, WMH-346) --
no new products are created here, only faction reassignment.

Also refreshes ebay_search_name to the confirmed values from the sheet's
"ebay & amazon search name" column (adds a colon after "Warmachine" that
the original auto-generated search names didn't have) -- this is the
single source of truth going forward for Amazon matching too, per the
user's process prompt.

Usage:
    python manage.py assign_warmachine_crucible_guard
"""

from django.core.management.base import BaseCommand

from products.models import Category, Faction, Product

# (gw_sku, ebay_search_name)
CRUCIBLE_GUARD_SKUS = [
    ('WMH-103', 'Warmachine: Crucible Guard Captain Eira Mackay & Railless Interceptor'),
    ('WMH-104', 'Warmachine: Crucible Guard Core Expansion'),
    ('WMH-108', 'Warmachine: Crucible Guard Defenses'),
    ('WMH-109', 'Warmachine: Crucible Guard Vulcan'),
    ('WMH-110', 'Warmachine: Crucible Guard Auxiliary Expansion'),
    ('WMH-124', 'Warmachine: Crucible Guard Toro/Suppressor/Vindicator Warjack'),
    ('WMH-125', 'Warmachine: Crucible Guard Liberator/Retaliator/Vanguard Warjack'),
    ('WMH-126', 'Warmachine: Crucible Guard Infantry and Officer & Standard Bearer'),
    ('WMH-127', 'Warmachine: Crucible Guard Rocketman Stinger'),
    ('WMH-128', 'Warmachine: Crucible Guard Mechaniks'),
    ('WMH-129', 'Warmachine: Crucible Guard Rocketmen Gunners'),
    ('WMH-130', 'Warmachine: Crucible Guard Rocketmen & Rocketman Captain'),
    ('WMH-131', 'Warmachine: Crucible Guard Rocketman Ace'),
    ('WMH-132', 'Warmachine: Crucible Guard Combat Alchemists'),
    ('WMH-133', "Warmachine: Crucible Guard Dragon's Breath Rocket"),
    ('WMH-134', 'Warmachine: Crucible Guard Assault Troopers'),
    ('WMH-135', 'Warmachine: Crucible Guard Storm Troopers'),
    ('WMH-136', 'Warmachine: Crucible Guard Containment Operatives'),
    ('WMH-137', 'Warmachine: Crucible Guard Failed Experiments'),
    ('WMH-336', 'Warmachine: Crucible Guard Battlegroup Box'),
    ('WMH-337', 'Warmachine: Crucible Guard Command Starter'),
    ('WMH-346', 'Warmachine: Crucible Guard Athanor Locke'),
]


class Command(BaseCommand):
    """Create the Crucible Guard faction and reassign its products."""

    help = 'Creates Warmachine: Crucible Guard faction and reassigns its 22 products.'

    def handle(self, *args, **options):
        category = Category.objects.get(slug='warmachine')

        faction, created = Faction.objects.get_or_create(
            name='Crucible Guard',
            defaults={'slug': 'warmachine-crucible-guard', 'category': category},
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created faction: Crucible Guard'))
        else:
            self.stdout.write(f'Found faction: Crucible Guard (pk={faction.pk})')

        reassigned = 0
        missing = []
        for gw_sku, ebay_search_name in CRUCIBLE_GUARD_SKUS:
            try:
                product = Product.objects.get(gw_sku=gw_sku)
            except Product.DoesNotExist:
                missing.append(gw_sku)
                continue
            product.faction = faction
            product.ebay_search_name = ebay_search_name
            product.save(update_fields=['faction', 'ebay_search_name'])
            reassigned += 1
            self.stdout.write(f'  reassigned: {product.name} ({gw_sku})')

        if missing:
            self.stdout.write(self.style.WARNING(f'  Not found, skipped: {", ".join(missing)}'))

        self.stdout.write(self.style.SUCCESS(
            f'assign_warmachine_crucible_guard complete. {reassigned} product(s) reassigned.'
        ))
