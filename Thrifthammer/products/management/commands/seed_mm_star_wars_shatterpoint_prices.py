"""
Management command: seed_mm_star_wars_shatterpoint_prices

Seeds Miniature Market CurrentPrice records for Star Wars: Shatterpoint
products.

51 of 53 products have a confirmed Miniature Market URL, matched by
cross-referencing Asmodee's own product code (embedded in our image
filenames, e.g. SWP21) against Miniature Market's own SKU codes (embedded
in their URLs, e.g. AMGSWP21), then confirmed by product name. SWS-001 (I
Am No Jedi Deluxe Duel Pack) has no listing anywhere (eBay, Amazon, or MM)
and is intentionally left out. SWS-045 (Dice Pack) uses MM's "SWP19" code,
which omits the "EN" language-variant suffix present in our own "SWP19EN"
code -- confirmed as the same physical product by the user.

Usage:
    python manage.py seed_mm_star_wars_shatterpoint_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

# (slug, listing_title, price, url, in_stock, not_available)
MM_PRICES = [
    ('star-wars-shatterpoint-fear-and-dead-men-squad-pack', 'Star Wars Shatterpoint: Fear & Dead Men Squad Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-fear-dead-men-squad-pack-amgswp21.html', False, False),
    ('star-wars-shatterpoint-delta-squad-form-up-squad-pack', 'Star Wars Shatterpoint: Delta Squad, Form Up Squad Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-delta-squad-form-up-squad-pack-amgswp62.html', False, False),
    ('star-wars-shatterpoint-all-the-way-squad-pack', 'Star Wars Shatterpoint: All the Way Squad Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-all-way-squad-pack-amgswp31.html', False, False),
    ('star-wars-shatterpoint-certified-guild-squad-pack', 'Star Wars Shatterpoint: Certified Guild Squad Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-certified-guild-squad-pack-amgswp24.html', False, False),
    ('star-wars-shatterpoint-deploy-the-garrison-squad-pack', 'Star Wars Shatterpoint: Deploy the Garrison Squad Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-deploy-garrison-squad-pack-amgswp51.html', False, False),
    ('star-wars-shatterpoint-make-the-impossible-possible-squad-pack', 'Star Wars Shatterpoint: Make the Impossible Possible Squad Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-make-impossible-possible-squad-pack-amgswp44.html', False, False),
    ('star-wars-shatterpoint-lead-by-example-squad-pack', 'Star Wars Shatterpoint: Lead by Example Squad Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-lead-example-squad-pack-amgswp11.html', False, False),
    ('star-wars-shatterpoint-fearless-and-inventive-squad-pack', 'Star Wars Shatterpoint: Fearless & Inventive Squad Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-fearless-inventive-squad-pack-amgswp22.html', False, False),
    ('star-wars-shatterpoint-stronger-than-fear-squad-pack', 'Star Wars Shatterpoint: Stronger Than Fear Squad Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-stronger-than-fear-squad-pack-amgswp29.html', False, False),
    ('star-wars-shatterpoint-first-contact-mission-pack', 'Star Wars Shatterpoint: First Contact Mission Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-first-contact-mission-pack-amgswp49.html', False, False),
    ('star-wars-shatterpoint-never-tell-me-the-odds-mission-pack', 'Star Wars Shatterpoint: Never Tell Me the Odds Mission Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-never-tell-me-odds-mission-pack-amgswp48.html', False, False),
    ('star-wars-shatterpoint-you-have-something-i-want-squad-pack', 'Star Wars Shatterpoint: You Have Something I Want Squad Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-you-have-something-i-want-squad-pack-amgswp26.html', False, False),
    ('star-wars-shatterpoint-sabotage-showdown', 'Star Wars Shatterpoint: Sabotage Showdown Mission Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-sabotage-showdown-mission-pack-amgswp45.html', False, False),
    ('star-wars-shatterpoint-this-is-rogue-one-squad-pack', 'Star Wars Shatterpoint: This is Rogue One Squad Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-this-is-rogue-one-squad-pack-amgswp52.html', False, False),
    ('star-wars-shatterpoint-we-dont-need-their-scum-unit-pack', 'Star Wars Shatterpoint: We Don\'t Need Their Scum Unit Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-we-dont-need-their-scum-unit-pack-amgswp25.html', False, False),
    ('star-wars-shatterpoint-this-is-the-way-squad-pack', 'Star Wars Shatterpoint: This Is the Way Squad Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-this-is-way-squad-pack-amgswp16.html', False, False),
    ('star-wars-shatterpoint-yub-nub-squad-pack', 'Star Wars Shatterpoint: Yub Nub Squad Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-yub-nub-squad-pack-amgswp39.html', False, False),
    ('star-wars-shatterpoint-i-am-no-jedi-duel-pack', 'Star Wars Shatterpoint: I Am No Jedi Duel Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-i-am-no-jedi-duel-pack-amgswp42.html', False, False),
    ('star-wars-shatterpoint-today-the-rebellion-dies-squad-pack', 'Star Wars Shatterpoint: Today the Rebellion Dies Squad Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-today-rebellion-dies-squad-pack-amgswp34.html', False, False),
    ('star-wars-shatterpoint-hello-there-general-obi-wan-kenobi-squad-pack', 'Star Wars Shatterpoint: Hello There Squad Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-hello-there-squad-pack-amgswp06.html', False, False),
    ('star-wars-shatterpoint-twice-the-pride-count-dooku-squad-pack', 'Star Wars Shatterpoint: Twice the Pride Squad Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-twice-the-pride-squad-pack-amgswp03.html', False, False),
    ('star-wars-shatterpoint-this-partys-over-mace-windu-squad-pack', 'Star Wars Shatterpoint: This Party\'s Over Squad Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-this-partys-over-squad-pack-amgswp08.html', False, False),
    ('star-wars-shatterpoint-witches-of-dathomir-mother-talzin-squad-pack', 'Star Wars Shatterpoint: Witches of Dathomir Squad Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-witches-of-dathomir-squad-pack-amgswp07.html', False, False),
    ('star-wars-shatterpoint-jedi-hunters', 'Star Wars Shatterpoint: Jedi Hunters Squad Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-jedi-hunters-squad-pack-amgswp12.html', False, False),
    ('star-wars-shatterpoint-we-are-brave-squad-pack', 'Star Wars Shatterpoint: We Are Brave Squad Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-we-are-brave-squad-pack-amgswp15.html', False, False),
    ('star-wars-shatterpoint-fistful-of-credits-cad-bane-squad-pack', 'Star Wars Shatterpoint: Fistful of Credits Squad Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-fistful-of-credits-squad-pack-amgswp09.html', False, False),
    ('star-wars-shatterpoint-you-cannot-run-duel-pack', 'Star Wars Shatterpoint: You Cannot Run Duel Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-you-cannot-run-duel-pack-amgswp30.html', False, False),
    ('star-wars-shatterpoint-plans-and-preparation-squad-pack', 'Star Wars Shatterpoint: Plans & Preparation Squad Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-plans-preparation-squad-pack-amgswp04.html', False, False),
    ('star-wars-shatterpoint-take-cover-terrain-pack', 'Star Wars Shatterpoint: Take Cover Terrain Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-take-cover-terrain-pack-amgswp17.html', False, False),
    ('star-wars-shatterpoint-secure-the-future-squad-pack', 'Star Wars Shatterpoint: Secure the Future Squad Pack', None, 'https://www.miniaturemarket.com/Star-Wars-Shatterpoint-Secure-the-Future-Squad-Pack/AMGSWP82', False, False),
    ('star-wars-shatterpoint-requesting-your-surrender-squad-pack', 'Star Wars Shatterpoint: Requesting Your Surrender Squad Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-requesting-your-surrender-squad-pack-amgswp37.html', False, False),
    ('star-wars-shatterpoint-wisdom-of-the-council-squad-pack', 'Star Wars Shatterpoint: Wisdom of the Council Squad Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-wisdom-council-squad-pack-amgswp50.html', False, False),
    ('star-wars-shatterpoint-real-quiet-like-squad-pack', 'Star Wars Shatterpoint: Real Quiet Like Squad Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-real-quiet-like-squad-pack-amgswp35.html', False, False),
    ('star-wars-shatterpoint-my-loyalty-my-life-squad-pack', 'Star Wars Shatterpoint: My Loyalty, My Life Squad Pack', None, 'https://www.miniaturemarket.com/Star-Wars-Shatterpoint-My-Loyalty-My-Life-Squad-Pack/AMGSWP83', False, False),
    ('star-wars-shatterpoint-terror-from-below-squad-pack', 'Star Wars Shatterpoint: Terror From Below Squad Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-terror-from-below-squad-pack-amgswp63.html', False, False),
    ('star-wars-shatterpoint-ee-chee-wa-maa-squad-pack', 'Star Wars Shatterpoint: Ee Chee Wa Maa! Squad Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-ee-chee-wa-maa-squad-pack-amgswp27.html', False, False),
    ('star-wars-shatterpoint-not-accepting-surrenders-squad-pack', 'Star Wars Shatterpoint: Not Accepting Surrenders Squad Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-not-accepting-surrenders-squad-pack-amgswp28.html', False, False),
    ('star-wars-shatterpoint-this-is-some-rescue-squad-pack', 'Star Wars Shatterpoint: This is Some Rescue! Squad Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-this-is-some-rescue-squad-pack-amgswp41.html', False, False),
    ('star-wars-shatterpoint-thats-good-business-squad-pack', 'Star Wars Shatterpoint: That\'s Good Business Squad Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-thats-good-business-squad-pack-amgswp10.html', False, False),
    ('star-wars-shatterpoint-strategic-positions', 'Star Wars Shatterpoint: Strategic Positions', None, 'https://www.miniaturemarket.com/Star-Wars-Shatterpoint-Strategic-Positions/AMGSWP72', False, False),
    ('star-wars-shatterpoint-maximum-firepower-squad-pack', 'Star Wars Shatterpoint: Maximum Firepower Squad Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-maximum-firepower-squad-pack-amgswp46.html', False, False),
    ('star-wars-shatterpoint-core-set', 'Star Wars Shatterpoint: Core Set', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-core-set-amgswp01en.html', False, False),
    ('star-wars-shatterpoint-good-soldiers-follow-orders-squad-pack', 'Star Wars Shatterpoint: Good Soldiers Follow Orders Squad Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-good-soldiers-follow-orders-squad-pack-amgswp36.html', False, False),
    ('star-wars-shatterpoint-outer-rim-outpost-terrain-pack', 'Star Wars Shatterpoint: Outer Rim Outpost Terrain Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-outer-rim-outpost-terrain-pack-amgswp60.html', False, False),
    ('star-wars-shatterpoint-measuring-tools', 'Star Wars Shatterpoint: Measurement Tools', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-measurement-tools-amgswp20.html', False, False),
    ('star-wars-shatterpoint-appetite-for-destruction-squad-pack', 'Star Wars Shatterpoint: Appetite for Destruction Squad Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-appetite-for-destruction-squad-pack-amgswp05.html', False, False),
    ('star-wars-shatterpoint-what-have-we-here-squad-pack', 'Star Wars Shatterpoint: What Have We Here Squad Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-what-have-we-here-squad-pack-amgswp47.html', False, False),
    ('star-wars-shatterpoint-maintenance-bay-terrain-pack', 'Star Wars Shatterpoint: Maintenance Bay Terrain Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-maintenance-bay-terrain-pack-amgswp18.html', False, False),
    ('star-wars-shatterpoint-dice-pack', 'Star Wars Shatterpoint: Dice Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-dice-pack-amgswp19.html', False, False),
    ('star-wars-shatterpoint-high-ground-terrain-pack', 'Star Wars Shatterpoint: High Ground Terrain Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-high-ground-terrain-pack-amgswp02.html', False, False),
    ('star-wars-shatterpoint-clone-force-99-squad-pack', 'Star Wars Shatterpoint: Clone Force 99 Squad Pack', None, 'https://www.miniaturemarket.com/star-wars-shatterpoint-clone-force-99-squad-pack-amgswp38.html', False, False),
]


class Command(BaseCommand):
    """Seed Miniature Market prices for Star Wars: Shatterpoint products (idempotent)."""

    help = 'Seeds Miniature Market CurrentPrice records for Star Wars: Shatterpoint products.'

    def handle(self, *args, **options):
        if not MM_PRICES:
            self.stdout.write(self.style.WARNING('MM_PRICES is empty -- nothing to seed.'))
            return

        retailer = Retailer.objects.get(slug='miniature-market')

        created = 0
        updated = 0

        for slug, listing_title, price, url, in_stock, not_available in MM_PRICES:
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
            f'Miniature Market prices: {created} created, {updated} updated.'
        ))
