#!usr/bin/env python
'''
Functions to handle retrieving data from a table
'''

import time
import Queue
import DBInterface

class TraderNetDALC():
    def __init__(self, request_queue, results_queue):
        self.request_queue = request_queue
        self.results_queue = results_queue

    def select_from_table(self, table_name, select_cols, where_pairs, thread_id, order_by=None, distinct=False):
        if distinct:
            exec_string = "SELECT DISTINCT "
        else:
            exec_string = "SELECT "
        repl = []
        length = len(select_cols)
        for i in xrange(length):
            if i != length - 1:
                exec_string += select_cols[i] + ", "
            else:
                exec_string += select_cols[i]
        exec_string += " FROM " + table_name
        length = len(where_pairs)
        if length != 0:
            exec_string += " WHERE "
            for i in xrange(length):
                if i != length - 1:
                    exec_string += where_pairs[i][0] + "=? AND "
                    repl.append(where_pairs[i][1])
                else:
                    exec_string += where_pairs[i][0] + "=?"
                    repl.append(where_pairs[i][1])
        if order_by:
            exec_string += " ORDER BY " + order_by
        id = self.generate_id(thread_id)
        print "putting request to the queue"
        self.request_queue.put({id: (exec_string, tuple(repl))})
        results = self.get_results(id)
        return results

    # TRADER
    # Need to be able to select NUMBER_OWNED for a particular TRADER_ID, TICKER pair
    def select_number_owned(self, trader_id, ticker, thread_id):
        where_pairs = [['TRADER_ID', trader_id],
                       ['TICKER', ticker]]
        result = self.select_from_table('TRADER', ['NUMBER_OWNED'], where_pairs, thread_id)
        return result

    # TRADER_PERFORMANCE with TRADER_ID, MEASURE_DATE, ACCOUNT_VALUE

    def select_account_value(self, trader_id, thread_id, order_by_arg='MEASURE_DATE DESC'):
        where_pairs = [['TRADER_ID', trader_id]]
        result = self.select_from_table('TRADER_PERFORMANCE', ['ACCOUNT_VALUE','MEASURE_DATE'], where_pairs, thread_id, order_by=order_by_arg)
        return result

    # TRADER_PROPERTIES with TRADER_ID, TRADER_TYPE, PE, EBITDA, TICKER_TREND, SHORT_RATIO, BALANCE

    def select_trader_properties(self, thread_id, trader_id=None):
        if trader_id:
            where_pairs = [['TRADER_ID', trader_id]]
        else:
            where_pairs = []
        result = self.select_from_table('TRADER_PROPERTIES', ['*'], where_pairs, thread_id)
        return result

    # All stocks owned by trader and number owned

    def select_stocks_owned(self, trader_id, thread_id):
        where_pairs  = [['TRADER_ID', trader_id]]
        result = self.select_from_table('TRADER', ['TICKER', 'NUMBER_OWNED'], where_pairs, thread_id)
        return result
        
    def select_top_four(self, thread_id):
        exec_string = "SELECT tp1.TRADER_ID, (SELECT * FROM (SELECT ACCOUNT_VALUE FROM TRADER_PERFORMANCE WHERE TRADER_ID=tp1.TRADER_ID ORDER BY MEASURE_DATE DESC) LIMIT 1) AS ACCOUNT_VALUE FROM TRADER_PERFORMANCE tp1 WHERE TRADER_ID NOT LIKE '%ADX%' AND TRADER_ID NOT LIKE '%RANDOM%' AND TRADER_ID NOT LIKE '%INDEX%' GROUP BY TRADER_ID ORDER BY ACCOUNT_VALUE DESC LIMIT 4"
        id = self.generate_id(thread_id)
        self.request_queue.put({id: (exec_string, ())})
        result = self.get_results(id)
        return result
    
    def select_bottom_two(self, thread_id):
        exec_string = "SELECT tp1.TRADER_ID, (SELECT * FROM (SELECT ACCOUNT_VALUE FROM TRADER_PERFORMANCE WHERE TRADER_ID=tp1.TRADER_ID ORDER BY MEASURE_DATE DESC) LIMIT 1) AS ACCOUNT_VALUE FROM TRADER_PERFORMANCE tp1 WHERE TRADER_ID NOT LIKE '%ADX%' AND TRADER_ID NOT LIKE '%RANDOM%' AND TRADER_ID NOT LIKE '%INDEX%' GROUP BY TRADER_ID ORDER BY ACCOUNT_VALUE ASC LIMIT 2"
        id = self.generate_id(thread_id)
        self.request_queue.put({id: (exec_string, ())})
        result = self.get_results(id)
        return result
    
    def generate_id(self, thread_id):
        time.sleep(60)
        return 'DALC_' + str(thread_id.name) + '_' + str(time.time())
    
    def get_results(self, id):
        found = False
        while not found:
            if self.results_queue.empty():
                time.sleep(5)
                print 'sleeping'
            elif self.results_queue.queue[0].keys()[0] == id:
                result = self.results_queue.get()[id]
                print 'found it and returning it to the code'
                found = True
        return result

if __name__ == '__main__':
    request_queue = Queue.Queue()
    results_queue = Queue.Queue()
    db = DBInterface.DBInterface(request_queue, results_queue)
    class1 = TraderNetDALC(request_queue, results_queue)
    class1.select_top_four('banger')
