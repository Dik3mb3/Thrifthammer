from django.core.management.base import BaseCommand
from products.models import Product


class Command(BaseCommand):
    help = (
        'Aug 2026a: eBay negative keyword additions across ~35 named products '
        '(bits/wrong-edition/wrong-variant mismatches) plus a Blood Bowl '
        'category-wide exclusion for merchandise (transfers/decals/sheet) that '
        'was matching against team/star-player kits.'
    )

    def handle(self, *args, **options):
        fixes = [
            ('ebay_negative_keywords', '71-06', 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x issues 90 91 Maulerfiend forgefiend'),
            ('ebay_negative_keywords', '51-16', 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x Citadel'),
            ('ebay_negative_keywords', 'EOM-005', 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x Marauder AA229'),
            ('ebay_negative_keywords', '83-30', 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x standard 8x'),
            ('ebay_negative_keywords', 'SK-001', 'legions imperialis Resin 04-113 100th 1926 TShirt Plushie Plush Proxies 2022 Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x 2019 Horned'),
            ('ebay_negative_keywords', '90-10', '1989 legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x 15x R86'),
            ('ebay_negative_keywords', 'BOK-009', 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x *'),
            ('ebay_negative_keywords', 'SG-031', 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x Sealed'),
            ('ebay_negative_keywords', 'DOT-010', 'legions imperialis Resin 04-113 Proxies sealed Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x HB'),
            ('ebay_negative_keywords', 'SE-024', 'legions imperialis Resin 04-113 100th 1926 TShirt Plushie Plush Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x Errant'),
            ('ebay_negative_keywords', 'SWL-085', 'legions imperialis Resin 04-113 Proxies Foil magazine issue Brand'),
            ('ebay_negative_keywords', 'SWL-084', 'legions imperialis Resin 04-113 Proxies Foil magazine issue 1st'),
            ('ebay_negative_keywords', 'CSM-029', 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x jump pack'),
            ('ebay_negative_keywords', 'LRL-011', 'legions imperialis Resin 04-113 Proxies army-book Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x AS401'),
            ('ebay_negative_keywords', '91-12', 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x Executioner Grimghast stalkers'),
            ('ebay_negative_keywords', 'BB-093', 'Dice Proxies Foil magazine issue Goreball compatible transfers decals decal sheet'),
            ('ebay_negative_keywords', '50-58', 'legions imperialis Resin 04-113 D&D 5e 100th 1926 TShirt Plushie Plush Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x build Freeks'),
            ('ebay_negative_keywords', 'HER-017', 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x x15 AZ165'),
            ('ebay_negative_keywords', '49-23', '3rd 4th 5th 6th 7th 8th 9th legions imperialis Resin 04-113 D&D 5e 100th 1926 TShirt Plushie Plush Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x 2020'),
            ('ebay_negative_keywords', 'AM-015', 'legions imperialis 3rd 4th 5th 6th 7th 8th 9th Resin 04-113 100th 1926 TShirt Plushie Plush Proxies 2014 History Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x 2022'),
            ('ebay_negative_keywords', 'CK-001', 'Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x Sealed'),
            ('ebay_negative_keywords', 'BOK-012', 'legions imperialis Resin 04-113 Proxies Khorgorath Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x Korghos Mighty'),
            ('ebay_negative_keywords', 'CSM-030', 'legions imperialis 3rd 4th 5th 6th 7th 8th 9th Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x brand'),
            ('ebay_negative_keywords', 'FEC-021', 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x 11650'),
            ('ebay_negative_keywords', 'AL-034', 'Imperialis legions imperialis Resin 04-113 Proxies Foil magazine issue ranged'),
            ('ebay_negative_keywords', 'TY-013', 'legions imperialis Resin 04-113 100th 1926 TShirt Plushie Plush Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x x6 WH40K'),
            ('ebay_negative_keywords', '70-22', 'legions imperialis Resin 04-113 Proxies Foil magazine issue Grenadiers 5x x5 x10 10x x2 2x 3x x3 x4 4x Ash'),
            ('ebay_negative_keywords', 'FOE-016', 'Imperialis legions imperialis Resin 04-113 Proxies Foil magazine issue x5 Volkite'),
            ('ebay_negative_keywords', '43-55', 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x spewers'),
            ('ebay_negative_keywords', 'NM-028', 'Foil magazine issue cultist Secundus genestealer'),
            ('ebay_negative_keywords', 'OBR-004', 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x built'),
            # Blocked eBay item IDs (wrong-edition battletomes / 3D-print
            # listings whose titles gave no distinguishing keyword to exclude
            # on -- see apply_batch_fixes_jul2026i for the original pattern).
            # Requires the item-ID legacy-ID-extraction fix in
            # ebay_api_client.py / ebay_api_client_uk.py landed alongside this
            # command; the raw "v1|<id>|0" comparison never matched before that.
            ('ebay_negative_keywords', 'COS-008', 'legions imperialis Resin 04-113 Proxies sealed Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x 336621480482'),
            ('ebay_negative_keywords', 'IDK-019', 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x 296420920051'),
            ('ebay_negative_keywords', 'MON-019', 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x 135320214150'),
            ('ebay_negative_keywords', 'GG-029', 'legions imperialis Resin 04-113 Proxies sealed Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x 365692887514'),
            ('ebay_negative_keywords', '50-36', 'legions imperialis Resin 04-113 D&D 5e 100th 1926 TShirt Plushie Plush Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x 358675554120'),
            # BB-028 gets its item-ID block AND the Blood Bowl bulk suffix
            # combined here (not in bloodbowl_current below) to avoid the
            # bulk loop overwriting this value and dropping the item-ID block.
            ('ebay_negative_keywords', 'BB-028', 'Dice Proxies Foil magazine issue 358674546636 transfers decals decal sheet'),
        ]

        for field, sku, value in fixes:
            updated = Product.objects.filter(gw_sku=sku).update(**{field: value})
            self.stdout.write(f'{sku} {field}=[{value}] rows={updated}')

        # Blood Bowl category-wide addition: "transfers decals decal sheet"
        # excludes water-slide transfer sheets / decal packs sold separately
        # from the actual team/star-player miniature kits. Frozen snapshot of
        # each SKU's current value below (captured 2026-08-02) so this stays
        # deterministic on re-run, rather than reading live DB state.
        # BB-093 (Goblin Blood Bowl Team) is handled above -- it also needed
        # its own product-specific keywords, so its complete final value
        # (base + specific + these four) is set directly in `fixes`.
        bloodbowl_current = {
            'BB-003': 'Dice Proxies Foil magazine issue',
            'BB-080': 'Dice Proxies Foil magazine issue',
            'BB-052': 'Dice Proxies Foil magazine issue',
            'BB-087': 'Dice Proxies Foil magazine issue',
            'BB-092': 'Dice Proxies Foil magazine issue',
            'BB-037': 'Dice Proxies Foil magazine issue',
            'BB-036': 'Dice Proxies Foil magazine issue',
            'BB-032': 'Dice Proxies Foil magazine issue',
            'BB-039': 'Dice Proxies Foil magazine issue',
            'BB-031': 'Dice Proxies Foil magazine issue',
            'BB-035': 'Dice Proxies Foil magazine issue',
            'BB-063': 'Dice Proxies Foil magazine issue',
            'BB-033': 'Dice Proxies Foil magazine issue',
            'BB-030': 'Dice Proxies Foil magazine issue',
            'BB-002': 'Dice Proxies Foil magazine issue',
            'BB-001': 'Dice Proxies Foil magazine issue',
            'BB-034': 'Dice Proxies Foil magazine issue',
            'BB-038': 'Dice Proxies Foil magazine issue',
            'BB-040': 'Dice Proxies Foil magazine issue',
            'BB-029': 'Dice Proxies Foil magazine issue',
            'BB-046': 'Dice Proxies Foil magazine issue',
            'BB-025': 'Dice Proxies Foil magazine issue',
            'BB-090': 'Dice Proxies Foil magazine issue',
            'BB-017': 'Dice Proxies Foil magazine issue',
            'BB-026': 'Dice Proxies Foil magazine issue',
            'BB-044': 'Dice Proxies Foil magazine issue',
            'BB-088': 'Dice Proxies Foil magazine issue',
            'BB-014': 'Dice Proxies Foil magazine issue',
            'BB-061': 'Dice Proxies Foil magazine issue',
            'BB-043': 'Dice Proxies Foil magazine issue',
            'BB-022': 'Dice Proxies Foil magazine issue',
            'BB-068': 'Dice Proxies Foil magazine issue',
            'BB-056': 'Dice Proxies Foil magazine issue',
            'BB-021': 'Dice Proxies Foil magazine issue',
            'BB-047': 'Dice Proxies Foil magazine issue',
            'BB-051': 'Dice Proxies Foil magazine issue',
            'BB-070': 'Dice Proxies Foil magazine issue',
            'BB-100': 'Dice Proxies Foil magazine issue',
            'BB-045': 'Dice Proxies Foil magazine issue',
            'BB-009': 'Dice Proxies Foil Treeman magazine issue',
            'BB-089': 'Dice Proxies Foil magazine issue',
            'BB-058': 'Dice Proxies Foil magazine issue',
            'BB-099': 'Dice Proxies Foil magazine issue',
            'BB-072': 'Dice Proxies Foil magazine issue',
            'BB-071': 'Dice Proxies Foil magazine issue',
            'BB-079': 'Dice Proxies Foil magazine issue',
            'BB-073': 'Dice Proxies Foil magazine issue',
            'BB-020': 'Dice Proxies Foil magazine issue',
            'BB-064': 'Dice Proxies Foil magazine issue',
            'BB-023': 'Dice Proxies Foil magazine issue',
            'BB-083': 'Dice Proxies Foil magazine issue',
            'BB-012': 'Dice Dugouts Pitch Proxies Foil magazine issue',
            'BB-011': 'Dice Proxies Foil magazine issue',
            'BB-041': 'Dice Proxies Foil magazine issue',
            'BB-050': 'Dice Proxies Foil magazine issue',
            'BB-077': 'Dice Proxies Foil magazine issue',
            'BB-084': 'Dice Proxies Foil magazine issue',
            'BB-069': 'Dice Proxies Foil magazine issue',
            'BB-065': 'Dice Proxies Foil magazine issue',
            'BB-005': 'Dice Proxies Foil magazine issue',
            'BB-054': 'Dice Proxies Foil magazine issue',
            'BB-006': 'Dice Proxies Foil magazine issue',
            'BB-062': 'Dice Proxies Foil magazine issue',
            'BB-076': 'Dice Proxies Foil magazine issue',
            'BB-098': 'Dice Proxies Foil magazine issue',
            'BB-074': 'Dice Proxies Foil magazine issue',
            'BB-007': 'Dice Proxies Foil magazine issue',
            'BB-097': 'Dice Proxies Foil magazine issue',
            'BB-004': 'Dice Proxies Foil magazine issue',
            'BB-008': 'Dice Proxies Foil magazine issue',
            'BB-013': 'Dice Proxies Foil magazine issue',
            'BB-010': 'Dice Proxies Foil magazine issue',
            'BB-094': 'Dice Dugouts Pitch Proxies Foil magazine issue',
            'BB-081': 'Dice Proxies Foil magazine issue',
            'BB-042': 'Dice Proxies Foil magazine issue',
            'BB-085': 'Dice Proxies Foil magazine issue',
            'BB-078': 'Dice Proxies Foil magazine issue',
            'BB-067': 'Dice Proxies Foil magazine issue',
            'BB-048': 'Dice Proxies Foil magazine issue',
            'BB-053': 'Dice Proxies Foil magazine issue',
            'BB-015': 'Dice Proxies Foil magazine issue',
            'BB-016': 'Dice Proxies Foil magazine issue',
            'BB-086': 'Dice Proxies Foil magazine issue',
            'BB-059': 'Dice Proxies Foil magazine issue',
            'BB-018': 'Dice Proxies Foil magazine issue',
            'BB-075': 'Dice Proxies Foil magazine issue',
            'BB-066': 'Dice Proxies Foil magazine issue',
            'BB-049': 'Dice Proxies Foil magazine issue',
            'BB-024': 'Dice Proxies Foil magazine issue',
            'BB-091': 'Dice Proxies Foil magazine issue',
            'BB-027': 'Dice Proxies Foil magazine issue',
            'BB-057': 'Dice Proxies Foil magazine issue',
            'BB-055': 'Dice Proxies Foil magazine issue',
            'BB-060': 'Dice Proxies Foil magazine issue',
            'BB-096': 'Dice Proxies Foil magazine issue',
            'BB-019': 'Dice Proxies Foil magazine issue',
            'BB-095': 'Dice Proxies Foil magazine issue',
            'BB-082': 'Dice Proxies Foil magazine issue',
        }
        bb_suffix = ' transfers decals decal sheet'
        bb_updated = 0
        for sku, current in bloodbowl_current.items():
            bb_updated += Product.objects.filter(gw_sku=sku).update(
                ebay_negative_keywords=current + bb_suffix
            )
        self.stdout.write(f'Blood Bowl category rows={bb_updated}')

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_aug2026a done'))
