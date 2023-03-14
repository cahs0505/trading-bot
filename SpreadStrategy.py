from threading import Thread
import logging
import datetime
import time
import json

from util import log, check_exchange_active, time_until_exchange_start,time_until_exchange_end, check_trading_hours,check_trading_days

class SpreadStrategy :

    def __init__(self, _main_bot):

        self.main_bot = _main_bot
        self.api = self.main_bot.api

        self.set_logger()
        
        self.exchange: str = ""
        self.sec_type: str = ""
        self.symbol_first: str = ""
        self.symbol_second: str = ""
        self.pair: list = []
        self.hedge_ratio = None                                                                
        self.spread_mean = None                          
        self.spread_std = None 
        self.entry_Zscore = None 
        self.exit_Zscore = None 

        self.current_position: int = 0
        self.unfilled_order: bool = False

        

    def set_logger (self):
        logger =  logging.getLogger("spread1")
        f_handler = logging.FileHandler(filename="logs/strategy/spread1.log")
        f_handler.setLevel(logging.ERROR)
        f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        f_handler.setFormatter(f_format)
        logger.addHandler(f_handler)
        self.logger = logger
    # def log (self):

        
    def load_param (self):
        f = open("config/strategy/strategy_param_1.json")
        data = json.load(f)

        for key, value in data.items():
                setattr(self, key, value)
       
    def buy_spread (self):                                                    
        self.main_bot.order(self.sec_type,"LIMIT","BUY",self.symbol_first,1,self.api.ticks[self.symbol_first]["ask"])
        self.main_bot.order(self.sec_type,"LIMIT","SELL",self.symbol_second,1,self.api.ticks[self.symbol_second]["bid"])
        self.logger.critical(f"Buy {self.symbol_first} at {self.api.ticks[self.symbol_first]['ask']}")
        self.logger.critical(f"Sell {self.symbol_second} at {self.api.ticks[self.symbol_second]['bid']}")

    def sell_spread (self):                                                   
        self.main_bot.order(self.sec_type,"LIMIT","SELL",self.symbol_first,1,self.api.ticks[self.symbol_first]["bid"])
        self.main_bot.order(self.sec_type,"LIMIT","BUY",self.symbol_second,1,self.api.ticks[self.symbol_second]["ask"])
        self.logger.critical(f"Sell {self.symbol_first} at {self.api.ticks[self.symbol_first]['bid']}")
        self.logger.critical(f"Buy {self.symbol_second} at {self.api.ticks[self.symbol_second]['ask']}")

    # 1:long / 0:neutral/ -1:short
    def check_position (self):
        if not self.symbol_first in self.api.my_position or not self.symbol_second in self.api.my_position :
            self.current_position = 0

        else:  
            if self.api.my_position[self.symbol_first]["position"] > 0 and self.api.my_position[self.symbol_second]["position"] < 0:   
                self.current_position = 1

            elif self.api.my_position[self.symbol_first]["position"] < 0 and self.api.my_position[self.symbol_second]["position"] > 0:
                self.current_position = -1

            else:
                self.current_position = 0

    def check_unfilled_order (self):
        if not self.api.orders:
             self.unfilled_order = False
             return
        
        for orderid , order in self.api.orders.items():
            if order["symbol"] in self.pair:
                self.unfilled_order = True  
                break

    def cancel_all_order (self):
        if not self.api.orders:
            return
        
        for orderid , order in self.api.orders.items():
            if order["symbol"] in self.pair:
                self.api.cancel_order(orderid)
                self.logger.critical(f"Cancelling order: symbol: {order['symbol']}, action: {order['action']}, quantity: {order['quantity']}, limit_price:{order['limit_price']}")

    def start(self):
        self.thread: Thread = Thread(target=self.run)
        self.thread.start()

    def stop(self):
        self.thread.join()

    def run(self):
        time.sleep(5)  
        self.load_param() 

        self.exchange_active = check_exchange_active(self.exchange)
        self.api.request_account_info()
        self.api.request_account_updates()
        self.api.request_position()
        self.api.request_open_orders()
        
        self.api.request_market_data_type("DELAYED")
        self.api.request_market_data(self.sec_type,self.symbol_first)
        self.api.request_market_data(self.sec_type,self.symbol_second)
        
        while self.api.isConnected():
        
            time.sleep(5)
            
            self.exchange_active = check_exchange_active(self.exchange)
            # log(f"ACCOUNT {self.api.account_summary}")
            log(f"POSITIONS {self.api.my_position}")
            log(f"ORDER {self.api.orders}")
            # log(f"REQUESTS {self.api.requests}")

            if not self.exchange_active:
                log(f"{self.exchange} active in {':'.join(str(time_until_exchange_start(self.exchange)).split(':')[:2])}")
                continue
            
            #stop trading when close to exchange close to prevent unfilled order overnight
            if time_until_exchange_end(self.exchange) < datetime.timedelta(minutes=10):     
                log(f"{self.exchange} down in {':'.join(str(time_until_exchange_end(self.exchange)).split(':')[:2])}, cancelling unfilled order, stopping trades")
                self.cancel_all_order()
                continue

            log(f"TICKS {self.api.ticks}")
            self.check_position ()     
            self.check_unfilled_order ()
            
            long_spread = self.api.ticks[self.symbol_first]["ask"] - self.api.ticks[self.symbol_second]["bid"]
            long_zScore = round((long_spread-self.spread_mean) / self.spread_std,2)

            short_spread = self.api.ticks[self.symbol_first]["bid"] - self.api.ticks[self.symbol_second]["ask"]
            short_zScore = round((short_spread-self.spread_mean) / self.spread_std,2)

            if self.unfilled_order:                                 #check if there is unfilled order
                log(f"ALGO unfilled order, not entering position")
                continue

            if self.current_position == 0:                            #when in neutral position

                if long_zScore < -self.entry_Zscore:
                    log(f"ALGO z-score:{long_zScore},buying spread")
                    self.logger.critical(f"Buy spread at z-score: {long_zScore}")
                    self.buy_spread()
                    
                elif short_zScore > self.entry_Zscore:
                    log(f"ALGO z-score:{short_zScore},selling spread")
                    self.logger.critical(f"Sell spread at z-score: {short_zScore}")
                    self.sell_spread()
                    
                else:
                    log(f"ALGO z-score:{long_zScore},nothing happens")

            elif self.current_position == 1:                          #when in long position  
            
                if short_zScore > self.exit_Zscore:
                    log(f"ALGO z-score:{short_zScore},exiting short position")
                    self.logger.critical(f"Sell spread at z-score: {short_zScore}")
                    self.sell_spread()
                    
            elif self.current_position == -1:                         #when in short position        
            
                if long_zScore < -self.exit_Zscore:
                    log(f"ALGO z-score:{long_zScore},exiting long position")
                    self.logger.critical(f"Buy spread at z-score: {long_zScore}")
                    self.buy_spread()
                    
