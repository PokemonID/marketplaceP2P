# Generated by Django 4.2.5 on 2024-02-17 06:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('testsite', '0042_rename_balance_amount_balance_balance_amount'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pccntr_exchp',
            name='ExchangePointDeals',
        ),
    ]