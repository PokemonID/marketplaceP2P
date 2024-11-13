from django.db import models

# Create your models here.
from django.db import models
from django.urls import reverse


class Users(models.Model):
    TG_Contact = models.CharField(max_length=255, verbose_name = 'Ник в Телеграм', blank=True) #
    user_ID = models.CharField(max_length=255, verbose_name = 'ID в Телеграм', blank=True) #
    ip = models.CharField(max_length=255, verbose_name = 'IP-адрес', blank=True)
    Name = models.CharField(max_length=255, verbose_name = 'Фамилия', blank=True) #
    Surname = models.CharField(max_length=255, verbose_name = 'Имя', blank=True) #
    Otchestvo = models.CharField(max_length=255, verbose_name='Отчество (при наличии)', blank=True)
    registeredDate = models.DateTimeField(auto_now_add=True, verbose_name = 'Дата регистрации', blank=True) #
    ContactType = models.CharField(max_length=255, verbose_name = 'Тип контакта', blank=True)
    GENDER = models.CharField(max_length=255, verbose_name = 'Пол', blank=True) #
    COUNTRY = models.CharField(max_length=255, verbose_name = 'Страна', blank=True) #
    CITY = models.CharField(max_length=255, verbose_name = 'Город', blank=True) #
    SUBSCRIPTION = models.CharField(max_length=255, verbose_name = 'Подписка', blank=True)
    ACTIVE = models.IntegerField(verbose_name = 'Статус пользователя', blank=True, default=1) # 0 - заблокирован, 1 - активен, 2 - временно заблокирован
    VERIFIED = models.CharField(max_length=255, verbose_name = 'Статус верификации пользователя', blank=True)
    Language = models.CharField(max_length=255, verbose_name = 'Язык', blank=True) #
    balanceFull = models.IntegerField(verbose_name='Баланс', default=0, blank=True)
    bonusPercentFull = models.IntegerField(verbose_name='Бонус', default=0, blank=True)
    #ordersVolumeFull = models.CharField(max_length=255, verbose_name = 'Оборот обменов', blank=True)
    ordersVolume = models.CharField(max_length=255, verbose_name = 'Оборот обменов (число)', blank=True)
    referralLinkUrl = models.CharField(max_length=255, verbose_name = 'Реферальная ссылка', blank=True)
    referralId = models.CharField(max_length=255, verbose_name = 'Идентификатор реферера (0: нет)', blank=True)
    referralLogin = models.CharField(max_length=255, verbose_name = 'Логин реферера (null: нет)', blank=True)
    referralsVolumeFull = models.CharField(max_length=255, verbose_name = 'Оборот реферальных обменов', blank=True)
    referralsVolume = models.CharField(max_length=255, verbose_name = 'Оборот реферальных обменов (число)', blank=True)
    rewardPercentFull = models.CharField(max_length=255, verbose_name = 'Вознаграждение по реферальной программе', blank=True)
    rewardPercent = models.CharField(max_length=255, verbose_name = 'Вознаграждение по реферальной программе (число)', blank=True)
    investmentsVolumeFull = models.CharField(max_length=255, verbose_name = 'Оборот инвестиций', blank=True)
    investmentsVolume = models.CharField(max_length=255, verbose_name = 'Оборот инвестиций (число)', blank=True)
    #Новые поля от 14.08
    BLOCKTIMESTAMP = models.DateTimeField(verbose_name = 'Время разблокировки', blank=True)
    sendinUSDT = models.FloatField(verbose_name='Отдаваемая сумма обмена в эквиваленте USDT', blank=True)
    sendinEUR = models.FloatField(verbose_name='Отдаваемая сумма обмена в эквиваленте EUR', blank=True)


    def __str__(self):
        return self.TG_Contact

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'
        ordering = ['registeredDate']

class Countries(models.Model):
    Country_code = models.CharField(max_length=255, verbose_name = 'Аббревиатура наименования страны')
    Name_RUS = models.CharField(max_length=255, verbose_name = 'Наименования страны (RUS)')
    Name_ENG = models.CharField(max_length=255, verbose_name='Наименования города (ENG)')
    Name_DEU = models.CharField(max_length=255, verbose_name='Наименования города (DEU)')
    Name_SRB = models.CharField(max_length=255, verbose_name='Наименования города (SRB)')


    def __str__(self):
        return self.Country_code

    class Meta:
        verbose_name = 'Страна'
        verbose_name_plural = 'Страны'
        ordering = ['Country_code']

