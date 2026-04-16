from django.db import migrations, models
import django.db.models.constraints
from django.db.models import Q


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0004_userlibrary_saved_words'),
    ]

    operations = [
        migrations.AddField(
            model_name='novel',
            name='hero_slot',
            field=models.PositiveSmallIntegerField(
                blank=True,
                choices=[(1, 'Hero Slot 1'), (2, 'Hero Slot 2'), (3, 'Hero Slot 3')],
                help_text='Select a homepage hero slot for this novel.',
                null=True,
            ),
        ),
        migrations.AddConstraint(
            model_name='novel',
            constraint=django.db.models.constraints.UniqueConstraint(
                condition=Q(hero_slot__isnull=False),
                fields=('hero_slot',),
                name='unique_hero_slot_when_set',
            ),
        ),
    ]
