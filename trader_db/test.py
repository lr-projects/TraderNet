#!usr/bin/env python
'''
'''

import sqlite3 as lite


con = lite.connect('test.db')
#repl = ('ID3', 'TSCO', 16)

with con:
	cur = con.cursor()
	repl = ('ID3',)
	cur.execute("SELECT TICKER, NUMBER_OWNED FROM TRADER WHERE TRADER_ID=?", repl)
	data = cur.fetchone()
	print data
	raw_input("cunt")
	data = cur.fetchone()
	print data