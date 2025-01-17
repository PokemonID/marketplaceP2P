# Generated by Django 4.2.5 on 2023-12-22 15:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testsite', '0031_exchangerequest'),
    ]

    operations = [
        migrations.RenameField(
            model_name='exchangerequest',
            old_name='profit_centers',
            new_name='PCCNTR',
        ),
        migrations.RenameField(
            model_name='exchangerequest',
            old_name='currency_code_in',
            new_name='receive_currency_ISO',
        ),
        migrations.RenameField(
            model_name='exchangerequest',
            old_name='sum_out',
            new_name='send_amount',
        ),
        migrations.RenameField(
            model_name='exchangerequest',
            old_name='currency_code_out',
            new_name='send_currency_ISO',
        ),
        migrations.RenameField(
            model_name='exchangerequest',
            old_name='staus_id',
            new_name='status_id',
        ),
        migrations.RenameField(
            model_name='exchangerequest',
            old_name='interval_of_deal_date',
            new_name='time_interval',
        ),
        migrations.RemoveField(
            model_name='exchangerequest',
            name='date_unix',
        ),
        migrations.RemoveField(
            model_name='exchangerequest',
            name='exchange_point_id',
        ),
        migrations.RemoveField(
            model_name='exchangerequest',
            name='exchanger_id',
        ),
        migrations.RemoveField(
            model_name='exchangerequest',
            name='sum_in',
        ),
        migrations.RemoveField(
            model_name='exchangerequest',
            name='user_id',
        ),
        migrations.AddField(
            model_name='exchangerequest',
            name='ExchangePointID',
            field=models.IntegerField(blank=True, default=0, verbose_name='ID обменника'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='exchangerequest',
            name='OperType',
            field=models.IntegerField(blank=True, default=0, verbose_name='Идентификатор направления обмена'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='exchangerequest',
            name='TG_Contact',
            field=models.IntegerField(blank=True, default=0, verbose_name='Идентификатор пользователя'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='exchangerequest',
            name='receive_amount',
            field=models.IntegerField(blank=True, default=0, verbose_name='Получаемая сумма (число)'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='exchangerequest',
            name='date',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Дата создания'),
        ),
        migrations.AlterField(
            model_name='exchangerequest',
            name='deal_date',
            field=models.DateField(auto_now_add=True, verbose_name='Дата сделки'),
        ),
        migrations.AlterField(
            model_name='exchangerequest',
            name='deal_id',
            field=models.IntegerField(blank=True, verbose_name='Номер сделки'),
        ),
        migrations.AlterField(
            model_name='exchangerequest',
            name='number_of_decimal',
            field=models.IntegerField(blank=True, verbose_name='Количество знаков после запятой получаемой валюты'),
        ),
        migrations.AlterField(
            model_name='exchangerequest',
            name='order_id',
            field=models.IntegerField(blank=True, verbose_name='Номер ордера'),
        ),
        migrations.AlterField(
            model_name='exchangerequest',
            name='request_id',
            field=models.IntegerField(blank=True, verbose_name='Номер заявки'),
        ),
        migrations.AlterField(
            model_name='exchangerequest',
            name='sum_eur',
            field=models.IntegerField(blank=True, verbose_name='Сумма обмена в эквиваленте EUR'),
        ),
        migrations.AlterField(
            model_name='exchangerequest',
            name='sum_usd',
            field=models.IntegerField(blank=True, verbose_name='Сумма обмена в эквиваленте USD'),
        ),
    ]
