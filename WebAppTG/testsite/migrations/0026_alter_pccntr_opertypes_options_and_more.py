# Generated by Django 4.2.5 on 2023-12-09 18:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('testsite', '0025_pccntr_opertypes_bank'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='pccntr_opertypes',
            options={'ordering': ['PCCNTR'], 'verbose_name': 'Центр прибыли и затрат и направления сделки', 'verbose_name_plural': 'Центры прибыли и затрат и направления сделки'},
        ),
        migrations.RenameField(
            model_name='pccntr_opertypes',
            old_name='PCCNTR_Code',
            new_name='PCCNTR',
        ),
    ]
