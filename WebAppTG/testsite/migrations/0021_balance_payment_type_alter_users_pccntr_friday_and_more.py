# Generated by Django 4.2.5 on 2023-11-26 18:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testsite', '0020_remove_pccntr_exchp_contacttype'),
    ]

    operations = [
        migrations.AddField(
            model_name='balance',
            name='Payment_type',
            field=models.CharField(blank=True, max_length=255, verbose_name='Тип платежа'),
        ),
        migrations.AlterField(
            model_name='users_pccntr',
            name='Friday',
            field=models.BooleanField(blank=True, default=False, verbose_name='Дни работы (Пятница)'),
        ),
        migrations.AlterField(
            model_name='users_pccntr',
            name='Monday',
            field=models.BooleanField(blank=True, default=False, verbose_name='Дни работы (Понедельник)'),
        ),
        migrations.AlterField(
            model_name='users_pccntr',
            name='Saturday',
            field=models.BooleanField(blank=True, default=False, verbose_name='Дни работы (Суббота)'),
        ),
        migrations.AlterField(
            model_name='users_pccntr',
            name='Sunday',
            field=models.BooleanField(blank=True, default=False, verbose_name='Дни работы (Воскресенье)'),
        ),
        migrations.AlterField(
            model_name='users_pccntr',
            name='Thursday',
            field=models.BooleanField(blank=True, default=False, verbose_name='Дни работы (Четверг)'),
        ),
        migrations.AlterField(
            model_name='users_pccntr',
            name='Tuesday',
            field=models.BooleanField(blank=True, default=False, verbose_name='Дни работы (Вторник)'),
        ),
        migrations.AlterField(
            model_name='users_pccntr',
            name='Wednesday',
            field=models.BooleanField(blank=True, default=False, verbose_name='Дни работы (Среда)'),
        ),
    ]
