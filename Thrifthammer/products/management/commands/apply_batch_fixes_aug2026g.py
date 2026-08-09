from django.core.management.base import BaseCommand
from products.models import Product


class Command(BaseCommand):
    help = (
        'Aug 2026g: three Drukhari eBay matching fixes, all user-confirmed '
        '2026-08-07. (1) DR-002 Drazhar: add "painted" to '
        'ebay_allowed_title_words -- the correct $37 listing '
        '("...Brand new sealed") was being rejected because its '
        'shortDescription says "features intricate painted details" '
        '(marketing boilerplate about sculpt detail, not a painted-model '
        'disclosure); ebay_allowed_title_words exempts words from both the '
        'title AND description bits filters. (2) DR-004 Succubus: add '
        '"blister" to ebay_allowed_title_words -- two cheaper listings '
        '($30.40/$35.50) were rejected for saying "Blister" in the title; '
        'user confirmed this packaging is legitimate for this SKU. '
        '(3) DR-018 Hellions: set ebay_search_name to "Hellions Warhammer '
        '40K" (was defaulting to product name "Drukhari Hellions", a '
        '2-keyword name that fails whenever a seller title omits '
        '"Drukhari" -- the only real, correctly-priced listings on eBay do '
        'exactly that). Verified via a non-saving dry test that this '
        'surfaces the correct $33.25 listing as both eBay Best Match #1 '
        'and cheapest valid, so it wins outright -- confirmed even though '
        'the query still returns some invalid "(No Hellions)" bundle '
        'listings that pass validation (a separate, still-open matcher '
        'gap not fixed here), those are both pricier and rank lower, so '
        'they are never chosen.'
    )

    def handle(self, *args, **options):
        updated = Product.objects.filter(gw_sku='DR-002').update(
            ebay_allowed_title_words='painted'
        )
        self.stdout.write(f'DR-002 ebay_allowed_title_words updated, rows={updated}')

        updated = Product.objects.filter(gw_sku='DR-004').update(
            ebay_allowed_title_words='blister'
        )
        self.stdout.write(f'DR-004 ebay_allowed_title_words updated, rows={updated}')

        updated = Product.objects.filter(gw_sku='DR-018').update(
            ebay_search_name='Hellions Warhammer 40K'
        )
        self.stdout.write(f'DR-018 ebay_search_name updated, rows={updated}')

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_aug2026g done'))
