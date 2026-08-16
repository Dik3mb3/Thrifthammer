"""
Management command: add_warcry_secondary_faction

Tags 17 existing products with the Warcry secondary faction so they
appear on the Warcry category/faction page without creating duplicate
records. These are Warcry warbands that are the same physical kit as an
existing Age of Sigmar faction product (e.g. Mindstealer Sphiranx
already exists as S2D-020 under Slaves to Darkness).

S2D-034 "Chaos Legionnaires" is deliberately NOT in this list, even
though it shares a name with WC-006 "Warcry: Chaos Legionnaires" -- they
were initially thought to be the same kit double-counted, but turned out
to be two genuinely separate GW SKUs (different GW URLs, $60 vs $65,
same catalogue-number image prefix but distinct product pages). User
confirmed 2026-08-09 to keep both as fully separate products -- WC-006
already covers this unit under Warcry on its own, so S2D-034 stays
Slaves-to-Darkness-only with no secondary tag.

The products' primary faction FK and category are NOT changed — they
remain under their original faction. The M2M secondary_factions field
powers the dual-display. Name/slug/gw_sku/price/image are untouched.

This command MUST run after populate_warcry_products (which creates the
Warcry faction). In the Procfile it is placed immediately after
populate_warcry_products.

Idempotent — safe to re-run. ManyToManyField.add() is a no-op if the
relation already exists.
"""

from django.core.management.base import BaseCommand

from products.models import Faction, Product

# (gw_sku, display name for logging)
_DUAL_TAG_SKUS = [
    ('S2D-020', 'Mindstealer Sphiranx'),
    ('S2D-021', 'Fomoroid Crusher'),
    ('S2D-022', 'Chaotic Beasts'),
    ('COS-015', 'Wildercorps Hunters'),
    ('FEC-018', 'Royal Beastflayers'),
    ('MON-017', 'Rotmire Creed'),
    ('S2D-013', 'Centaurion Marshal'),
    ('SG-020', 'Askurgan Trueblades'),
    ('FYR-012', 'Vulkyn Flameseekers'),
    ('OW-018', 'Monsta Killaz'),
    ('99120201050', 'Chaos Spawn'),
    ('DOK-012', 'Khainite Shadowstalkers'),
    ('OM-018', 'Gorger Mawpack'),
    ('OBR-017', 'Warcry: Teratic Cohort'),
    ('OM-019', 'Mawpit'),
    ('SYL-004', 'Twistweald'),
    ('S2D-007', 'Ogroid Myrmidon'),
]


class Command(BaseCommand):
    """Tag existing products with the Warcry secondary faction."""

    help = 'Add Warcry secondary faction tag to cross-system products.'

    def handle(self, *args, **options):
        """Run the command."""
        try:
            warcry_faction = Faction.objects.get(slug='warcry')
        except Faction.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                'Warcry faction not found in DB. Run populate_warcry_products first.'
            ))
            return

        sku_list = [sku for sku, _ in _DUAL_TAG_SKUS]
        products = list(
            Product.objects.filter(gw_sku__in=sku_list).order_by('gw_sku', 'name')
        )

        found_skus = {p.gw_sku for p in products}
        missing = [sku for sku in sku_list if sku not in found_skus]
        if missing:
            self.stdout.write(self.style.WARNING(
                f'  Not found in DB, skipped: {", ".join(missing)}'
            ))

        if not products:
            self.stdout.write(self.style.WARNING('No matching products found.'))
            return

        tagged = 0
        for product in products:
            product.secondary_factions.add(warcry_faction)
            self.stdout.write(f'  tagged: {product.name} ({product.gw_sku})')
            tagged += 1

        self.stdout.write(self.style.SUCCESS(
            f'add_warcry_secondary_faction complete. Tagged {tagged} product(s).'
        ))
