"""
Management command: seed_mm_marvel_crisis_protocol_prices

Seeds Miniature Market CurrentPrice records for Marvel Crisis Protocol
products.

64 of 73 products have a confirmed Miniature Market URL (source: Marvel
Crisis Protocol - Miniature Market.xlsx, matched by product title against
the DB product names). The remaining 9 products have no MM listing and are
intentionally left out.

Usage:
    python manage.py seed_mm_marvel_crisis_protocol_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

# (slug, listing_title, price, url, in_stock, not_available)
MM_PRICES = [
    ('marvel-crisis-protocol-x-men-starter-set', 'Marvel Crisis Protocol: X-Men Starter Set', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-x-men-starter-set-amgcp271.html', False, False),
    ('marvel-crisis-protocol-bastion-nimrod-omega-sentinel', 'Marvel Crisis Protocol: Bastion, Nimrod & Omega Sentinel', None, 'https://www.miniaturemarket.com/Marvel-Crisis-Protocol-Bastion-Nimrod-Omega-Sentinel/AMGMCP09', False, False),
    ('marvel-crisis-protocol-prowler-spider-man-2099-ultimate-spider-man', 'Marvel Crisis Protocol: Prowler, Spider-Man 2099, & Ultimate Spider-Man Character Pack', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-prowler-spider-man-2099-ultimate-spider-man-character-pack-amgcp169.html', False, False),
    ('marvel-crisis-protocol-phoenix-phoenix-unleashed', 'Marvel Crisis Protocol: Phoenix & Phoenix Unleashed', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-phoenix-phoenix-unleashed-amgcp83.html', False, False),
    ('marvel-crisis-protocol-spider-foes-starter-set', 'Marvel Crisis Protocol: Spider-Foes Starter Set', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-spider-foes-starter-set-amgcp272.html', False, False),
    ('marvel-crisis-protocol-silk-spider-ham-spider-man-noir', 'Marvel Crisis Protocol: Silk, Spider-Man Noir, Spider-Ham Character Pack', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-silk-spider-man-noir-spider-ham-character-pack-amgcp170.html', False, False),
    ('marvel-crisis-protocol-operation-zero-tolerance-character-crisis-card-pack', 'Marvel Crisis Protocol: Operation: Zero Tolerance - Character & Crisis Card Pack', None, 'https://www.miniaturemarket.com/Marvel-Crisis-Protocol-Operation-Zero-Tolerance-Character-Crisis-Card-Pack/AMGCA23', False, False),
    ('marvel-crisis-protocol-iron-lad-iron-monger-kang-the-conqueror-rescue', 'Marvel Crisis Protocol: Iron Lad, Iron Monger, Kang, & Rescue', None, 'https://www.miniaturemarket.com/Marvel-Crisis-Protocol-Iron-Lad-Iron-Monger-Kang-Rescue/AMGCP154', False, False),
    ('marvel-crisis-protocol-iceman-shadowcat', 'Marvel Crisis Protocol: Iceman & Shadowcat', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-iceman-shadowcat-amgcp96.html', False, False),
    ('marvel-crisis-protocol-adam-warlock-moondragon-quasar', 'Marvel Crisis Protocol: Adam Warlock, Moondragon, & Quasar', None, 'https://www.miniaturemarket.com/Marvel-Crisis-Protocol-Adam-Warlock-Moondragon-Quasar/AMGCP191', False, False),
    ('marvel-crisis-protocol-apocalypse', 'Marvel Crisis Protocol: Apocalypse', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-apocalypse-amgcp107.html', False, False),
    ('marvel-crisis-protocol-monsters-unleashed-character-pack', 'Marvel Crisis Protocol: Monsters Unleashed', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-monsters-unleashed-amgcp245.html', False, False),
    ('marvel-crisis-protocol-war-of-kings-character-and-crisis-card-pack', 'Marvel Crisis Protocol: War of Kings - Character & Crisis Card Pack', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-war-kings-character-crisis-card-pack-amgca13.html', False, False),
    ('marvel-crisis-protocol-xaviers-students-affiliation-pack', 'Marvel Crisis Protocol: Xavier\'s Students Affiliation Pack', None, 'https://www.miniaturemarket.com/Marvel-Crisis-Protocol-Xavier-s-Students-Affiliation-Pack/AMGCP226', False, False),
    ('marvel-crisis-protocol-web-swinging-heroes', 'Marvel Crisis Protocol: Web-Swinging Heroes Affiliation Pack', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-web-swinging-heroes-affiliation-pack-amgcp234.html', False, False),
    ('marvel-crisis-protocol-professor-x-shadow-king', 'Marvel Crisis Protocol: Professor X & Shadow King', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-professor-x-shadow-king-amgcp151.html', False, False),
    ('marvel-crisis-protocol-angel-archangel', 'Marvel Crisis Protocol: Angel & Archangel', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-angel-archangel-amgcp152.html', False, False),
    ('marvel-crisis-protocol-avalanche-exodus-lady-mastermind', 'Marvel Crisis Protocol: Avalanche, Exodus, & Lady Mastermind', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-avalanche-exodus-lady-mastermind-amgcp173.html', False, False),
    ('marvel-crisis-protocol-echo-ronin-tigra', 'Marvel Crisis Protocol: Echo, Ronin, & Tigra Character Pack', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-echo-ronin-tigra-character-pack-amgcp168.html', False, False),
    ('marvel-crisis-protocol-abomination-wrecking-crew', 'Marvel Crisis Protocol: Abomination & Wrecking Crew', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-abomination-wrecking-crew-amgcp162.html', False, False),
    ('marvel-crisis-protocol-tomb-of-dracula-terrain-pack', 'Marvel Crisis Protocol: Tomb of Dracula Terrain Pack', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-tomb-dracula-terrain-pack-amgcpe05.html', False, False),
    ('marvel-crisis-protocol-guardians-of-the-galaxy-starter-set', 'Marvel Crisis Protocol: Guardians of the Galaxy Starter Set (Preorder)', None, 'https://www.miniaturemarket.com/Marvel-Crisis-Protocol-Guardians-of-the-Galaxy-Starter-Set-Preorder/AMGMCP65EN', False, False),
    ('marvel-crisis-protocol-guardians-of-the-galaxy-affiliation-pack', 'Marvel Crisis Protocol: Guardians of the Galaxy Affiliation Pack', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-guardians-galaxy-affiliation-pack-amgcp222.html', False, False),
    ('marvel-crisis-protocol-rejuvenation-chamber-ultimate-encounter', 'Marvel Crisis Protocol: Rejuvenation Chamber - Terrain & Ultimate Encounter', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-rejuvenation-chamber-terrain-ultimate-encounter-amgcp194.html', False, False),
    ('marvel-crisis-protocol-asgardians-starter-set', 'Marvel Crisis Protocol: Asgardians Starter Set (Preorder)', None, 'https://www.miniaturemarket.com/Marvel-Crisis-Protocol-Asgardians-Starter-Set-Preorder/AMGMCP64', False, False),
    ('marvel-crisis-protocol-the-galaxys-deadliest-character-pack', 'Marvel Crisis Protocol: The Galaxy\'s Deadliest Character Pack', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-galaxys-deadliest-character-pack-amgcp223.html', False, False),
    ('marvel-crisis-protocol-shield-affiliation-pack', 'Marvel Crisis Protocol: S.H.I.E.L.D Affiliation Pack', None, 'https://www.miniaturemarket.com/Marvel-Crisis-Protocol-S.H.I.E.L.D-Affiliation-Pack/AMGMCP03', False, False),
    ('marvel-crisis-protocol-criminal-syndicate-affiliation-pack', 'Marvel Crisis Protocol: Criminal Syndicate Affiliation Pack', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-criminal-syndicate-affiliation-pack-amgcp214.html', False, False),
    ('marvel-crisis-protocol-dark-future-terrain-pack', 'Marvel Crisis Protocol: Dark Future Terrain Pack', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-dark-future-terrain-pack-amgcp185.html', False, False),
    ('marvel-crisis-protocol-shrine-to-en-sabah-nur-terrain-pack', 'Marvel Crisis Protocol: Shrine to En Sabah Nur Terrain Pack', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-shrine-to-en-sabah-nur-terrain-pack-amgcp110.html', False, False),
    ('marvel-crisis-protocol-convocation-affiliation-pack', 'Marvel Crisis Protocol: Convocation Affiliation Pack', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-convocation-affiliation-pack-amgcp221.html', False, False),
    ('marvel-crisis-protocol-movement-range-tool-pack', 'Marvel Crisis Protocol: Movement & Range Tool Pack', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-movement-range-tool-pack-amgca11.html', False, False),
    ('marvel-crisis-protocol-dice-pack', 'Marvel Crisis Protocol: Dice Pack', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-dice-pack-amgcp269.html', False, False),
    ('marvel-crisis-protocol-asgardian-shrine-terrain-pack', 'Marvel Crisis Protocol: Asgardian Shrine Terrain Pack', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-asgardian-shrine-terrain-pack-amgcp106.html', False, False),
    ('marvel-crisis-protocol-dimensional-terror-terrain-pack', 'Marvel Crisis Protocol: Dimensional Terror Terrain Pack (Preorder)', None, 'https://www.miniaturemarket.com/Marvel-Crisis-Protocol-Dimensional-Terror-Terrain-Pack-Preorder/AMGMCP11', False, False),
    ('marvel-crisis-protocol-battle-for-asgard-terrain-pack', 'Marvel Crisis Protocol: Battle for Asgard Terrain Pack', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-battle-for-asgard-terrain-pack-amgcp95.html', False, False),
    ('marvel-crisis-protocol-inhumans-affiliation-pack', 'Marvel Crisis Protocol: Inhumans Affiliation Pack', None, 'https://www.miniaturemarket.com/Marvel-Crisis-Protocol-Inhumans-Affiliation-Pack/AMGCP218', False, False),
    ('marvel-crisis-protocol-dark-dimension-incursion-terrain-pack', 'Marvel Crisis Protocol: Dark Dimension Incursion Terrain Pack (Preorder)', None, 'https://www.miniaturemarket.com/Marvel-Crisis-Protocol-Dark-Dimension-Incursion-Terrain-Pack-Preorder/AMGMCP12', False, False),
    ('marvel-crisis-protocol-spider-foes-affiliation-pack', 'Marvel Crisis Protocol: Spider-Foes Affiliation Pack', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-spider-foes-affiliation-pack-amgcp148.html', False, False),
    ('marvel-crisis-protocol-icons-of-bast-terrain-pack', 'Marvel Crisis Protocol: Icons of Bast Terrain Pack', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-icons-bast-terrain-pack-amgcp180.html', False, False),
    ('marvel-crisis-protocol-warriors-of-asgard-affiliation-pack', 'Marvel Crisis Protocol: Warriors of Asgard Affiliation Pack', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-warriors-asgard-affiliation-pack-amgcp225.html', False, False),
    ('marvel-crisis-protocol-movement-range-tools', 'Marvel Crisis Protocol: Movement & Range Tools', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-movement-range-tools-amgcp270.html', False, False),
    ('marvel-crisis-protocol-kingdom-of-wakanda-terrain-pack', 'Marvel Crisis Protocol: Kingdom of Wakanda Terrain Pack', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-kingdom-wakanda-terrain-pack-amgcp59.html', False, False),
    ('marvel-crisis-protocol-avengers-affiliation-pack', 'Marvel Crisis Protocol: Avengers Affiliation Pack', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-avengers-affiliation-pack-amgcp141.html', False, False),
    ('marvel-crisis-protocol-cabal-affiliation-pack', 'Marvel Crisis Protocol: Cabal Affiliation Pack', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-cabal-affiliation-pack-amgcp142.html', False, False),
    ('marvel-crisis-protocol-hydra-tank-terrain-ultimate-encounter', 'Marvel Crisis Protocol: Hydra Tank Terrain & Ultimate Encounter', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-hydra-tank-terrain-ultimate-encounter-amgcp78en.html', False, False),
    ('marvel-crisis-protocol-gwenom-scarlet-spider', 'Marvel Crisis Protocol: Gwenom & Scarlet Spider', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-gwenom-scarlet-spider-amgcp155.html', False, False),
    ('marvel-crisis-protocol-elsa-bloodstone-man-thing', 'Marvel Crisis Protocol: Elsa Bloodstone & Man-Thing', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-elsa-bloodstone-man-thing-amgcp186.html', False, False),
    ('marvel-crisis-protocol-mighty-thor-lady-sif-thor-hero-of-midgard-loki-prince-of-lies', 'Marvel Crisis Protocol: Mighty Thor, Lady Sif, Thor Hero of Midgard & Loki, Prince of Lies', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-mighty-thor-lady-sif-thor-hero-midgard-loki-prince-lies-amgcp91.html', False, False),
    ('marvel-crisis-protocol-valkyrie-on-elendil-warriors-three', 'Marvel Crisis Protocol: Valkyrie on Elendil & Warriors Three', None, 'https://www.miniaturemarket.com/Marvel-Crisis-Protocol-Valkyrie-on-Elendil-Warriors-Three/AMGCP94', False, False),
    ('marvel-crisis-protocol-yondu-nova', 'Marvel Crisis Protocol: Yondu & Nova', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-yondu-nova-amgcp126.html', False, False),
    ('marvel-crisis-protocol-earths-mightiest-core-set', 'Marvel Crisis Protocol: Earth\'s Mightiest Core Set', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-earths-mightiest-core-set-amgcp143en.html', False, False),
    ('marvel-crisis-protocol-black-panther-chosen-of-bast-namor-the-sub-mariner', 'Marvel Crisis Protocol: Black Panther, Chosen of Bast & Namor, the Sub-Mariner', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-black-panther-chosen-bast-namor-sub-mariner-amgcp158.html', False, False),
    ('marvel-crisis-protocol-defenders-affiliation-pack', 'Marvel Crisis Protocol: Defenders Affiliation Pack', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-defenders-affiliation-pack-amgcp219.html', False, False),
    ('marvel-crisis-protocol-shang-chi-silver-sable', 'Marvel Crisis Protocol: Shang Chi & Silver Sable', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-shang-chi-silver-sable-amgcp69.html', False, False),
    ('marvel-crisis-protocol-sentinels-affiliation-pack', 'Marvel Crisis Protocol: Sentinels Affiliation Pack', None, 'https://www.miniaturemarket.com/Marvel-Crisis-Protocol-Sentinels-Affiliation-Pack/AMGCP236', False, False),
    ('marvel-crisis-protocol-mojo-ball-scenario-pack', 'Marvel Crisis Protocol: Mojo Ball Scenario Pack', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-mojo-ball-scenario-pack-amgca14.html', False, False),
    ('marvel-crisis-protocol-x-force-affiliation-pack', 'Marvel Crisis Protocol: X-Force Affiliation Pack (Preorder)', None, 'https://www.miniaturemarket.com/Marvel-Crisis-Protocol-X-Force-Affiliation-Pack-Preorder/AMGCP224', False, False),
    ('marvel-crisis-protocol-blue-marvel-spectrum', 'Marvel Crisis Protocol: Blue Marvel & Spectrum', None, 'https://www.miniaturemarket.com/Marvel-Crisis-Protocol-Blue-Marvel-Spectrum/AMGCP129', False, False),
    ('marvel-crisis-protocol-inhuman-royal-court', 'Marvel Crisis Protocol: Inhuman Royal Court', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-inhuman-royal-court-amgcp166.html', False, False),
    ('marvel-crisis-protocol-weapon-x-maverick', 'Marvel Crisis Protocol: Weapon X & Maverick', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-weapon-x-maverick-amgcp109.html', False, False),
    ('marvel-crisis-protocol-nyc-city-block-terrain-collection', 'Marvel Crisis Protocol: NYC City Block Terrain Collection', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-nyc-city-block-terrain-collection-amgcpe06.html', False, False),
    ('marvel-crisis-protocol-sunspot-warlock', 'Marvel Crisis Protocol: Sunspot & Warlock', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-sunspot-warlock-amgcp153.html', False, False),
    ('marvel-crisis-protocol-mephisto', 'Marvel Crisis Protocol: Mephisto', None, 'https://www.miniaturemarket.com/marvel-crisis-protocol-mephisto-amgcp66.html', False, False),
]


class Command(BaseCommand):
    """Seed Miniature Market prices for Marvel Crisis Protocol products (idempotent)."""

    help = 'Seeds Miniature Market CurrentPrice records for Marvel Crisis Protocol products.'

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
