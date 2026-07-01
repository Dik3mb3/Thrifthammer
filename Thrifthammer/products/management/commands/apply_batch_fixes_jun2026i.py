from django.core.management.base import BaseCommand

from products.models import Product


class Command(BaseCommand):
    help = 'Jun 2026i: Astartes Legions eBay search name, negative keyword, and allowed title word fixes'

    def handle(self, *args, **options):
        # ── eBay search name updates ──────────────────────────────────────────
        search_fixes = [
            ('AL-005', 'Legiones Astartes Whirlwind Missile Tank Warhammer'),
            ('AL-009', 'Legion Praetor With Power Axe Horus Heresy Warhammer'),
            ('AL-011', 'Legion Cataphractii Praetor & Chaplain Consul Warhammer'),
            ('AL-012', 'Legiones Astartes Tartaros Terminator Squad Warhammer'),
            ('AL-013', 'Geigor Fell-Hand Captain Space Wolves Warhammer Horus Heresy'),
            ('AL-016', 'Breacher Squad Upgrade Set Legiones Astartes Warhammer'),
            ('AL-031', 'Legiones Astartes Land Raider Proteus Warhammer Horus Heresy'),
            ('AL-032', 'Volkite Culverins Lascannon Autocannon Heavy Weapons Upgrade Set'),
            ('AL-033', 'Warhammer Horus Heresy Legiones Astartes Heavy Weapons Upgrade Set Heavy Flamers'),
            ('AL-034', 'Horus Heresy Leviathan Siege Dreadnought with Claw & Drill Weapons'),
            ('AL-036', 'Contemptor Dreadnought Weapons Frame 2 Warhammer The Horus Heresy'),
            ('AL-037', 'Contemptor Dreadnought Weapons Frame 1 Warhammer The Horus Heresy'),
            ('AL-039', 'Special Weapons Upgrade Set Warhammer Horus Heresy Legiones Astartes'),
            ('AL-040', 'Missile Launchers Heavy Bolters Heavy Weapons Upgrade Set Warhammer'),
            ('AL-046', 'Disintegrator Weapons Upgrade Set Warhammer Horus Heresy'),
            ('AL-056', 'Legiones Astartes Melee Weapons Upgrade Set Warhammer 30k'),
            ('AL-057', 'Legiones Astartes MKIII Command Squad Warhammer'),
            ('AL-058', 'MKVI Command Squad Legiones Astartes Warhammer Horus Heresy'),
        ]
        for sku, name in search_fixes:
            updated = Product.objects.filter(gw_sku=sku).update(ebay_search_name=name)
            self.stdout.write(f'{sku} ebay_search_name=[{name}] rows={updated}')

        # ── eBay negative keyword updates ─────────────────────────────────────
        # Complete replacement values (not additive)
        neg_fixes = [
            ('AL-005', 'Tank Squadron'),
            ('AL-036', '1'),
            ('AL-037', '2'),
        ]
        for sku, keywords in neg_fixes:
            updated = Product.objects.filter(gw_sku=sku).update(ebay_negative_keywords=keywords)
            self.stdout.write(f'{sku} ebay_negative_keywords=[{keywords}] rows={updated}')

        # ── eBay allowed title words ───────────────────────────────────────────
        # AL-011 search name contains & — allow it through the bits filter
        updated = Product.objects.filter(gw_sku='AL-011').update(ebay_allowed_title_words='&')
        self.stdout.write(f'AL-011 ebay_allowed_title_words=[&] rows={updated}')

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_jun2026i done'))
