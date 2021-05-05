import time
import numpy as np
from datetime import datetime

import threading
#----------
import configparser
#----------
from binance import RequestClient_s
from binance.utils.timeservice import *
from system.symbol import *
from system.manageorder import *
from system.utils import *



###################################################################################
#---------------------------------  main program  --------------------------------#
###################################################################################
class main():
    def __init__(self):
        #self.API = bitkubAPI(API_HOST,API_KEY,API_SECRET)
        config = configparser.ConfigParser()
        config.read('config.ini') 
        
        #API
        self.client = RequestClient_s(
            config['API']['server'],
            config['API']['key'].encode(),
            config['API']['secret'],
        )
        
        self.api_connect = True
        
        #system
        self.system_name = config['SYSTEM']['name']
        self.symbol = {'symbol':config['SYSTEM']['symbol']}
        self.margin = float(config['SYSTEM']['margin'])
        self.quoteAssetNotional = float(config['SYSTEM']['quoteAssetNotional'])
        self.line_token = config['SYSTEM']['line_token']
        
        #time
        self.tm = ''
        self.time_string = ''
        self.time_interval = 0
        self.interval = config['SYSTEM']['interval']
        
        #baseAssetInfo
        self.baseAsset = ''
        self.basePrecision = 0
        self.baseAsset_amt = 0
        
        #quoteAssetInfo
        self.quoteAsset = ''
        self.quotePrecision = 0
        self.quoteAsset_amt = 0
        
        self.minNotional = 0.0

        self.minQty = 0.0
        self.Qtypoint = 0
        self.tickPoint = 0
        self.balance=dict()

    ########################### getdata ###########################   
    def time_check(self):
        #get_time
        self.tm = time.localtime() # get struct_time
        self.time_string = time.strftime("%Y-%m-%d, %H:%M:%S", self.tm)
        
        if getattr(self.tm,self.interval) != self.time_interval:
            self.time_interval = getattr(self.tm,self.interval)
            return True
        else:
            return False
    
    def get_balance(self,sym_list):
        account = self.client.get_account()
        balance = {}
        for sym in sym_list:
            for n in range(len(account)):
                if account[n]["asset"] ==  sym:
                    balance[sym] = float(account[n]['free'])
                    
        return balance
    
    
    def get_ticker(self):
        try:
            ticker = self.client.MKTdepth(self.symbol['symbol'])
            self.symbol['bid'] = round(float(ticker['bids'][0][0]),self.tickPoint)
            self.symbol['bidv'] = round(float(ticker['bids'][0][1]),self.Qtypoint)
            self.symbol['ask'] = round(float(ticker['asks'][0][0]),self.tickPoint)
            self.symbol['askv'] = round(float(ticker['asks'][0][1]),self.Qtypoint)
            return True
        except:
            return False
  
    def cal_value(self):
        #cal value[0] in base USDT
        return round(float(self.balance[self.baseAsset]['amt']) * self.symbol['ask'])
    
    ########################### open order ###########################

    def place_orders_open(self,sym,side,quantity,order_comment):
        res = self.client.place_orders(symbol=sym, side=side, ordertype='MARKET', quantity=quantity)
        print('#################### place_orders_open ####################')
        print(res)
        print('#################### ################# ####################')
        restime = timestampToDatetime( int(res["transactTime"])/1000 )
        return{ 'orderId' : res['orderId'],
                'open_date': f'{restime}',
                'open_price': self.symbol['ask'],
                'side':res['side'],
                'origQty': res['origQty'],
                'cummulativeQuoteQty': float(res['cummulativeQuoteQty']),
                'status':res['status'],
                'fills':res['fills'],
                'order_comment':f'{order_comment}',
                }
                        
    def rebalance(self):

        ask   = self.symbol['ask']
        symbol= self.symbol['symbol']
                     
        #rebalance Diff Quote
        rebalanceDiff = abs(self.balance[self.quoteAsset]['value'] - self.balance[self.baseAsset]['value'])
        #rebalance Condition Quote
        rebalanceCon = rebalanceDiff > self.margin
        #rebalance Qty
        rebalanceQty = round( (rebalanceDiff/2)/ask ,self.Qtypoint)
        
        #check Qty&Notional
        check_minQty = rebalanceQty > self.minQty 
        check_minNotional = rebalanceDiff/2 > self.minNotional 

        #Send order
        if(rebalanceCon and check_minQty and check_minNotional):
            base_v = self.balance[self.baseAsset]['value']
            print('#################### Value ####################')
            print(f'rebalanceCon : {rebalanceCon}')
            print(f'self.margin : {self.margin} quote')
            print(f'rebalanceDiff : {rebalanceDiff} notional quote')
            print(f'rebalance_Qty : {rebalanceQty} base')
            print(f'baseAsset_value : {base_v}')
            print('################################################')
        

            order_comment = f"{self.symbol['symbol']}:{ask} {rebalanceDiff}|{rebalanceQty} {base_v}"
            #buy [0] 
            if( self.balance[self.quoteAsset]['value'] > self.balance[self.baseAsset]['value'] ):
                res=self.place_orders_open(symbol,'BUY',rebalanceQty,order_comment)
                
                #self.balance[self.baseAsset]['amt'] = self.balance[self.baseAsset]['amt'] + rebalanceQty
                #get all baseAsset amt 
                balance_binance = self.get_balance([self.baseAsset, self.quoteAsset])
                self.balance[self.baseAsset]['amt']  = round(balance_binance[self.baseAsset], self.basePrecision)
                
                self.balance[self.baseAsset]['value'] = round( self.balance[self.baseAsset]['amt'] + res['cummulativeQuoteQty'] ,self.basePrecision)
                self.balance[self.quoteAsset]['amt'] = round( self.balance[self.quoteAsset]['amt']    - res['cummulativeQuoteQty'] ,self.basePrecision)
                self.balance[self.quoteAsset]['value']= round( self.balance[self.quoteAsset]['value'] - res['cummulativeQuoteQty'] ,self.basePrecision)
                
                #write_csv
                res[self.baseAsset] = self.balance[self.baseAsset]
                res[self.quoteAsset] = self.balance[self.quoteAsset]
                write_csv(res,'log.csv')
                
                quoteValue = self.balance[self.quoteAsset]['value']
                msg_line = f'{self.system_name} BUY {symbol}:{ask} \r\n value:{quoteValue} qty:{rebalanceQty}'
                
            #sell [0]
            if( self.balance[self.quoteAsset]['value'] < self.balance[self.baseAsset]['value'] ):
                res=self.place_orders_open(symbol,'SELL',rebalanceQty,order_comment)
                
                self.balance[self.baseAsset]['amt'] = self.balance[self.baseAsset]['amt'] - rebalanceQty
                self.balance[self.baseAsset]['value'] = round( self.balance[self.baseAsset]['value'] - res['cummulativeQuoteQty'] ,self.basePrecision)
                self.balance[self.quoteAsset]['amt'] = round( self.balance[self.quoteAsset]['amt']   + res['cummulativeQuoteQty'] ,self.basePrecision)
                self.balance[self.quoteAsset]['value']= round( self.balance[self.quoteAsset]['value']+ res['cummulativeQuoteQty'] ,self.basePrecision)

                #write_csv
                res[self.baseAsset] = self.balance[self.baseAsset]
                res[self.quoteAsset] = self.balance[self.quoteAsset]
                write_csv(res,'log.csv')
                
                quoteValue = self.balance[self.quoteAsset]['value']
                msg_line = f'{self.system_name} SELL {symbol}:{ask} \r\n value:{quoteValue} qty:{rebalanceQty}'
            

            lineSendMas(self.line_token,msg_line)
            
            #save value
            save_json(self.balance,'wallet.json')
            
        
    ########################### initialize ########################### 
    def initialize(self):
        self.get_info()
        if  self.get_wallet() :
            save_json(self.balance,'wallet.json')
            return True
        else:
            return False
    
    def get_info(self):
        sym_info={}
        info = self.client.exchangeInfo()
        for sym in info['symbols']:
            if sym['symbol'] == self.symbol['symbol']:
                sym_info = sym
                break    
                
        if sym_info != {}:
            #baseAssetInfo
            self.baseAsset = sym_info['baseAsset']
            self.basePrecision = int(sym_info['baseAssetPrecision'])

            #quoteAssetInfo
            self.quoteAsset = sym_info['quoteAsset']
            self.quotePrecision = int(sym_info['quotePrecision'])

            for filters in sym_info['filters']:
                if filters['filterType'] == 'PRICE_FILTER':
                    self.tickPoint = decimal_point(filters['tickSize'])
                if filters['filterType'] == 'MIN_NOTIONAL':
                    self.minNotional = float(filters['minNotional'])
                if filters['filterType'] == 'LOT_SIZE': 
                    self.minQty = float(filters['minQty'])
                    self.Qtypoint = decimal_point(filters['minQty'])
            self.balance[self.quoteAsset]={}
            self.balance[self.baseAsset]={}
            return True
        else:
            print('Cant find symbol')
            return False
    
    def get_wallet(self):
        wallet = load_json('wallet.json')
        sym_list=[]
        ticker = self.get_ticker()
        
        self.balance[self.baseAsset]={}
        self.balance[self.quoteAsset]={}
        if wallet != {} and ticker:
            # load wallet.json 
            self.balance[self.baseAsset]['amt']  = round( float(wallet[self.baseAsset]['amt']),self.basePrecision)
            self.balance[self.quoteAsset]['amt'] = round( float(wallet[self.quoteAsset]['amt']),self.quotePrecision)
            self.balance[self.baseAsset]['value']  = round( float(wallet[self.baseAsset]['value']),self.quotePrecision)
            self.balance[self.quoteAsset]['value'] = round( float(wallet[self.quoteAsset]['value']),self.quotePrecision)
        elif(ticker):
            # have't file wallet.json 
            # ask price
            ask  = self.symbol['ask']
            # get balance amt 
            balance_binance = self.get_balance([self.baseAsset, self.quoteAsset])
            # create_sub_wallet_condition
            if balance_binance[self.quoteAsset] + (balance_binance[self.baseAsset]*ask)  > self.quoteAssetNotional * 2 :
                
                if balance_binance[self.quoteAsset] < self.quoteAssetNotional:
                    self.balance[self.baseAsset]['amt']  = round( self.quoteAssetNotional/ask, self.basePrecision)
                    self.balance[self.baseAsset]['value']  = round( self.quoteAssetNotional, self.quotePrecision)
                    self.balance[self.quoteAsset]['amt'] = round(  balance_binance[self.quoteAsset], self.quotePrecision)
                    self.balance[self.quoteAsset]['value'] = round( balance_binance[self.quoteAsset] , self.quotePrecision)
                
                elif balance_binance[self.baseAsset]*ask < self.quoteAssetNotional  :
                    self.balance[self.baseAsset]['amt']  = round(balance_binance[self.baseAsset], self.basePrecision)
                    self.balance[self.baseAsset]['value']  = round( balance_binance[self.baseAsset]*ask, self.quotePrecision)
                    self.balance[self.quoteAsset]['amt'] = round(  self.quoteAssetNotional, self.quotePrecision)
                    self.balance[self.quoteAsset]['value'] = round( self.quoteAssetNotional , self.quotePrecision)
                else:
                    self.balance[self.baseAsset]['amt']  = round(balance_binance[self.baseAsset], self.basePrecision)
                    self.balance[self.baseAsset]['value']  = round( balance_binance[self.baseAsset]*ask, self.quotePrecision)
                    self.balance[self.quoteAsset]['amt'] = round(  self.quoteAssetNotional, self.quotePrecision)
                    self.balance[self.quoteAsset]['value'] = round( self.quoteAssetNotional , self.quotePrecision)
   
            else:
                print("error : not enough quoteAsset") 
                return False
        else:
            print("error : can't get ticker")
            return False
        
        return True

    
    def start(self):
        if self.get_ticker() :
            ask  = self.symbol['ask']
            self.balance[self.baseAsset]['value'] = round(self.balance[self.baseAsset]['amt'] * ask,self.quotePrecision)
            
            if self.time_check() :
                self.rebalance()
            
            sym = self.symbol['symbol']
            baseAmt = round(self.balance[self.baseAsset]['amt'],self.basePrecision)
            baseValue = round(self.balance[self.baseAsset]['value'],self.quotePrecision)
            quoteValue = round(self.balance[self.quoteAsset]['amt'],self.quotePrecision)
            diff = round(quoteValue - baseValue,self.quotePrecision)
            diffPercent = round(diff/quoteValue*100,2)
            print(f'{self.system_name} {sym}:{ask} {baseAmt}[{baseValue}]:{quoteValue}  {diff}[{diffPercent}%]   {self.time_string}              ',end='\r')
        else:           
            print(f'{self.system_name} connection failed {self.time_string}                                                                      ',end='\r')



################ initialize ################
program = main()
initialize = program.initialize()

################ start ################
while(True):
    program.start()
    time.sleep(0)