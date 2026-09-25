from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0018_appointment_keycrm_card_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='PriceListSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated_on', models.DateField(default=django.utils.timezone.localdate, verbose_name='Ціни актуальні на')),
            ],
            options={
                'verbose_name': 'Дата прайсу',
                'verbose_name_plural': 'Дата прайсу',
            },
        ),
    ]
