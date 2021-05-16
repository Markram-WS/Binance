import time
import numpy as np
from datetime import datetime

import threading
#----------
import configparser
#----------
from ftx import RequestClient_s
from ftx.utils.timeservice import *
from system.symbol import *
from system.manageorder import load_json
from system.manageorder import save_json
from system.manageorder import write_csv
from system.utils import lineSendMas
from system.utils import checkIn
from system.utils import decimal_nPoint
from system import timeFunction
from system import systemCondition




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
            config['API']['secret'])
        
        self.api_connect = True
        
        #system
        self.system_name = config['SYSTEM']['name']
        self.symbol = {'symbol':config['SYSTEM']['symbol']}
        self.margin = float(config['SYSTEM']['margin'])
        self.assetNotional = float(config['SYSTEM']['assetNotional'])
        self.line_token = config['SYSTEM']['line_token']
        self.baseAssetRatio =  float(config['SYSTEM']['baseAssetRatio'])
        self.quoteAssetRatio = 1 - self.baseAssetRatio
        self.portfolioValue = {}
        

        # openOrder load
        self.openOrder = list([])
        load_ord = load_json('openedOrder.json')
        for i in load_ord:
            self.openOrder.append(i)
        
        #time
        self.tm = ''
        self.time_string = ''
        self.time_store_value = 0
        self.interval = config['SYSTEM']['interval']
        self.timeFunction = timeFunction()
        
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
        
        
        self.system = systemCondition(self.portfolioValue)
    ########################### getdata ###########################   
    def time_check(self):
        #get_time
        self.tm = time.localtime() # get struct_time
        self.time_string = time.strftime("%Y-%m-%d, %H:%M:%S", self.tm)
        
        if getattr(self.tm,self.interval) != self.time_store_value :
            self.time_store_value = getattr(self.tm,self.interval)
            #time checkIn
            checkIn(self.system_name)
            #####################
            #time function
            if self.timeFunction.time_condition():
                return True
            #####################
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
        return round(float(self.balance[self.baseAsset]['amt']) * self.symbol['ask'] ,self.basePrecision)
    ########################### cancle order ###########################
    def cancel_openOrder(self):
        if(len(self.openOrder)>0):
            for ord_ in self.openOrder:
                order =  self.client.cancel_order(self.symbol['symbol'],ord_["orderId"])
                if  order["status"] == "CANCELED":
                    #save openOrder
                    price = ord_['price']
                    symbol = ord_['symbol']
                    msg_line = f'{self.system_name} {symbol} {price} [ canceled ]'
                    self.openOrder.remove(ord_)
                    save_json(self.openOrder,'openedOrder.json')
                    lineSendMas(self.line_token,msg_line)
                    print('                                                                                                     ',end='\r')
                    print(' ###################################### CANCEL ORDER ###################################### ')
                    print(order)
                    print("")
                else:
                    continue
                    
                    
                    

    ########################### check open order ###########################
    def check_filled_order(self):
        if(len(self.openOrder)>0):
            for order in self.openOrder:
                delDict = order

                try:
                    _order = self.client.get_order(self.symbol['symbol'],order["orderId"])
                    if float(_order["price"]) == 0 and _order["status"] == "FILLED":
                        print('                                                                                                     ',end='\r')
                        print(' ######################################## MP FILLED ####################################### ')
                        print(_order)
                        print("")
                except:
                    _order={}

                if _order != {}:
                    if _order["status"] == "FILLED" and float(_order["price"]) != 0:
                        msg_line=''
                        price = float(_order["price"])
                        
                        symbol = _order['symbol']
                        
                        order['price'] = _order["price"]
                        order['origQty'] = _order["origQty"]
                        order['cummulativeQuoteQty'] = _order["cummulativeQuoteQty"]
                        rebalanceQty = round(float(_order['executedQty']),self.basePrecision)
                        cummulativeQuoteQty =round(float( order['cummulativeQuoteQty']),self.quotePrecision)

                        if _order["side"] == "BUY":
                            #get acc from binance
                            #balance_binance = self.get_balance([self.baseAsset, self.quoteAsset])
                            #self.balance[self.baseAsset]['amt']  = round(float(balance_binance[self.baseAsset]), self.basePrecision)

                            self.balance[self.baseAsset]['amt']  = round( self.balance[self.baseAsset]['amt'] + rebalanceQty ,self.basePrecision)
                            self.balance[self.baseAsset]['value'] = round( self.balance[self.baseAsset]['amt'] * price  ,self.quotePrecision)

                            self.balance[self.quoteAsset]['amt'] = round( self.balance[self.quoteAsset]['amt'] - cummulativeQuoteQty ,self.quotePrecision)
                            self.balance[self.quoteAsset]['value'] = self.balance[self.quoteAsset]['amt'] 


                            #write_csv
                            order[self.baseAsset] =self.balance[self.baseAsset]['amt'] 
                            order[self.quoteAsset] = self.balance[self.quoteAsset]['amt'] 
                            write_csv(order,'log.csv')

                            baseAmt = self.balance[self.baseAsset]['amt'] 
                            baseValue = self.balance[self.baseAsset]['value']
                            quoteAmt = self.balance[self.quoteAsset]['amt'] 
                            totalValue = round( self.balance[self.baseAsset]['value']  + self.balance[self.quoteAsset]['value']  ,self.quotePrecision)
                            msg_line = f'{self.system_name}\r\n BUY {symbol}:{price}\r\n rebalanceQty:{rebalanceQty}[{cummulativeQuoteQty}]\r\n baseAmt:{baseAmt}[{baseValue}]\r\n quoteAmt:{quoteAmt}\r\n totalValue:{totalValue}'
                
                        elif _order["side"] == "SELL":
                            #get acc from binance
                            #balance_binance = self.get_balance([self.baseAsset, self.quoteAsset])
                            #self.balance[self.baseAsset]['amt']  = round(float(balance_binance[self.baseAsset]), self.basePrecision)

                            self.balance[self.baseAsset]['amt']  = round( self.balance[self.baseAsset]['amt'] - rebalanceQty ,self.basePrecision)
                            self.balance[self.baseAsset]['value'] = round( self.balance[self.baseAsset]['amt'] * price  ,self.quotePrecision)

                            self.balance[self.quoteAsset]['amt'] = round( self.balance[self.quoteAsset]['amt'] + cummulativeQuoteQty ,self.quotePrecision)
                            self.balance[self.quoteAsset]['value'] = self.balance[self.quoteAsset]['amt'] 

                            #write_csv
                            order[self.baseAsset] =self.balance[self.baseAsset]['amt'] 
                            order[self.quoteAsset] = self.balance[self.quoteAsset]['amt'] 
                            write_csv(order,'log.csv')

                            baseAmt = self.balance[self.baseAsset]['amt'] 
                            baseValue = self.balance[self.baseAsset]['value']
                            quoteAmt = self.balance[self.quoteAsset]['amt'] 
                            totalValue = round( self.balance[self.baseAsset]['value']  + self.balance[self.quoteAsset]['value']   ,self.quotePrecision)
                            msg_line = f'{self.system_name}\r\n SELL {symbol}:{price}\r\n rebalanceQty:{rebalanceQty}[{cummulativeQuoteQty}]\r\n baseAmt:{baseAmt}[{baseValue}]\r\n quoteAmt:{quoteAmt}\r\n totalValue:{totalValue}'

                        print('                                                                                                     ',end='\r')
                        print(' ###################################### FILLED ORDER ###################################### ')
                        print(order)
                        print("")
                        
                        lineSendMas(self.line_token,msg_line)

                        #save balance
                        save_json(self.balance,'wallet.json')
                        

                        #save openOrder
                        self.openOrder.remove(delDict)
                        save_json(self.openOrder,'openedOrder.json')



    ########################### open order ###########################
    def place_orders_open(self, sym, side, quantity, order_comment):
        if side == 'BUY':
            price = self.symbol['bid']
        else:
            price = self.symbol['ask']

        symbol = self.symbol['symbol']
        
        res = self.client.place_orders(symbol=sym, side=side, price=price,ordertype='limit', timeInForce='GTC', quantity=quantity)
        print(res)
        print("")
        
        restime = timestampToDatetime( int(res["transactTime"])/1000 )
        
        if len(res['fills']) > 0:
            for fill in res['fills']:
                commission = float(fill["commission"])
                commissionAsset = fill["commissionAsset"]
        else :
            commission=0
            commissionAsset=self.quoteAsset


        #save openOrder
        self.openOrder.append({ 'orderId' : res['orderId'],
                'date': f'{restime}',
                'symbol': f'{symbol}',
                'price': price,
                'side':res['side'],
                'origQty': res['origQty'],
                'cummulativeQuoteQty': float(res['cummulativeQuoteQty']),
                'status':res['status'],
                'commission':commission,
                'commissionAsset':commissionAsset,
                'order_comment':f'{order_comment}',
                })
        
        msg_line = f'{self.system_name} {side} {symbol}:{price} [ place order ]'
        lineSendMas(self.line_token,msg_line)
        
        save_json(self.openOrder,'openedOrder.json')

    def calculate_rebalance(self):
        ask   = self.symbol['ask']     
        totalValue = self.balance[self.quoteAsset]['value'] + self.balance[self.baseAsset]['value']
        baseAssetRatioValue  = totalValue * self.baseAssetRatio
        quoteAssetRatioValue = totalValue * self.quoteAssetRatio 
        baseDiff  =  self.balance[self.baseAsset]['value'] - baseAssetRatioValue
        quoteDiff =  self.balance[self.quoteAsset]['value'] - quoteAssetRatioValue

        #keep value to echo
        self.portfolioValue['symbol'] = self.symbol['symbol']
        self.portfolioValue['ask'] = ask
        self.portfolioValue['baseAssetRatioValue'] = round(baseAssetRatioValue,self.quotePrecision)
        self.portfolioValue['quoteAssetRatioValue'] = round(quoteAssetRatioValue,self.quotePrecision)
        self.portfolioValue['baseAssetAmt'] = round(self.balance[self.baseAsset]['amt'],self.basePrecision)
        self.portfolioValue['baseAssetValue'] = round(self.balance[self.baseAsset]['value'],self.quotePrecision)
        self.portfolioValue['quoteAssetAmt'] = round(self.balance[self.quoteAsset]['amt'],self.quotePrecision)
        self.portfolioValue['quoteAssetValue'] = round(self.balance[self.quoteAsset]['value'],self.quotePrecision)
        self.portfolioValue['baseDiff']   = round(baseDiff,self.quotePrecision)
        self.portfolioValue['quoteDiff']   = round(baseDiff,self.quotePrecision)
        self.portfolioValue['totalValue'] = round(totalValue,self.quotePrecision)

    def rebalancing(self):
        if(len(self.openOrder)==0):
            ask   = self.symbol['ask']     
            totalValue = self.portfolioValue['totalValue'] 
            baseAssetRatioValue  = self.portfolioValue['baseAssetRatioValue']
            quoteAssetRatioValue = self.portfolioValue['quoteAssetRatioValue']
            baseDiff  = self.portfolioValue['baseDiff']  

            #rebalance Condition
            rebalanceSide = ''

            if abs(baseDiff) > self.margin and baseDiff > 0:
                rebalanceSide = 'SELL'
            elif abs(baseDiff) > self.margin and baseDiff < 0:
                rebalanceSide = 'BUY'

            #rebalance Qty
            rebalanceQty = round(abs(baseDiff)/ask ,self.Qtypoint) #base
            
            #check Qty&Notional
            check_minQty = rebalanceQty > self.minQty 
            check_minNotional = abs(baseDiff) > self.minNotional 
            
            #check openOrder == 0
            check_openedOrder = True if len(self.openOrder) == 0 else False

            #Send order
            if(rebalanceSide != '' and check_minQty and check_minNotional and check_openedOrder):
                quoteAssetV = self.balance[self.quoteAsset]['value']
                baseAssetV = self.balance[self.baseAsset]['value']
                print('                                                                                                     ',end='\r')
                print(' ####################################### PLACE ORDER ##################################### ')
                order_comment = f"{self.symbol['symbol']}:{ask} {baseDiff}|{rebalanceQty} [{totalValue}]"
                self.place_orders_open(self.symbol['symbol'], rebalanceSide, rebalanceQty, order_comment)
                
        
    ########################### initialize ########################### 
    def initialize(self):
        self.get_info()
        if  self.get_wallet() :
            print(self.balance)
            save_json(self.balance,'wallet.json')
            return True
        else:
            return False
    
    def get_info(self):
        print("----- get_info -----")
        sym_info={}
        info = self.client.exchangeInfo()
        for sym in info['symbols']:
            search_symbol = sym['symbol'] 
            print(f'searching {search_symbol}             ',end='\r')
            if search_symbol == self.symbol['symbol']:
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
                    self.tickPoint = decimal_nPoint(filters['tickSize'])
                if filters['filterType'] == 'MIN_NOTIONAL':
                    self.minNotional = float(filters['minNotional'])
                if filters['filterType'] == 'LOT_SIZE': 
                    self.minQty = float(filters['minQty'])
                    self.Qtypoint = decimal_nPoint(filters['minQty'])
            
            self.balance[self.quoteAsset]={}
            self.balance[self.baseAsset]={}
            return True
        else:
            print('Cant find symbol')
            return False
    
    def get_wallet(self):
        print("----- get_wallet -----")
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

            baseValueRequire = self.assetNotional * self.baseAssetRatio 
            quoteValueRequire= self.assetNotional * self.quoteAssetRatio 
            
            self.balance[self.baseAsset]['value'] = 0
            self.balance[self.baseAsset]['amt'] = 0
            self.balance[self.quoteAsset]['value'] = 0
            self.balance[self.quoteAsset]['amt'] = 0

            #baseAsset
            if(balance_binance[self.baseAsset]*ask >= baseValueRequire):#baseAsset > baseValueRequire
                self.balance[self.baseAsset]['value']  = round( baseValueRequire, self.quotePrecision)
                self.balance[self.baseAsset]['amt']  = round( baseValueRequire/ask, self.basePrecision)

            elif(balance_binance[self.baseAsset]*ask < baseValueRequire  #baseAsset < baseValueRequire
            and balance_binance[self.baseAsset]*ask + balance_binance[self.quoteAsset] > self.assetNotional ):
                self.balance[self.baseAsset]['value']  = round( balance_binance[self.baseAsset]*ask, self.quotePrecision)
                self.balance[self.baseAsset]['amt']  = round( balance_binance[self.baseAsset], self.basePrecision)
                #quoteAsset plus
                self.balance[self.quoteAsset]['value'] = round((baseValueRequire - self.balance[self.baseAsset]['value']), self.quotePrecision)
                self.balance[self.quoteAsset]['amt'] = round(self.balance[self.quoteAsset]['value'], self.quotePrecision)
                
            else:
                print("error : not enough asset") 
                return False
            

            if(balance_binance[self.quoteAsset]>= quoteValueRequire):#quoteAsset > quoteValueRequire
                self.balance[self.quoteAsset]['value'] =  round(self.balance[self.quoteAsset]['value'] + round( quoteValueRequire , self.quotePrecision) , self.quotePrecision)
                self.balance[self.quoteAsset]['amt'] =   round(self.balance[self.quoteAsset]['value'] , self.quotePrecision)

            elif(balance_binance[self.quoteAsset] < quoteValueRequire  #quoteAsset > quoteValueRequire
            and balance_binance[self.quoteAsset] + balance_binance[self.baseAsset]*ask > self.assetNotional ):
                self.balance[self.quoteAsset]['value'] = round( balance_binance[self.quoteAsset]  , self.quotePrecision) 
                self.balance[self.quoteAsset]['amt'] =   round(  balance_binance[self.quoteAsset] , self.quotePrecision)
                #baseAsset serplus
                self.balance[self.baseAsset]['value'] =   round(self.balance[self.baseAsset]['value'] + (quoteValueRequire -  self.balance[self.quoteAsset]['value'] ) , self.basePrecision)
                self.balance[self.baseAsset]['amt']  = round(self.balance[self.baseAsset]['value'] /ask, self.basePrecision)

            else:
                print("error : not enough asset") 
                return False

        else:
            print("error : can't get ticker")
            return False
        
        return True

    
    def start(self):
        if self.get_ticker() :
            ask  = self.symbol['ask']
            self.balance[self.baseAsset]['value'] = round(self.balance[self.baseAsset]['amt'] * ask,self.quotePrecision)
            #--calculate_rebalance
            self.calculate_rebalance()

            #--check_openOrder
            self.check_filled_order()    

            if self.time_check() :
                #--close order
                self.cancel_openOrder() 
                 
                #--rebalance
                self.rebalancing()
            
            #---echo
            sym = self.portfolioValue['symbol'] 
            baseAssetRatioValue  = self.portfolioValue['baseAssetRatioValue']
            quoteAssetRatioValue = self.portfolioValue['quoteAssetRatioValue'] 
            baseAssetAmt = self.portfolioValue['baseAssetAmt'] 
            baseAssetValue = self.portfolioValue['baseAssetValue'] 
            quoteAssetValue = self.portfolioValue['quoteAssetValue'] 
            baseDiff = self.portfolioValue['baseDiff']
            baseDiffPercent = round((baseDiff/baseAssetRatioValue)*100,2)
            totalValue = self.portfolioValue['totalValue'] 

            print(f'{self.system_name} {sym}:{ask}, {baseAssetAmt}[{baseAssetValue}]:{quoteAssetValue}, {baseDiff}[{baseDiffPercent}%], {totalValue}, {self.time_string}           ',end='\r')
        else:           
            print(f'{self.system_name} connection failed {self.time_string}                                                                                                         ',end='\r')


################ initialize ################
program = main()
print(" ####################################### initialize ####################################### ")
initialize = program.initialize()

print(" ######################################### Start ########################################## ")
print("")
while(True):
    
    while(program.system.control()):
        program.start()
        time.sleep(0)
    
    print(f'System stop [critical point]                                                                                                         ',end='\r')
    time.sleep(1)
