"""
Migration 0019 — Faction page data for Deathwatch, Drukhari, Genestealer Cults,
Grey Knights, Imperial Knights, Necrons, Orks.
"""

from django.db import migrations


DEATHWATCH_SYNOPSIS = (
    "The Deathwatch are the Chamber Militant of the Ordo Xenos, a secretive order "
    "of Space Marines drawn from every Chapter across the Imperium and united in a "
    "single purpose: the destruction of alien threats. Each warrior brings the "
    "expertise of their home Chapter, making the Deathwatch uniquely flexible at "
    "the squad level.\n\n"
    "On the tabletop they are a low model count, high quality elite army. Kill "
    "Teams and Veterans form the core, each loadout able to specialise against "
    "specific target types. The faction rewards players who study their opponent "
    "and build their squad configurations accordingly, rather than running a "
    "fixed list game after game.\n\n"
    "The hobby appeal is strong. Black armour with silver trim is fast to paint "
    "to a sharp standard, and the freedom to incorporate shoulder pads and details "
    "from any Chapter makes every squad a creative project. Building a squad that "
    "pulls from five different Chapters is as rewarding as the painting itself.\n\n"
    "The deals below are tracked daily from US retailers. With a small model count, "
    "the per-kit investment matters more than in larger armies. Finding even a "
    "modest discount on Veterans or a Corvus Blackstar makes a real difference."
)

DRUKHARI_SYNOPSIS = (
    "The Drukhari, also known as the Dark Eldar, are raiders from the shadowed "
    "city of Commorragh, corsairs who feed on the suffering of others to sustain "
    "their immortal lives. On the tabletop they are one of the fastest and most "
    "aggressive factions in the game, built around lightning-fast transports, "
    "precise strike-and-withdraw tactics, and poisoned weapons that bypass armour.\n\n"
    "Playing Drukhari well requires a deep understanding of priority and timing. "
    "Units hit hard and move fast, but they are fragile when caught in the open. "
    "The faction rewards experienced players who can read the board several turns "
    "ahead and find angles their opponent has not anticipated.\n\n"
    "The models are visually striking, combining alien elegance with grotesque "
    "cruelty in a way that stands out from every other army in the hobby. Sharp "
    "edges, skeletal frames, and excessive spikes make Drukhari a painter's "
    "challenge that pays off when done well.\n\n"
    "Prices below are updated daily from US retailers. Raiders and Kabalite "
    "Warriors are the foundation of most lists, and both are worth tracking for "
    "discounts before you commit to building your raiding party."
)

GENESTEALER_CULTS_SYNOPSIS = (
    "Genestealer Cults are the vanguard of a Tyranid invasion, hybrids of human "
    "and xenos biology who infiltrate planetary populations and prepare the way for "
    "the Great Devourer. On the tabletop they are a uniquely subversive faction, "
    "built around ambush mechanics, units appearing from unexpected directions, "
    "and a core of fanatical infantry supported by industrial mining equipment "
    "repurposed as weapons of war.\n\n"
    "The faction demands forward planning. Abilities like Cult Ambush and the "
    "Bladed Cog or Four Armed Emperor subfaction rules create layers of decision "
    "making that reward players who invest time in understanding the army. The "
    "payoff is a playstyle unlike anything else in the game.\n\n"
    "Hobby-wise the Cults offer range. Human Neophytes and Acolytes blend "
    "industrial worker aesthetic with xenos mutation, while Aberrants and Patriarch "
    "models carry enough visual drama to anchor any display army. The palette is "
    "flexible, from grimy worker overalls to vivid alien skin.\n\n"
    "Prices below are tracked daily across US retailers. Neophytes and the "
    "Atalan Jackals are the best starting points for building the core of a Cult."
)

