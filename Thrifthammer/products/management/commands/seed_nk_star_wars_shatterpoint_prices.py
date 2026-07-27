"""
Management command: seed_nk_star_wars_shatterpoint_prices

Seeds Noble Knight CurrentPrice records for Star Wars: Shatterpoint
products.

51 of 52 products have a confirmed Noble Knight URL, matched by strict
keyword-overlap on product name (Noble Knight's sheet has no Asmodee
product codes, unlike Miniature Market's). SWS-001 (I Am No Jedi Deluxe
Duel Pack) has no listing anywhere (eBay, Amazon, or MM) and is
intentionally left out. SWS-023 uses NK's own listing title "This Party's
Over Squad Pack" (NK's title omits "Mace Windu") -- confirmed as the same
product by the user.

Affiliate tag ?awid=1576 appended to all NK URLs.

Usage:
    python manage.py seed_nk_star_wars_shatterpoint_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_NK = 'https://www.nobleknight.com'
_AFF = '?awid=1576'

# (slug, listing_title, price, url, in_stock, not_available)
NK_PRICES = [
    ('star-wars-shatterpoint-fear-and-dead-men-squad-pack', 'Fear and Dead Men Squad Pack', None, f'{_NK}/P/2148112645/Fear-and-Dead-Men-Squad-Pack{_AFF}', False, False),
    ('star-wars-shatterpoint-delta-squad-form-up-squad-pack', 'Delta Squad, Form Up Squad Pack', None, f'{_NK}/P/2148324816/Delta-Squad-Form-Up-Squad-Pack{_AFF}', False, False),
    ('star-wars-shatterpoint-all-the-way-squad-pack', 'All the Way Squad Pack', None, f'{_NK}/P/2148278696/All-the-Way-Squad-Pack{_AFF}', False, False),
    ('star-wars-shatterpoint-certified-guild-squad-pack', 'Certified Guild Squad Pack', None, f'{_NK}/P/2148122190/Certified-Guild-Squad-Pack{_AFF}', False, False),
    ('star-wars-shatterpoint-deploy-the-garrison-squad-pack', 'Deploy the Garrison Squad Pack', None, f'{_NK}/P/2148278697/Deploy-the-Garrison-Squad-Pack{_AFF}', False, False),
    ('star-wars-shatterpoint-make-the-impossible-possible-squad-pack', 'Make the Impossible Possible Squad Pack', None, f'{_NK}/P/2148175919/Make-the-Impossible-Possible-Squad-Pack{_AFF}', False, False),
    ('star-wars-shatterpoint-lead-by-example-squad-pack', 'Lead by Example Squad Pack', None, f'{_NK}/P/2148112656/Lead-by-Example-Squad-Pack{_AFF}', False, False),
    ('star-wars-shatterpoint-fearless-and-inventive-squad-pack', 'Fearless and Inventive Squad Pack', None, f'{_NK}/P/2148112647/Fearless-and-Inventive-Squad-Pack{_AFF}', False, False),
    ('star-wars-shatterpoint-stronger-than-fear-squad-pack', 'Stronger than Fear Squad Pack', None, f'{_NK}/P/2148175934/Stronger-than-Fear-Squad-Pack{_AFF}', False, False),
    ('star-wars-shatterpoint-first-contact-mission-pack', 'First Contact Mission Pack', None, f'{_NK}/P/2148286599/First-Contact-Mission-Pack{_AFF}', False, False),
    ('star-wars-shatterpoint-never-tell-me-the-odds-mission-pack', 'Never Tell Me the Odds Mission Pack', None, f'{_NK}/P/2148142336/Never-Tell-Me-the-Odds-Mission-Pack{_AFF}', False, False),
    ('star-wars-shatterpoint-you-have-something-i-want-squad-pack', 'You Have Something I Want Squad Pack', None, f'{_NK}/P/2148122192/You-Have-Something-I-Want-Squad-Pack{_AFF}', False, False),
    ('star-wars-shatterpoint-sabotage-showdown', 'Sabotage Showdown Mission Pack', None, f'{_NK}/P/2148090227/Sabotage-Showdown-Mission-Pack{_AFF}', False, False),
    ('star-wars-shatterpoint-this-is-rogue-one-squad-pack', 'This is Rogue One Squad Pack', None, f'{_NK}/P/2148324800/This-is-Rogue-One-Squad-Pack{_AFF}', False, False),
    ('star-wars-shatterpoint-we-dont-need-their-scum-unit-pack', 'We Don\'t Need Their Scum Unit Pack', None, f'{_NK}/P/2148198748/We-Dont-Need-Their-Scum-Unit-Pack{_AFF}', False, False),
    ('star-wars-shatterpoint-this-is-the-way-squad-pack', 'This is the Way Squad Pack', None, f'{_NK}/P/2148198752/This-is-the-Way-Squad-Pack{_AFF}', False, False),
    ('star-wars-shatterpoint-yub-nub-squad-pack', 'Yub Nub Squad Pack', None, f'{_NK}/P/2148112667/Yub-Nub-Squad-Pack{_AFF}', False, False),
    ('star-wars-shatterpoint-i-am-no-jedi-duel-pack', 'I Am No Jedi Duel Pack', None, f'{_NK}/P/2148341973/I-Am-No-Jedi-Duel-Pack{_AFF}', False, False),
    ('star-wars-shatterpoint-today-the-rebellion-dies-squad-pack', 'Today the Rebellion Dies Squad Pack', None, f'{_NK}/P/2148144657/Today-the-Rebellion-Dies-Squad-Pack{_AFF}', False, False),
    ('star-wars-shatterpoint-hello-there-general-obi-wan-kenobi-squad-pack', 'Hello There - General Obi-Wan Kenobi Squad Pack', None, f'{_NK}/P/2148043267/Hello-There---General-Obi-Wan-Kenobi-Squad-Pack{_AFF}', False, False),
    ('star-wars-shatterpoint-twice-the-pride-count-dooku-squad-pack', 'Twice the Pride - Count Dooku Squad Pack', None, f'{_NK}/P/2148043269/Twice-the-Pride---Count-Dooku-Squad-Pack{_AFF}', False, False),
    ('star-wars-shatterpoint-this-partys-over-mace-windu-squad-pack', 'This Party\'s Over Squad Pack', None, f'{_NK}/P/2148071179/This-Partys-Over-Squad-Pack{_AFF}', False, False),
    ('star-wars-shatterpoint-witches-of-dathomir-mother-talzin-squad-pack', 'Witches of Dathomir - Mother Talzin Squad Pack', None, f'{_NK}/P/2148071181/Witches-of-Dathomir---Mother-Talzin-Squad-Pack{_AFF}', False, False),
    ('star-wars-shatterpoint-jedi-hunters', 'Jedi Hunters Squad Pack', None, f'{_NK}/P/2148056376/Jedi-Hunters-Squad-Pack{_AFF}', False, False),
    ('star-wars-shatterpoint-we-are-brave-squad-pack', 'We are Brave Squad Pack', None, f'{_NK}/P/2148077058/We-are-Brave-Squad-Pack{_AFF}', False, False),
    ('star-wars-shatterpoint-fistful-of-credits-cad-bane-squad-pack', 'Fistful of Credits - Cad Bane Squad Pack', None, f'{_NK}/P/2148077055/Fistful-of-Credits---Cad-Bane-Squad-Pack{_AFF}', False, False),
    ('star-wars-shatterpoint-you-cannot-run-duel-pack', 'You Cannot Run Duel Pack', None, f'{_NK}/P/2148056379/You-Cannot-Run-Duel-Pack{_AFF}', False, False),
    ('star-wars-shatterpoint-plans-and-preparation-squad-pack', 'Plans and Preparation Squad Pack', None, f'{_NK}/P/2148043271/Plans-and-Preparation-Squad-Pack{_AFF}', False, False),
    ('star-wars-shatterpoint-take-cover-terrain-pack', 'Terrain Pack - Take Cover', None, f'{_NK}/P/2148043277/Terrain-Pack---Take-Cover{_AFF}', False, False),
    ('star-wars-shatterpoint-secure-the-future-squad-pack', 'Secure the Future Squad Pack', None, f'{_NK}/P/2148454839/Secure-the-Future-Squad-Pack{_AFF}', False, False),
    ('star-wars-shatterpoint-requesting-your-surrender-squad-pack', 'Requesting Your Surrender Squad Pack', None, f'{_NK}/P/2148258913/Requesting-Your-Surrender-Squad-Pack{_AFF}', False, False),
    ('star-wars-shatterpoint-wisdom-of-the-council-squad-pack', 'Wisdom of the Council Squad Pack', None, f'{_NK}/P/2148250698/Wisdom-of-the-Council-Squad-Pack{_AFF}', False, False),
    ('star-wars-shatterpoint-real-quiet-like-squad-pack', 'Real Quiet Like Squad Pack', None, f'{_NK}/P/2148144635/Real-Quiet-Like-Squad-Pack{_AFF}', False, False),
    ('star-wars-shatterpoint-my-loyalty-my-life-squad-pack', 'My Loyalty, My Life Squad Pack', None, f'{_NK}/P/2148454841/My-Loyalty-My-Life-Squad-Pack{_AFF}', False, False),
    ('star-wars-shatterpoint-terror-from-below-squad-pack', 'Terror From Below Squad Pack', None, f'{_NK}/P/2148324804/Terror-From-Below-Squad-Pack{_AFF}', False, False),
    ('star-wars-shatterpoint-ee-chee-wa-maa-squad-pack', 'Ee Chee Wa Maa! Squad Pack', None, f'{_NK}/P/2148112674/Ee-Chee-Wa-Maa-Squad-Pack{_AFF}', False, False),
    ('star-wars-shatterpoint-not-accepting-surrenders-squad-pack', 'Not Accepting Surrenders Squad Pack', None, f'{_NK}/P/2148175379/Not-Accepting-Surrenders-Squad-Pack{_AFF}', False, False),
    ('star-wars-shatterpoint-this-is-some-rescue-squad-pack', 'This is Some Rescue! Squad Pack', None, f'{_NK}/P/2148175383/This-is-Some-Rescue-Squad-Pack{_AFF}', False, False),
    ('star-wars-shatterpoint-thats-good-business-squad-pack', 'That\'s Good Business Squad Pack', None, f'{_NK}/P/2148122172/Thats-Good-Business-Squad-Pack{_AFF}', False, False),
    ('star-wars-shatterpoint-strategic-positions', 'Strategic Positions Mission Pack', None, f'{_NK}/P/2148421593/Strategic-Positions-Mission-Pack{_AFF}', False, False),
    ('star-wars-shatterpoint-maximum-firepower-squad-pack', 'Maximum Firepower Squad Pack', None, f'{_NK}/P/2148198755/Maximum-Firepower-Squad-Pack{_AFF}', False, False),
    ('star-wars-shatterpoint-core-set', 'Shatterpoint Core Set', None, f'{_NK}/P/2148043264/Shatterpoint-Core-Set{_AFF}', False, False),
    ('star-wars-shatterpoint-dice-pack', 'Shatterpoint Dice Pack (14)', None, f'{_NK}/P/2148055930/Shatterpoint-Dice-Pack-14{_AFF}', False, False),
    ('star-wars-shatterpoint-good-soldiers-follow-orders-squad-pack', 'Good Soldiers Follow Orders Squad Pack', None, f'{_NK}/P/2148195677/Good-Soldiers-Follow-Orders-Squad-Pack{_AFF}', False, False),
    ('star-wars-shatterpoint-outer-rim-outpost-terrain-pack', 'Terrain Pack - Outer Rim Outpost', None, f'{_NK}/P/2148324803/Terrain-Pack---Outer-Rim-Outpost{_AFF}', False, False),
    ('star-wars-shatterpoint-measuring-tools', 'Shatterpoint Measuring Tools', None, f'{_NK}/P/2148055932/Shatterpoint-Measuring-Tools{_AFF}', False, False),
    ('star-wars-shatterpoint-appetite-for-destruction-squad-pack', 'Appetite for Destruction Squad Pack', None, f'{_NK}/P/2148043273/Appetite-for-Destruction-Squad-Pack{_AFF}', False, False),
    ('star-wars-shatterpoint-what-have-we-here-squad-pack', 'What Have We Here Squad Pack', None, f'{_NK}/P/2148198757/What-Have-We-Here-Squad-Pack{_AFF}', False, False),
    ('star-wars-shatterpoint-maintenance-bay-terrain-pack', 'Terrain Pack - Maintenance Bay', None, f'{_NK}/P/2148175406/Terrain-Pack---Maintenance-Bay{_AFF}', False, False),
    ('star-wars-shatterpoint-high-ground-terrain-pack', 'Terrain Pack - High Ground', None, f'{_NK}/P/2148043275/Terrain-Pack---High-Ground{_AFF}', False, False),
    ('star-wars-shatterpoint-clone-force-99-squad-pack', 'Clone Force 99 Squad Pack', None, f'{_NK}/P/2148122188/Clone-Force-99-Squad-Pack{_AFF}', False, False),
]


class Command(BaseCommand):
    """Seed Noble Knight prices for Star Wars: Shatterpoint products (idempotent)."""

    help = 'Seeds Noble Knight CurrentPrice records for Star Wars: Shatterpoint products.'

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
