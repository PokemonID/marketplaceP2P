# Generated by Django 4.2.5 on 2023-11-13 23:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('testsite', '0019_remove_pccntr_exchp_exchangepointaddress_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pccntr_exchp',
            name='ContactType',
        ),
    ]
