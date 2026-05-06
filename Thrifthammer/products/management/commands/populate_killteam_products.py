"""
Management command: populate_killteam_products

Seeds 33 Kill Team products (KT-001 to KT-033) with GW, Amazon,
Miniature Market, and Noble Knight price rows.

Idempotent — safe to re-run.
"""

from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Product, Retailer

AMAZON_TAG = 'thrifthammer7-20'
NK_AWID = '1576'


def _amazon_url(asin):
    if not asin:
        return ''
    return f'https://www.amazon.com/dp/{asin}?tag={AMAZON_TAG}'


def _nk_url(base_url):
    if not base_url:
        return ''
    return f'{base_url}?awid={NK_AWID}'


# (gw_sku, name, slug, msrp, gw_url, amazon_asin, mm_url, nk_base_url)
PRODUCTS = [
    ('KT-001', 'Kill Team: Starter Set', 'kill-team-starter-set', Decimal('114.00'),
     'https://www.warhammer.com/en-US/shop/kill-team-starter-set-2024-eng',
     'B0DKNXNTKS',
     'https://www.miniaturemarket.com/kill-team-starter-set-gw-103-54.html',
     'https://www.nobleknight.com/P/2148213779/Kill-Team---Starter-Set'),

    ('KT-002', 'Killzone: Tomb World', 'killzone-tomb-world', Decimal('165.00'),
     'https://www.warhammer.com/en-US/shop/killzone-tomb-world-2025',
     'B0FZD5H5FQ',
     'https://www.miniaturemarket.com/Warhammer-40K-Kill-Team-Killzone-Tomb-World/GW-103-99-2025',
     'https://www.nobleknight.com/P/2148373772/Killzone---Tomb-World'),

    ('KT-003', 'Kill Team: Core Book', 'kill-team-core-book', Decimal('64.00'),
     'https://www.warhammer.com/en-US/shop/kill-team-core-book-2024-eng',
     '1804573744',
     'https://www.miniaturemarket.com/warhammer-40k-kill-team-core-book-gw-102-01-2024.html',
     'https://www.nobleknight.com/P/2148198023/Kill-Team---Core-Book'),

    ('KT-004', 'Kill Team: Battleclade', 'kill-team-battleclade', Decimal('73.50'),
     'https://www.warhammer.com/en-US/shop/kill-team-battleclade-2025',
     'B0FNS1MKFZ',
     'https://www.miniaturemarket.com/kill-team-battleclade-gw-103-97.html',
     'https://www.nobleknight.com/P/2148344136/Battleclade'),

    ('KT-005', 'Kill Team: Sanctifiers', 'kill-team-sanctifiers', Decimal('69.00'),
     'https://www.warhammer.com/en-US/shop/kill-team-sanctifiers-2025',
     'B0FCG9TJ21',
     'https://www.miniaturemarket.com/kill-team-sanctifiers-gw-103-90.html',
     'https://www.nobleknight.com/P/2148317259/Sanctifiers'),

    ('KT-006', 'Kill Team: Goremongers', 'kill-team-goremongers', Decimal('69.00'),
     'https://www.warhammer.com/en-US/shop/kill-team-goremongers-2025',
     'B0FCG8V21Z',
     'https://www.miniaturemarket.com/kill-team-goremongers-gw-103-89.html',
     'https://www.nobleknight.com/P/2148317256/Goremongers'),

    ('KT-007', 'Kill Team: Wrecka Krew', 'kill-team-wrecka-krew', Decimal('69.00'),
     'https://www.warhammer.com/en-US/shop/kill-team-wrecka-krew-2025',
     'B0F1P71975',
     'https://www.miniaturemarket.com/kill-team-wrecka-krew-ork-breaka-boyz-tankbustas-mob-gw-103-87.html',
     'https://www.nobleknight.com/P/2148286609/Wrecka-Crew'),

    ('KT-008', 'Kill Team: Fellgor Ravagers', 'kill-team-fellgor-ravagers', Decimal('69.00'),
     'https://www.warhammer.com/en-US/shop/kill-team-fellgor-ravagers-2024',
     'B0DPMY3Y5Z',
     'https://www.miniaturemarket.com/kill-team-fellgor-ravagers-gw-103-34-2024.html',
     'https://www.nobleknight.com/P/2148239650/Fellgor-Ravagers'),

    ('KT-009', 'Kill Team: Exaction Squad', 'kill-team-exaction-squad', Decimal('69.00'),
     'https://www.warhammer.com/en-US/shop/kill-team-exaction-squad-2024',
     'B0DPMWY66S',
     'https://www.miniaturemarket.com/kill-team-exaction-squad-gw-103-27-2024.html',
     'https://www.nobleknight.com/P/2148239666/Exaction-Squad'),

    ('KT-010', 'Kill Team: Imperial Navy Breachers', 'kill-team-imperial-navy-breachers', Decimal('69.00'),
     'https://www.warhammer.com/en-US/shop/kill-team-imperial-navy-breachers-2024',
     'B0DPMX5NG4',
     'https://www.miniaturemarket.com/kill-team-imperial-navy-breachers-gw-103-07-2024.html',
     'https://www.nobleknight.com/P/2148239639/Imperial-Navy-Breachers'),

    ('KT-011', 'Kill Team: Tempestus Aquilons', 'kill-team-tempestus-aquilons', Decimal('69.00'),
     'https://www.warhammer.com/en-US/shop/kill-team-tempestus-aquilons-2024',
     'B0DPMX422X',
     'https://www.miniaturemarket.com/kill-team-tempestus-aquilons-gw-103-52.html',
     'https://www.nobleknight.com/P/2148239648/Tempestus-Aquilons'),

    ('KT-012', 'Kill Team: Kasrkin', 'kill-team-kasrkin', Decimal('69.00'),
     'https://www.warhammer.com/en-US/shop/kill-team-kasrkin-2024',
     'B0DKNXGVWL',
     'https://www.miniaturemarket.com/kill-team-kasrkin-gw-103-18-2024.html',
     'https://www.nobleknight.com/P/2148213787/Kasrkin'),

    ('KT-013', 'Killzone: Bheta-Decima', 'killzone-bheta-decima', Decimal('127.00'),
     'https://www.warhammer.com/en-US/shop/killzone-bheta-decima-2024',
     'B0CQ3MQVVM',
     '',
     'https://www.nobleknight.com/P/2148108032/Kill-Team---Killzone-Bheta-Decima'),

    ('KT-014', 'Killzone: Gallowdark', 'killzone-gallowdark', Decimal('127.00'),
     'https://www.warhammer.com/en-US/shop/killzone-gallowdark-2024',
     'B0C4HM7VCQ',
     '',
     ''),

    ('KT-015', 'Kill Team: Equipment Pack', 'kill-team-equipment-pack', Decimal('47.00'),
     'https://www.warhammer.com/en-US/shop/kill-team-upgrade-equipment-pack-2024',
     'B0DH4VMJMN',
     'https://www.miniaturemarket.com/warhammer-40k-kill-team-equipment-pack-gw-103-53.html',
     'https://www.nobleknight.com/P/2148198397/Kill-Team---Equipment-Pack'),

    ('KT-016', 'Kill Team: Brood Brothers', 'kill-team-brood-brothers', Decimal('69.00'),
     'https://www.warhammer.com/en-US/shop/kill-team-brood-brothers-2024',
     'B0DH4X7DYS',
     'https://www.miniaturemarket.com/warhammer-40k-kill-team-genestealer-cults-brood-brothers-gw-103-31.html',
     'https://www.nobleknight.com/P/2148198391/Brood-Brothers'),

    ('KT-017', 'Kill Team: Nemesis Claw', 'kill-team-nemesis-claw', Decimal('77.00'),
     'https://www.warhammer.com/en-US/shop/kill-team-nemesis-claw-2024',
     'B0DH4WPSSJ',
     'https://www.miniaturemarket.com/warhammer-40k-kill-team-chaos-space-marines-nemesis-claw-gw-103-43.html',
     'https://www.nobleknight.com/P/2148198382/Nemesis-Claw'),

    ('KT-018', 'Kill Team: Scout Squad', 'kill-team-scout-squad', Decimal('82.00'),
     'https://www.warhammer.com/en-US/shop/kill-team-scout-squad-2024',
     'B0DH4Y2GJS',
     'https://www.miniaturemarket.com/warhammer-40k-kill-team-space-marines-scout-squad-gw-103-44-2024.html',
     'https://www.nobleknight.com/P/2148198377/Scout-Squad'),

    ('KT-019', 'Kill Team: Ratlings', 'kill-team-ratlings', Decimal('69.00'),
     'https://www.warhammer.com/en-US/shop/kill-team-ratlings-2025',
     'B0F1NZDM7L',
     'https://www.miniaturemarket.com/kill-team-ratlings-astra-militarum-abhuman-sharpshooters-gw-103-86.html',
     'https://www.nobleknight.com/P/2148286610/Ratlings'),

    ('KT-020', 'Kill Team: Hearthkyn Salvagers', 'kill-team-hearthkyn-salvagers', Decimal('69.00'),
     'https://www.warhammer.com/en-US/shop/kill-team-hearthkyn-salvagers-2024',
     'B0DPMXJ9JR',
     'https://www.miniaturemarket.com/kill-team-hearthkyn-salvagers-gw-103-33-2024.html',
     'https://www.nobleknight.com/P/2148239658/Hearthkyn-Salvagers'),

    ('KT-021', 'Kill Team: Hand of the Archon', 'kill-team-hand-of-the-archon', Decimal('60.00'),
     'https://www.warhammer.com/en-US/shop/kill-team-hand-of-the-archon-2024',
     'B0DPMY5CGJ',
     'https://www.miniaturemarket.com/kill-team-hand-archon-gw-103-26.html',
     'https://www.nobleknight.com/P/2148239660/Hand-of-the-Archon'),

    ('KT-022', 'Kill Team: Hierotek Circle', 'kill-team-hierotek-circle', Decimal('77.00'),
     'https://www.warhammer.com/en-US/shop/kill-team-hierotek-circle-2024',
     'B0DPMWXWQ5',
     'https://www.miniaturemarket.com/kill-team-hierotek-circle-gw-103-19-2024.html',
     'https://www.nobleknight.com/P/2148239640/Hierotek-Circle'),

    ('KT-023', 'Kill Team: Farstalker Kinband', 'kill-team-farstalker-kinband', Decimal('69.00'),
     'https://www.warhammer.com/en-US/shop/kill-team-farstalker-kinband-2024',
     'B0DPMYQNCS',
     'https://www.miniaturemarket.com/kill-team-farstalker-kinband-gw-103-08-2024.html',
     'https://www.nobleknight.com/P/2148239646/Farstalker-Kinband'),

    ('KT-024', 'Kill Team: Vespid Stingwings', 'kill-team-vespid-stingwings', Decimal('69.00'),
     'https://www.warhammer.com/en-US/shop/kill-team-tau-empire-vespid-stingwings-2024',
     'B0DPMWDS2D',
     'https://www.miniaturemarket.com/kill-team-vespid-stingwings-gw-103-51.html',
     'https://www.nobleknight.com/P/2148239661/Vespid-Stingwings'),

    ('KT-025', 'Kill Team: Hernkyn Yaegirs', 'kill-team-hernkyn-yaegirs', Decimal('69.00'),
     'https://www.warhammer.com/en-US/shop/kill-team-hernkyn-yaegirs-2024',
     'B0DH4VYQ39',
     'https://www.miniaturemarket.com/warhammer-40k-kill-team-leagues-votann-hernkyn-yaegirs-gw-103-35.html',
     'https://www.nobleknight.com/P/2148198368/Hernkyn-Yaegirs'),

    ('KT-026', 'Kill Team: Wolf Scouts', 'kill-team-wolf-scouts', Decimal('69.00'),
     'https://www.warhammer.com/en-US/shop/kill-team-wolf-scouts-2026',
     'B0GHP5LMM5',
     'https://www.miniaturemarket.com/Warhammer-40K-Kill-Team-Wolf-Scouts/GW-102-11-2026',
     'https://www.nobleknight.com/P/2148404196/Wolf-Scouts'),

    ('KT-027', 'Kill Team: Mandrakes', 'kill-team-mandrakes', Decimal('82.00'),
     'https://www.warhammer.com/en-US/shop/kill-team-mandrakes-2024',
     'B0DH4WXJ4G',
     'https://www.miniaturemarket.com/warhammer-40k-kill-team-drukhari-mandrakes-gw-103-42.html',
     'https://www.nobleknight.com/P/2148198376/Mandrakes'),

    ('KT-028', 'Kill Team: Stealth Battlesuits', 'kill-team-stealth-battlesuits', Decimal('69.00'),
     'https://www.warhammer.com/en-US/shop/kill-team-xv26-stealth-battlesuits-2026',
     'B0GHPCGWN3',
     'https://www.miniaturemarket.com/Warhammer-40K-Kill-Team-XV26-Stealth-Battlesuits/GW-102-13-2026',
     'https://www.nobleknight.com/P/2148404187/XV26-Stealth-Battlesuits'),

    ('KT-029', 'Kill Team: Canoptek Circle', 'kill-team-canoptek-circle', Decimal('77.00'),
     'https://www.warhammer.com/en-US/shop/kill-team-canoptek-circle-2025',
     'B0FZD49K3H',
     'https://www.miniaturemarket.com/Warhammer-40K-Kill-Team-Canoptek-Circle/GW-103-94-2025',
     'https://www.nobleknight.com/P/2148373788/Canoptek-Circle'),

    ('KT-030', 'Kill Team: Raveners', 'kill-team-raveners', Decimal('69.00'),
     'https://www.warhammer.com/en-US/shop/kill-team-raveners-2025',
     'B0FNR75WNM',
     'https://www.miniaturemarket.com/kill-team-raveners-gw-103-98.html',
     'https://www.nobleknight.com/P/2148344143/Raveners'),

    ('KT-031', 'Killzone: Volkus', 'killzone-volkus', Decimal('138.00'),
     'https://www.warhammer.com/en-US/shop/killzone-volkus-2024',
     'B0DPMY5CFW',
     'https://www.miniaturemarket.com/kill-team-killzone-volkus-gw-103-49.html',
     'https://www.nobleknight.com/P/2148239668/Killzone---Volkus'),

    ('KT-032', 'Kill Team: Blades of Khaine', 'kill-team-blades-of-khaine', Decimal('82.00'),
     'https://www.warhammer.com/en-US/shop/kill-team-blades-of-khaine-2024',
     'B0DPMYCXRS',
     'https://www.miniaturemarket.com/kill-team-blades-khaine-gw-103-41-2024.html',
     'https://www.nobleknight.com/P/2148239655/Blades-of-Khaine'),

    ('KT-033', 'Kill Team: Inquisitorial Agents', 'kill-team-inquisitorial-agents', Decimal('60.00'),
     'https://www.warhammer.com/en-US/shop/kill-team-inquisitorial-agents-2024',
     'B0DKNW2QNV',
     'https://www.miniaturemarket.com/kill-team-inquisitorial-agents-gw-103-38-2024.html',
     'https://www.nobleknight.com/P/2148075175/Inquisitorial-Agents-Kill-Team-2023-Edition'),
]


