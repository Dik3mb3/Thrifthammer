"""
Management command: seed_nk_star_wars_legion_prices

Seeds Noble Knight CurrentPrice records for Star Wars: Legion products.

106 of 112 products have a confirmed Noble Knight URL (49 found via the
Noble Knight Excel scrape and cross-checked by title/price, the rest found
directly on NK's site by hand). The remaining 6 products have no NK listing
and are intentionally left out, per the "blank row = no entry" rule.

Several products intentionally share the same NK listing as a sibling
product (e.g. SWL-005/SWL-057 both point at NK's single "Upgrades Card
Pack" listing; SWL-021/SWL-092 both point at "Fifth Brother and Seventh
Sister Operative Expansion"; SWL-032/SWL-110 both point at "B2 Super Battle
Droids") -- confirmed directly by the user, not an error.

Affiliate tag ?awid=1576 appended to all NK URLs.

Usage:
    python manage.py seed_nk_star_wars_legion_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_NK = 'https://www.nobleknight.com'
_AFF = '?awid=1576'

# (slug, listing_title, price, url, in_stock, not_available)
NK_PRICES = [
    ('star-wars-legion-mandalorian-special-edition-army-box', 'Mandalorian Special Edition Army Box', None, f'{_NK}/P/2148468322/Mandalorian-Special-Edition-Army-Box{_AFF}', False, False),
    ('star-wars-legion-mandalorian-leaders', 'Mandalorian Leaders', None, f'{_NK}/P/2148468321/Mandalorian-Leaders{_AFF}', False, False),
    ('star-wars-legion-galactic-republic-starter-set', 'Galactic Republic Starter Set', None, f'{_NK}/P/2148355842/Galactic-Republic-Starter-Set{_AFF}', False, False),
    ('star-wars-legion-customizable-jedi-general-and-knight', 'Customizable Jedi General and Knight', None, f'{_NK}/P/2148360322/Customizable-Jedi-General-and-Knight{_AFF}', False, False),
    ('star-wars-legion-upgrades-card-pack', 'Upgrades Card Pack', None, f'{_NK}/P/2148347199/Upgrades-Card-Pack{_AFF}', False, False),
    ('star-wars-legion-galactic-empire-starter-set', 'Galactic Empire Starter Set', None, f'{_NK}/P/2148347500/Galactic-Empire-Starter-Set{_AFF}', False, False),
    ('star-wars-legion-general-grievous-tsmeu-6-wheel-bike', 'General Grievious\' TSMEU-6 Wheel Bike', None, f'{_NK}/P/2148360328/General-Grievious-TSMEU-6-Wheel-Bike{_AFF}', False, False),
    ('star-wars-legion-separatist-alliance-starter-set', 'Separatist Alliance Starter Set', None, f'{_NK}/P/2148355845/Separatist-Alliance-Starter-Set{_AFF}', False, False),
    ('star-wars-legion-empire-card-pack', 'Galactic Empire Unit Card Pack', None, f'{_NK}/P/2148347528/Galactic-Empire-Unit-Card-Pack{_AFF}', False, False),
    ('star-wars-legion-customizable-imperial-officer-agent', 'Customizable Imperial Officer & Agent', None, f'{_NK}/P/2148351990/Customizable-Imperial-Officer-and-Agent{_AFF}', False, False),
    ('star-wars-legion-customizable-super-tactical-command-droid', 'Customizable Super Tactical Command Droid', None, f'{_NK}/P/2148360323/Customizable-Super-Tactical-Command-Droid{_AFF}', False, False),
    ('star-wars-legion-commander-padawan-ahsoka-tano', 'Commander & Padawan Ahsoka Tano', None, f'{_NK}/P/2148291787/Commander-and-Padawan-Ahsoka-Tano{_AFF}', False, False),
    ('star-wars-legion-arf-troopers', 'ARF Troopers Unit Expansion', None, f'{_NK}/P/2148258898/ARF-Troopers-Unit-Expansion{_AFF}', False, False),
    ('star-wars-legion-bad-batch-operative-expansion', 'Bad Batch Operative Expansion', None, f'{_NK}/P/2148166577/Bad-Batch-Operative-Expansion{_AFF}', False, False),
    ('star-wars-legion-galactic-empire-command-card-pack', 'Galactic Empire Command Card Pack', None, f'{_NK}/P/2148347525/Galactic-Empire-Command-Card-Pack{_AFF}', False, False),
    ('star-wars-legion-imperial-high-command', 'Imperial High Command', None, f'{_NK}/P/2148424750/Imperial-High-Command{_AFF}', False, False),
    ('star-wars-legion-separatist-alliance-card-pack', 'Separatist Alliance Unit Card Pack', None, f'{_NK}/P/2148347534/Separatist-Alliance-Unit-Card-Pack{_AFF}', False, False),
    ('star-wars-legion-galactic-republic-command-card-pack', 'Galactic Republic Command Card Pack', None, f'{_NK}/P/2148347522/Galactic-Republic-Command-Card-Pack{_AFF}', False, False),
    ('star-wars-legion-mercenary-card-pack', 'Mercenary Card Pack', None, f'{_NK}/P/2148347314/Mercenary-Card-Pack{_AFF}', False, False),
    ('star-wars-legion-fifth-brother-and-seventh-sister-operative-expansion', 'Fifth Brother and Seventh Sister Operative Expansion', None, f'{_NK}/P/2148121465/Fifth-Brother-and-Seventh-Sister-Operative-Expansion{_AFF}', False, False),
    ('star-wars-legion-mandalorian-warriors', 'Mandalorian Warriors', None, f'{_NK}/P/2148473515/Mandalorian-Warriors{_AFF}', False, False),
    ('star-wars-legion-leaders-of-the-shadow-collective', 'Leaders of the Shadow Collective', None, f'{_NK}/P/2148468294/Leaders-of-the-Shadow-Collective{_AFF}', False, False),
    ('star-wars-legion-mandalorian-super-commandos', 'Mandalorian Super Commandos', None, f'{_NK}/P/2148468325/Mandalorian-Super-Commandos{_AFF}', False, False),
    ('star-wars-legion-upgrades-card-pack-2', 'Upgrade Card Pack 2', None, f'{_NK}/P/2147987769/Upgrade-Card-Pack-2{_AFF}', False, False),
    ('star-wars-legion-sun-fac-and-poggle-the-lesser-operative-and-commander-expansion', 'Sun Fac and Poggle the Lesser Operative and Commander Expansion', None, f'{_NK}/P/2148097161/Sun-Fac-and-Poggle-the-Lesser-Operative-and-Commander-Expansion{_AFF}', False, False),
    ('star-wars-legion-stormtroopers', 'Stormtroopers', None, f'{_NK}/P/2148291783/Stormtroopers{_AFF}', False, False),
    ('star-wars-legion-tx-130-saber-tank', 'TX-130 Saber Tank', None, f'{_NK}/P/2148395165/TX-130-Saber-Tank{_AFF}', False, False),
    ('star-wars-legion-heroes-of-the-rebellion-character-pack', 'Heroes of the Rebellion Character Pack', None, f'{_NK}/P/2148351976/Heroes-of-the-Rebellion-Character-Pack{_AFF}', False, False),
    ('star-wars-legion-rebel-troopers', 'Rebel Troopers', None, f'{_NK}/P/2148291785/Rebel-Troopers{_AFF}', False, False),
    ('star-wars-legion-3d-objective-tokens', '3d Objective Tokens', None, f'{_NK}/P/2148395170/3d-Objective-Tokens{_AFF}', False, False),
    ('star-wars-legion-b2-super-rocket-battle-droids', 'B2 Super Battle Droids', None, f'{_NK}/P/2148291792/B2-Super-Battle-Droids{_AFF}', False, False),
    ('star-wars-legion-republic-at-rt', 'Republic AT-RT', None, f'{_NK}/P/2148421589/Republic-AT-RT{_AFF}', False, False),
    ('star-wars-legion-bx-series-droid-commandos', 'BX Series Droid Commandos', None, f'{_NK}/P/2148421587/BX-Series-Droid-Commandos{_AFF}', False, False),
    ('star-wars-legion-arc-troopers-unit-expansion', 'ARC Troopers Unit Expansion', None, f'{_NK}/P/2148395167/ARC-Troopers-Unit-Expansion{_AFF}', False, False),
    ('star-wars-legion-imperial-death-troopers', 'Imperial Death Troopers', None, f'{_NK}/P/2148454825/Imperial-Death-Troopers{_AFF}', False, False),
    ('star-wars-legion-darth-vader-general-veers-character-expansion', 'Darth Vader & General Veers', None, f'{_NK}/P/2148352385/Darth-Vader-and-General-Veers{_AFF}', False, False),
    ('star-wars-legion-clone-commander-cody', 'Clone Commander Cody', None, f'{_NK}/P/2148291795/Clone-Commander-Cody{_AFF}', False, False),
    ('star-wars-legion-rogues-rebels', 'Rogues & Rebels', None, f'{_NK}/P/2148473511/Rogues-and-Rebels{_AFF}', False, False),
    ('star-wars-legion-outer-rim-outlaws', 'Outer Rim Outlaws', None, f'{_NK}/P/2148327725/Outer-Rim-Outlaws{_AFF}', False, False),
    ('star-wars-legion-scout-troopers', 'Scout Troopers', None, f'{_NK}/P/2148291801/Scout-Troopers{_AFF}', False, False),
    ('star-wars-legion-imperial-shoretroopers', 'Imperial Shoretroopers', None, f'{_NK}/P/2148396267/Imperial-Shoretroopers{_AFF}', False, False),
    ('star-wars-legion-geonosian-warriors-unit-expansion', 'Geonosian Warriors Unit Expansion', None, f'{_NK}/P/2148278699/Geonosian-Warriors-Unit-Expansion{_AFF}', False, False),
    ('star-wars-legion-ahsoka-tano-operative-expansion', 'Ahsoka Tano Operative Expansion', None, f'{_NK}/P/2148052693/Ahsoka-Tano-Operative-Expansion{_AFF}', False, False),
    ('star-wars-legion-republic-specialists', 'Republic Specialists', None, f'{_NK}/P/2148468295/Republic-Specialists{_AFF}', False, False),
    ('star-wars-legion-outer-rim-battles-terrain-pack', 'Outer Rim Battles Terrain Pack', None, f'{_NK}/P/2148258899/Outer-Rim-Battles-Terrain-Pack{_AFF}', False, False),
    ('star-wars-legion-dsd1-dwarf-spider-droid', 'DSD1 Dwarf Spider Droid', None, f'{_NK}/P/2148423989/DSD1-Dwarf-Spider-Droid{_AFF}', False, False),
    ('star-wars-legion-ig-100-magnaguards', 'IG-100 Magnaguards', None, f'{_NK}/P/2147942114/IG-100-MagnaGuards-Unit-Expansion{_AFF}', False, False),
    ('star-wars-legion-aat-battle-tank', 'AAT Battle Tank', None, f'{_NK}/P/2148395164/AAT-Battle-Tank{_AFF}', False, False),
    ('star-wars-legion-e-web-heavy-blaster-team', 'E-Web Heavy Blaster Team', None, f'{_NK}/P/2148454826/E-Web-Heavy-Blaster-Team{_AFF}', False, False),
    ('star-wars-legion-legion-attack-dice-pack', 'Legion Dice Pack (15)', None, f'{_NK}/P/2147694228/Legion---Dice-Pack-15{_AFF}', False, False),
    ('star-wars-legion-sabine-wren', 'Sabine Wren', None, f'{_NK}/P/2147757139/Sabine-Wren---Operative-Expansion{_AFF}', False, False),
    ('star-wars-legion-clone-troopers-infantry', 'Clone Troopers Infantry', None, f'{_NK}/P/2148360335/Clone-Troopers-Infantry{_AFF}', False, False),
    ('star-wars-legion-rebel-commandos', 'Rebel Commandos', None, f'{_NK}/P/2148291802/Rebel-Commandos{_AFF}', False, False),
    ('star-wars-legion-upgrade-card-pack', 'Upgrades Card Pack', None, f'{_NK}/P/2148347199/Upgrades-Card-Pack{_AFF}', False, False),
    ('star-wars-legion-t-47-airspeeder', 'T-47 Airspeeder', None, f'{_NK}/P/2148396258/T-47-Airspeeder{_AFF}', False, False),
    ('star-wars-legion-at-st-walker-expansion', 'AT-ST Walker Expansion', None, f'{_NK}/P/2148056443/AT-ST-Walker-Expansion{_AFF}', False, False),
    ('star-wars-legion-imperial-special-forces', 'Imperial Special Forces', None, f'{_NK}/P/2148421591/Imperial-Special-Forces{_AFF}', False, False),
    ('star-wars-legion-ewok-warriors', 'Ewok Warriors', None, f'{_NK}/P/2148396271/Ewok-Warriors{_AFF}', False, False),
    ('star-wars-legion-essentials-pack', 'Essentials Kit', None, f'{_NK}/P/2148347518/Essentials-Kit{_AFF}', False, False),
    ('star-wars-legion-dark-troopers', 'Dark Troopers', None, f'{_NK}/P/2148396266/Dark-Troopers{_AFF}', False, False),
    ('star-wars-legion-74-z-speeder-bike', '74-Z Speeder Bike', None, f'{_NK}/P/2148454829/74-Z-Speeder-Bike{_AFF}', False, False),
    ('star-wars-legion-fleet-troopers-unit', 'Fleet Troopers Unit', None, f'{_NK}/P/2148454830/Fleet-Troopers-Unit{_AFF}', False, False),
    ('star-wars-legion-a-a5-speeder-truck', 'A-A5 Speeder Truck (2021 Edition)', None, f'{_NK}/P/2147876788/A-A5-Speeder-Truck-2021-Edition{_AFF}', False, False),
    ('star-wars-legion-legion-defense-dice-pack', 'Legion Defense Dice Pack (16)', None, f'{_NK}/P/2148203059/Legion-Defense-Dice-Pack-16{_AFF}', False, False),
    ('star-wars-legion-b1-battle-droids', 'B1 Battle Droids', None, f'{_NK}/P/2148360336/B1-Battle-Droids{_AFF}', False, False),
    ('star-wars-legion-asajj-ventress-operative-expansion', 'Asajj Ventress Operative Expansion', None, f'{_NK}/P/2148040625/Asajj-Ventress-Operative-Expansion{_AFF}', False, False),
    ('star-wars-legion-tauntaun-riders', 'Tauntaun Riders', None, f'{_NK}/P/2148473806/Tauntaun-Riders{_AFF}', False, False),
    ('star-wars-legion-moff-gideon-commander-expansion', 'Moff Gideon Commander Expansion', None, f'{_NK}/P/2148036215/Moff-Gideon-Commander-Expansion{_AFF}', False, False),
    ('star-wars-legion-cassian-andor-jyn-erso-k-2so', 'Cassian Andor, Jyn Erso & K-2SO', None, f'{_NK}/P/2148395176/Cassian-Andor-Jyn-Erso-and-K-2SO{_AFF}', False, False),
    ('star-wars-legion-x-34-landspeeder', 'X-34 Landspeeder', None, f'{_NK}/P/2148473510/X-34-Landspeeder{_AFF}', False, False),
    ('star-wars-legion-imperial-specialists', 'Imperial Specialists', None, f'{_NK}/P/2148468299/Imperial-Specialists{_AFF}', False, False),
    ('star-wars-legion-ig-series-assassin-droids', 'IG Assassin Droids', None, f'{_NK}/P/2148327724/IG-Assassin-Droids{_AFF}', False, False),
    ('star-wars-legion-bad-batch', 'Bad Batch', None, f'{_NK}/P/2148473505/Bad-Batch{_AFF}', False, False),
    ('star-wars-legion-separatist-specialists', 'Separatist Specialists', None, f'{_NK}/P/2148468296/Separatist-Specialists{_AFF}', False, False),
    ('star-wars-legion-super-tactical-droid-commanders', 'Super Tactical Droid Commanders', None, f'{_NK}/P/2148396260/Super-Tactical-Droid-Commanders{_AFF}', False, False),
    ('star-wars-legion-r2d2-c-3po', 'R2D2 & C-3PO', None, f'{_NK}/P/2148396270/R2D2-and-C-3PO{_AFF}', False, False),
    ('star-wars-legion-kashyyyk-wookiee-warriors', 'Kashyyyk Wookiee Warriors', None, f'{_NK}/P/2148360337/Kashyyyk-Wookiee-Warriors{_AFF}', False, False),
    ('star-wars-legion-logray-wicket-commander-expansion', 'Logray & Wicket Commander Expansion', None, f'{_NK}/P/2148056454/Logray-and-Wicket-Commander-Expansion{_AFF}', False, False),
    ('star-wars-legion-snowtrooper', 'Snowtrooper', None, f'{_NK}/P/2148473508/Snowtrooper{_AFF}', False, False),
    ('star-wars-legion-rebel-specialists', 'Rebel Specialists', None, f'{_NK}/P/2148468298/Rebel-Specialists{_AFF}', False, False),
    ('star-wars-legion-rebel-veterans', 'Rebel Veterans', None, f'{_NK}/P/2148473507/Rebel-Veterans{_AFF}', False, False),
    ('star-wars-legion-range-troopers', 'Range Troopers', None, f'{_NK}/P/2148132333/Range-Troopers{_AFF}', False, False),
    ('star-wars-legion-poggle-the-lesser-sun-fac', 'Poggle the Lesser & Sun Fac', None, f'{_NK}/P/2148421586/Poggle-the-Lesser-and-Sun-Fac{_AFF}', False, False),
    ('star-wars-legion-droidekas', 'Droidekas', None, f'{_NK}/P/2148396261/Droidekas{_AFF}', False, False),
    ('star-wars-legion-rebel-at-rt', 'AT-RT - Rebel Unit Expansion', None, f'{_NK}/P/2147694226/AT-RT---Rebel-Unit-Expansion{_AFF}', False, False),
    ('star-wars-legion-infantry-support-platform', 'Infantry Support Platform', None, f'{_NK}/P/2147943173/Infantry-Support-Platform-Unit-Expansion{_AFF}', False, False),
    ('star-wars-legion-fifth-brother-seventh-sister', 'Fifth Brother & Seventh Sister', None, f'{_NK}/P/2148121465/Fifth-Brother-and-Seventh-Sister-Operative-Expansion{_AFF}', False, False),
    ('star-wars-legion-rebel-alliance-starter-set', 'Rebel Alliance Starter Set', None, f'{_NK}/P/2148347504/Rebel-Alliance-Starter-Set{_AFF}', False, False),
    ('star-wars-legion-separatist-alliance-command-card-pack', 'Separatist Alliance Command Card Pack', None, f'{_NK}/P/2148347349/Separatist-Alliance-Command-Card-Pack{_AFF}', False, False),
    ('star-wars-legion-rebellion-card-pack', 'Rebellion Card Pack', None, f'{_NK}/P/2148347220/Rebellion-Card-Pack{_AFF}', False, False),
    ('star-wars-legion-rebel-alliance-command-card-pack', 'Rebel Alliance Command Card Pack', None, f'{_NK}/P/2148347247/Rebel-Alliance-Command-Card-Pack{_AFF}', False, False),
    ('star-wars-legion-clone-trooper-marksmen', 'Clone Trooper Marksmen', None, f'{_NK}/P/2148360331/Clone-Trooper-Marksmen{_AFF}', False, False),
    ('star-wars-legion-republic-clone-commandos', 'Republic Clone Commandos', None, f'{_NK}/P/2148396241/Republic-Clone-Commandos{_AFF}', False, False),
    ('star-wars-legion-customizable-rebel-officer-agent', 'Customizable Rebel Officer & Agent', None, f'{_NK}/P/2148352383/Customizable-Rebel-Officer-and-Agent{_AFF}', False, False),
    ('star-wars-legion-battle-card-pack', 'Battle Deck Card Pack', None, f'{_NK}/P/2148347172/Battle-Deck-Card-Pack{_AFF}', False, False),
    ('star-wars-legion-clan-wren-mandalorians', 'Clan Wren Mandalorians', None, f'{_NK}/P/2148468324/Clan-Wren-Mandalorians{_AFF}', False, False),
    ('star-wars-legion-battle-deck-card-pack-ii', 'Battle Deck Card Pack II', None, f'{_NK}/P/2148423996/Battle-Deck-Card-Pack-II{_AFF}', False, False),
    ('star-wars-legion-aqua-droid-unit-expansion', 'Aqua Droid Unit Expansion', None, f'{_NK}/P/2148242022/Aqua-Droid-Unit-Expansion{_AFF}', False, False),
    ('star-wars-legion-captain-solo-commander-skywalker-on-tauntauns', 'Captain Solo & Commander Skywalker on Tauntauns', None, f'{_NK}/P/2148424760/Captain-Solo-and-Commander-Skywalker-on-Tauntauns{_AFF}', False, False),
    ('star-wars-legion-lm-432-crab-droid-unit-expansion', 'LM-432 Crab Droid Unit Expansion', None, f'{_NK}/P/2148242032/LM-432-Crab-Droid-Unit-Expansion{_AFF}', False, False),
    ('star-wars-legion-imperial-probe-droids', 'Imperial Probe Droid', None, f'{_NK}/P/2148429370/Imperial-Probe-Droid{_AFF}', False, False),
    ('star-wars-legion-hondo-ohnaka-weequay-pirates', 'Hondo Ohnaka & Weequay Pirates', None, f'{_NK}/P/2148424769/Hondo-Ohnaka-and-Weequay-Pirates{_AFF}', False, False),
    ('star-wars-legion-tsmeu-6-personal-wheel-bike', 'TSMEU-6 Personal Wheel Bike', None, f'{_NK}/P/2148423995/TSMEU-6-Personal-Wheel-Bike{_AFF}', False, False),
    ('star-wars-legion-heroes-of-the-clone-army', 'Heroes of the Clone Army', None, f'{_NK}/P/2148396263/Heroes-of-the-Clone-Army{_AFF}', False, False),
    ('star-wars-legion-b2-super-battle-droids', 'B2 Super Battle Droids', None, f'{_NK}/P/2148291792/B2-Super-Battle-Droids{_AFF}', False, False),
    ('star-wars-legion-wl0-5-speeder-tank', 'WL0-5 Speeder Tank', None, f'{_NK}/P/2148473813/WL0-5-Speeder-Tank{_AFF}', False, False),
]


class Command(BaseCommand):
    """Seed Noble Knight prices for Star Wars: Legion products (idempotent)."""

    help = 'Seeds Noble Knight CurrentPrice records for Star Wars: Legion products.'

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
