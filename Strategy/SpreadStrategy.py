from threading import Thread
import logging
import datetime
import time
import json

from util import exchange_time, setup_logger, check_exchange_active, time_until_exchange_start,time_until_exchange_end, check_trading_hours,check_trading_days

class SpreadStrategy :

    def __init__(self):

        self.main_bot = None
        self.api = None

        self._run = True
        
        self.name: str = ""
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

        self.data_type = "DELAYED"
        self.current_position: int = 0
        self.unfilled_order: bool = False



       
    def load_param (self):
        f = open("config/strategy/strategy_param_1.json")
        data = json.load(f)

        for key, value in data.items():
                setattr(self, key, value)
       
    def buy_spread (self):                                                    
        self.api.order(self.sec_type,"LIMIT","BUY",self.symbol_first,1,self.api.ticks[self.symbol_first]["ask"])
        self.api.order(self.sec_type,"LIMIT","SELL",self.symbol_second,1,self.api.ticks[self.symbol_second]["bid"])
        self.logger.critical(f"ALGO {exchange_time(self.exchange)}: Buy {self.symbol_first} at {self.api.ticks[self.symbol_first]['ask']}")
        self.logger.critical(f"ALGO {exchange_time(self.exchange)}: Sell {self.symbol_second} at {self.api.ticks[self.symbol_second]['bid']}")

    def sell_spread (self):                                                   
        self.api.order(self.sec_type,"LIMIT","SELL",self.symbol_first,1,self.api.ticks[self.symbol_first]["bid"])
        self.api.order(self.sec_type,"LIMIT","BUY",self.symbol_second,1,self.api.ticks[self.symbol_second]["ask"])
        self.logger.critical(f"ALGO {exchange_time(self.exchange)}: Sell {self.symbol_first} at {self.api.ticks[self.symbol_first]['bid']}")
        self.logger.critical(f"ALGO {exchange_time(self.exchange)}: Buy {self.symbol_second} at {self.api.ticks[self.symbol_second]['ask']}")

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
                self.logger.critical(f"ALGO {exchange_time(self.exchange)}: Cancelling order: symbol: {order['symbol']}, action: {order['action']}, quantity: {order['quantity']}, limit_price:{order['limit_price']}")
    
    #check if ticks function normally
    def check_ticks (self):
        
        if( not self.api.ticks[self.symbol_first] or
            not self.api.ticks[self.symbol_second] or
            self.api.ticks[self.symbol_first]["bid"] == 0 or
            self.api.ticks[self.symbol_first]["ask"] == 0 or
            self.api.ticks[self.symbol_second]["bid"] == 0 or
            self.api.ticks[self.symbol_second]["ask"] == 0):
            
            return False
        
        return True

    def start(self):
        self.load_param()

        setup_logger(self.name,f"logs/strategy/{self.name}.log")
        self.logger = logging.getLogger(self.name)

        self.logger.warning(f"{exchange_time(self.exchange)}: starting strategy")
        self.thread: Thread = Thread(target=self.run)
        self.thread.start()

    def stop(self):
        self.logger.warning(f"{exchange_time(self.exchange)}: stopping strategy")
        self._run = False

    def run(self):

        time.sleep(3)  
    
        self.exchange_active = check_exchange_active(self.exchange)
        self.api.request_account_info()
        self.api.request_account_updates()
        self.api.request_position()
        self.api.request_open_orders()
        
        self.api.request_market_data_type(self.data_type)
        self.api.request_market_data(self.sec_type,self.symbol_first)
        self.api.request_market_data(self.sec_type,self.symbol_second)
        
        while self._run:
            time.sleep(5)
            while self.api.client.isConnected():

                if not self._run:
                    break
            
                time.sleep(5)
                
                self.exchange_active = check_exchange_active(self.exchange)
                if not self.exchange_active:
                    self.logger.warning(f"{self.exchange} active in {':'.join(str(time_until_exchange_start(self.exchange)).split('.')[:1])}")
                    continue
                
                #stop trading when close to exchange close to prevent unfilled order overnight
                if time_until_exchange_end(self.exchange) < datetime.timedelta(minutes=10):     
                    self.logger.warning(f"{self.exchange} down in {':'.join(str(time_until_exchange_end(self.exchange)).split('.')[:1])}, cancelling unfilled order, stopping trades")
                    self.cancel_all_order()
                    continue
                
                self.check_position ()     
                self.check_unfilled_order ()

                self.logger.info(f"TICKS {exchange_time(self.exchange)}: {self.api.ticks}")

                if not self.check_ticks():
                    self.logger.warning("Ticks malfunctioning, skipping")
                    continue

                #check if there is unfilled order
                if self.unfilled_order:                                 
                    self.logger.info(f"ALGO unfilled order, not entering position")
                    continue

                long_spread = self.api.ticks[self.symbol_first]["ask"] - self.api.ticks[self.symbol_second]["bid"]
                long_zScore = round((long_spread-self.spread_mean) / self.spread_std,2)

                short_spread = self.api.ticks[self.symbol_first]["bid"] - self.api.ticks[self.symbol_second]["ask"]
                short_zScore = round((short_spread-self.spread_mean) / self.spread_std,2)

                #when in neutral position
                if self.current_position == 0:                            

                    if long_zScore < -self.entry_Zscore:               
                        self.logger.critical(f"ALGO {exchange_time(self.exchange)}: Buy spread at z-score: {long_zScore}")
                        self.buy_spread()
                        
                    elif short_zScore > self.entry_Zscore:
                        self.logger.critical(f"ALGO {exchange_time(self.exchange)}: Sell spread at z-score: {short_zScore}")
                        self.sell_spread()
                        
                    else:
                        self.logger.info(f"ALGO {exchange_time(self.exchange)}: z-score:{long_zScore},nothing happens")
                        
                #when in long position 
                elif self.current_position == 1:                           
                
                    if short_zScore > self.exit_Zscore:
                        self.logger.critical(f"ALGO {exchange_time(self.exchange)}: Sell spread at z-score: {short_zScore}")
                        self.sell_spread()

                #when in short position        
                elif self.current_position == -1:                              
                
                    if long_zScore < -self.exit_Zscore:
                        self.logger.critical(f"ALGO {exchange_time(self.exchange)}: Buy spread at z-score: {long_zScore}")
                        self.buy_spread()

            if not self._run:
                    break
            
            print("reconnecting")

        self.stop()               