class Cities(models.Model):
    City_code = models.CharField(max_length=255, verbose_name = 'Аббревиатура наименования города')
    Name_RUS = models.CharField(max_length=255, verbose_name = 'Наименования города (RUS)')
    Name_ENG = models.CharField(max_length=255, verbose_name='Наименования города (ENG)')
    Name_DEU = models.CharField(max_length=255, verbose_name='Наименования города (DEU)')
    Name_SRB = models.CharField(max_length=255, verbose_name='Наименования города (SRB)')
    Country = models.CharField(max_length=255, verbose_name='Страна')


    def __str__(self):
        return self.City_code


    class Meta:
        verbose_name = 'Город'
        verbose_name_plural = 'Города'
        ordering = ['City_code']

class Gender(models.Model):
    Gender_code = models.CharField(max_length=255, verbose_name = 'Аббревиатура наименования гендера')
    Name_RUS = models.CharField(max_length=255, verbose_name = 'Наименования гендера (RUS)')
    Name_ENG = models.CharField(max_length=255, verbose_name='Наименования гендера (ENG)')
    Name_DEU = models.CharField(max_length=255, verbose_name='Наименования гендера (DEU)')
    Name_SRB = models.CharField(max_length=255, verbose_name='Наименования гендера (SRB)')


    def __str__(self):
        return self.Gender_code

    class Meta:
        verbose_name = 'Пол'
        verbose_name_plural = 'Пол'
        ordering = ['Gender_code']

class Currency(models.Model):
    Currency_code = models.CharField(max_length=255, verbose_name = 'Аббревиатура валюты')
    Name_RUS = models.CharField(max_length=255, verbose_name = 'Наименования валюты (RUS)')
    Name_ENG = models.CharField(max_length=255, verbose_name='Наименования валюты (ENG)')
    Name_DEU = models.CharField(max_length=255, verbose_name='Наименования валюты (DEU)')
    Name_SRB = models.CharField(max_length=255, verbose_name='Наименования валюты (SRB)')


    def __str__(self):
        return self.Currency_code

    class Meta:
        verbose_name = 'Валюта'
        verbose_name_plural = 'Валюты'
        ordering = ['Currency_code']

class ContactType(models.Model):
    ContactType_code = models.CharField(max_length=255, verbose_name = 'Аббревиатура типа пользователя')
    Name_RUS = models.CharField(max_length=255, verbose_name = 'Наименования типа пользователя (RUS)')
    Name_ENG = models.CharField(max_length=255, verbose_name='Наименования типа пользователя (ENG)')
    Name_DEU = models.CharField(max_length=255, verbose_name='Наименования типа пользователя (DEU)')
    Name_SRB = models.CharField(max_length=255, verbose_name='Наименования типа пользователя (SRB)')


    def __str__(self):
        return self.ContactType_code

    class Meta:
        verbose_name = 'Тип пользователя'
        verbose_name_plural = 'Типы пользователя'
        ordering = ['ContactType_code']

class FeedBack(models.Model):
    User = models.CharField(max_length=255, verbose_name = 'ID пользователя')
    ip = models.CharField(max_length=255, verbose_name = 'IP-адрес', blank=True)
    Country_code = models.CharField(max_length=255, verbose_name='Код страны пользователя')
    Language_code = models.CharField(max_length=255, verbose_name='Код языка пользователя')
    email = models.CharField(max_length=255, verbose_name='Email пользователя')
    Name = models.CharField(max_length=255, verbose_name='Имя пользователя')
    PCCNTR = models.CharField(max_length=255, verbose_name='Центр прибыли и затрат', blank=True)
    ExchangePointID = models.CharField(max_length=255, verbose_name='ID обменника', blank=True)
    Text = models.CharField(max_length=2000, verbose_name='Текст')
    Rating = models.FloatField(verbose_name='Оценка')
    Active = models.IntegerField(verbose_name='На модерации (1 - нет; 0 - да , -1 - удален)', default=1)
    CreatedDate = models.DateTimeField(auto_now_add=True, verbose_name = 'Время отправления')
    Page = models.CharField(max_length=2000, verbose_name='Страница обращения', default='-')
    Comment = models.CharField(max_length=2000, verbose_name='Комментарий', blank=True)



    def __str__(self):
        return self.User


    class Meta:
        verbose_name = 'Обратная связь'
        verbose_name_plural = 'Обратная связь'
        ordering = ['User']

