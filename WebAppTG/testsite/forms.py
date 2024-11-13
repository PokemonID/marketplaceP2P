from urllib import request
import case as case
import emoji
import urllib.request
import when as when
from django import forms
from django.contrib import auth
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import *
from itertools import chain
from datetime import datetime, timedelta
import time
import urllib.parse
import pytz
from tzlocal import get_localzone
from urllib.request import urlopen
import json
import dateutil.tz


class RegisterUserForm(UserCreationForm):
    username = forms.CharField(label='ТГ-аккаунт', widget=forms.TextInput(attrs={'class': 'form-input'}))
    password1 = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={'class': 'form-input'}))
    password2 = forms.CharField(label='Повтор пароля', widget=forms.PasswordInput(attrs={'class': 'form-input'}))
    email = forms.CharField(label='Email', widget=forms.EmailInput(attrs={'class': 'form-input'}))

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2', 'email')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-input'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'})
        }

    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            User.objects.get(email=email)
        except User.DoesNotExist:
            return email
        raise forms.ValidationError('Пользователь с таким email уже существует')


class LoginUserForm(AuthenticationForm):
    username = forms.CharField(label='ТГ-аккаунт', widget=forms.TextInput(attrs={'class': 'form-input'}))
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={'class': 'form-input'}))


class AddPersonalInformation(forms.Form):
    CHOICES = (
        ('Клиент', 'Клиент'),
        ('Обменник-Партнер', 'Партнер'),
    )
    USERTYPE = forms.ChoiceField(label='Тип пользователя', choices=CHOICES)
    Surname = forms.CharField(max_length=255, label='Фамилия', widget=forms.TextInput(attrs={'class': 'form-input'}))
    Name = forms.CharField(max_length=255, label='Имя', widget=forms.TextInput(attrs={'class': 'form-input'}))
    Otchestvo = forms.CharField(max_length=255, label='Отчество (при наличии)',
                                widget=forms.TextInput(attrs={'class': 'form-input'}), required=False)
    GENDER = forms.ModelChoiceField(queryset=Gender.objects.values_list('Name_RUS', flat=True),
                                    to_field_name='Name_RUS', label='Пол', empty_label='Пол не выбран')
    COUNTRY = forms.ModelChoiceField(queryset=Countries.objects.values_list('Name_RUS', flat=True),
                                     to_field_name='Name_RUS', label='Страна',
                                     empty_label='Страна не выбрана', widget=forms.Select(attrs={'hx-get':'load_cities/', 'hx-target':'#id_CITY'}))
    # CITY = forms.ModelChoiceField(queryset=Cities.objects.values_list('Name_RUS', flat=True), to_field_name='Name_RUS',
    #                               label='Город',
    #                               empty_label='Город не выбран')

    CITY = forms.ModelChoiceField(queryset=Cities.objects.none(), label='Город', empty_label='Город не выбран')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if 'COUNTRY' in self.data:
            country_name = str(self.data.get('COUNTRY'))
            country_name = urllib.parse.unquote(country_name)
            country_id = Countries.objects.filter(Name_RUS=country_name).values('Country_code')[0]['Country_code']
            self.fields['CITY'].queryset = Cities.objects.filter(Country=country_id).values_list('Name_RUS', flat=True)
            self.fields['CITY'].to_field_name = 'Name_RUS'
            self.fields['CITY'].empty_label='Город не выбран'


    CHOICES = (
        ('RUS', 'Русский'),
        ('ENG', 'English'),
        ('DEU', 'Deutsch'),
        ('SRB', 'Српски'),
    )
    Language = forms.ChoiceField(label='Язык', choices=CHOICES)


class Emailconfirm(forms.Form):
    code = forms.CharField(max_length=255, label='Код', widget=forms.NumberInput(attrs={'class': 'form-input'}))


class Emailforreset(forms.Form):
    email = forms.CharField(label='Email', widget=forms.EmailInput(attrs={'class': 'form-input'}))


class ChangePersonalInformation(forms.Form):
    Surname = forms.CharField(max_length=255, label='Фамилия', widget=forms.TextInput(attrs={'class': 'form-input'}),
                              required=False)
    Name = forms.CharField(max_length=255, label='Имя', widget=forms.TextInput(attrs={'class': 'form-input'}),
                           required=False)
    Otchestvo = forms.CharField(max_length=255, label='Отчество (при наличии)',
                                widget=forms.TextInput(attrs={'class': 'form-input'}), required=False)
    GENDER = forms.ModelChoiceField(queryset=Gender.objects.values_list('Name_RUS', flat=True),
                                    to_field_name='Name_RUS', label='Пол', empty_label='Пол не выбран', required=False)
    COUNTRY = forms.ModelChoiceField(queryset=Countries.objects.values_list('Name_RUS', flat=True),
                                     to_field_name='Name_RUS', label='Страна',
                                     empty_label='Страна не выбрана',
                                     widget=forms.Select(attrs={'hx-get': 'load_cities/', 'hx-target': '#id_CITY'}))
    # CITY = forms.ModelChoiceField(queryset=Cities.objects.values_list('Name_RUS', flat=True), to_field_name='Name_RUS',
    #                               label='Город',
    #                               empty_label='Город не выбран', required=False)

    CITY = forms.ModelChoiceField(queryset=Cities.objects.none(), label='Город', empty_label='Город не выбран')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        country_name = str(self.data.get('COUNTRY'))
        country_name = urllib.parse.unquote(country_name)
        try:
            country_id = Countries.objects.filter(Name_RUS=country_name).values('Country_code')[0]['Country_code']
        except:
            country_name = self.initial['COUNTRY']
            country_id = Countries.objects.filter(Name_RUS=country_name).values('Country_code')[0]['Country_code']
        self.fields['CITY'].queryset = Cities.objects.filter(Country=country_id).values_list('Name_RUS', flat=True)
        self.fields['CITY'].to_field_name = 'Name_RUS'

    CHOICES = (
        ('Язык не выбран', 'Язык не выбран'),
        ('RUS', 'Русский'),
        ('ENG', 'English'),
        ('DEU', 'Deutsch'),
        ('SRB', 'Српски'),
    )
    Language = forms.ChoiceField(label='Язык', choices=CHOICES)


class Feedback(forms.Form):
    def __init__(self, param,  *args, **kwargs):
        super().__init__(*args, **kwargs)
        if param != 2 and param != 4 and param != 38:
            self.fields['TG_contact'].required = False
    TG_contact = forms.CharField(max_length=255, label='Имя пользователя в TG', required=True)
    Text = forms.CharField(max_length=2000, label='Текст', widget=forms.Textarea)
    CHOICES = (
        ('-1', '-'),
        ('1', emoji.emojize(':star:')),
        ('2', emoji.emojize(':star: :star:')),
        ('3', emoji.emojize(':star: :star: :star:')),
        ('4', emoji.emojize(':star: :star: :star: :star:')),
        ('5', emoji.emojize(':star: :star: :star: :star: :star:')),
    )
    Rating = forms.ChoiceField(label='Оценка (не обязательно в случае обращения в поддержку)', choices=CHOICES, required=False)


class AddPCCNTRName(forms.Form):
    PCCNTR_name = forms.CharField(max_length=255, label='Наименование Центра прибыли и затрат',
                                    widget=forms.TextInput(attrs={'class': 'form-input'}))

class ChooseOrgforExchP(forms.Form):
    UserToCheck = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-input'}))


class ExchPInformation(forms.Form):
    Countries = Countries.objects.values_list('Name_RUS').order_by('Name_RUS')
    countries_for_form = []
    for country in Countries:
        countries_for_form.append((str(country[0]), str(country[0])))
    countries_for_form_tuple = tuple(i for i in countries_for_form)

    ExchPCountry = forms.MultipleChoiceField(
        choices=countries_for_form_tuple,
        label="Страна(-ы)",
        widget=forms.CheckboxSelectMultiple)

    Cities = Cities.objects.values_list('Name_RUS').order_by('Name_RUS')
    cities_for_form = []
    for city in Cities:
        cities_for_form.append((str(city[0]), str(city[0])))
    cities_for_form_tuple = tuple(i for i in cities_for_form)

    ExchPCity = forms.MultipleChoiceField(
        choices=cities_for_form_tuple,
        label="Город(-а)",
        widget=forms.CheckboxSelectMultiple)

    ExchPName = forms.CharField(max_length=255, label='Наименование обменника',
                                    widget=forms.TextInput(attrs={'class': 'form-input'}))
    CHOICES = (
        ('Курьер', 'Курьер'),
        ('Офис', 'Офис'),
    )
    ExchPOfficeCourier = forms.MultipleChoiceField(label='Тип доставки', choices=CHOICES, widget=forms.CheckboxSelectMultiple)

