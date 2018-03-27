import csv
import datetime
from bitstamp import *
from settings import *

FILE_HEADING = [
    'coin', 'date', 'min_ask_price_ice', 'max_bid_price_bitstamp', 'balance_bitstamp', 'coin_amount', 'fund_buy_usd',
    'fund_sell_usd', 'variance', 'currency_pair_id', 'price_bitstamp', 'min_ask_price_usd',
    'max_bid_amount', 'coin_amount', 'response_buy', 'fund_buy_usd', 'ice_order_id', 'ice_transaction_id',
    'response_sell', 'fund_sell_usd', 'bitstamp_order_id']

bot_summary = [{'coin': 'btc', 'min_ask_price_ice': 8907.76190862398, 'max_bid_price_bitstamp': '8082.06',
                'currency_pair_id': '3', 'price_bitstamp': '8089.05', 'min_ask_price_usd': 8907.76190862398,
                'balance_bitstamp': 0.0, 'variance': 170445.91047632036,
                'date': datetime.datetime(2018, 3, 26, 16, 39, 33, 916090),
                'error_msg': ' Wallet amount is less than $30'},
               {'coin': 'ltc', 'min_ask_price_ice': 170.543398, 'max_bid_price_bitstamp': '147.51',
                'currency_pair_id': '6', 'price_bitstamp': '147.67', 'min_ask_price_usd': 170.543398,
                'balance_bitstamp': 0.00150481, 'variance': 132.63435585660108,
                'date': datetime.datetime(2018, 3, 26, 16, 39, 33, 916574),
                'error_msg': ' Wallet amount is less than $30'},
               {'coin': 'eth', 'min_ask_price_ice': 531.9411414, 'max_bid_price_bitstamp': '485.19',
                'currency_pair_id': '11', 'price_bitstamp': '486.50', 'min_ask_price_usd': 531.9411414,
                'balance_bitstamp': 0.0, 'variance': 546.4173055506983,
                'date': datetime.datetime(2018, 3, 26, 16, 39, 33, 916970),
                'error_msg': ' Wallet amount is less than $30'},
               {'coin': 'bch', 'min_ask_price_ice': 1045.54243142998, 'max_bid_price_bitstamp': '915.75',
                'currency_pair_id': '15', 'price_bitstamp': '915.27', 'min_ask_price_usd': 1045.54243142998,
                'balance_bitstamp': 0.0, 'variance': 4211.51881412652,
                'date': datetime.datetime(2018, 3, 26, 16, 39, 33, 917432),
                'error_msg': ' Wallet amount is less than $30'}]

# a = open()


def write_into_file(bot_summary):
    record_fl = open('trade_record.csv', 'a+')  # open csv file in append mode
    csv_rows = csv.reader(record_fl)
    file_writer = csv.writer(record_fl, delimiter=',')
    if len(list(csv_rows)) == 0:
        print(type(FILE_HEADING))
        file_writer.writerow(FILE_HEADING)
    for coin in bot_summary:
        row = []
        for heading in FILE_HEADING:
            row.append(coin.get(heading, '-'))
        print(type(row))
        file_writer.writerow(row)  # appending trade summary for every coin success and failure both
    record_fl.close()


# write_into_file(bot_summary)

CURRENCIES = ['btc', 'ltc', 'eth', 'bch']


def main():

    bitstamp = Bitstamp(key=Bitstamp_key, secret=Bitstamp_secret, client_id=Bitstamp_client_id, coins=CURRENCIES)
    bitstamp.send_bets(amount='0.1', price='8069.00', coin='btc', side='sell')

main()