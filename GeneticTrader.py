#!usr/bin/env python
'''
Trader - uses pe, ebitda, eps, dividend_yield, 
shares_outstanding, ticker_trend, short_ratio to decide when to buy and when to sell.
'''
import numpy as np
import ystockquote as ys
import threading
import time
import datetime
import Queue
import Account
import TraderNetDALC
import TraderNetDML
import DBInterface

class GeneticTrader(threading.Thread):

    def __init__(self, traderID, startingBalance, stockList, chromosome, dalc, dml):
        self.done = False
        self.request_queue = Queue.Queue()
        self.traderID = traderID
        self.dalc = dalc
        self.dml = dml
        self.account = Account.Account(self.request_queue, startingBalance, self.traderID, self.dalc, self.dml)
        self.account.start()
        self.stockList = stockList
        self.chromosome = chromosome
        self.buyPerStock = 1000
        threading.Thread.__init__(self)

    def run(self):
        print 'Genetic trader reporting for duty'
        while not self.done:
            hour = str(datetime.datetime.now().time())[0:2]
            weekday = datetime.datetime.today().weekday()
            if hour == '16' and weekday in (0,1,2,3,4):
                self.account.getNetWorth()
                time.sleep(3600)
            elif hour == '14' and weekday in (0,1,2,3,4):
                for stock in self.stockList:
                    dataDict = ys.get_all(stock)
                    if not len(dataDict) == 0:
                        if self.checkData(dataDict):
                            sum = self.innerProd(dataDict)
                            print 'For ' + str(stock) + ' the sum is ' + str(sum)
                            if sum > 1000000000:
                                self.buy(stock)
                            if sum < 100000000:
                                self.sell(stock)
                time.sleep(3600)
            else:
                time.sleep(3600)

    def setDone():
        self.account.setDone()
        self.done = True
    
    def getChromosome(self):
        return self.chromosome
        
    def checkData(self, dataDict):
        for key in self.chromosome.keys():
            if key not in dataDict.keys():
                print 'data does not contain the correct keys'
                return False
            elif dataDict[key] == 'N/A':
                print 'data is N/A'
                return False
        print 'found data'
        return True
    
    def innerProd(self, dataDict):
        sum = 0
        for key in self.chromosome.keys():
            sum += self.chromosome[key]*float(self.cleanse(dataDict[key]))
        return sum
    
    def cleanse(self, value):
        if 'M' in value:
            value = value.replace("M", "")
            return float(value)*10000000
        elif 'B' in value:
            value = value.replace("B", "")
            return float(value)*1000000000
        else:
            return value
    
    def buy(self, symbol):
        print '[Trader Number ' + self.traderID + '] is Buying'
        self.request_queue.put({'requestType': 'Buy', 'symbol': symbol, 'value': self.buyPerStock})

    def sell(self, symbol):
        self.request_queue.put({'requestType': 'Sell', 'symbol': symbol, 'value': self.buyPerStock})

if __name__=='__main__':
    chromosome = {'pe':1, 'ebitda':1, 'ticker_trend':1, 'short_ratio':1}
    f = open('./exchanges/FTSE.txt', 'r')
    stockSymbols = f.read().splitlines()
    request_queue = Queue.Queue()
    results_queue = Queue.Queue()
    db = DBInterface.DBInterface(request_queue, results_queue)
    db.start()
    # traderID, startingBalance, stockList, chromosome, dalc, dml
    dml = TraderNetDML.TraderNetDML(request_queue)
    dalc = TraderNetDALC.TraderNetDALC(request_queue, results_queue)
    geneticTrader = GeneticTrader('Genetic Trader 1', 100000, stockSymbols, chromosome, dalc, dml)
    #geneticTrader.start()
    #geneticTrader.buy('TSCO')
    geneticTrader.test_run()