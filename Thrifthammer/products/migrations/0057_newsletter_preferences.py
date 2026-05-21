# Generated 2026-05-20
#
# Adds newsletter preference fields to NewsletterSignup:
#   - is_confirmed  (default True — existing 27 subscribers automatically confirmed)
#   - monday_40k    (default True  — Monday Warhammer 40K digest)
#   - friday_other  (default True  — Friday AoS & Other digest)
#   - sunday_faction (default False — Sunday personalised faction digest, opt-in only)
#   - factions       M2M to Faction — which factions to include in Sunday email
#   - user           optional OneToOneField to User — linked account

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0056_add_global_neg_keywords_may2026c'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='newslettersignup',
            name='is_confirmed',
            field=models.BooleanField(
                default=True,
                help_text=(
                    'Email address confirmed via opt-in link. '
                    'Existing subscribers are set True by default so they are unaffected. '
                    'New homepage signups start False until the confirmation link is clicked.'
                ),
            ),
        ),
        migrations.AddField(
            model_name='newslettersignup',
            name='monday_40k',
            field=models.BooleanField(
                default=True,
                help_text='Receive the Monday Warhammer 40K deal digest.',
            ),
        ),
        migrations.AddField(
            model_name='newslettersignup',
            name='friday_other',
            field=models.BooleanField(
                default=True,
                help_text='Receive the Friday Age of Sigmar & Other deal digest.',
            ),
        ),
        migrations.AddField(
            model_name='newslettersignup',
            name='sunday_faction',
            field=models.BooleanField(
                default=False,
                help_text=(
                    'Receive a Sunday personalised faction deal digest. '
                    'Subscribers must also select at least one faction below.'
                ),
            ),
        ),
        migrations.AddField(
            model_name='newslettersignup',
            name='factions',
            field=models.ManyToManyField(
                blank=True,
                help_text='Factions to include in the Sunday personalised email.',
                related_name='newsletter_subscribers',
                to='products.faction',
            ),
        ),
        migrations.AddField(
            model_name='newslettersignup',
            name='user',
            field=models.OneToOneField(
                blank=True,
                help_text='Linked user account, if the subscriber has created one.',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='newsletter_signup',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
