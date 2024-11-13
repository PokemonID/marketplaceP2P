import requests
import json

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

def binance_p2p_rates(currency, bank_name, filter, side='SELL'):
    '''
    Курсы валют к USDT на P2P binance с разными фильтрами
    params
    side: выбор стакана продажи или покупки (SELL - стакан продажи, BUY - покупки)
    filter: загатовленные наборы фильтров
    '''
    return_norm = 1
    #кэш только для рублей

    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "u-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Content-Length": "281",
        "Content-Type": "application/json",
        "Origin": "https://p2p.binance.com",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    }
    # уточнить параметры у Антона
    data = {
        "fiat": currency,
        "page": 1,
        "rows": 20,
        "tradeType": side,
        "asset": "USDT",
        "countries": [],
        "proMerchantAds": False,
        "shieldMerchantAds": False,
        "filterType": "all",
        "periods": [],
        "additionalKycVerifyFilter": 0,
        "publisherType": binance_filter_payloads[filter]['publisherType'],
        "payTypes": [
            bank_name
        ],
        "classifies": [
            "mass",
            "profession",
            "fiat_trade"
        ]
    }     

    r = requests.post('https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search', headers=headers, json=data)
    json_data = r.json()
    usdt_rate, counter = 0, 0
    # print(json_data['data'])
    for rate in json_data['data'][binance_filter_payloads[filter]['range'][0]: binance_filter_payloads[filter]['range'][1]]:
        usdt_rate += float(rate['adv']['price'])
        counter += 1
    usdt_rate = usdt_rate / counter
    #if usdt_rate == 0:
    return usdt_rate

# print(binance_p2p_rates(currency="UAH", bank_name="Monobank", filter="BNCMCHTAVG2", side='BUY'))