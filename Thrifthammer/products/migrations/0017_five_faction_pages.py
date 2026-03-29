"""
Migration 0017 — Faction page data for Black Templars, Blood Angels,
Chaos Space Marines, Dark Angels, Death Guard.
"""

from django.db import migrations


BLACK_TEMPLARS_SYNOPSIS = (
    "The Black Templars are the largest Space Marine Chapter in the Imperium, a "
    "crusading brotherhood that has waged endless war across the galaxy since the "
    "aftermath of the Horus Heresy. Where most Chapters station themselves around "
    "a home world, the Black Templars exist solely to fight, cycling through "
    "Crusades that can last centuries.\n\n"
    "On the tabletop they are one of the most aggressive Marine armies available. "
    "The entire faction is built around closing distance and winning in melee, with "
    "Crusader Squads, Sword Brethren, and the iconic Emperor's Champion leading the "
    "charge. A well-piloted Black Templars list punishes any opponent who lets the "
    "army close, and the faction rewards bold, forward-pressing play.\n\n"
    "Model count sits in the low to medium range for a Marine army, which keeps the "
    "painting commitment manageable. The black armour scheme is one of the most "
    "forgiving in the hobby: a solid basecoat, careful edge highlights, and a few "
    "purity seals go a long way. Newer painters regularly produce striking results "
    "without advanced techniques.\n\n"
    "The deals tracked below pull from US retailers daily. Core Black Templars kits "
    "like the Crusader Squad and Sword Brethren are the best places to start looking "
    "for savings before you commit."
)

BLOOD_ANGELS_SYNOPSIS = (
    "The Blood Angels are one of the oldest and most celebrated Space Marine Chapters, "
    "cursed with a genetic flaw that drives their warriors toward berserk fury in the "
    "heat of battle. That flaw, the Black Rage, shapes the entire faction on the "
    "tabletop: Blood Angels are built to close in fast and hit devastatingly hard in "
    "melee, with some of the strongest assault units in the Marine range.\n\n"
    "Death Company Marines and Sanguinary Guard are the centrepieces of most lists, "
    "delivering high-damage melee strikes while Primaris support units screen and "
    "provide fire support. The faction suits aggressive players who want to control "
    "the tempo of a game through threat and pressure rather than range.\n\n"
    "The Blood Angels aesthetic is among the richest in the hobby. Deep reds, gold "
    "trim, and angelic iconography make every model a painting project worth "
    "investing in. The colour scheme rewards layering and glazing techniques, but "
    "contrast paints have also made the base scheme faster to execute than ever.\n\n"
    "Prices below are tracked daily across US retailers. Starting with the Combat "
    "Patrol or picking up a Death Company box at a discount is the most cost-effective "
    "way to build toward a full list."
)

CHAOS_SPACE_MARINES_SYNOPSIS = (
    "Chaos Space Marines are the corrupted mirror of the Imperium's finest warriors, "
    "Space Marines who turned from the Emperor during the Horus Heresy or fell to "
    "Chaos in the millennia that followed. On the tabletop they are one of the most "
    "flexible and varied factions in the entire game, with access to Marks of Chaos, "
    "daemonic support, and a wide roster of specialized units that can be built "
    "around almost any playstyle.\n\n"
    "The faction rewards players who enjoy customizing their approach. Legionaries "
    "form a flexible infantry core, while Chosen, Possessed, and Dark Apostles provide "
    "combat power and buff support. Daemon Engines like the Maulerfiend bring melee "
    "threat, while Obliterators and Havocs offer shooting options. The breadth of the "
    "roster means no two Chaos lists play the same way.\n\n"
    "From a hobby perspective, Chaos Space Marines offer total creative freedom. "
    "Conversion work, mixed-Warband schemes, and corrupted armour effects are all "
    "deeply rewarded by the aesthetic. The models carry far more sculpted detail than "
    "loyalist counterparts, which challenges painters but produces extraordinary results.\n\n"
    "The prices below are pulled daily from across US retailers. Core boxes like "
    "Legionaries and Chosen represent the best value entry points for a new warband."
)

DARK_ANGELS_SYNOPSIS = (
    "The Dark Angels are the First Legion, the oldest Space Marine Chapter and keepers "
    "of a secret shame that has shaped every decision they have made since the Horus "
    "Heresy. That inner conflict drives one of the most thematically rich factions in "
    "the game, split between the power-armoured Battle Companies, the elite veteran "
    "Deathwing in Terminator plate, and the fast-moving Ravenwing on bikes and speeders.\n\n"
    "On the tabletop, Dark Angels reward players who build around their Chapter's "
    "unique strengths. Deathwing Terminators are among the most durable infantry in "
    "the Marine range. Ravenwing units bring speed and board control that other Marine "
    "armies cannot match. Balancing both wings into a single list is where experienced "
    "Dark Angels players find the faction's real depth.\n\n"
    "The hobby offers variety at every level. Dark green armour is forgiving and "
    "striking in equal measure, while the Deathwing bone scheme and Ravenwing black "
    "give painters two contrasting projects within the same army.\n\n"
    "Deals below are tracked daily across US retailers. Deathwing Terminators and "
    "Ravenwing Black Knights are the two kits most worth watching for discounts when "
    "building toward a fully fleshed-out Dark Angels force."
)

