import requests
import json
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

def bybit_p2p_rates(currency, bank_name, filter, side='ask'):
    '''
    Курсы валют к USDT на P2P Bybit с разными фильтрами
    params
    side: выбор стакана продажи или покупки (bid - стакан продажи, else покупки)
    filter: загатовленные наборы фильтров
    cash_flag: True - курс для налички с гарантекса
    '''
    return_norm = 1
    payment = bybit_banks.get(bank_name)
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "ru-RU",
        "Cache-Control": "no-cache",
        "Content-Length": "149",
        "content-type": "application/json;charset=UTF-8",
        "Origin": "https://www.bybit.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
    }
    # уточнить параметры у Антона
    side_data = "0" if side == 'bid' else "1"
    data = {"userId": 19502056,
            "tokenId": "USDT",
            "currencyId": currency,
            "payment": payment,
            "side": side_data,
            "size": bybit_filter_payloads[filter]["size"],
            "page": "1",
            "authMaker": bybit_filter_payloads[filter]["authMaker"],
            "canTrade": bybit_filter_payloads[filter]["canTrade"],
            "amount": ""
            }
    r = requests.post('https://api2.bybit.com/fiat/otc/item/online', headers=headers, json=data)
    json_data = r.json()
    usdt_rate, counter = 0, 0
    for rate in json_data['result']['items'][bybit_filter_payloads[filter]['range'][0]: bybit_filter_payloads[filter]['range'][1]]:
        usdt_rate += float(rate['price'])
        counter += 1
    usdt_rate = usdt_rate / counter
    return usdt_rate

# print(bybit_p2p_rates(currency="KZT", bank_name="Kaspi", filter="BBTMCHTAVG1", side='bid'))