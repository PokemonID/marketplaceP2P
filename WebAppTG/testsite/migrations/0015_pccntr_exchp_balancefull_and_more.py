# Generated by Django 4.2.5 on 2023-10-15 16:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testsite', '0014_alter_orders_comment'),
    ]

    operations = [
        migrations.AddField(
            model_name='pccntr_exchp',
            name='balanceFull',
            field=models.CharField(blank=True, max_length=255, verbose_name='Баланс'),
        ),
        migrations.AddField(
            model_name='pccntr_exchp',
            name='balancePercentFull',
            field=models.CharField(blank=True, max_length=255, verbose_name='Бонус'),
        ),
    ]