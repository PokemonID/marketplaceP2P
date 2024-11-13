from WebAppTG.celery import app
import requests
import math
import json
import datetime
from pytz import timezone
from multiprocessing.dummy import Pool as ThreadPool
from .models import *
from .rates_parser.abcex import abcex_rates
from .rates_parser.binance import binance_p2p_rates
from .rates_parser.bybit import bybit_p2p_rates
from .rates_parser.garantex import garantex_rates
from .rates_parser.trading import trading_rates
from .rates_parser.rapira import TOOL, Rapira


#import time

# def scrab_usdt_euro_rate(username, euro_amount):
#     tz = timezone('Europe/Moscow')
#     headers = {
#         "Accept": "text/plain, */*; q=0.01",
#         "Accept-Encoding": "gzip, deflate, br, zstd",
#         "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
#         "Content-Length": "454",
#         "Origin": "https://www.tradingview.com",
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
#     }
#     data = {
#         "filter":[{"left":"name,description","operation":"match","right":"usdeu"}],
#         "options":{"lang":"ru"},
#         "markets":["forex"],
#         "symbols":{"query":{"types":["forex"]},"tickers":[]},
#         "columns":["base_currency_logoid","currency_logoid","name","close","change","change_abs","bid","ask","high","low","Recommend.All","description","type","subtype","update_mode","pricescale","minmov","fractional","minmove2"],
#         "sort":{"sortBy":"name","sortOrder":"asc"},
#         "range":[0,150]
#         }
#     response = requests.post(url='https://scanner.tradingview.com/forex/scan', headers=headers, json=data).json()
#     rate_param = 0.985
#     USDT_EUR = response['data'][0]['d'][3] * rate_param
#     date = datetime.datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
#     #print(f'{date}, tg_username = {username}, USDT_EURO = {USDT_EUR} tradingview, EURO AMOUNT = {euro_amount}')
#     return USDT_EUR
#
# def get_fiat_rates_tradingview():
#     headers = {
#         "Accept": "application/json",
#         "Accept-Encoding": "gzip, deflate, br",
#         "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
#         "Content-Length": "396",
#         "Content-Type": "text/plain;charset=UTF-8",
#         "Origin": "https://www.tradingview.com",
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
#         }
#     data = {"columns":["currency_logoid","base_currency_logoid","name","description","update_mode","type","typespecs","close","pricescale","minmov","fractional","minmove2","currency","change","change_abs","bid","ask","high","low","Recommend.All"],"ignore_unknown_fields":False,"options":{"lang":"en"},"range":[0,20000],"sort":{"sortBy":"name","sortOrder":"asc","nullsFirst":False},"preset":"forex_rates_all"}
#
#     response = requests.post(url='https://scanner.tradingview.com/forex/scan', headers=headers, json=data).json()
#     USD_RUB, EUR_RUB, BGN_RUB, EUR_USD, EUR_UAH, USD_UAH, USD_KZT, EUR_KZT, RSD_USD, RSD_EUR = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
#     for pair in response['data']:
#         if pair['d'][2] == 'USDRUB' and USD_RUB == 0:
#             USD_RUB = pair['d'][7]
#         elif pair['d'][2] == 'EURRUB' and EUR_RUB == 0:
#             EUR_RUB = pair['d'][7]
#         elif pair['d'][2] == 'USDBGN' and BGN_RUB == 0:
#             BGN_RUB = pair['d'][7]
#         elif pair['d'][2] == 'EURUSD' and EUR_USD == 0:
#             EUR_USD = pair['d'][7]
#         elif pair['d'][2] == 'EURUAH' and EUR_UAH == 0:
#             EUR_UAH = pair['d'][7]
#         elif pair['d'][2] == 'EURKZT' and EUR_KZT == 0:
#             EUR_KZT = pair['d'][7]
#         elif pair['d'][2] == 'USDUAH' and USD_UAH == 0:
#             USD_UAH = pair['d'][7]
#         elif pair['d'][2] == 'USDKZT' and USD_KZT == 0:
#             USD_KZT = pair['d'][7]
#         elif pair['d'][2] == 'RSDUSD' and RSD_USD == 0:
#             RSD_USD = pair['d'][7]
#         elif pair['d'][2] == 'RSDEUR' and RSD_EUR == 0:
#             RSD_EUR = pair['d'][7]
#         elif USD_RUB != 0 and EUR_RUB != 0 and BGN_RUB != 0 and EUR_USD != 0 and EUR_UAH != 0 and EUR_KZT != 0 and USD_UAH != 0 and USD_KZT != 0 and RSD_USD != 0 and RSD_EUR != 0:
#             break
#     BGN_RUB = USD_RUB / BGN_RUB
#     tz = timezone('Europe/Moscow')
#     date = datetime.datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
#     #print(f'{date}, USD_RUB = {USD_RUB}, EUR_RUB = {EUR_RUB}, BGN_RUB = {BGN_RUB}, EUR_USD = {EUR_USD}, USD_EUR = {1/EUR_USD}, EUR_UAH = {EUR_UAH}, EUR_KZT = {EUR_KZT} tradingview')
#     return {'USD_RUB': USD_RUB, 'EUR_RUB': EUR_RUB, 'BGN_RUB': BGN_RUB, 'EUR_USD': EUR_USD, 'USD_EUR': 1/EUR_USD, 'EUR_UAH': EUR_UAH, 'EUR_KZT': EUR_KZT, 'RSD_USD': RSD_USD, 'RSD_EUR': RSD_EUR, 'USD_UAH': USD_UAH, 'USD_KZT': USD_KZT}
#
# def scrab_usdt_kzt_rate(username, kzt_amount):
#     tz = timezone('Europe/Moscow')
#     headers = {
#         "Accept": "text/plain, */*; q=0.01",
#         "Accept-Encoding": "gzip, deflate, br",
#         "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
#         "Content-Length": "686",
#         "Origin": "https://www.tradingview.com",
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
#     }
#     data = {"filter":[{"left":"name,description","operation":"match","right":"usdtkzt"}],"options":{"lang":"en"},"filter2":{"operator":"and","operands":[{"operation":{"operator":"or","operands":[{"expression":{"left":"type","operation":"in_range","right":["spot"]}}]}}]},"markets":["crypto"],"symbols":{"query":{"types":[]},"tickers":[]},"columns":["base_currency_logoid","currency_logoid","name","close","change","change_abs","high","low","volume","24h_vol|5","24h_vol_change|5","Recommend.All","exchange","description","type","subtype","update_mode","pricescale","minmov","fractional","minmove2"],"sort":{"sortBy":"name","sortOrder":"asc"},"price_conversion":{"to_symbol":False},"range":[0,150]}
#
#     response = requests.post(url='https://scanner.tradingview.com/crypto/scan', headers=headers, json=data).json()
#     USDT_KZT = response['data'][0]['d'][3] #* 0.993
#     date = datetime.datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
#     #print(f'{date}, tg_username = {username}, USDT_KZT = {USDT_KZT} tradingview, KZT AMOUNT = {kzt_amount}')
#     return USDT_KZT
#
# def get_p2p_rate(pool_doc):
#     #________________________________Bybit
#     euro_amount = pool_doc[0]
#     usdt_euro_rate = pool_doc[1]
#     eur_rub_rate = pool_doc[2]
#     username = pool_doc[3]
#     bank_name = pool_doc[4]
#     rub_need_filter = euro_amount * eur_rub_rate
#     tz = timezone('Europe/Moscow')
#     headers = {
#         "Accept": "application/json",
#         "Accept-Encoding": "gzip, deflate, br",
#         "Accept-Language": "ru-RU",
#         "Cache-Control": "no-cache",
#         "Content-Length": "149",
#         "content-type": "application/json;charset=UTF-8",
#         "Origin": "https://www.bybit.com",
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
#     }
#     # уточнить параметры у Антона
#     if bank_name == 'Сбербанк':
#         payment = ["582"]
#     elif bank_name == 'Тинькофф':
#         payment = ["581"]
#     elif bank_name == 'Райффайзен':
#         payment = ["64"]
#     else:
#         payment = ["583"]
#     data = {"userId": 19502056,
#             "tokenId": "USDT",
#             "currencyId": "RUB",
#             "payment": payment,
#             "side": "1",
#             "size": "8",
#             "page": "1",
#             "amount": f"{rub_need_filter}",
#             "authMaker": False,
#             "canTrade": False}
#
#     r = requests.post('https://api2.bybit.com/fiat/otc/item/online', headers=headers, json=data)
#     json_data = r.json()
#
#     price = 0.0
#     found_flag = 'found'
#     nick_name_saler = 'NaN'
#     q = 0
#     for row in json_data['result']['items'][3:]:
#         order_rub_min = float(row['minAmount'])
#         order_rub_max = float(row['maxAmount'])
#         recent_execute_rate = int(row['recentExecuteRate'])
#         recent_order_num = int(row['recentOrderNum'])
#         rub_usdt = float(row['price'])  # rub/usdt
#         rub_need = euro_amount / usdt_euro_rate * rub_usdt
#         if (payment != ["583"] and rub_need >= order_rub_min and rub_need <= order_rub_max or payment == ["583"]) and recent_execute_rate >= 95 and recent_order_num >= 100:
#             q += 1
#             price += rub_usdt + 0.15
#             nick_name_saler = row['nickName']
#     if price == 0.0 or q == 0:
#         price = float(json_data['result']['items'][-1]['price']) + 0.15
#         found_flag = 'not found'
#     else:
#         price = price / q
#     date = datetime.datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
#     #print(f'{date}, tg_username = {username}, RUB_USDT P2P = {price} ({found_flag}), EURO AMOUNT = {euro_amount}, nickName = {nick_name_saler}\n')
#     return (euro_amount, price, username)
#
# #RUB Сбербанк =>EUR Cash
# #RUB Тинькоф =>EUR Cash
# #RUB Райффайзен =>EUR Cash
# #RUB Альфа (Прочие) =>EUR Cash
#
# def compute_rub_euro_amount(euro_amount, username, cash_flag, bank_name):
#     # переопределили норму доходности (09.02.2023)
#     usdt_euro_rate = scrab_usdt_euro_rate(username, euro_amount)
#     if cash_flag == True:
#         response = requests.get(url='https://garantex.org/api/v2/depth?market=usdtrub').json()
#         p2p_rub_usdt = float(response['asks'][0]['price']) * 1.0025
#     else:
#         eur_rub_rate = get_fiat_rates_tradingview()['EUR_RUB']
#         p2p_rub_usdt = get_p2p_rate((euro_amount, usdt_euro_rate, eur_rub_rate, username, bank_name))[1]
#     rub_amount = euro_amount * (p2p_rub_usdt) / usdt_euro_rate
#     return {
#         'rate': round(math.ceil(rub_amount) / euro_amount, 2),
#     }
#
# #EUR Cash => RUB Сбербанк
# #EUR Cash => RUB Тинькоф
# #EUR Cash => RUB Райффайзен
# #EUR Cash => RUB Альфа (Прочие)
#
# def compute_eur_rub_amount(currency_amount, username, bank_name):
#     # переопределили норму доходности (09.02.2023)
#     fiat_rates = get_fiat_rates_tradingview()
#     eur_rub_rate = fiat_rates['EUR_RUB']
#     eur_usd_rate = fiat_rates['EUR_USD']
#     usdt_rub_rate = get_p2p_rate((currency_amount, eur_rub_rate, 1, username, bank_name))[1]
#     test_rate = usdt_rub_rate / eur_usd_rate
#     return {
#         'rate': test_rate,
#     }
#
# #USDT TRC20 => RUB Сбербанк
# #USDT TRC20 => RUB Тинькоф
# #USDT TRC20 => RUB Райффайзен
# #USDT TRC20 => RUB Альфа (Прочие)
#
# def compute_usdt_rub_amount(rub_amount, cash_flag, bank_name):
#     if bank_name == 'Сбербанк':
#         payment = ["582"]
#     elif bank_name == 'Тинькофф':
#         payment = ["581"]
#     elif bank_name == 'Райффайзен':
#         payment = ["64"]
#     else:
#         payment = ["64", "582", "581", "583"]
#     if cash_flag == True:
#         response = requests.get(url='https://garantex.org/api/v2/depth?market=usdtrub').json()
#         usdt_rub_rate = float(response['asks'][0]['price'])
#     else:
#         headers = {
#             "Accept": "application/json",
#             "Accept-Encoding": "gzip, deflate, br",
#             "Accept-Language": "ru-RU",
#             "Cache-Control": "no-cache",
#             "Content-Length": "149",
#             "content-type": "application/json;charset=UTF-8",
#             "Origin": "https://www.bybit.com",
#             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
#         }
#         # уточнить параметры у Антона
#         data = {"userId": 19502056,
#                 "tokenId": "USDT",
#                 "currencyId": "RUB",
#                 "payment": payment,
#                 "side": "0",
#                 "size": "10",
#                 "page": "1",
#                 "amount": "",
#                 "authMaker": False,
#                 "canTrade": False}
#
#         r = requests.post('https://api2.bybit.com/fiat/otc/item/online', headers=headers, json=data)
#         json_data = r.json()
#         #usdt_rub_rate = get_p2p_rate((rub_amount, 1, username, bank_name))[1] #далее предусмотреть выбор банка в p2p
#         usdt_rub_rate = float(json_data['result']['items'][5]['price'])
#     return {
#         'rate': round(usdt_rub_rate, 4)
#     }
#
# # USDT ГРИВНЫ все банки
#
# def compute_usdt_uah_amount(uah_amount, bank_name):
#     if bank_name == 'Monobank':
#         payment = ["43"]
#     elif bank_name == 'PUMB':
#         payment = ["61"]
#     elif bank_name == 'ПриватБанк':
#         payment = ["60"]
#     elif bank_name == 'А-Банк':
#         payment = ["1"]
#     elif bank_name == 'Izibank':
#         payment = ["544"]
#     else:
#         payment = ["43", "60", "1", "61", "544"]
#     headers = {
#         "Accept": "application/json",
#         "Accept-Encoding": "gzip, deflate, br",
#         "Accept-Language": "ru-RU",
#         "Cache-Control": "no-cache",
#         "Content-Length": "149",
#         "content-type": "application/json;charset=UTF-8",
#         "Origin": "https://www.bybit.com",
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
#     }
#     # уточнить параметры у Антона
#     data = {"userId": 19502056,
#             "tokenId":"USDT",
#             "currencyId":"UAH",
#             "payment": payment,
#             "side":"1",
#             "size":"10",
#            "page":"1",
#            "amount":"",
#            "authMaker":False,
#            "canTrade":False}
#     r = requests.post('https://api2.bybit.com/fiat/otc/item/online', headers=headers, json=data)
#     json_data = r.json()
#     usdt_uah_rate = float(json_data['result']['items'][1]['price'])
#     return {
#         'rate': usdt_uah_rate
#     }
#
# #USDT TRC20 => KZT Kaspi
# #USDT TRC20 => KZT Jusan
# #USDT TRC20 => KZT Halyk
# #USDT TRC20 => KZT ЦентрКредитБанк
# #USDT TRC20 => KZT Forte
# #USDT TRC20 => KZT Freedom
# #USDT TRC20 => KZT Altyn
#
# def compute_usdt_kzt_amount(kzt_amount, bank_name):
#     if bank_name == 'Kaspi Bank':
#         payment = ["150"]
#     elif bank_name == 'Halyk Bank':
#         payment = ["203"]
#     elif bank_name == 'ЦентрКредит Банк':
#         payment = ["211"]
#     elif bank_name == 'Jysan Bank':
#         payment = ["149"]
#     elif bank_name == 'Forte Bank':
#         payment = ["144"]
#     elif bank_name == 'Altyn Bank':
#         payment = ["280"]
#     elif bank_name == 'Freedom Bank':
#         payment = ["549"]
#     else:
#         payment = ["150", "203", "280", "211", "144", "549", "149"]
#     headers = {
#         "Accept": "application/json",
#         "Accept-Encoding": "gzip, deflate, br",
#         "Accept-Language": "ru-RU",
#         "Cache-Control": "no-cache",
#         "Content-Length": "149",
#         "content-type": "application/json;charset=UTF-8",
#         "Origin": "https://www.bybit.com",
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
#     }
#     # уточнить параметры у Антона
#     data = {"userId": 19502056,
#             "tokenId":"USDT",
#             "currencyId":"KZT",
#             "payment": payment,
#             "side":"1",
#             "size":"10",
#            "page":"1",
#            "amount":"",
#            "authMaker":False,
#            "canTrade":False}
#     r = requests.post('https://api2.bybit.com/fiat/otc/item/online', headers=headers, json=data)
#     json_data = r.json()
#     usdt_kzt_rate = float(json_data['result']['items'][1]['price'])
#     return {
#         'rate': usdt_kzt_rate
#     }
# #RUB => KZT Kaspi
# #RUB => KZT Jusan
# #RUB => KZT Halyk
# #RUB => KZT ЦентрКредитБанк
# #RUB => KZT Forte
# #RUB => KZT Freedom
# #RUB => KZT Altyn
#
# def compute_rub_kzt_amount(kzt_amount, username, bank_name):
#     fiat_rates = get_fiat_rates_tradingview()
#     kzt_rub_rate = fiat_rates['USD_RUB'] / fiat_rates['USD_KZT']
#     usdt_kzt_rate = scrab_usdt_kzt_rate(username, kzt_amount)
#     p2p_rub_usdt = get_p2p_rate((kzt_amount, 1 / usdt_kzt_rate, kzt_rub_rate, username, bank_name))[1]  #далее предусмотреть выбор банка в p2p    rub_amount = kzt_amount * (1 + return_norm) * (p2p_rub_usdt) / usdt_kzt_rate
#     rub_amount = kzt_amount * (p2p_rub_usdt) / usdt_kzt_rate
#     return {
#         'rate': round(math.ceil(rub_amount) / kzt_amount, 4)
#     }
#
# #USDT TRC20 => RSD Cash
# #USDT ERC20 => RSD Cash
#
# def compute_usdt_rsd_amount():
#     rsd_usd_rate = get_fiat_rates_tradingview()['RSD_USD'] * 0.99
#     return {
#         'rate': rsd_usd_rate
#     }
#
# #RUB Сбербанк =>RSD Cash
# #RUB Тинькоф =>RSD Cash
# #RUB Райффайзен =>RSD Cash
# #RUB Альфа (Прочие) =>RSD Cash
#
# def compute_rub_rsd_amount(rsd_amount, username, cash_flag, bank_name):
#     rsd_usd_rate = get_fiat_rates_tradingview()['RSD_USD'] * 0.99
#     if cash_flag:
#         response = requests.get(url='https://garantex.org/api/v2/depth?market=usdtrub').json()
#         p2p_rub_usdt = float(response['asks'][0]['price']) * 1.0025
#     else:
#         fiat_rates = get_fiat_rates_tradingview()
#         rub_rsd_rate = 1 / (fiat_rates['USD_RUB'] * fiat_rates['RSD_USD'])
#         p2p_rub_usdt = get_p2p_rate((rsd_amount, rsd_usd_rate, rub_rsd_rate, username, bank_name))[1] #далее предусмотреть выбор банка в p2p
#     rub_amount = rsd_amount * (p2p_rub_usdt) * rsd_usd_rate
#     return {
#         'rate': round(rsd_amount / math.ceil(rub_amount), 3)
#     }
#
# #RSD Cash => RUB Сбербанк
# #RSD Cash => RUB Тинькоф
# #RSD Cash => RUB Райффайзен
# #RSD Cash => RUB Альфа (Прочие)
#
# def compute_rsd_rub_amount(currency_amount, username, bank_name):
#     fiat_rates = get_fiat_rates_tradingview()
#     rsd_usd_rate = fiat_rates['RSD_USD']
#     rub_rsd_rate = 1 / (fiat_rates['USD_RUB'] * fiat_rates['RSD_USD'])
#     usdt_rub_rate = get_p2p_rate((currency_amount, 1/rsd_usd_rate, rub_rsd_rate, username, bank_name))[1]
#     currency_from_amount = currency_amount / usdt_rub_rate / rsd_usd_rate / 0.987
#     test_rate = usdt_rub_rate / rsd_usd_rate
#     return {
#         'rate': round(currency_amount / math.ceil(currency_from_amount), 3)
#     }
#

