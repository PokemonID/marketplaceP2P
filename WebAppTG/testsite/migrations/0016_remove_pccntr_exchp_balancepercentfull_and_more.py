# Generated by Django 4.2.5 on 2023-10-15 17:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testsite', '0015_pccntr_exchp_balancefull_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pccntr_exchp',
            name='balancePercentFull',
        ),
        migrations.AddField(
            model_name='pccntr_exchp',
            name='bonusPercentFull',
            field=models.IntegerField(blank=True, default=0, verbose_name='Бонус'),
        ),
        migrations.AlterField(
            model_name='pccntr_exchp',
            name='balanceFull',
            field=models.IntegerField(blank=True, default=0, verbose_name='Баланс'),
        ),
    ]