from ice3x import Ice3x
import requests
import json
from bitstamp import Bitstamp
import email.mime.application
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import email
import smtplib
import datetime
import csv
import time
import logging
from settings import *
import os.path
dir = str(os.path.dirname(os.path.abspath(__file__)) + "/")


# coins to implement the strategy on
CURRENCIES = ['btc', 'ltc', 'eth', 'bch']

# heading for summary table to send in email
EMAIL_HEADING = ('coin', 'date', 'min_ask_price_ice', 'max_bid_price_bitstamp', 'balance_bitstamp', 'coin_amount', 'fund_buy_usd',
                 'fund_sell_usd', 'variance')

# heading for summary table to save in csv file
FILE_HEADING = ['coin', 'date', 'min_ask_price_ice', 'max_bid_price_bitstamp', 'balance_bitstamp', 'coin_amount', 'fund_buy_usd',
                'fund_sell_usd', 'variance', 'currency_pair_id', 'price_bitstamp', 'min_ask_price_usd',
                'max_bid_amount', 'coin_amount', 'response_buy', 'fund_buy_usd', 'ice_order_id', 'ice_transaction_id',
                'response_sell', 'fund_sell_usd', 'bitstamp_order_id']


def _init_logger():                             # initialize exchange logger
    logger = logging.getLogger('BOT')
    handler = logging.FileHandler(dir + 'logs/bot.log')
    logging.basicConfig(level=logging.INFO)
    handler.setLevel(logging.INFO)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    return logger


def _format_log(string, level):  # logging format
        return "{} {}: {}".format(level, datetime.datetime.now(), string)


def currency_exchange_rate():  # currency exchange rate from https://1forge.com/forex-data-api Zar to Usd
    res = requests.get('https://forex.1forge.com/1.0.3/quotes?pairs=USDZAR&api_key=THMvdfzLLoxEa3GVIb2mKBhvD8vaP3Mx')
    return (json.loads(res.text)[0])['price']


def currency_conversion(rate, price_zar):  # change min ask price of ice from Zar to Usd
    price_usd = {}
    for coin in CURRENCIES:
        price_usd[coin] = float(price_zar[coin]) / float(rate)
    return price_usd


def createHTMLtable(table_heading, heading, data):  # create HTML table for email
    htmltable = '<table border="1"><caption><b><u><font size=3>' + str(table_heading) + '</font></b></u></caption>'
    # Append Table Heading
    text = '<tr style = "background-color:rgb(221, 136, 151)">'
    for i in heading:                           # adding headings to email table
        text = text + '<th>' + str(i) + '</th>'
    text = text + '</tr>'
    # Append Table Data
    for row in data:
        text = text + '<tr>'
        for h in heading:
            text = text + '<td>' + str(row[h]) + '</td>'    # adding summary to email table
        text = text + '</tr>'
    htmltable = htmltable + text + '</table>'
    return htmltable


def sendEmail(email_sub, email_body_text, email_body, email_text_end):  # send email
    msg = MIMEMultipart()
    msg['Subject'] = email_sub
    msg['From'] = EMAIL_FROM
    msg['To'] = ','.join(EMAIL_TO)
    msg['Cc'] = ','.join(EMAIL_CC)

    body = MIMEText(email_body_text)
    msg.attach(body)
    for i in email_body:        # to create html table in email body
        body = MIMEText(i, 'html')
        msg.attach(body)
        body = MIMEText('\n')
        msg.attach(body)

    body = MIMEText(email_text_end) # email footer
    msg.attach(body)

    s = smtplib.SMTP('smtp.gmail.com')
    s.starttls()
    s.login(EMAIL_FROM, EMAIL_PASSWORD)     # login to send email

    FROM = EMAIL_FROM
    TO = EMAIL_TO
    CC = EMAIL_CC
    s.sendmail(FROM, TO + CC, msg.as_string())  # sending email bot summary
    s.quit()


