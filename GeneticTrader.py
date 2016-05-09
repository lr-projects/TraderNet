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

class GeneticTrader(threading.Thread):

	def __init__(self, traderID, startingBalance, stockList, chromosome):
		self.done = False
		self.request_queue = Queue.Queue()
		self.traderID = traderID
		self.account = Account.Account(self.request_queue, startingBalance, self.traderID)
		self.account.start()
		self.stockList = stockList
		self.chromosome = chromosome
		self.buyPerStock = 1000
		threading.Thread.__init__(self)

	def run(self):
		while not self.done:
			hour = str(datetime.datetime.now().time())[0:2]
			weekday = datetime.datetime.today().weekday()
			if hour == '16' and weekday in (0,1,2,3,4):
				self.account.getNetWorth()
			elif hour == '09' and weekday == 0:
				for stock in self.stockList:
					dataDict = ys.get_all(stock)
					if self.checkData(dataDict):
						sum = self.innerProd(dataDict)
						if sum > 103910000:
							self.buy(stock)
						if sum < 10391:
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
			if dataDict[key] == 'N/A':
				return False
		return True
	
	def innerProd(self, dataDict):
		sum = 0
		for key in self.chromosome.keys():
			sum += chromosome[key]*float(self.cleanse(dataDict[key]))
		return sum
	
	def cleanse(self, value):
		#print 'Value is ' + value
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
	geneticTrader = GeneticTrader('Genetic Trader 1', 100000, stockSymbols, chromosome)
	geneticTrader.start()