class PCCNTR(models.Model):
    PCCNTR_code = models.CharField(max_length=255, verbose_name = 'Код Центра прибыли и затрат', blank=True)
    PCCNTR_name = models.CharField(max_length=255, verbose_name = 'Наименование Центра прибыли и затрат')
    Balance = models.IntegerField(verbose_name='Баланс', default=0, blank=True)
    Bonus = models.CharField(max_length=20000, verbose_name='Диапазон скидок')
    Reserve = models.IntegerField(verbose_name='Резерв по сделкам', default=0, blank=True)


    def __str__(self):
        return self.PCCNTR_code

    class Meta:
        verbose_name = 'Центр прибыли и затрат'
        verbose_name_plural = 'Центры прибыли и затрат'
        ordering = ['PCCNTR_code']

class Users_PCCNTR(models.Model):
    TG_Contact = models.CharField(max_length=255, verbose_name = 'Ник в Телеграм')
    PCCNTR = models.CharField(max_length=255, verbose_name='Код Центра прибыли и затрат')
    ExchangePointID = models.CharField(max_length=255, verbose_name='ID обменнника', blank = True)  #
    COUNTRY = models.CharField(max_length=255, verbose_name='Страна')  #
    CITY = models.CharField(max_length=255, verbose_name='Город')  #
    Language = models.CharField(max_length=255, verbose_name='Язык')  #
    ContactType = models.CharField(max_length=255, verbose_name='Тип контакта')
    ACTIVE = models.IntegerField(verbose_name='Статус пользователя', blank=True,
                                 default=1)  # 0 - заблокирован, 1 - активен, 2 - временно заблокирован
    registeredDate = models.DateTimeField(auto_now_add=True, verbose_name='Дата регистрации', blank=True)
    Monday = models.BooleanField(verbose_name='Дни работы (Понедельник)', blank=True, default=False)
    Tuesday = models.BooleanField(verbose_name='Дни работы (Вторник)', blank=True, default=False)
    Wednesday = models.BooleanField(verbose_name='Дни работы (Среда)', blank=True, default=False)
    Thursday = models.BooleanField(verbose_name='Дни работы (Четверг)', blank=True, default=False)
    Friday = models.BooleanField(verbose_name='Дни работы (Пятница)', blank=True, default=False)
    Saturday = models.BooleanField(verbose_name='Дни работы (Суббота)', blank=True, default=False)
    Sunday = models.BooleanField(verbose_name='Дни работы (Воскресенье)', blank=True, default=False)
    ExchangePointOpenHours_Workingdays = models.CharField(max_length=255, verbose_name='Время работы (будние дни)', blank=True)
    ExchangePointOpenHours_Weekends = models.CharField(max_length=255, verbose_name='Время работы (выходные)', blank=True)
    ExchangePointAddress = models.CharField(max_length=2000, verbose_name='Адрес', blank=True)
    #Новые поля от 14.08
    sendinUSDT = models.FloatField(verbose_name='Отдаваемая сумма обмена в эквиваленте USDT', blank=True)
    sendinEUR = models.FloatField(verbose_name='Отдаваемая сумма обмена в эквиваленте EUR', blank=True)
    DiscountRate = models.FloatField(verbose_name='Размер скидки', default=0, blank=True)

    def __str__(self):
        return self.TG_Contact

    class Meta:
        verbose_name = 'Обменник'
        verbose_name_plural = 'Обменники'
        ordering = ['TG_Contact']


