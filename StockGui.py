from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QComboBox
from PyQt5.QtWidgets import QPushButton, QTableWidget, QScrollArea
from PyQt5.QtWidgets import QGridLayout, QVBoxLayout, QHBoxLayout
from PyQt5.QtWidgets import QGraphicsView
from PyQt5.QtChart import *
from PyQt5.QtGui import QColor, QPainter
from PyQt5 import QtCore
from YahooStockGrab import getYahooData
import time
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import sys
import database_module as db


# create main window

class StockGui(QMainWindow):
    
    def __init__(self):

        super().__init__()
        self.setWindowTitle('StockGUI')
        self.setFixedSize(1160, 680)

        # set central widget and general layout
        # we will use a grid layout for the general layout
        self.generalLayout = QGridLayout()
        self.centralWidget = QWidget(self)
        self.setCentralWidget(self.centralWidget)
        self.centralWidget.setLayout(self.generalLayout)

        # a variable to set true if a chart has been displayed
        # we will use this variable to delete the chart and display another
        # when the user selects a different ticker
        self.chartDisplayed = False;

        # establish a connection to the database
        try:
            self.dbConn = db.create_connection('stocksDB.db')
        except Exception as e:
            print("Unable to establish connection to database")
            print(e)

        # the central widget will have two smaller widgets inside


        # add leftWidget and rightWidget to central widget

        self.createLeftWidget()
        self.createRightWidget()

    """ Creates the left main widget that holds
        the chart widget and the news widget """
    def createLeftWidget(self):
        self.leftMainWidget = QWidget()
        self.leftMainLayout = QVBoxLayout()
        self.leftMainWidget.setLayout(self.leftMainLayout)
        self.leftMainWidget.setStyleSheet("border: 3px solid black;")
        self.leftMainWidget.setFixedSize(645, 650)

        # create chart widget
        self.createChartWidget()

        # create news widget
        self.createNewsWidget()

        self.generalLayout.addWidget(self.leftMainWidget, 0, 0)

    def createChartWidget(self):
        self.chartWidget = QWidget()
        self.chartWidget.setFixedSize(625, 400)
        self.chartWidgetLayout = QVBoxLayout()
        self.chartWidget.setLayout(self.chartWidgetLayout)
                    
        self.leftMainLayout.addWidget(self.chartWidget)

    """ 99% of what goes into making the candlestick chart is in this function """
    def updateCandleChart(self):
        # create the actual QChart that will display the candlestick chart
        self.candleChart = QChart()
        
         # create the series of data that will hold the stock data
        self.candleChartSeries = QCandlestickSeries()
        self.candleChartSeries.setIncreasingColor(QColor(0, 255, 0, 255)) #RGB+Alpha
        self.candleChartSeries.setDecreasingColor(QColor(255, 0, 0, 255))

        # create the set structure that holds one OHLCV day of data
        self.candleChartSet = QCandlestickSet()

        for x in range(6, len(self.cellList), 6):
            candleChartSet = QCandlestickSet()
            # Date as timestamp
            candleChartSet.setTimestamp(float(time.mktime(datetime.strptime(self.cellList[x].text(), " %Y-%m-%d ").timetuple())))
            candleChartSet.setOpen(float(self.cellList[x+1].text()[1:])) # Open
            candleChartSet.setHigh(float(self.cellList[x+2].text()[1:])) # High
            candleChartSet.setLow(float(self.cellList[x+3].text()[1:])) # Low
            candleChartSet.setClose(float(self.cellList[x+4].text()[1:])) # Close
            #ohlcList.append(self.cellList[x+5]) # Volume 

            self.candleChartSeries.append(candleChartSet)


        # add the data series to the QChart widget
        self.candleChart.addSeries(self.candleChartSeries)
        self.candleChart.setAnimationOptions(QChart.SeriesAnimations)
        
        # create default axes for chart
        self.candleChart.createDefaultAxes()

        # set the x axis

        self.axisX = QDateTimeAxis()
        
        dateEnd = QtCore.QDate()
        dateEnd.setDate(int(self.cellList[6].text()[1:5]), # year
                          int(self.cellList[6].text()[6:8]), # month
                          int(self.cellList[6].text()[9:11])) # day

        axisEnd = QtCore.QDateTime()
        axisEnd.setDate(dateEnd)

        dateBegin = QtCore.QDate()
        dateBegin.setDate(int(self.cellList[len(self.cellList)-6].text()[1:5]),
                        int(self.cellList[len(self.cellList)-6].text()[6:8]),
                        int(self.cellList[len(self.cellList)-6].text()[9:11]))
        
        axisBegin = QtCore.QDateTime()
        axisBegin.setDate(dateBegin)
        
        self.axisX.setRange(axisBegin, axisEnd)
        self.axisX.setFormat("yyyy-MM-dd")

        #self.candleChart.setAxisX(self.axisX, self.candleChartSeries)

        # hide the legend
        self.candleChart.legend().setVisible(False)

        # add the chart into a view
        self.chartView = QChartView(self.candleChart)
        self.chartView.setRenderHint(QPainter.Antialiasing)
        self.chartView.setRubberBand(QChartView.RectangleRubberBand)

    
        self.chartWidgetLayout.addWidget(self.chartView)

    def createNewsWidget(self):
        self.newsWidget = QWidget()
        self.newsWidget.setFixedSize(625, 205)

        self.leftMainLayout.addWidget(self.newsWidget)
        
    """ Creates the right main widget that holds
        the price table and the company ticker buttons """
    def createRightWidget(self):
        self.rightMainWidget = QWidget()
        self.rightMainLayout = QVBoxLayout()
        self.rightMainWidget.setLayout(self.rightMainLayout)
        self.rightMainWidget.setStyleSheet("border: 3px solid black;")
        self.rightMainWidget.setFixedSize(455, 650)

        self.createTickerSelectorWidget()
        self.createPredictedCloseWidget()
        self.createPriceTableWidget()

        self.generalLayout.addWidget(self.rightMainWidget, 0, 1)

    def createTickerSelectorWidget(self):
        self.tickerSelectorWidget = QWidget()
        self.tickerSelectorWidget.setFixedSize(430, 50)
        self.tickerSelectorLayout = QHBoxLayout()
        self.tickerSelectorWidget.setLayout(self.tickerSelectorLayout)

        # ticker combobox
        self.createTickerComboBoxWidget()

        # go button
        self.createScanButton()
        
        self.rightMainLayout.addWidget(self.tickerSelectorWidget)

    def createTickerComboBoxWidget(self):

        self.tickerComboBoxWidget = QWidget()
        self.tickerComboBoxWidget.setFixedSize(170, 40)
        self.tickerComboBoxWidgetLayout = QHBoxLayout() # this can really just be any layout so we can add others widgets
        self.tickerComboBoxWidget.setLayout(self.tickerComboBoxWidgetLayout)
        
         # ticker combobox
        self.tickerComboBox = QComboBox()
        
        # list of tickers that the program will support
        # list was taken from url
        # https://finviz.com/screener.ashx?v=211&f=cap_large,sec_technology
        # last updated: Nov 3, 2020

        tickerList = ['ACN', 'ADI', 'ADSK', 'AKAM', 'AMAT', 'AMD', 'ANET',
                      'ANSS', 'APH', 'ASML', 'AVGO', 'AVLR', 'BKI', 'BR',
                      'CAJ', 'CCC', 'CDAY', 'CDNS', 'CDW', 'CGNX', 'CHKP',
                      'COUP', 'CRWD', 'CSCO', 'CTSH', 'CTXS', 'DDOG', 'DELL',
                      'DNB', 'DOCU', 'DT', 'ENPH', 'EPAM', 'ERIC', 'FICO',
                      'FIS', 'FISV', 'FLT', 'FTNT', 'FIV', 'GDDY', 'GDS',
                      'GIB', 'GLW', 'GRMN', 'HPE', 'HPQ', 'HUBS', 'IBM',
                      'INFY', 'INTC', 'INTU', 'IPGP', 'IT', 'JKHY', 'KEYS',
                      'KLAC', 'LDOS', 'LOGI', 'LRCX', 'MCHP', 'MDB', 'MPWR',
                      'MRVL', 'MSI', 'MU', 'MXIM', 'NET', 'NICE', 'NLOK',
                      'NOK', 'NOW', 'NTAP', 'NXPI', 'OKTA', 'ON', 'ORCL',
                      'OTEX', 'PAGS', 'PANW', 'PAYC', 'PCTY', 'PLTR', 'PTC',
                      'QCOM', 'QRVO', 'RNG', 'SAP', 'SEDG', 'SHOP', 'SNE',
                      'SNOW', 'SNPS', 'SPLK', 'SQ', 'SSNC', 'STM', 'STNE',
                      'STX', 'SWKS', 'TDY', 'TEAM', 'TEL', 'TER', 'TRMB',
                      'TTD', 'TXN', 'TYL', 'U', 'UBER', 'UI', 'UMC', 'VMW',
                      'VRSN', 'WDAY', 'WDC', 'WIT', 'WIX', 'WORK', 'XLNX',
                      'ZBRA', 'ZEN', 'ZI', 'ZS']
                                
        self.tickerComboBox.addItems(tickerList)
        self.tickerComboBox.setEditable(True)

        self.tickerComboBox.setStyleSheet("font-size: 15px;")
        
        self.tickerComboBoxWidgetLayout.addWidget(self.tickerComboBox)
        
        self.tickerSelectorLayout.addWidget(self.tickerComboBoxWidget)

    def createScanButton(self):
        self.scanButtonWidget = QWidget()
        self.scanButtonWidget.setFixedSize(170, 40)
        self.scanButtonWidgetLayout = QHBoxLayout() # this can really just be any layout so we can add other widgets
        self.scanButtonWidget.setLayout(self.scanButtonWidgetLayout)

        self.scanButton = QPushButton("GO")
        
        self.scanButton.clicked.connect(self.goButtonAction)

        self.scanButton.setStyleSheet("font-size: 15px;")

        self.scanButtonWidgetLayout.addWidget(self.scanButton)

        self.tickerSelectorLayout.addWidget(self.scanButtonWidget)

    def createPredictedCloseWidget(self):
        self.predictedCloseWidget = QWidget()
        self.predictedCloseWidget.setFixedSize(430 , 50)
        self.predictedCloseWidgetLayout = QHBoxLayout()
        self.predictedCloseWidget.setLayout(self.predictedCloseWidgetLayout)
        
        self.predictedLabel = QLabel("Next Predicted Close: $5.00 (-0.02)")
        self.predictedLabel.setStyleSheet("font-size: 15px; \
                                           padding-left: 70px;")

        self.predictedCloseWidgetLayout.addWidget(self.predictedLabel)

        self.rightMainLayout.addWidget(self.predictedCloseWidget)

    def createPriceTableWidget(self, dataframeRows=253):

        # we are using labels to represent the price tables
        # since it is easier than trying to use a custom QTableView

        self.numberOfRows = dataframeRows
        numberOfCells = self.numberOfRows * 6 # 6 for the number of columns
        
        self.priceTableWidget = QWidget()
        self.priceTableWidget.setFixedSize(415, 9000)
        self.priceTableWidgetLayout = QGridLayout()
        self.priceTableWidgetLayout.setContentsMargins(0, 0, 0, 0)
        self.priceTableWidgetLayout.setHorizontalSpacing(0)
        self.priceTableWidgetLayout.setVerticalSpacing(0)
        self.priceTableWidget.setLayout(self.priceTableWidgetLayout)

        # scroll widget for making the widget container scollable
        self.scrollBar = QScrollArea()

        self.scrollBar.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scrollBar.setStyleSheet("border: none;")
        self.scrollBar.setWidget(self.priceTableWidget)

        # set minimum row height for all of the rows

        for x in range(0, self.numberOfRows):
            self.priceTableWidgetLayout.setRowMinimumHeight(x, 500)


        
        self.cellList = []

        # create cells
        for x in range(0, numberOfCells):
            self.cellList.append(QLabel())
            self.cellList[x].setAlignment(QtCore.Qt.AlignCenter)

        # set values and styles for header cells
        # this should be the first 6 cells in the list
        for x in range(0, 6):
            if x == 0:
                self.cellList[x].setText("Date")
            elif x == 1:
                self.cellList[x].setText("Open")
            elif x == 2:
                self.cellList[x].setText("High")
            elif x == 3:
                self.cellList[x].setText("Low")
            elif x == 4:
                self.cellList[x].setText("Close")
            elif x == 5:
                self.cellList[x].setText("Volume")
            else:
                print("ERROR SETTING PRICE TABLE HEADERS")

            self.cellList[x].setStyleSheet("font-size: 16px;\
                                            border-left: 3px solid black;\
                                            border-bottom: 3px solid black;\
                                            border-top: 3px solid black;\
                                            font-weight: bold;")

        # add text to the rest of the cells for testing purposes
        cellCount = 0 # used to figure out what cell we are on
        for x in range(6, numberOfCells):
            if not cellCount == 6:
                if cellCount == 0:
                    # date cell
                    self.cellList[x].setText("")
                    cellCount += 1
                elif cellCount == 1:
                    # open cell
                    self.cellList[x].setText("")
                    cellCount += 1
                elif cellCount == 2:
                    # high cell
                    self.cellList[x].setText("")
                    cellCount += 1
                elif cellCount == 3:
                    # low cell
                    self.cellList[x].setText("")
                    cellCount += 1
                elif cellCount == 4:
                    # close cell
                    self.cellList[x].setText("")
                    cellCount += 1
                elif cellCount == 5:
                    self.cellList[x].setText("")
                    cellCount = 0

        # set the style for the rest of the cells

        for x in range(6, numberOfCells):
            self.cellList[x].setStyleSheet("font-size: 14px;\
                                             border-left: 3px solid black;\
                                             border-bottom: 3px solid black;")
        # add the cells to the grid layout
        rowNumber = 0
        columnNumber = 0
        for x in range(0, numberOfCells):
            self.priceTableWidgetLayout.addWidget(self.cellList[x], rowNumber, columnNumber)
            if not columnNumber == 5:
                columnNumber += 1
            else:
                columnNumber = 0
                # go to the next row once all the columns have cells
                rowNumber += 1
        
            
        self.rightMainLayout.addWidget(self.scrollBar)

    """ Stuff that happens after hitting the go button """
    def goButtonAction(self):

        # get the currently selected ticker
        ticker = self.tickerComboBox.currentText()

        # get the stock prices
        stockPrices = self.getTickerPrices(ticker)
        
        # put the prices in the database
        db.insert_df(self.dbConn, ticker, stockPrices)

        # now grab the same prices out of the database
        stockPrices = db.select_all(self.dbConn, ticker)

        # populate the table with this data
        self.populateTable(stockPrices)

        # update the chart
        if self.chartDisplayed:
            self.chartWidgetLayout.removeWidget(self.chartView)

        # add chart to the chart widget
        self.chartDisplayed = True
        
        self.updateCandleChart()

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

        # redraw the table corresponding to the number of rows that were returned in the dataframe
        self.rightMainLayout.removeWidget(self.scrollBar) 
        self.createPriceTableWidget(len(stockData)+1)

        # Set the date cells in the table

        rowNum = 6 # start at the second row on the table
        pandaRowNum = len(stockData)-1 
        for x in range(self.numberOfRows-2, -1, -1):
            # set date cells
            self.cellList[rowNum].setText(" " + stockData.loc[pandaRowNum][0] + " ")

            # set open cells
            self.cellList[rowNum+1].setText("$" + str(stockData.loc[pandaRowNum][1]))

            # set high cells
            self.cellList[rowNum+2].setText("$" + str(stockData.loc[pandaRowNum][2]))

            # set low cells
            self.cellList[rowNum+3].setText("$" + str(stockData.loc[pandaRowNum][3]))

            # set close cells
            self.cellList[rowNum+4].setText("$" + str(stockData.loc[pandaRowNum][4]))

            # set volume cells
            self.cellList[rowNum+5].setText(" " + str(stockData.loc[pandaRowNum][5]))
                            
            rowNum += 6
            pandaRowNum -= 1





def main():
    """ Main function """
    stockProgram = QApplication([])
    stockGui = StockGui()
    stockGui.show()

    # execute Stock Program Application
    sys.exit(stockProgram.exec())


if __name__ == '__main__':

    main()
