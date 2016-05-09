#!usr/bin/env python
'''
Account Class - This is a class to keep track of the amount of capital that a trader has.
They will send their buy and sell requests via their account.
'''

import threading
import Queue
import ystockquote as yt
import time
import TraderBean
import TraderDataSource

class Account(threading.Thread):

	def __init__(self, queue, starting_balance, traderId):
		self.done = False
		self.traderId = traderId
		self.queue = queue
		self.traderDataSource = TraderDataSource('./trader_db/test.db')
		self.balance = starting_balance
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

	def setDone():
		self.done = True

	def getBalance(self):
		return self.balance

	def getNetWorth(self):
		value = 0
		
		con = lite.connect('./trader_db/test.db')
		lastWeekDate = str(datetime.datetime.today())[0:10]
		repl = (self.traderId, )

		with con:
			cur = con.cursor()
			cur.execute("SELECT TICKER, NUMBER_OWNED FROM TRADER WHERE TRADER_ID=?", repl)
			data = cur.fetchall()
			for i in xrange(len(data)):
				bid = self.get_bid(data[i][0])
				if temp != -1:
					value += data[i][1]*bid
			repl = (self.traderId, str(datetime.datetime.today())[0:10], value)
			cur.execute("INSERT INTO TRADER_PERFORMANCE (TRADER_ID, MEASURE_DATE, ACCOUNT_VALUE) VALUES (?, DATE(?), ?)", repl)
			con.commit()
			con.close()

	def buy(self, symbol, value):
		share_price = self.get_ask(symbol)
		if share_price != -1:
			num_shares = round((value/share_price),0)
			if num_shares*share_price < self.balance:
				bean = self.traderDataSource.getTraderTickerRecord(self.traderId, symbol)
				self.traderDataSource.insertTraderTicker(bean.setNumberOwned(bean.getNumberOwned() + num_shares))
			else:
				print 'Requesting to buy more shares than your Trader can afford'

	def sell(self, symbol, value):
		bean = self.traderDataSource.getTraderTickerRecord(self.traderId, symbol)
		owned = bean.getNumberOwned()
		if owned == 0:
			print 'Sell request submitted for stock that you do not own'
		else:
			share_price = self.get_bid(symbol)
			if share_price != -1:
				num_shares = round((value/share_price),0)
				if num_shares > owned:
					print 'You cannot sell more shares than you own - instead selling all of your current holdings'
					self.balance += owned*share_price
					bean.setNumberOwned(0)
					self.traderDataSource.insertTraderTicker(bean)
				else:
					self.balance += num_shares*share_price
					bean.setNumberOwned(owned-num_shares)
					self.traderDataSource.insertTraderTicker(bean)
				
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