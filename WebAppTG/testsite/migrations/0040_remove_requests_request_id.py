# Generated by Django 4.2.5 on 2023-12-22 17:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('testsite', '0039_requests'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='requests',
            name='request_id',
        ),
    ]
