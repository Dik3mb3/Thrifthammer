"""
Migration 0023 — Faction pages for Leagues of Votann and Chaos Knights.
Also creates the Chaos Knights faction record (40K category) if absent.
"""

from django.db import migrations


VOTANN_SYNOPSIS = (
    "The Leagues of Votann are a rediscovered human offshoot, stocky and tenacious "
    "void-born warriors who have carved out empires in the resource-rich galactic "
    "core. Known historically as Squats, they have returned to Warhammer 40,000 "
    "with an entirely new range, deep lore, and a uniquely self-sufficient identity "
    "that sets them apart from every other human faction in the game.\n\n"
    "On the tabletop they are a durable mid-range shooting army with excellent "
    "equipment across the board. Hearthkyn Warriors form the infantry core, backed "
    "by Einhyr Hearthguard for elite muscle and Hernkyn Pioneers for fast "
    "objective pressure. The faction rewards players who like consistent "
    "performance and solid fundamentals rather than glass-cannon specialisation.\n\n"
    "The hobby side is one of the freshest in the game. Exo-armour, runic "
    "iconography, heavy industry aesthetics, and compact muscular proportions "
    "give painters a completely different visual language. The range is still "
    "growing, which means building a Votann force now means getting ahead of "
    "the curve.\n\n"
    "Prices below are tracked daily from US retailers. The Combat Patrol is the "
    "best entry point and regularly shows up at meaningful discounts — watch "
    "it closely before committing to your first League."
)

CHAOS_KNIGHTS_SYNOPSIS = (
    "Chaos Knights are the corrupted counterparts of the Imperial Knights, "
    "once-noble war machines that have fallen to the dark powers and now serve "
    "Chaos as towering engines of destruction and malice. Where Imperial Knights "
    "fight with duty and honour, their Chaos counterparts revel in slaughter, "
    "their baroque armour twisted by warp energy and hung with the trophies of "
    "their fallen foes.\n\n"
    "On the tabletop Chaos Knights mirror the Imperial Knights playstyle with "
    "a unique twist: Dread — a mechanic that rewards aggression and punishes "
    "passive play. War Dogs form the core of most lists, fast and expendable "
    "attack dogs that close distance rapidly while the bigger Knights deliver "
    "devastating firepower. The faction suits players who enjoy big-model "
    "armies with dramatic presence and a high-variance, high-reward playstyle.\n\n"
    "From a hobby perspective, Chaos Knights are among the most customisable "
    "kits in the game. Corrupted armour plating, chains, spikes, and warp "
    "iconography give every model a distinctive character, and the large flat "
    "panels are a canvas for freehand or weathering techniques. A converted "
    "Chaos Knight is one of the hobby's great achievements.\n\n"
    "Prices below are tracked daily from US retailers. War Dogs are the core "
    "kit to watch for discounts — you will typically run several, and the "
    "savings across a full pack add up significantly."
)

FACTIONS = [
    {
        'name': 'Leagues of Votann',
        'hero_tagline': "For Kin and Coin. Find the Best Prices on Every Leagues of Votann Kit.",
        'synopsis': VOTANN_SYNOPSIS,
        'difficulty': 'Beginner Friendly',
        'model_count_rating': 'Low-Medium',
        'painting_complexity': 'Easy-Medium',
        'playstyle': 'Durable Shooting',
        'price_range_display': '$$$',
        'tag_name': 'Leagues of Votann',
    },
    {
        'name': 'Chaos Knights',
        'hero_tagline': "Dread and Destruction. Compare Prices on Every Chaos Knights Kit.",
        'synopsis': CHAOS_KNIGHTS_SYNOPSIS,
        'difficulty': 'Beginner Friendly',
        'model_count_rating': 'Very Low',
        'painting_complexity': 'High',
        'playstyle': 'Dread Assault',
        'price_range_display': '$$$$$',
        'tag_name': 'Chaos Knights',
    },
]


def populate(apps, schema_editor):
    Category = apps.get_model('products', 'Category')
    Faction = apps.get_model('products', 'Faction')
    Tag = apps.get_model('blog', 'Tag')

    cat_40k = Category.objects.filter(name='Warhammer 40,000').first()

    for data in FACTIONS:
        # Create the faction record if it doesn't exist yet (Chaos Knights).
        Faction.objects.get_or_create(
            name=data['name'],
            defaults={
                'slug': data['name'].lower().replace(' ', '-').replace("'", ''),
                'category': cat_40k,
            },
        )

        tag, _ = Tag.objects.get_or_create(
            name=data['tag_name'],
            defaults={
                'slug': data['tag_name'].lower().replace(' ', '-').replace("'", ''),
            },
        )
        Faction.objects.filter(name=data['name']).update(
            display_name=data['name'],
            hero_tagline=data['hero_tagline'],
            synopsis=data['synopsis'],
            difficulty=data['difficulty'],
            model_count_rating=data['model_count_rating'],
            painting_complexity=data['painting_complexity'],
            playstyle=data['playstyle'],
            price_range_display=data['price_range_display'],
            blog_tag_id=tag.pk,
        )


def depopulate(apps, schema_editor):
    Faction = apps.get_model('products', 'Faction')
    for data in FACTIONS:
        Faction.objects.filter(name=data['name']).update(
            display_name='', hero_tagline='', synopsis='', difficulty='',
            model_count_rating='', painting_complexity='', playstyle='',
            price_range_display='', blog_tag=None,
        )
    # Remove Chaos Knights faction if it was created by this migration.
    Faction.objects.filter(name='Chaos Knights', products__isnull=True).delete()


class Migration(migrations.Migration):
    dependencies = [('products', '0022_eight_faction_pages')]
    operations = [migrations.RunPython(populate, depopulate)]