class PCCNTR_ExchP(models.Model):
    ExchangePointID = models.CharField(max_length=255, verbose_name='ID обменника')
    PCCNTR = models.CharField(max_length=255, verbose_name='Центр прибыли и затрат')
    ExchangePointCountry = models.CharField(max_length=255, verbose_name='Страна')
    ExchangePointCity = models.CharField(max_length=255, verbose_name='Город')
    ExchangePointName = models.CharField(max_length=255, verbose_name='Наименование обменника')
    ExchangePointOfficeCourier = models.CharField(max_length=255, verbose_name='Тип доставки')

    class Meta:
        verbose_name = 'Орг. структура обменника'
        verbose_name_plural = 'Орг. структура обменников'
        ordering = ['ExchangePointID']

class ExchangeID(models.Model):
    ExchID = models.CharField(max_length=255, verbose_name='ID обменника')
    Name_RUS = models.CharField(max_length=255, verbose_name='Наименования направления обмена (RUS)')
    Name_ENG = models.CharField(max_length=255, verbose_name='Наименования направления обмена (ENG)', blank=True)
    Name_DEU = models.CharField(max_length=255, verbose_name='Наименования направления обмена (DEU)', blank=True)
    Name_SRB = models.CharField(max_length=255, verbose_name='Наименования направления обмена (SRB)', blank=True)
    TransferTypes = models.CharField(max_length=10000, verbose_name='Типы платежей (переводов)', blank=True)
    OperTypes = models.CharField(max_length=10000, verbose_name='Типы операций', blank=True)
    SendTransferType = models.CharField(max_length=255, verbose_name='Тип отправляемой валюты', blank=True)
    ReceiveTransferType = models.CharField(max_length=255, verbose_name='Тип получаемой валюты', blank=True)
    SendCurrencyISO = models.CharField(max_length=255, verbose_name='Наименование отправляемой валюты', blank=True)
    ReceiveCurrencyISO = models.CharField(max_length=255, verbose_name='Наименование получаемой валюты', blank=True)

    class Meta:
        verbose_name = 'Направление обмена'
        verbose_name_plural = 'Направления обмена'
        ordering = ['ExchID']

class EP_ExchangeID(models.Model):
    PCCNTR = models.CharField(max_length=255, verbose_name='Центр прибыли и затрат')
    ExchangePointID = models.CharField(max_length=255, verbose_name='ID обменника')
    ExchangeTransferID = models.CharField(max_length=10000, verbose_name='Тип сделки')
    ExchTOAmount_Min = models.IntegerField(verbose_name='Минимальная сумма сделки', blank=True)
    ExchTOAmount_Max = models.IntegerField(verbose_name='Максимальная сумма сделки', blank=True)
    EP_PRFTNORM = models.CharField(max_length=20000, verbose_name='Нормы прибыли')

    class Meta:
        verbose_name = 'Обменник и направления сделки'
        verbose_name_plural = 'Обменники и направления сделки'
        ordering = ['PCCNTR', 'ExchangePointID']


class QuotesRC(models.Model):
    QuotesRC_Code = models.CharField(max_length=255, verbose_name='Код источника котировок')
    Name_RUS = models.CharField(max_length=255, verbose_name='Наименования источника котировок (RUS)')
    Name_ENG = models.CharField(max_length=255, verbose_name='Наименования источника котировок (ENG)')
    Name_DEU = models.CharField(max_length=255, verbose_name='Наименования источника котировок (DEU)')
    Name_SRB = models.CharField(max_length=255, verbose_name='Наименования источника котировок (SRB)')


    class Meta:
        verbose_name = 'Источник котировок'
        verbose_name_plural = 'Источники котировок'
        ordering = ['QuotesRC_Code']


class PCCNTR_OperTypes(models.Model):
    PCCNTR = models.CharField(max_length=255, verbose_name='Код Центра прибыли и затрат')
    OperType = models.CharField(max_length=255, verbose_name='Направление сделки')
    SendTransferType = models.CharField(max_length=255, verbose_name='Тип отправляемой валюты', blank=True)
    ReceiveTransferType = models.CharField(max_length=255, verbose_name='Тип получаемой валюты', blank=True)
    QuotesRC = models.CharField(max_length=255, verbose_name='Источник котировок')


    class Meta:
        verbose_name = 'Центр прибыли и затрат и направления сделки'
        verbose_name_plural = 'Центры прибыли и затрат и направления сделки'
        ordering = ['PCCNTR']


