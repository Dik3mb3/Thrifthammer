"""
Data migration: populate Adeptus Custodes faction page content.

Keeps the existing slug ('custodes') to avoid conflicts with the
separate 'Adeptus Custodes' faction that populate_products seeds.
Faction page is live at /factions/custodes/.
"""

from django.db import migrations


def populate_custodes_faction(apps, schema_editor):
    """Set all faction page fields for the Custodes faction."""
    Faction = apps.get_model('products', 'Faction')
    Tag = apps.get_model('blog', 'Tag')
    Post = apps.get_model('blog', 'Post')

    # Ensure the Adeptus Custodes blog tag exists
    tag, _ = Tag.objects.get_or_create(
        slug='adeptus-custodes',
        defaults={'name': 'Adeptus Custodes'},
    )

    # Tag the starter armies post if it exists
    try:
        post = Post.objects.get(slug='best-starter-warhammer-40k-armies-2026')
        post.tags.add(tag)
    except Post.DoesNotExist:
        pass

    # Update the Custodes faction — slug stays as 'custodes'
    Faction.objects.filter(name='Custodes').update(
        hero_tagline="The Emperor's Elite. Find the Best Prices on Every Kit.",
        difficulty='Beginner Friendly',
        model_count_rating='Low (20-40 models)',
        painting_complexity='Easy-Medium',
        playstyle='Melee Elite',
        price_range_display='$-$$$',
        synopsis=(
            "Adeptus Custodes are the Emperor's personal bodyguard, standing watch "
            "over the Golden Throne since the days of the Great Crusade. On the "
            "tabletop, they are the definition of elite: a full 2,000-point army "
            "fits comfortably in 20 to 40 models, meaning less time building and "
            "painting, and more time actually playing.\n\n"
            "Custodes are one of the most forgiving factions for new players. The "
            "unit count is low, the rules are straightforward, and the stat lines "
            "are resilient enough that early mistakes rarely spiral into losses. "
            "A single Custodian Guard is worth three Space Marines on paper. "
            "Every model matters.\n\n"
            "The playstyle is melee-focused and aggressive. Custodes reward players "
            "who push forward, pick targets carefully, and use the army's "
            "exceptional durability to weather return fire. They are not a horde "
            "army. They are not a shooting army. They are warriors who hit hard "
            "and hit precisely.\n\n"
            "The deals below are tracked daily across US retailers. Stop paying "
            "Games Workshop's full retail price."
        ),
        blog_tag_id=tag.pk,
    )


def reverse_custodes_faction(apps, schema_editor):
    """Clear faction page fields."""
    Faction = apps.get_model('products', 'Faction')
    Faction.objects.filter(name='Custodes').update(
        hero_tagline='',
        difficulty='',
        model_count_rating='',
        painting_complexity='',
        playstyle='',
        price_range_display='',
        synopsis='',
        blog_tag_id=None,
    )


class Migration(migrations.Migration):
    """Populate Adeptus Custodes faction page data."""

    dependencies = [
        ('blog', '0002_comment'),
        ('products', '0011_faction_page_fields'),
    ]

    operations = [
        migrations.RunPython(
            populate_custodes_faction,
            reverse_custodes_faction,
        ),
    ]
