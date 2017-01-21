#!usr/bin/env python
'''
Account Class - This is a class to keep track of the amount of capital that a trader has.
They will send their buy and sell requests via this class.
'''

import threading
import Queue
import ystockquote as yt
import time
import DBInterface as db

class Account(threading.Thread):

    def __init__(self, queue, starting_balance, traderId, dalc, dml):
        self.done = False
        self.traderId = traderId
        self.queue = queue
        self.balance = starting_balance
        self.dalc = dalc
        self.dml = dml
        threading.Thread.__init__(self)

    def run(self):
        while not self.done:
            if self.queue.empty():
                time.sleep(30)
            else:
                request =  self.queue.get()
                if request['requestType'] == 'Buy':
                    self.buy(request['symbol'], request['value'])
                if request['requestType'] == 'Sell':
                    self.sell(request['symbol'], request['value'])

    def setDone(self):
        self.done = True

    def getBalance(self):
        return self.balance

    def currentDate(self):
        temp_time = time.localtime(time.time())
        if len(str(temp_time[1])) == 1:
            if len(str(temp_time[2])) == 1:
                return str(temp_time[0]) + '-0' + str(temp_time[1]) + '-0' + str(temp_time[2])
            else:
                return str(temp_time[0]) + '-0' + str(temp_time[1]) + '-' + str(temp_time[2])
        else:
            return str(temp_time[0]) + '-' + str(temp_time[1]) + '-' + str(temp_time[2])

    def getNetWorth(self):
        value = self.balance
        query_result  = self.dalc.select_stocks_owned(self.traderId, threading.current_thread())
        for i in xrange(len(query_result)):
            value += query_result[i]['NUMBER_OWNED']*self.get_bid(query_result[i]['TICKER'])
        self.dml.insert_into_trader_performance(self.traderId, self.currentDate(), value, threading.current_thread())

    def buy(self, symbol, value):
        share_price = self.get_ask(symbol)
        if share_price != -1:
            num_shares = round((value/share_price),0)
            if num_shares*share_price < self.balance:
                get_num_owned = self.dalc.select_number_owned(self.traderId, symbol, threading.current_thread())
                if len(get_num_owned) != 0:
                    num_owned = get_num_owned[0]["NUMBER_OWNED"] + num_shares
                else:
                    num_owned = num_shares
                self.balance -= num_shares*share_price
                self.dml.update_trader_properties(self.traderId, self.balance, threading.current_thread())
                self.dml.update_trader(self.traderId, symbol, num_owned, threading.current_thread())
            else:
                print 'Requesting to buy more shares than your Trader can afford'

    def sell(self, symbol, value):
        get_num_owned = self.dalc.select_number_owned(self.traderId, symbol, threading.current_thread())
        if len(get_num_owned) != 0:
            num_owned = get_num_owned[0]['NUMBER_OWNED']
            share_price = self.get_bid(symbol)
            if share_price != -1:
                num_shares = round((value/share_price),0)
                if num_shares > num_owned:
                    print 'You cannot sell more shares than you own - instead selling all current holdings'
                    self.balance += num_owned*share_price
                    self.dml.update_trader_properties(self.traderId, self.balance, threading.current_thread())
                    self.dml.update_trader(self.traderId, symbol, 0, threading.current_thread())
                else:
                    self.balance += num_shares*share_price
                    new_num_owned  = owned-num_shares
                    self.dml.update_trader_properties(self.traderId, self.balance, threading.current_thread())
                    self.dml.update_trader(self.traderId, symbol, new_num_owned, threading.current_thread())
        else:
            print 'Sell request submitted for stock that you do not own'
                
    def get_ask(self, symbol):
        try:
            ask = yt.get_all(symbol)['ask_realtime']
        except:
            ask = 'No data available'
        if ask=='N/A':
            print 'THE MARKET IS CLOSED - NO PURCHASE POSSIBLE'
            return -1
        elif ask == 'No data available':
            print ask
            return -1
        else:
            return float(ask)
        return 26.78
    
    def get_bid(self, symbol):
        try:
            bid = yt.get_all(symbol)['bid_realtime']
        except:
            bid = 'No data available'
        if bid=='N/A':
            print 'THE MARKET IS CLOSED - NO SALE POSSIBLE'
            return -1
        elif bid == 'No data available':
            print bid
            return -1
        else:
            return float(bid)
                 
if __name__=='__main__':
    q = Queue.Queue()
    q.put({'requestType': 'Buy', 'symbol': 'GOOG', 'value': 200})
    thread1 = Account(q, 1000, 'trader1')
    thread1.start()
    thread1.getNetWorth()