GREY_KNIGHTS_SYNOPSIS = (
    "The Grey Knights are the secret weapon of the Imperium, a Chapter of Space "
    "Marines who are also potent psykers, trained and equipped to fight the "
    "daemonic forces of Chaos. Every warrior is a powerful warrior and a battle-"
    "hardened psychic fighter, making them among the most individually capable "
    "units in the entire game.\n\n"
    "On the tabletop they are an elite low model count army built around powerful "
    "psyker abilities and durable Terminator and Power Armour infantry. The faction "
    "punishes daemon and Chaos armies especially hard, but holds its own across "
    "the board through sheer resilience and output per model. Expect to field fewer "
    "units than almost any other army in the game.\n\n"
    "The silver armour scheme is one of the most iconic in the hobby. Metallic "
    "plate, force weapons crackling with psychic energy, and ornate scrollwork "
    "reward careful attention to highlighting and object source lighting. A fully "
    "painted Grey Knights force is always impressive on the table.\n\n"
    "Deals below are pulled daily from US retailers. With a small roster, each "
    "kit purchase counts. Discounts on Terminators or Strike Squads represent "
    "a meaningful saving across the whole army."
)

IMPERIAL_KNIGHTS_SYNOPSIS = (
    "Imperial Knights are towering war machines pledged to the service of the "
    "Imperium, armoured behemoths that stride across the battlefield and deliver "
    "devastating firepower and melee strikes. An Imperial Knights army consists "
    "almost entirely of these massive walkers, supported by a small number of "
    "Armiger-class outriders.\n\n"
    "On the tabletop this means one of the most unique experiences in Warhammer "
    "40,000. You field a handful of models, each one a significant centrepiece, "
    "and win by making every Knight count. The faction suits players who enjoy "
    "a cinematic, big-impact playstyle rather than managing large numbers of units.\n\n"
    "From a hobby perspective, Imperial Knights are among the most rewarding "
    "projects in the game. Each kit is large, detailed, and fully posable, offering "
    "real scope for converting and personalising your war machine. Painting a "
    "single Knight to a high standard is a satisfying project in itself, and a "
    "full household across a display shelf is a serious achievement.\n\n"
    "Prices below update daily from US retailers. Knights are expensive kits at "
    "retail, which makes tracking discounts here particularly worthwhile before "
    "you buy your next war engine."
)

NECRONS_SYNOPSIS = (
    "The Necrons are ancient beyond measure, a race of undying mechanical warriors "
    "who slumbered in their tomb worlds for millions of years and have now risen "
    "to reclaim a galaxy they regard as rightfully theirs. On the tabletop they "
    "are a durable mid-range army defined by their Reanimation Protocols, the "
    "ability to bring models back from the dead that makes them frustratingly "
    "resilient to opponents.\n\n"
    "The faction plays as a methodical advance army. Warriors and Immortals form "
    "a rock-solid core, Canoptek constructs provide utility and board control, "
    "while the C'tan Shards offer powerful, unpredictable special abilities. "
    "The faction suits players who enjoy attrition and controlling space over "
    "time, rather than high-speed burst damage.\n\n"
    "Necrons are among the best factions for new painters. The models are "
    "predominantly metal and bone, which means a few key colours and a wash go "
    "a long way. Contrast paints have made the core infantry quicker than ever "
    "to bring to a strong tabletop standard.\n\n"
    "Deals below are tracked daily from US retailers. Necron Warriors and "
    "Immortals are the best kits to watch for discounts, given how many you "
    "will need for a full army."
)

ORKS_SYNOPSIS = (
    "The Orks are the most numerous and belligerent species in the galaxy, a "
    "race of warlike aliens who exist for one purpose: to fight. On the tabletop "
    "they are a horde army defined by sheer volume of bodies, brutal melee "
    "capability, and a chaotic energy that makes them unpredictable for opponents "
    "to face.\n\n"
    "Building an Orks army means embracing quantity. Boyz form the backbone "
    "of most lists, with Nobz, Meganobz, and vehicles like the Battlewagon "
    "providing the heavy hitting. The faction rewards players who press forward "
    "relentlessly and use their numbers to overwhelm before the opponent can "
    "react. It is not a subtle army.\n\n"
    "Orks are one of the best factions in the hobby for creative freedom. "
    "Conversions, scratch-built vehicles, and wild colour schemes are not just "
    "accepted but expected. The models carry enormous character, and no two "
    "Ork collections ever look quite the same. Speed painting with contrast "
    "paints and washes produces great results fast, which matters when you are "
    "painting dozens of Boyz.\n\n"
    "Prices below are updated daily from US retailers. Boyz are the single "
    "most important kit to find at a discount, and the savings across four or "
    "five boxes add up fast."
)