class Command(BaseCommand):
    """Seed 33 Kill Team products (KT-001 to KT-033) with retailer price rows."""

    help = 'Seed Kill Team products and their GW, Amazon, MM, and NK price rows.'

    def handle(self, *args, **options):
        """Run the seed."""
        try:
            kt_category = Category.objects.get(name='Kill Team')
        except Category.DoesNotExist:
            self.stdout.write(self.style.ERROR('Category "Kill Team" not found — create it in admin first.'))
            return

        retailers = {
            slug: Retailer.objects.get(slug=slug)
            for slug in ['games-workshop', 'amazon', 'miniature-market', 'noble-knight-games']
        }

        created_count = 0
        updated_count = 0

        for gw_sku, name, slug, msrp, gw_url, amazon_asin, mm_url, nk_base_url in PRODUCTS:
            product, created = Product.objects.update_or_create(
                gw_sku=gw_sku,
                defaults={
                    'name': name,
                    'slug': slug,
                    'msrp': msrp,
                    'gw_url': gw_url,
                    'image_url': '',
                    'category': kt_category,
                    'faction': None,
                    'is_active': True,
                    'batch_tag': 'kill-team',
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

            # GW — seed at MSRP
            CurrentPrice.objects.update_or_create(
                product=product,
                retailer=retailers['games-workshop'],
                defaults={
                    'price': msrp,
                    'url': gw_url,
                    'in_stock': True,
                    'not_available': False,
                },
            )

            # Amazon — placeholder with affiliate URL
            amazon_url = _amazon_url(amazon_asin)
            CurrentPrice.objects.update_or_create(
                product=product,
                retailer=retailers['amazon'],
                defaults={
                    'price': None,
                    'url': amazon_url,
                    'in_stock': False,
                    'not_available': False,
                },
            )

            # Miniature Market — only create row if URL exists
            if mm_url:
                CurrentPrice.objects.update_or_create(
                    product=product,
                    retailer=retailers['miniature-market'],
                    defaults={
                        'price': None,
                        'url': mm_url,
                        'in_stock': False,
                        'not_available': False,
                    },
                )

            # Noble Knight — only create row if URL exists
            nk_url = _nk_url(nk_base_url)
            if nk_url:
                CurrentPrice.objects.update_or_create(
                    product=product,
                    retailer=retailers['noble-knight-games'],
                    defaults={
                        'price': None,
                        'url': nk_url,
                        'in_stock': False,
                        'not_available': False,
                    },
                )

            self.stdout.write(f'  [{"new" if created else "upd"}] {gw_sku} — {name}')

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Created: {created_count}  Updated: {updated_count}'
        ))
