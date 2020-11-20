import sqlite3
from sqlite3 import Error
import pandas as pd
from datetime import datetime
import sys
from YahooStockGrab import getYahooData

# The purpose of this module is to communicate and exchange data with SQLite3 databse

# creates connection to SQLite3 database specified by file
# parameter is database file name & local directory
def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return conn

# selects all data from a table and returns it as a pandas dataframe
# parameters are database connection object and ticker aka table name
def select_all(conn, ticker):
    cur = conn.cursor()
    cur.execute("Select * FROM " + ticker)
    rows = cur.fetchall()
    tableDF = pd.DataFrame(rows, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
    return tableDF

# selects a specific cell from a row identified by its date
# parameters are connection object, ticker, cell, date
# returns python data type
def select_specific_data(conn, ticker, cell, date):
    cur = conn.cursor()
    cur.execute("SELECT" + cell + " FROM " + ticker + " WHERE Date=?",(date,))
    data = cur.fetchall()
    return data

# selects a whole row from a table by date and returns as pandas dataframe
# params are connection object, ticker, date
def select_specific_data(conn, ticker, date):
    cur = conn.cursor()
    cur.execute("SELECT * FROM " + ticker + " WHERE date=?",(date,))
    rows = cur.fetchall()
    rowDF = pd.DataFrame(rows, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
    return rowDF

# creates a table if it doesnt exist by ticker name
# params are connection object and ticker
def create_table(conn, ticker):
    create_table_sql = """CREATE TABLE IF NOT EXISTS """ + ticker + """ (
                                Date   STRING,
                                Open   DOUBLE,
                                High   DOUBLE,
                                Low    DOUBLE,
                                Close  DOUBLE,
                                Volume INTEGER
                            ); """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)

# deletes all rows from a table without deleting the table
# params are connection object and ticker
def delete_rows(conn, ticker):
    cur = conn.cursor()
    cur.execute("DELETE FROM " + ticker)

# deletes a whole table
# params are connection object and ticker
def delete_table(conn, ticker):
    cur = conn.cursor()
    cur.execute("DROP TABLE " + ticker)

# takes a dataframe from YahooStockGrab.py
# and inserts it into the database
def insert_df(conn, ticker, stockData):

    # create the table if it doesn't exist
    create_table(conn, str.upper(ticker))

    # delete all current data if the table does exist
    delete_rows(conn, ticker)
        
    for x in range(0, len(stockData)):
        dbRowEntry = []
        dbRowEntry.append(stockData['Date'][x])
        dbRowEntry.append(float(stockData['Open'][x]))
        dbRowEntry.append(float(stockData['High'][x]))
        dbRowEntry.append(float(stockData['Low'][x]))
        dbRowEntry.append(float(stockData['Close'][x]))
        dbRowEntry.append(int(stockData['Volume'][x]))

        create_row(conn, ticker, dbRowEntry)

# inserts a new row of data into the specified table
# params are connection object, ticker, entry (a python list)
def create_row(conn, ticker, entry):
    command = ''' INSERT INTO ''' + ticker + ''' (date, open, high, low, close, volume) VALUES(?,?,?,?,?,?) '''
    cur = conn.cursor()
    cur.execute(command, entry)
    conn.commit()
    return cur.lastrowid

# updates close cell of speficied date in specified table
# params are connection object, ticker, date, close
def update_cell(conn, ticker, date, close):
    cur = conn.cursor()
    cur.execute("UPDATE " + ticker + " SET close=? WHERE date=?",(close,date,))
    conn.commit()
    