class ChooseUserforExchP(forms.Form):
    def __init__(self, user, exchange_name,  *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        pcc = Users_PCCNTR.objects.filter(TG_Contact=self.user, ContactType__in=['PART', 'ORG']).values('TG_Contact', 'PCCNTR')
        pcc_name = PCCNTR.objects.get(PCCNTR_code=pcc[0]['PCCNTR'])
        ExchPCountries = PCCNTR_ExchP.objects.filter(PCCNTR=pcc_name.PCCNTR_code, ExchangePointName=exchange_name).values_list("ExchangePointCountry", flat=True)
        ExchPPositions = PCCNTR_ExchP.objects.filter(PCCNTR=pcc_name.PCCNTR_code, ExchangePointName=exchange_name).values_list("ExchangePointOfficeCourier",flat=True)

        countries = []
        positions = []

        for country in ExchPCountries:
            countries.append(Countries.objects.filter(Country_code=country.strip()).values_list('Name_RUS', flat=True)[0])

        for position in ExchPPositions:
            while ";" in position:
                position_1 = position[:position.find(';')]
                if position_1.strip() == 'Офис':
                    position_1 = 'Куратор'
                else:
                    position_1 = 'Курьер'
                position = position[position.find(';')+2:].strip()
                positions.append(position_1.strip())
            if position.strip() == 'Офис':
                position = 'Куратор'
            else:
                position = 'Курьер'
            positions.append(position.strip())

        countries = list(set(countries))
        positions = list(set(positions))

        countries_for_form = [('', 'Страна не выбрана')]
        for country in countries:
            countries_for_form.append((str(country), str(country)))
        countries_for_form_tuple = tuple(i for i in countries_for_form)
        self.fields['ExchPCountries'].choices = countries_for_form_tuple

        positions_for_form = []
        for position in positions:
            positions_for_form.append((str(position), str(position)))
        positions_for_form_tuple = tuple(i for i in positions_for_form)
        self.fields['ExchPOfficeCourier'].choices = positions_for_form_tuple

        if 'ExchPCountries' in self.data:
            country_name = str(self.data.get('ExchPCountries'))
            country_name = urllib.parse.unquote(country_name)
            country_id = Countries.objects.filter(Name_RUS=country_name).values('Country_code')[0]['Country_code']
            ExchPCities = PCCNTR_ExchP.objects.filter(PCCNTR=pcc_name.PCCNTR_code, ExchangePointName=exchange_name,
                                        ExchangePointCountry=country_id).values_list("ExchangePointCity", flat=True)

            cities = []
            for city in ExchPCities:
                while ";" in city:
                    city_1 = city[:city.find(';')]
                    city = city[city.find(';') + 2:].strip()
                    cities.append(Cities.objects.filter(City_code=city_1.strip()).values_list('Name_RUS', flat=True)[0])
                cities.append(Cities.objects.filter(City_code=city.strip()).values_list('Name_RUS', flat=True)[0])

            cities = list(set(cities))

            cities_for_form = [('', 'Город не выбран')]
            for city in cities:
                cities_for_form.append((str(city), str(city)))
            cities_for_form_tuple = tuple(i for i in cities_for_form)
            self.fields['ExchPCities'].choices = cities_for_form_tuple

    chosen_user = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-input'}))

    country_for_form = [('', 'Страна не выбрана')]
    country_for_form_tuple = tuple(i for i in country_for_form)
    ExchPCountries = forms.ChoiceField(choices=country_for_form_tuple, label='Страна', widget=forms.Select(attrs={'hx-get': 'load_cities_num/', 'hx-target': '#id_ExchPCities'}))
    city_for_form = [('', 'Город не выбран')]
    city_for_form_tuple = tuple(i for i in city_for_form)
    ExchPCities = forms.MultipleChoiceField(label='Город', widget=forms.SelectMultiple, choices=city_for_form_tuple)
    ExchPOfficeCourier = forms.MultipleChoiceField(label='Должность сотрудника',widget=forms.CheckboxSelectMultiple)

    CHOICES_Time = (
        ('00:00', '00:00'), ('01:00', '01:00'), ('02:00', '02:00'), ('03:00', '03:00'), ('04:00', '04:00'),
        ('05:00', '05:00'), ('06:00', '06:00'), ('07:00', '07:00'), ('08:00', '08:00'), ('09:00', '09:00')
        , ('10:00', '10:00'), ('11:00', '11:00'), ('12:00', '12:00'), ('13:00', '13:00'), ('14:00', '14:00')
        , ('15:00', '15:00'), ('16:00', '16:00'), ('17:00', '17:00'), ('18:00', '18:00'), ('19:00', '19:00')
        , ('20:00', '20:00'), ('21:00', '21:00'), ('22:00', '22:00'), ('23:00', '23:00'), ('24:00', '24:00'),
    )
    Mon = forms.BooleanField(label='Понедельник', required=False)
    Tue = forms.BooleanField(label='Вторник', required=False)
    Wed = forms.BooleanField(label='Среда', required=False)
    Thu = forms.BooleanField(label='Четверг', required=False)
    Fri = forms.BooleanField(label='Пятница', required=False)
    Working_hours_Open_Working_days = forms.ChoiceField(label='Часы работы (будние дни) с', choices=CHOICES_Time, required=False)
    Working_hours_Close_Working_days = forms.ChoiceField(label='до', choices=CHOICES_Time, required=False)
    Sat = forms.BooleanField(label='Суббота', required=False)
    Sun = forms.BooleanField(label='Воскресенье', required=False)
    Working_hours_Open_Weekends = forms.ChoiceField(label='Часы работы (выходные) с', choices=CHOICES_Time, required=False)
    Working_hours_Close_Weekends = forms.ChoiceField(label='до', choices=CHOICES_Time, required=False)
    ExchPAddress = forms.CharField(max_length=255, label='Адрес обменника', widget=forms.TextInput(attrs={'class': 'form-input'}), required=False)


class ChooseUserforExchP_without_name(forms.Form):
    def __init__(self, user, ExchangeName, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        pcc = Users_PCCNTR.objects.filter(TG_Contact=self.user, ContactType__in=['PART', 'ORG']).values('TG_Contact', 'PCCNTR')
        pcc_name = PCCNTR.objects.get(PCCNTR_code=pcc[0]['PCCNTR'])
        # print(pcc_name.PCCNTR_code)
        # print(ExchangeName)
        ExchPCountries = PCCNTR_ExchP.objects.filter(PCCNTR=pcc_name.PCCNTR_code, ExchangePointName=ExchangeName).values_list("ExchangePointCountry", flat=True)
        # print(ExchPCountries)
        # print(self.data)
        ExchPPositions = PCCNTR_ExchP.objects.filter(PCCNTR=pcc_name.PCCNTR_code, ExchangePointName=ExchangeName).values_list("ExchangePointOfficeCourier",flat=True)

        positions = []

        countries = list(Countries.objects.filter(Country_code__in=ExchPCountries).values_list('Name_RUS', flat=True))

        for position in ExchPPositions:
            while ";" in position:
                position_1 = position[:position.find(';')]
                if position_1.strip() == 'Офис':
                    position_1 = 'Куратор'
                else:
                    position_1 = 'Курьер'
                position = position[position.find(';')+2:].strip()
                positions.append(position_1.strip())
            if position.strip() == 'Офис':
                position = 'Куратор'
            else:
                position = 'Курьер'
            positions.append(position.strip())

        countries = list(set(countries))
        positions = list(set(positions))

        countries_for_form = [('', 'Страна не выбрана')]
        for country in countries:
            countries_for_form.append((str(country), str(country)))
        countries_for_form_tuple = tuple(i for i in countries_for_form)
        self.fields['ExchPCountries'].choices = countries_for_form_tuple

        positions_for_form = []
        for position in positions:
            positions_for_form.append((str(position), str(position)))
        positions_for_form_tuple = tuple(i for i in positions_for_form)
        self.fields['ExchPOfficeCourier'].choices = positions_for_form_tuple


        if 'ExchPCountries' in self.data:
            country_name = str(self.data.get('ExchPCountries'))
            country_name = urllib.parse.unquote(country_name)
            country_id = Countries.objects.filter(Name_RUS=country_name).values('Country_code')[0]['Country_code']
            ExchPCities = PCCNTR_ExchP.objects.filter(PCCNTR=pcc_name.PCCNTR_code, ExchangePointName=ExchangeName,
                                        ExchangePointCountry=country_id).values_list("ExchangePointCity", flat=True)

            cities = []
            for city in ExchPCities:
                while ";" in city:
                    city_1 = city[:city.find(';')]
                    city = city[city.find(';') + 2:].strip()
                    cities.append(Cities.objects.filter(City_code=city_1.strip()).values_list('Name_RUS', flat=True)[0])
                cities.append(Cities.objects.filter(City_code=city.strip()).values_list('Name_RUS', flat=True)[0])

            cities = list(set(cities))

            cities_for_form = []
            for city in cities:
                cities_for_form.append((str(city), str(city)))
            cities_for_form_tuple = tuple(i for i in cities_for_form)
            self.fields['ExchPCities'].choices = cities_for_form_tuple

    country_for_form = [('', 'Страна не выбрана')]
    country_for_form_tuple = tuple(i for i in country_for_form)
    ExchPCountries = forms.ChoiceField(choices=country_for_form_tuple, label='Страна', widget=forms.Select(attrs={'hx-get': 'load_cities_text/', 'hx-target': '#id_ExchPCities'}))
    city_for_form = [('', 'Город не выбран')]
    city_for_form_tuple = tuple(i for i in city_for_form)
    ExchPCities = forms.MultipleChoiceField(label='Город', widget=forms.SelectMultiple, choices=city_for_form_tuple)
    # ExchPCities = forms.ChoiceField(choices=city_for_form_tuple, label='Город')

    ExchPOfficeCourier = forms.MultipleChoiceField(label='Должность сотрудника',widget=forms.CheckboxSelectMultiple)

    CHOICES_Time = (
        ('00:00', '00:00'), ('01:00', '01:00'), ('02:00', '02:00'), ('03:00', '03:00'), ('04:00', '04:00'),
        ('05:00', '05:00'), ('06:00', '06:00'), ('07:00', '07:00'), ('08:00', '08:00'), ('09:00', '09:00')
        ,('10:00', '10:00'),('11:00', '11:00'), ('12:00', '12:00'), ('13:00', '13:00'), ('14:00', '14:00')
        ,('15:00', '15:00'),('16:00', '16:00'), ('17:00', '17:00'), ('18:00', '18:00'), ('19:00', '19:00')
        ,('20:00', '20:00'),('21:00', '21:00'), ('22:00', '22:00'), ('23:00', '23:00'), ('24:00', '24:00'),
    )
    Mon = forms.BooleanField(label='Понедельник', required=False)
    Tue = forms.BooleanField(label='Вторник', required=False)
    Wed = forms.BooleanField(label='Среда', required=False)
    Thu = forms.BooleanField(label='Четверг', required=False)
    Fri = forms.BooleanField(label='Пятница', required=False)
    Working_hours_Open_Working_days = forms.ChoiceField(label='Часы работы (будние дни) с', choices=CHOICES_Time, required=False)
    Working_hours_Close_Working_days = forms.ChoiceField(label='до', choices=CHOICES_Time, required=False)
    Sat = forms.BooleanField(label='Суббота', required=False)
    Sun = forms.BooleanField(label='Воскресенье', required=False)
    Working_hours_Open_Weekends = forms.ChoiceField(label='Часы работы (выходные) с', choices=CHOICES_Time, required=False)
    Working_hours_Close_Weekends = forms.ChoiceField(label='до', choices=CHOICES_Time, required=False)
    ExchPAddress = forms.CharField(max_length=255, label='Адрес обменника',
                                widget=forms.TextInput(attrs={'class': 'form-input'}), required=False)


class ChooseDealsforExchP(forms.Form):
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        pcc = Users_PCCNTR.objects.filter(TG_Contact=self.user).values('TG_Contact', 'PCCNTR')
        pcc_name = PCCNTR.objects.get(PCCNTR_code=pcc[0]['PCCNTR'])
        ExchPCodes = EP_ExchangeID.objects.filter(PCCNTR=pcc_name.PCCNTR_code).values_list("ExchangePointID", flat=True)
        ExchPCodes = list(set(list(ExchPCodes)))

        ExchPoints1 = PCCNTR_ExchP.objects.filter(PCCNTR=pcc_name.PCCNTR_code, ExchangePointID__in=ExchPCodes).values_list("ExchangePointName").order_by("ExchangePointName")
        exchp1_for_form = []
        for ex1 in ExchPoints1:
            exchp1_for_form.append((str(ex1[0]), str(ex1[0])))
        exchp1_for_form_tuple = tuple(i for i in exchp1_for_form)
        self.fields['ExchangePoints'].choices = exchp1_for_form_tuple


        ExchPoints2 = PCCNTR_ExchP.objects.filter(PCCNTR=pcc_name.PCCNTR_code).exclude(ExchangePointID__in=ExchPCodes).values_list("ExchangePointName").order_by("ExchangePointName")
        exchp2_for_form = []
        for ex2 in ExchPoints2:
            exchp2_for_form.append((str(ex2[0]), str(ex2[0])))
        exchp2_for_form_tuple = tuple(i for i in exchp2_for_form)
        print(ExchPoints2)
        self.fields['ExchangePoints2'].choices = exchp2_for_form_tuple


        if 'Currency_to_sell' in self.data:
            Currency_to_sell = str(self.data.get('Currency_to_sell'))
            currency_types = list(
                set(ExchangeID.objects.filter(SendCurrencyISO=Currency_to_sell).values_list("SendTransferType",
                                                                                            flat=True)))
            currency_types_for_form = []
            # print(str(self.data.get('Currency_to_sell')))
            if 'CRP' in currency_types:
                currency_types_for_form.append('Перевод по сети блокчейн')
            if 'CSH' in currency_types:
                currency_types_for_form.append('Наличные')
            if 'CRD' in currency_types:
                currency_types_for_form.append('Карточный перевод')
            currency_types_for_form.sort()

            curr_types_for_form = [('', 'Тип перевода не выбран')]
            for curr in currency_types_for_form:
                curr_types_for_form.append((str(curr), str(curr)))
            curr_types_for_form_tuple = tuple(i for i in curr_types_for_form)
            # print(curr_types_for_form_tuple)
            self.fields['Pay_type_sell'].choices = curr_types_for_form_tuple

        if 'Currency_to_buy' in self.data:
            Currency_to_buy = str(self.data.get('Currency_to_buy'))
            currency_types = list(
                set(ExchangeID.objects.filter(ReceiveCurrencyISO=Currency_to_buy).values_list("ReceiveTransferType",
                                                                                              flat=True)))
            currency_types_for_form = []
            if 'CRP' in currency_types:
                currency_types_for_form.append('Перевод по сети блокчейн')
            if 'CSH' in currency_types:
                currency_types_for_form.append('Наличные')
            if 'CRD' in currency_types:
                currency_types_for_form.append('Карточный перевод')
            currency_types_for_form.sort()

            curr_types_for_form = [('', 'Тип перевода не выбран')]
            for curr in currency_types_for_form:
                curr_types_for_form.append((str(curr), str(curr)))
            curr_types_for_form_tuple = tuple(i for i in curr_types_for_form)
            # print(curr_types_for_form_tuple)
            self.fields['Pay_type_buy'].choices = curr_types_for_form_tuple

        # if 'Pay_type_sell' in self.data:
        #     Pay_type_sell = str(self.data.get('Pay_type_sell'))
        #     Pay_type_sell = urllib.parse.unquote(Pay_type_sell)
        #     finofficefrom_for_form = [('', 'Метод оплаты не выбран')]
        #     if Pay_type_sell == 'Карточный перевод':
        #         FinOfficeFromTypes_Banks = list(
        #             FinOffice.objects.filter(FinOfficeType="Банки").values_list("Name_RUS", flat=True).order_by(
        #                 "Name_RUS"))
        #         for finoffice in FinOfficeFromTypes_Banks:
        #             finofficefrom_for_form.append((finoffice, finoffice))
        #     elif Pay_type_sell == 'Наличные':
        #         FinOfficeFromTypes_Banks = list(
        #             FinOffice.objects.filter(FinOfficeType="Наличные").values_list("Name_RUS", flat=True).order_by(
        #                 "Name_RUS"))
        #         for finoffice in FinOfficeFromTypes_Banks:
        #             finofficefrom_for_form.append((finoffice, finoffice))
        #     elif Pay_type_sell == 'Перевод по сети блокчейн':
        #         FinOfficeFromTypes_Crypto_Exchange = list(
        #             FinOffice.objects.filter(FinOfficeType="Криптобиржи-Отправители").values_list("Name_RUS",
        #                                                                                           flat=True))
        #         # finofficefrom_for_form.append((" - Криптобиржи", " - Криптобиржи"))
        #         for finoffice in FinOfficeFromTypes_Crypto_Exchange:
        #             finofficefrom_for_form.append((finoffice, finoffice))
        #
        #         FinOfficeFromTypes_Crypto_Wallet = list(
        #             FinOffice.objects.filter(FinOfficeType="Криптокошельки-Отправители").values_list("Name_RUS",
        #                                                                                              flat=True))
        #         # finofficefrom_for_form.append((" - Криптокошельки", " - Криптокошельки"))
        #         for finoffice in FinOfficeFromTypes_Crypto_Wallet:
        #             finofficefrom_for_form.append((finoffice, finoffice))
        #     finofficefrom_for_form_tuple = tuple(i for i in finofficefrom_for_form)
        #     #print(finoffice_for_form_tuple)
        #     self.fields['FinOfficeFrom'].choices = finofficefrom_for_form_tuple
        #
        # if 'Pay_type_buy' in self.data:
        #     Pay_type_buy = str(self.data.get('Pay_type_buy'))
        #     Pay_type_buy = urllib.parse.unquote(Pay_type_buy)
        #     finofficeto_for_form = [('', 'Метод оплаты не выбран')]
        #     if Pay_type_buy == 'Карточный перевод':
        #         FinOfficeToTypes_Banks = list(
        #             FinOffice.objects.filter(FinOfficeType="Банки").values_list("Name_RUS", flat=True).order_by(
        #                 "Name_RUS"))
        #         for finoffice in FinOfficeToTypes_Banks:
        #             finofficeto_for_form.append((finoffice, finoffice))
        #     elif Pay_type_buy == 'Наличные':
        #         FinOfficeToTypes_Banks = list(
        #             FinOffice.objects.filter(FinOfficeType="Наличные").values_list("Name_RUS", flat=True).order_by(
        #                 "Name_RUS"))
        #         for finoffice in FinOfficeToTypes_Banks:
        #             finofficeto_for_form.append((finoffice, finoffice))
        #     elif Pay_type_buy == 'Перевод по сети блокчейн':
        #         FinOfficeToTypes_Crypto_Exchange = list(
        #             FinOffice.objects.filter(FinOfficeType="Криптобиржи-Отправители").values_list("Name_RUS",
        #                                                                                           flat=True))
        #         # finofficeto_for_form.append((" - Криптобиржи", " - Криптобиржи"))
        #         for finoffice in FinOfficeToTypes_Crypto_Exchange:
        #             finofficeto_for_form.append((finoffice, finoffice))
        #
        #         FinOfficeToTypes_Crypto_Wallet = list(
        #             FinOffice.objects.filter(FinOfficeType="Криптокошельки-Отправители").values_list("Name_RUS",
        #                                                                                              flat=True))
        #         # finofficeto_for_form.append((" - Криптокошельки", " - Криптокошельки"))
        #         for finoffice in FinOfficeToTypes_Crypto_Wallet:
        #             finofficeto_for_form.append((finoffice, finoffice))
        #     finofficeto_for_form_tuple = tuple(i for i in finofficeto_for_form)
        #     self.fields['FinOfficeTo'].choices = finofficeto_for_form_tuple

    ExchangePoints = forms.ChoiceField(required=False)

    ExchangePoints2 = forms.ChoiceField(required=False)


    # Deals = ExchangeID.objects.values_list('Name_RUS').order_by('Name_RUS')
    # deals_for_form = []
    # for deal in Deals:
    #     deals_for_form.append((str(deal[0]), str(deal[0])))
    # deals_for_form_tuple = tuple(i for i in deals_for_form)
    #
    # chosen_deals = forms.MultipleChoiceField(
    #     choices=deals_for_form_tuple,
    #     label="Выберите направления сделок",
    #     widget=forms.CheckboxSelectMultiple, required=True)

    Currency_sell = list(set(list(ExchangeID.objects.values_list("SendCurrencyISO").order_by("SendCurrencyISO"))))

    curr_sell_for_form = []
    curr_sell_for_form.append(((""), ("-")))
    for curr in Currency_sell:
        curr_sell_for_form.append((str(curr[0]), str(curr[0])))
    curr_sell_for_form_tuple = tuple(i for i in curr_sell_for_form)

    Currency_to_sell = forms.ChoiceField(choices=curr_sell_for_form_tuple, widget=forms.Select(attrs={'hx-get': 'load_pay_type_sell/', 'hx-target': '#id_Pay_type_sell'}))

    Currency_buy = list(set(list(ExchangeID.objects.values_list("ReceiveCurrencyISO").order_by("ReceiveCurrencyISO"))))
    curr_buy_for_form = []
    curr_buy_for_form.append(((""), ("-")))
    for curr in Currency_buy:
        curr_buy_for_form.append((str(curr[0]), str(curr[0])))
    curr_buy_for_form_tuple = tuple(i for i in curr_buy_for_form)

    Currency_to_buy = forms.ChoiceField(choices=curr_buy_for_form_tuple, widget=forms.Select(attrs={'hx-get': 'load_pay_type_buy/', 'hx-target': '#id_Pay_type_buy'}))

    pay_types_for_form = [('', 'Тип перевода не выбран')] # ('', 'Тип перевода не выбран')
    pay_types_sell_for_form_tuple = tuple(i for i in pay_types_for_form)
    Pay_type_sell = forms.ChoiceField(choices=pay_types_sell_for_form_tuple, widget=forms.Select(attrs={'hx-get':'load_payment_method_from/', 'hx-target':'#id_FinOfficeFrom'}))


    # finofficefrom_for_form = [('', 'Метод оплаты не выбран')] #('', 'Метод оплаты не выбран')
    # finofficefrom_for_form_tuple = tuple(i for i in finofficefrom_for_form)
    # FinOfficeFrom = forms.ChoiceField(choices=finofficefrom_for_form_tuple)

    pay_types_buy_for_form = [('', 'Тип перевода не выбран')] # ('', 'Тип перевода не выбран')
    pay_types_buy_for_form_tuple = tuple(i for i in pay_types_buy_for_form)
    Pay_type_buy = forms.ChoiceField(choices=pay_types_buy_for_form_tuple, widget=forms.Select(attrs={'hx-get':'load_payment_method_to/', 'hx-target':'#id_FinOfficeTo'}))

    # finofficeto_for_form = [('', 'Метод оплаты не выбран')]  # ('', 'Метод оплаты не выбран')
    # finofficeto_for_form_tuple = tuple(i for i in finofficeto_for_form)
    # FinOfficeTo = forms.ChoiceField(choices=finofficeto_for_form_tuple)

    Min_amount = forms.IntegerField(label='Минимальная сумма сделки')
    Max_amount = forms.IntegerField(label='Максимальная сумма сделки')

    Norm_Prib_Name_1_1 = forms.IntegerField(label='Введите первый интервал сделки (например 100-499)',
                                    widget=forms.TextInput(attrs={'class': 'form-input'}))
    Norm_Prib_Name_1_2 = forms.IntegerField(widget=forms.TextInput(attrs={'class': 'form-input'}))
    Norm_Prib_Percent_1 = forms.FloatField(label='Введите процент прибыли ')

    Norm_Prib_Name_2_1 = forms.IntegerField(label='Введите второй интервал сделки (не обязательно)',
                                       widget=forms.TextInput(attrs={'class': 'form-input'}), required = False)
    Norm_Prib_Name_2_2 = forms.IntegerField(widget=forms.TextInput(attrs={'class': 'form-input'}), required=False)
    Norm_Prib_Percent_2 = forms.FloatField(label='Введите процент прибыли  (не обязательно)', required = False)

    Norm_Prib_Name_3_1 = forms.IntegerField(label='Введите третий интервал сделки (не обязательно)',
                                       widget=forms.TextInput(attrs={'class': 'form-input'}), required = False)
    Norm_Prib_Name_3_2 = forms.IntegerField(widget=forms.TextInput(attrs={'class': 'form-input'}), required=False)
    Norm_Prib_Percent_3 = forms.FloatField(label='Введите процент прибыли  (не обязательно)', required = False)

class ChooseDealsforExchP_add(forms.Form):
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        pcc = Users_PCCNTR.objects.filter(TG_Contact=self.user).values('TG_Contact', 'PCCNTR')
        pcc_name = PCCNTR.objects.get(PCCNTR_code=pcc[0]['PCCNTR'])

        if 'Currency_to_sell' in self.data:
            Currency_to_sell = str(self.data.get('Currency_to_sell'))
            currency_types = list(
                set(ExchangeID.objects.filter(SendCurrencyISO=Currency_to_sell).values_list("SendTransferType",
                                                                                            flat=True)))
            currency_types_for_form = []
            # print(str(self.data.get('Currency_to_sell')))
            if 'CRP' in currency_types:
                currency_types_for_form.append('Перевод по сети блокчейн')
            if 'CSH' in currency_types:
                currency_types_for_form.append('Наличные')
            if 'CRD' in currency_types:
                currency_types_for_form.append('Карточный перевод')
            currency_types_for_form.sort()

            curr_types_for_form = [('', 'Тип перевода не выбран')]
            for curr in currency_types_for_form:
                curr_types_for_form.append((str(curr), str(curr)))
            curr_types_for_form_tuple = tuple(i for i in curr_types_for_form)
            # print(curr_types_for_form_tuple)
            self.fields['Pay_type_sell'].choices = curr_types_for_form_tuple

        if 'Currency_to_buy' in self.data:
            Currency_to_buy = str(self.data.get('Currency_to_buy'))
            currency_types = list(
                set(ExchangeID.objects.filter(ReceiveCurrencyISO=Currency_to_buy).values_list("ReceiveTransferType",
                                                                                              flat=True)))
            currency_types_for_form = []
            if 'CRP' in currency_types:
                currency_types_for_form.append('Перевод по сети блокчейн')
            if 'CSH' in currency_types:
                currency_types_for_form.append('Наличные')
            if 'CRD' in currency_types:
                currency_types_for_form.append('Карточный перевод')
            currency_types_for_form.sort()

            curr_types_for_form = [('', 'Тип перевода не выбран')]
            for curr in currency_types_for_form:
                curr_types_for_form.append((str(curr), str(curr)))
            curr_types_for_form_tuple = tuple(i for i in curr_types_for_form)
            # print(curr_types_for_form_tuple)
            self.fields['Pay_type_buy'].choices = curr_types_for_form_tuple

        # if 'Pay_type_sell' in self.data:
        #     Pay_type_sell = str(self.data.get('Pay_type_sell'))
        #     Pay_type_sell = urllib.parse.unquote(Pay_type_sell)
        #     finofficefrom_for_form = [('', 'Метод оплаты не выбран')]
        #     if Pay_type_sell == 'Карточный перевод':
        #         FinOfficeFromTypes_Banks = list(
        #             FinOffice.objects.filter(FinOfficeType="Банки").values_list("Name_RUS", flat=True).order_by(
        #                 "Name_RUS"))
        #         for finoffice in FinOfficeFromTypes_Banks:
        #             finofficefrom_for_form.append((finoffice, finoffice))
        #     elif Pay_type_sell == 'Наличные':
        #         FinOfficeFromTypes_Banks = list(
        #             FinOffice.objects.filter(FinOfficeType="Наличные").values_list("Name_RUS", flat=True).order_by(
        #                 "Name_RUS"))
        #         for finoffice in FinOfficeFromTypes_Banks:
        #             finofficefrom_for_form.append((finoffice, finoffice))
        #     elif Pay_type_sell == 'Перевод по сети блокчейн':
        #         FinOfficeFromTypes_Crypto_Exchange = list(
        #             FinOffice.objects.filter(FinOfficeType="Криптобиржи-Отправители").values_list("Name_RUS",
        #                                                                                           flat=True))
        #         finofficefrom_for_form.append((" - Криптобиржи", " - Криптобиржи"))
        #         for finoffice in FinOfficeFromTypes_Crypto_Exchange:
        #             finofficefrom_for_form.append((finoffice, finoffice))
        #
        #         FinOfficeFromTypes_Crypto_Wallet = list(
        #             FinOffice.objects.filter(FinOfficeType="Криптокошельки-Отправители").values_list("Name_RUS",
        #                                                                                              flat=True))
        #         finofficefrom_for_form.append((" - Криптокошельки", " - Криптокошельки"))
        #         for finoffice in FinOfficeFromTypes_Crypto_Wallet:
        #             finofficefrom_for_form.append((finoffice, finoffice))
        #     finofficefrom_for_form_tuple = tuple(i for i in finofficefrom_for_form)
        #     #print(finoffice_for_form_tuple)
        #     self.fields['FinOfficeFrom'].choices = finofficefrom_for_form_tuple
        #
        # if 'Pay_type_buy' in self.data:
        #     Pay_type_buy = str(self.data.get('Pay_type_buy'))
        #     Pay_type_buy = urllib.parse.unquote(Pay_type_buy)
        #     finofficeto_for_form = [('', 'Метод оплаты не выбран')]
        #     if Pay_type_buy == 'Карточный перевод':
        #         FinOfficeToTypes_Banks = list(
        #             FinOffice.objects.filter(FinOfficeType="Банки").values_list("Name_RUS", flat=True).order_by(
        #                 "Name_RUS"))
        #         for finoffice in FinOfficeToTypes_Banks:
        #             finofficeto_for_form.append((finoffice, finoffice))
        #     elif Pay_type_buy == 'Наличные':
        #         FinOfficeToTypes_Banks = list(
        #             FinOffice.objects.filter(FinOfficeType="Наличные").values_list("Name_RUS", flat=True).order_by(
        #                 "Name_RUS"))
        #         for finoffice in FinOfficeToTypes_Banks:
        #             finofficeto_for_form.append((finoffice, finoffice))
        #     elif Pay_type_buy == 'Перевод по сети блокчейн':
        #         FinOfficeToTypes_Crypto_Exchange = list(
        #             FinOffice.objects.filter(FinOfficeType="Криптобиржи-Отправители").values_list("Name_RUS",
        #                                                                                           flat=True))
        #         finofficeto_for_form.append((" - Криптобиржи", " - Криптобиржи"))
        #         for finoffice in FinOfficeToTypes_Crypto_Exchange:
        #             finofficeto_for_form.append((finoffice, finoffice))
        #
        #         FinOfficeToTypes_Crypto_Wallet = list(
        #             FinOffice.objects.filter(FinOfficeType="Криптокошельки-Отправители").values_list("Name_RUS",
        #                                                                                              flat=True))
        #         finofficeto_for_form.append((" - Криптокошельки", " - Криптокошельки"))
        #         for finoffice in FinOfficeToTypes_Crypto_Wallet:
        #             finofficeto_for_form.append((finoffice, finoffice))
        #     finofficeto_for_form_tuple = tuple(i for i in finofficeto_for_form)
        #     self.fields['FinOfficeTo'].choices = finofficeto_for_form_tuple

    Currency_sell = list(set(list(ExchangeID.objects.values_list("SendCurrencyISO").order_by("SendCurrencyISO"))))

    curr_sell_for_form = []
    curr_sell_for_form.append(((""), ("-")))
    for curr in Currency_sell:
        curr_sell_for_form.append((str(curr[0]), str(curr[0])))
    curr_sell_for_form_tuple = tuple(i for i in curr_sell_for_form)

    Currency_to_sell = forms.ChoiceField(choices=curr_sell_for_form_tuple, widget=forms.Select(attrs={'hx-get': 'load_pay_type_sell/', 'hx-target': '#id_Pay_type_sell'}))

    Currency_buy = list(set(list(ExchangeID.objects.values_list("ReceiveCurrencyISO").order_by("ReceiveCurrencyISO"))))
    curr_buy_for_form = []
    curr_buy_for_form.append(((""), ("-")))
    for curr in Currency_buy:
        curr_buy_for_form.append((str(curr[0]), str(curr[0])))
    curr_buy_for_form_tuple = tuple(i for i in curr_buy_for_form)

    Currency_to_buy = forms.ChoiceField(choices=curr_buy_for_form_tuple, widget=forms.Select(attrs={'hx-get': 'load_pay_type_buy/', 'hx-target': '#id_Pay_type_buy'}))

    pay_types_for_form = [('', 'Тип перевода не выбран')] # ('', 'Тип перевода не выбран')
    pay_types_sell_for_form_tuple = tuple(i for i in pay_types_for_form)
    Pay_type_sell = forms.ChoiceField(choices=pay_types_sell_for_form_tuple, widget=forms.Select(attrs={'hx-get':'load_payment_method_from/', 'hx-target':'#id_FinOfficeFrom'}))


    # finofficefrom_for_form = [('', 'Метод оплаты не выбран')] #('', 'Метод оплаты не выбран')
    # finofficefrom_for_form_tuple = tuple(i for i in finofficefrom_for_form)
    # FinOfficeFrom = forms.ChoiceField(choices=finofficefrom_for_form_tuple)

    pay_types_buy_for_form = [('', 'Тип перевода не выбран')] # ('', 'Тип перевода не выбран')
    pay_types_buy_for_form_tuple = tuple(i for i in pay_types_buy_for_form)
    Pay_type_buy = forms.ChoiceField(choices=pay_types_buy_for_form_tuple, widget=forms.Select(attrs={'hx-get':'load_payment_method_to/', 'hx-target':'#id_FinOfficeTo'}))

    # finofficeto_for_form = [('', 'Метод оплаты не выбран')]  # ('', 'Метод оплаты не выбран')
    # finofficeto_for_form_tuple = tuple(i for i in finofficeto_for_form)
    # FinOfficeTo = forms.ChoiceField(choices=finofficeto_for_form_tuple)

    Min_amount = forms.IntegerField(label='Минимальная сумма сделки')
    Max_amount = forms.IntegerField(label='Максимальная сумма сделки')

    Norm_Prib_Name_1_1 = forms.IntegerField(label='Введите первый интервал сделки (например 100-499)',
                                    widget=forms.TextInput(attrs={'class': 'form-input'}))
    Norm_Prib_Name_1_2 = forms.IntegerField(widget=forms.TextInput(attrs={'class': 'form-input'}))
    Norm_Prib_Percent_1 = forms.FloatField(label='Введите процент прибыли ')

    Norm_Prib_Name_2_1 = forms.IntegerField(label='Введите второй интервал сделки (не обязательно)',
                                       widget=forms.TextInput(attrs={'class': 'form-input'}), required = False)
    Norm_Prib_Name_2_2 = forms.IntegerField(widget=forms.TextInput(attrs={'class': 'form-input'}), required=False)
    Norm_Prib_Percent_2 = forms.FloatField(label='Введите процент прибыли  (не обязательно)', required = False)

    Norm_Prib_Name_3_1 = forms.IntegerField(label='Введите третий интервал сделки (не обязательно)',
                                       widget=forms.TextInput(attrs={'class': 'form-input'}), required = False)
    Norm_Prib_Name_3_2 = forms.IntegerField( widget=forms.TextInput(attrs={'class': 'form-input'}), required=False)
    Norm_Prib_Percent_3 = forms.FloatField(label='Введите процент прибыли  (не обязательно)', required = False)


class ChooseExchangePointsandDeals(forms.Form):
    def __init__(self, user, usertype, ExchangeName, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        pcc = Users_PCCNTR.objects.filter(TG_Contact=self.user, ContactType=usertype).values('TG_Contact', 'PCCNTR')
        pcc_name = PCCNTR.objects.get(PCCNTR_code=pcc[0]['PCCNTR'])
        ExchPCodes = EP_ExchangeID.objects.filter(PCCNTR=pcc_name.PCCNTR_code).values_list("ExchangePointID", flat=True)
        ExchPCodes = list(set(list(ExchPCodes)))



        if usertype == 'PART':
            ExchPoints1 = PCCNTR_ExchP.objects.filter(PCCNTR=pcc_name.PCCNTR_code,
                                                      ExchangePointID__in=ExchPCodes).values_list(
                "ExchangePointName").order_by("ExchangePointName")
            exchp1_for_form = []
            for ex1 in ExchPoints1:
                if (str(ex1[0]), str(ex1[0])) not in exchp1_for_form:
                    exchp1_for_form.append((str(ex1[0]), str(ex1[0])))
            exchp1_for_form_tuple = tuple(i for i in exchp1_for_form)
            self.fields['ExchangePoints'].choices = exchp1_for_form_tuple

            Deals = list(set(EP_ExchangeID.objects.filter(PCCNTR=pcc_name.PCCNTR_code).values_list('ExchangeTransferID',
                                                                                                   flat=True)))
            Deals.sort()

        elif usertype == 'ORG':
            ExchPoints1 = [ExchangeName]

            exchp1_for_form = []
            for ex1 in ExchPoints1:
                if (str(ex1), str(ex1)) not in exchp1_for_form:
                    exchp1_for_form.append((str(ex1), str(ex1)))
            exchp1_for_form_tuple = tuple(i for i in exchp1_for_form)
            self.fields['ExchangePoints'].choices = exchp1_for_form_tuple



            EPID = PCCNTR_ExchP.objects.filter(ExchangePointName=ExchangeName).values_list('ExchangePointID',flat=True).order_by('ExchangePointID')
            EPID_str = '; '.join(EPID)
            ExchangePoints = EPID_str

            EPIDs = []
            if ';' in ExchangePoints:
                while ";" in ExchangePoints:
                    ExchangePointID = ExchangePoints[:ExchangePoints.find(";")].strip()
                    EPIDs.append(ExchangePointID)
                    ExchangePoints = ExchangePoints[ExchangePoints.find(";") + 1:].strip()
                EPIDs.append(ExchangePoints[1:].strip())
            else:
                EPIDs.append(ExchangePoints.strip())
            EPIDs = list(set(EPIDs))
            Deals = []
            for EPID in EPIDs:
                exch_deals = list(
                    set(EP_ExchangeID.objects.filter(PCCNTR=pcc_name.PCCNTR_code, ExchangePointID=EPID).values_list(
                        'ExchangeTransferID', flat=True)))
                for deal in exch_deals:
                    Deals.append(deal)

            Deals = list(set(Deals))
            Deals.sort()

        if 'Currency_to_sell' in self.data:
            Currency_to_sell = str(self.data.get('Currency_to_sell'))
            currency_types = list(
                set(ExchangeID.objects.filter(SendCurrencyISO=Currency_to_sell).values_list("SendTransferType",
                                                                                            flat=True)))
            currency_types_for_form = []
            # print(str(self.data.get('Currency_to_sell')))
            if 'CRP' in currency_types:
                currency_types_for_form.append('Перевод по сети блокчейн')
            if 'CSH' in currency_types:
                currency_types_for_form.append('Наличные')
            if 'CRD' in currency_types:
                currency_types_for_form.append('Карточный перевод')
            currency_types_for_form.sort()

            curr_types_for_form = [('', 'Тип перевода не выбран')]
            for curr in currency_types_for_form:
                curr_types_for_form.append((str(curr), str(curr)))
            curr_types_for_form_tuple = tuple(i for i in curr_types_for_form)
            # print(curr_types_for_form_tuple)
            self.fields['Pay_type_sell'].choices = curr_types_for_form_tuple

        if 'Currency_to_buy' in self.data:
            Currency_to_buy = str(self.data.get('Currency_to_buy'))
            currency_types = list(
                set(ExchangeID.objects.filter(ReceiveCurrencyISO=Currency_to_buy).values_list("ReceiveTransferType",
                                                                                              flat=True)))
            currency_types_for_form = []
            if 'CRP' in currency_types:
                currency_types_for_form.append('Перевод по сети блокчейн')
            if 'CSH' in currency_types:
                currency_types_for_form.append('Наличные')
            if 'CRD' in currency_types:
                currency_types_for_form.append('Карточный перевод')
            currency_types_for_form.sort()

            curr_types_for_form = [('', 'Тип перевода не выбран')]
            for curr in currency_types_for_form:
                curr_types_for_form.append((str(curr), str(curr)))
            curr_types_for_form_tuple = tuple(i for i in curr_types_for_form)
            # print(curr_types_for_form_tuple)
            self.fields['Pay_type_buy'].choices = curr_types_for_form_tuple

        # if 'Pay_type_sell' in self.data:
        #     Pay_type_sell = str(self.data.get('Pay_type_sell'))
        #     Pay_type_sell = urllib.parse.unquote(Pay_type_sell)
        #     finofficefrom_for_form = [('', 'Метод оплаты не выбран')]
        #     if Pay_type_sell == 'Карточный перевод':
        #         FinOfficeFromTypes_Banks = list(
        #             FinOffice.objects.filter(FinOfficeType="Банки").values_list("Name_RUS", flat=True).order_by(
        #                 "Name_RUS"))
        #         for finoffice in FinOfficeFromTypes_Banks:
        #             finofficefrom_for_form.append((finoffice, finoffice))
        #     elif Pay_type_sell == 'Наличные':
        #         FinOfficeFromTypes_Banks = list(
        #             FinOffice.objects.filter(FinOfficeType="Наличные").values_list("Name_RUS", flat=True).order_by(
        #                 "Name_RUS"))
        #         for finoffice in FinOfficeFromTypes_Banks:
        #             finofficefrom_for_form.append((finoffice, finoffice))
        #     elif Pay_type_sell == 'Перевод по сети блокчейн':
        #         FinOfficeFromTypes_Crypto_Exchange = list(
        #             FinOffice.objects.filter(FinOfficeType="Криптобиржи-Отправители").values_list("Name_RUS",
        #                                                                                           flat=True))
        #         # finofficefrom_for_form.append((" - Криптобиржи", " - Криптобиржи"))
        #         for finoffice in FinOfficeFromTypes_Crypto_Exchange:
        #             finofficefrom_for_form.append((finoffice, finoffice))
        #
        #         FinOfficeFromTypes_Crypto_Wallet = list(
        #             FinOffice.objects.filter(FinOfficeType="Криптокошельки-Отправители").values_list("Name_RUS",
        #                                                                                              flat=True))
        #         # finofficefrom_for_form.append((" - Криптокошельки", " - Криптокошельки"))
        #         for finoffice in FinOfficeFromTypes_Crypto_Wallet:
        #             finofficefrom_for_form.append((finoffice, finoffice))
        #     finofficefrom_for_form_tuple = tuple(i for i in finofficefrom_for_form)
        #     #print(finoffice_for_form_tuple)
        #     self.fields['FinOfficeFrom'].choices = finofficefrom_for_form_tuple
        #
        # if 'Pay_type_buy' in self.data:
        #     Pay_type_buy = str(self.data.get('Pay_type_buy'))
        #     Pay_type_buy = urllib.parse.unquote(Pay_type_buy)
        #     finofficeto_for_form = [('', 'Метод оплаты не выбран')]
        #     if Pay_type_buy == 'Карточный перевод':
        #         FinOfficeToTypes_Banks = list(
        #             FinOffice.objects.filter(FinOfficeType="Банки").values_list("Name_RUS", flat=True).order_by(
        #                 "Name_RUS"))
        #         for finoffice in FinOfficeToTypes_Banks:
        #             finofficeto_for_form.append((finoffice, finoffice))
        #     elif Pay_type_buy == 'Наличные':
        #         FinOfficeToTypes_Banks = list(
        #             FinOffice.objects.filter(FinOfficeType="Наличные").values_list("Name_RUS", flat=True).order_by(
        #                 "Name_RUS"))
        #         for finoffice in FinOfficeToTypes_Banks:
        #             finofficeto_for_form.append((finoffice, finoffice))
        #     elif Pay_type_buy == 'Перевод по сети блокчейн':
        #         FinOfficeToTypes_Crypto_Exchange = list(
        #             FinOffice.objects.filter(FinOfficeType="Криптобиржи-Отправители").values_list("Name_RUS",
        #                                                                                           flat=True))
        #         # finofficeto_for_form.append((" - Криптобиржи", " - Криптобиржи"))
        #         for finoffice in FinOfficeToTypes_Crypto_Exchange:
        #             finofficeto_for_form.append((finoffice, finoffice))
        #
        #         FinOfficeToTypes_Crypto_Wallet = list(
        #             FinOffice.objects.filter(FinOfficeType="Криптокошельки-Отправители").values_list("Name_RUS",
        #                                                                                              flat=True))
        #         # finofficeto_for_form.append((" - Криптокошельки", " - Криптокошельки"))
        #         for finoffice in FinOfficeToTypes_Crypto_Wallet:
        #             finofficeto_for_form.append((finoffice, finoffice))
        #     finofficeto_for_form_tuple = tuple(i for i in finofficeto_for_form)
        #     self.fields['FinOfficeTo'].choices = finofficeto_for_form_tuple

        # deals_for_form = []
        # for deal in Deals:
        #     deals_for_form.append((str(deal), str(deal)))
        # deals_for_form_tuple = tuple(i for i in deals_for_form)
        # self.fields['chosen_deals'].choices = deals_for_form_tuple



    ExchangePoints = forms.ChoiceField(required=True)

    Currency_sell = list(set(list(ExchangeID.objects.values_list("SendCurrencyISO").order_by("SendCurrencyISO"))))

    curr_sell_for_form = []
    curr_sell_for_form.append(((""), ("-")))
    for curr in Currency_sell:
        curr_sell_for_form.append((str(curr[0]), str(curr[0])))
    curr_sell_for_form_tuple = tuple(i for i in curr_sell_for_form)

    Currency_to_sell = forms.ChoiceField(choices=curr_sell_for_form_tuple, widget=forms.Select(attrs={'hx-get': 'load_pay_type_sell/', 'hx-target': '#id_Pay_type_sell'}))

    Currency_buy = list(set(list(ExchangeID.objects.values_list("ReceiveCurrencyISO").order_by("ReceiveCurrencyISO"))))
    curr_buy_for_form = []
    curr_buy_for_form.append(((""), ("-")))
    for curr in Currency_buy:
        curr_buy_for_form.append((str(curr[0]), str(curr[0])))
    curr_buy_for_form_tuple = tuple(i for i in curr_buy_for_form)

    Currency_to_buy = forms.ChoiceField(choices=curr_buy_for_form_tuple, widget=forms.Select(attrs={'hx-get': 'load_pay_type_buy/', 'hx-target': '#id_Pay_type_buy'}))

    pay_types_for_form = [('', 'Тип перевода не выбран')] # ('', 'Тип перевода не выбран')
    pay_types_sell_for_form_tuple = tuple(i for i in pay_types_for_form)
    Pay_type_sell = forms.ChoiceField(choices=pay_types_sell_for_form_tuple, widget=forms.Select(attrs={'hx-get':'load_payment_method_from/', 'hx-target':'#id_FinOfficeFrom'}))


    # finofficefrom_for_form = [('', 'Метод оплаты не выбран')] #('', 'Метод оплаты не выбран')
    # finofficefrom_for_form_tuple = tuple(i for i in finofficefrom_for_form)
    # FinOfficeFrom = forms.ChoiceField(choices=finofficefrom_for_form_tuple)

    pay_types_buy_for_form = [('', 'Тип перевода не выбран')] # ('', 'Тип перевода не выбран')
    pay_types_buy_for_form_tuple = tuple(i for i in pay_types_buy_for_form)
    Pay_type_buy = forms.ChoiceField(choices=pay_types_buy_for_form_tuple, widget=forms.Select(attrs={'hx-get':'load_payment_method_to/', 'hx-target':'#id_FinOfficeTo'}))

    # finofficeto_for_form = [('', 'Метод оплаты не выбран')]  # ('', 'Метод оплаты не выбран')
    # finofficeto_for_form_tuple = tuple(i for i in finofficeto_for_form)
    # FinOfficeTo = forms.ChoiceField(choices=finofficeto_for_form_tuple)

    # chosen_deals = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, required=True)



class ChangeDealInfo(forms.Form):
    Min_amount = forms.IntegerField(label='Минимальная сумма сделки')
    Max_amount = forms.IntegerField(label='Максимальная сумма сделки')

    Norm_Prib_Name_1_1 = forms.IntegerField(label='Введите первый интервал сделки (например 100-499)',
                                    widget=forms.TextInput(attrs={'class': 'form-input'}))
    Norm_Prib_Name_1_2 = forms.IntegerField(widget=forms.TextInput(attrs={'class': 'form-input'}))
    Norm_Prib_Percent_1 = forms.FloatField(label='Введите процент прибыли ')

    Norm_Prib_Name_2_1 = forms.IntegerField(label='Введите второй интервал сделки (не обязательно)',
                                       widget=forms.TextInput(attrs={'class': 'form-input'}), required = False)
    Norm_Prib_Name_2_2 = forms.IntegerField(widget=forms.TextInput(attrs={'class': 'form-input'}), required=False)
    Norm_Prib_Percent_2 = forms.FloatField(label='Введите процент прибыли  (не обязательно)', required = False)

    Norm_Prib_Name_3_1 = forms.IntegerField(label='Введите третий интервал сделки (не обязательно)',
                                       widget=forms.TextInput(attrs={'class': 'form-input'}), required = False)
    Norm_Prib_Name_3_2 = forms.IntegerField(widget=forms.TextInput(attrs={'class': 'form-input'}), required=False)
    Norm_Prib_Percent_3 = forms.FloatField(label='Введите процент прибыли  (не обязательно)', required = False)


class ChooseDealsInfo_bonus(forms.Form):
    usdt_or_eur_for_form = (('EUR', 'EUR'), ('USDT', 'USDT'))
    Usdt_or_eur = forms.ChoiceField(choices=usdt_or_eur_for_form, label = 'Выберите валюту для интервалов')
    Bonus_Name_1_1 = forms.IntegerField(label='Введите первый интервал скидки',
                                    widget=forms.TextInput(attrs={'class': 'form-input', 'readonly':'readonly'}))
    Bonus_Name_1_2 = forms.IntegerField(widget=forms.TextInput(attrs={'class': 'form-input'}))
    Bonus_Percent_1 = forms.FloatField(label='Введите процент скидки')

    Bonus_Name_2_1 = forms.IntegerField(label='Введите второй интервал скидки',
                                       widget=forms.TextInput(attrs={'class': 'form-input'}), required = True)
    Bonus_Name_2_2 = forms.IntegerField(widget=forms.TextInput(attrs={'class': 'form-input'}), required=True)
    Bonus_Percent_2 = forms.FloatField(label='Введите процент скидки', required = True)

    Bonus_Name_3_1 = forms.IntegerField(label='Введите третий интервал скидки',
                                       widget=forms.TextInput(attrs={'class': 'form-input'}), required = True)
    Bonus_Name_3_2 = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-input', 'readonly':'readonly'}))
    Bonus_Percent_3 = forms.FloatField(label='Введите процент скидки', required = True)



class Exchangeorder(forms.Form):
    Currency_sell = list(set(list(ExchangeID.objects.values_list("SendCurrencyISO").order_by("SendCurrencyISO"))))

    curr_sell_for_form = []
    curr_sell_for_form.append(((""), ("-")))
    for curr in Currency_sell:
        curr_sell_for_form.append((str(curr[0]), str(curr[0])))
    curr_sell_for_form_tuple = tuple(i for i in curr_sell_for_form)

    Currency_to_sell = forms.ChoiceField(choices=curr_sell_for_form_tuple, widget=forms.Select(attrs={'hx-get':'load_pay_type_sell/', 'hx-target':'#id_Pay_type_sell'}))
    '#id_Currency_to_buy'

    Currency_buy = list(set(list(ExchangeID.objects.values_list("ReceiveCurrencyISO").order_by("ReceiveCurrencyISO"))))
    curr_buy_for_form = []
    curr_buy_for_form.append(((""), ("-")))
    for curr in Currency_buy:
        curr_buy_for_form.append((str(curr[0]), str(curr[0])))
    curr_buy_for_form_tuple = tuple(i for i in curr_buy_for_form)

    Currency_to_buy = forms.ChoiceField(choices=curr_buy_for_form_tuple, widget=forms.Select(attrs={'hx-get':'load_pay_type_buy/', 'hx-target':'#id_Pay_type_buy'}))

    CHOICES = (
        ('Плавающая', 'Плавающая'),
        ('Фиксированная', 'Фиксированная'),
    )
    PriceType = forms.ChoiceField(choices=CHOICES)
    # Pay_types_sell = list(set(list(ExchangeID.objects.values_list("TransferTypes", flat=True))))
    # pay_types_unique = []
    # for p_t in Pay_types_sell:
    #     while ";" in p_t:
    #         p_t_u = p_t[:p_t.find(";")]
    #         p_t = p_t[p_t.find(";") + 2:]
    #         if p_t_u not in pay_types_unique:
    #             pay_types_unique.append(p_t_u)
    #     if p_t not in pay_types_unique:
    #         pay_types_unique.append(p_t)
    # pay_types_unique.sort()
    pay_types_for_form = [('', 'Тип перевода не выбран')] # ('', 'Тип перевода не выбран')
    # for p_t in pay_types_unique:
    #     pay_types_for_form.append((p_t, p_t))
    pay_types_sell_for_form_tuple = tuple(i for i in pay_types_for_form)
    Pay_type_sell = forms.ChoiceField(choices=pay_types_sell_for_form_tuple, widget=forms.Select(attrs={'hx-get':'load_payment_method_from/', 'hx-target':'#id_FinOfficeFrom'}))

    finoffice_for_form = [('', 'Метод оплаты не выбран')] #('', 'Метод оплаты не выбран')
    # FinOfficeFromTypes_Banks = list(FinOffice.objects.filter(FinOfficeType="Банки").values_list( "Name_RUS", flat=True))
    # finoffice_for_form.append((" - Банки", " - Банки"))
    # for finoffice in FinOfficeFromTypes_Banks:
    #     finoffice_for_form.append((finoffice, finoffice))
    #
    #
    # FinOfficeFromTypes_Crypto_Exchange = list(
    #     FinOffice.objects.filter(FinOfficeType="Криптобиржи-Отправители").values_list("Name_RUS", flat=True))
    # finoffice_for_form.append((" - Криптобиржи-Отправители", " - Криптобиржи-Отправители"))
    # for finoffice in FinOfficeFromTypes_Crypto_Exchange:
    #     finoffice_for_form.append((finoffice, finoffice))
    #
    # FinOfficeFromTypes_Crypto_Wallet = list(
    #     FinOffice.objects.filter(FinOfficeType="Криптокошельки-Отправители").values_list("Name_RUS", flat=True))
    # finoffice_for_form.append((" - Криптокошельки-Отправители", " - Криптокошельки-Отправители"))
    # for finoffice in FinOfficeFromTypes_Crypto_Wallet:
    #     finoffice_for_form.append((finoffice, finoffice))
    #
    finoffice_for_form_tuple = tuple(i for i in finoffice_for_form)
    FinOfficeFrom = forms.ChoiceField(choices=finoffice_for_form_tuple)
    # Pay_types_buy = list(set(list(ExchangeID.objects.values_list("TransferTypes", flat=True))))

    # pay_types_buy_unique = []
    # for p_t in Pay_types_buy:
    #     p_t_u = p_t[p_t.find(";")+2:]
    #     if p_t_u not in pay_types_buy_unique:
    #         pay_types_buy_unique.append(p_t_u)
    pay_types_buy_for_form = [('', 'Тип перевода не выбран')] # ('', 'Тип перевода не выбран')
    # for p_t in pay_types_buy_unique:
    #     pay_types_buy_for_form.append((p_t, p_t))
    pay_types_buy_for_form_tuple = tuple(i for i in pay_types_buy_for_form)
    Pay_type_buy = forms.ChoiceField(choices=pay_types_buy_for_form_tuple, widget=forms.Select(attrs={'hx-get':'load_payment_method_to/', 'hx-target':'#id_FinOfficeTo'}))
    # COUNTRY = forms.ModelChoiceField(queryset=Countries.objects.values_list('Name_RUS', flat=True),
    #                                  to_field_name='Name_RUS', label='Страна',
    #                                  empty_label='Страна не выбрана', required=False)
    finofficeto_for_form = [('', 'Метод оплаты не выбран')]  # ('', 'Метод оплаты не выбран')
    finofficeto_for_form_tuple = tuple(i for i in finofficeto_for_form)
    FinOfficeTo = forms.ChoiceField(choices=finofficeto_for_form_tuple)

    CITY = forms.ChoiceField(label='Город')
    # dateList = [datetime.now().date() + timedelta(days=x) for x in range(numdays)]
    # dateList = [str(x.day) + "-" + str(x.month) + "-" + str(x.year) for x in dateList]

    # date_for_form = []
    # for date in dateList:
    #     date_for_form.append((date, date))
    # date_for_form_tuple = tuple(i for i in date_for_form)
    #
    # Order_day = forms.ChoiceField(choices=date_for_form_tuple)
    Order_time = forms.ChoiceField()

    CHOICES = (
        ('Курьер', 'Курьер'),
        ('Офис', 'Офис'),
    )
    DeliveryType = forms.MultipleChoiceField(choices=CHOICES, widget=forms.CheckboxSelectMultiple, required=False)

    CHOICES = (
        ('Кол-во актива к покупке', 'Кол-во актива к покупке'),
        ('Кол-во контрактива к продаже', 'Кол-во контрактива к продаже'),
    )
    Send_or_Receive = forms.ChoiceField(choices=CHOICES, required=True)
    Order_amount = forms.IntegerField()
    Limit_amount = forms.IntegerField(required=False)
    Comment = forms.CharField(max_length=10000, widget=forms.Textarea, required=False)

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        user_info = Users.objects.get(TG_Contact=user)
        cities = list(
            Cities.objects.filter(Country=user_info.COUNTRY).values_list('Name_RUS', flat=True).order_by('Name_RUS'))

        cities_for_form = []
        for city in cities:
            cities_for_form.append((str(city), str(city)))
        cities_for_form_tuple = tuple(i for i in cities_for_form)
        self.fields['CITY'].choices = cities_for_form_tuple

        numtimes = [1, 2, 3]

        url = 'http://ipinfo.io/json'
        response = urlopen(url)
        ip_data = json.load(response)
        d = datetime.now(pytz.timezone(ip_data['timezone']))  # or some other local date
        # print(d)
        current_hour = int(str(d)[11:13])
        time_for_form = []
        for num in numtimes:
            if current_hour + num + 1 == 25:
                break
            if current_hour + num < 10 and current_hour + num + 1 < 10:
                add_time = '0' + str(current_hour + num) + ':00 - 0' + str(current_hour + num + 1) + ':00'
            elif current_hour + num < 10 and current_hour + num + 1 >= 10:
                add_time = '0' + str(current_hour + num) + ':00 - ' + str(current_hour + num + 1) + ':00'
            else:
                add_time = str(current_hour + num) + ':00 - ' + str(current_hour + num + 1) + ':00'
            time_for_form.append((add_time, add_time))
        time_for_form_tuple = tuple(i for i in time_for_form)
        # print(time_for_form_tuple)
        self.fields['Order_time'].choices = time_for_form_tuple

        if 'Currency_to_sell' in self.data:
            Currency_to_sell = str(self.data.get('Currency_to_sell'))
            currency_types = list(set(ExchangeID.objects.filter(SendCurrencyISO=Currency_to_sell).values_list("SendTransferType",flat=True)))
            currency_types_for_form = []
            # print(str(self.data.get('Currency_to_sell')))
            if 'CRP' in currency_types:
                currency_types_for_form.append('Перевод по сети блокчейн')
            if 'CSH' in currency_types:
                currency_types_for_form.append('Наличные')
            if 'CRD' in currency_types:
                currency_types_for_form.append('Карточный перевод')
            currency_types_for_form.sort()

            curr_types_for_form = [('','Тип перевода не выбран')]
            for curr in currency_types_for_form:
                curr_types_for_form.append((str(curr), str(curr)))
            curr_types_for_form_tuple = tuple(i for i in curr_types_for_form)
            # print(curr_types_for_form_tuple)
            self.fields['Pay_type_sell'].choices = curr_types_for_form_tuple

        if 'Currency_to_buy' in self.data:
            Currency_to_buy = str(self.data.get('Currency_to_buy'))
            currency_types = list(set(ExchangeID.objects.filter(ReceiveCurrencyISO=Currency_to_buy).values_list("ReceiveTransferType",flat=True)))
            currency_types_for_form = []
            if 'CRP' in currency_types:
                currency_types_for_form.append('Перевод по сети блокчейн')
            if 'CSH' in currency_types:
                currency_types_for_form.append('Наличные')
            if 'CRD' in currency_types:
                currency_types_for_form.append('Карточный перевод')
            currency_types_for_form.sort()

            curr_types_for_form = [('', 'Тип перевода не выбран')]
            for curr in currency_types_for_form:
                curr_types_for_form.append((str(curr), str(curr)))
            curr_types_for_form_tuple = tuple(i for i in curr_types_for_form)
            # print(curr_types_for_form_tuple)
            self.fields['Pay_type_buy'].choices = curr_types_for_form_tuple

        if 'Pay_type_sell' in self.data:
            Pay_type_sell = str(self.data.get('Pay_type_sell'))
            Pay_type_sell = urllib.parse.unquote(Pay_type_sell)
            finoffice_for_form = [('', 'Метод оплаты не выбран')]
            if Pay_type_sell == 'Карточный перевод':
                FinOfficeFromTypes_Banks = list(Currency_source.objects.filter(FinOfficeFrom__in = list(FinOffice.objects.filter(FinOfficeType="Банки").values_list("Name_RUS", flat=True).order_by('Name_RUS'))).values_list('FinOfficeFrom', flat=True).order_by('FinOfficeFrom').distinct())
                for finoffice in FinOfficeFromTypes_Banks:
                    finoffice_for_form.append((finoffice, finoffice))
            elif Pay_type_sell == 'Наличные':
                FinOfficeFromTypes_Banks = list(Currency_source.objects.filter(FinOfficeFrom__in = list(FinOffice.objects.filter(FinOfficeType="Наличные").values_list("Name_RUS", flat=True).order_by('Name_RUS'))).values_list('FinOfficeFrom', flat=True).order_by('FinOfficeFrom').distinct())
                for finoffice in FinOfficeFromTypes_Banks:
                    finoffice_for_form.append((finoffice, finoffice))
            elif Pay_type_sell == 'Перевод по сети блокчейн':
                FinOfficeFromTypes_Crypto_Exchange = list(Currency_source.objects.filter(FinOfficeFrom__in = list(FinOffice.objects.filter(FinOfficeType="Криптобиржи-Отправители").values_list("Name_RUS", flat=True).order_by('Name_RUS'))).values_list('FinOfficeFrom', flat=True).order_by('FinOfficeFrom').distinct())
                # finoffice_for_form.append((" - Криптобиржи", " - Криптобиржи"))
                for finoffice in FinOfficeFromTypes_Crypto_Exchange:
                    finoffice_for_form.append((finoffice, finoffice))

                FinOfficeFromTypes_Crypto_Wallet = list(Currency_source.objects.filter(FinOfficeFrom__in = list(FinOffice.objects.filter(FinOfficeType="Криптокошельки-Отправители").values_list("Name_RUS", flat=True).order_by('Name_RUS'))).values_list('FinOfficeFrom', flat=True).order_by('FinOfficeFrom').distinct())
                # finoffice_for_form.append((" - Криптокошельки", " - Криптокошельки"))
                for finoffice in FinOfficeFromTypes_Crypto_Wallet:
                    finoffice_for_form.append((finoffice, finoffice))
            finoffice_for_form_tuple = tuple(i for i in finoffice_for_form)
            #print(finoffice_for_form_tuple)
            self.fields['FinOfficeFrom'].choices = finoffice_for_form_tuple

        if 'Pay_type_buy' in self.data:
            Pay_type_buy = str(self.data.get('Pay_type_buy'))
            Pay_type_buy = urllib.parse.unquote(Pay_type_buy)
            finofficeto_for_form = [('', 'Метод оплаты не выбран')]
            if Pay_type_buy == 'Карточный перевод':
                FinOfficeToTypes_Banks = list(Currency_source.objects.filter(FinOfficeTo__in=list(FinOffice.objects.filter(FinOfficeType="Банки").values_list("Name_RUS", flat=True).order_by('Name_RUS'))).values_list('FinOfficeTo', flat=True).order_by('FinOfficeTo').distinct())
                for finoffice in FinOfficeToTypes_Banks:
                    finofficeto_for_form.append((finoffice, finoffice))
            elif Pay_type_buy == 'Наличные':
                FinOfficeToTypes_Banks = list(Currency_source.objects.filter(FinOfficeTo__in=list(FinOffice.objects.filter(FinOfficeType="Наличные").values_list("Name_RUS", flat=True).order_by('Name_RUS'))).values_list('FinOfficeTo', flat=True).order_by('FinOfficeTo').distinct())
                for finoffice in FinOfficeToTypes_Banks:
                    finofficeto_for_form.append((finoffice, finoffice))
            elif Pay_type_buy == 'Перевод по сети блокчейн':
                FinOfficeToTypes_Crypto_Exchange = list(Currency_source.objects.filter(FinOfficeTo__in=list(FinOffice.objects.filter(FinOfficeType="Криптобиржи-Отправители").values_list("Name_RUS", flat=True).order_by('Name_RUS'))).values_list('FinOfficeTo', flat=True).order_by('FinOfficeTo').distinct())
                # finofficeto_for_form.append((" - Криптобиржи", " - Криптобиржи"))
                for finoffice in FinOfficeToTypes_Crypto_Exchange:
                    finofficeto_for_form.append((finoffice, finoffice))

                FinOfficeToTypes_Crypto_Wallet = list(Currency_source.objects.filter(FinOfficeTo__in=list(FinOffice.objects.filter(FinOfficeType="Криптокошельки-Отправители").values_list("Name_RUS", flat=True).order_by('Name_RUS'))).values_list('FinOfficeTo', flat=True).order_by('FinOfficeTo').distinct())
                # finofficeto_for_form.append((" - Криптокошельки", " - Криптокошельки"))
                for finoffice in FinOfficeToTypes_Crypto_Wallet:
                    finofficeto_for_form.append((finoffice, finoffice))
            finofficeto_for_form_tuple = tuple(i for i in finofficeto_for_form)
            self.fields['FinOfficeTo'].choices = finofficeto_for_form_tuple


class Changeexchangeorder(forms.Form):
    Currency_sell = list(set(list(ExchangeID.objects.values_list("SendCurrencyISO").order_by("SendCurrencyISO"))))

    curr_sell_for_form = []
    curr_sell_for_form.append(((""), ("-")))
    for curr in Currency_sell:
        curr_sell_for_form.append((str(curr[0]), str(curr[0])))
    curr_sell_for_form_tuple = tuple(i for i in curr_sell_for_form)

    Currency_to_sell = forms.ChoiceField(choices=curr_sell_for_form_tuple, widget=forms.Select(attrs={'hx-get':'load_pay_type_sell_num/', 'hx-target':'#id_Pay_type_sell'}))
    '#id_Currency_to_buy'

    Currency_buy = list(set(list(ExchangeID.objects.values_list("ReceiveCurrencyISO").order_by("ReceiveCurrencyISO"))))
    curr_buy_for_form = []
    curr_buy_for_form.append(((""), ("-")))
    for curr in Currency_buy:
        curr_buy_for_form.append((str(curr[0]), str(curr[0])))
    curr_buy_for_form_tuple = tuple(i for i in curr_buy_for_form)

    Currency_to_buy = forms.ChoiceField(choices=curr_buy_for_form_tuple, widget=forms.Select(attrs={'hx-get':'load_pay_type_buy_num/', 'hx-target':'#id_Pay_type_buy'}))

    CHOICES = (
        ('Плавающая', 'Плавающая'),
        ('Фиксированная', 'Фиксированная'),
    )
    PriceType = forms.ChoiceField(choices=CHOICES)
    # Pay_types_sell = list(set(list(ExchangeID.objects.values_list("TransferTypes", flat=True))))
    # pay_types_unique = []
    # for p_t in Pay_types_sell:
    #     while ";" in p_t:
    #         p_t_u = p_t[:p_t.find(";")]
    #         p_t = p_t[p_t.find(";") + 2:]
    #         if p_t_u not in pay_types_unique:
    #             pay_types_unique.append(p_t_u)
    #     if p_t not in pay_types_unique:
    #         pay_types_unique.append(p_t)
    # pay_types_unique.sort()
    pay_types_for_form = [('', 'Тип перевода не выбран')] # ('', 'Тип перевода не выбран')
    # for p_t in pay_types_unique:
    #     pay_types_for_form.append((p_t, p_t))
    pay_types_sell_for_form_tuple = tuple(i for i in pay_types_for_form)
    Pay_type_sell = forms.ChoiceField(choices=pay_types_sell_for_form_tuple, widget=forms.Select(attrs={'hx-get':'load_payment_method_from_num/', 'hx-target':'#id_FinOfficeFrom'}))

    finoffice_for_form = [('', 'Метод оплаты не выбран')] #('', 'Метод оплаты не выбран')
    # FinOfficeFromTypes_Banks = list(FinOffice.objects.filter(FinOfficeType="Банки").values_list( "Name_RUS", flat=True))
    # finoffice_for_form.append((" - Банки", " - Банки"))
    # for finoffice in FinOfficeFromTypes_Banks:
    #     finoffice_for_form.append((finoffice, finoffice))
    #
    #
    # FinOfficeFromTypes_Crypto_Exchange = list(
    #     FinOffice.objects.filter(FinOfficeType="Криптобиржи-Отправители").values_list("Name_RUS", flat=True))
    # finoffice_for_form.append((" - Криптобиржи-Отправители", " - Криптобиржи-Отправители"))
    # for finoffice in FinOfficeFromTypes_Crypto_Exchange:
    #     finoffice_for_form.append((finoffice, finoffice))
    #
    # FinOfficeFromTypes_Crypto_Wallet = list(
    #     FinOffice.objects.filter(FinOfficeType="Криптокошельки-Отправители").values_list("Name_RUS", flat=True))
    # finoffice_for_form.append((" - Криптокошельки-Отправители", " - Криптокошельки-Отправители"))
    # for finoffice in FinOfficeFromTypes_Crypto_Wallet:
    #     finoffice_for_form.append((finoffice, finoffice))
    #
    finoffice_for_form_tuple = tuple(i for i in finoffice_for_form)
    FinOfficeFrom = forms.ChoiceField(choices=finoffice_for_form_tuple)
    # Pay_types_buy = list(set(list(ExchangeID.objects.values_list("TransferTypes", flat=True))))

    # pay_types_buy_unique = []
    # for p_t in Pay_types_buy:
    #     p_t_u = p_t[p_t.find(";")+2:]
    #     if p_t_u not in pay_types_buy_unique:
    #         pay_types_buy_unique.append(p_t_u)
    pay_types_buy_for_form = [('', 'Тип перевода не выбран')] # ('', 'Тип перевода не выбран')
    # for p_t in pay_types_buy_unique:
    #     pay_types_buy_for_form.append((p_t, p_t))
    pay_types_buy_for_form_tuple = tuple(i for i in pay_types_buy_for_form)
    Pay_type_buy = forms.ChoiceField(choices=pay_types_buy_for_form_tuple, widget=forms.Select(attrs={'hx-get':'load_payment_method_to_num/', 'hx-target':'#id_FinOfficeTo'}))
    # COUNTRY = forms.ModelChoiceField(queryset=Countries.objects.values_list('Name_RUS', flat=True),
    #                                  to_field_name='Name_RUS', label='Страна',
    #                                  empty_label='Страна не выбрана', required=False)
    finofficeto_for_form = [('', 'Метод оплаты не выбран')]  # ('', 'Метод оплаты не выбран')
    finofficeto_for_form_tuple = tuple(i for i in finofficeto_for_form)
    FinOfficeTo = forms.ChoiceField(choices=finofficeto_for_form_tuple)

    CITY = forms.ChoiceField(label='Город')
    # dateList = [datetime.now().date() + timedelta(days=x) for x in range(numdays)]
    # dateList = [str(x.day) + "-" + str(x.month) + "-" + str(x.year) for x in dateList]

    # date_for_form = []
    # for date in dateList:
    #     date_for_form.append((date, date))
    # date_for_form_tuple = tuple(i for i in date_for_form)
    #
    # Order_day = forms.ChoiceField(choices=date_for_form_tuple)

    Order_time = forms.ChoiceField()

    CHOICES = (
        ('Курьер', 'Курьер'),
        ('Офис', 'Офис'),
    )
    DeliveryType = forms.MultipleChoiceField(choices=CHOICES, widget=forms.CheckboxSelectMultiple, required=False)

    CHOICES = (
        ('Кол-во актива к покупке', 'Кол-во актива к покупке'),
        ('Кол-во контрактива к продаже', 'Кол-во контрактива к продаже'),
    )
    Send_or_Receive = forms.ChoiceField(choices=CHOICES, required=True)
    Order_amount = forms.IntegerField()
    Limit_amount = forms.IntegerField(required=False)
    Comment = forms.CharField(max_length=10000, widget=forms.Textarea, required=False)

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print(self.data)
        self.user = user
        user_info = Users.objects.get(TG_Contact=user)
        cities = list(
            Cities.objects.filter(Country=user_info.COUNTRY).values_list('Name_RUS', flat=True).order_by('Name_RUS'))

        cities_for_form = []
        for city in cities:
            cities_for_form.append((str(city), str(city)))
        cities_for_form_tuple = tuple(i for i in cities_for_form)
        self.fields['CITY'].choices = cities_for_form_tuple

        numtimes = [1, 2, 3]

        url = 'http://ipinfo.io/json'
        response = urlopen(url)
        ip_data = json.load(response)
        d = datetime.now(pytz.timezone(ip_data['timezone']))  # or some other local date
        # print(d)
        current_hour = int(str(d)[11:13])
        time_for_form = []
        for num in numtimes:
            if current_hour + num + 1 == 25:
                break
            if current_hour + num < 10 and current_hour + num + 1 < 10:
                add_time = '0' + str(current_hour + num) + ':00 - 0' + str(current_hour + num + 1) + ':00'
            elif current_hour + num < 10 and current_hour + num + 1 >= 10:
                add_time = '0' + str(current_hour + num) + ':00 - ' + str(current_hour + num + 1) + ':00'
            else:
                add_time = str(current_hour + num) + ':00 - ' + str(current_hour + num + 1) + ':00'
            time_for_form.append((add_time, add_time))
        time_for_form_tuple = tuple(i for i in time_for_form)
        # print(time_for_form_tuple)
        self.fields['Order_time'].choices = time_for_form_tuple


        if 'Currency_to_sell' in self.data:
            Currency_to_sell = str(self.data.get('Currency_to_sell'))
            currency_types = list(set(ExchangeID.objects.filter(SendCurrencyISO=Currency_to_sell).values_list("SendTransferType",flat=True)))
            currency_types_for_form = []
            # print(str(self.data.get('Currency_to_sell')))
            if 'CRP' in currency_types:
                currency_types_for_form.append('Перевод по сети блокчейн')
            if 'CSH' in currency_types:
                currency_types_for_form.append('Наличные')
            if 'CRD' in currency_types:
                currency_types_for_form.append('Карточный перевод')
            currency_types_for_form.sort()

            curr_types_for_form = [('','Тип перевода не выбран')]
            for curr in currency_types_for_form:
                curr_types_for_form.append((str(curr), str(curr)))
            curr_types_for_form_tuple = tuple(i for i in curr_types_for_form)
            # print(curr_types_for_form_tuple)
            self.fields['Pay_type_sell'].choices = curr_types_for_form_tuple

        if 'Currency_to_buy' in self.data:
            Currency_to_buy = str(self.data.get('Currency_to_buy'))
            currency_types = list(set(ExchangeID.objects.filter(ReceiveCurrencyISO=Currency_to_buy).values_list("ReceiveTransferType",flat=True)))
            currency_types_for_form = []
            if 'CRP' in currency_types:
                currency_types_for_form.append('Перевод по сети блокчейн')
            if 'CSH' in currency_types:
                currency_types_for_form.append('Наличные')
            if 'CRD' in currency_types:
                currency_types_for_form.append('Карточный перевод')
            currency_types_for_form.sort()

            curr_types_for_form = [('', 'Тип перевода не выбран')]
            for curr in currency_types_for_form:
                curr_types_for_form.append((str(curr), str(curr)))
            curr_types_for_form_tuple = tuple(i for i in curr_types_for_form)
            # print(curr_types_for_form_tuple)
            self.fields['Pay_type_buy'].choices = curr_types_for_form_tuple

        if 'Pay_type_sell' in self.data:
            Pay_type_sell = str(self.data.get('Pay_type_sell'))
            Pay_type_sell = urllib.parse.unquote(Pay_type_sell)
            finoffice_for_form = [('', 'Метод оплаты не выбран')]
            if Pay_type_sell == 'Карточный перевод':
                FinOfficeFromTypes_Banks = list(Currency_source.objects.filter(FinOfficeFrom__in=list(
                    FinOffice.objects.filter(FinOfficeType="Банки").values_list("Name_RUS", flat=True).order_by(
                        'Name_RUS'))).values_list('FinOfficeFrom', flat=True).order_by('FinOfficeFrom').distinct())
                for finoffice in FinOfficeFromTypes_Banks:
                    finoffice_for_form.append((finoffice, finoffice))
            elif Pay_type_sell == 'Наличные':
                FinOfficeFromTypes_Banks = list(Currency_source.objects.filter(FinOfficeFrom__in=list(
                    FinOffice.objects.filter(FinOfficeType="Наличные").values_list("Name_RUS", flat=True).order_by(
                        'Name_RUS'))).values_list('FinOfficeFrom', flat=True).order_by('FinOfficeFrom').distinct())
                for finoffice in FinOfficeFromTypes_Banks:
                    finoffice_for_form.append((finoffice, finoffice))
            elif Pay_type_sell == 'Перевод по сети блокчейн':
                FinOfficeFromTypes_Crypto_Exchange = list(Currency_source.objects.filter(FinOfficeFrom__in=list(
                    FinOffice.objects.filter(FinOfficeType="Криптобиржи-Отправители").values_list("Name_RUS",
                                                                                                  flat=True).order_by(
                        'Name_RUS'))).values_list('FinOfficeFrom', flat=True).order_by('FinOfficeFrom').distinct())
                # finoffice_for_form.append((" - Криптобиржи", " - Криптобиржи"))
                for finoffice in FinOfficeFromTypes_Crypto_Exchange:
                    finoffice_for_form.append((finoffice, finoffice))

                FinOfficeFromTypes_Crypto_Wallet = list(Currency_source.objects.filter(FinOfficeFrom__in=list(
                    FinOffice.objects.filter(FinOfficeType="Криптокошельки-Отправители").values_list("Name_RUS",
                                                                                                     flat=True).order_by(
                        'Name_RUS'))).values_list('FinOfficeFrom', flat=True).order_by('FinOfficeFrom').distinct())
                # finoffice_for_form.append((" - Криптокошельки", " - Криптокошельки"))
                for finoffice in FinOfficeFromTypes_Crypto_Wallet:
                    finoffice_for_form.append((finoffice, finoffice))
            finoffice_for_form_tuple = tuple(i for i in finoffice_for_form)
            # print(finoffice_for_form_tuple)
            self.fields['FinOfficeFrom'].choices = finoffice_for_form_tuple

        if 'Pay_type_buy' in self.data:
            Pay_type_buy = str(self.data.get('Pay_type_buy'))
            Pay_type_buy = urllib.parse.unquote(Pay_type_buy)
            finofficeto_for_form = [('', 'Метод оплаты не выбран')]
            if Pay_type_buy == 'Карточный перевод':
                FinOfficeToTypes_Banks = list(Currency_source.objects.filter(FinOfficeTo__in=list(
                    FinOffice.objects.filter(FinOfficeType="Банки").values_list("Name_RUS", flat=True).order_by(
                        'Name_RUS'))).values_list('FinOfficeTo', flat=True).order_by('FinOfficeTo').distinct())
                for finoffice in FinOfficeToTypes_Banks:
                    finofficeto_for_form.append((finoffice, finoffice))
            elif Pay_type_buy == 'Наличные':
                FinOfficeToTypes_Banks = list(Currency_source.objects.filter(FinOfficeTo__in=list(
                    FinOffice.objects.filter(FinOfficeType="Наличные").values_list("Name_RUS", flat=True).order_by(
                        'Name_RUS'))).values_list('FinOfficeTo', flat=True).order_by('FinOfficeTo').distinct())
                for finoffice in FinOfficeToTypes_Banks:
                    finofficeto_for_form.append((finoffice, finoffice))
            elif Pay_type_buy == 'Перевод по сети блокчейн':
                FinOfficeToTypes_Crypto_Exchange = list(Currency_source.objects.filter(FinOfficeTo__in=list(
                    FinOffice.objects.filter(FinOfficeType="Криптобиржи-Отправители").values_list("Name_RUS",
                                                                                                  flat=True).order_by(
                        'Name_RUS'))).values_list('FinOfficeTo', flat=True).order_by('FinOfficeTo').distinct())
                # finofficeto_for_form.append((" - Криптобиржи", " - Криптобиржи"))
                for finoffice in FinOfficeToTypes_Crypto_Exchange:
                    finofficeto_for_form.append((finoffice, finoffice))

                FinOfficeToTypes_Crypto_Wallet = list(Currency_source.objects.filter(FinOfficeTo__in=list(
                    FinOffice.objects.filter(FinOfficeType="Криптокошельки-Отправители").values_list("Name_RUS",
                                                                                                     flat=True).order_by(
                        'Name_RUS'))).values_list('FinOfficeTo', flat=True).order_by('FinOfficeTo').distinct())
                # finofficeto_for_form.append((" - Криптокошельки", " - Криптокошельки"))
                for finoffice in FinOfficeToTypes_Crypto_Wallet:
                    finofficeto_for_form.append((finoffice, finoffice))
            finofficeto_for_form_tuple = tuple(i for i in finofficeto_for_form)
            self.fields['FinOfficeTo'].choices = finofficeto_for_form_tuple




class RefillBalance(forms.Form):
    # def __init__(self, user, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.user = user
    #     pcc = Users_PCCNTR.objects.filter(TG_Contact=self.user).values('TG_Contact', 'PCCNTR')
    #
    #
    #     pccntr = PCCNTR.objects.filter(PCCNTR_code=pcc[0]['PCCNTR']).values_list("PCCNTR_name")
    #     pccntr_for_form = []
    #     for pcc in pccntr:
    #         if (str(pcc[0]), str(pcc[0])) not in pccntr_for_form:
    #             pccntr_for_form.append((str(pcc[0]), str(pcc[0])))
    #     pccntr_for_form_tuple = tuple(i for i in pccntr_for_form)
    #     self.fields['PCCNTRs'].choices = pccntr_for_form_tuple
    #
    #
    # PCCNTRs = forms.ChoiceField(required=False)

    balance_Amount = forms.IntegerField()
    Payment_code = forms.CharField(max_length=1000,widget=forms.TextInput(attrs={'class': 'form-input'}))


class WithdrawBalance(forms.Form):
    # def __init__(self, user, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.user = user
    #     pcc = Users_PCCNTR.objects.filter(TG_Contact=self.user).values('TG_Contact', 'PCCNTR')
    #
    #     pccntr = PCCNTR.objects.filter(PCCNTR_code=pcc[0]['PCCNTR']).values_list("PCCNTR_name")
    #     pccntr_for_form = []
    #     for pcc in pccntr:
    #         if (str(pcc[0]), str(pcc[0])) not in pccntr_for_form:
    #             pccntr_for_form.append((str(pcc[0]), str(pcc[0])))
    #     pccntr_for_form_tuple = tuple(i for i in pccntr_for_form)
    #     self.fields['PCCNTRs'].choices = pccntr_for_form_tuple
    #
    # PCCNTRs = forms.ChoiceField(required=False)
    CHOICES = (
        ('EPC20', 'EPC20'),
        ('BEP20', 'BEP20'),
        ('TRC20', 'TRC20'),
    )
    Blockchain_transfer = forms.ChoiceField(choices=CHOICES)
    balance_Amount = forms.IntegerField()
    Payment_code = forms.CharField(max_length=1000,widget=forms.TextInput(attrs={'class': 'form-input'}))


class ChooseSourceforExchDeals(forms.Form):
    def __init__(self, Currency_types, *args, **kwargs):
        super().__init__(*args, **kwargs)
        opertypes = []
        for i in range(len(Currency_types)):
            Quotes_available = Currency_source.objects.filter(OperType = Currency_types[i][0]).values_list('QuotesRC', flat=True)
            Quotes = QuotesRC.objects.filter(QuotesRC_Code__in=Quotes_available).values_list('Name_RUS', flat=True).order_by('Name_RUS')
            Quotes_for_form = []
            for quote in Quotes:
                Quotes_for_form.append((str(quote), str(quote)))
            Quotes_for_form_tuple = tuple(i for i in Quotes_for_form)

            if i == 0:
                self.fields['chosen_quote_1'].choices = Quotes_for_form_tuple

            elif i == 1:
                self.fields['chosen_quote_2'].choices = Quotes_for_form_tuple

            elif i == 2:
                self.fields['chosen_quote_3'].choices = Quotes_for_form_tuple

            elif i == 3:
                self.fields['chosen_quote_4'].choices = Quotes_for_form_tuple

            elif i == 4:
                self.fields['chosen_quote_5'].choices = Quotes_for_form_tuple

    Quotes = QuotesRC.objects.all().values_list('Name_RUS', flat=True).order_by('Name_RUS')
    # # Banks = FinOffice.objects.filter(FinOfficeType='Банки').exclude(Name_RUS='Наличные').values_list('Name_RUS',
    # #                                                                                                      flat=True).order_by('Name_RUS')
    #
    Quotes_for_form = []
    for quote in Quotes:
        Quotes_for_form.append((str(quote), str(quote)))
    Quotes_for_form_tuple = tuple(i for i in Quotes_for_form)
    #
    # Banks_for_form = []
    # for bank in Banks:
    #     Banks_for_form.append((str(bank), str(bank)))
    # Banks_for_form_tuple = tuple(i for i in Banks_for_form)

    chosen_quote_1 = forms.ChoiceField(choices=Quotes_for_form_tuple, required=True)
    # chosen_bank_1 = forms.ChoiceField(choices=Banks_for_form_tuple, required=True)

    chosen_quote_2 = forms.ChoiceField(choices=Quotes_for_form_tuple, required=False)
    # chosen_bank_2 = forms.ChoiceField(choices=Banks_for_form_tuple, required=False)

    chosen_quote_3 = forms.ChoiceField(choices=Quotes_for_form_tuple, required=False)
    # chosen_bank_3 = forms.ChoiceField(choices=Banks_for_form_tuple, required=False)

    chosen_quote_4 = forms.ChoiceField(choices=Quotes_for_form_tuple, required=False)
    # chosen_bank_4 = forms.ChoiceField(choices=Banks_for_form_tuple, required=False)

    chosen_quote_5 = forms.ChoiceField(choices=Quotes_for_form_tuple, required=False)
    # chosen_bank_5 = forms.ChoiceField(choices=Banks_for_form_tuple, required=False)


class Exchangerequest(forms.Form):
    exchange_rate = forms.FloatField(label='Курс валюты', widget=forms.TextInput())
    reverse_exchange_rate = forms.FloatField(label='Обратный курс валюты', widget=forms.TextInput())
    amount = forms.FloatField(label='Стоимость обмена', widget=forms.TextInput())
