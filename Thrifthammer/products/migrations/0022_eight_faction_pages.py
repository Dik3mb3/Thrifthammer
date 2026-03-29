"""
Migration 0022 — Faction page data for Sisters of Battle, Space Marines,
Space Wolves, T'au Empire, Thousand Sons, Tyranids, Ultramarines, World Eaters.
"""

from django.db import migrations


SISTERS_SYNOPSIS = (
    "The Sisters of Battle, formally known as the Adepta Sororitas, are the "
    "militant arm of the Ecclesiarchy, warrior nuns clad in power armour who "
    "channel their absolute faith in the Emperor into supernatural miracles on "
    "the battlefield. They are the only non-Space Marine faction in the Imperium "
    "that wears power armour as standard, making them among the toughest human "
    "infantry in the game.\n\n"
    "On the tabletop they play as a mid-range shooting army with a powerful "
    "secondary layer built around Acts of Faith, miracle dice that can be spent "
    "to dramatically alter the outcome of rolls at key moments. Managing that "
    "miracle dice pool is the central skill of the faction, rewarding players who "
    "save their resources for the moments that matter most.\n\n"
    "The hobby investment is significant and satisfying in equal measure. Sisters "
    "models are among the most detailed in the entire range, with intricate armour, "
    "flowing robes, and elaborate iconography. The red and gold classic scheme is "
    "striking, but the faction lends itself to custom colour choices that can make "
    "a force feel entirely personal.\n\n"
    "Deals below are tracked daily from US retailers. Battle Sisters squads are "
    "the core to watch for discounts, as you will need several to form a "
    "competitive core."
)

SPACE_MARINES_SYNOPSIS = (
    "The Space Marines are the backbone of the Imperium and the most iconic faction "
    "in Warhammer 40,000. Genetically engineered warriors clad in power armour, "
    "they represent the game's most balanced and versatile army, with a roster so "
    "broad that virtually any playstyle is achievable within the codex.\n\n"
    "On the tabletop this breadth is the faction's defining strength. Primaris "
    "infantry form a reliable and durable core. Vehicles like the Repulsor and "
    "Gladiator provide firepower, while jump pack units and Terminators offer "
    "melee threat. Building a Space Marine list is one of the best ways to learn "
    "the game, because the tools to handle any situation are all available.\n\n"
    "For new hobbyists, Space Marines are the ideal starting point. The models are "
    "forgiving to assemble and paint, the blue or any Chapter colour looks strong "
    "with basic techniques, and the sheer volume of tutorials available online "
    "means help is always a search away.\n\n"
    "Prices below are updated daily across US retailers. Intercessors and the "
    "Combat Patrol box are the most cost-effective entry points, and both are "
    "worth watching for discounts when building your first company."
)

SPACE_WOLVES_SYNOPSIS = (
    "The Space Wolves are the most savage of the Space Marine Chapters, fierce "
    "warriors from the frozen world of Fenris who blend the discipline of a "
    "Space Marine with the feral instincts of a Viking raider. Their culture, "
    "their units, and their playstyle all reflect that duality.\n\n"
    "On the tabletop Space Wolves lean toward aggressive melee supported by "
    "ranged fire, with unique units like Blood Claws and Grey Hunters providing "
    "a characterful infantry core. Thunderwolf Cavalry are one of the most "
    "memorable units in the game, combining speed, hitting power, and presence "
    "in a way few other kits match.\n\n"
    "The hobby is rich with character. Wolf pelts, runestones, axes, and "
    "the distinctive grey-blue armour make Space Wolves immediately recognisable "
    "on any table. Converting heads and adding Viking-inspired details is a "
    "natural part of the hobby for most collectors. The faction attracts "
    "painters who enjoy telling a story through their models.\n\n"
    "Deals below update daily from US retailers. The Combat Patrol and Grey "
    "Hunters box are the strongest starting points for building the core of "
    "a Fenrisian warband."
)

TAU_SYNOPSIS = (
    "The T'au Empire are a relatively young but technologically advanced "
    "civilization built around the philosophy of the Greater Good, a collective "
    "ideal that binds humans, T'au, and allied species together. On the "
    "tabletop they are a long-range shooting army with a strong emphasis on "
    "vehicles, battlesuits, and supporting fire mechanics.\n\n"
    "The faction rewards methodical players who understand range control and "
    "fire arc positioning. Crisis Battlesuits are the heart of most lists, "
    "customisable platforms that can be built for almost any role. Hammerheads "
    "and Devilfish provide vehicle support, while Kroot infantry offer cheap "
    "objective holding.\n\n"
    "Building a T'au army gives painters a distinctive canvas. Sleek armour "
    "panels, advanced weapons, and sept markings create a very different "
    "visual language from the gothic aesthetic of Imperial forces. The "
    "battlesuits lend themselves well to both speed painting and display "
    "quality work.\n\n"
    "Prices below are tracked daily from US retailers. Crisis Battlesuits "
    "and the Combat Patrol are the best entry-level purchases to watch for "
    "savings before you start your sept."
)

