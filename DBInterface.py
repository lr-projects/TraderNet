#!usr/bin/env python
'''
Only thread that owns the db connection.
Receives requests from the request queue and adds results to the results queue for other threads to use.
'''

import sqlite3 as lite
import threading

class DBInterface(threading.Thread):

    def __init__(self, request_queue, results_queue):
        self.db_string = './trader_db/test.db' #get db string from a file
        self.con = lite.connect(self.db_string)
        self.con.row_factory = lite.Row
        self.request_queue = request_queue
        self.results_queue = results_queue
        threading.Thread.__init__(self)

    def run(self):
        con = lite.connect(self.db_string)
        con.row_factory = lite.Row
        while True:
            if not self.request_queue.empty():
                print 'found a request'
                request = self.request_queue.get()
                id = request.keys()[0]
                if id[0:3] == 'DML':
                    self.databaseManipulation(con, request[id][0], request[id][1])
                else:
                    self.databaseAccess(con, request[id][0], request[id][1], id)

    def databaseAccess(self, con, exec_string, repl, request_id):
        with con:
            cur = con.cursor()
            cur.execute(exec_string, repl)
            result = cur.fetchall()
            print "printing out results now"
            print result
            print "did the results appear?"
            self.results_queue.put({request_id: self.convertResultsToPythonObject(result)})
            print 'added result to the results queue'
            
    def databaseManipulation(self, con, exec_string, repl): # No need to provide an id as a result is not expected
        print repl
        with con:
            cur = con.cursor()
            cur.execute(exec_string, repl)
            
    def convertResultsToPythonObject(self, results):
        results_list = []
        for i in xrange(len(results)):
            a = {}
            for el in results[i].keys():
                a[el] = results[i][el]
            results_list.append(a)
        return results_list