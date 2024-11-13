# Generated by Django 4.2.5 on 2023-10-15 19:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testsite', '0017_refillbalancerequests'),
    ]

    operations = [
        migrations.CreateModel(
            name='Balance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('CreatedDate', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('TG_Contact', models.CharField(max_length=255, verbose_name='Имя пользователя')),
                ('ExchangePointID', models.CharField(max_length=255, verbose_name='ID обменника')),
                ('Blockchain', models.CharField(max_length=255, verbose_name='Блокчейн для перевода')),
                ('balance_Amount', models.IntegerField(verbose_name='Сумма для пополнения')),
                ('Payment_data', models.CharField(blank=True, max_length=255, verbose_name='Данные платежа')),
            ],
            options={
                'verbose_name': 'Изменение баланса',
                'verbose_name_plural': 'Изменения баланса',
                'ordering': ['CreatedDate'],
            },
        ),
        migrations.DeleteModel(
            name='RefillBalanceRequests',
        ),
    ]