class FinOffice(models.Model):
    FinOfficeType = models.CharField(max_length=255, verbose_name='Тип финансового учреждения')
    Name_RUS = models.CharField(max_length=255, verbose_name='Наименования финансового учреждения (RUS)', blank=True)
    Name_ENG = models.CharField(max_length=255, verbose_name='Наименования финансового учреждения (ENG)', blank=True)
    Name_DEU = models.CharField(max_length=255, verbose_name='Наименования финансового учреждения (DEU)', blank=True)
    Name_SRB = models.CharField(max_length=255, verbose_name='Наименования финансового учреждения (SRB)', blank=True)
    FinOfficeCurr = models.CharField(max_length=255, verbose_name='Валюта финансового учреждения')

    class Meta:
        verbose_name = 'Финансовое учреждение'
        verbose_name_plural = 'Финансовые учреждения'
        ordering = ['FinOfficeType']


class Orders(models.Model):
    CreatedDate = models.DateTimeField(auto_now_add=True, verbose_name = 'Дата создания')
    TG_Contact = models.CharField(max_length=255, verbose_name='Имя пользователя')
    ExchangeID = models.CharField(max_length=255, verbose_name='ID направления сделки')
    Status = models.CharField(max_length=255, verbose_name='Статус заявки', default='Создан')
    PriceType = models.CharField(max_length=255, verbose_name='Тип цены')
    SendCurrencyISO = models.CharField(max_length=255, verbose_name='ID отдаваемой валюты')
    ReceiveCurrencyISO = models.CharField(max_length=255, verbose_name='ID получаемой валюты')
    # SendCurrencyRate = models.CharField(max_length=255, verbose_name='Курс отдаваемой валюты', blank=True, null=True)
    # ReceiveCurrencyRate = models.CharField(max_length=255, verbose_name='Курс получаемой валюты', blank=True, null=True)
    SendTransferType = models.CharField(max_length=255, verbose_name='Тип перевода отдаваемой валюты')
    ReceiveTransferType = models.CharField(max_length=255, verbose_name='Тип перевода получаемой валюты')
    SendAmount = models.IntegerField(verbose_name='Сумма отдаваемой валюты', blank=True, null=True)
    ReceiveAmount = models.IntegerField(verbose_name='Сумма получаемой валюты', blank=True, null=True)
    FinOfficeFrom = models.CharField(max_length=255, verbose_name='Финансовое учреждение отправителя')
    FinOfficeTo = models.CharField(max_length=255, verbose_name='Финансовое учреждение получателя')
    OrderDate = models.DateField(auto_now_add=True, verbose_name='Дата cделки')
    TimeInterval = models.CharField(max_length=255, verbose_name='Интервал времени сделки')
    Country = models.CharField(max_length=255, verbose_name='Страна')
    City = models.CharField(max_length=255, verbose_name='Город')
    DeliveryType = models.CharField(max_length=255, verbose_name='Тип доставки')
    OrderLimit = models.IntegerField(verbose_name='Лимит ордера', blank=True, null=True)
    Comment = models.CharField(max_length=10000, verbose_name='Комментарий', blank=True, null=True)
    RequestID = models.IntegerField(verbose_name='Номер предложения', blank=True, null=True)
    DealID = models.IntegerField(verbose_name='Номер сделки', blank=True, null=True)
    #Новые поля от 14.08
    # sendinUSDT = models.FloatField(verbose_name='Отдаваемая сумма обмена в эквиваленте USDT', blank=True)
    # sendinEUR = models.FloatField(verbose_name='Отдаваемая сумма обмена в эквиваленте EUR', blank=True)
    # receiveinUSDT = models.FloatField(verbose_name='Получаемая сумма обмена в эквиваленте USDT', blank=True)
    # receiveinEUR = models.FloatField(verbose_name='Получаемая сумма обмена в эквиваленте EUR', blank=True)
    # ExchRateUSDTEUR = models.FloatField(verbose_name='Кросс курс USDT EUR', blank=True)
    # ExchRateEURUSDT = models.FloatField(verbose_name='Кросс курс EUR USDT', blank=True)

    class Meta:
        verbose_name = 'Ордер'
        verbose_name_plural = 'Ордеры'
        ordering = ['CreatedDate']

