import time
import configparser

class timeFunction():
    def __init__(self):
        config = configparser.ConfigParser()
        config.read('config.ini') 
        self.tm = time.localtime() # get struct_time
        self.time_string = time.strftime("%Y-%m-%d, %H:%M:%S", self.tm)
        self.time_interval = int(config['SYSTEM']['time_interval'])
        self.interval = config['SYSTEM']['interval']

    def update_time(self):
        self.tm = time.localtime() # get struct_time
        self.time_string = time.strftime("%Y-%m-%d, %H:%M:%S", self.tm)

    def time_condition(self):
        ################### input logic #######################
        self.update_time()
        if self.time_interval != 0 and getattr(self.tm,self.interval) % self.time_interval == 0:
            return True
        elif self.time_interval == 0 and  getattr(self.tm,self.interval) == 0:
            return True
        else:
            return False
        #######################################################