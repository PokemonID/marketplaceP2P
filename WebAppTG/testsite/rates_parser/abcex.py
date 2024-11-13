import requests
import json

bearer_token = 'eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJrenNJYUxtY0R2RVBlRGRYVHVQOXVYN050UzZDSXZ5WXR5VXhwemRrdEZJIn0.eyJleHAiOjE3NTM5NjAzNDQsImlhdCI6MTcyMjQyNDM0NCwianRpIjoiNzFhNzZiZWItMzY3Yy00ZGEzLWJjMzQtZDc4NWU0OTAzYzZhIiwiaXNzIjoiaHR0cHM6Ly9hdXRoLmFiY2V4LmlvL3JlYWxtcy9hYmNleCIsImF1ZCI6ImFjY291bnQiLCJzdWIiOiI4Zjc0MDRmNy03MzU2LTQ0YmQtOGRhNS1iMGM2NDhiZmM2MDUiLCJ0eXAiOiJCZWFyZXIiLCJhenAiOiJhcHAtYXBpLWtleWNsb2FrLWdhdGV3YXkiLCJzZXNzaW9uX3N0YXRlIjoiMDMyMGFkYmYtZWNkNC00OTQ1LTlmNzctOWFmODJkNTFiNDYyIiwiYWNyIjoiMSIsImFsbG93ZWQtb3JpZ2lucyI6WyIvKiJdLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiIsImRlZmF1bHQtcm9sZXMtYWJjZXguaW8iXX0sInJlc291cmNlX2FjY2VzcyI6eyJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19LCJzY29wZSI6IiIsInNpZCI6IjAzMjBhZGJmLWVjZDQtNDk0NS05Zjc3LTlhZjgyZDUxYjQ2MiIsImlkIjoiN2ZhOWEwYTktMTc5Yi00Y2ViLWFkMTMtZTgyODhkMDcwMTY5In0.Tcj2rJxjuLrpmFatlCCt8pNweNwd9a_6EmEvQP8xzxiXNNw1Hwaa7CA2LU4c3op6NFkS6utN90C0s-bW9yxGvxqJRFYHBETH1sVzGGK7GWjurjTJkGX9R_HztQMZxVAHpE4Tzc78dNBLYp3Ea3QJVRP4973KEEgei4egvxcgo6eEixnFD0uW2nO9lnpQjAPd0lx43m5f-lp64GKQAEZvocFI2VmpCHjCraqGuM3-RNGweWry9Tdqc_m-pwc3MLGX4YsPNuC3JOfjknaQaBH6wqP1f_AdyrPkMZPlDwkMAME_yT3KCI7sTGAhlqROm69ab3L1g_o8zJzpPvE7xlQ6eA'

def abcex_rates(currency_pair, side='ask'):
    '''
    Курсы валют с ABCEX
    currency_pair: [USDTRUB, USDTUSD]
    side: выбор стакана продажи или покупки (bid - стакан продажи, ask покупки)
    '''
    url = f'https://gateway.abcex.io/api/v1/exchange/client/market-data/order-book/depth?marketId={currency_pair}'
    headers = {
        'Authorization': f'Bearer {bearer_token}',
        'Content-Type': 'application/json'  # Optional, depending on the API
    }
    response = requests.get(url, headers=headers)
    response_json = response.json()
    # print(response_json)
    if side in ['bid', 'ask']:
        rate = response_json[side][0]['price']
    else:
        rate = response_json['ask'][0]['price']
    #print(json.dumps(response_json, indent=4))  # Pretty-print the JSON
    return rate

# print(abcex_rates(currency_pair='USDTRUB', side=''))
