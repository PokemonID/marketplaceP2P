# Generated by Django 4.2.5 on 2023-12-13 11:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testsite', '0026_alter_pccntr_opertypes_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orders',
            name='ReceiveAmount',
            field=models.IntegerField(blank=True, verbose_name='Сумма получаемой валюты'),
        ),
        migrations.AlterField(
            model_name='orders',
            name='SendAmount',
            field=models.IntegerField(blank=True, verbose_name='Сумма отдаваемой валюты'),
        ),
    ]
