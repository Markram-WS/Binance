import time
import configparser

class systemCondition():
    def __init__(self,portfolioValue):
        config = configparser.ConfigParser()
        config.read('./config.ini') 
        self.assetNotional = float(config['SYSTEM']['assetNotional'])
        self.portfolioValue = portfolioValue
    
    def control(self):
        return True
    '''    
        ### input condition ####
        if self.portfolioValue != {}:
            if self.portfolioValue['totalValue'] < assetNotional* 0.5:
                return True
            else: 
                return False
        else:
            return True
        #######################
    '''