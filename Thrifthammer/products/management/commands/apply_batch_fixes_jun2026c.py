"""
Management command: apply_batch_fixes_jun2026c

eBay negative keyword additions (2026-06-24). All values are complete strings.

  AM-008  Astra Militarum Bullgryns
    ebay_negative_keywords: + 'unpainted'

  AM-037  Astra Militarum Ogryns
    ebay_negative_keywords: + 'unpainted'

  AM-015  Codex: Astra Militarum
    ebay_negative_keywords: + '2014'

  CK-005  Chaos War Dog Stalkers
    ebay_negative_keywords: + 'x1'

  CK-006  Chaos War Dog Brigands
    ebay_negative_keywords: + 'x1'

  CK-007  Chaos War Dog Karnivores
    ebay_negative_keywords: + 'x1'

  CD-016  Burning Chariot of Tzeentch
    ebay_negative_keywords: + 'No Riders'

  CSM-010  Chaos Space Marine Dark Apostle
    ebay_negative_keywords: + 'both'

  HOS-015  Endless Spells: Hedonites of Slaanesh
    ebay_negative_keywords: + 'Wheels'

  COS-008  Order Battletome: Cities of Sigmar 4th Edition
    ebay_negative_keywords: + 'sealed'

  DOT-010  Chaos Battletome: Disciples of Tzeentch
    ebay_negative_keywords: + 'sealed'

  DOT-011  Endless Spells: Disciples of Tzeentch
    ebay_negative_keywords: + 'burning'

  OBR-008  Endless Spells: Ossiarch Bonereapers
    ebay_negative_keywords: + 'SHRIEKER'

  BOK-002  Judgements of Khorne
    ebay_negative_keywords: + 'Wrath-Axe'

  BOK-012  Goreblade Warband
    ebay_negative_keywords: + 'Khorgorath'

  LRL-011  Order Battletome: Lumineth Realm-lords
    ebay_negative_keywords: + 'army-book'

  FEC-020  Endless Spells: Flesh-eater Courts
    ebay_negative_keywords: + 'CADAVEROUS'

  GG-016  Endless Spells: Gloomspite Gitz
    ebay_negative_keywords: + 'ARACHNOCAULDRON'

  GG-029  Destruction Battletome: Gloomspite Gitz
    ebay_negative_keywords: + 'sealed'

  SYL-009  Endless Spells: Sylvaneth
    ebay_negative_keywords: + 'Spiteswarm'

  SK-001  Chaos Battletome: Skaven
    ebay_negative_keywords: + '2022'
"""

from django.core.management.base import BaseCommand

from products.models import Product


class Command(BaseCommand):
    """eBay negative keyword additions for 21 products across 10 factions."""

    help = 'apply_batch_fixes_jun2026c — eBay negative keyword additions'

    def handle(self, *args, **options):
        """Run the command."""
        fixes = [
            ('AM-008',  'legions imperialis Resin 04-113 100th 1926 TShirt Plushie Plush Proxies unpainted'),
            ('AM-037',  'legions imperialis Resin 04-113 100th 1926 TShirt Plushie Plush Proxies unpainted'),
            ('AM-015',  'legions imperialis 3rd 4th 5th 6th 7th 8th 9th Resin 04-113 100th 1926 TShirt Plushie Plush Proxies 2014'),
            ('CK-005',  'Proxies x1'),
            ('CK-006',  'Proxies x1'),
            ('CK-007',  'Proxies x1'),
            ('CD-016',  'legions imperialis Resin 04-113 Proxies No Riders'),
            ('CSM-010', 'legions imperialis Resin 04-113 Proxies both'),
            ('HOS-015', 'legions imperialis Resin 04-113 Proxies Wheels'),
            ('COS-008', 'legions imperialis Resin 04-113 Proxies sealed'),
            ('DOT-010', 'legions imperialis Resin 04-113 Proxies sealed'),
            ('DOT-011', 'legions imperialis Resin 04-113 Proxies burning'),
            ('OBR-008', 'legions imperialis Resin 04-113 Proxies SHRIEKER'),
            ('BOK-002', 'legions imperialis Resin 04-113 Proxies Wrath-Axe'),
            ('BOK-012', 'legions imperialis Resin 04-113 Proxies Khorgorath'),
            ('LRL-011', 'legions imperialis Resin 04-113 Proxies army-book'),
            ('FEC-020', 'legions imperialis Resin 04-113 Proxies CADAVEROUS'),
            ('GG-016',  'legions imperialis Resin 04-113 Proxies ARACHNOCAULDRON'),
            ('GG-029',  'legions imperialis Resin 04-113 Proxies sealed'),
            ('SYL-009', 'legions imperialis Resin 04-113 Proxies Spiteswarm'),
            ('SK-001',  'legions imperialis Resin 04-113 100th 1926 TShirt Plushie Plush Proxies 2022'),
        ]

        for sku, value in fixes:
            updated = Product.objects.filter(gw_sku=sku).update(ebay_negative_keywords=value)
            if updated:
                self.stdout.write(f'  {sku}: ebay_negative_keywords set to {repr(value)}')
            else:
                self.stdout.write(self.style.WARNING(f'  {sku}: not found'))

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_jun2026c complete.'))
