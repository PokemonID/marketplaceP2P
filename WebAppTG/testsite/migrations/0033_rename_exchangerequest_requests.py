# Generated by Django 4.2.5 on 2023-12-22 15:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('testsite', '0032_rename_profit_centers_exchangerequest_pccntr_and_more'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='ExchangeRequest',
            new_name='Requests',
        ),
    ]
