from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0002_comment'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='author',
            field=models.CharField(
                blank=True,
                default='ThriftHammer',
                help_text='Author display name shown on cards and articles. Defaults to "ThriftHammer".',
                max_length=100,
            ),
        ),
    ]
