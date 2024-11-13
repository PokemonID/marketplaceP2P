import requests

hosts = "https://api.rapira.net"
rapira_uid = "adb339b6-8449-4b14-8c37-0aeda9c1c582"
rapira_secret = "80fc9bda520142d6bfadc4e2fa197be2"

class TOOL(object):

    def create_jwt(self):
        url = "https://api.rapira.net/open/generate_jwt"
        headers = {
            "accept": "application/json",
            "content-type": "*/*"
            }
        return requests.post(url, headers=headers).json()['token']
    
    def public_request(self, method, url, params=None):
        url = '{}{}'.format(self.hosts, url)
        return requests.request(method, url, params=params)

class Rapira(TOOL):

    def __init__(self, hosts, rapira_uid):
        self.hosts = hosts
        self.rapira_uid = rapira_uid

    def get_rates_json(self):
        method = 'GET'
        url = '/open/market/rates'
        response = self.public_request(method, url)
        return response.json()
    
    def get_pair_info(self, json_data, target_pair):
        '''
        Args:
        params (str): Параметр для выбора валютной пары из вывода функции get_rates_json

        Returns:
            dict: информация по конкретной валютной паре из респонса API Rapira."""
        '''
        for pair in json_data['data']:
            if pair['symbol'] == target_pair:
                return pair
            else:
                return 'Not found'
    
rapira = Rapira(hosts=hosts, rapira_uid=rapira_uid)
# print(rapira.get_pair_info(rapira.get_rates_json(), 'USDT/RUB'))