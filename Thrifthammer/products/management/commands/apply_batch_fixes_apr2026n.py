"""
apply_batch_fixes_apr2026n
~~~~~~~~~~~~~~~~~~~~~~~~~~
- Rhino + Chaos Rhino: add '30K' SKU avoid kw
- Space Marine Apothecary: add '9193' SKU avoid kw
- Lieutenant with Power Sword: update search name to be more specific
- Firestrike Servo-Turrets: fix search name (add hyphen), clear eBay not_available
- Gladiator Valiant: clear eBay not_available; copy Lancer eBay URL to Reaper+Valiant
- Space Marine Scouts: update search name to Kill Team Scout Squad
- Assault Intercessors with Jump Packs: update search name
- Space Marine Incursors: copy MM+eBay URLs from Infiltrators (leave GW)
- Space Marine Combat Patrol: add 'emperors children chaos' SKU avoid kws
- Logan Grimnar: enable eBay scraping, set search name
- Delete ultramarines-roboute-guilliman (duplicate of space-marine-roboute-guilliman)
- Delete ultramarines-marneus-calgar (duplicate of marneus-calgar)
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product


def _add_neg_kws(product, kws, stdout):
    existing = set((product.ebay_negative_keywords or '').split())
    existing.update(kws)
    product.ebay_negative_keywords = ' '.join(sorted(existing))
    product.save()
    stdout.write(f'  {product.slug}: neg kws -> {product.ebay_negative_keywords}')


def _copy_url(src, dst, retailer_id, stdout):
    cp_src = CurrentPrice.objects.filter(
        product=src, retailer_id=retailer_id, not_available=False
    ).exclude(url='').first()
    if not cp_src:
        return
    cp_dst, _ = CurrentPrice.objects.get_or_create(
        product=dst, retailer_id=retailer_id,
        defaults={'price': None, 'url': '', 'in_stock': False, 'not_available': True},
    )
    cp_dst.url = cp_src.url
    cp_dst.price = cp_src.price
    cp_dst.in_stock = cp_src.in_stock
    cp_dst.not_available = False
    cp_dst.save()
    stdout.write(f'    r{retailer_id}: copied from {src.slug}')


def _clear_ebay(product, search_name=None, stdout=None):
    cp, created = CurrentPrice.objects.get_or_create(
        product=product, retailer_id=6,
        defaults={'price': None, 'url': '', 'in_stock': False, 'not_available': False},
    )
    if not created:
        cp.not_available = False
        cp.url = ''
        cp.price = None
        cp.save()
    if search_name is not None:
        product.ebay_search_name = search_name
        product.save()
    if stdout:
        stdout.write(f'  {product.slug}: eBay enabled | search={search_name!r}')


class Command(BaseCommand):
    help = 'Apr-2026-n: SM keyword fixes, dual-kit syncs, duplicate deletes.'

    def handle(self, *args, **options):

        # ── Rhino + Chaos Rhino: add '30K' avoid kw ──────────────────────────
        for slug in ('space-marine-rhino', 'chaos-rhino'):
            try:
                _add_neg_kws(Product.objects.get(slug=slug), {'30k'}, self.stdout)
            except Product.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'  {slug} not found'))

        # ── Space Marine Apothecary: add '9193' avoid kw ─────────────────────
        try:
            _add_neg_kws(Product.objects.get(slug='space-marine-apothecary'), {'9193'}, self.stdout)
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING('  space-marine-apothecary not found'))

        # ── Lieutenant with Power Sword: more specific search name ────────────
        try:
            p = Product.objects.get(slug='space-marine-lieutenant-with-power-sword')
            p.ebay_search_name = 'Primaris Lieutenant Power Sword Space Marines Warhammer'
            p.save()
            self.stdout.write(f'  {p.slug}: search name updated')
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING('  space-marine-lieutenant-with-power-sword not found'))

        # ── Firestrike Servo-Turrets: fix search name + enable eBay ──────────
        try:
            p = Product.objects.get(slug='space-marine-firestrike-servo-turrets')
            _clear_ebay(p, search_name='Space Marine Firestrike Servo-Turrets Warhammer', stdout=self.stdout)
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING('  space-marine-firestrike-servo-turrets not found'))

        # ── Gladiator: clear Valiant eBay, copy Lancer URL to Valiant+Reaper ─
        try:
            lancer = Product.objects.get(slug='space-marine-gladiator-lancer')
            for slug in ('space-marine-gladiator-valiant', 'space-marine-gladiator-reaper'):
                try:
                    p = Product.objects.get(slug=slug)
                    _copy_url(lancer, p, 6, self.stdout)
                    self.stdout.write(f'  {slug}: eBay URL synced from Lancer')
                except Product.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'  {slug} not found'))
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING('  space-marine-gladiator-lancer not found'))

        # ── Space Marine Scouts: update search name ───────────────────────────
        try:
            p = Product.objects.get(slug='space-marine-scouts')
            p.ebay_search_name = 'Kill Team Scout Squad Space Marine Warhammer'
            p.save()
            self.stdout.write(f'  {p.slug}: search name updated')
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING('  space-marine-scouts not found'))

        # ── Assault Intercessors with Jump Packs: update search name ──────────
        try:
            p = Product.objects.get(slug='space-marine-assault-intercessors-jump-packs')
            p.ebay_search_name = 'Jump Pack Intercessors Space Marines Warhammer'
            p.save()
            self.stdout.write(f'  {p.slug}: search name updated')
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING('  space-marine-assault-intercessors-jump-packs not found'))

        # ── Space Marine Incursors: copy MM + eBay from Infiltrators ─────────
        try:
            infil = Product.objects.get(slug='space-marine-infiltrators')
            incur = Product.objects.get(slug='space-marine-incursors')
            for rid in (2, 6):  # MM, eBay
                _copy_url(infil, incur, rid, self.stdout)
            self.stdout.write('  space-marine-incursors: MM + eBay synced from Infiltrators')
        except Product.DoesNotExist as e:
            self.stdout.write(self.style.WARNING(f'  Incursors/Infiltrators not found: {e}'))

        # ── Space Marine Combat Patrol: add avoid kws ─────────────────────────
        try:
            _add_neg_kws(
                Product.objects.get(slug='space-marine-combat-patrol'),
                {'emperors', 'children', 'chaos'},
                self.stdout,
            )
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING('  space-marine-combat-patrol not found'))

        # ── Logan Grimnar: enable eBay scraping ───────────────────────────────
        try:
            p = Product.objects.get(slug='space-wolves-logan-grimnar')
            _clear_ebay(p, search_name='Logan Grimnar Space Wolves Warhammer 40k', stdout=self.stdout)
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING('  space-wolves-logan-grimnar not found'))

        # ── Delete duplicate Roboute Guilliman (phase-2 duplicate) ────────────
        n, _ = Product.objects.filter(slug='ultramarines-roboute-guilliman').delete()
        self.stdout.write(
            f'  Deleted ultramarines-roboute-guilliman' if n
            else self.style.WARNING('  ultramarines-roboute-guilliman not found')
        )

        # ── Delete duplicate Marneus Calgar (phase-2 duplicate) ───────────────
        n, _ = Product.objects.filter(slug='ultramarines-marneus-calgar').delete()
        self.stdout.write(
            f'  Deleted ultramarines-marneus-calgar' if n
            else self.style.WARNING('  ultramarines-marneus-calgar not found')
        )

        self.stdout.write(self.style.SUCCESS('Done.'))