THOUSAND_SONS_SYNOPSIS = (
    "The Thousand Sons are the sorcerous warriors of Tzeentch, a Legion of "
    "Chaos Space Marines whose bodies were consumed by mutation and whose "
    "mortal warriors were trapped in their armour as Rubric Marines, immortal "
    "automata sustained only by the will of their Sorcerer masters. They are "
    "among the most visually striking and thematically rich factions in the game.\n\n"
    "On the tabletop they are a psychic shooting army built around Sorcerers "
    "and Rubric Marines. The faction leans on mortal wounds dealt at range "
    "through psychic powers, with Scarab Occult Terminators providing "
    "durable elite support. Managing psychic actions and powers while "
    "advancing is the central challenge the army presents.\n\n"
    "Painting Thousand Sons is one of the hobby's signature projects. "
    "Electric blue armour, gold trim, and arcane iconography across every "
    "surface make for a complex but deeply rewarding scheme. The models "
    "reward patience and contrast between armour and metal, and the end "
    "result is always a centrepiece army.\n\n"
    "Deals below are updated daily from US retailers. Rubric Marines are "
    "the core infantry to watch for discounts, as you will want multiple "
    "squads to fill a competitive list."
)

TYRANIDS_SYNOPSIS = (
    "The Tyranids are a vast extragalactic swarm, a consuming force of alien "
    "biology that has stripped entire star systems of all organic matter. "
    "They have no individual ambition, no politics, and no mercy — only "
    "the endless hunger of the Hive Mind driving them forward. On the "
    "tabletop they play as a horde faction with exceptional synergy, "
    "combining fast melee units with monstrous creatures and swarm infantry "
    "into a wave of biological fury.\n\n"
    "Hormagaunts and Termagants form the expendable core of most lists, "
    "soaking fire while Carnifexes, Hive Tyrants, and the Norn Emissary "
    "deliver serious threat. The faction suits aggressive players who "
    "enjoy overwhelming opponents through volume and pressure.\n\n"
    "Painting a Tyranid army is one of the most scalable projects in the hobby. "
    "Speed techniques like dipping, drybrushing, and contrast paints work "
    "brilliantly on the organic forms, and the faction has been among the "
    "biggest beneficiaries of modern painting shortcuts. The creative range "
    "of colour schemes is extraordinary.\n\n"
    "Prices below are tracked daily from US retailers. Hormagaunts and "
    "Termagants are the kits to watch for the deepest savings, given "
    "how many you will need to fill your swarm."
)

ULTRAMARINES_SYNOPSIS = (
    "The Ultramarines are the largest and most celebrated Space Marine Chapter, "
    "the poster faction of Warhammer 40,000 and the model for what a Space "
    "Marine Chapter should be. Led by Roboute Guilliman, the Primarch returned, "
    "they are a disciplined, well-rounded army with access to the full Space "
    "Marine roster plus unique Ultramarines units and rules.\n\n"
    "On the tabletop they are one of the most flexible and beginner-friendly "
    "armies in the game. The full Primaris range is available, Guilliman himself "
    "is one of the strongest single model choices in the faction, and the "
    "Chapter's focus on combat doctrine gives them strong performance across "
    "multiple phases without needing specialist builds.\n\n"
    "For new hobbyists, Ultramarines are the natural starting point. Ultramarine "
    "blue is iconic, tutorials are everywhere, and the army is forgiving enough "
    "to learn with. Veterans who return to the hobby often start here again "
    "before branching into other Chapters.\n\n"
    "Prices below update daily from US retailers. The Combat Patrol and "
    "Intercessors are the best entry kits to watch for discounts as you "
    "build your XIII Legion."
)

