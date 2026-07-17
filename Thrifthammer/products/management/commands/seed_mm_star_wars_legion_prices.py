"""
Management command: seed_mm_star_wars_legion_prices

Seeds Miniature Market CurrentPrice records for Star Wars: Legion products.

99 of 112 products have a confirmed Miniature Market URL (matched by hand
against the Miniature Market Excel scrape, cross-checked against Asmodee's
own product codes embedded in image filenames vs Miniature Market's SKU
codes embedded in their URLs). The remaining 13 products have no MM listing
and are intentionally left out.

Several products intentionally share the same MM listing as a sibling
product (e.g. SWL-005/SWL-025 both point at Miniature Market's single
"Upgrades Card Pack" listing; SWL-021/SWL-092 both point at "Fifth Brother
& Seventh Sister") -- confirmed directly by the user, not an error.

Usage:
    python manage.py seed_mm_star_wars_legion_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

# (slug, listing_title, price, url, in_stock, not_available)
MM_PRICES = [
    ('star-wars-legion-mandalorian-special-edition-army-box', 'Star Wars: Legion - Mandalorian Special Edition Army Box (New Arrival)', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-Mandalorian-Special-Edition-Army-Box-New-Arrival/AMGSWQ150', False, False),
    ('star-wars-legion-mandalorian-leaders', 'Star Wars: Legion - Mandalorian Leaders (New Arrival)', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-Mandalorian-Leaders-New-Arrival/AMGSWQ82', False, False),
    ('star-wars-legion-galactic-republic-starter-set', 'Star Wars: Legion - Galactic Republic Starter Set', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-Galactic-Republic-Starter-Set/AMGSWQ19', False, False),
    ('star-wars-legion-customizable-jedi-general-and-knight', 'Star Wars: Legion - Customizable Jedi General & Knight', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-Customizable-Jedi-General-Knight/AMGSWQ20', False, False),
    ('star-wars-legion-upgrades-card-pack', 'Star Wars: Legion - Upgrades Card Pack', None, 'https://www.miniaturemarket.com/star-wars-legion-upgrades-card-pack-amgswq144en.html', False, False),
    ('star-wars-legion-galactic-empire-starter-set', 'Star Wars: Legion - Galactic Empire Starter Set', None, 'https://www.miniaturemarket.com/star-wars-legion-galactic-empire-starter-set-amgswq02.html', False, False),
    ('star-wars-legion-general-grievous-tsmeu-6-wheel-bike', 'Star Wars: Legion - General Grievous\' TSMEU-6 Wheel Bike', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-General-Grievous-TSMEU-6-Wheel-Bike/AMGSWQ31', False, False),
    ('star-wars-legion-separatist-alliance-starter-set', 'Star Wars: Legion - Separatist Alliance Starter Set', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-Separatist-Alliance-Starter-Set/AMGSWQ28', False, False),
    ('star-wars-legion-empire-card-pack', 'Star Wars: Legion - Galactic Empire Unit Card Pack', None, 'https://www.miniaturemarket.com/star-wars-legion-galactic-empire-unit-card-pack-amgswq06en.html', False, False),
    ('star-wars-legion-customizable-imperial-officer-agent', 'Star Wars: Legion - Customizable Imperial Officer & Agent', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-Customizable-Imperial-Officer-Agent/AMGSWQ09', False, False),
    ('star-wars-legion-customizable-super-tactical-command-droid', 'Star Wars: Legion - Customizable Super Tactical Command Droid', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-Customizable-Super-Tactical-Command-Droid/AMGSWQ29', False, False),
    ('star-wars-legion-commander-padawan-ahsoka-tano', 'Star Wars: Legion - Commander & Padawan Ahsoka Tano', None, 'https://www.miniaturemarket.com/star-wars-legion-commander-padawan-ahsoka-tano-amgswq22.html', False, False),
    ('star-wars-legion-arf-troopers', 'Star Wars: Legion - ARF Troopers', None, 'https://www.miniaturemarket.com/star-wars-legion-arf-troopers-amgswq135.html', False, False),
    ('star-wars-legion-galactic-empire-command-card-pack', 'Star Wars: Legion - Galactic Empire Command Card Pack', None, 'https://www.miniaturemarket.com/star-wars-legion-galactic-empire-command-card-pack-amgswq156en.html', False, False),
    ('star-wars-legion-separatist-alliance-card-pack', 'Star Wars: Legion - Separatist Alliance Unit Card Pack', None, 'https://www.miniaturemarket.com/star-wars-legion-separatist-alliance-unit-card-pack-amgswq08en.html', False, False),
    ('star-wars-legion-galactic-republic-command-card-pack', 'Star Wars: Legion - Galactic Republic Command Card Pack', None, 'https://www.miniaturemarket.com/star-wars-legion-galactic-republic-command-card-pack-amgswq157en.html', False, False),
    ('star-wars-legion-mercenary-card-pack', 'Star Wars: Legion - Mercenary Card Pack', None, 'https://www.miniaturemarket.com/star-wars-legion-mercenary-card-pack-amgswq04en.html', False, False),
    ('star-wars-legion-fifth-brother-and-seventh-sister-operative-expansion', 'Star Wars: Legion - Fifth Brother & Seventh Sister', None, 'https://www.miniaturemarket.com/star-wars-legion-fifth-brother-seventh-sister-amgswl113.html', False, False),
    ('star-wars-legion-mandalorian-warriors', 'Star Wars: Legion - Mandalorian Warriors (Preorder)', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-Mandalorian-Warriors-Preorder/AMGSWQ81', False, False),
    ('star-wars-legion-leaders-of-the-shadow-collective', 'Star Wars: Legion - Leaders of the Shadow Collective', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-Leaders-of-the-Shadow-Collective/AMGSWQ77', False, False),
    ('star-wars-legion-mandalorian-super-commandos', 'Star Wars: Legion - Mandalorian Super Commandos (New Arrival)', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-Mandalorian-Super-Commandos-New-Arrival/AMGSWQ69', False, False),
    ('star-wars-legion-upgrades-card-pack-2', 'Star Wars: Legion - Upgrades Card Pack', None, 'https://www.miniaturemarket.com/star-wars-legion-upgrades-card-pack-amgswq144en.html', False, False),
    ('star-wars-legion-sun-fac-and-poggle-the-lesser-operative-and-commander-expansion', 'Star Wars: Legion - Sun Fac & Poggle the Lesser', None, 'https://www.miniaturemarket.com/star-wars-legion-sun-fac-poggle-lesser-amgswl116.html', False, False),
    ('star-wars-legion-stormtroopers', 'Star Wars: Legion - Stormtroopers', None, 'https://www.miniaturemarket.com/star-wars-legion-stormtroopers-amgswq11.html', False, False),
    ('star-wars-legion-tx-130-saber-tank', 'Star Wars: Legion - TX-130 Saber-Class Tank', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-TX-130-Saber-Class-Tank/AMGSWQ27', False, False),
    ('star-wars-legion-heroes-of-the-rebellion-character-pack', 'Star Wars: Legion - Heroes of the Rebellion', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-Heroes-of-the-Rebellion/AMGSWQ14', False, False),
    ('star-wars-legion-rebel-troopers', 'Star Wars: Legion - Rebel Troopers', None, 'https://www.miniaturemarket.com/star-wars-legion-rebel-troopers-amgswq15.html', False, False),
    ('star-wars-legion-3d-objective-tokens', 'Star Wars: Legion - 3D Objective Tokens', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-3D-Objective-Tokens/AMGSWQ102', False, False),
    ('star-wars-legion-republic-at-rt', 'Star Wars: Legion - Republic AT-RT', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-Republic-AT-RT/AMGSWQ198', False, False),
    ('star-wars-legion-bx-series-droid-commandos', 'Star Wars: Legion - BX-Series Droid Commandos', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-BX-Series-Droid-Commandos/AMGSWQ52', False, False),
    ('star-wars-legion-arc-troopers-unit-expansion', 'Star Wars: Legion - ARC Troopers Unit Expansion', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-ARC-Troopers-Unit-Expansion/AMGSWQ133', False, False),
    ('star-wars-legion-darth-vader-general-veers-character-expansion', 'Star Wars: Legion - Darth Vader & General Veers Character Expansion', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-Darth-Vader-General-Veers-Character-Expansion/AMGSWQ103', False, False),
    ('star-wars-legion-clone-commander-cody', 'Star Wars: Legion - Clone Commander Cody', None, 'https://www.miniaturemarket.com/star-wars-legion-clone-commander-cody-amgswq72.html', False, False),
    ('star-wars-legion-rogues-rebels', 'Star Wars: Legion - Rogues & Rebels (Preorder)', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-Rogues-Rebels-Preorder/AMGSWQ50', False, False),
    ('star-wars-legion-outer-rim-outlaws', 'Star Wars: Legion - Outer Rim Outlaws', None, 'https://www.miniaturemarket.com/star-wars-legion-outher-rim-outlaws-amgswq138.html', False, False),
    ('star-wars-legion-scout-troopers', 'Star Wars: Legion - Scout Troopers', None, 'https://www.miniaturemarket.com/star-wars-legion-scout-troopers-amgswq12.html', False, False),
    ('star-wars-legion-imperial-shoretroopers', 'Star Wars: Legion - Imperial Shoretroopers (Multilingual)', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-Imperial-Shoretroopers-Multilingual/AMGSWQ199', False, False),
    ('star-wars-legion-geonosian-warriors-unit-expansion', 'Star Wars: Legion - Geonosian Warriors Unit Expansion', None, 'https://www.miniaturemarket.com/star-wars-legion-geonosian-warriors-unit-expansion-amgswq37.html', False, False),
    ('star-wars-legion-ahsoka-tano-operative-expansion', 'Star Wars: Legion - Ahsoka Tano Operative Expansion', None, 'https://www.miniaturemarket.com/star-wars-legion-ahsoka-tano-operative-expansion-amgswl106en.html', False, False),
    ('star-wars-legion-republic-specialists', 'Star Wars: Legion - Republic Specialists', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-Republic-Specialists/AMGSWQ200', False, False),
    ('star-wars-legion-outer-rim-battles-terrain-pack', 'Star Wars: Legion - Outer Rim Battles Terrain Pack', None, 'https://www.miniaturemarket.com/star-wars-legion-outer-rim-battles-terrain-pack-amgswq137.html', False, False),
    ('star-wars-legion-dsd1-dwarf-spider-droid', 'Star Wars: Legion - DSD1 Dwarf Spider Droid', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-DSD1-Dwarf-Spider-Droid/AMGSWQ61', False, False),
    ('star-wars-legion-ig-100-magnaguards', 'Star Wars: Legion - IG-100 MagnaGuards (Multilingual)', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-IG-100-MagnaGuards-Multilingual/AMGSWQ58', False, False),
    ('star-wars-legion-aat-battle-tank', 'Star Wars: Legion - AAT Battle Tank', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-AAT-Battle-Tank/AMGSWQ33', False, False),
    ('star-wars-legion-legion-attack-dice-pack', 'Star Wars: Legion - Legion Attack Dice Pack (16)', None, 'https://www.miniaturemarket.com/star-wars-legion-legion-attack-dice-pack-16-amgswq131.html', False, False),
    ('star-wars-legion-sabine-wren', 'Star Wars: Legion - Sabine Wren', None, 'https://www.miniaturemarket.com/ffgswl37.html', False, False),
    ('star-wars-legion-clone-troopers-infantry', 'Star Wars: Legion - Clone Trooper Infantry', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-Clone-Trooper-Infantry/AMGSWQ24', False, False),
    ('star-wars-legion-rebel-commandos', 'Star Wars: Legion - Rebel Commandos', None, 'https://www.miniaturemarket.com/star-wars-legion-rebel-commandos-amgswq16.html', False, False),
    ('star-wars-legion-upgrade-card-pack', 'Star Wars: Legion - Upgrade Card Pack', None, 'https://www.miniaturemarket.com/ffgswl51.html', False, False),
    ('star-wars-legion-t-47-airspeeder', 'Star Wars: Legion - T-47 Airspeeder (Multilingual) (Preorder)', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-T-47-Airspeeder-Multilingual-Preorder/AMGSWQ17', False, False),
    ('star-wars-legion-at-st-walker-expansion', 'Star Wars: Legion - AT-ST Walker (Multilingual)', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-AT-ST-Walker-Multilingual/AMGSWQ10', False, False),
    ('star-wars-legion-imperial-special-forces', 'Star Wars: Legion - Imperial Special Forces', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-Imperial-Special-Forces/AMGSWQ53', False, False),
    ('star-wars-legion-ewok-warriors', 'Star Wars: Legion - Ewok Warriors (Multilingual)', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-Ewok-Warriors-Multilingual/AMGSWQ73', False, False),
    ('star-wars-legion-essentials-pack', 'Star Wars: Legion - Essentials Pack', None, 'https://www.miniaturemarket.com/star-wars-legion-essentials-pack-amgswq03.html', False, False),
    ('star-wars-legion-dark-troopers', 'Star Wars: Legion - Imperial Dark Troopers (Multilingual)', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-Imperial-Dark-Troopers-Multilingual/AMGSWQ63', False, False),
    ('star-wars-legion-fleet-troopers-unit', 'Star Wars: Legion - Fleet Troopers Unit', None, 'https://www.miniaturemarket.com/ffgswl13.html', False, False),
    ('star-wars-legion-a-a5-speeder-truck', 'Star Wars: Legion - A-A5 Speeder Truck', None, 'https://www.miniaturemarket.com/star-wars-legion-a-a5-speeder-truck-amgswq92.html', False, False),
    ('star-wars-legion-legion-defense-dice-pack', 'Star Wars: Legion - Legion Defense Dice Pack (16)', None, 'https://www.miniaturemarket.com/star-wars-legion-legion-defense-dice-pack-16-amgswq132.html', False, False),
    ('star-wars-legion-b1-battle-droids', 'Star Wars: Legion - B1 Battle Droids', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-B1-Battle-Droids/AMGSWQ30', False, False),
    ('star-wars-legion-asajj-ventress-operative-expansion', 'Star Wars: Legion - Asajj Ventress', None, 'https://www.miniaturemarket.com/star-wars-legion-asajj-ventress-amgswl108en.html', False, False),
    ('star-wars-legion-tauntaun-riders', 'Star Wars: Legion - Tauntaun Riders', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-Tauntaun-Riders/AMGSWQ40', False, False),
    ('star-wars-legion-moff-gideon-commander-expansion', 'Star Wars: Legion - Moff Gideon Commander Expansion', None, 'https://www.miniaturemarket.com/star-wars-legion-moff-gideon-commander-expansion-amgswl102en.html', False, False),
    ('star-wars-legion-cassian-andor-jyn-erso-k-2so', 'Star Wars: Legion - Cassian Andor, Jyn Erso, & K-2SO', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-Cassian-Andor-Jyn-Erso-K-2SO/AMGSWQ39', False, False),
    ('star-wars-legion-x-34-landspeeder', 'Star Wars: Legion - X-34 Landspeeder (Preorder)', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-X-34-Landspeeder-Preorder/AMGSWQ202', False, False),
    ('star-wars-legion-imperial-specialists', 'Star Wars: Legion - Imperial Specialists', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-Imperial-Specialists/AMGSWQ192', False, False),
    ('star-wars-legion-ig-series-assassin-droids', 'Star Wars: Legion - IG Assassin Droids', None, 'https://www.miniaturemarket.com/star-wars-legion-ig-series-assassin-droids-amgswq139.html', False, False),
    ('star-wars-legion-bad-batch', 'Star Wars: Legion - Bad Batch (New Arrival)', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-Bad-Batch-New-Arrival/AMGSWQ90', False, False),
    ('star-wars-legion-separatist-specialists', 'Star Wars: Legion - Separatist Specialists', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-Separatist-Specialists/AMGSWQ201', False, False),
    ('star-wars-legion-super-tactical-droid-commanders', 'Star Wars: Legion - Super Tactical Droid Commanders (Multilingual)', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-Super-Tactical-Droid-Commanders-Multilingual/AMGSWQ38', False, False),
    ('star-wars-legion-r2d2-c-3po', 'Star Wars: Legion - R2-D2 & C-3PO (Multilingual)', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-R2-D2-C-3PO-Multilingual/AMGSWQ142', False, False),
    ('star-wars-legion-kashyyyk-wookiee-warriors', 'Star Wars: Legion - Kashyyyk Wookie Warriors', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-Kashyyyk-Wookie-Warriors/AMGSWQ18', False, False),
    ('star-wars-legion-logray-wicket-commander-expansion', 'Star Wars: Legion - Logray & Wicket (Multilingual) (Preorder)', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-Logray-Wicket-Multilingual-Preorder/AMGSWQ74', False, False),
    ('star-wars-legion-snowtrooper', 'Star Wars: Legion - Snowtrooper (Preorder)', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-Snowtrooper-Preorder/AMGSWQ43', False, False),
    ('star-wars-legion-rebel-specialists', 'Star Wars: Legion - Rebel Specialists', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-Rebel-Specialists/AMGSWQ193', False, False),
    ('star-wars-legion-rebel-veterans', 'Star Wars: Legion - Rebel Veterans (Preorder)', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-Rebel-Veterans-Preorder/AMGSWQ75', False, False),
    ('star-wars-legion-range-troopers', 'Star Wars: Legion - Range Troopers', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-Range-Troopers/AMGSWQ89', False, False),
    ('star-wars-legion-poggle-the-lesser-sun-fac', 'Star Wars: Legion - Sun Fac & Poggle the Lesser', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-Sun-Fac-Poggle-the-Lesser/AMGSWQ101', False, False),
    ('star-wars-legion-droidekas', 'Star Wars: Legion - Droidekas (Multilingual) (Preorder)', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-Droidekas-Multilingual-Preorder/AMGSWQ36', False, False),
    ('star-wars-legion-infantry-support-platform', 'Star Wars: Legion - Infantry Support Platform Unit Expansion', None, 'https://www.miniaturemarket.com/amgswl85.html', False, False),
    ('star-wars-legion-fifth-brother-seventh-sister', 'Star Wars: Legion - Fifth Brother & Seventh Sister', None, 'https://www.miniaturemarket.com/star-wars-legion-fifth-brother-seventh-sister-amgswl113.html', False, False),
    ('star-wars-legion-rebel-alliance-starter-set', 'Star Wars: Legion - Rebel Alliance Starter Set', None, 'https://www.miniaturemarket.com/star-wars-legion-rebel-alliance-starter-set-amgswq01.html', False, False),
    ('star-wars-legion-separatist-alliance-command-card-pack', 'Star Wars: Legion - Separatist Alliance Command Card Pack', None, 'https://www.miniaturemarket.com/star-wars-legion-separatist-alliance-command-card-pack-amgswq158en.html', False, False),
    ('star-wars-legion-rebellion-card-pack', 'Star Wars: Legion - Rebel Alliance Unit Card Pack', None, 'https://www.miniaturemarket.com/star-wars-legion-rebel-alliance-unit-card-pack-amgswq05en.html', False, False),
    ('star-wars-legion-rebel-alliance-command-card-pack', 'Star Wars: Legion - Rebel Alliance Command Card Pack', None, 'https://www.miniaturemarket.com/star-wars-legion-rebel-alliance-command-card-pack-amgswq155en.html', False, False),
    ('star-wars-legion-clone-trooper-marksmen', 'Star Wars: Legion - Clone Trooper Marksmen', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-Clone-Trooper-Marksmen/AMGSWQ23', False, False),
    ('star-wars-legion-republic-clone-commandos', 'Star Wars: Legion - Republic Clone Commandos (Multilingual)', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-Republic-Clone-Commandos-Multilingual/AMGSWQ26', False, False),
    ('star-wars-legion-customizable-rebel-officer-agent', 'Star Wars: Legion - Customizable Rebel Officer & Agent', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-Customizable-Rebel-Officer-Agent/AMGSWQ13', False, False),
    ('star-wars-legion-battle-card-pack', 'Star Wars: Legion - Battle Deck Card Pack', None, 'https://www.miniaturemarket.com/star-wars-legion-battle-deck-card-pack-amgswq125en.html', False, False),
    ('star-wars-legion-clan-wren-mandalorians', 'Star Wars: Legion - Clan Wren Mandalorians (New Arrival)', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-Clan-Wren-Mandalorians-New-Arrival/AMGSWQ56', False, False),
    ('star-wars-legion-battle-deck-card-pack-ii', 'Star Wars: Legion - Battle Deck Card Pack II', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-Battle-Deck-Card-Pack-II/AMGSWQ151', False, False),
    ('star-wars-legion-aqua-droid-unit-expansion', 'Star Wars: Legion - Aqua Droid Unit Expansion', None, 'https://www.miniaturemarket.com/star-wars-legion-aqua-droid-unit-expansion-amgswq136.html', False, False),
    ('star-wars-legion-captain-solo-commander-skywalker-on-tauntauns', 'Star Wars: Legion - Captain Solo & Commander Skywalker on Tauntauns (Multilingual)', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-Captain-Solo-Commander-Skywalker-on-Tauntauns-Multilingual/AMGSWQ41', False, False),
    ('star-wars-legion-lm-432-crab-droid-unit-expansion', 'Star Wars: Legion - LM-432 Crab Droids Unit Expansion', None, 'https://www.miniaturemarket.com/star-wars-legion-lm-432-crab-droids-unit-expansion-amgswq134.html', False, False),
    ('star-wars-legion-imperial-probe-droids', 'Star Wars: Legion - Imperial Probe Droids', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-Imperial-Probe-Droids/AMGSWQ98', False, False),
    ('star-wars-legion-hondo-ohnaka-weequay-pirates', 'Star Wars: Legion - Hondo Ohnaka & Weequay Pirates', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-Hondo-Ohnaka-Weequay-Pirates/AMGSWQ45', False, False),
    ('star-wars-legion-tsmeu-6-personal-wheel-bike', 'Star Wars: Legion - TSMEU-6 Personal Wheel Bike', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-TSMEU-6-Personal-Wheel-Bike/AMGSWQ32', False, False),
    ('star-wars-legion-heroes-of-the-clone-army', 'Star Wars: Legion - Heroes of the 501st (Multilingual)', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-Heroes-of-the-501st-Multilingual/AMGSWQ21', False, False),
    ('star-wars-legion-b2-super-battle-droids', 'Star Wars: Legion - B2 Super Battle Droids', None, 'https://www.miniaturemarket.com/star-wars-legion-b2-super-battle-droids-amgswq35.html', False, False),
    ('star-wars-legion-wl0-5-speeder-tank', 'Star Wars: Legion - WL0-5 Speeder Tanks', None, 'https://www.miniaturemarket.com/Star-Wars-Legion-WL0-5-Speeder-Tanks/AMGSWQ59', False, False),
]


class Command(BaseCommand):
    """Seed Miniature Market prices for Star Wars: Legion products (idempotent)."""

    help = 'Seeds Miniature Market CurrentPrice records for Star Wars: Legion products.'

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
