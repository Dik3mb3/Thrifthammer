from django.core.management.base import BaseCommand
from products.models import Product


class Command(BaseCommand):
    help = (
        'Aug 2026b: codifies two eBay negative-keyword batches that were '
        'applied directly to production via one-off scripts and never had a '
        'management-command representation -- 21 product-specific fixes plus '
        'two catalog-wide keyword additions ("magazine"/"issue" on every '
        'active product; "x5/5x/x10/10x/x2/2x/x3/3x/x4/4x" on Age of Sigmar, '
        'Warhammer 40,000, and The Old World). Without this file, a DB '
        'restore from an older backup would silently lose this data.'
    )

    def handle(self, *args, **options):
        fixes = [
            ('ebay_negative_keywords', 'CD-019', 'legions imperialis Resin 04-113 Proxies Foil Dwarves Crew Loader magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x'),
            ('ebay_negative_keywords', '50-38', 'legions imperialis Resin 04-113 D&D 5e 100th 1926 TShirt Plushie Plush Proxies Foil Warlord Warlords magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x'),
            ('ebay_negative_keywords', '51-42', 'legions imperialis Resin 04-113 Proxies Foil Magus magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x'),
            ('ebay_negative_keywords', 'TY-040', 'legions imperialis Resin 04-113 100th 1926 TShirt Plushie Plush Proxies Foil BNIB magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x'),
            ('ebay_negative_keywords', 'prod3550127-99129915060', 'legions imperialis Resin 04-113 D&D 5e 100th 1926 TShirt Plushie Plush Proxies Foil Plaguebearer magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x'),
            ('ebay_negative_keywords', '52-02', 'legions imperialis Resin 04-113 Proxies Foil Abbess Sanctorum magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x'),
            ('ebay_negative_keywords', '50-43', 'legions imperialis Resin 04-113 D&D 5e 100th 1926 TShirt Plushie Plush Proxies 1986 Chuck Ninja Foil Dice magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x'),
            ('ebay_negative_keywords', '46-09', 'legions imperialis Resin 04-113 Proxies Foil Classic magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x'),
            ('ebay_negative_keywords', 'LRL-025', 'legions imperialis Resin 04-113 Proxies Foil Painted magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x'),
            ('ebay_negative_keywords', 'OM-022', 'legions imperialis Resin 04-113 Proxies Foil Kingdoms magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x'),
            ('ebay_negative_keywords', '53-26', 'legions imperialis Resin 04-113 D&D 5e 100th 1926 TShirt Plushie Plush Proxies Foil magazine issue Metallica x5 5x x10 10x x2 2x 3x x3 x4 4x'),
            ('ebay_negative_keywords', '50-12', 'legions imperialis Resin 04-113 Proxies Foil magazine issue Teleporta Kustom Blasta x5 5x x10 10x x2 2x 3x x3 x4 4x'),
            ('ebay_negative_keywords', 'AL-008', 'Imperialis legions imperialis Resin 04-113 Proxies Foil magazine issue 10'),
            ('ebay_negative_keywords', '89-10', 'legions imperialis Resin 04-113 Proxies Foil magazine issue bagpipe cymbals grot x5 5x x10 10x x2 2x 3x x3 x4 4x'),
            ('ebay_negative_keywords', '99129915052', 'legions imperialis Resin 04-113 D&D 5e 100th 1926 TShirt Plushie Plush Proxies Foil magazine issue hell x5 5x x10 10x x2 2x 3x x3 x4 4x'),
            ('ebay_negative_keywords', '50-42', 'legions imperialis Resin 04-113 D&D 5e 100th 1926 TShirt Plushie Plush Proxies Foil magazine issue salvation apparatus Mechasite x5 5x x10 10x x2 2x 3x x3 x4 4x'),
            ('ebay_negative_keywords', '41-04', 'legions imperialis Resin 04-113 Proxies Foil magazine issue "jump pack" x5 5x x10 10x x2 2x 3x x3 x4 4x'),
            ('ebay_negative_keywords', '48-07', 'power fist legions imperialis Resin 04-113 Proxies Foil Horus magazine issue x10 x5 5x 10x x2 2x 3x x3 x4 4x'),
            ('ebay_negative_keywords', '91-28', 'artel legions imperialis Resin 04-113 D&D 5e 100th 1926 TShirt Plushie Plush Proxies Foil magazine issue undead x5 5x x10 10x x2 2x 3x x3 x4 4x'),
            ('ebay_negative_keywords', '48-06', 'assault legions imperialis Resin 04-113 Proxies Foil Chaos magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x'),
            ('ebay_negative_keywords', '43-48', 'legions imperialis Resin 04-113 D&D 5e 100th 1926 TShirt Plushie Plush Proxies Foil magazine issue Repugnus x5 5x x10 10x x2 2x 3x x3 x4 4x'),
        ]

        for field, sku, value in fixes:
            updated = Product.objects.filter(gw_sku=sku).update(**{field: value})
            self.stdout.write(f'{sku} {field}=[{value}] rows={updated}')

        # ── Catalog-wide keyword additions ──────────────────────────────────
        # These two touch thousands of products (magazine/issue: ~2510;
        # x5/5x/etc: ~1569), so hardcoding a per-SKU literal snapshot the way
        # the fixes above do isn't practical. Instead this uses the same
        # check-before-append pattern as the existing
        # migrations/0029_add_general_ebay_negative_keywords.py -- read each
        # product's current value, only append words that aren't already
        # present, save. This is idempotent and safe to re-run (as it will be
        # on every future deploy via the Procfile): already-tagged products
        # are left untouched, nothing is ever overwritten or removed.
        magazine_words = ['magazine', 'issue']
        all_products = Product.objects.filter(is_active=True).only('id', 'ebay_negative_keywords')
        to_update = []
        for p in all_products:
            existing = p.ebay_negative_keywords or ''
            existing_lower = existing.lower()
            to_add = [w for w in magazine_words if w not in existing_lower]
            if to_add:
                sep = ' ' if existing else ''
                p.ebay_negative_keywords = existing + sep + ' '.join(to_add)
                to_update.append(p)
        Product.objects.bulk_update(to_update, ['ebay_negative_keywords'], batch_size=500)
        self.stdout.write(f'Catalog-wide magazine/issue rows updated={len(to_update)}')

        qty_words = ['x5', '5x', 'x10', '10x', 'x2', '2x', '3x', 'x3', 'x4', '4x']
        category_slugs = ['age-of-sigmar', 'warhammer-40000', 'the-old-world']
        cat_products = (
            Product.objects.filter(is_active=True, category__slug__in=category_slugs)
            .only('id', 'ebay_negative_keywords')
        )
        to_update = []
        for p in cat_products:
            existing = p.ebay_negative_keywords or ''
            existing_lower = existing.lower()
            to_add = [w for w in qty_words if w not in existing_lower]
            if to_add:
                sep = ' ' if existing else ''
                p.ebay_negative_keywords = existing + sep + ' '.join(to_add)
                to_update.append(p)
        Product.objects.bulk_update(to_update, ['ebay_negative_keywords'], batch_size=500)
        self.stdout.write(f'AoS/40K/Old World quantity-keyword rows updated={len(to_update)}')

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_aug2026b done'))
