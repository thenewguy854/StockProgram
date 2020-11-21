from PyQt5.QtCore import QThread, pyqtSignal
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from YahooStockGrab import getYahooData
import database_module as db
from PyQt5.QtChart import *
from PyQt5.QtGui import QColor, QPainter
from PyQt5 import QtCore

""" Controller class that is primarily used to
    handle the different threads that run in the application """
class GuiCtrl():

    def __init__(self, gui):
        # give the class an instance of the gui so that it can
        # do things with it
        self.gui = gui

        # a variable to set true if a chart has been displayed
        # we will use this variable to delete the chart and display another
        # when the user selects a different ticker
        self.chartDisplayed = False;

        # create instances of each thread
        self.goButtonThread = GoButtonThread(gui, self)

        self.connectSignals()

    def display(self):
        self.gui.show()

    """ This function has all of the signals that need to be dealt with
        as they are called. Connects them to their respective functions """
    def connectSignals(self):
        self.gui.scanButton.clicked.connect(self.startGoButtonThread)
        # connect the goButtonThread signal to update the chart with
        # the function that actually updates the chart
        self.goButtonThread.updateChartSig.connect(self.gui.updateChartSeries)

    def startGoButtonThread(self):
        self.goButtonThread.start()
        

    """ gets and returns a dataframe of stock prices for a given ticker """
    def getTickerPrices(self, ticker):

        # get today's date

        todayDate = date.today()
        todayDate = todayDate + relativedelta(days=1)
        lastYearDate = todayDate - relativedelta(years=1, days=1)

        todayDate = todayDate.strftime('%d-%m-%Y')
        lastYearDate = lastYearDate.strftime('%d-%m-%Y')

        # grab a year's worth of data
        stockData = getYahooData(ticker, lastYearDate, todayDate, "1d")
        
        return stockData

    """ puts price data from the database into the table on the GUI """
    def populateTable(self, stockData):

        # Set the date cells in the table
        rowNum = 6 # start at the second row on the table
        pandaRowNum = len(stockData)-1
        for x in range(self.gui.numberOfRows-2, -1, -1):
            # set date cells
            self.gui.cellList[rowNum].setText(" " + stockData.loc[pandaRowNum][0] + " ")

            # set open cells
            self.gui.cellList[rowNum+1].setText("$" + str(stockData.loc[pandaRowNum][1]))

            # set high cells
            self.gui.cellList[rowNum+2].setText("$" + str(stockData.loc[pandaRowNum][2]))

            # set low cells
            self.gui.cellList[rowNum+3].setText("$" + str(stockData.loc[pandaRowNum][3]))

            # set close cells
            self.gui.cellList[rowNum+4].setText("$" + str(stockData.loc[pandaRowNum][4]))

            # set volume cells
            self.gui.cellList[rowNum+5].setText(" " + str(stockData.loc[pandaRowNum][5]))
                            
            rowNum += 6
            pandaRowNum -= 1
    
""" Thread that handles making the initial price data pull,
    updating the database and price table,
    and drawing the CandleStick chart """
class GoButtonThread(QThread):

    updateChartSig = pyqtSignal()

    def __init__(self, gui, ctrl):
        QThread.__init__(self)
        self.gui = gui
        self.controller = ctrl


    def run(self):
        ticker = self.gui.tickerComboBox.currentText()
        stockPrices = self.controller.getTickerPrices(ticker)
        
        # establish a connection to the database
        self.dbConn = db.create_connection('stocksDB.db')

        # put the prices in the database
        db.insert_df(self.dbConn, ticker, stockPrices)

        # now grab the same prices out of the database
        stockPrices = db.select_all(self.dbConn, ticker)

        # populate the table with this data
        self.controller.populateTable(stockPrices)

        self.updateChartSig.emit()

        




