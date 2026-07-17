"""
Management command: populate_gsi_creos_products

Creates the GSI Creos airbrush product line as a flat Faction
(category=Paint & Supplies, no parent_faction) — matches the Harder &
Steenbeck precedent structurally, but with no retailer row of any kind.

GSI Creos has no online store with pricing, so unlike Iwata/Gaahleri
there is no brand-website CurrentPrice row here, and no GW/NK/MM rows
either. Products are seeded with only name, image_url, and
ebay_search_name; msrp and gw_url are left blank (per explicit
instruction — the source Excel has no price data for this brand at
all, and the "Title_URL" column is intentionally not used).

Usage:
    python manage.py populate_gsi_creos_products
"""

from django.core.management.base import BaseCommand

from products.models import Category, Faction, Product

# (slug, gw_sku, name, image_url, ebay_search_name)
PRODUCTS = [
    ('procon-boy-fwa-platinum-02mm', 'GSI-001', 'Procon Boy Fwa Platinum 0.2mm', 'https://www.mr-hobby.com/uploads/products/01JN5TN7FYFA740YM1XNTT2P86.jpg', 'Procon Boy Fwa Platinum 0.2mm'),
    ('procon-boy-lsa-single-action-04', 'GSI-002', 'Procon Boy Lsa Single Action 04', 'https://www.mr-hobby.com/uploads/products/01JWG3TXPGJTPD1AKZPTQ3XKBZ.png', 'Procon Boy Lsa Single Action 04'),
    ('procon-boy-lwa-h-triger-type-04', 'GSI-003', 'Procon Boy Lwa-H Triger Type 04', 'https://www.mr-hobby.com/uploads/products/01JWG37KJJRY5ZHQBZQFK62P2F.png', 'Procon Boy Lwa-H Triger Type 04'),
    ('mrairbrush-supreme', 'GSI-004', 'Mr.Airbrush Supreme', 'https://www.mr-hobby.com/uploads/products/01JN5TB5MVW8ZTYTK94XFJS6SJ.jpg', 'Mr.Airbrush Supreme'),
    ('procon-boy-lwa-triger-type', 'GSI-005', 'Procon Boy Lwa Triger Type', 'https://www.mr-hobby.com/uploads/products/01JN5TDJ01HSH1J4HAVDVGW1KA.jpg', 'Procon Boy Lwa Triger Type'),
    ('procon-boy-wa-platinum-ver2-03mm', 'GSI-006', 'Procon Boy Wa Platinum Ver.2 0.3mm', 'https://www.mr-hobby.com/uploads/products/01JN5TF03H8Z40GDYQJH7TQ74K.jpg', 'Procon Boy Wa Platinum Ver.2 0.3mm'),
    ('mr-procon-boy-wa-03mm-trigger', 'GSI-007', 'Mr. Procon Boy Wa 0.3mm Trigger', 'https://www.mr-hobby.com/uploads/products/01JN5TJQWNYHMJRNP5R16TP6SS.jpg', 'Mr. Procon Boy Wa 0.3mm Trigger'),
    ('mrprocon-double-action-3mm', 'GSI-008', 'Mr.Procon Double Action 3mm', 'https://www.mr-hobby.com/uploads/products/01JN5TKXW9648KYBFVBD0F9ZDE.jpg', 'Mr.Procon Double Action 3mm'),
    ('procon-boy-sq', 'GSI-009', 'Procon Boy Sq', 'https://www.mr-hobby.com/uploads/products/01JN5T9MYQYE82A0TRHGMBXV3B.jpg', 'Procon Boy Sq'),
    ('procon-boy-fwa', 'GSI-010', 'Procon Boy Fwa', 'https://www.mr-hobby.com/uploads/products/01JN5TQY4AV6ATC6B0VZKP90DH.jpg', 'Procon Boy Fwa'),
    ('mrprocon-boy-lwa-05mm-airbrush', 'GSI-011', 'Mr.Procon Boy Lwa 0.5mm Airbrush', 'https://www.mr-hobby.com/uploads/products/01JN5V5YQ1GEB18CJ40F1BD99W.jpg', 'Mr.Procon Boy Lwa 0.5mm Airbrush'),
    ('procon-boy-single-action', 'GSI-012', 'Procon Boy Single Action', 'https://www.mr-hobby.com/uploads/products/01JN5TX3PWX3E8K6QH43AQ8JFV.jpg', 'Procon Boy Single Action'),
    ('procon-boy-sq-light-aluminiun-black', 'GSI-013', 'Procon Boy Sq Light Aluminiun Black', 'https://www.mr-hobby.com/uploads/products/01JN5V3RG257FAH2KNAH2MN3KJ.png', 'Procon Boy Sq Light Aluminiun Black'),
]


class Command(BaseCommand):
    """Populate the GSI Creos airbrush product line (idempotent)."""

    help = 'Populates GSI Creos airbrush products (GSI-001 to GSI-013). No retailer/price rows.'

    def handle(self, *args, **options):
        category, _ = Category.objects.get_or_create(
            slug='paint-supplies',
            defaults={'name': 'Paint & Supplies'},
        )

        gsi_faction, _ = Faction.objects.get_or_create(
            slug='gsi-creos',
            defaults={'name': 'GSI Creos', 'category': category},
        )

        products_created = 0
        products_updated = 0

        for slug, gw_sku, name, image_url, ebay_search_name in PRODUCTS:
            product, created = Product.objects.update_or_create(
                slug=slug,
                defaults={
                    'gw_sku': gw_sku,
                    'name': name,
                    'category': category,
                    'faction': gsi_faction,
                    'msrp': None,
                    'image_url': image_url,
                    'gw_url': '',
                    'ebay_search_name': ebay_search_name,
                    'batch_tag': 'gsi-creos',
                    'is_active': True,
                },
            )
            if created:
                products_created += 1
            else:
                products_updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'Products: {products_created} created, {products_updated} updated.'
        ))
