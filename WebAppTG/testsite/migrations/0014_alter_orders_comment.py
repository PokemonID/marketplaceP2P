# Generated by Django 4.2.5 on 2023-10-15 16:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testsite', '0013_finofficefrom_orders'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orders',
            name='Comment',
            field=models.CharField(blank=True, max_length=10000, verbose_name='Комментарий'),
        ),
    ]