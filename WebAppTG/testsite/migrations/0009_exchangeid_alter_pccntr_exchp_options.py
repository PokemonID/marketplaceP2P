# Generated by Django 4.2.5 on 2023-10-07 16:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testsite', '0008_pccntr_exchp'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExchangeID',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ExchID', models.CharField(max_length=255, verbose_name='ID обменника')),
                ('Name_RUS', models.CharField(max_length=255, verbose_name='Наименования направления обмена (RUS)')),
                ('Name_ENG', models.CharField(blank=True, max_length=255, verbose_name='Наименования направления обмена (ENG)')),
                ('Name_DEU', models.CharField(blank=True, max_length=255, verbose_name='Наименования направления обмена (DEU)')),
                ('Name_SRB', models.CharField(blank=True, max_length=255, verbose_name='Наименования направления обмена (SRB)')),
                ('TransferTypes', models.CharField(max_length=10000, verbose_name='Типы платежей (переводов)')),
                ('SendTransferType', models.CharField(max_length=255, verbose_name='Тип отправляемой валюты')),
                ('ReceiveTransferType', models.CharField(max_length=255, verbose_name='Тип получаемой валюты')),
                ('SendCurrencyISO', models.CharField(max_length=255, verbose_name='Наименование отправляемой валюты')),
                ('ReceiveCurrencyISO', models.CharField(max_length=255, verbose_name='Наименование получаемой валюты')),
            ],
            options={
                'verbose_name': 'Направление обмена',
                'verbose_name_plural': 'Направления обмена',
                'ordering': ['ExchID'],
            },
        ),
        migrations.AlterModelOptions(
            name='pccntr_exchp',
            options={'ordering': ['ExchangePointID'], 'verbose_name': 'Орг. структура обменника', 'verbose_name_plural': 'Орг. структура обменников'},
        ),
    ]
