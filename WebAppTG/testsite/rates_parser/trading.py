import requests

def trading_rates(currency_pair):
    '''
    Курсы валют с TradingView forex ICE
    currency_pair: [usdeur, usdrsd, usdbgn] и обратные
    '''
    headers = {
        "Accept": "text/plain, */*; q=0.01",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Content-Length": "454",
        "Origin": "https://www.tradingview.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
    }
    data = {"filter":[{"left":"name,description","operation":"match","right":currency_pair}],
            "options":{"lang":"ru"},
            "markets":["forex"],
            "symbols":{"query":{"types":["forex"]},"tickers":[]},
            "columns":["base_currency_logoid","currency_logoid","name","close","change","change_abs","bid","ask","high","low","Recommend.All","description","type","subtype","update_mode","pricescale","minmov","fractional","minmove2"],
            "sort":{"sortBy":"name","sortOrder":"asc"},
            "range":[0,150]}
    response = requests.post(url='https://scanner.tradingview.com/forex/scan', headers=headers, json=data).json()
    print(response['data'])
    for pair_info in response['data']:
        if 'FX_IDC' in pair_info['s']:
            rate = pair_info['d'][3]
    return rate

# print(trading_rates(currency_pair='bgnusd'))