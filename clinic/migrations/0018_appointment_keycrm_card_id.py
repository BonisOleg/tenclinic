from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0017_delete_homeaboutussettings'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='keycrm_card_id',
            field=models.PositiveIntegerField(
                blank=True,
                null=True,
                unique=True,
                verbose_name='KeyCRM картка',
            ),
        ),
    ]
