# Generated by Django 4.2.5 on 2024-08-05 11:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testsite', '0047_currency_source_bank'),
    ]

    operations = [
        migrations.AddField(
            model_name='exchangeid',
            name='FinOfficeFrom',
            field=models.CharField(blank=True, max_length=255, verbose_name='Тип финансового учреждения (продажа)'),
        ),
        migrations.AddField(
            model_name='exchangeid',
            name='FinOfficeTo',
            field=models.CharField(blank=True, max_length=255, verbose_name='Тип финансового учреждения (покупка)'),
        ),
        migrations.AddField(
            model_name='exchangeid',
            name='OperTypes',
            field=models.CharField(blank=True, max_length=10000, verbose_name='Типы операций'),
        ),
        migrations.AlterField(
            model_name='exchangeid',
            name='ReceiveCurrencyISO',
            field=models.CharField(blank=True, max_length=255, verbose_name='Наименование получаемой валюты'),
        ),
        migrations.AlterField(
            model_name='exchangeid',
            name='ReceiveTransferType',
            field=models.CharField(blank=True, max_length=255, verbose_name='Тип получаемой валюты'),
        ),
        migrations.AlterField(
            model_name='exchangeid',
            name='SendCurrencyISO',
            field=models.CharField(blank=True, max_length=255, verbose_name='Наименование отправляемой валюты'),
        ),
        migrations.AlterField(
            model_name='exchangeid',
            name='SendTransferType',
            field=models.CharField(blank=True, max_length=255, verbose_name='Тип отправляемой валюты'),
        ),
        migrations.AlterField(
            model_name='exchangeid',
            name='TransferTypes',
            field=models.CharField(blank=True, max_length=10000, verbose_name='Типы платежей (переводов)'),
        ),
    ]