WORLD_EATERS_SYNOPSIS = (
    "The World Eaters are the warriors of Khorne, the Blood God, a Legion "
    "consumed entirely by rage and the desire to kill in close combat. "
    "They are the most straightforward Chaos faction in terms of purpose: "
    "close the distance as fast as possible and destroy everything in melee. "
    "There is no subtlety here, and that is exactly the point.\n\n"
    "On the tabletop they are one of the most aggressive armies in the game. "
    "Jakhals and Berzerkers form a fast melee core, Angron himself is one "
    "of the most powerful and dangerous Daemon Primarchs available, and "
    "the faction's rules reward committing fully to assault rather than "
    "hedging toward a mixed strategy. Against unprepared opponents, a "
    "World Eaters charge can end a game in two turns.\n\n"
    "The hobby side matches the playstyle. Blood, brass, and bone-white "
    "armour tell the story clearly, and the models carry that brutality in "
    "every sculpt. Berzerkers especially are among the most dynamic "
    "infantry kits in the modern range.\n\n"
    "Prices below are tracked daily from US retailers. Berzerkers are "
    "the core purchase to watch for savings — you will want plenty of them."
)


FACTIONS = [
    {
        'name': 'Sisters of Battle',
        'hero_tagline': "Faith is Their Shield. Compare Prices on Every Sisters of Battle Kit.",
        'synopsis': SISTERS_SYNOPSIS,
        'difficulty': 'Intermediate',
        'model_count_rating': 'Medium',
        'painting_complexity': 'High',
        'playstyle': 'Faith-Powered Shooting',
        'price_range_display': '$$$',
        'tag_name': 'Sisters of Battle',
    },
    {
        'name': 'Space Marines',
        'hero_tagline': "For the Emperor. Find the Best Prices on Every Space Marines Kit.",
        'synopsis': SPACE_MARINES_SYNOPSIS,
        'difficulty': 'Beginner Friendly',
        'model_count_rating': 'Medium',
        'painting_complexity': 'Easy',
        'playstyle': 'Balanced All-Rounder',
        'price_range_display': '$$',
        'tag_name': 'Space Marines',
    },
    {
        'name': 'Space Wolves',
        'hero_tagline': "For Russ and the Allfather. Find the Best Prices on Space Wolves Kits.",
        'synopsis': SPACE_WOLVES_SYNOPSIS,
        'difficulty': 'Intermediate',
        'model_count_rating': 'Low-Medium',
        'painting_complexity': 'Medium',
        'playstyle': 'Aggressive Melee',
        'price_range_display': '$$',
        'tag_name': 'Space Wolves',
    },
    {
        'name': "T'au Empire",
        'hero_tagline': "For the Greater Good. Track Every T'au Kit at the Best Price.",
        'synopsis': TAU_SYNOPSIS,
        'difficulty': 'Intermediate',
        'model_count_rating': 'Low-Medium',
        'painting_complexity': 'Easy-Medium',
        'playstyle': 'Long-Range Shooting',
        'price_range_display': '$$$',
        'tag_name': "T'au Empire",
    },
    {
        'name': 'Thousand Sons',
        'hero_tagline': "All is Dust. Compare Prices on Every Thousand Sons Kit.",
        'synopsis': THOUSAND_SONS_SYNOPSIS,
        'difficulty': 'Advanced',
        'model_count_rating': 'Low',
        'painting_complexity': 'High',
        'playstyle': 'Psychic Shooting',
        'price_range_display': '$$$',
        'tag_name': 'Thousand Sons',
    },
    {
        'name': 'Tyranids',
        'hero_tagline': "The Hive Mind Hungers. Find the Best Prices on Every Tyranids Kit.",
        'synopsis': TYRANIDS_SYNOPSIS,
        'difficulty': 'Intermediate',
        'model_count_rating': 'Very High',
        'painting_complexity': 'Easy',
        'playstyle': 'Horde Assault',
        'price_range_display': '$$',
        'tag_name': 'Tyranids',
    },
    {
        'name': 'Ultramarines',
        'hero_tagline': "Courage and Honour. Find the Best Prices on Every Ultramarines Kit.",
        'synopsis': ULTRAMARINES_SYNOPSIS,
        'difficulty': 'Beginner Friendly',
        'model_count_rating': 'Medium',
        'painting_complexity': 'Easy',
        'playstyle': 'Balanced All-Rounder',
        'price_range_display': '$$',
        'tag_name': 'Ultramarines',
    },
    {
        'name': 'World Eaters',
        'hero_tagline': "Blood for the Blood God. Compare Prices on Every World Eaters Kit.",
        'synopsis': WORLD_EATERS_SYNOPSIS,
        'difficulty': 'Beginner Friendly',
        'model_count_rating': 'Medium',
        'painting_complexity': 'Easy-Medium',
        'playstyle': 'All-In Melee',
        'price_range_display': '$$',
        'tag_name': 'World Eaters',
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
            defaults={'slug': data['tag_name'].lower().replace(' ', '-').replace("'", '')},
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
    dependencies = [('products', '0021_grey_knights_synopsis_fix')]
    operations = [migrations.RunPython(populate, depopulate)]