FACTIONS = [
    {
        'name': 'Deathwatch',
        'hero_tagline': "Every Alien. One Purpose. Find the Best Prices on Deathwatch Kits.",
        'synopsis': DEATHWATCH_SYNOPSIS,
        'difficulty': 'Intermediate',
        'model_count_rating': 'Low',
        'painting_complexity': 'Easy-Medium',
        'playstyle': 'Elite Strike Force',
        'price_range_display': '$$',
        'tag_name': 'Deathwatch',
    },
    {
        'name': 'Drukhari',
        'hero_tagline': "Pain is Power. Compare Prices on Every Drukhari Kit.",
        'synopsis': DRUKHARI_SYNOPSIS,
        'difficulty': 'Advanced',
        'model_count_rating': 'Medium',
        'painting_complexity': 'Medium-High',
        'playstyle': 'Lightning Raids',
        'price_range_display': '$$',
        'tag_name': 'Drukhari',
    },
    {
        'name': 'Genestealer Cults',
        'hero_tagline': "The Cult Rises. Track Down the Best Prices on Every Kit.",
        'synopsis': GENESTEALER_CULTS_SYNOPSIS,
        'difficulty': 'Advanced',
        'model_count_rating': 'Medium-High',
        'painting_complexity': 'Medium',
        'playstyle': 'Ambush',
        'price_range_display': '$$',
        'tag_name': 'Genestealer Cults',
    },
    {
        'name': 'Grey Knights',
        'hero_tagline': "Humanity's Finest Weapon. Find the Best Deals on Grey Knights.",
        'synopsis': GREY_KNIGHTS_SYNOPSIS,
        'difficulty': 'Intermediate',
        'model_count_rating': 'Low',
        'painting_complexity': 'Medium-High',
        'playstyle': 'Psychic Elite',
        'price_range_display': '$$$',
        'tag_name': 'Grey Knights',
    },
    {
        'name': 'Imperial Knights',
        'hero_tagline': "Honour Imperialis. Track Every Imperial Knights Kit at the Best Price.",
        'synopsis': IMPERIAL_KNIGHTS_SYNOPSIS,
        'difficulty': 'Beginner Friendly',
        'model_count_rating': 'Very Low',
        'painting_complexity': 'High',
        'playstyle': 'Titanic Firepower',
        'price_range_display': '$$$$$',
        'tag_name': 'Imperial Knights',
    },
    {
        'name': 'Necrons',
        'hero_tagline': "We Have Awakened. Find the Best Prices on Every Necrons Kit.",
        'synopsis': NECRONS_SYNOPSIS,
        'difficulty': 'Beginner Friendly',
        'model_count_rating': 'Medium',
        'painting_complexity': 'Easy',
        'playstyle': 'Durable Attrition',
        'price_range_display': '$$',
        'tag_name': 'Necrons',
    },
    {
        'name': 'Orks',
        'hero_tagline': "Waaagh! Compare Prices on Every Orks Kit Before You Buy.",
        'synopsis': ORKS_SYNOPSIS,
        'difficulty': 'Beginner Friendly',
        'model_count_rating': 'Very High',
        'painting_complexity': 'Easy',
        'playstyle': 'Horde Melee',
        'price_range_display': '$',
        'tag_name': 'Orks',
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
    dependencies = [('products', '0018_faction_stats_corrections2')]
    operations = [migrations.RunPython(populate, depopulate)]
