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


def decimal_nPoint(text):
    nPoint = 0
    begincount = False
    text = str(text)
    for i in range(len(text)):
        if text[i] == '.':
            begincount = True
        if begincount and text[i] != '.':
            nPoint = i
    return nPoint



def precision_format(text):
    begincount = False
    precision_text = '0.' 
    text = str(text)
    for i in range(len(text)):
        if text[i] == '.':
            begincount = True
        if begincount and text[i] != '.':
            precision_text = precision_text + '0'
        elif begincount and i == len(text)-1:
            precision_text = precision_text + '1'
    return precision_text