"""
Management command: seed_nk_malifaux_prices

Seeds Noble Knight CurrentPrice records for Malifaux products.

45 of 51 products have a confirmed Noble Knight URL (40 matched by product
code against the Noble Knight Excel scrape, 5 more found directly on NK's
site by hand). The remaining 6 products have no NK listing and are
intentionally left out, per the "blank row = no entry" rule.

Affiliate tag ?awid=1576 appended to all NK URLs.

Usage:
    python manage.py seed_nk_malifaux_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_NK = 'https://www.nobleknight.com'
_AFF = '?awid=1576'

# (slug, listing_title, price, url, in_stock, not_available)
NK_PRICES = [
    ('malifaux-fourth-edition-two-player-starter', 'Malifaux 4th Edition - Two Player Starter Set', None, f'{_NK}/P/2148369531/Malifaux-4th-Edition---Two-Player-Starter-Set{_AFF}', False, False),
    ('malifaux-fourth-edition-gaining-grounds-season-zero', 'Gaining Grounds 4th Edition - Season Zero', None, f'{_NK}/P/2148339877/Gaining-Grounds-4th-Edition---Season-Zero{_AFF}', False, False),
    ('malifaux-fourth-edition-rules-manual', 'Malifaux 4th Edition - Rules Manual', None, f'{_NK}/P/2148339873/Malifaux-4th-Edition---Rules-Manual{_AFF}', False, False),
    ('malifaux-fourth-edition-pandora-despairs-desire', "Pandora - Despair's Desire", None, f'{_NK}/P/2148331827/Pandora---Despairs-Desire{_AFF}', False, False),
    ('malifaux-fourth-edition-sandeep-desai-the-quiet-flame', 'Sandeep Desai, the Quiet Flame', None, f'{_NK}/P/2148355872/Sandeep-Desai-the-Quiet-Flame{_AFF}', False, False),
    ('malifaux-fourth-edition-yan-lo-the-spirit-walker', 'Yan Lo - The Spirit Walker', None, f'{_NK}/P/2148359991/Yan-Lo---The-Spirit-Walker{_AFF}', False, False),
    ('malifaux-fourth-edition-wong-the-wonderful', 'Wong, the Wonderful', None, f'{_NK}/P/2148355869/Wong-the-Wonderful{_AFF}', False, False),
    ('malifaux-fourth-edition-the-dreamer-fast-asleep', 'Dreamer, The - Fast Asleep', None, f'{_NK}/P/2148331825/Dreamer-The---Fast-Asleep{_AFF}', False, False),
    ('malifaux-fourth-edition-anya-lycarayen-the-resolute', 'Anya Lycarayen, the Resolute', None, f'{_NK}/P/2148355915/Anya-Lycarayen-the-Resolute{_AFF}', False, False),
    ('malifaux-fourth-edition-viktoria-chambers-ashes-and-blood', 'Viktoria Chambers, Ashes and Blood', None, f'{_NK}/P/2148339882/Viktoria-Chambers-Ashes-and-Blood{_AFF}', False, False),
    ('malifaux-fourth-edition-the-clampetts-fisherfolk', 'Clampetts, The - Fisherfolk', None, f'{_NK}/P/2148339887/Clampetts-The---Fisherfolk{_AFF}', False, False),
    ('malifaux-fourth-edition-dr-mcmourning-malpractitioner', 'Dr. McMourning, Malpractitioner', None, f'{_NK}/P/2148432009/Dr-McMourning-Malpractitioner{_AFF}', False, False),
    ('malifaux-fourth-edition-seamus-aka-sebastian-baker', 'Seamus, aka Sebastian Baker', None, f'{_NK}/P/2148369609/Seamus-aka-Sebastian-Baker{_AFF}', False, False),
    ('malifaux-fourth-edition-jack-daw-spirit-of-betrayal', 'Jack Daw, Spirit of Betrayal', None, f'{_NK}/P/2148331816/Jack-Daw-Spirit-of-Betrayal{_AFF}', False, False),
    ('malifaux-fourth-edition-nellie-voice-of-disorder', 'Nellie Cochrane, Voice of Disorder', None, f'{_NK}/P/2148369594/Nellie-Cochrane-Voice-of-Disorder{_AFF}', False, False),
    ('malifaux-fourth-edition-lucius-mattheson-in-plain-sight', 'Lucius Mattheson, In Plain Sight', None, f'{_NK}/P/2148369536/Lucius-Mattheson-In-Plain-Sight{_AFF}', False, False),
    ('malifaux-fourth-edition-guild-faction-pack', 'Guild Faction Pack (4th Edition)', None, f'{_NK}/P/2148432485/Guild-Faction-Pack-4th-Edition{_AFF}', False, False),
    ('malifaux-fourth-edition-arcanist-faction-pack', 'Arcanist Faction Pack (4th Edition)', None, f'{_NK}/P/2148431210/Arcanist-Faction-Pack-4th-Edition{_AFF}', False, False),
    ('malifaux-fourth-edition-resurrectionist-faction-pack', 'Resurrectionist Faction Pack (4th Edition)', None, f'{_NK}/P/2148431212/Resurrectionist-Faction-Pack-4th-Edition{_AFF}', False, False),
    ('malifaux-fourth-edition-neverborn-faction-pack', 'Neverborn Faction Pack (4th Edition)', None, f'{_NK}/P/2148431194/Neverborn-Faction-Pack-4th-Edition{_AFF}', False, False),
    ('malifaux-fourth-edition-ten-thunders-faction-pack', 'Ten Thunders Faction Pack (4th Edition)', None, f'{_NK}/P/2148431207/Ten-Thunders-Faction-Pack-4th-Edition{_AFF}', False, False),
    ('malifaux-fourth-edition-outcast-faction-pack', 'Outcast Faction Pack (4th Edition)', None, f'{_NK}/P/2148431217/Outcast-Faction-Pack-4th-Edition{_AFF}', False, False),
    ('malifaux-fourth-edition-bayou-faction-pack', 'Bayou Faction Pack (4th Edition)', None, f'{_NK}/P/2148431202/Bayou-Faction-Pack-4th-Edition{_AFF}', False, False),
    ('malifaux-fourth-edition-explorers-society-faction-pack', "Explorer's Society Faction Pack (4th Edition)", None, f'{_NK}/P/2148431198/Explorers-Society-Faction-Pack-4th-Edition{_AFF}', False, False),
    ('malifaux-fourth-edition-guild-faction-book', 'Guild Faction Book (4th Edition)', None, f'{_NK}/P/2148431128/Guild-Faction-Book-4th-Edition{_AFF}', False, False),
    ('malifaux-fourth-edition-resurrectionist-faction-book', 'Resurrectionist Faction Book (4th Edition)', None, f'{_NK}/P/2148431125/Resurrectionist-Faction-Book-4th-Edition{_AFF}', False, False),
    ('malifaux-fourth-edition-arcanist-faction-book', 'Arcanist Faction Book (4th Edition)', None, f'{_NK}/P/2148431122/Arcanist-Faction-Book-4th-Edition{_AFF}', False, False),
    ('malifaux-fourth-edition-neverborn-faction-book', 'Neverborn Faction Book (4th Edition)', None, f'{_NK}/P/2148431106/Neverborn-Faction-Book-4th-Edition{_AFF}', False, False),
    ('malifaux-fourth-edition-ten-thunders-faction-book', 'Ten Thunders Faction Book (4th Edition)', None, f'{_NK}/P/2148431114/Ten-Thunders-Faction-Book-4th-Edition{_AFF}', False, False),
    ('malifaux-fourth-edition-outcast-faction-book', 'Outcast Faction Book (4th Edition)', None, f'{_NK}/P/2148431113/Outcast-Faction-Book-4th-Edition{_AFF}', False, False),
    ('malifaux-fourth-edition-bayou-faction-book', 'Bayou Faction Book (4th Edition)', None, f'{_NK}/P/2148431119/Bayou-Faction-Book-4th-Edition{_AFF}', False, False),
    ('malifaux-fourth-edition-explorers-society-faction-book', "Explorer's Society Faction Book (4th Edition)", None, f'{_NK}/P/2148431117/Explorers-Society-Faction-Book-4th-Edition{_AFF}', False, False),
    ('malifaux-fourth-edition-tara-voidcaller', 'Tara, Voidcaller', None, f'{_NK}/P/2148432000/Tara-Voidcaller{_AFF}', False, False),
    ('malifaux-fourth-edition-nexus-heart-of-the-hive', 'Nexus, Heart of the Hive', None, f'{_NK}/P/2148403627/Nexus-Heart-of-the-Hive{_AFF}', False, False),
    ('malifaux-fourth-edition-colette-du-bois-star-of-the-show', 'Colette Du Bois - Star of the Show', None, f'{_NK}/P/2148331820/Colette-Du-Bois---Star-of-the-Show{_AFF}', False, False),
    ('malifaux-fourth-edition-jakob-lynch-wild-card', 'Jakob Lynch, Wild Card', None, f'{_NK}/P/2148432090/Jakon-Lynch-Wild-Card{_AFF}', False, False),
    ('malifaux-fourth-edition-tara-timeless', 'Tara, Timeless', None, f'{_NK}/P/2148426114/Tara-Timeless{_AFF}', False, False),
    ('malifaux-fourth-edition-sonnia-criid-unrelenting', 'Sonnia Criid, Unrelenting', None, f'{_NK}/P/2148432507/Sonnia-Criid-Unrelenting{_AFF}', False, False),
    ('malifaux-fourth-edition-sandeep-desai-font-of-magic', 'Sandeep Desai, Font of Magic', None, f'{_NK}/P/2148426094/Sandeep-Desai-Font-of-Magic{_AFF}', False, False),
    ('malifaux-fourth-edition-dashel-barker-the-old-guard', 'Dashel Barker, The Old Guard', None, f'{_NK}/P/2148459648/Dashel-Barker-The-Old-Guard{_AFF}', False, False),
    ('malifaux-fourth-edition-viktoria-chambers-twin-blades', 'Viktoria Chambers, Twin Blades', None, f'{_NK}/P/2148459607/Viktoria-Chambers-Twin-Blades{_AFF}', False, False),
    ('malifaux-fourth-edition-intrepid-fate', 'Intrepid Fate (2025 Edition)', None, f'{_NK}/P/2148459676/Intrepid-Fate-2025-Edition{_AFF}', False, False),
    ('malifaux-fourth-edition-the-clampetts-bally-hoo-bucket', 'Clampetts, The - Bally-Hoo Bucket', None, f'{_NK}/P/2148459678/Clampetts-The---Bally-Hoo-Bucket{_AFF}', False, False),
    ('malifaux-fourth-edition-carrion-fate', 'Carrion Fate (2025 Edition)', None, f'{_NK}/P/2148459633/Carrion-Fate-2025-Edition{_AFF}', False, False),
    ('malifaux-fourth-edition-arcane-fate', 'Arcane Fate (2025 Edition)', None, f'{_NK}/P/2148459661/Arcane-Fate-2025-Edition{_AFF}', False, False),
]


class Command(BaseCommand):
    """Seed Noble Knight prices for Malifaux products (idempotent)."""

    help = 'Seeds Noble Knight CurrentPrice records for Malifaux products.'

    def handle(self, *args, **options):
        if not NK_PRICES:
            self.stdout.write(self.style.WARNING('NK_PRICES is empty -- nothing to seed.'))
            return

        retailer = Retailer.objects.get(slug='noble-knight-games')

        created = 0
        updated = 0

        for slug, listing_title, price, url, in_stock, not_available in NK_PRICES:
            try:
                product = Product.objects.get(slug=slug)
            except Product.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Product not found for slug: {slug}'))
                continue

            _, price_created = CurrentPrice.objects.update_or_create(
                product=product,
                retailer=retailer,
                create_defaults={
                    'price': price,
                    'in_stock': in_stock,
                },
                defaults={
                    'url': url,
                    'listing_title': listing_title,
                    'not_available': not_available,
                },
            )
            if price_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'Noble Knight prices: {created} created, {updated} updated.'
        ))
