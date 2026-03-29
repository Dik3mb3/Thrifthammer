"""
Migration 0014 — Faction page data for Adeptus Mechanicus, Aeldari, Astra Militarum.

Creates blog tags for each faction and populates all faction page fields:
display_name, hero_tagline, synopsis, difficulty, model_count_rating,
painting_complexity, playstyle, price_range_display, blog_tag.
"""

from django.db import migrations


ADEPTUS_MECHANICUS_SYNOPSIS = (
    "The Adeptus Mechanicus are the keepers of technology for the entire Imperium, "
    "a vast priesthood that worships the Omnissiah and fields its armies using a "
    "fusion of ancient machinery and augmented warriors. On the tabletop they play "
    "as a mid-range shooting faction with strong board control, packing everything "
    "from rank-and-file Skitarii infantry to hulking Dunecrawlers and precision "
    "Dragoon cavalry.\n\n"
    "Painting an AdMech army is one of the hobby's most rewarding projects. Every "
    "model carries rich mechanical detail, robed tech-priests, and arcane weaponry "
    "that responds well across painting skill levels. Expect to spend real time on "
    "each unit, which is exactly why finding a discount matters here.\n\n"
    "Army building rewards careful synergy. Kastelan Robots become nearly unkillable "
    "when the Datasmiths are nearby. Skitarii Rangers and Vanguard provide a "
    "dependable infantry core. The faction favors methodical positioning and stacking "
    "buffs over charging headlong into melee, which suits players who enjoy layering "
    "mechanical advantages as a match develops.\n\n"
    "The prices tracked below are pulled daily from across US retailers. When you are "
    "buying three or four infantry boxes at once, even 15 percent off adds up to real "
    "savings before your army ever hits the table."
)

AELDARI_SYNOPSIS = (
    "The Aeldari are among the oldest and most technically advanced civilizations in "
    "the Warhammer 40,000 universe, a dying empire of psychic warriors who fight with "
    "calculated aggression and razor-sharp positioning. On the tabletop they reward "
    "players who plan several moves ahead, combining fast-moving units with devastating "
    "psychic powers and precise shooting to dictate where and when battles are fought.\n\n"
    "This is not a forgiving faction for new players. Aeldari units hit hard but die "
    "quickly, which means poor positioning or a badly judged advance can unravel an "
    "entire game plan. Players who invest the time to understand the synergies will "
    "find one of the most satisfying armies in the game.\n\n"
    "Painting Aeldari miniatures ranges from the sleek curves of Aspect Warriors to "
    "the flowing detail of wraith constructs, offering something for every painting "
    "preference. The distinctive colour schemes and large, unbroken armour panels make "
    "them a strong choice for painters who want bold, striking results without "
    "overwhelming surface detail.\n\n"
    "The prices below update daily across US retailers. Aeldari kits sit at the higher "
    "end of the price scale, which makes tracking discounts on boxes like the Wave "
    "Serpent or Wraithguard even more worthwhile before you commit to buying."
)

ASTRA_MILITARUM_SYNOPSIS = (
    "The Astra Militarum, formerly known as the Imperial Guard, is the largest "
    "fighting force in the Imperium, fielding millions of ordinary soldiers against "
    "the greatest threats in the galaxy. On the tabletop they play as a horde "
    "shooting army that buries opponents in bodies, artillery, and tanks. A full "
    "Astra Militarum army is one of the most model-intensive builds in Warhammer "
    "40,000, with infantry squads forming the backbone of every competitive list.\n\n"
    "For new players, this is one of the most approachable factions to learn. The "
    "core rules are straightforward, the infantry paints up quickly in a standard "
    "regimental scheme, and the faction punishes over-extension through sheer weight "
    "of fire rather than complex combo chains. Veterans of other tabletop systems "
    "will find the playstyle intuitive from the first game.\n\n"
    "The hobby investment here is significant. Buying enough Cadian Shock Troops, "
    "Heavy Weapon Teams, and tanks to fill a 2,000-point list adds up at full retail. "
    "Players who shop smart across US retailers regularly save 15 to 25 percent on "
    "their infantry boxes, which translates to meaningful savings when you need eight "
    "or ten of them.\n\n"
    "The deals below are tracked daily so you never overpay for your regiment."
)


def populate_faction_pages(apps, schema_editor):
    """Seed faction page content for AdMech, Aeldari, and Astra Militarum."""
    Faction = apps.get_model('products', 'Faction')
    Tag = apps.get_model('blog', 'Tag')

    factions = [
        {
            'name': 'Adeptus Mechanicus',
            'display_name': 'Adeptus Mechanicus',
            'hero_tagline': "The Machine God's Army. Track Down Every Kit at the Best Price.",
            'synopsis': ADEPTUS_MECHANICUS_SYNOPSIS,
            'difficulty': 'Intermediate',
            'model_count_rating': 'Medium',
            'painting_complexity': 'High',
            'playstyle': 'Shooting Control',
            'price_range_display': '$',
            'tag_name': 'Adeptus Mechanicus',
        },
        {
            'name': 'Aeldari',
            'display_name': 'Aeldari',
            'hero_tagline': 'Ancient Wisdom, Lethal Precision. Compare Prices on Every Aeldari Kit.',
            'synopsis': AELDARI_SYNOPSIS,
            'difficulty': 'Advanced',
            'model_count_rating': 'Medium',
            'painting_complexity': 'Medium-High',
            'playstyle': 'Speed and Flexibility',
            'price_range_display': '$$',
            'tag_name': 'Aeldari',
        },
        {
            'name': 'Astra Militarum',
            'display_name': 'Astra Militarum',
            'hero_tagline': "The Emperor's Hammer. Best Prices on Every Regiment Kit.",
            'synopsis': ASTRA_MILITARUM_SYNOPSIS,
            'difficulty': 'Beginner Friendly',
            'model_count_rating': 'High',
            'painting_complexity': 'Easy-Medium',
            'playstyle': 'Horde Shooting',
            'price_range_display': '$',
            'tag_name': 'Astra Militarum',
        },
    ]

    for data in factions:
        faction = Faction.objects.filter(name=data['name']).first()
        if not faction:
            continue

        tag, _ = Tag.objects.get_or_create(
            name=data['tag_name'],
            defaults={'slug': data['tag_name'].lower().replace(' ', '-')},
        )

        Faction.objects.filter(name=data['name']).update(
            display_name=data['display_name'],
            hero_tagline=data['hero_tagline'],
            synopsis=data['synopsis'],
            difficulty=data['difficulty'],
            model_count_rating=data['model_count_rating'],
            painting_complexity=data['painting_complexity'],
            playstyle=data['playstyle'],
            price_range_display=data['price_range_display'],
            blog_tag_id=tag.pk,
        )


def reverse_faction_pages(apps, schema_editor):
    """Clear faction page data for the three factions."""
    Faction = apps.get_model('products', 'Faction')
    for name in ('Adeptus Mechanicus', 'Aeldari', 'Astra Militarum'):
        Faction.objects.filter(name=name).update(
            display_name='',
            hero_tagline='',
            synopsis='',
            difficulty='',
            model_count_rating='',
            painting_complexity='',
            playstyle='',
            price_range_display='',
            blog_tag=None,
        )


class Migration(migrations.Migration):
    """Populate faction landing page data for AdMech, Aeldari, Astra Militarum."""

    dependencies = [
        ('products', '0013_faction_display_name'),
        ('blog', '0002_comment'),
    ]

    operations = [
        migrations.RunPython(
            populate_faction_pages,
            reverse_faction_pages,
        ),
    ]
