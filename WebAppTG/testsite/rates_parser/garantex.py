import requests

def garantex_rates(currency_pair, side='asks'):
    '''
    currency_pair: [USDTRUB, USDTUSD]
    side: выбор стакана продажи или покупки (bids - стакан продажи, asks покупки)
    '''
    response = requests.get(url=f'https://garantex.org/api/v2/depth?market={currency_pair}').json()
    rate = float(response[side][0]['price'])
    return rate

# print(garantex_rates(currency_pair='usdtrub', side='bids'))