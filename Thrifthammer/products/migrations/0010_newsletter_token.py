import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    """Add unsubscribe token to NewsletterSignup."""

    dependencies = [
        ('products', '0009_faction_parent_faction'),
    ]

    operations = [
        migrations.AddField(
            model_name='newslettersignup',
            name='token',
            field=models.UUIDField(
                default=uuid.uuid4,
                unique=True,
                editable=False,
                help_text='Unique token used to generate a one-click unsubscribe link.',
            ),
        ),
    ]
