#!usr/bin/env python
'''
Functions to handle inserting into or updating a table
'''

import time

class TraderNetDML():

    def __init__(self, request_queue):
        self.request_queue = request_queue

    def insert_into_table(self, table_name, col_val_pairs, thread_id):
        beg_string = "INSERT INTO " + table_name
        col_names = " ("
        repl = []
        end_string = "("
        length = len(col_val_pairs)
        for i in xrange(length):
            if i!=length-1:
                col_names += col_val_pairs[i][0] + ", "
                repl.append(str(col_val_pairs[i][1]))
                end_string += "?, "
            else:
                col_names += col_val_pairs[i][0] + ") VALUES "
                repl.append(str(col_val_pairs[i][1]))
                end_string += "?)"
        exec_string = beg_string + col_names + end_string
        id = self.generate_id(thread_id)
        self.request_queue.put({id: (exec_string, tuple(repl))})
        
    def update_table(self, table_name, update_pairs, where_pairs, thread_id):
        #TODO Change it so that it doesn't insert into brackets if there is one update field
        beg_string = "UPDATE " + table_name + " SET "
        update_cols = "("
        repl = []
        length = len(update_pairs)
        for i in xrange(length):
            if i!=length-1:
                update_cols += update_pairs[i][0] + "=?, "
                repl.append(update_pairs[i][1])
            else:
                update_cols += update_pairs[i][0] + "=?)"
                repl.append(update_pairs[i][1])
        update_cols += " WHERE ("
        length = len(where_pairs)
        for i in xrange(length):
            if i!=length-1:
                update_cols += where_pairs[i][0] + "=? AND "
                repl.append(where_pairs[i][1])
            else:
                update_cols += where_pairs[i][0] + "=?)"
                repl.append(where_pairs[i][1])
        exec_string = beg_string + update_cols
        repl.append('')
        id = self.generate_id(thread_id)
        self.request_queue.put({id: (exec_string, tuple(repl))})        
        
    def delete_from_table(self, table_name, where_pairs):
        exec_string = "DELETE FROM " + table_name + " WHERE "
        length = len(where_pairs)
        repl = []
        for i in xrange(length):
            if i != length-1:
                exec_string += where_pairs[i][0] + "=? AND "
                repl.append(str(where_pairs[i][1]))
            else:
                exec_string += where_pairs[i][0] + "=?"
                repl.append(str(where_pairs[i][1]))
        id = self.generate_id(thread_id)
        self.request_queue.put({id: (exec_string, tuple(repl))})
                
        
    # Write methods for inserting into each of the tables and updating the information in these tables
    # the tables are: 
    # TRADER with TRADER_ID, TICKER, NUMBER_OWNED
    
    def insert_into_trader(self, trader_id, ticker, number_owned, thread_id):
        col_val_pairs = [['TRADER_ID', trader_id],
                         ['TICKER', ticker],
                         ['NUMBER_OWNED', number_owned]]
        self.insert_into_table('TRADER', col_val_pairs, thread_id)
    
    def update_trader(self, trader_id, ticker, number_owned, thread_id):
        update_pairs = [['NUMBER_OWNED', number_owned]]
        where_pairs = [['TRADER_ID', trader_id],
                         ['TICKER', ticker]]
        self.update_table('TRADER', update_pairs, where_pairs, thread_id)
            
    # TRADER_PERFORMANCE with TRADER_ID, MEASURE_DATE, ACCOUNT_VALUE
    
    def insert_into_trader_performance(self, trader_id, measure_date, account_value, thread_id):
        col_val_pairs = [['TRADER_ID', trader_id],
                         ['MEASURE_DATE', 'DATE(' + measure_date + ')'],
                         ['ACCOUNT_VALUE', account_value]]
        self.insert_into_table('TRADER_PERFORMANCE', col_val_pairs, thread_id)
    
    # TRADER_PROPERTIES with TRADER_ID, TRADER_TYPE, PE, EBITDA, TICKER_TREND, SHORT_RATIO, BALANCE
    
    def insert_into_trader_properties(self, trader_id, trader_type, pe, ebitda, ticker_trend, short_ratio, p_trade, balance, thread_id):
        col_val_pairs = [['TRADER_ID', trader_id],
                         ['TRADER_TYPE', trader_type],
                         ['PE', pe],
                         ['EBITDA', ebitda],
                         ['TICKER_TREND', ticker_trend],
                         ['SHORT_RATIO', short_ratio],
                         ['RANDOM_P', p_trade],
                         ['BALANCE', balance]]
        self.insert_into_table('TRADER_PROPERTIES', col_val_pairs, thread_id)
    
    def update_trader_properties(self, trader_id, balance, thread_id):
        update_pairs = [['BALANCE', balance]]
        where_pairs = [['TRADER_ID', trader_id]]
        self.update_table('TRADER_PROPERTIES', update_pairs, where_pairs, thread_id)
		
    def truncate_tables(self, thread_id):
        exec_strings = ["DELETE FROM TRADER",
		               "DELETE FROM TRADER_PROPERTIES",
                       "DELETE FROM TRADER_PERFORMANCE",
                       "VACUUM"]
        for i in xrange(len(exec_strings)):
            id = self.generate_id(thread_id)
            self.request_queue.put({id: (exec_strings[i], ())})
        
    def generate_id(self, thread_id):
        return 'DML_' + str(thread_id) + '_' + str(time.time())

if __name__=='__main__':
    class1 = TraderNetDML('string')
    class1.update_table('VAGINA', [('PENIS', '12'),('MOP', '15')], [('FLAP', '13'),('HELP','16')])