class Payments(models.Model):
    CreatedDate = models.DateTimeField(auto_now_add=True, verbose_name = 'Дата создания')
    TG_Contact = models.CharField(max_length=255, verbose_name='Имя пользователя')
    PCCNTR = models.CharField(max_length=255, verbose_name='Центр прибыли и затрат')
    Blockchain = models.CharField(max_length=255, verbose_name='Блокчейн для перевода')
    Balance_Amount = models.IntegerField(verbose_name='Сумма для пополнения')
    Payment_data = models.CharField(max_length=255, verbose_name='Данные платежа', blank=True)
    Payment_type = models.CharField(max_length=255, verbose_name='Тип платежа', blank=True)


    class Meta:
        verbose_name = 'Изменение баланса'
        verbose_name_plural = 'Изменения баланса'
        ordering = ['-CreatedDate']


class Requests(models.Model):
    OrderID = models.IntegerField(verbose_name='Номер ордера')
    CreatedDate = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    TG_Contact = models.CharField(max_length=255, verbose_name='Имя пользователя')
    PCCNTR = models.CharField(max_length=255, verbose_name='Центры прибыли и затрат')
    ExchangePointID = models.CharField(max_length=255, verbose_name='ID обменника')
    ExchangeID = models.CharField(max_length=255, verbose_name='Идентификатор направления обмена')
    SendCurrencyISO = models.CharField(max_length=255, verbose_name='Код отдаваемой валюты')
    ReceiveCurrencyISO = models.CharField(max_length=255, verbose_name='Код получаемой валюты')
    SendAmount = models.IntegerField(verbose_name='Отдаваемая сумма (число)')
    ReceiveAmount = models.IntegerField(verbose_name='Получаемая сумма (число)')
    #SumUSDT = models.IntegerField(verbose_name='Сумма обмена в эквиваленте USDT', blank=True)
    #SumEUR = models.IntegerField(verbose_name='Сумма обмена в эквиваленте EUR', blank=True)
    DealDate = models.DateField(auto_now_add=True, verbose_name='Дата сделки')
    Status = models.CharField(max_length=255, verbose_name='Идентификатор статуса', blank=True)
    DealID = models.IntegerField(verbose_name='Номер сделки', blank=True, null=True)
    #Новые поля от 14.08
    sendinUSDT = models.FloatField(verbose_name='Отдаваемая сумма обмена в эквиваленте USDT')
    sendinEUR = models.FloatField(verbose_name='Отдаваемая сумма обмена в эквиваленте EUR')
    receiveinUSDT = models.FloatField(verbose_name='Получаемая сумма обмена в эквиваленте USDT')
    receiveinEUR = models.FloatField(verbose_name='Получаемая сумма обмена в эквиваленте EUR')
    ExchRateUSDTEUR = models.FloatField(verbose_name='Кросс курс USDT EUR', blank=True)
    ExchRateEURUSDT = models.FloatField(verbose_name='Кросс курс EUR USDT', blank=True)
    Active = models.BooleanField(verbose_name='Активно предложение или нет', default=True)

class Deals(models.Model):
    # DealID = models.IntegerField(verbose_name='Номер сделки',)
    CreatedDate = models.DateTimeField(auto_now_add=True, verbose_name = 'Дата создания')
    TG_Contact = models.CharField(max_length=255, verbose_name='Имя пользователя')
    PCCNTR = models.CharField(max_length=255, verbose_name='Центры прибыли и затрат')
    ExchangePointID = models.CharField(max_length=255, verbose_name='ID обменника')
    RequestID = models.IntegerField(verbose_name='Номер предложения')
    OrderID = models.IntegerField(verbose_name='Номер заявки')

    class Meta:
        verbose_name = 'Сделка'
        verbose_name_plural = 'Сделки'
        ordering = ['CreatedDate']

class Currency_source(models.Model):
    OperType = models.CharField(max_length=255, verbose_name='Направление сделки')
    FinOfficeFrom = models.CharField(max_length=255, verbose_name='Тип отправления', blank=True)
    FinOfficeTo = models.CharField(max_length=255, verbose_name='Тип получения', blank=True)
    SendTransferType = models.CharField(max_length=255, verbose_name='Тип отправляемой валюты', blank=True)
    ReceiveTransferType = models.CharField(max_length=255, verbose_name='Тип получаемой валюты', blank=True)
    QuotesRC = models.CharField(max_length=255, verbose_name='Источник котировок')
    Value = models.FloatField(verbose_name='Курс валют')



    class Meta:
        verbose_name = 'Курс валют'
        verbose_name_plural = 'Курсы валют'
        ordering = ['OperType']


