# Generated by Django 4.2.5 on 2023-10-07 19:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testsite', '0009_exchangeid_alter_pccntr_exchp_options'),
    ]

    operations = [
        migrations.CreateModel(
            name='EP_ExchangeID',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('PCCNTR', models.CharField(max_length=255, verbose_name='Центр прибыли и затрат')),
                ('ExchangePointID', models.CharField(max_length=255, verbose_name='ID обменника')),
                ('ExchangePointCountry', models.CharField(max_length=255, verbose_name='Страна')),
                ('ExchangePointCity', models.CharField(max_length=10000, verbose_name='Город')),
                ('ExchangeTransferID', models.CharField(max_length=10000, verbose_name='Тип сделки')),
                ('ExchTOAmount_Min', models.IntegerField(blank=True, verbose_name='Минимальная сумма сделки')),
                ('ExchTOAmount_Max', models.IntegerField(blank=True, verbose_name='Максимальная сумма сделки')),
                ('EP_PRFTNORM', models.CharField(max_length=20000, verbose_name='Нормы прибыли')),
            ],
            options={
                'verbose_name': 'Обменник и направления сделки',
                'verbose_name_plural': 'Обменники и направления сделки',
                'ordering': ['PCCNTR', 'ExchangePointID'],
            },
        ),
        migrations.CreateModel(
            name='PCCNTR_OperTypes',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('PCCNTR_Code', models.CharField(max_length=255, verbose_name='Код Центра прибыли и затрат')),
                ('PCCNTR_Name', models.CharField(max_length=255, verbose_name='Наименование Центра прибыли и затрат')),
                ('OperType', models.CharField(max_length=255, verbose_name='Направление сделки')),
            ],
            options={
                'verbose_name': 'Центр прибыли и затрат и направления сделки',
                'verbose_name_plural': 'Центры прибыли и затрат и направления сделки',
                'ordering': ['PCCNTR_Code'],
            },
        ),
    ]