def variance(max_bid_price_bitstamp, min_ask_price_usd):  # calculate variance of two values
    val1 = float(max_bid_price_bitstamp) - float(min_ask_price_usd)
    variance = (val1 * 100) / float(min_ask_price_usd)
    return variance


def strategy(coin, coin_data, bitstamp, ice, logger):  # coin, (min_ask, max_bid, current_price, any much more),
                                                        # bitstamp object, ice object
    error_msg = ''
    try:
        coin_data['variance'] = variance(coin_data['max_bid_price_bitstamp'],
                                         coin_data['min_ask_price_usd'])  # getting variance for every coin
        # input min ask price in usd and max bid price in usd

        coin_data['date'] = datetime.datetime.now()         # storing date time for current trade

        print('Checking Variance for ' + coin + ' Variance is ' + str(coin_data['variance']))
        if coin_data['variance'] > -2:                      # if variance meets our requirements proceed for trading
            
            wallet_Amount = float(coin_data['balance_bitstamp'])    # amount of the coin that is in the Bitstamp wallet
            coin_data['balance_bitstamp'] = wallet_Amount
            # Only continue if the value of wallet_amount of the coin is higher than $30
            if wallet_Amount * float(coin_data['price_bitstamp']) > 30:     # value of wallet amount in USD = wallet amount * lastprice in COIN/USD from bitstamp
    
                MaxBidAmount = float(bitstamp.max_bid_amount(coin_data['coin'])) # getting MaxBidAmount of coin from highest buy order on bitstamp
                coin_data['max_bid_amount'] = MaxBidAmount
    
                if MaxBidAmount != {}:
                    if MaxBidAmount > wallet_Amount:    # amount of coin to place order is the lowest from wallet_amount and MaxBidAmount
                        CoinAmount = wallet_Amount
                    else:
                        CoinAmount = MaxBidAmount
                    coin_data['coin_amount'] = CoinAmount
    
                    print('placing buy order on ICE for ' + str(coin) + ' of amount ' + str(CoinAmount) + ' at price ' +
                          str(coin_data['min_ask_price_ice']))
    
                    # placing buy order on ice with min ask price and said coin amount.
                    response_buy = ice.place_order(amount=CoinAmount, price=coin_data['min_ask_price_ice'], type='buy',
                                                   pair_id=coin_data['currency_pair_id'])
                    coin_data['response_buy'] = response_buy
                    # only continue strategy if buy on ice placed successfully
                    if response_buy['errors'] == 'false' or response_buy['errors'] == False:
    
                        print('Successfully placed buy order')
    
                        fund_buy_usd = CoinAmount * coin_data['min_ask_price_usd']  # fund used in USD used in placing buy order
                        coin_data['fund_buy_usd'] = fund_buy_usd
                        coin_data['ice_order_id'] = response_buy['response']['entity']['order_id']  # order_id of successful buy order
                        coin_data['ice_transaction_id'] = response_buy['response']['entity']['transaction_id']  # transaction_id of successful buy
    
                        print('placing sell order on BITSTAMP for ' + str(coin) + ' of amount ' + str(CoinAmount) + ' at price '
                              + str(coin_data['max_bid_price_bitstamp']))
    
                        # placing sell order on bitstamp with max bid price and said coin amount.
                        response_sell = bitstamp.send_bets(amount=CoinAmount, price=coin_data['max_bid_price_bitstamp'],
                                                           coin=coin_data['coin'], side='sell')
                        coin_data['response_sell'] = response_sell
                        if response_sell['status'] == 'success':    # successful sell order on bitstamp
    
                            print('Successfully placed sell order')
    
                            fund_sell_usd = CoinAmount * float(coin_data['max_bid_price_bitstamp']) # fund used in USD used in placing sell order
                            coin_data['fund_sell_usd'] = fund_sell_usd
                            coin_data['bitstamp_order_id'] = response_sell['id']        # order_id of successful sell order
                            logger.info(_format_log(coin_data, "INFO"))
    
                        else:
                            error_msg = error_msg + ' Unable to place sell order on BITSTAMP. ' + response_sell['reason']
    
                    else:
                        error_msg = error_msg + ' Unable to place buy order on ICE. ' + response_buy['reason']
                else:
                    error_msg = error_msg + ' Unable to fetch MaxBidAmount from bitstamp'
            else:
                error_msg = error_msg + ' Wallet amount is less than $30'
        else:
            error_msg = error_msg + ' variance is less than 2. '
        coin_data['error_msg'] = error_msg
    except Exception as e:
        logger.info(_format_log(e, "ERROR"))
        print(error_msg)
        coin_data['error_msg'] = error_msg
    return coin_data


