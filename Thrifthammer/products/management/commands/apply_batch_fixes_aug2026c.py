from django.core.management.base import BaseCommand
from products.models import Product


class Command(BaseCommand):
    help = (
        'Aug 2026c: eBay negative keyword additions -- "Sealed" added to all '
        'The Old World SKUs, "Dice" added to all Kill Team SKUs, and '
        '"Gregor"/"1988" added to BB-012 (Human Blood Bowl Team). Also fixes '
        'BB-012 image_url, which pointed at a Drakfang Thirsters product photo '
        'instead of the correct Reikland Reavers (Human team) photo.'
    )

    def handle(self, *args, **options):
        fixes = [
            ('ebay_negative_keywords', 'BB-012', 'Dice Dugouts Pitch Proxies Foil magazine issue transfers decals decal sheet Gregor 1988'),
            ('image_url', 'BB-012', 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120902001_ReiklandReaversTeam01.jpg'),
        ]

        for field, sku, value in fixes:
            updated = Product.objects.filter(gw_sku=sku).update(**{field: value})
            self.stdout.write(f'{sku} {field}=[{value}] rows={updated}')

        # The Old World and Kill Team category-wide additions below touch 125
        # and 34 SKUs respectively, so hardcoding a per-SKU literal snapshot
        # the way the fix above does isn't practical. Frozen snapshot of each
        # SKU's current value (captured 2026-08-05) so this stays
        # deterministic on re-run, rather than reading live DB state --
        # matches the pattern already used in apply_batch_fixes_aug2026a/b.
        old_world_current = {
            'WER-004': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'GCA-012': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'GCA-011': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'EOM-001': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'HER-002': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'KOB-008': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'GCA-015': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'WOC-008': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'TKK-012': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'TKK-013': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'WOC-002': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'WER-002': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'GCA-003': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'KOB-006': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'BBH-002': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'BBH-008': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'BBH-007': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'OGT-005': 'legions imperialis Resin 04-113 Proxies Foil Banner Icon Drum Choppa Smasha magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'EOM-009': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'EOM-017': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'GCA-008': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'WOC-004': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'WOC-010': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'WOC-001': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'WOC-003': 'legions imperialis Resin 04-113 Proxies Foil Cloaks magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'WOC-005': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'WOC-006': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'EOM-015': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'BBH-004': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'EOM-010': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'WOC-009': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'HER-008': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'DMH-004': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'DMH-001': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'DMH-005': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'DMH-008': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'DMH-009': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'DMH-002': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'DMH-007': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'DMH-006': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'DMH-010': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'DMH-012': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'DMH-003': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'DMH-011': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'HER-015': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'HER-013': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'HER-024': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'HER-003': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'EOM-016': 'legions imperialis Resin 04-113 Proxies Foil Bretonnia magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'EOM-008': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'EOM-004': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'EOM-012': 'legions imperialis Resin 04-113 Proxies Panther Grand Master Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'EOM-011': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'EOM-007': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'EOM-002': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'WER-007': 'legions imperialis Resin 04-113 Proxies Foil Shields magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'EOM-005': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x Marauder AA229',
            'HER-006': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'EOM-013': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'GCA-009': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'EOM-014': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'WER-008': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'WER-006': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'OGT-003': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'OGT-001': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'OGT-002': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'BBH-006': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'GCA-004': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'HER-020': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'HER-021': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'EOM-003': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'HER-012': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'HER-005': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'HER-011': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'HER-023': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'GCA-001': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'GCA-005': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'GCA-014': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'TKK-008': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'KOB-003': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'KOB-007': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'HER-022': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'TKK-003': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'HER-016': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'KOB-004': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'HER-025': 'legions imperialis Resin 04-113 Proxies Foil "sea guard champion" magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'HER-007': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'KOB-002': 'legions imperialis Resin 04-113 Proxies Foil "rank x5" magazine issue 5x x10 10x x2 2x 3x x3 x4 4x',
            'GCA-006': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'BBH-005': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'TKK-007': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'TKK-009': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'OGT-010': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'OGT-006': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'OGT-004': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'OGT-009': 'legions imperialis Resin 04-113 Proxies Foil Goblin magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'OGT-008': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'OGT-007': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'KOB-001': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'GCA-002': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'KOB-005': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'HER-009': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'TKK-004': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'TKK-010': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'GCA-010': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'HER-004': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'HER-010': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'TKK-001': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'GCA-007': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'WOC-007': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'EOM-006': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'HER-017': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x x15 AZ165',
            'GCA-013': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'HER-001': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'TKK-011': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'TKK-006': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'TKK-005': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'TKK-002': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'BBH-001': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'BBH-003': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'EOM-018': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'HER-014': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'WER-005': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'WER-003': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
            'WER-001': 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x',
        }
        ow_suffix = ' Sealed'
        ow_updated = 0
        for sku, current in old_world_current.items():
            ow_updated += Product.objects.filter(gw_sku=sku).update(
                ebay_negative_keywords=current + ow_suffix
            )
        self.stdout.write(f'The Old World category rows={ow_updated}')

        kill_team_current = {
            'KT-004': 'legions imperialis Resin 04-113 100th 1926 TShirt Plushie Plush Proxies Foil magazine issue',
            'KT-032': 'x5 5x Foil magazine issue',
            'KT-016': 'legions imperialis Resin 04-113 100th 1926 TShirt Plushie Plush Proxies Foil magazine issue',
            'KT-029': 'Geomancer model Foil magazine issue',
            'KT-015': 'legions imperialis Resin 04-113 100th 1926 TShirt Plushie Plush Proxies Foil magazine issue',
            'KT-009': 'legions imperialis Resin 04-113 100th 1926 TShirt Plushie Plush Proxies Foil magazine issue',
            'KT-023': 'legions imperialis Resin 04-113 100th 1926 TShirt Plushie Plush Proxies Foil magazine issue',
            'KT-008': 'legions imperialis Resin 04-113 100th 1926 TShirt Plushie Plush Proxies Foil magazine issue',
            'KT-006': 'legions imperialis Resin 04-113 100th 1926 TShirt Plushie Plush Proxies Foil magazine issue',
            'KT-021': 'legions imperialis Resin 04-113 100th 1926 TShirt Plushie Plush Proxies Foil magazine issue',
            'KT-020': 'legions imperialis Resin 04-113 100th 1926 TShirt Plushie Plush Proxies Foil magazine issue',
            'KT-025': 'legions imperialis Resin 04-113 100th 1926 TShirt Plushie Plush Proxies Foil magazine issue',
            'KT-022': 'legions imperialis Resin 04-113 100th 1926 TShirt Plushie Plush Proxies Foil magazine issue',
            'KT-010': 'legions imperialis Resin 04-113 100th 1926 TShirt Plushie Plush Proxies Foil magazine issue',
            'KT-033': 'legions imperialis Resin 04-113 100th 1926 TShirt Plushie Plush Proxies Foil magazine issue',
            'KT-105': 'legions imperialis Resin 04-113 Proxies Foil magazine issue',
            'KT-012': 'legions imperialis Resin 04-113 100th 1926 TShirt Plushie Plush Proxies Foil magazine issue',
            'KT-027': 'legions imperialis Resin 04-113 100th 1926 TShirt Plushie Plush Proxies Foil magazine issue',
            'KT-017': 'legions imperialis Resin 04-113 100th 1926 TShirt Plushie Plush Proxies Foil magazine issue',
            'KT-019': 'legions imperialis Resin 04-113 100th 1926 TShirt Plushie Plush Proxies Foil magazine issue',
            'KT-030': 'legions imperialis Resin 04-113 100th 1926 TShirt Plushie Plush Proxies Foil magazine issue',
            'KT-005': 'legions imperialis Resin 04-113 100th 1926 TShirt Plushie Plush Proxies Foil magazine issue',
            'KT-018': 'legions imperialis Resin 04-113 100th 1926 TShirt Plushie Plush Proxies Foil magazine issue',
            'KT-028': 'legions imperialis Resin 04-113 100th 1926 TShirt Plushie Plush Proxies Foil magazine issue',
            'KT-011': 'legions imperialis Resin 04-113 100th 1926 TShirt Plushie Plush Proxies Foil magazine issue',
            'KT-024': 'legions imperialis Resin 04-113 100th 1926 TShirt Plushie Plush Proxies Foil magazine issue',
            'KT-103': 'legions imperialis Resin 04-113 Proxies Foil magazine issue',
            'KT-102': 'legions imperialis Resin 04-113 Proxies Foil magazine issue',
            'KT-026': 'legions imperialis Resin 04-113 100th 1926 TShirt Plushie Plush Proxies Foil magazine issue',
            'KT-007': 'legions imperialis Resin 04-113 100th 1926 TShirt Plushie Plush Proxies Foil magazine issue',
            'KT-013': 'legions imperialis Resin 04-113 100th 1926 TShirt Plushie Plush Proxies Foil magazine issue',
            'KT-014': 'legions imperialis Resin 04-113 100th 1926 TShirt Plushie Plush Proxies Foil magazine issue',
            'KT-002': 'legions imperialis Resin 04-113 Proxies Dynamo Generator Console Terrain Foil magazine issue',
            'KT-031': 'legions imperialis Resin 04-113 100th 1926 TShirt Plushie Plush Proxies Foil magazine issue',
        }
        kt_suffix = ' Dice'
        kt_updated = 0
        for sku, current in kill_team_current.items():
            kt_updated += Product.objects.filter(gw_sku=sku).update(
                ebay_negative_keywords=current + kt_suffix
            )
        self.stdout.write(f'Kill Team category rows={kt_updated}')

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_aug2026c done'))
