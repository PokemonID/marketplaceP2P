# Generated by Django 4.2.5 on 2023-12-22 17:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testsite', '0038_delete_requests'),
    ]

    operations = [
        migrations.CreateModel(
            name='Requests',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_id', models.IntegerField(blank=True, verbose_name='Номер ордера')),
                ('request_id', models.IntegerField(blank=True, verbose_name='Номер заявки')),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('TG_Contact', models.CharField(max_length=255, verbose_name='Имя пользователя')),
                ('PCCNTR', models.CharField(blank=True, max_length=255, verbose_name='Центры прибыли и затрат')),
                ('ExchangePointID', models.CharField(blank=True, max_length=255, verbose_name='ID обменника')),
                ('ExchangeID', models.CharField(blank=True, max_length=255, verbose_name='Идентификатор направления обмена')),
                ('price_type', models.CharField(blank=True, max_length=255, verbose_name='Тип цены')),
                ('send_currency_ISO', models.CharField(blank=True, max_length=255, verbose_name='Код отдаваемой валюты')),
                ('receive_currency_ISO', models.CharField(blank=True, max_length=255, verbose_name='Код получаемой валюты')),
                ('send_amount', models.IntegerField(blank=True, verbose_name='Отдаваемая сумма (число)')),
                ('receive_amount', models.IntegerField(blank=True, verbose_name='Получаемая сумма (число)')),
                ('number_of_decimal', models.IntegerField(blank=True, verbose_name='Количество знаков после запятой получаемой валюты')),
                ('sum_usd', models.IntegerField(blank=True, verbose_name='Сумма обмена в эквиваленте USD')),
                ('sum_eur', models.IntegerField(blank=True, verbose_name='Сумма обмена в эквиваленте EUR')),
                ('fin_office_to', models.CharField(blank=True, max_length=255, verbose_name='Финансовые учреждения Получатели')),
                ('deal_date', models.DateField(auto_now_add=True, verbose_name='Дата сделки')),
                ('time_interval', models.CharField(blank=True, max_length=255, verbose_name='Интервал времени сделки')),
                ('city', models.CharField(blank=True, max_length=255, verbose_name='Город')),
                ('delivery_type', models.CharField(blank=True, max_length=255, verbose_name='Тип доставки')),
                ('limit_order', models.CharField(blank=True, max_length=255, verbose_name='Лимит ордера')),
                ('comment', models.CharField(blank=True, max_length=255, verbose_name='Комментарий')),
                ('status', models.CharField(blank=True, max_length=255, verbose_name='Идентификатор статуса')),
                ('deal_id', models.IntegerField(blank=True, verbose_name='Номер сделки')),
            ],
        ),
    ]
