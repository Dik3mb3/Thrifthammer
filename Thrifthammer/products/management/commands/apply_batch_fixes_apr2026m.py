"""
apply_batch_fixes_apr2026m
~~~~~~~~~~~~~~~~~~~~~~~~~~
- Delete blood-angels-death-company
- chaos-sorcerer-lord-terminator: fix 404 GW URL
- chaos-defiler: add 'paint' SKU avoid kw, clear wrong eBay URL
- GK Interceptor/Purifier/Purgation squads: copy MM+Amazon+eBay from Strike Squad,
  update ebay_search_name to auto-match Strike Squad listings
- iron-hands-iron-father-feirros: clear not_available on eBay row
- ork-combat-patrol: add 'deffkoptas' + 'waaagh' SKU avoid kws
- ork-painboy: clear not_available, set search name
- ork-warboss-with-attack-squig: clear not_available, set search name
- ork-gunwagon + ork-bonebreaka: copy MM+NK+Amazon+eBay from ork-battlewagon
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product


RETAILER_GW = 1
RETAILER_MM = 2
RETAILER_NK = 3
RETAILER_AMZ = 5
RETAILER_EBAY = 6


def _copy_url(src_product, dst_product, retailer_id, stdout):
    """Copy a retailer URL from src to dst, skipping GW and empty sources."""
    src = CurrentPrice.objects.filter(
        product=src_product, retailer_id=retailer_id, not_available=False
    ).exclude(url='').first()
    if not src:
        return
    dst, _ = CurrentPrice.objects.get_or_create(
        product=dst_product,
        retailer_id=retailer_id,
        defaults={'price': None, 'url': '', 'in_stock': False, 'not_available': True},
    )
    dst.url = src.url
    dst.price = src.price
    dst.in_stock = src.in_stock
    dst.not_available = False
    dst.save()
    stdout.write(f'    r{retailer_id}: copied from {src_product.slug}')


def _clear_ebay_na(product, search_name=None, stdout=None):
    """Clear not_available on eBay row so scraper can find a listing."""
    cp, created = CurrentPrice.objects.get_or_create(
        product=product,
        retailer_id=RETAILER_EBAY,
        defaults={'price': None, 'url': '', 'in_stock': False, 'not_available': False},
    )
    if not created:
        cp.not_available = False
        cp.url = ''
        cp.price = None
        cp.save()
    if search_name:
        product.ebay_search_name = search_name
        product.save()
    if stdout:
        stdout.write(f'  {product.slug}: eBay enabled for scraping')


class Command(BaseCommand):
    help = 'Apr-2026-m: delete death company, GK dual-kit sync, eBay fixes, Ork SKUs.'

    def handle(self, *args, **options):

        # ── Delete Blood Angels Death Company ────────────────────────────────
        n, _ = Product.objects.filter(slug='blood-angels-death-company').delete()
        if n:
            self.stdout.write('  Deleted blood-angels-death-company')
        else:
            self.stdout.write(self.style.WARNING('  blood-angels-death-company not found'))

        # ── Chaos Sorcerer Lord in Terminator Armour: fix GW URL ─────────────
        try:
            p = Product.objects.get(slug='chaos-sorcerer-lord-terminator')
            cp, _ = CurrentPrice.objects.get_or_create(
                product=p, retailer_id=RETAILER_GW,
                defaults={'price': None, 'url': '', 'in_stock': False, 'not_available': True},
            )
            cp.url = ('https://www.warhammer.com/en-US/shop/Chaos-Terminator-Sorcerer-2019'
                      '?queryID=c87ff804b4228e04bac1b57d3dabcfb7')
            cp.not_available = False
            cp.save()
            self.stdout.write('  chaos-sorcerer-lord-terminator: GW URL fixed')
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING('  chaos-sorcerer-lord-terminator not found'))

        # ── Chaos Defiler: add 'paint' avoid kw, clear wrong eBay URL ────────
        try:
            p = Product.objects.get(slug='chaos-defiler')
            kws = set((p.ebay_negative_keywords or '').split())
            kws.add('paint')
            p.ebay_negative_keywords = ' '.join(sorted(kws))
            p.save()
            # Clear the wrong eBay listing so scraper can find a correct one
            cp = CurrentPrice.objects.filter(product=p, retailer_id=RETAILER_EBAY).first()
            if cp:
                cp.url = ''
                cp.price = None
                cp.not_available = False
                cp.save()
            self.stdout.write("  chaos-defiler: 'paint' kw added, eBay URL cleared")
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING('  chaos-defiler not found'))

        # ── GK Interceptor/Purifier/Purgation: copy from Strike Squad ────────
        try:
            strike = Product.objects.get(slug='grey-knights-strike-squad')
            gk_search_name = 'Grey Knights Strike Squad Warhammer'
            for slug in ('grey-knights-interceptor-squad',
                         'grey-knights-purifier-squad',
                         'grey-knights-purgation-squad'):
                try:
                    p = Product.objects.get(slug=slug)
                    p.ebay_search_name = gk_search_name
                    p.save()
                    self.stdout.write(f'  {slug}: search name updated')
                    for rid in (RETAILER_MM, RETAILER_AMZ, RETAILER_EBAY):
                        _copy_url(strike, p, rid, self.stdout)
                except Product.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'  {slug} not found'))
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING('  grey-knights-strike-squad not found'))

        # ── Iron Father Feirros: enable eBay scraping ─────────────────────────
        try:
            p = Product.objects.get(slug='iron-hands-iron-father-feirros')
            _clear_ebay_na(p, stdout=self.stdout)
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING('  iron-hands-iron-father-feirros not found'))

        # ── Ork Combat Patrol: add avoid kws ─────────────────────────────────
        try:
            p = Product.objects.get(slug='ork-combat-patrol')
            kws = set((p.ebay_negative_keywords or '').split())
            kws.update({'deffkoptas', 'waaagh'})
            p.ebay_negative_keywords = ' '.join(sorted(kws))
            p.save()
            self.stdout.write("  ork-combat-patrol: 'deffkoptas' + 'waaagh' added")
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING('  ork-combat-patrol not found'))

        # ── Ork Painboy: enable eBay scraping ────────────────────────────────
        try:
            p = Product.objects.get(slug='ork-painboy')
            _clear_ebay_na(p, search_name='Ork Painboy Warhammer 40k', stdout=self.stdout)
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING('  ork-painboy not found'))

        # ── Ork Warboss with Attack Squig: enable eBay scraping ──────────────
        try:
            p = Product.objects.get(slug='ork-warboss-with-attack-squig')
            _clear_ebay_na(
                p,
                search_name='Ork Warboss Attack Squig Warhammer 40k',
                stdout=self.stdout,
            )
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING('  ork-warboss-with-attack-squig not found'))

        # ── Gunwagon + Bonebreaka: copy from Battlewagon ─────────────────────
        try:
            battlewagon = Product.objects.get(slug='ork-battlewagon')
            for slug in ('ork-gunwagon', 'ork-bonebreaka'):
                try:
                    p = Product.objects.get(slug=slug)
                    self.stdout.write(f'  {slug}: copying URLs from ork-battlewagon')
                    for rid in (RETAILER_MM, RETAILER_NK, RETAILER_AMZ, RETAILER_EBAY):
                        _copy_url(battlewagon, p, rid, self.stdout)
                except Product.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'  {slug} not found'))
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING('  ork-battlewagon not found'))

        self.stdout.write(self.style.SUCCESS('Done.'))