DEATH_GUARD_SYNOPSIS = (
    "The Death Guard are the chosen warriors of Nurgle, the Chaos God of plague and "
    "decay, bloated with pestilence and near-impossible to kill. On the tabletop they "
    "are the definition of an attrition army: slow, heavily resilient, and designed to "
    "grind opponents down through weight of wounds, debuffs, and corrosive firepower "
    "rather than speed or subtlety.\n\n"
    "Plague Marines are among the toughest infantry in the entire game relative to "
    "their points cost. Backed by Mortarion, the Daemon Primarch, or supported by "
    "Bloat-drones and Plagueburst Crawlers, a Death Guard list can absorb punishment "
    "that would wipe other armies off the table and keep walking forward. The faction "
    "suits players who enjoy outlasting opponents and controlling the pace of a game.\n\n"
    "From a hobby standpoint, Death Guard models are among the most distinctive ever "
    "produced. The layers of corruption, tentacles, and necrotic detail reward advanced "
    "painters, though contrast paints and washes have made the bloated armour "
    "surprisingly accessible for those earlier in their hobby journey.\n\n"
    "Prices below update daily from US retailers. Plague Marines and the Blightlord "
    "Terminators box are the highest-value kits to track for discounts when starting "
    "or expanding a Death Guard collection."
)


FACTIONS = [
    {
        'name': 'Black Templars',
        'hero_tagline': "No Mercy, No Respite. Find the Best Prices on Every Black Templars Kit.",
        'synopsis': BLACK_TEMPLARS_SYNOPSIS,
        'difficulty': 'Beginner Friendly',
        'model_count_rating': 'Low-Medium',
        'painting_complexity': 'Easy',
        'playstyle': 'Aggressive Melee',
        'price_range_display': '$$',
        'tag_name': 'Black Templars',
    },
    {
        'name': 'Blood Angels',
        'hero_tagline': "For Sanguinius and the Emperor. Track Every Blood Angels Deal.",
        'synopsis': BLOOD_ANGELS_SYNOPSIS,
        'difficulty': 'Intermediate',
        'model_count_rating': 'Low-Medium',
        'painting_complexity': 'Medium',
        'playstyle': 'Assault Elite',
        'price_range_display': '$$',
        'tag_name': 'Blood Angels',
    },
    {
        'name': 'Chaos Space Marines',
        'hero_tagline': "Glory to Chaos. Compare Prices Across Every Warband Kit.",
        'synopsis': CHAOS_SPACE_MARINES_SYNOPSIS,
        'difficulty': 'Intermediate',
        'model_count_rating': 'Medium',
        'painting_complexity': 'Medium-High',
        'playstyle': 'Flexible All-Rounder',
        'price_range_display': '$$',
        'tag_name': 'Chaos Space Marines',
    },
    {
        'name': 'Dark Angels',
        'hero_tagline': "Secrets and Steel. Find the Best Deals on Every Dark Angels Kit.",
        'synopsis': DARK_ANGELS_SYNOPSIS,
        'difficulty': 'Intermediate',
        'model_count_rating': 'Low-Medium',
        'painting_complexity': 'Medium',
        'playstyle': 'Balanced Dual-Wing',
        'price_range_display': '$$',
        'tag_name': 'Dark Angels',
    },
    {
        'name': 'Death Guard',
        'hero_tagline': "Blessed by Nurgle. Compare Prices on Every Death Guard Kit.",
        'synopsis': DEATH_GUARD_SYNOPSIS,
        'difficulty': 'Beginner Friendly',
        'model_count_rating': 'Low-Medium',
        'painting_complexity': 'Medium-High',
        'playstyle': 'Attrition',
        'price_range_display': '$$',
        'tag_name': 'Death Guard',
    },
]


def populate(apps, schema_editor):
    Faction = apps.get_model('products', 'Faction')
    Tag = apps.get_model('blog', 'Tag')
    for data in FACTIONS:
        if not Faction.objects.filter(name=data['name']).exists():
            continue
        tag, _ = Tag.objects.get_or_create(
            name=data['tag_name'],
            defaults={'slug': data['tag_name'].lower().replace(' ', '-')},
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


class Migration(migrations.Migration):
    dependencies = [('products', '0016_aeldari_model_count_fix')]
    operations = [migrations.RunPython(populate, depopulate)]
