# Generated by Django 4.2.5 on 2024-05-27 15:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testsite', '0044_feedback_page'),
    ]

    operations = [
        migrations.CreateModel(
            name='Currency_source',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('OperType', models.CharField(max_length=255, verbose_name='Направление сделки')),
                ('FinOfficeFrom', models.CharField(blank=True, max_length=255, verbose_name='Тип отправления')),
                ('FinOfficeTo', models.CharField(blank=True, max_length=255, verbose_name='Тип получения')),
                ('SendTransferType', models.CharField(blank=True, max_length=255, verbose_name='Тип отправляемой валюты')),
                ('ReceiveTransferType', models.CharField(blank=True, max_length=255, verbose_name='Тип получаемой валюты')),
                ('QuotesRC', models.CharField(max_length=255, verbose_name='Источник котировок')),
                ('Value', models.IntegerField(verbose_name='Курс валют')),
            ],
            options={
                'verbose_name': 'Курс валют',
                'verbose_name_plural': 'Курсы валют',
                'ordering': ['OperType'],
            },
        ),
    ]
