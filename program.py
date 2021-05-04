import time
import numpy as np
from datetime import datetime

import threading
#----------
import configparser
#----------
from binance import RequestClient_f
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
        self.client = RequestClient_f(
            config['API']['server'],
            config['API']['key'].encode(),
            config['API']['secret'],
        )
        
        self.api_connect = True
        
        #system
        self.margin = float(config['SYSTEM']['margin'])
        self.size = float(config['SYSTEM']['size'])
        self.fee = float(config['SYSTEM']['fee'])
        self.side = config['SYSTEM']['side'].split(',')
        self.symbol = config['SYSTEM']['symbol'].split(',')
        self.sys_name   = config['SYSTEM']['name']
        self.slippage   = float(config['SYSTEM']['slippage'])
        self.order = load_json('data.json')
        self.del_order_list = list([])
        self.ticker = {}
        self.zone = 0
        self.system = True
        
        #indecator 
        self.timeframe = int(config['SYSTEM']['timeframe']) #min #day:1440  #5m:5
        self.period = int(config['SYSTEM']['period']) #bar

        #time
        self.tm = time.localtime() # get struct_time
        self.time_string = time.strftime("%Y-%m-%d, %H:%M:%S", self.tm)
        #time refresh
        self.refSec = 0 #refresh rate get Hisprice
        self.timeout = 0
        
        #HisPrice init
        self.sys = list([])
        for i in range(len(self.symbol)):self.sys.append(i)
        for i in range(len(self.sys)): 
            self.sys[i] = symbol(self.symbol[i],self.client)
        self.hisPrice_init()
            
    ########################### getdata ###########################   
    def time_check(self):
        #get_time
        self.tm = time.localtime() # get struct_time
        self.time_string = time.strftime("%Y-%m-%d, %H:%M:%S", self.tm)
        return True
    
    def hisPrice_init(self):
        for i in range(len(self.sys)):
            self.sys[i].getHisPrice(self.timeframe,100)
        for i in range(len(self.sys)):
            if i == 0: 
                self.ma = self.sys[i].ma('close')
                self.refBar = self.sys[i].refBar('high',1)
            elif i == 1: 
                self.ma = round(self.ma - self.sys[i].ma('close') , 5)
                self.refBar = round(self.refBar - self.sys[i].refBar('high',1) , 5)
            else:
                print('getHisPrice function error')
        
    def getHisPrice(self):
        if(self.refSec != self.tm and self.tm.tm_sec % self.timeframe  == 0):
            self.refSec = self.tm.tm_sec
            hisdatas = list()
            for i in range(len(self.sys)):
                get_hisdata = threading.Thread(target=self.sys[i].getHisPrice, args=[self.timeframe, self.period])
                get_hisdata.start()
                hisdatas.append(get_hisdata)
            for i in hisdatas:
                i.join()
                
            for i in range(len(self.sys)):
                if i == 0: 
                    self.ma = self.sys[i].ma('close')
                    self.refBar = self.sys[i].refBar('high',1)
                elif i == 1: 
                    self.ma = round(self.ma - self.sys[i].ma('close') , 5)
                    self.refBar = round(self.refBar - self.sys[i].refBar('high',1) , 5)
                else:
                    print('getHisPrice function error')
    
    
    ########################### open order ###########################
    #long|short speerate thread
    #-----place open orders fn------
    def place_orders_open(self,sym,positionSide,size,price,order_comment):
        side='BUY' if positionSide == 'LONG' else 'SELL'
        res = self.client.place_orders(symbol=sym, side=side, ordertype='MARKET',
                                       positionSide=positionSide, quantity=size)
        orderId = res['orderId']
        order = self.client.get_order(sym,orderId)
        price = float(order['avgPrice'])
        origQty =  float(order['origQty'])
        restime = timestampToDatetime( int(res["updateTime"])/1000 )
        return{ 'status':'open',
                'orderId' : orderId,
                'open_date': restime,
                'open_price': price,
                'side':positionSide,
                'size': float(res['origQty']),
                'sl': '',
                'tp': '',
                'fee':round(( origQty * price ) * self.fee ,5),
                'order_comment':f'{order_comment}',
                }
                        
    #-----long order-----side[i] 
    #long|short speerate thread
    def long_open_conditon(self):
        #------check short_conditon
        long_conditon = all([  self.ticker['ask'] < self.ma,
                               abs(self.ticker['ask'] - self.zone) < self.margin/90,
                               str(self.zone) not in self.order.keys()
                          ])

        if(long_conditon):
            self.order[f'{self.zone}'] = {}
            print(f' --------------------------------------- open long {self.zone} ---------------------------------------')
            for i in range(len(self.sys)):
                price = self.sys[i].ticker['ask'] if self.side[i] == 'LONG' else self.sys[i].ticker['bid']
                zone = self.ticker['ask']
                ord_size = cal_size(self.size,price,self.sys[i].quantityPrecision)
  
                #comment 
                open_ord_comment =  f'open:{zone} sys{i}:[{price}]'
                #place_orders_open
                order_response = self.place_orders_open(self.sys[i].symbol,self.side[i],ord_size,price,open_ord_comment)
                self.order[f'{self.zone}'][self.sys[i].symbol] = order_response
                print(order_response)
                print('')
            save_json(self.order,'data.json')
            print('--------')
            
    #-----short order-----side[-i]
    #long|short speerate thread
    def short_open_conditon(self):
        #------check short_conditon
        short_conditon = all([ self.ticker['bid'] > self.ma,
                               abs(self.ticker['bid'] - self.zone) < self.margin/90,
                               str(self.zone) not in self.order.keys()
                          ])
        if(short_conditon):
            self.order[f'{self.zone}'] = {}
            print(f' --------------------------------------- open short {self.zone} ---------------------------------------')
            for i in range(len(self.sys)):
                price = self.sys[i].ticker['ask'] if self.side[-i] == 'LONG' else self.sys[i].ticker['bid']
                zone = self.ticker['ask']
                ord_size = cal_size(self.size,price,self.sys[i].quantityPrecision)

                #comment 
                open_ord_comment =  f'open:{zone} sys{i}:[{price}]'
                #place_orders_open
                order_response = self.place_orders_open(self.sys[i].symbol,self.side[-i],ord_size,price,open_ord_comment)
                self.order[f'{self.zone}'][self.sys[i].symbol] = order_response           
                print(order_response)
                print('')
            save_json(self.order,'data.json')
            print('--------')
        
    ########################### close_order ###########################  
    #long|short combine thread
    #-----place close orders fn------
    def place_orders_close(self,sym,positionSide,size,price,zone,order_comment):
        side='SELL' if positionSide == 'LONG' else 'BUY'
        res = self.client.place_orders(symbol=sym, side=side, ordertype='MARKET',
                                       positionSide=positionSide, quantity=size)
        orderId = res['orderId']
        order = self.client.get_order(sym,orderId)
        price = float(order['avgPrice'])
        origQty = float(order['origQty'])
        restime = timestampToDatetime( int(res["updateTime"])/1000 )
        
        self.order[f'{zone}'][sym]['status'] = 'close'
        self.order[f'{zone}'][sym]['close_id'] = orderId
        self.order[f'{zone}'][sym]['close_date'] = restime
        self.order[f'{zone}'][sym]['close_price'] = price
        close_val = price * float(self.order[f'{zone}'][sym]['size'])                                 #USDT
        open_val = float(self.order[f'{zone}'][sym]['size']) * float(self.order[f'{zone}'][sym]['open_price'])   #USDT
        self.order[f'{zone}'][sym]['fee'] = self.order[f'{zone}'][sym]['fee'] + (close_val * self.fee)
        
        #calculate order_profit
        if(self.order[f'{zone}'][sym]['side']=='LONG'):
            self.order[f'{zone}'][sym]['order_profit'] = close_val - open_val - self.order[f'{zone}'][sym]['fee'] 
        elif(self.order[f'{zone}'][sym]['side']=='SHORT'):
            self.order[f'{zone}'][sym]['order_profit'] = open_val - close_val - self.order[f'{zone}'][sym]['fee'] 
        else:
            print('error calculate order_profit')
            print('')
            self.system = False
            
        self.order[f'{zone}'][sym]['order_comment'] = f'{order_comment}'
        self.order[f'{zone}'][sym]['zone'] = zone
        
        #get balance
        port = self.client.get_balance('USDT')
        self.order[f'{zone}'][sym]['balance'] = port['balance']
        self.order[f'{zone}'][sym]['available'] = port['withdrawAvailable'] 
        
        return self.order[f'{zone}'][sym]
        
    #-----process close_order---------

    #-----CLOSE ORDER------
    def process_closeOrder(self,zone):
        zone = float(zone)
        now_zone = self.ticker['ask']
        open_order_sys1 = self.order[f'{zone}'][self.sys[0].symbol]['size'] * self.order[f'{zone}'][self.sys[0].symbol]['open_price']
        open_order_sys2 = self.order[f'{zone}'][self.sys[1].symbol]['size'] * self.order[f'{zone}'][self.sys[1].symbol]['open_price']
        fee = self.order[f'{zone}'][self.sys[0].symbol]['fee'] + self.order[f'{zone}'][self.sys[1].symbol]['fee']
        zone_profit = 0  
        conditon_close=False
        #-----CLOSE LONG
        if(self.order[f'{zone}'][self.sys[0].symbol]['side'] == 'LONG'):   
            price = [self.sys[0].ticker['bid'], self.sys[1].ticker['ask']] 
            current_order_sys1 = self.order[f'{zone}'][self.sys[0].symbol]['size'] * price[0]
            current_order_sys2 = self.order[f'{zone}'][self.sys[1].symbol]['size'] * price[1]
            fee = fee + (current_order_sys2 * self.fee) + (current_order_sys1 * self.fee)
            conditon_close = (current_order_sys1 - open_order_sys1) + (open_order_sys2-current_order_sys2) > self.margin + self.slippage + fee
            if(conditon_close): 
                #cal total profit
                for i in range(len(self.sys)):
                    price = self.sys[i].ticker['ask'] if self.side[i] == 'LONG' else self.sys[i].ticker['bid']
                    #comment
                    close_ord_comment = self.order[f'{zone}'][self.sys[i].symbol]['order_comment'] + f' | close:{now_zone} sys{i}:[{price}]'
                    order_response = self.place_orders_close(self.sys[i].symbol,self.side[-i],self.order[f'{zone}'][self.sys[i].symbol]['size'],price,zone,close_ord_comment)
                    zone_profit = zone_profit + order_response['order_profit']
                #add total profit
                for i in range(len(self.sys)):
                    self.order[f'{zone}'][self.sys[i].symbol]['zone_profit'] = zone_profit
                #set del order
                self.del_order_list.append(f'{zone}')
            
        #---CLOSE SHORT
        elif(self.order[f'{zone}'][self.sys[0].symbol]['side'] == 'SHORT'):
            price = [self.sys[0].ticker['ask'], self.sys[1].ticker['bid']] 
            current_order_sys1 = (self.order[f'{zone}'][self.sys[0].symbol]['size'] * price[0])
            current_order_sys2 = (self.order[f'{zone}'][self.sys[1].symbol]['size'] * price[1])
            fee = fee + (current_order_sys2 * self.fee) + (current_order_sys1 * self.fee)
            conditon_close = (open_order_sys1 - current_order_sys1) + (current_order_sys2-open_order_sys2) > self.margin + self.slippage + fee
            if(conditon_close): 
                #cal total profit
                for i in range(len(self.sys)):
                    price = self.sys[i].ticker['ask'] if self.side[i] == 'LONG' else self.sys[i].ticker['bid']
                    #comment
                    close_ord_comment = self.order[f'{zone}'][self.sys[i].symbol]['order_comment'] + f' | close:{now_zone} sys{i}:[{price}]'
                    order_response = self.place_orders_close(self.sys[i].symbol,self.side[i],self.order[f'{zone}'][self.sys[i].symbol]['size'],price,zone,close_ord_comment)
                    zone_profit = zone_profit + order_response['order_profit']
                #add total profit
                for i in range(len(self.sys)):
                    self.order[f'{zone}'][self.sys[i].symbol]['zone_profit'] = zone_profit
                #set del order
                self.del_order_list.append(f'{zone}')
                
    #-----operation------
    def close_order(self):
        processes = list()
        for zone in self.order.keys():
            process = threading.Thread(target=self.process_closeOrder, args=[zone])
            process.start()
            processes.append(process)
        for process in processes:
            process.join()
        
        #save log
        if len(self.del_order_list) > 0:
            print(f' --------------------------------------- close order --------------------------------------- ')
            for del_zone in self.del_order_list:
                print(f'------ {del_zone} ------')
                for order in self.order[f'{del_zone}']:
                    print(self.order[f'{del_zone}'][order])
                    print('')
                    write_log(self.order[f'{del_zone}'][order],'log.csv')
                print('--------')
                del self.order[del_zone]
                
            save_json(self.order,'data.json')
            self.del_order_list=[]

            
    ######################## program control ####################
    def controlPanel(self,timeout):
        self.timeout  = timeout*60 #min to sec
        lastsec=0
        while(self.system and (timeout != 0)):
            if(lastsec != self.tm.tm_sec):
                lastsec = self.tm.tm_sec
                self.timeout -= 1
            if(self.timeout<0):
                self.system = False
                
    ########################### start ###########################   
    def start(self):
        try:
            #get_ticker
            self.api_connect = all([self.sys[i].get_ticker() for i in range(len(self.sys))])
            #cal_ticker
            self.ticker['ask']  = round(self.sys[0].ticker['ask'] - self.sys[1].ticker['bid'], 5)
            self.ticker['bid']  = round(self.sys[0].ticker['bid'] - self.sys[1].ticker['ask'], 5)

            #----thread set 
            thr_getHisPrice = threading.Thread(target=self.getHisPrice)
            #----thread start 
            thr_getHisPrice.start()
        except:
            self.api_connect=False

        if(self.api_connect):
            #update time
            self.time_check()
            
            #cal zone
            self.zone = round((self.ticker['ask'] // self.margin) * self.margin,5)
            
            #----thread set 
            #------check open long_conditon
            #thr_open_long = threading.Thread(target=self.long_open_conditon)
            #------check open short_conditon
            #thr_open_short = threading.Thread(target=self.short_open_conditon)
               
            #----thread open order start 
            #thr_open_long.start()
            #thr_open_short.start()
            #----thread open order join 
            #thr_open_long.join()
            #thr_open_short.join()
            
            #------check close_conditon
            self.close_order()
            
            ask  = self.ticker['ask']
            print(f'{self.sys[0].symbol}/{self.sys[1].symbol}:{self.sys_name} zone:{self.zone} ask:{ask} ma:{self.ma} {self.time_string}  timeout:{self.timeout}  ',end='\r')
        else:           
            print(f'{self.sys_name} connection failed {self.time_string}                                                                                          ',end='\r')


program = main()
while(program.system):
    program.start()
    time.sleep(0)