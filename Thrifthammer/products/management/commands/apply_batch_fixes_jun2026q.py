from django.core.management.base import BaseCommand
from django.db.models import F, Value
from django.db.models.functions import Concat

from products.models import Product


class Command(BaseCommand):
    help = 'Jun 2026q: eBay keyword fixes (9 SKUs), global Foil, delete KT-100/KT-003'

    def handle(self, *args, **options):
        # ── Individual SKU eBay negative keyword updates ──────────────────────
        # Complete replacement strings — prior keywords included verbatim.
        # Run BEFORE global Foil so the append lands on the final value.
        neg_fixes = [
            # KT-002 Kill Team: Into the Dark
            # prior: 'legions imperialis Resin 04-113 Proxies'
            # add:   Dynamo Generator Console Terrain
            (
                'KT-002',
                'legions imperialis Resin 04-113 Proxies Dynamo Generator Console Terrain',
            ),
            # EOM-012 Empire Knights
            # prior: 'legions imperialis Resin 04-113 Proxies'
            # add:   Panther Grand Master (stored as separate words per eBay keyword rules)
            (
                'EOM-012',
                'legions imperialis Resin 04-113 Proxies Panther Grand Master',
            ),
            # NM-057 Van Saar Tek-hunters
            # prior: '' (empty)
            # add:   4x x4
            (
                'NM-057',
                '4x x4',
            ),
            # AM-015 Codex: Astra Militarum
            # prior: 'legions imperialis 3rd 4th 5th 6th 7th 8th 9th Resin 04-113 100th 1926 TShirt Plushie Plush Proxies 2014'
            # add:   History
            (
                'AM-015',
                'legions imperialis 3rd 4th 5th 6th 7th 8th 9th Resin 04-113 100th 1926 TShirt Plushie Plush Proxies 2014 History',
            ),
            # 56-19 T'au Pathfinders
            # prior: 'datacards Apex mantic enforcer firefight grav-inhibitor legions imperialis Resin 04-113 8080C 2000 Proxies'
            # add:   Drone
            (
                '56-19',
                'datacards Apex mantic enforcer firefight grav-inhibitor legions imperialis Resin 04-113 8080C 2000 Proxies Drone',
            ),
            # GG-016 Endless Spells: Gloomspite Gitz
            # prior: 'legions imperialis Resin 04-113 Proxies ARACHNOCAULDRON'
            # add:   Mushroom
            (
                'GG-016',
                'legions imperialis Resin 04-113 Proxies ARACHNOCAULDRON Mushroom',
            ),
            # OBR-008 Endless Spells: Ossiarch Bonereapers
            # prior: 'legions imperialis Resin 04-113 Proxies SHRIEKER'
            # add:   souleater
            (
                'OBR-008',
                'legions imperialis Resin 04-113 Proxies SHRIEKER souleater',
            ),
            # SYL-009 Endless Spells: Sylvaneth
            # prior: 'legions imperialis Resin 04-113 Proxies Spiteswarm'
            # add:   Skullroot
            (
                'SYL-009',
                'legions imperialis Resin 04-113 Proxies Spiteswarm Skullroot',
            ),
            # NM-008 Orlock Gang
            # prior: '' (empty)
            # add:   Book
            (
                'NM-008',
                'Book',
            ),
        ]
        for sku, value in neg_fixes:
            updated = Product.objects.filter(gw_sku=sku).update(ebay_negative_keywords=value)
            self.stdout.write(f'{sku} ebay_negative_keywords=[{value}] rows={updated}')

        # ── 56-19 batch_tag: set to tau-empire so faction-wide scraper picks it up ──
        updated = Product.objects.filter(gw_sku='56-19').update(batch_tag='tau-empire')
        self.stdout.write(f'56-19 batch_tag=tau-empire rows={updated}')

        # ── Global Foil: append to all products ───────────────────────────────
        # Runs after individual updates so Foil lands on the final combined value.
        empty_count = Product.objects.filter(
            ebay_negative_keywords=''
        ).update(ebay_negative_keywords='Foil')
        self.stdout.write(f'Foil set (was empty) rows={empty_count}')

        nonempty_count = Product.objects.exclude(
            ebay_negative_keywords=''
        ).exclude(
            ebay_negative_keywords__icontains='Foil'
        ).update(
            ebay_negative_keywords=Concat(F('ebay_negative_keywords'), Value(' Foil'))
        )
        self.stdout.write(f'Foil appended (non-empty) rows={nonempty_count}')

        # ── Delete KT-100 and KT-003 ──────────────────────────────────────────
        deleted_100, _ = Product.objects.filter(gw_sku='KT-100').delete()
        self.stdout.write(f'KT-100 deleted rows={deleted_100}')

        deleted_003, _ = Product.objects.filter(gw_sku='KT-003').delete()
        self.stdout.write(f'KT-003 deleted rows={deleted_003}')

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_jun2026q done'))
