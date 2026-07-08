from django.core.management.base import BaseCommand

from products.models import Product


class Command(BaseCommand):
    help = 'Jun 2026r: eBay search name + allow-no-box + allowed-title-words fixes for Armageddon splits'

    def handle(self, *args, **options):
        # ── Armageddon splits eBay search name overrides ──────────────────────
        # populate_armageddon_splits_products resets these to the original values
        # on every deploy, so this command runs after it to lock in the correct
        # search names that actually surface listings on eBay.
        search_fixes = [
            # AGA-006 Vanguard Veterans with Jump Packs
            # prior (set by populate): 'Armageddon Vanguard Veterans with Jump Packs Warhammer 40K'
            # reason: original query returns 0 eBay results; shorter name surfaces listings
            ('AGA-006', 'Armageddon Vanguard Veterans'),

            # AGA-007 Eradicators with Heavy Bolters
            # prior (set by populate): 'Armageddon Eradicators with Heavy Bolters Warhammer 40K'
            # reason: original query returns 0 eBay results; shorter name surfaces listings
            ('AGA-007', 'Armageddon Eradicators 40k'),

            # AGA-020 Chapter Approved 2026-2027: Mission Deck
            # prior (set by populate): 'Armageddon Chapter Approved 2026-2027: Mission Deck Warhammer 40K'
            # reason: original query returns 0 eBay results; leading product name surfaces listings
            ('AGA-020', 'Chapter Approved Mission Deck 11th Edition Armageddon Warhammer 40K'),

            # AGA-022 Armageddon Box Ork Half
            # prior (set by populate): 'Armageddon Box Ork Half Warhammer 40K'
            # reason: original query misses the preferred listing; seller phrasing matches new name
            ('AGA-022', '40k Armageddon Orks half'),
        ]
        for sku, value in search_fixes:
            updated = Product.objects.filter(gw_sku=sku).update(ebay_search_name=value)
            self.stdout.write(f'{sku} ebay_search_name=[{value}] rows={updated}')

        # ── AGA all: ebay_allow_no_box + base ebay_allowed_title_words ──────────
        # populate_armageddon_splits_products does not set either field; both
        # default to False/'' on Railway after each deploy.
        #
        # ebay_allow_no_box=True:  box-split listings are sold without the original
        #   GW retail box, so "no box" in the title is expected and valid.
        #
        # ebay_allowed_title_words='nos sprue':
        #   nos   → bypasses the _DESC_BITS_KEYWORDS 'nos' check in descriptions
        #            (NOS = new-on-sprue; common phrasing for sealed split sprues)
        #   sprue → bypasses the _BITS_KEYWORDS 'sprue' check in titles/descriptions
        #
        # IMPORTANT: this bulk update MUST run before any per-SKU overrides below,
        # because the per-SKU updates would otherwise be overwritten.
        updated = Product.objects.filter(batch_tag='armageddon-splits').update(
            ebay_allow_no_box=True,
            ebay_allowed_title_words='nos sprue',
        )
        self.stdout.write(
            f'AGA all: ebay_allow_no_box=True, ebay_allowed_title_words=[nos sprue]  rows={updated}'
        )

        # ── AGA-010 Bannernob: also allow 'bits' ─────────────────────────────
        # Bannernob is an uncommon term; valid listings often include 'bits' or
        # 'Ork bits' in the title because sellers lump it with sprue listings.
        updated = Product.objects.filter(gw_sku='AGA-010').update(
            ebay_allowed_title_words='nos sprue bits'
        )
        self.stdout.write(f'AGA-010 ebay_allowed_title_words=[nos sprue bits] rows={updated}')

        # ── AGA-024 Big Boss + Painboy + Bannernob: also allow & and digit 3 ──
        # The canonical listing title contains "Big Boss, Bannernob & Painboy",
        # so & must be allowed (bypasses the bundle-detection check).
        # The bundle is 3 models; some listings include a standalone count digit.
        updated = Product.objects.filter(gw_sku='AGA-024').update(
            ebay_allowed_title_words='nos sprue & 3'
        )
        self.stdout.write(f'AGA-024 ebay_allowed_title_words=[nos sprue & 3] rows={updated}')

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_jun2026r done'))
