#!usr/bin/env python
'''
Trader - This trader will look at the history of a certain quantity for all stocks, store an average and a standard deviation. If ever the 
quantity deviates from the average by more than a standard deviation below (or above in certain circumstances) then he will bet in proportion
to the deviation.
'''
import numpy as np
import ystockquote as ys
import threading
import time
import Queue
import Account
import datetime
import TraderNetDML as dml
import TraderNetDALC as dalc
import DBInterface as db
import sys

class RandomTrader(threading.Thread):

    def __init__(self, traderID, startingBalance, stockList, threshold, dalc, dml):
        self.request_queue = Queue.Queue()
        self.traderID = traderID
        self.dalc = dalc
        self.dml = dml
        self.account = Account.Account(self.request_queue, startingBalance, self.traderID, self.dalc, self.dml)
        self.account.start()
        self.stockList = stockList
        self.threshold = threshold
        self.buyPerStock = startingBalance/(len(stockList)*(1-self.threshold))
        threading.Thread.__init__(self)

    def run(self):
        bought = False
        while not bought:
            self.today()
            if self.thisDate != '0':
                if str(datetime.datetime.now().time())[0:2] == '09':
                    for stock in self.stockList:
                        if np.random.random() >= (1 - self.threshold):
                            self.buy(stock)
                    sys.stdout.flush()
                    bought = True
                else:
                    time.sleep(3600)
            else:
                time.sleep(3600)
        while bought:
            if str(datetime.datetime.now().time())[0:2] == '16':
                self.today()
                if self.thisDate != '0':
                    self.account.getNetWorth()
                    time.sleep(3600)
                else:
                    time.sleep(3600)
            else:
                time.sleep(3600)
    
    def today(self):
        weekday = datetime.datetime.today().weekday()
        if weekday == 5 or weekday == 6:
            self.thisDate = '0'
            self.lastDate = '0'
        elif weekday == 0:
            self.thisDate = str(datetime.datetime.today())[0:10]
            self.lastDate = str(datetime.datetime.today() - datetime.timedelta(days=3))[0:10]
        else:
            self.thisDate = str(datetime.datetime.today())[0:10]
            self.lastDate = str(datetime.datetime.today() - datetime.timedelta(days=1))[0:10]
    
    def buy(self, symbol):
        print '[Trader Number ' + self.traderID + '] is Buying'
        self.request_queue.put({'requestType': 'Buy', 'symbol': symbol, 'value': self.buyPerStock})

    def sell(self, symbol):
        self.request_queue.put({'requestType': 'Sell', 'symbol': symbol, 'value': 20})
    