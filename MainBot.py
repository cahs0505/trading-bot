from IBGateway.IBGateway import IBGateway
from Strategy.SpreadStrategy import SpreadStrategy

from threading import Thread
import datetime
import os
import json
import signal
import logging
import time

from util import exchange_time, setup_logger, check_exchange_active, time_until_exchange_start,time_until_exchange_end, check_trading_hours,check_trading_days

SEC_TYPE = {
    "STK",
    "CASH",
    "CMDTY"
}

ORDER_TYPE = {
    "LIMIT",
    "MARKET",
    "MID_PRICE"
}

ACTION = {
    "BUY",
    "SELL"
}

#######To Do###########

#1 Logging capability
#2 Refactoring: Abstract Class
#3 Connectivity : Re-connect
#4 Order management: unfilled order overnight ?
#5 Order management: same contract over several strategy?
#6 GUI?
#7 Performance tracking
#8 Alternative Data Source 
#9 error handling: If request fail, esp. data feed



#######To Do###########
class MainBot :

    def __init__(self):
        
        self.host: str = "127.0.0.1"                                         #localhost
        self.port: int = 7497                                                #live:7496, paper:7497
        self.clientid: int = 0                                                  #0: default
        self.accountid: str = "DU6734746"                                            
        
        self.api = IBGateway()
        self.strategy = []

        self.run_strategy : bool = False

        self.currency = "USD"
        self.position = None
        self.exchange = "NASDAQ"
        self.exchange_active = None
        signal.signal(signal.SIGINT, self.keyboardInterruptHandler)

        self.active = True

    def start(self):

        setup_logger("main",f"logs/main.log")
        self.logger = logging.getLogger("main") 

        self.logger.warning("Starting app...")

        self.api.connect_and_run(self.host,self.port,0,self.accountid)
        self.run_strategy = True

        for strategy in self.strategy:
            strategy.start()

        self._logging_thread: Thread = Thread(target=self._logging_thread)
        self._logging_thread.start()
            
    
    def close(self):
        self.logger.warning("Closing app...")

        for strategy in self.strategy:
            strategy.stop()

        self.active = False

        now = datetime.datetime.now().strftime("%Y-%m-%d")
        PATH = "PnL.json"
        if not os.path.isfile(PATH):
            data = {now:self.api.portfolio}
            with open(PATH, 'w') as f:
                json.dump(data,f)
        else:

            with open(PATH,'r') as t:
                data = json.load(t)

            data[now] = self.api.portfolio
            
            with open(PATH, 'w') as f:
                json.dump(data,f)

        if self.api.client.isConnected():
            self.api.disconnect()

    def add_strategy(self, strategy):
        strategy._main_bot = self
        strategy.api = self.api
        self.strategy.append(strategy)

    def keyboardInterruptHandler(self, signal, frame):
        print("KeyboardInterrupt (ID: {}) has been caught. Cleaning up...".format(signal))
        self.close()

    def _main_thread (self):
        pass

    def _logging_thread (self):
        
        while self.active:
            time.sleep(60)
            self.logger.info(f"ACCOUNT {exchange_time(self.exchange)}: {self.api.account_summary}")
            self.logger.info(f"POSITIONS {exchange_time(self.exchange)}: {self.api.my_position}")
            self.logger.info(f"PORTFOLIO {exchange_time(self.exchange)}: {self.api.portfolio}")
            self.logger.info(f"ORDER {exchange_time(self.exchange)}: {self.api.orders}")
            self.logger.info(f"REQUESTS {exchange_time(self.exchange)}: {self.api.requests}")

        

def main():

    # while time_until_exchange_start("NASDAQ") > datetime.timedelta(minutes = 15):
        
    #     print(f"exchange active in {':'.join(str(time_until_exchange_start('NASDAQ')).split(':')[:2])}")
    #     time.sleep (60)

    app = MainBot ()
    app.add_strategy(SpreadStrategy())
    app.start()

if __name__ == "__main__":
  
  main()   