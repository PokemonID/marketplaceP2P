# Generated by Django 4.2.5 on 2023-12-22 17:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testsite', '0035_alter_requests_tg_contact'),
    ]

    operations = [
        migrations.AlterField(
            model_name='requests',
            name='ExchangePointID',
            field=models.CharField(blank=True, max_length=255, verbose_name='ID обменника'),
        ),
    ]