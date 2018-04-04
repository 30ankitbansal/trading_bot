import requests
import json
import time
import base64
import hashlib
import hmac
import logging
from urllib3.request import urlencode
import os.path
import datetime

dir = os.path.dirname(os.path.abspath(__file__)) + '/'


class Ice3x(object):
    def __init__(self, key=None, secret=None, client_id=None, coins=None):
        self.logger = logging.getLogger('ICE3X')
        self.BASE_URL = 'https://ice3x.com/api/v1/'
        self.handler = logging.FileHandler(dir + 'logs/ice3x.log')
        self.is_continuous = False
        self.key = key
        self.secret = secret
        self.client_id = client_id
        self.coins = coins
        self._init_logger()

    def _init_logger(self):
        self.logger.setLevel(logging.INFO)
        self.handler.setLevel(logging.INFO)
        self.logger.addHandler(self.handler)

    def _format_log(self, string, level):
        return '{} {}: {}'.format(level, datetime.datetime.now(), string)

    def min_ask_price_ice(self):  # return min ask price of asked coins
        min_ask_price_ice = {}
        currency_pair_id = {}
        try:
            response = requests.get(self.BASE_URL + 'stats/marketdepthbtcav').text  # This method provides info about
            # currency pair, for a certain period of time (24h by default):
            # Note: Value of params last_price, min_ask and max_bid don’t depend on chosen period of time
            # (date_from, date_to) and always provides info for current time.
            result = json.loads(response)
            if result['errors'] == 'false' or result['errors'] == False:  # for successful response getting min ask
                for data in result['response']['entities']:  # price for every coin
                    currency_pair = str(data['pair_name']).split('/')
                    if currency_pair[1] == 'zar' and str(currency_pair[0]) in self.coins:
                        min_ask_price_ice[currency_pair[0]] = data['min_ask']  # min ask price
                        currency_pair_id[currency_pair[0]] = data['pair_id']  # currency pair id for every coin will be
                self.logger.info(self._format_log(result, 'INFO'))  # used in buy order.
        except Exception as e:
            self.logger.info(self._format_log(e, 'ERROR'))
            min_ask_price_ice = {}
            currency_pair_id = {}
        return min_ask_price_ice, currency_pair_id

    def place_order(self, pair_id, amount, type, price):  # place a order
        if self.key and self.secret:
            try:
                nonce = str(int(time.time()) * 1e6)
                uri = 'order/new'  # Api_method/api_action
                post_data = {'nonce': nonce,
                             'pair_id': pair_id,  # Currency pair id
                             'amount': amount,  # The volume of transactions (amount)
                             'type': type,  # Transaction type (type) – buy / sell
                             'price': price  # The price of the buy / sell
                             }
                str_to_sign = str(urlencode(post_data))  # encoding post data for signature
                # str_to_sign = 'nonce=' + nonce + '&amp;type=sell&amp;pair_id=3&amp;price=1652.00&amp;amount=1.00150481'
                signature = hmac.new(self.secret.encode('utf-8'), msg=str_to_sign.encode('utf-8'),
                                     digestmod=hashlib.sha512)
                headers = {'Content-Type': 'application/x-www-form-urlencoded',
                           'Key': self.key,
                           'Sign': signature}
                r = requests.post(self.BASE_URL + uri, data=post_data,
                                  headers=headers)  # placing order on ice3x exchange
                print(r.text)
                response = json.loads(r.text)
                print(response)
                self.logger.info(self._format_log(response, 'INFO'))
                return response
            except Exception as e:
                self.logger.info(self._format_log(e, 'ERROR'))
                return {}
        else:
            return "KEY AND SECRET NEEDED FOR BETTING"
