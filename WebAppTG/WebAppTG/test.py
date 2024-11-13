import requests
from urllib.request import urlopen
import json

def tradingview_forex(currency_to_buy, currency_to_sell, amount, profit_norms):
    opertype = str(currency_to_sell) + str(currency_to_buy)
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Content-Length": "396",
        "Content-Type": "text/plain;charset=UTF-8",
        "Origin": "https://www.tradingview.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
    }
    data = {"columns": ["currency_logoid", "base_currency_logoid", "name", "description", "update_mode", "type","typespecs", "close"]
        , "filter": [{"left": "name", "operation": "match", "right": opertype}]
        , "ignore_unknown_fields": False
        , "options": {"lang": "en"}
        , "range": [0, 2000]
        , "sort": {"sortBy": "name", "sortOrder": "asc", "nullsFirst": False}
        , "preset": "forex_rates_all"
            }
    try:
        response = requests.post(url='https://scanner.tradingview.com/forex/scan', headers=headers, json=data).json()
        print(response['data'][0]['d'])
        currency_cost = float(response['data'][0]['d'][7])
        param = 0 # параметр нахождения нужного курса
    except:
        opertype = str(currency_to_sell) + str(currency_to_buy)
        data = {"columns": ["currency_logoid", "base_currency_logoid", "name", "description", "update_mode", "type",
                            "typespecs", "close"]
            , "filter": [{"left": "name", "operation": "match", "right": opertype}]
            , "ignore_unknown_fields": False
            , "options": {"lang": "en"}
            , "range": [0, 2000]
            , "sort": {"sortBy": "name", "sortOrder": "asc", "nullsFirst": False}
            , "preset": "forex_rates_all"
                }
        param = 1  # параметр нахождения нужного курса
        response = requests.post(url='https://scanner.tradingview.com/forex/scan', headers=headers, json=data).json()
        print(response['data'][0]['d'])
        currency_cost = float(response['data'][0]['d'][7])

    currency_full_value = currency_cost * amount
    max_percent = 0
    for profit_norm in profit_norms:
        if currency_full_value >= profit_norm['ExchTOAmount_Min'] and currency_full_value <= profit_norm['ExchTOAmount_Max']:
            Norm_Prib = profit_norm['EP_PRFTNORM']
            Norm_Prib_Name_1 = []
            Norm_Prib_Name_2 = []
            Norm_Prib_Percent = []
            if ';' in Norm_Prib:
                while ";" in Norm_Prib:
                    N_P = Norm_Prib[:Norm_Prib.find(";")].strip()
                    Name = N_P[:N_P.find(' ')].strip()
                    Percent = N_P[N_P.find(':') + 2:N_P.find('%')].strip()
                    Name_1 = Name[:Name.find("-")].strip()
                    Norm_Prib_Name_1.append(Name_1)
                    Name_2 = Name[Name.find("-") + 1:].strip()
                    Norm_Prib_Name_2.append(Name_2)
                    Norm_Prib_Percent.append(Percent)
                    Norm_Prib = Norm_Prib[Norm_Prib.find(";") + 1:].strip()
                Name = Norm_Prib[:Norm_Prib.find(' ')].strip()
                Percent = Norm_Prib[Norm_Prib.find(':') + 2:Norm_Prib.find('%')].strip()
                Name_1 = Name[:Name.find("-")].strip()
                Norm_Prib_Name_1.append(Name_1)
                Name_2 = Name[Name.find("-") + 1:].strip()
                Norm_Prib_Name_2.append(Name_2)
                Norm_Prib_Percent.append(Percent)
            else:
                Name = Norm_Prib[:Norm_Prib.find(' ')].strip()
                Percent = Norm_Prib[Norm_Prib.find(':') + 2:Norm_Prib.find('%')].strip()
                Name_1 = Name[:Name.find("-")].strip()
                Norm_Prib_Name_1.append(Name_1)
                Name_2 = Name[Name.find("-") + 1:].strip()
                Norm_Prib_Name_2.append(Name_2)
                Norm_Prib_Percent.append(Percent)

            for i in range(len(Norm_Prib_Name_1)):
                if currency_full_value >= float(Norm_Prib_Name_1[i]) and currency_full_value <= float(
                        Norm_Prib_Name_2[i]):
                    if max_percent < float(Norm_Prib_Percent[i]):
                        max_percent = float(Norm_Prib_Percent[i])

    if param == 0:
        currency_value = currency_cost * (1 + float(max_percent/100))
    else:
        currency_value = 1/currency_cost * (1 + float(max_percent / 100))
    currency_full_value = round(currency_value,5) * amount
    results = {'currency_value': round(currency_value,5), 'currency_full_value': round(currency_full_value,2)}
    return results
#
# print(tradingview_forex('RUB', 'USD', 500, '0-5000 USD: 7.0%'))

from WorldTimeAPI.schemas import *
from WorldTimeAPI.service import Client

payload = {"area":"America","location":"New_York"}

myclient = Client('timezone')

r = myclient.get(**payload)

if isinstance(r, ErrorJson):
    print(r.errMsg)

elif isinstance(r, DateTimeJson):
    print(r.datetime)


# regions = myclient.regions()
# print(regions.data)
from datetime import datetime
from tzlocal import get_localzone  # $ pip install tzlocal
tz = get_localzone()  # local timezone
d = datetime.now(tz)  # or some other local date
utc_offset = d.utcoffset().total_seconds()

print(int(str(d)[11:13]))

url = 'http://ipinfo.io/json'
response = urlopen(url)
print(json.load(response))
