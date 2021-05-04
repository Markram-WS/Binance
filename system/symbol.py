import numpy as np
import pandas as pd
import time
from system.utils import *
############################################################################################
#------------------------------------  symbol class   -------------------------------------#
############################################################################################
class symbol():
    def __init__(self,symbol,client):
        self.symbol = symbol
        self.ticker = {'ask':0,'bid':0,'askv':0,'bidv':0}
        self.his_price={}
        self.client = client
        
        exchangeInfo=client.exchangeInfo()
        for sym in exchangeInfo['symbols']:
            if sym['symbol'] == self.symbol:
                self.quantityPrecision = sym['quantityPrecision']
                self.pricePrecision = sym['pricePrecision']
                break
        

        
    def get_ticker(self):
        try:
            depth = self.client.MKTdepth(self.symbol)
            #depth['bids'][ndepth][0 value|1 volume ] 
            self.ticker['bid'] = float(depth['bids'][0][0])
            self.ticker['bidv'] = float(depth['bids'][0][1])
            self.ticker['ask'] = float(depth['asks'][0][0])
            self.ticker['askv'] = float(depth['asks'][0][1])
            return True
        except:
            return False
        
        
    def getHisPrice(self,timeframe,nbar):
        price = self.client.historicalPrice(self.symbol,timeframe_convert(timeframe),time.time()-(timeframe*nbar),time.time(),nbar)
        self.his_price = pd.DataFrame.from_dict(price)     
        
    def ma(self,type_bar):
        return self.his_price[type_bar].mean()

    def refBar(self,type_bar,bar):
        return self.his_price[type_bar][len(self.his_price)-bar]
    
    def atr(self):
        tr=[]
        for i in range(len(self.his_price)):
            tr.append(
                max(
                    (self.his_price['high'][i]-self.his_price['low'][i]),
                    abs(self.his_price['high'][i]-self.his_price['close'][i]),
                    (self.his_price['low'][i]-self.his_price['close'][i])
                )) 
        return np.mean(tr)