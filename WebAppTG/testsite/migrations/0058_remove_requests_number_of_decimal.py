# Generated by Django 4.2.5 on 2024-08-10 20:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('testsite', '0057_requests_finofficefrom'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='requests',
            name='number_of_decimal',
        ),
    ]