class Notifications(models.Model):
    TG_Contact = models.CharField(max_length=255, verbose_name='Имя пользователя')
    ContactType = models.CharField(max_length=255, verbose_name='Тип контакта')
    PCCNTR = models.CharField(max_length=255, verbose_name='Код Центра прибыли и затрат', blank=True)
    ExchangePointID = models.CharField(max_length=255, verbose_name='ID обменнника', blank=True)
    Unread = models.BooleanField(verbose_name='Прочитано уведомление или нет', default=False)
    NoticeDate = models.DateTimeField(auto_now_add=True, verbose_name = 'Дата и время уведомления')
    Text = models.CharField(max_length=100000, verbose_name='Текст уведомления')

    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ['-Unread']


class DealReserve(models.Model):
    CreatedDate = models.DateTimeField(auto_now_add=True, verbose_name = 'Дата создания')
    PCCNTR = models.CharField(max_length=255, verbose_name='Центр прибыли и затрат')
    Reserve_Amount = models.IntegerField(verbose_name='Сумма для пополнения')
    OrderID = models.IntegerField(verbose_name='Номер ордера', blank=True)
    RequestID = models.IntegerField(verbose_name='Номер предложения', blank=True)
    DealID= models.IntegerField(verbose_name='Номер сделки', blank=True)

    class Meta:
        verbose_name = 'Изменение резерва'
        verbose_name_plural = 'Изменения резерва'

        ordering = ['-CreatedDate']

#Новая таблица от 27.09
class CURR_COGS_COMMISSION(models.Model):
    PCCNTR = models.CharField(max_length=255, verbose_name='Центр прибыли и затрат', blank=True)
    ReceiveCurrencyISO = models.CharField(max_length=255, verbose_name='Наименование получаемой валюты', blank=True)
    receiveTRNSFRTYPE = models.CharField(max_length=255, verbose_name='Тип получаемой валюты', blank=True)
    VALUE_COMMISSION_ABS = models.FloatField(verbose_name='Комиссия для валюты (в абсолютных значениях)', default=0)
    VALUE_COMMISSION = models.FloatField(verbose_name='Комиссия для валюты (в %)', default=0)
    VALUE_COGS = models.FloatField(verbose_name='Себестоимость для валюты (в %)', default=0)

    class Meta:
        verbose_name = 'Комиссии и себестоимость валют'
        verbose_name_plural = 'Комиссии и себестоимость валют'

        ordering = ['PCCNTR']

class Chats(models.Model):
    CreatedTime = models.DateTimeField(auto_now_add=True, verbose_name='Дата и время создания чата')
    Chat_status = models.CharField(max_length=255, verbose_name='Статус чата', default='Открыт')
    Send_User = models.CharField(max_length=255, verbose_name='ТГ-Контакт отправителя')
    Receive_User = models.CharField(max_length=255, verbose_name='ТГ-Контакт получателя')
    OrderID = models.IntegerField(verbose_name='Номер ордера', blank=True, null=True)
    RequestID = models.IntegerField(verbose_name='Номер предложения', blank=True, null=True)
    DealID = models.IntegerField(verbose_name='Номер сделки', blank=True, null=True)

    class Meta:
        verbose_name = 'Чат'
        verbose_name_plural = 'Чаты'

        ordering = ['pk']

class Messages(models.Model):
    Chat_code = models.CharField(max_length=255, verbose_name='Номер/Имя чата')
    MessageTime = models.DateTimeField(auto_now_add=True, verbose_name='Дата и время отправки сообщения')
    Send_User = models.CharField(max_length=255, verbose_name='ТГ-Контакт отправителя')
    Receive_User = models.CharField(max_length=255, verbose_name='ТГ-Контакт получателя')
    Text = models.CharField(max_length=100000, verbose_name='Текст сообщения')
    MessageType = models.CharField(max_length=255, verbose_name='Тип сообщения')

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'

        ordering = ['Chat_code', '-MessageTime']