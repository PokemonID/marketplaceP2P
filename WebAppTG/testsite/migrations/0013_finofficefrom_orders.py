# Generated by Django 4.2.5 on 2023-10-15 11:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testsite', '0012_remove_pccntr_opertypes_pccntr_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='FinOfficeFrom',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('FinOfficeType', models.CharField(max_length=255, verbose_name='Тип финансового учреждения')),
                ('Name_RUS', models.CharField(blank=True, max_length=255, verbose_name='Наименования финансового учреждения (RUS)')),
                ('Name_ENG', models.CharField(blank=True, max_length=255, verbose_name='Наименования финансового учреждения (ENG)')),
                ('Name_DEU', models.CharField(blank=True, max_length=255, verbose_name='Наименования финансового учреждения (DEU)')),
                ('Name_SRB', models.CharField(blank=True, max_length=255, verbose_name='Наименования финансового учреждения (SRB)')),
                ('FinOfficeCurr', models.CharField(max_length=255, verbose_name='Валюта финансового учреждения')),
            ],
            options={
                'verbose_name': 'Финансовое учреждение - отправитель',
                'verbose_name_plural': 'Финансовые учреждения - отправители',
                'ordering': ['FinOfficeType'],
            },
        ),
        migrations.CreateModel(
            name='Orders',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('CreatedDate', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('TG_Contact', models.CharField(max_length=255, verbose_name='Имя пользователя')),
                ('ExchangeID', models.CharField(max_length=255, verbose_name='ID направления сделки')),
                ('PriceType', models.CharField(max_length=255, verbose_name='Тип цены')),
                ('SendCurrencyISO', models.CharField(max_length=255, verbose_name='ID отдаваемой валюты')),
                ('ReceiveCurrencyISO', models.CharField(max_length=255, verbose_name='ID получаемой валюты')),
                ('SendCurrencyRate', models.CharField(blank=True, max_length=255, verbose_name='Курс отдаваемой валюты')),
                ('ReceiveCurrencyRate', models.CharField(blank=True, max_length=255, verbose_name='Курс получаемой валюты')),
                ('SendTransferType', models.CharField(max_length=255, verbose_name='Тип перевода отдаваемой валюты')),
                ('ReceiveTransferType', models.CharField(max_length=255, verbose_name='Тип перевода получаемой валюты')),
                ('SendAmount', models.IntegerField(verbose_name='Сумма отдаваемой валюты')),
                ('ReceiveAmount', models.IntegerField(verbose_name='Сумма получаемой валюты')),
                ('FinOfficeFrom', models.CharField(max_length=255, verbose_name='Финансовое учреждение отправителя')),
                ('OrderDate', models.DateField(auto_now_add=True, verbose_name='Дата cделки')),
                ('TimeInterval', models.CharField(max_length=255, verbose_name='Интервал времени сделки')),
                ('Country', models.CharField(max_length=255, verbose_name='Страна')),
                ('City', models.CharField(max_length=255, verbose_name='Город')),
                ('DeliveryType', models.CharField(max_length=255, verbose_name='Тип доставки')),
                ('OrderLimit', models.IntegerField(blank=True, verbose_name='Лимит ордера')),
                ('Comment', models.CharField(blank=True, max_length=255, verbose_name='Комментарий')),
                ('RequestID', models.IntegerField(blank=True, verbose_name='Комментарий')),
                ('Deal_ID', models.IntegerField(blank=True, verbose_name='Комментарий')),
            ],
            options={
                'verbose_name': 'Ордер',
                'verbose_name_plural': 'Ордеры',
                'ordering': ['CreatedDate'],
            },
        ),
    ]
