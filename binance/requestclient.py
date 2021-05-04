from binance.restapirequest import create_request
from binance.restapirequest import call_sync
from binance.utils.inputchecker import check_should_not_none
from binance.utils.urlparamsbuilder import UrlParamsBuilder
from binance.utils.constant import *
from binance.utils.timeservice import *
import time
###############################################################################################
#----------------------------------------RequestClient_s--------------------------------------#
###############################################################################################
class RequestClient_s:  
    def __init__(self,server_url,api_key,secret_key):
        self._request=create_request(server_url,api_key,secret_key)

    def server_time(self):
        builder = UrlParamsBuilder()
        res = call_sync(self._request._get(f'/api/v3/time', builder))
        return res['serverTime']
    
    def MKTdepth(self,symbol,limit:'int'= None):
        check_should_not_none(symbol, "symbol")
        builder = UrlParamsBuilder()
        builder.put_url("symbol", symbol)
        builder.put_url("limit", limit)
        return call_sync(self._request._get(f'/api/v3/depth', builder))

    def exchangeInfo(self):
        builder = UrlParamsBuilder()
        return call_sync(self._request._get(f'/api/v3/exchangeInfo', builder))
    
    def _listToDict_HistoricalPriceFN(self,price_list):
        price_dict={'time':[],
                 'open':[],
                 'high':[],
                 'low':[],
                 'close':[],
                 'volume':[]
                }
        for i in price_list:
            price_dict["time"].append(timestampToDatetime(int(i[0])/1000))
            price_dict["open"].append(float(i[1]))
            price_dict["high"].append(float(i[2]))
            price_dict["low"].append(float(i[3]))
            price_dict["close"].append(float(i[4]))
            price_dict["volume"].append(float(i[5]))
        return price_dict

    def historicalPrice(self, symbol: 'str', interval: 'CandlestickInterval', 
                            startTime: 'long' = None, endTime: 'long' = None, limit: 'int' = None) -> any:
        check_should_not_none(symbol, "symbol")
        check_should_not_none(symbol, "interval")
        builder = UrlParamsBuilder()
        builder.put_url("symbol", symbol)
        builder.put_url("interval", interval)
        builder.put_url("startTime", startTime)
        builder.put_url("endTime", endTime)
        builder.put_url("limit", limit)
        res = call_sync(self._request._get(f'/api/v3/klines', builder))
        return self._listToDict_HistoricalPriceFN(res)
    
    def place_orders(self, symbol: 'str', side: 'OrderSide', ordertype: 'OrderType', 
                timeInForce: 'TimeInForce' = TimeInForce.INVALID, quantity: 'float' = None,
                quoteOrderQty: 'quoteOrderQty' = None, price: 'float' = None,
                newClientOrderId: 'str' = None, stopPrice: 'float' = None, 
                icebergQty: 'icebergQty' = None,  newOrderRespType: 'OrderRespType' = OrderRespType.INVALID,
                recvWindow: 'recvWindow' = None) -> any:
        check_should_not_none(symbol, "symbol")
        check_should_not_none(side, "side")
        check_should_not_none(ordertype, "ordertype")
        builder = UrlParamsBuilder()
        builder.put_url("symbol", symbol)
        builder.put_url("side", side)
        builder.put_url("type", ordertype)
        builder.put_url("timeInForce", timeInForce)
        builder.put_url("quantity", quantity)
        builder.put_url("reducquoteOrderQtyeOnly", quoteOrderQty)
        builder.put_url("price", price)
        builder.put_url("newClientOrderId", newClientOrderId)
        builder.put_url("stopPrice", stopPrice)
        builder.put_url("icebergQty", icebergQty)
        builder.put_url("recvWindow", recvWindow)
        builder.put_url("newOrderRespType", newOrderRespType)
        return call_sync(self._request._post_with_signature("/api/v3/order", builder,True))

    def place_orders_test(self, symbol: 'str', side: 'OrderSide', ordertype: 'OrderType', 
                timeInForce: 'TimeInForce' = TimeInForce.INVALID, quantity: 'float' = None,
                quoteOrderQty: 'quoteOrderQty' = None, price: 'float' = None,
                newClientOrderId: 'str' = None, stopPrice: 'float' = None, 
                icebergQty: 'icebergQty' = None,  newOrderRespType: 'OrderRespType' = OrderRespType.INVALID,
                recvWindow: 'recvWindow' = None) -> any:
        check_should_not_none(symbol, "symbol")
        check_should_not_none(side, "side")
        check_should_not_none(ordertype, "ordertype")
        builder = UrlParamsBuilder()
        builder.put_url("symbol", symbol)
        builder.put_url("side", side)
        builder.put_url("type", ordertype)
        builder.put_url("timeInForce", timeInForce)
        builder.put_url("quantity", quantity)
        builder.put_url("reducquoteOrderQtyeOnly", quoteOrderQty)
        builder.put_url("price", price)
        builder.put_url("newClientOrderId", newClientOrderId)
        builder.put_url("stopPrice", stopPrice)
        builder.put_url("icebergQty", icebergQty)
        builder.put_url("recvWindow", recvWindow)
        builder.put_url("newOrderRespType", newOrderRespType)
        return call_sync(self._request._post_with_signature("/api/v3/order/test", builder,True))

    def get_account(self,symbol: 'str' = None):
        builder = UrlParamsBuilder()
        res = call_sync(self._request._get_with_signature("/api/v3/account", builder))
        if symbol != None:
            for n_sym in range(len(symbol)):
                if res['balances'][n_sym]['asset'] == symbol:
                    return res['balances'][n_sym]
                    break
        else:
            return res['balances']         

    def get_order(self , symbol: 'str', orderId: 'long' = None):
            check_should_not_none(symbol, "symbol")
            builder = UrlParamsBuilder()
            builder.put_url("symbol", symbol)
            builder.put_url("orderId", orderId)
            return call_sync(self._request._get_with_signature("/api/v3/order", builder))


    def get_all_open_order(self , symbol: 'str', recvWindow: 'long' = None):
        builder = UrlParamsBuilder()
        builder.put_url("symbol", symbol)
        builder.put_url("recvWindow", recvWindow)
        request = call_sync(self._request._get_with_signature("/api/v3/openOrderList", builder))
        return request




