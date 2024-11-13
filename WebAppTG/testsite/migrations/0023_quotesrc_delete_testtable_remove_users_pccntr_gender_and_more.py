# Generated by Django 4.2.5 on 2023-12-05 13:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testsite', '0022_orders_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuotesRC',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('QuotesRC_Code', models.CharField(max_length=255, verbose_name='Код источника котировок')),
                ('Name_RUS', models.CharField(max_length=255, verbose_name='Наименования источника котировок (RUS)')),
                ('Name_ENG', models.CharField(max_length=255, verbose_name='Наименования источника котировок (ENG)')),
                ('Name_DEU', models.CharField(max_length=255, verbose_name='Наименования источника котировок (DEU)')),
                ('Name_SRB', models.CharField(max_length=255, verbose_name='Наименования источника котировок (SRB)')),
            ],
            options={
                'verbose_name': 'Источник котировок',
                'verbose_name_plural': 'Источники котировок',
                'ordering': ['QuotesRC_Code'],
            },
        ),
        migrations.DeleteModel(
            name='testtable',
        ),
        migrations.RemoveField(
            model_name='users_pccntr',
            name='GENDER',
        ),
        migrations.RemoveField(
            model_name='users_pccntr',
            name='Name',
        ),
        migrations.RemoveField(
            model_name='users_pccntr',
            name='Otchestvo',
        ),
        migrations.RemoveField(
            model_name='users_pccntr',
            name='Surname',
        ),
        migrations.AddField(
            model_name='pccntr_opertypes',
            name='QuotesRC',
            field=models.CharField(default=0, max_length=255, verbose_name='Источник котировок'),
            preserve_default=False,
        ),
    ]
