# -*- coding: utf-8 -*-
import hashlib
import hmac
import json
import logging
import time
import datetime
import requests
import os.path
dir = os.path.dirname(os.path.abspath(__file__)) + "/"


class Bitstamp(object):
    def __init__(self, key=None, secret=None, client_id=None, coins=None):
        self.logger = logging.getLogger("BITSTAMP")
        self.BASE_URL = "https://www.bitstamp.net/api/v2/"
        self.handler = logging.FileHandler(dir+'logs/bitstamp.log')
        self.is_continuous = False
        self.key = key
        self.secret = secret
        self.client_id = client_id
        self._init_logger()
        self.coins = coins

    def _init_logger(self):         # initialize exchange logger
        self.logger.setLevel(logging.INFO)
        self.handler.setLevel(logging.INFO)
        self.logger.addHandler(self.handler)

    def _format_log(self, string, level):  # logging format
        return "{} {}: {}".format(level, datetime.datetime.now(), string)

    def max_bid_price_bitstamp(self):       # return max bid price and last price (current) for said coins
        max_bid_price_bitstamp = {}
        price_bitstamp = {}
        response_log = ''
        try:
            for coin in self.coins:  # get min ask price for every coin
                found = False
                count = 0
                while not found and count < 5:     # calling api until we get the max bid price for every coin we required.
                    try:
                        count += 1
                        response = requests.get(self.BASE_URL + 'ticker/' + str(coin) + 'USD',
                                                headers={'User-Agent': 'Mozilla/5.0'}).text
                        response = json.loads(response)
                        max_bid_price_bitstamp[str(coin)] = response['bid']  # max bid price
                        price_bitstamp[str(coin)] = response['last']         # last price
                        found = True
                        response_log = response_log + response      # log response for every api hit
                    except Exception as e:
                        pass
            self.logger.info(self._format_log(response_log, "INFO"))
            return max_bid_price_bitstamp, price_bitstamp
        except Exception as e:
            self.logger.info(self._format_log(e, "ERROR"))
            return {}, {}

    def max_bid_amount(self, coin):     # return max bid order amount from order book
        try:
            response = requests.get(self.BASE_URL + 'order_book/' + str(coin).lower() + 'usd/')     # getting orderbook from bitstamp
            response = json.loads(response.text)['bids']
            MaxBidAmount = response[0][1]
            for data in response:
                if data[1] > MaxBidAmount:      # checking for max bid order
                    MaxBidAmount = data[1]
            self.logger.info(self._format_log(response, "INFO"))
            return MaxBidAmount
        except Exception as e:
            self.logger.info(self._format_log(e, "ERROR"))
            return {}

    def send_bets(self, **params):          # place order
        if self.key and self.secret:
            try:
                nonce = str(int(time.time() * 1e6))
                message = nonce + self.client_id + self.key
                signature = hmac.new(           # creating signature for authentication
                    self.secret.encode('utf-8'), msg=message.encode('utf-8'), digestmod=hashlib.sha256)
                signature = signature.hexdigest().upper()
                params.update({
                    'key': self.key, 'signature': signature, 'nonce': nonce
                })
                url = self.BASE_URL + params['side'] + "/" + params['coin'] + 'usd/' # url to place order
                r = requests.post(url, data=params)     # placing order using post
                response = json.loads(r.text)
                self.logger.info(self._format_log(response, "INFO"))
                return response
            except Exception as e:
                self.logger.info(self._format_log(e, "ERROR"))
                return {}
        else:
            return "KEY AND SECRET NEEDED FOR BETTING"

    def get_balance(self):        # return walletamount for particular coin
        if self.key and self.secret:       # checking key and secret
            params = {}
            balance = {}
            try:
                nonce = str(int(time.time() * 1e6))
                message = nonce + self.client_id + self.key
                signature = hmac.new(           # creating signature for authentication
                    self.secret.encode('utf-8'), msg=message.encode('utf-8'), digestmod=hashlib.sha256)
                signature = signature.hexdigest().upper()
                params.update({
                    'key': self.key, 'signature': signature, 'nonce': nonce})
                url = self.BASE_URL + 'balance/'                                                # url to get balance
                r = requests.post(url=url, data=params)  # get balance using post
                response = json.loads(r.text)
                for coin in self.coins:
                    balance_key = coin + '_available'           # wallet amount for coin
                    balance[coin] = response[balance_key]
                self.logger.info(self._format_log(response, "INFO"))
                return balance
            except Exception as e:
                self.logger.info(self._format_log(e, "ERROR"))
                return {}
        else:
            return "KEY AND SECRET NEEDED FOR BETTING"


