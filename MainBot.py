from IBGateway import IBGateway
from SpreadStrategy import SpreadStrategy
import datetime
import os
import json
import signal

from util import log,check_trading_hours,check_trading_days,check_exchange_active, time_until_exchange_start,time_until_exchange_end

from Contracts import Contracts
from Orders import Orders


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
#9 error handling



#######To Do###########
class MainBot :

    def __init__(self):
        
        self.host: str = "127.0.0.1"                                         #localhost
        self.port: int = 7497                                                #live:7496, paper:7497
        self.clientid: int = 0                                                  #0: default
        self.accountid: str = "DU6734746"                                            
        
        self.api = IBGateway()
        self.strategy = SpreadStrategy(_main_bot = self)

        self.run_strategy : bool = False

        self.currency = "USD"
        self.position = None
        self.exchange = None
        self.exchange_active = None
        signal.signal(signal.SIGINT, self.keyboardInterruptHandler)

    def start(self):                                               
        self.api.connect_and_run(self.host,self.port,0,self.accountid)
        self.run_strategy = True
        self.strategy.start()
    
    def order(                                                  #to be refactor 
        self, 
        sec_type,
        order_type,
        action, 
        symbol, 
        quantity, 
        price
    ):
        if sec_type == "STK":                                                          
            contract = Contracts.USStockAtSmart(symbol)
        elif sec_type == "CASH":
            contract = Contracts.Fx(symbol, "USD")
        elif sec_type == "CMDTY":
            contract = Contracts.Commodity(symbol)

        if order_type == "LIMIT":                                                      
            order = Orders.LimitOrder(action,quantity,price)
        elif order_type == "MARKET":
            order = Orders.MarketOrder(action,quantity)
        elif order_type == "MID_PRICE":
            order = Orders.Midprice(action,quantity)

        self.api.place_order(contract,order)
    
    def close(self):
        log("Closing app...")
        self.strategy.stop()

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
        self.strategy = SpreadStrategy(_main_bot = self)

    def keyboardInterruptHandler(self, signal, frame):
        print("KeyboardInterrupt (ID: {}) has been caught. Cleaning up...".format(signal))
        self.close()

def main():

    app = MainBot ()
    app.start()

if __name__ == "__main__":
  
  main()   