def summary_into_file(bot_summary):  # append summary to trade_report.csv file
    record_fl = open('trade_record.csv', 'a+')       # open csv file in append mode
    csv_rows = csv.reader(record_fl)
    file_writer = csv.writer(record_fl, delimiter=',')
    if len(list(csv_rows)) == 0:
        file_writer.writerows(FILE_HEADING)
    for coin in bot_summary:
        row = []
        for heading in FILE_HEADING:
            row.append(coin.get(heading, '-'))
        file_writer.writerow(row)       # appending trade summary for every coin success and failure both
    record_fl.close()


def main():
    logger = _init_logger()

    bot_summary = []  # to store summary in csv.
    email_summary = []  # to email summary

    try:
        ice = Ice3x(key=Ice_key, secret=Ice_secret, coins=CURRENCIES)

        bitstamp = Bitstamp(key=Bitstamp_key, secret=Bitstamp_secret, client_id=Bitstamp_client_id, coins=CURRENCIES)

        min_ask_price_ice, currency_pair_id = ice.min_ask_price_ice()               # min ask price in COIN/ZAR and currency pair
        max_bid_price_bitstamp, price_bitstamp = bitstamp.max_bid_price_bitstamp()  # max bid price and current price in COIN/USD
        balance_bitstamp = bitstamp.get_balance()

        if min_ask_price_ice != {} and max_bid_price_bitstamp != {} and balance_bitstamp != {}:
            htmlcontent = []

            exchange_rate = currency_exchange_rate()                                    # getting currency exchange rate from forex.1forge.com
            min_ask_price_usd = currency_conversion(exchange_rate, min_ask_price_ice)   # converting min ask price from COIN/ZAR TO COIN/USD'
            print(min_ask_price_usd, 'USD')
            print(min_ask_price_ice, 'zar')
            for coin in CURRENCIES:                                                     # Iterating over coins to implement the strategy
                coin_data = {'coin': coin, 'min_ask_price_ice': min_ask_price_ice[coin],
                             'max_bid_price_bitstamp': max_bid_price_bitstamp[coin],
                             'currency_pair_id': currency_pair_id[coin], 'price_bitstamp': price_bitstamp[coin],
                             'min_ask_price_usd': min_ask_price_usd[coin], 'balance_bitstamp': balance_bitstamp[coin]}
                print('Starting strategy for ' + coin.upper())
                logger.info(_format_log(coin_data, "INFO"))
                coin_summary = strategy(coin, coin_data, bitstamp, ice, logger)

                bot_summary.append(coin_summary) # append summary to store in csv
                # print(bot_summary)

                if coin_summary['error_msg'] == '':  # email only successful trades
                    email_summary.append(coin_summary)
                    # create html table storing summary
            summary_into_file(bot_summary)  # append summary to email

            if len(email_summary) > 0:
                htmlcontent.append(createHTMLtable('Summary of successful orders', EMAIL_HEADING, email_summary))
                email_sub = 'Trading Bot Report'
                email_body_text = 'Hi All,\n\nPFB the summary of orders:'
                email_body = htmlcontent
                email_text_end = '\n\nRegards\nTrading Bot'
                sendEmail(email_sub, email_body_text, email_body, email_text_end)
        else:
            print('Error in price or balance see the API log files for more info')
    except Exception as e:
        logger.info(_format_log(e, "ERROR"))


main()

