# Generated by Django 4.2.5 on 2023-12-22 17:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testsite', '0034_rename_opertype_requests_exchangeid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='requests',
            name='TG_Contact',
            field=models.CharField(max_length=255, verbose_name='Имя пользователя'),
        ),
    ]
