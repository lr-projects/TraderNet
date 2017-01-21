#!usr/bin/env python
'''
Trader
'''
import numpy as np
import ystockquote as ys
import threading
import time
import datetime
import Queue
import Account
import sys

class ADXTrader(threading.Thread):

    def __init__(self, traderID, startingBalance, stockList, dalc, dml):
        self.done = False
        self.request_queue = Queue.Queue()
        self.stockList = stockList
        self.traderID = traderID
        self.dalc = dalc
        self.dml = dml
        self.account = Account.Account(self.request_queue, startingBalance, self.traderID, self.dalc, self.dml)
        self.account.start()
        self.MMA = {}
        threading.Thread.__init__(self)

    def run(self):
        for stock in self.stockList:
            self.MMA[stock] = {'PDM':[], 'NDM':[], 'ATR':[], 'PDI':[], 'NDI':[], 'ADX':[], 'DIFF':[]}
            self.initiateData(stock)
        while not self.done:
            self.today()
            sys.stdout.flush()
            if str(datetime.datetime.now().time())[0:2] == '09':
                if self.thisDate != '0':
                    for stock in self.stockList:
                        try:
                            self.ADX(stock, self.lastDate, self.thisDate)
                            print 'success for ' + stock
                        except:
                            print 'not able to find data for ' + stock
                        self.analysis(stock)
                    time.sleep(3600)
            elif str(datetime.datetime.now().time())[0:2] == '16':
                self.account.getNetWorth()
                time.sleep(3600)
            else:
                time.sleep(3600)
    
    def setDone():
        self.account.setDone()
        self.done = True
    
    def ADX(self, stock, date1, date2):
        data = ys.get_historical_prices(stock, date1, date2)
        if date1 in data.keys() and date2 in data.keys(): 
            upMove = float(data[date2]['High']) - float(data[date1]['High'])
            downMove = float(data[date1]['Low']) - float(data[date2]['Low'])
            
            if (upMove > downMove) and (upMove > 0):
                PDM = upMove
            else:
                PDM = 0
            
            if (downMove > upMove) and (downMove > 0):
                NDM = downMove
            else:
                NDM = 0
            
            hilo = float(data[date2]['High']) - float(data[date1]['High'])
            hiclo  = abs(float(data[date2]['High']) - float(data[date1]['Close']))
            hipreclo = abs(float(data[date2]['Low']) - float(data[date1]['Close']))
            
            TR = max([hilo, hiclo, hipreclo])
            
            length = len(self.MMA[stock]['PDM']) + 1
            if length == 1:
                self.MMA[stock]['PDM'].append(PDM)
                self.MMA[stock]['NDM'].append(NDM)
                self.MMA[stock]['ATR'].append(TR)
            elif length > 1 and length < 14:
                self.MMA[stock]['PDM'].append(((length-1)*self.MMA[stock]['PDM'][-1] + PDM)/length)
                self.MMA[stock]['NDM'].append(((length-1)*self.MMA[stock]['NDM'][-1] + NDM)/length)
                self.MMA[stock]['ATR'].append(((length-1)*self.MMA[stock]['ATR'][-1] + TR)/length)
            else:
                self.MMA[stock]['PDM'].append(((length-1)*self.MMA[stock]['PDM'][-1] + PDM)/length)
                self.MMA[stock]['NDM'].append(((length-1)*self.MMA[stock]['NDM'][-1] + NDM)/length)
                self.MMA[stock]['ATR'].append(((length-1)*self.MMA[stock]['ATR'][-1] + TR)/length)
                del self.MMA[stock]['PDM'][0]
                del self.MMA[stock]['NDM'][0]
                del self.MMA[stock]['ATR'][0]
            
            if self.MMA[stock]['ATR'][-1] != 0:
                self.MMA[stock]['PDI'].append(100*self.MMA[stock]['PDM'][-1]/self.MMA[stock]['ATR'][-1])
                self.MMA[stock]['NDI'].append(100*self.MMA[stock]['NDM'][-1]/self.MMA[stock]['ATR'][-1])
            else:
                self.MMA[stock]['PDI'].append(100*self.MMA[stock]['PDM'][-1])
                self.MMA[stock]['NDI'].append(100*self.MMA[stock]['NDM'][-1])
                
            if self.MMA[stock]['PDI'][-1]+self.MMA[stock]['NDI'][-1] != 0:
                diff = abs((self.MMA[stock]['PDI'][-1]-self.MMA[stock]['NDI'][-1])/(self.MMA[stock]['PDI'][-1]+self.MMA[stock]['NDI'][-1]))
            else:
                diff = abs((self.MMA[stock]['PDI'][-1]-self.MMA[stock]['NDI'][-1]))
            if length == 1:
                self.MMA[stock]['DIFF'].append(diff)
            elif length > 1 and length < 14:
                self.MMA[stock]['DIFF'].append(((length-1)*self.MMA[stock]['DIFF'][-1]+diff)/length)
            else:
                self.MMA[stock]['DIFF'].append(((length-1)*self.MMA[stock]['DIFF'][-1]+diff)/length)
                del self.MMA[stock]['DIFF'][0]
            
            self.MMA[stock]['ADX'].append(100*self.MMA[stock]['DIFF'][-1])
        
    def analysis(self, stock):
        short, long = self.derivative(stock)
        if long > 0 and short <=0:
            if self.MMA[stock]['PDI'][-1] > self.MMA[stock]['NDI'][-1]:
                self.buy(stock)
        elif long < 0 and short > long:
            self.sell(stock)

    def derivative(self, stock):
        if len(self.MMA[stock]['ADX']) > 1:
            tenDay = np.average(np.gradient(self.MMA[stock]['ADX'][-10:]))
            threeDay = np.average(np.gradient(self.MMA[stock]['ADX'][-3:]))
            return threeDay, tenDay
        else:
            return 0, 0
    
    def buy(self, symbol):
        print '[Trader Number ' + self.traderID + '] is Buying'
        self.request_queue.put({'requestType': 'Buy', 'symbol': symbol, 'value': 100})

    def sell(self, symbol):
        self.request_queue.put({'requestType': 'Sell', 'symbol': symbol, 'value': 100})
        
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
    
    def initiateData(self, stock):
        ''' Assumes that the program is only going to be kicked off on a weekday'''
        sys.stdout.flush()
        weekday = datetime.datetime.today().weekday()
        if weekday in (3,4):
            for i in xrange(18):
                date2 = (datetime.datetime.today()-datetime.timedelta(days=(17-i)))
                if date2.weekday()==0:
                    try:
                        self.ADX(stock, str(datetime.datetime.today()-datetime.timedelta(days=(20-i)))[0:10], str(date2)[0:10])
                    except:
                        print 'Not recording data for these dates'
                elif date2.weekday() in (1,2,3,4):
                    try:
                        self.ADX(stock, str(datetime.datetime.today()-datetime.timedelta(days=(18-i)))[0:10], str(date2)[0:10])
                    except:
                        print 'Not recording data for these dates'
        elif weekday in (0,1,2):
            for i in xrange(20):
                date2 = (datetime.datetime.today()-datetime.timedelta(days=(19-i)))
                if date2.weekday()==0:
                    try:
                        self.ADX(stock, str(datetime.datetime.today()-datetime.timedelta(days=(22-i)))[0:10], str(date2)[0:10])
                    except:
                        print 'Not recording data for these dates'
                elif date2.weekday() in (1,2,3,4):
                    try:
                        self.ADX(stock, str(datetime.datetime.today()-datetime.timedelta(days=(20-i)))[0:10], str(date2)[0:10])
                    except:
                        print 'Not recording data for these dates'

if __name__=='__main__':
    # traderID, startingBalance, stockList):
    f = open('./exchanges/FTSE.txt', 'r')
    stockSymbols = f.read().splitlines()
    thread1 = ADXTrader('ADX TRADER 1', 1000000, stockSymbols)
    thread1.start()