from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0019_pricelistsettings'),
    ]

    operations = [
        migrations.AddField(
            model_name='pricelistsettings',
            name='use_today',
            field=models.BooleanField(default=False, verbose_name='Показувати сьогоднішню дату'),
        ),
    ]
