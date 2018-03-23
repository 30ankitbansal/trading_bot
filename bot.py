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
from settings import *

# coins to implement the strategy on
CURRENCIES = ['btc', 'ltc', 'eth', 'bch']

# heading for summary table to send in email
EMAIL_HEADING = ('coin', 'date', 'min_ask_price_ice', 'max_bid_price_bitstamp', 'coin_amount', 'fund_buy_usd',
                 'fund_sell_usd', 'variance')

# heading for summary table to save in csv file
FILE_HEADING = ('coin', 'date', 'min_ask_price_ice', 'max_bid_price_bitstamp', 'coin_amount', 'fund_buy_usd',
                'fund_sell_usd', 'variance', 'currency_pair_id', 'price_bitstamp', 'min_ask_price_usd',
                'max_bid_amount', 'coin_amount', 'response_buy', 'fund_buy_usd', 'ice_order_id', 'ice_transaction_id',
                'response_sell', 'fund_sell_usd', 'bitstamp_order_id')


def currency_exchange_rate():  # currency exchange rate from https://1forge.com/forex-data-api Zar to Usd
    res = requests.get('https://forex.1forge.com/1.0.3/quotes?pairs=ZARUSD&api_key=THMvdfzLLoxEa3GVIb2mKBhvD8vaP3Mx')
    return (json.loads(res.text)[0])['price']


def currency_conversion(rate, price_zar):  # change min ask price of ice from Zar to Usd
    for coin in CURRENCIES:
        price_zar[coin] = float(price_zar[coin]) * float(rate)
    return price_zar


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


def variance(val1, val2):  # calculate variance of two values
    val1 = float(val1)
    val2 = float(val2)
    mean = (val1 + val2) / 2
    val1_sqr = (val1 - mean) ** 2
    val2_sqr = (val2 - mean) ** 2
    variance = val1_sqr + val2_sqr
    return variance


def strategy(coin, coin_data, bitstamp, ice):  # coin, (min_ask, max_bid, current_price, any much more),
                                                        # bitstamp object, ice object
    error_msg = ''
    coin_data['variance'] = variance(coin_data['min_ask_price_usd'],
                                     coin_data['max_bid_price_bitstamp'])  # getting variance for every coin
    # input min ask price in usd and max bid price in usd

    coin_data['date'] = datetime.datetime.now()         # storing date time for current trade
    if coin_data['variance'] > -2:                      # if variance meets our requirements proceed for trading
        wallet_Amount = float(bitstamp.get_balance(coin_data['coin']))    # amount of the coin that is in the Bitstamp wallet

        # Only continue if the value of wallet_amount of the coin is higher than $30
        if wallet_Amount * float(coin_data['price_bitstamp']) > 30:     # value of wallet amount in USD = wallet amount * lastprice in COIN/USD from bitstamp
            MaxBidAmount = float(bitstamp.max_bid_amount(coin_data['coin'])) # getting maxbidamount of coin from highest buy order on bitstamp
            coin_data['max_bid_amount'] = MaxBidAmount

            if MaxBidAmount > wallet_Amount:    # amount of coin to place order is the lowest from wallet_amount and maxbidamount
                CoinAmount = wallet_Amount
            else:
                CoinAmount = MaxBidAmount
            coin_data['coin_amount'] = CoinAmount
            # placing buy order on ice with min ask price and said coin amount.
            response_buy = ice.place_order(amount=CoinAmount, price=coin_data['min_ask_price_ice'], type='buy',
                                           pair_id=coin_data['currency_pair_id'])
            coin_data['response_buy'] = response_buy
            # only continue strategy if buy on ice placed successfully
            if response_buy['errors'] == 'false':
                fund_buy_usd = CoinAmount * coin_data['min_ask_price_usd']  # fund used in USD used in placing buy order
                coin_data['fund_buy_usd'] = fund_buy_usd
                coin_data['ice_order_id'] = response_buy['response']['entity']['order_id']  # order_id of successful buy order
                coin_data['ice_transaction_id'] = response_buy['response']['entity']['transaction_id']  # transaction_id of successful buy

                # placing sell order on bitstamp with max bid price and said coin amount.
                response_sell = bitstamp.send_bets(amount=CoinAmount, price=coin_data['max_bid_price_bitstamp'],
                                                   coin=coin_data['coin'], side='sell')
                coin_data['response_sell'] = response_sell
                if response_sell['status'] == 'success':    # successful sell order on bitstamp
                    fund_sell_usd = CoinAmount * float(coin_data['max_bid_price_bitstamp']) # fund used in USD used in placing sell order
                    coin_data['fund_sell_usd'] = fund_sell_usd
                    coin_data['bitstamp_order_id'] = response_sell['id']        # order_id of successful sell order

                else:
                    error_msg = error_msg + ' Unable to place sell order on BITSTAMP. ' + response_sell['reason']
            else:
                error_msg = error_msg + ' Unable to place buy order on ICE. ' + response_buy['error']
        else:
            error_msg = error_msg + ' Wallet amount is less than $30'
    else:
        error_msg = error_msg + ' variance is less than 2. '
    coin_data['error_msg'] = error_msg
    return coin_data


