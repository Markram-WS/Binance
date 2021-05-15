import requests
########################### order #############################
def cal_size(size,price,pricePrecision):
    return  f'{round(size/price,pricePrecision)}'

def timeframe_convert(tf):
    if(tf==60):
        return '1m'
    elif(tf==300):
        return '5m'
    elif(tf==900):
        return '15m'
    elif(tf==3600):
        return '1h'
    elif(tf==86400):
        return '1d'

########################### Msg Line ###########################   
def lineSendMas(token,msg_line):
    if token != '':
        url_line = 'https://notify-api.line.me/api/notify'
        headers_line = {'content-type':'application/x-www-form-urlencoded','Authorization':'Bearer '+ token}
        requests.post(url_line, headers=headers_line , data = {'message':msg_line})


def decimal_nPoint(impout):
    nPoint = 0
    simpout = str(impout)
    simpout = simpout.split('.')
    fimpout = float(impout)
    if len(simpout)>1:
        for i in range(len(simpout[1])+1):
            decimal = round( fimpout - round(fimpout,i) ,len(simpout[1])+1)
            if decimal == 0 :
                return  i
                break
    else:
        return  0
