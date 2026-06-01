"""
Management command: add_chaos_daemons_secondary_faction

Tags 23 existing products with the Chaos Daemons secondary faction so they
appear on the Chaos Daemons faction page without creating duplicate records.

The products' primary faction FK is NOT changed — they remain in their
current faction (Emperor's Children, Death Guard, Thousand Sons, World Eaters,
Chaos Space Marines). The M2M secondary_factions field added in migration 0061
powers the dual-display.

This command MUST run after populate_chaos_daemons_products (which creates the
Chaos Daemons faction). In the Procfile it is placed immediately after that
command.

Idempotent — safe to re-run. ManyToManyField.add() is a no-op if the
relation already exists.
"""

from django.core.management.base import BaseCommand

from products.models import Faction, Product

# (gw_sku, display name for logging)
# Note: gw_sku '99129915056' covers two separate products —
# Keeper of Secrets AND Shalaxi Helbane (same physical kit, both in DB).
# filter(gw_sku__in=...) returns both rows; both get tagged.
_DUAL_TAG_SKUS = [
    ('99129915036',              'Daemonettes of Slaanesh'),
    ('99120201130',              'Daemon Prince'),
    ('prod3550127-99129915060',  'Nurglings'),
    ('99129915056',              'Keeper of Secrets / Shalaxi Helbane'),
    ('99129915052',              'Fiends'),
    ('P-KHORNE-FLESHHOUNDS',     'Flesh Hounds of Khorne'),
    ('P-PINK-HORRORS-40K',       'Pink Horrors of Tzeentch'),
    ('prod3700271-99129915063',  'Rotigus'),
    ('prod3700247-99129915063',  'Great Unclean One'),
    ('prod3700246-99129915062',  'Beast of Nurgle'),
    ('prod3610130-99129915038',  'Plague Drones of Nurgle'),
    ('P-NURGLE-PLAGUEBEARERS-40K', 'Plaguebearers of Nurgle'),
    ('P-TZEENTCH-SCREAMERS',     'Screamers of Tzeentch'),
    ('P-TZEENTCH-FLAMERS',       'Flamers of Tzeentch'),
    ('P-TZEENTCH-BLUEHORRORS',   'Blue Horrors and Brimstone Horrors'),
    ('P-KHORNE-BLOODTHIRSTER',   'Bloodthirster'),
    ('P-KHORNE-BLOODCRUSHERS',   'Bloodcrushers of Khorne'),
    ('P-KHORNE-SKARBRAND',       'Skarbrand the Bloodthirster'),
    ('99129915005',              'Seekers of Slaanesh'),
    ('P-KHORNE-BLOODLETTERS-40K', 'Bloodletters of Khorne'),
    ('P-TZEENTCH-KAIROS',        'Kairos Fateweaver'),
    ('P-TZEENTCH-LOC',           'Lord of Change'),
]


class Command(BaseCommand):
    """Tag existing products with the Chaos Daemons secondary faction."""

    help = 'Add Chaos Daemons secondary faction tag to cross-faction daemon products.'

    def handle(self, *args, **options):
        """Run the command."""
        try:
            cd_faction = Faction.objects.get(slug='chaos-daemons')
        except Faction.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                'Chaos Daemons faction not found in DB. '
                'Run populate_chaos_daemons_products first.'
            ))
            return

        sku_list = [sku for sku, _ in _DUAL_TAG_SKUS]
        products = list(
            Product.objects.filter(gw_sku__in=sku_list).order_by('gw_sku', 'name')
        )

        if not products:
            self.stdout.write(self.style.WARNING('No matching products found.'))
            return

        tagged = 0
        for product in products:
            product.secondary_factions.add(cd_faction)
            self.stdout.write(f'  tagged: {product.name} ({product.gw_sku})')
            tagged += 1

        self.stdout.write(self.style.SUCCESS(
            f'add_chaos_daemons_secondary_faction complete. Tagged {tagged} product(s).'
        ))