# abcex
@app.task #регистриуем таску
def update_currency():
    bearer_token = 'eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJrenNJYUxtY0R2RVBlRGRYVHVQOXVYN050UzZDSXZ5WXR5VXhwemRrdEZJIn0.eyJleHAiOjE3NTM5NjAzNDQsImlhdCI6MTcyMjQyNDM0NCwianRpIjoiNzFhNzZiZWItMzY3Yy00ZGEzLWJjMzQtZDc4NWU0OTAzYzZhIiwiaXNzIjoiaHR0cHM6Ly9hdXRoLmFiY2V4LmlvL3JlYWxtcy9hYmNleCIsImF1ZCI6ImFjY291bnQiLCJzdWIiOiI4Zjc0MDRmNy03MzU2LTQ0YmQtOGRhNS1iMGM2NDhiZmM2MDUiLCJ0eXAiOiJCZWFyZXIiLCJhenAiOiJhcHAtYXBpLWtleWNsb2FrLWdhdGV3YXkiLCJzZXNzaW9uX3N0YXRlIjoiMDMyMGFkYmYtZWNkNC00OTQ1LTlmNzctOWFmODJkNTFiNDYyIiwiYWNyIjoiMSIsImFsbG93ZWQtb3JpZ2lucyI6WyIvKiJdLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiIsImRlZmF1bHQtcm9sZXMtYWJjZXguaW8iXX0sInJlc291cmNlX2FjY2VzcyI6eyJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19LCJzY29wZSI6IiIsInNpZCI6IjAzMjBhZGJmLWVjZDQtNDk0NS05Zjc3LTlhZjgyZDUxYjQ2MiIsImlkIjoiN2ZhOWEwYTktMTc5Yi00Y2ViLWFkMTMtZTgyODhkMDcwMTY5In0.Tcj2rJxjuLrpmFatlCCt8pNweNwd9a_6EmEvQP8xzxiXNNw1Hwaa7CA2LU4c3op6NFkS6utN90C0s-bW9yxGvxqJRFYHBETH1sVzGGK7GWjurjTJkGX9R_HztQMZxVAHpE4Tzc78dNBLYp3Ea3QJVRP4973KEEgei4egvxcgo6eEixnFD0uW2nO9lnpQjAPd0lx43m5f-lp64GKQAEZvocFI2VmpCHjCraqGuM3-RNGweWry9Tdqc_m-pwc3MLGX4YsPNuC3JOfjknaQaBH6wqP1f_AdyrPkMZPlDwkMAME_yT3KCI7sTGAhlqROm69ab3L1g_o8zJzpPvE7xlQ6eA'
    print('abcex')
    USDT_RUB = abcex_rates(currency_pair='USDTRUB', side='')
    curr_source = Currency_source.objects.get(OperType = 'USDT => RUB', SendTransferType='CRP',  ReceiveTransferType='CSH',
                                                FinOfficeFrom = 'TRC20', FinOfficeTo = 'Наличные', QuotesRC='ABCExALL')
    curr_source.Value = round(USDT_RUB,2)
    curr_source.save()
    curr_source = Currency_source.objects.get(OperType = 'USDT => RUB', SendTransferType='CRP',  ReceiveTransferType='CRD',
                                                FinOfficeFrom = 'TRC20', FinOfficeTo = 'Сбербанк', QuotesRC='ABCExALL')
    curr_source.Value = round(USDT_RUB,2)
    curr_source.save()
    curr_source = Currency_source.objects.get(OperType = 'USDT => RUB', SendTransferType='CRP',  ReceiveTransferType='CRD',
                                                FinOfficeFrom = 'TRC20', FinOfficeTo = 'Тинькофф', QuotesRC='ABCExALL')
    curr_source.Value = round(USDT_RUB,2)
    curr_source.save()

    curr_source = Currency_source.objects.get(OperType = 'RUB => USDT', SendTransferType='CSH',  ReceiveTransferType='CRP',
                                                FinOfficeFrom = 'Наличные', FinOfficeTo = 'TRC20', QuotesRC='ABCExALL')
    curr_source.Value = round(1/USDT_RUB,5)
    curr_source.save()
    curr_source = Currency_source.objects.get(OperType = 'RUB => USDT', SendTransferType='CRD',  ReceiveTransferType='CRP',
                                                FinOfficeFrom = 'Сбербанк', FinOfficeTo = 'TRC20', QuotesRC='ABCExALL')
    curr_source.Value = round(1/USDT_RUB,5)
    curr_source.save()
    curr_source = Currency_source.objects.get(OperType = 'RUB => USDT', SendTransferType='CRD',  ReceiveTransferType='CRP',
                                                FinOfficeFrom = 'Тинькофф', FinOfficeTo = 'TRC20', QuotesRC='ABCExALL')
    curr_source.Value = round(1/USDT_RUB,5)
    curr_source.save()

    # print(abcex_rates(currency_pair='USDTEUR', side=''))
    # print(1/abcex_rates(currency_pair='USDTEUR', side=''))

    # binance
    binance_filter_payloads = {
        "BNCALL": {
            "publisherType": None,
            "range": [0, 1]
        },
        "BNCALLMCHT": {
            "publisherType": 'merchant',
            "range": [0, 1]
        },
        "BNCMCHTAVG1": {
            "publisherType": 'merchant',
            "range": [2, 15]
        },
        "BNCMCHTAVG2": {
            "publisherType": 'merchant',
            "range": [4, 15]
        }
    }
    print('binance')
    # print(binance_p2p_rates(currency="EUR", bank_name="Райффайзенбанк", filter="BNCALL", side='BUY'))
    # print(binance_p2p_rates(currency="RUB", bank_name="Сбербанк", filter="BNCALLMCHT", side='BUY'))
    # print(binance_p2p_rates(currency="RUB", bank_name="Сбербанк", filter="BNCMCHTAVG1", side='BUY'))
    # print(binance_p2p_rates(currency="RUB", bank_name="Сбербанк", filter="BNCMCHTAVG2", side='BUY'))

    # bybit
    bybit_banks = {"Сбербанк": "582", "Тинькофф": "581", "Райффайзен": "64", "Halyk": "203",
                   "Kaspi": "150", "Jusan": "563", "Freedom": "549", "Raiffeisenbank": "64",
                   "Revolut": "65", "UniCredit": "166","Revolut": "65", "UniCredit": "166",
                   "Monobank": "43", "Monobank": "60","Izibank": "544", "PUMB": "61", "SBP": "382"}
    bybit_filter_payloads = {
        "BBTALL": {
            "size": "5",
            "page": "1",
            "authMaker": False,
            "canTrade": False,
            "range": [0, 1]
        },
        "BBTALLMCHT": {
            "size": "5",
            "page": "1",
            "authMaker": True,
            "canTrade": True,
            "range": [0, 1]
        },
        "BBTMCHTAVG1": {
            "size": "15",
            "page": "1",
            "authMaker": True,
            "canTrade": True,
            "range": [2, 15]
        },
        "BBTMCHTAVG2": {
            "size": "15",
            "page": "1",
            "authMaker": True,
            "canTrade": True,
            "range": [4, 15]
        }
    }
    print('bybit')

    USDT_RUB_SBER = bybit_p2p_rates(currency="RUB", bank_name="Сбербанк", filter="BBTALL", side='bid')
    USDT_RUB_TINK = bybit_p2p_rates(currency="RUB", bank_name="Тинькофф", filter="BBTALL", side='bid')
    USDT_RUB_CASH = bybit_p2p_rates(currency="RUB", bank_name="SBP", filter="BBTALL", side='bid')
    USDT_EUR_CASH = bybit_p2p_rates(currency="EUR", bank_name="SBP", filter="BBTALL", side='bid')
    curr_source = Currency_source.objects.get(OperType = 'USDT => RUB', SendTransferType='CRP',  ReceiveTransferType='CSH',
                                                FinOfficeFrom = 'TRC20', FinOfficeTo = 'Наличные', QuotesRC='BBTALL')
    curr_source.Value = round(USDT_RUB_CASH,2)
    curr_source.save()
    curr_source = Currency_source.objects.get(OperType = 'USDT => RUB', SendTransferType='CRP',  ReceiveTransferType='CRD',
                                                FinOfficeFrom = 'TRC20', FinOfficeTo = 'Сбербанк', QuotesRC='BBTALL')
    curr_source.Value = round(USDT_RUB_SBER,2)
    curr_source.save()
    curr_source = Currency_source.objects.get(OperType = 'USDT => RUB', SendTransferType='CRP',  ReceiveTransferType='CRD',
                                                FinOfficeFrom = 'TRC20', FinOfficeTo = 'Тинькофф', QuotesRC='BBTALL')
    curr_source.Value = round(USDT_RUB_TINK,2)
    curr_source.save()

    curr_source = Currency_source.objects.get(OperType = 'RUB => USDT', SendTransferType='CSH',  ReceiveTransferType='CRP',
                                                FinOfficeFrom = 'Наличные', FinOfficeTo = 'TRC20', QuotesRC='BBTALL')
    curr_source.Value = round(1/USDT_RUB_CASH,5)
    curr_source.save()
    curr_source = Currency_source.objects.get(OperType = 'RUB => USDT', SendTransferType='CRD',  ReceiveTransferType='CRP',
                                                FinOfficeFrom = 'Сбербанк', FinOfficeTo = 'TRC20', QuotesRC='BBTALL')
    curr_source.Value = round(1/USDT_RUB_SBER,5)
    curr_source.save()
    curr_source = Currency_source.objects.get(OperType = 'RUB => USDT', SendTransferType='CRD',  ReceiveTransferType='CRP',
                                                FinOfficeFrom = 'Тинькофф', FinOfficeTo = 'TRC20', QuotesRC='BBTALL')
    curr_source.Value = round(1/USDT_RUB_TINK,5)
    curr_source.save()

    curr_source = Currency_source.objects.get(OperType = 'USDT => EUR', SendTransferType='CRP',  ReceiveTransferType='CSH',
                                                FinOfficeFrom = 'TRC20', FinOfficeTo = 'Наличные', QuotesRC='BBTALL')
    curr_source.Value = round(USDT_EUR_CASH,2)
    curr_source.save()
    curr_source = Currency_source.objects.get(OperType = 'EUR => USDT', SendTransferType='CSH',  ReceiveTransferType='CRP',
                                                FinOfficeFrom = 'Наличные', FinOfficeTo = 'TRC20', QuotesRC='BBTALL')
    curr_source.Value = round(1/USDT_EUR_CASH,5)
    curr_source.save()


    USDT_RUB_SBER = bybit_p2p_rates(currency="RUB", bank_name="Сбербанк", filter="BBTALLMCHT", side='bid')
    USDT_RUB_TINK = bybit_p2p_rates(currency="RUB", bank_name="Тинькофф", filter="BBTALLMCHT", side='bid')
    USDT_RUB_CASH = bybit_p2p_rates(currency="RUB", bank_name="SBP", filter="BBTALLMCHT", side='bid')
    USDT_EUR_CASH = bybit_p2p_rates(currency="EUR", bank_name="SBP", filter="BBTALLMCHT", side='bid')
    curr_source = Currency_source.objects.get(OperType = 'USDT => RUB', SendTransferType='CRP',  ReceiveTransferType='CSH',
                                                FinOfficeFrom = 'TRC20', FinOfficeTo = 'Наличные', QuotesRC='BBTALLMCHT')
    curr_source.Value = round(USDT_RUB_CASH,2)
    curr_source.save()
    curr_source = Currency_source.objects.get(OperType = 'USDT => RUB', SendTransferType='CRP',  ReceiveTransferType='CRD',
                                                FinOfficeFrom = 'TRC20', FinOfficeTo = 'Сбербанк', QuotesRC='BBTALLMCHT')
    curr_source.Value = round(USDT_RUB_SBER,2)
    curr_source.save()
    curr_source = Currency_source.objects.get(OperType = 'USDT => RUB', SendTransferType='CRP',  ReceiveTransferType='CRD',
                                                FinOfficeFrom = 'TRC20', FinOfficeTo = 'Тинькофф', QuotesRC='BBTALLMCHT')
    curr_source.Value = round(USDT_RUB_TINK,2)
    curr_source.save()

    curr_source = Currency_source.objects.get(OperType = 'RUB => USDT', SendTransferType='CSH',  ReceiveTransferType='CRP',
                                                FinOfficeFrom = 'Наличные', FinOfficeTo = 'TRC20', QuotesRC='BBTALLMCHT')
    curr_source.Value = round(1/USDT_RUB_CASH,5)
    curr_source.save()
    curr_source = Currency_source.objects.get(OperType = 'RUB => USDT', SendTransferType='CRD',  ReceiveTransferType='CRP',
                                                FinOfficeFrom = 'Сбербанк', FinOfficeTo = 'TRC20', QuotesRC='BBTALLMCHT')
    curr_source.Value = round(1/USDT_RUB_SBER,5)
    curr_source.save()
    curr_source = Currency_source.objects.get(OperType = 'RUB => USDT', SendTransferType='CRD',  ReceiveTransferType='CRP',
                                                FinOfficeFrom = 'Тинькофф', FinOfficeTo = 'TRC20', QuotesRC='BBTALLMCHT')
    curr_source.Value = round(1/USDT_RUB_TINK,5)
    curr_source.save()

    curr_source = Currency_source.objects.get(OperType = 'USDT => EUR', SendTransferType='CRP',  ReceiveTransferType='CSH',
                                                FinOfficeFrom = 'TRC20', FinOfficeTo = 'Наличные', QuotesRC='BBTALLMCHT')
    curr_source.Value = round(USDT_EUR_CASH,2)
    curr_source.save()
    curr_source = Currency_source.objects.get(OperType = 'EUR => USDT', SendTransferType='CSH',  ReceiveTransferType='CRP',
                                                FinOfficeFrom = 'Наличные', FinOfficeTo = 'TRC20', QuotesRC='BBTALLMCHT')
    curr_source.Value = round(1/USDT_EUR_CASH,5)
    curr_source.save()

    USDT_RUB_SBER = bybit_p2p_rates(currency="RUB", bank_name="Сбербанк", filter="BBTMCHTAVG1", side='bid')
    USDT_RUB_TINK = bybit_p2p_rates(currency="RUB", bank_name="Тинькофф", filter="BBTMCHTAVG1", side='bid')
    USDT_RUB_CASH = bybit_p2p_rates(currency="RUB", bank_name="SBP", filter="BBTMCHTAVG1", side='bid')
    curr_source = Currency_source.objects.get(OperType = 'USDT => RUB', SendTransferType='CRP',  ReceiveTransferType='CSH',
                                                FinOfficeFrom = 'TRC20', FinOfficeTo = 'Наличные', QuotesRC='BBTMCHTAVG1')
    curr_source.Value = round(USDT_RUB_CASH,2)
    curr_source.save()
    curr_source = Currency_source.objects.get(OperType = 'USDT => RUB', SendTransferType='CRP',  ReceiveTransferType='CRD',
                                                FinOfficeFrom = 'TRC20', FinOfficeTo = 'Сбербанк', QuotesRC='BBTMCHTAVG1')
    curr_source.Value = round(USDT_RUB_SBER,2)
    curr_source.save()
    curr_source = Currency_source.objects.get(OperType = 'USDT => RUB', SendTransferType='CRP',  ReceiveTransferType='CRD',
                                                FinOfficeFrom = 'TRC20', FinOfficeTo = 'Тинькофф', QuotesRC='BBTMCHTAVG1')
    curr_source.Value = round(USDT_RUB_TINK,2)
    curr_source.save()

    curr_source = Currency_source.objects.get(OperType = 'RUB => USDT', SendTransferType='CSH',  ReceiveTransferType='CRP',
                                                FinOfficeFrom = 'Наличные', FinOfficeTo = 'TRC20', QuotesRC='BBTMCHTAVG1')
    curr_source.Value = round(1/USDT_RUB_CASH,5)
    curr_source.save()
    curr_source = Currency_source.objects.get(OperType = 'RUB => USDT', SendTransferType='CRD',  ReceiveTransferType='CRP',
                                                FinOfficeFrom = 'Сбербанк', FinOfficeTo = 'TRC20', QuotesRC='BBTMCHTAVG1')
    curr_source.Value = round(1/USDT_RUB_SBER,5)
    curr_source.save()
    curr_source = Currency_source.objects.get(OperType = 'RUB => USDT', SendTransferType='CRD',  ReceiveTransferType='CRP',
                                                FinOfficeFrom = 'Тинькофф', FinOfficeTo = 'TRC20', QuotesRC='BBTMCHTAVG1')
    curr_source.Value = round(1/USDT_RUB_TINK,5)
    curr_source.save()

    USDT_RUB_SBER = bybit_p2p_rates(currency="RUB", bank_name="Сбербанк", filter="BBTMCHTAVG2", side='bid')
    USDT_RUB_TINK = bybit_p2p_rates(currency="RUB", bank_name="Тинькофф", filter="BBTMCHTAVG2", side='bid')
    USDT_RUB_CASH = bybit_p2p_rates(currency="RUB", bank_name="SBP", filter="BBTMCHTAVG2", side='bid')
    curr_source = Currency_source.objects.get(OperType = 'USDT => RUB', SendTransferType='CRP',  ReceiveTransferType='CSH',
                                                FinOfficeFrom = 'TRC20', FinOfficeTo = 'Наличные', QuotesRC='BBTMCHTAVG2')
    curr_source.Value = round(USDT_RUB_CASH,2)
    curr_source.save()
    curr_source = Currency_source.objects.get(OperType = 'USDT => RUB', SendTransferType='CRP',  ReceiveTransferType='CRD',
                                                FinOfficeFrom = 'TRC20', FinOfficeTo = 'Сбербанк', QuotesRC='BBTMCHTAVG2')
    curr_source.Value = round(USDT_RUB_SBER,2)
    curr_source.save()
    curr_source = Currency_source.objects.get(OperType = 'USDT => RUB', SendTransferType='CRP',  ReceiveTransferType='CRD',
                                                FinOfficeFrom = 'TRC20', FinOfficeTo = 'Тинькофф', QuotesRC='BBTMCHTAVG2')
    curr_source.Value = round(USDT_RUB_TINK,2)
    curr_source.save()

    curr_source = Currency_source.objects.get(OperType = 'RUB => USDT', SendTransferType='CSH',  ReceiveTransferType='CRP',
                                                FinOfficeFrom = 'Наличные', FinOfficeTo = 'TRC20', QuotesRC='BBTMCHTAVG2')
    curr_source.Value = round(1/USDT_RUB_CASH,5)
    curr_source.save()
    curr_source = Currency_source.objects.get(OperType = 'RUB => USDT', SendTransferType='CRD',  ReceiveTransferType='CRP',
                                                FinOfficeFrom = 'Сбербанк', FinOfficeTo = 'TRC20', QuotesRC='BBTMCHTAVG2')
    curr_source.Value = round(1/USDT_RUB_SBER,5)
    curr_source.save()
    curr_source = Currency_source.objects.get(OperType = 'RUB => USDT', SendTransferType='CRD',  ReceiveTransferType='CRP',
                                                FinOfficeFrom = 'Тинькофф', FinOfficeTo = 'TRC20', QuotesRC='BBTMCHTAVG2')
    curr_source.Value = round(1/USDT_RUB_TINK,5)
    curr_source.save()

    # print(bybit_p2p_rates(currency="EUR", bank_name="SBP", filter="BBTMCHTAVG1", side='bid'))
    # print(bybit_p2p_rates(currency="EUR", bank_name="SBP", filter="BBTMCHTAVG2", side='bid'))

    # print(1/bybit_p2p_rates(currency="EUR", bank_name="SBP", filter="BBTMCHTAVG1", side='bid'))
    # print(1/bybit_p2p_rates(currency="EUR", bank_name="SBP", filter="BBTMCHTAVG2", side='bid'))

    # garantex
    print('garantex')
    USDT_RUB = garantex_rates(currency_pair='usdtrub', side='bids')
    USDT_EUR = garantex_rates(currency_pair='usdteur', side='bids')
    curr_source = Currency_source.objects.get(OperType = 'USDT => RUB', SendTransferType='CRP',  ReceiveTransferType='CSH',
                                                FinOfficeFrom = 'TRC20', FinOfficeTo = 'Наличные', QuotesRC='GARALL')
    curr_source.Value = round(USDT_RUB,2)
    curr_source.save()
    curr_source = Currency_source.objects.get(OperType = 'USDT => RUB', SendTransferType='CRP',  ReceiveTransferType='CRD',
                                                FinOfficeFrom = 'TRC20', FinOfficeTo = 'Сбербанк', QuotesRC='GARALL')
    curr_source.Value = round(USDT_RUB,2)
    curr_source.save()
    curr_source = Currency_source.objects.get(OperType = 'USDT => RUB', SendTransferType='CRP',  ReceiveTransferType='CRD',
                                                FinOfficeFrom = 'TRC20', FinOfficeTo = 'Тинькофф', QuotesRC='GARALL')
    curr_source.Value = round(USDT_RUB,2)
    curr_source.save()

    curr_source = Currency_source.objects.get(OperType = 'RUB => USDT', SendTransferType='CSH',  ReceiveTransferType='CRP',
                                                FinOfficeFrom = 'Наличные', FinOfficeTo = 'TRC20', QuotesRC='GARALL')
    curr_source.Value = round(1/USDT_RUB,5)
    curr_source.save()
    curr_source = Currency_source.objects.get(OperType = 'RUB => USDT', SendTransferType='CRD',  ReceiveTransferType='CRP',
                                                FinOfficeFrom = 'Сбербанк', FinOfficeTo = 'TRC20', QuotesRC='GARALL')
    curr_source.Value = round(1/USDT_RUB,5)
    curr_source.save()
    curr_source = Currency_source.objects.get(OperType = 'RUB => USDT', SendTransferType='CRD',  ReceiveTransferType='CRP',
                                                FinOfficeFrom = 'Тинькофф', FinOfficeTo = 'TRC20', QuotesRC='GARALL')
    curr_source.Value = round(1/USDT_RUB,5)
    curr_source.save()

    curr_source = Currency_source.objects.get(OperType = 'USDT => EUR', SendTransferType='CRP',  ReceiveTransferType='CSH',
                                                FinOfficeFrom = 'TRC20', FinOfficeTo = 'Наличные', QuotesRC='GARALL')
    curr_source.Value = round(USDT_EUR,2)
    curr_source.save()
    curr_source = Currency_source.objects.get(OperType = 'EUR => USDT', SendTransferType='CSH',  ReceiveTransferType='CRP',
                                                FinOfficeFrom = 'Наличные', FinOfficeTo = 'TRC20', QuotesRC='GARALL')
    curr_source.Value = round(1/USDT_EUR,5)
    curr_source.save()

    # tradingview
    print('tradingview')
    # print(trading_rates(currency_pair='usdtrub'))

    # rapira
    hosts = "https://api.rapira.net"
    rapira_uid = "adb339b6-8449-4b14-8c37-0aeda9c1c582"
    rapira_secret = "80fc9bda520142d6bfadc4e2fa197be2"
    rapira = Rapira(hosts=hosts, rapira_uid=rapira_uid)
    print('rapira')
    USDT_RUB = rapira.get_pair_info(rapira.get_rates_json(), 'USDT/RUB')['close']

    curr_source = Currency_source.objects.get(OperType = 'USDT => RUB', SendTransferType='CRP',  ReceiveTransferType='CSH',
                                                FinOfficeFrom = 'TRC20', FinOfficeTo = 'Наличные', QuotesRC='RAPIRAALL')
    curr_source.Value = round(USDT_RUB,2)
    curr_source.save()
    curr_source = Currency_source.objects.get(OperType = 'USDT => RUB', SendTransferType='CRP',  ReceiveTransferType='CRD',
                                                FinOfficeFrom = 'TRC20', FinOfficeTo = 'Сбербанк', QuotesRC='RAPIRAALL')
    curr_source.Value = round(USDT_RUB,2)
    curr_source.save()
    curr_source = Currency_source.objects.get(OperType = 'USDT => RUB', SendTransferType='CRP',  ReceiveTransferType='CRD',
                                                FinOfficeFrom = 'TRC20', FinOfficeTo = 'Тинькофф', QuotesRC='RAPIRAALL')
    curr_source.Value = round(USDT_RUB,2)
    curr_source.save()

    curr_source = Currency_source.objects.get(OperType = 'RUB => USDT', SendTransferType='CSH',  ReceiveTransferType='CRP',
                                                FinOfficeFrom = 'Наличные', FinOfficeTo = 'TRC20', QuotesRC='RAPIRAALL')
    curr_source.Value = round(1/USDT_RUB,5)
    curr_source.save()
    curr_source = Currency_source.objects.get(OperType = 'RUB => USDT', SendTransferType='CRD',  ReceiveTransferType='CRP',
                                                FinOfficeFrom = 'Сбербанк', FinOfficeTo = 'TRC20', QuotesRC='RAPIRAALL')
    curr_source.Value = round(1/USDT_RUB,5)
    curr_source.save()
    curr_source = Currency_source.objects.get(OperType = 'RUB => USDT', SendTransferType='CRD',  ReceiveTransferType='CRP',
                                                FinOfficeFrom = 'Тинькофф', FinOfficeTo = 'TRC20', QuotesRC='RAPIRAALL')
    curr_source.Value = round(1/USDT_RUB,5)
    curr_source.save()
    # print(rapira.get_pair_info(rapira.get_rates_json(), 'USDT/EUR')['close'])
    # print(1/rapira.get_pair_info(rapira.get_rates_json(), 'USDT/EUR')['close'])
    return 0