def summary_into_file(bot_summary):  # append summary to trade_report.csv file
    record_fl = open('trade_record.csv', 'a')       # open csv file in append mode
    file_writer = csv.writer(record_fl, delimiter=',', quotechar='', quoting=csv.QUOTE_ALL)
    for coin in bot_summary:
        row = []
        for heading in FILE_HEADING:
            row.append(coin.get(heading, '-'))
        file_writer.writerow(row)       # appending trade summary for every coin success and failure both
    record_fl.close()


def main():
    bot_summary = []  # to store summary in csv.
    email_summary = []  # to email summary
    ice = Ice3x(key=Ice_key, secret=Ice_secret, coins=CURRENCIES)

    bitstamp = Bitstamp(key=Bitstamp_key, secret=Bitstamp_secret, client_id=Bitstamp_client_id, coins=CURRENCIES)

    min_ask_price_ice, currency_pair_id = ice.min_ask_price_ice()  # min ask price in COIN/ZAR and currency pair
    max_bid_price_bitstamp, price_bitstamp = bitstamp.max_bid_price_bitstamp()  # max bid price and current price in COIN/USD

    htmlcontent = []
    
    exchange_rate = currency_exchange_rate()  # getting currency exchange rate from forex.1forge.com
    min_ask_price_usd = currency_conversion(exchange_rate,
                                            min_ask_price_ice)  # converting min ask price from COIN/ZAR TO COIN/USD'

    for coin in CURRENCIES:  # Iterating over coins to implement the strategy
        coin_data = {'coin': coin, 'min_ask_price_ice': min_ask_price_ice[coin],
                     'max_bid_price_bitstamp': max_bid_price_bitstamp[coin],
                     'currency_pair_id': currency_pair_id[coin], 'price_bitstamp': price_bitstamp[coin],
                     'min_ask_price_usd': min_ask_price_usd[coin]}
        coin_summary = strategy(coin, coin_data, bitstamp, ice)

        bot_summary.append(coin_summary) # append summary to store in csv

        summary_into_file(bot_summary)    # append summary to email

        if coin_summary['error_msg'] == '':  # email only successful trades
            email_summary.append(coin_summary)
            # create html table storing summary
            htmlcontent.append(createHTMLtable('Summary of successful orders', EMAIL_HEADING, email_summary))
            email_sub = 'Trading Bot Report'
            email_body_text = 'Hi All,\n\nPFB the summary of orders:'
            email_body = htmlcontent
            email_text_end = '\n\nRegards\nTrading Bot'
            sendEmail(email_sub, email_body_text, email_body, email_text_end)


main()
