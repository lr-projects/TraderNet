#!usr/bin/env python
'''
Bank - Creates and fires the Traders.
'''

import threading
import sys
import time
import datetime
import Queue
import ADXTrader
import RandomTrader
import GeneticTrader
import DBInterface
import TraderNetDALC
import TraderNetDML
import numpy as np
import sqlite3 as lite
import Queue

class Bank(threading.Thread):

    def __init__(self, initialInvestment, mode):
        self.mode = mode
        self.initialInvestment = initialInvestment
        f = open('./exchanges/FTSE.txt', 'r')
        self.stockSymbols = f.read().splitlines()
        f.close()
        self.request_queue = Queue.Queue()
        self.results_queue = Queue.Queue()
        self.db_interface = DBInterface.DBInterface(self.request_queue, self.results_queue)
        self.db_interface.start()
        self.dalc = TraderNetDALC.TraderNetDALC(self.request_queue, self.results_queue)
        self.dml = TraderNetDML.TraderNetDML(self.request_queue)
        self.traderThreadDict = {}
        self.traderCount = 0
        threading.Thread.__init__(self)

    def run(self):
        if self.mode == 'NEW':
            self.newMode()
        else:
            self.continuePreviousSession()
        while True:
            time.sleep(3600)
            hour = str(datetime.datetime.now().time())[0:2]
            weekday = datetime.datetime.today().weekday()
            if hour == '16' and weekday == 0:
				# Query the database to find the top 4 traders
				top_four = self.dalc.select_top_four(threading.current_thread())
				# Breed these traders together
				first = top_four[0]['TRADER_ID']
				second = top_four[1]['TRADER_ID']
				third = top_four[2]['TRADER_ID']
				fourth = top_four[3]['TRADER_ID']
				# TODO Rewrite the above
				self.breedTraders(first, fourth)
				self.breedTraders(second, third)
	
				# Query the database to find the bottom 2 traders
				bottom_two = self.dalc.select_bottom_two(threading.current_thread())
				second_to_last = bottom_two[0]['TRADER_ID']
				last = bottom_two[1]['TRADER_ID']
				# Remove bottom 2 traders
				self.traderThreadDict[last].setDone()
				self.traderThreadDict[second_to_last].setDone()
				del (self.traderThreadDict[last])
				del (self.traderThreadDict[second_to_last])
				# TODO Remove the traders from the database

    def newMode(self):
        # clear down the database as this is running in new mode
        self.dml.truncate_tables(threading.current_thread())
        # Generate some traders of other types for comparison
        self.traderThreadDict['ADX TRADER 1'] = ADXTrader.ADXTrader('ADX TRADER 1', self.initialInvestment,
                                                                    self.stockSymbols, self.dalc, self.dml)
        self.traderThreadDict['ADX TRADER 1'].start()
        self.dml.insert_into_trader_properties('ADX TRADER 1', 'ADX', None, None, None, None, 0, self.initialInvestment, threading.current_thread())
        
        self.traderThreadDict['RANDOM TRADER (P=0.5)'] = RandomTrader.RandomTrader('RANDOM TRADER (P=0.5)',
                                                                                   self.initialInvestment,
                                                                                   self.stockSymbols, 0.5, self.dalc, self.dml)
        self.traderThreadDict['RANDOM TRADER (P=0.5)'].start()
        self.dml.insert_into_trader_properties('RANDOM TRADER (P=0.5)', 'RANDOM', None, None, None, None, 0.5, self.initialInvestment, threading.current_thread())
        
        self.traderThreadDict['INDEX TRADER (P=1)'] = RandomTrader.RandomTrader('INDEX TRADER (P=1)',
                                                                                self.initialInvestment, ['UKX'], 0, self.dalc, self.dml)
        self.traderThreadDict['INDEX TRADER (P=1)'].start()
        self.dml.insert_into_trader_properties('RANDOM TRADER (P=1)', 'RANDOM', None, None, None, None, 0, self.initialInvestment, threading.current_thread())

        # Generate 50 random traders
        for i in xrange(20):
            self.generateTrader('Genetic Trader ' + str(self.traderCount))

    def continuePreviousSession(self):
        trader_list = self.dalc.select_trader_properties(threading.current_thread())
        # TODO GET MAXIMUM TRADER ID IN THE DATABASE
        # iterate through the list and set up the traders
        for i in xrange(len(trader_list)):
            if trader_list[i]['TRADER_TYPE'] == 'GENETIC':
                print 'I have found a genetic Trader'
                # logic for generating a random trader
                chromosome = {'pe': trader_list[i]['PE'], 'ebitda': trader_list[i]['EBITDA'], 'ticker_trend': trader_list[i]['TICKER_TREND'],
                      'short_ratio': trader_list[i]['SHORT_RATIO']}
                self.traderThreadDict[trader_list[i]['TRADER_ID']] = GeneticTrader.GeneticTrader(trader_list[i]['TRADER_ID'], trader_list[i]['BALANCE'], self.stockSymbols, chromosome, self.dalc, self.dml)
                self.traderThreadDict[trader_list[i]['TRADER_ID']].start()
            elif trader_list[i]['TRADER_TYPE'] == 'RANDOM':
                # logic for generating a random trader
                # different logic for the index trader to the 50:50 trader
                if trader_list[i]['TRADER_ID'][-5:] == '(P=1)':
                    self.traderThreadDict[trader_list[i]['TRADER_ID']] = RandomTrader.RandomTrader(trader_list[i]['TRADER_ID'], trader_list[i]['BALANCE'], ['UKX'], 0, self.dalc, self.dml)
                else:
                    self.traderThreadDict[trader_list[i]['TRADER_ID']] = RandomTrader.RandomTrader(trader_list[i]['TRADER_ID'], trader_list[i]['BALANCE'], self.stockSymbols, 0.5, self.dalc, self.dml)
                self.traderThreadDict[trader_list[i]['TRADER_ID']].start()
            elif trader_list[i]['TRADER_TYPE'] == 'ADX':
                # generate a genetic trader
                self.traderThreadDict[trader_list[i]['TRADER_ID']] = ADXTrader.ADXTrader(trader_list[i]['TRADER_ID'], trader_list[i]['BALANCE'], self.stockSymbols, self.dalc, self.dml)
                self.traderThreadDict[trader_list[i]['TRADER_ID']].start()
            else:
                print 'exception for trader record'

    def generateTrader(self, traderID):
        chromosome = {'pe': np.random.random(), 'ebitda': np.random.random(), 'ticker_trend': np.random.random(),
                      'short_ratio': np.random.random()}
        
        self.dml.insert_into_trader_properties(traderID, 'GENETIC', chromosome['pe'], chromosome['ebitda'], chromosome['ticker_trend'], chromosome['short_ratio'], 0, self.initialInvestment, threading.current_thread())
        
        self.traderThreadDict[traderID] = GeneticTrader.GeneticTrader(traderID, self.initialInvestment, self.stockSymbols, chromosome, self.dalc, self.dml)
        self.traderThreadDict[traderID].start()
        self.traderCount += 1

    def breedTraders(self, traderId1, traderId2):
        chrom1 = self.traderThreadDict[traderId1]['thread'].getChromosome()
        chrom2 = self.traderThreadDict[traderId2]['thread'].getChromosome()
        newChrom = {}
        if np.random.random() < 0.5:
            newChrom['pe'] = chrom1['pe'] + self.mutation()
        else:
            newChrom['pe'] = chrom2['pe'] + self.mutation()

        if np.random.random() < 0.5:
            newChrom['ebitda'] = chrom1['ebitda'] + self.mutation()
        else:
            newChrom['ebitda'] = chrom2['ebitda'] + self.mutation()

        if np.random.random() < 0.5:
            newChrom['ticker_trend'] = chrom1['ticker_trend'] + self.mutation()
        else:
            newChrom['ticker_trend'] = chrom2['ticker_trend'] + self.mutation()

        if np.random.random() < 0.5:
            newChrom['short_ratio'] = chrom1['short_ratio'] + self.mutation()
        else:
            newChrom['short_ratio'] = chrom2['short_ratio'] + self.mutation()
            
        self.dml.insert_into_trader_properties('Genetic Trader ' + str(self.traderCount), 'GENETIC', newChrom['pe'], newChrom['ebitda'], newChrom['ticker_trend'], newChrom['short_ratio'], 0, self.initialInvestment, threading.current_thread())

        self.traderThreadDict['Genetic Trader ' + str(self.traderCount)] = GeneticTrader.GeneticTrader(('Genetic Trader ' + str(self.traderCount)), self.initialInvestment, self.stockSymbols, newChrom)
        self.traderThreadDict['Genetic Trader ' + str(self.traderCount)]['thread'].start()
        self.traderCount += 1

    def mutation(self):
        if np.random.random() < 0.8:
            return (2 * np.random.random() - 1) / 10
        else:
            return 2 * np.random.random() - 1


if __name__ == '__main__':
    if sys.argv[1] in ('NEW', 'CONTINUE'):
        bankInstance = Bank(1000000, sys.argv[1])
        bankInstance.start()
    else:
        sys.stderr("Please enter a valid mode to run: either 'NEW' or 'CONTINUE'")
