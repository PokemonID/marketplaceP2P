# Generated by Django 4.2.5 on 2023-12-22 17:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('testsite', '0037_rename_status_id_requests_status_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Requests',
        ),
    ]
