# Generated by Django 4.2.5 on 2024-02-17 06:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('testsite', '0041_remove_balance_exchangepointid_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='balance',
            old_name='balance_Amount',
            new_name='Balance_Amount',
        ),
    ]