###############################################################################################
#----------------------------------------RequestClient_f--------------------------------------#
###############################################################################################
class RequestClient_f:  
    def __init__(self,server_url,api_key,secret_key):
        self._request=create_request(server_url,api_key,secret_key)

    def server_time(self):
        builder = UrlParamsBuilder()
        res = call_sync(self._request._get(f'/fapi/v1/time', builder))
        return res['serverTime']
    
    def MKTdepth(self,symbol,limit:'int'= None):
        check_should_not_none(symbol, "symbol")
        builder = UrlParamsBuilder()
        builder.put_url("symbol", symbol)
        builder.put_url("limit", limit)
        return call_sync(self._request._get(f'/fapi/v1/depth', builder))

    def exchangeInfo(self):
        builder = UrlParamsBuilder()
        return call_sync(self._request._get(f'/fapi/v1/exchangeInfo', builder))
    
    def _listToDict_HistoricalPriceFN(self,price_list):
        price_dict={'time':[],
                 'open':[],
                 'high':[],
                 'low':[],
                 'close':[],
                 'volume':[]
                }
        for i in price_list:
            price_dict["time"].append(timestampToDatetime(int(i[0])/1000))
            price_dict["open"].append(float(i[1]))
            price_dict["high"].append(float(i[2]))
            price_dict["low"].append(float(i[3]))
            price_dict["close"].append(float(i[4]))
            price_dict["volume"].append(float(i[5]))
        return price_dict

    def historicalPrice(self, symbol: 'str', interval: 'CandlestickInterval', 
                            startTime: 'long' = None, endTime: 'long' = None, limit: 'int' = None) -> any:
        check_should_not_none(symbol, "symbol")
        check_should_not_none(symbol, "interval")
        builder = UrlParamsBuilder()
        builder.put_url("symbol", symbol)
        builder.put_url("interval", interval)
        builder.put_url("startTime", startTime)
        builder.put_url("endTime", endTime)
        builder.put_url("limit", limit)
        res = call_sync(self._request._get(f'/fapi/v1/klines', builder))
        return self._listToDict_HistoricalPriceFN(res)
  
            
    def historicalPriceCon(self, symbol: 'str', interval: 'CandlestickInterval', 
                            startTime: 'long' = None, endTime: 'long' = None, limit: 'int' = None) -> any:
        check_should_not_none(symbol, "symbol")
        check_should_not_none(symbol, "interval")
        builder = UrlParamsBuilder()
        builder.put_url("symbol", symbol)
        builder.put_url("interval", interval)
        builder.put_url("startTime", startTime)
        builder.put_url("endTime", endTime)
        builder.put_url("limit", limit)
        res = call_sync(self._request._get(f'/fapi/v1/continuousKlines', builder))
        return self._listToDict_HistoricalPriceFN(res)


    
    def place_orders(self, symbol: 'str', side: 'OrderSide', ordertype: 'OrderType', 
                timeInForce: 'TimeInForce' = TimeInForce.INVALID, quantity: 'float' = None,
                reduceOnly: 'boolean' = None, price: 'float' = None,
                newClientOrderId: 'str' = None, stopPrice: 'float' = None, 
                workingType: 'WorkingType' = WorkingType.INVALID, closePosition: 'boolean' = None,
                positionSide: 'PositionSide' = PositionSide.INVALID, callbackRate: 'float' = None,
                activationPrice: 'float' = None, newOrderRespType: 'OrderRespType' = OrderRespType.INVALID) -> any:
        check_should_not_none(symbol, "symbol")
        check_should_not_none(side, "side")
        check_should_not_none(ordertype, "ordertype")
        builder = UrlParamsBuilder()
        builder.put_url("symbol", symbol)
        builder.put_url("side", side)
        builder.put_url("type", ordertype)
        builder.put_url("timeInForce", timeInForce)
        builder.put_url("quantity", quantity)
        builder.put_url("reduceOnly", reduceOnly)
        builder.put_url("price", price)
        builder.put_url("newClientOrderId", newClientOrderId)
        builder.put_url("stopPrice", stopPrice)
        builder.put_url("workingType", workingType)
        builder.put_url("closePosition", closePosition)
        builder.put_url("positionSide", positionSide)
        builder.put_url("callbackRate", callbackRate)
        builder.put_url("activationPrice", activationPrice)
        builder.put_url("newOrderRespType", newOrderRespType)
        return call_sync(self._request._post_with_signature("/fapi/v1/order", builder,True))

    def get_balance(self,symbol: 'str' = None):
        builder = UrlParamsBuilder()
        res = call_sync(self._request._get_with_signature("/fapi/v1/balance", builder))
        if symbol != None:
            for i in res:
                if i['asset'] == symbol:
                    return i
                    break
        else:
            return res           

    def get_order(self , symbol: 'str', orderId: 'long' = None):
            check_should_not_none(symbol, "symbol")
            builder = UrlParamsBuilder()
            builder.put_url("symbol", symbol)
            builder.put_url("orderId", orderId)
            return call_sync(self._request._get_with_signature("/fapi/v1/order", builder))

    def get_all_orders(self , symbol: 'str', orderId: 'long' = None, startTime: 'long' = None, 
                        endTime: 'long' = None, limit: 'int' = None) -> any:
            check_should_not_none(symbol, "symbol")
            builder = UrlParamsBuilder()
            builder.put_url("symbol", symbol)
            builder.put_url("orderId", orderId)
            builder.put_url("startTime", startTime)
            builder.put_url("endTime", endTime)
            builder.put_url("limit", limit)
            return call_sync(self._request._get_with_signature("/fapi/v1/allOrders", builder))

    def get_open_order(self , symbol: 'str', orderId: 'long' = None):
        builder = UrlParamsBuilder()
        builder.put_url("symbol", symbol)
        builder.put_url("orderId", orderId)
        request = call_sync(self._request._get_with_signature("/fapi/v1/openOrder", builder))
        return request

    def get_all_open_order(self , symbol: 'str', recvWindow: 'long' = None):
        builder = UrlParamsBuilder()
        builder.put_url("symbol", symbol)
        builder.put_url("recvWindow", recvWindow)
        request = call_sync(self._request._get_with_signature("/fapi/v1/openOrders", builder))
        return request
