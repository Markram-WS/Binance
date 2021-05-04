from binance.utils.timeservice import get_current_timestamp
from binance.base.printobject import PrintMix
from binance.utils.apisignature import create_signature
from binance.utils.apisignature import create_signature_with_query
from binance.exception.binanceapiexception import BinanceApiException
from binance.utils import *

import time
import requests 
import json 

###############################################################################################
#----------------------------------------create_request------------------------------------------#
###############################################################################################
import hmac
import hashlib
class create_request:
    def __init__(self,server_url,api_key,secret_key):
        self._server_url = server_url
        self._api_key = api_key
        self._secret_key = secret_key

    def _get(self, url, builder):
        request = RestApiRequest()
        request.method = "GET"
        request.host = self._server_url
        request.header.update({'Content-Type': 'application/json'})
        request.url = url + "?" + builder.build_url()
        return request

    def _get_with_apikey(self, url, builder, printRequest: 'bool' = None)-> any:
        request = RestApiRequest()
        request.method = "GET"
        request.host = self._server_url
        request.header.update({'Content-Type': 'application/json'})
        request.header.update({"X-MBX-APIKEY": self.__api_key})
        request.url = url + "?" + builder.build_url()
        # For develop
        if printRequest == True:
            print("====== Request ======")
            print(request)
            PrintMix.print_data(request)
            print("=====================")
        return request

    def _get_with_signature(self, url, builder, printRequest: 'bool' = None)-> any:
        request = RestApiRequest()
        request.method = "GET"
        request.host = self._server_url
        builder.put_url("recvWindow", 60000)
        builder.put_url("timestamp", str(get_current_timestamp() - 1000))
        create_signature(self._secret_key, builder)
        request.header.update({"Content-Type": "application/x-www-form-urlencoded"})
        request.header.update({"X-MBX-APIKEY": self._api_key})
        request.url = url + "?" + builder.build_url()
        # For develop
        if printRequest == True:
            print("====== Request ======")
            print(request)
            PrintMix.print_data(request)
            print("=====================")
        return request
    
    def _post_with_signature(self, url, builder, printRequest: 'bool' = None)-> any:
        request = RestApiRequest()
        request.method = "POST"
        request.host = self._server_url
        builder.put_url("recvWindow", 60000)
        builder.put_url("timestamp", str(get_current_timestamp() - 1000))
        create_signature(self._secret_key, builder)
        request.header.update({'Content-Type': 'application/json'})
        request.header.update({"X-MBX-APIKEY": self._api_key})
        request.post_body = builder.post_map
        request.url = url + "?" + builder.build_url()
        # For develop
        if printRequest == True:
            print("====== Request ======")
            print(request)
            PrintMix.print_data(request)
            print("=====================")
        return request

###############################################################################################
#----------------------------------------RestApiRequest---------------------------------------#
###############################################################################################
class RestApiRequest(object):
    def __init__(self):
        self.method = ""
        self.url = ""
        self.host = ""
        self.post_body = ""
        self.header = dict()
        self.json_parser = None
        self.header.update({"client_SDK_Version": "binance_futures-1.0.1-py3.7"})
        
###############################################################################################
#---------------------------------------rest API Invoker--------------------------------------#
###############################################################################################
def check_response(json_wrapper):
    if json_wrapper.contain_key("success"):
        success = json_wrapper.get_boolean("success")
        if success is False:
            err_code = json_wrapper.get_int_or_default("code", "")
            err_msg = json_wrapper.get_string_or_default("msg", "")
            if err_code == "":
                raise BinanceApiException(BinanceApiException.EXEC_ERROR, "[Executing] " + err_msg)
            else:
                raise BinanceApiException(BinanceApiException.EXEC_ERROR, "[Executing] " + str(err_code) + ": " + err_msg)
    elif json_wrapper.contain_key("code"):
        code = json_wrapper.get_int("code")
        msg = json_wrapper.get_string_or_default("msg", "")
        if code != 200:
            raise BinanceApiException(BinanceApiException.EXEC_ERROR, "[Executing] " + str(code) + ": " + msg)

def get_limits_usage(response):
    limits = {}
    limits_headers = ["X-MBX-USED-WEIGHT-", "X-MBX-ORDER-COUNT-" ]  # Limit headers to catch
    for key,value in response.headers.items():
        if any([key.startswith(h) for h in limits_headers]):
            limits[key] = value
    return limits

def call_sync(request):
    if request.method == "GET":
        response = requests.get(request.host + request.url, headers=request.header)
        limits = get_limits_usage(response)
        #print(response.text)
        json_wrapper = parse_json_from_string(response.text)
        check_response(json_wrapper)
        return json.loads(response.text)
    elif request.method == "POST":
        response = requests.post(request.host + request.url, headers=request.header)
        limits = get_limits_usage(response)
        #print(response.text)
        json_wrapper = parse_json_from_string(response.text)
        check_response(json_wrapper)
        return json.loads(response.text)
    elif request.method == "DELETE":
        response = requests.delete(request.host + request.url, headers=request.header)
        limits = get_limits_usage(response)
        #print(response.text)
        json_wrapper = parse_json_from_string(response.text)
        check_response(json_wrapper)
        return json.loads(response.text)
    elif request.method == "PUT":
        response = requests.put(request.host + request.url, headers=request.header)
        limits = get_limits_usage(response)
        #print(response.text)
        json_wrapper = parse_json_from_string(response.text)
        check_response(json_wrapper)
        return json.loads(response.text)
