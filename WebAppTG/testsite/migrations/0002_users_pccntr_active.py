# Generated by Django 4.2.5 on 2023-10-01 19:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testsite', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='users_pccntr',
            name='ACTIVE',
            field=models.IntegerField(blank=True, default=1, verbose_name='Статус пользователя'),
        ),
    ]
