from IBGateway.IBGateway import IBGateway
from MongodbDatabase.Mongodb_Database import MongodbDatabase
from Strategy.SpreadStrategy import SpreadStrategy

from threading import Thread
import datetime
import os
import json
import signal
import logging
import time
from bson.decimal128 import Decimal128
from dotenv import load_dotenv

from util import *

from pymongo import MongoClient

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
        
        self.host: str = ""                                        #localhost
        self.port: int = None                                      #live:7496, paper:7497
        self.clientid: int = 0                                     #0: default
        self.accountid: str = ""                                            
        
        self.api = IBGateway()
        self.db = MongodbDatabase()
        self.strategy = []                                         #deployed strategy            

        self.run_strategy : bool = False

        self.currency = ""
        self.position = None
        self.exchange = ""
        self.exchange_active = None
        signal.signal(signal.SIGINT, self.keyboardInterruptHandler)

        self.active = True

    def start(self):

        setup_logger("main",f"logs/main.log")
        self.logger = logging.getLogger("main") 
        self.logger.warning("Starting app...")

        #to be combined
        self.load_param()
        load_dotenv()
        
        #connect to IBapi
        self.api.main_bot = self
        self.api.connect_and_run(self.host,self.port,self.clientid,self.accountid)

        #connect and init database
        utc_now = datetime.datetime.combine(datetime.datetime.utcnow(),datetime.time(0, 0, 0))     
        self.db.main_bot = self
        self.db.connect()
        self.db.api = self.api
        self.db.db.portfolios.update_one({"date": utc_now},{'$setOnInsert':{"date": utc_now, "algo" : []}},upsert=True)
        self.db.db.accounts.update_one({"date": utc_now},{'$setOnInsert':{"date": utc_now}},upsert=True)

        #request basic info from api
        self.api.request_account_info()
        self.api.request_account_updates()
        self.api.request_position()
        self.api.request_open_orders()

        #starting trading strategy
        self.run_strategy = True
        for strategy in self.strategy:
            strategy.start()

        self._thread: Thread = Thread(target=self._main_thread)
        self._thread.start()

    def load_param(self):
        f = open("config/account.json")
        data = json.load(f)

        for key, value in data.items():
                setattr(self, key, value)
            
    def close(self):
        self.logger.warning("Closing app...")

        for strategy in self.strategy:
            strategy.stop()

        self.active = False

        self.db.save_account_info(self.api.account_summary)

        if self.api.client.isConnected():
            self.api.disconnect()

    def add_strategy(self, strategy):
        strategy.main_bot = self
        strategy.api = self.api
        self.strategy.append(strategy)

    def keyboardInterruptHandler(self, signal, frame):
        print("KeyboardInterrupt (ID: {}) has been caught. Cleaning up...".format(signal))
        self.close()

    def _main_thread (self):
        
        while self.active:
            time.sleep(30)

            if not self.api.client.isConnected:
                self.api.check_connection()
                
            self.logger.info(f"ACCOUNT {exchange_time(self.exchange)}: {self.api.account_summary}")
            # self.logger.info(f"POSITIONS {exchange_time(self.exchange)}: {self.api.my_position}")
            self.logger.info(f"PORTFOLIO {exchange_time(self.exchange)}: {self.api.portfolio}")
            # self.logger.info(f"ORDER {exchange_time(self.exchange)}: {self.api.orders}")
            self.logger.info(f"REQUESTS {exchange_time(self.exchange)}: {self.api.requests}")
            self.logger.info(f"TICKSS {exchange_time(self.exchange)}: {self.api.ticks}")

            #error handling, to be refactored and extended
            while self.api.errors :
                error = self.api.errors.pop()
                if error["request_id"] // 1000 == 1:
                    request = self.api.requests["market_data"][error["request_id"]]
                    
                    if error["error_code"] == 354:
                        
                        self.logger.error(f"ERROR {exchange_time(self.exchange)}: {error['error_code']}")
                        self.logger.error(f"ERROR {exchange_time(self.exchange)}: requesting again")
                        self.api.request_market_data(request["sec_type"],request["symbol"])
                        self.api.requests["market_data"].pop(error["request_id"])
            
            self.db.save_account_info(self.api.account_summary)



        

def main():

    app = MainBot ()
    app.add_strategy(SpreadStrategy("spread1"))
    app.start()

if __name__ == "__main__":
  
  main()   