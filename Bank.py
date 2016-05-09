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
import numpy as np
import sqlite3 as lite


class Bank(threading.Thread):
    def __init__(self, initialInvestment, mode):
        self.mode = mode
        self.dataDict = {}
        self.initialInvestment = initialInvestment
        f = open('./exchanges/FTSE.txt', 'r')
        self.stockSymbols = f.read().splitlines()
        f.close()
        self.traderThreadDict = {}
        self.traderCount = 0
        threading.Thread.__init__(self)

    def run(self):
        if self.mode == 'NEW':
            self.newMode()
        else:
            self.continuePreviousSession()
        while True:
            time.sleep(3600 * 24 * 7)
            con = lite.connect('./trader_db/test.db')

            lastWeekDate = str(datetime.datetime.today() - datetime.timedelta(days=7))[0:10]
            repl = (lastWeekDate,)
            with con:
                cur = con.cursor()
                cur.execute(
                    "SELECT TRADER_ID FROM TRADER_PERFORMANCE WHERE MEASURE_DATE > DATE(?) ORDER BY ACCOUNT_VALUE DESC",
                    repl)
                topTraders = []
                while len(topTraders) < 4:
                    data = cur.fetchone()
                    if data[0] in self.traderThreadDict.keys():
                        topTraders.append(data[0])

                # Breed these traders together
                self.breedTraders(topTraders[0], topTraders[1])
                self.breedTraders(topTraders[3], topTraders[4])

                # Remove bottom 2 traders
                cur.execute(
                    "SELECT TRADER_ID FROM TRADER_PERFORMANCE WHERE MEASURE_DATE > DATE(?) DESC ORDER BY ACCOUNT_VALUE ASC",
                    repl)
                bottomTraders = []
                while len(bottomTraders) < 2:
                    data = cur.fetchone()
                    if data[0] in self.traderThreadDict.keys() and 'Genetic' in data[0]:
                        bottomTraders.append(data[0])

                self.traderThreadDict[bottomTraders[0]].setDone()
                self.traderThreadDict[bottomTraders[1]].setDone()
                del (self.traderThreadDict[bottomTraders[0]])
                del (self.traderThreadDict[bottomTraders[1]])

    def newMode(self):
        # Generate some traders of other types for comparison
        self.traderThreadDict['ADX TRADER 1'] = ADXTrader.ADXTrader('ADX TRADER 1', self.initialInvestment,
                                                                    self.stockSymbols)
        self.traderThreadDict['ADX TRADER 1'].start()
        self.traderThreadDict['RANDOM TRADER (P=0.5)'] = RandomTrader.RandomTrader('RANDOM TRADER (P=0.5)',
                                                                                   self.initialInvestment,
                                                                                   self.stockSymbols, 0.5)
        self.traderThreadDict['RANDOM TRADER (P=0.5)'].start()
        self.traderThreadDict['INDEX TRADER (P=1)'] = RandomTrader.RandomTrader('INDEX TRADER (P=1)',
                                                                                self.initialInvestment, ['UKX'], 0)
        self.traderThreadDict['INDEX TRADER (P=1)'].start()

        # Generate 50 random traders
        for i in xrange(50):
            self.generateTrader('Genetic Trader ' + str(self.traderCount))

    def continuePreviousSession(self):
        return False

    def generateTrader(self, traderID):
        chromosome = {'pe': np.random.random(), 'ebitda': np.random.random(), 'ticker_trend': np.random.random(),
                      'short_ratio': np.random.random()}
        self.traderThreadDict[traderID] = GeneticTrader.GeneticTrader(traderID, 1000000, self.stockSymbols, chromosome)
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

        self.traderThreadDict['Genetic Trader Number ' + str(self.traderCount)] = {
            'thread': GeneticTrader.GeneticTrader(('Genetic Trader Number ' + str(self.traderCount)), 1000000,
                                                  self.stockSymbols, newChrom), 'value': self.initialInvestment}
        self.traderThreadDict['Genetic Trader Number ' + str(self.traderCount)]['thread'].start()
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
