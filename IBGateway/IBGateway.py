import argparse

import logging
from threading import Thread
from typing import Dict
from decimal import *
import queue

import ibapi
from ibapi.wrapper import EWrapper
from ibapi.client import EClient
from ibapi.wrapper import *
from ibapi.ticktype import *
from ibapi.common import *
from ibapi.utils import *

from ibapi.account_summary_tags import *
from .Contracts import Contracts
from .Orders import Orders

print(ibapi.__version__)

MARKET_DATA_TYPE = {
    "LIVE": 1,
    "FROZEN": 2,
    "DELAYED": 3,
    "DELAYED_FROZEN":4
}

class IBGateway(EWrapper):

    def __init__(self):

        EWrapper.__init__(self)

        self.client: EClient = EClient(self)

        self.main_bot = None

        self.host: str = ""
        self.port: int = None
        self.clientid: int = 0
        self.accountid: str = ""  
        
        self.connection_status: bool = False
        self.account_summary: Dict = {}
        self.requests : Dict = {
                                "market_data": {},
                                "account_info": {},
                                "position": {},
                                "open_orders": {},
                                "account_updates" : {}
                              }
        self.pending_request = queue.Queue() 
        self.ticks: Dict = {}
        self.my_position: Dict = {}
        self.portfolio: Dict ={}
        self.orderid: int = 0
        self.orders: Dict = {}
        self.errors : list = []
  
      
    ####Connection########
    def connect_and_run(
        self, 
        host: str, 
        port: int, 
        clientid: int,
        accountid: str
    ):

        self.host = host
        self.port = port
        self.clientid = clientid
        self.accountid = accountid       

        self.client.connect(self.host, self.port, self.clientid)
        self.connection_status = True
        self.thread = Thread(target=self.client.run)
        self.thread.start()

        self.request_processor: Thread = Thread(target=self.process_request)
        self.request_processor.start()

    def disconnect(self):
        # if not self.connection_status:
        #     return 
        
        # self.connection_status = False
        self.client.disconnect()
        
      
    def check_connection(self):
        if self.client.isConnected():
            return
        
        if self.connection_status:
            self.disconnect()

        self.connect_and_run(self.host,self.port,self.clientid)
    ####Connection########

    ####Receving########
    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)

        logging.debug("setting nextValidOrderId: %d", orderId)

        if not self.orderid:
          self.orderid = orderId

        print("NextValidId:", orderId)

    def error(
        self, 
        reqId: TickerId, 
        errorCode: int, 
        errorString: str, 
        advancedOrderRejectJson = ""
    ):
        super().error(reqId, errorCode, errorString, advancedOrderRejectJson)

        if advancedOrderRejectJson:
            print("Error. Id:", reqId, "Code:", errorCode, "Msg:", errorString, "AdvancedOrderRejectJson:", advancedOrderRejectJson)
            
        else:
            print("Error. Id:", reqId, "Code:", errorCode, "Msg:", errorString)

        #error handling for requests
        
        error = {
            "request_id": reqId,
            "error_code": errorCode,
        }
        self.errors.append(error)
        

    def tickPrice(
        self, 
        req: TickerId, 
        tickType: TickType, 
        price: float,
        attrib: TickAttrib
    ): 
        super().tickPrice(req, tickType, price, attrib)

        if tickType == 1 or tickType == 66:
          
          if price != 0:
            symbol = self.requests["market_data"][req]["symbol"]
            self.ticks[symbol]["bid"] = Decimal(str(price))
           
        if tickType == 2 or tickType == 67:
          
          if price != 0:
            symbol = self.requests["market_data"][req]["symbol"]
            self.ticks[symbol]["ask"] = Decimal(str(price))

        if tickType == 4 or tickType == 68:
          
          if price != 0:
            symbol = self.requests["market_data"][req]["symbol"]
            self.ticks[symbol]["last_price"] = Decimal(str(price))
        
    def contractDetails(self, reqId, contractDetails):
        print(f"contract details: {contractDetails}")

    def contractDetailsEnd(self, reqId):
        print("End of contractDetails")
        self.disconnect()

    def accountSummary(
        self, 
        reqId: int, 
        account: str, 
        tag: str, 
        value: str,
        currency: str
    ):
        super().accountSummary(reqId, account, tag, value, currency)

        self.account_summary[tag] = (value,currency)

    def accountSummaryEnd(self, reqId: int):  
        super().accountSummaryEnd(reqId)

        print("AccountSummaryEnd. ReqId:", reqId)

    def position(
        self, 
        account: str, 
        contract: Contract, 
        position: Decimal,
        avgCost: float
    ):     
        super().position(account, contract, position, avgCost)

        if position != 0:
            self.my_position[contract.symbol] = {
                                                "position":position,
                                                "avg_cost":floatMaxString(avgCost)
                                                }
        
    def positionEnd(self):
        super().positionEnd()
        print("PositionEnd")
      
    def openOrder(
        self, 
        orderId: OrderId, 
        contract: Contract, 
        order: Order,
        orderState: OrderState
    ):      
        super().openOrder(
            orderId, contract, order, orderState
        )

        orderid: str = str(orderId)
    
        self.orders[orderid] = {
                                "symbol": contract.symbol,
                                "sec_type": contract.secType,
                                "action": order.action,
                                "order_type": order.orderType,
                                "quantity": order.totalQuantity,
                                "limit_price": order.lmtPrice,
                                "status": orderState.status,
                                }
        
        # self.main_bot.db.save_order(orderid, self.orders[orderid])

        print(self.orders)

    def orderStatus(
        self, 
        orderId: OrderId, 
        status: str, 
        filled: Decimal,
        remaining: Decimal, 
        avgFillPrice: float, 
        permId: int,
        parentId: int, 
        lastFillPrice: float, 
        clientId: int,
        whyHeld: str, 
        mktCapPrice: float
    ):             
        super().orderStatus(
            orderId, 
            status, 
            filled, 
            remaining,
            avgFillPrice, 
            permId, 
            parentId, 
            lastFillPrice, 
            clientId, 
            whyHeld, 
            mktCapPrice
        )

        orderid: str = str(orderId)      

        self.orders[orderid].update({
                                    "filled": filled,
                                    "remaining": remaining,
                                    "avg_fill_price": avgFillPrice
                                    })
        
        # self.main_bot.db.update_order(orderid, self.orders[orderid])

        if self.orders[orderid]['status'] == "Filled":
           self.orders.pop(orderid)

    #  After the initial callback to updateAccountValue, callbacks only occur for values which have changed. 
    # This occurs at the time of a position change, or every 3 minutes at most. 
    def updateAccountValue(self, 
        key: str, 
        val: str, 
        currency: str,
        accountName: str
    ):
        super().updateAccountValue(key, val, currency, accountName)
        
        # print("UpdateAccountValue. Key:", key, "Value:", val,
        #             "Currency:", currency, "AccountName:", accountName)
    
    #After the initial callback to updatePortfolio, callbacks only occur for positions which have changed. 
    def updatePortfolio(self, 
                        contract: Contract, 
                        position: Decimal,
                        marketPrice: float, 
                        marketValue: float,
                        averageCost: float, 
                        unrealizedPNL: float,
                        realizedPNL: float, 
                        accountName: str
    ):
        super().updatePortfolio(contract, position, marketPrice, marketValue,
                            averageCost, unrealizedPNL, realizedPNL, accountName)
        
        self.portfolio[contract.symbol] = {
                                            "sec_type": contract.secType,
                                            "exchange": contract.exchange,
                                            "position": decimalMaxString(position),
                                            "market_price": floatMaxString(marketPrice),
                                            "market_value": floatMaxString(marketValue),
                                            "average_cost": floatMaxString(averageCost),
                                            "unrealized_PnL": floatMaxString(unrealizedPNL),
                                            "realized_PnL": floatMaxString(realizedPNL),                          
                                            }
        
        # self.main_bot.db.save_portfolio(self.portfolio)
        
    ########Receving########

    #######Request#########

    def request_market_data_type(self,type):

        request = {
            "type":"market_data_type",
            "params":{
                "type": type,
            }
        }

        self.pending_request.put(request)

    def request_market_data(self,sec_type,symbol):

        request = {
            "type":"market_data",
            "params":{
                "sec_type": sec_type,
                "symbol": symbol
            }
        }

        self.pending_request.put(request)

    def request_account_info(self):

        request = {
            "type":"account_info",
            "params":{     
            }
        }

        self.pending_request.put(request)

    def request_position(self):

        request = {
            "type":"position",
            "params":{     
            }
        }

        self.pending_request.put(request)
       
    def request_open_orders(self):
        
        request = {
            "type":"open_orders",
            "params":{     
            }
        }

        self.pending_request.put(request)

    def request_account_updates(self):

        request = {
            "type":"account_updates",
            "params":{     
            }
        }

        self.pending_request.put(request)
        
    #######Request#########

    def process_request(self):
        while self.client.isConnected():

            while not self.pending_request.empty():

                request = self.pending_request.get()

                if(request["type"] == "market_data_type"):

                    self.client.reqMarketDataType(MARKET_DATA_TYPE[request["params"]["type"]])
                
                elif (request["type"] == "market_data"):

                    if not self.requests["market_data"]:
                        request_id = 1000
                    else:
                        request_id = max(k for k, v in self.requests["market_data"].items()) + 1

                    self.ticks[request["params"]["symbol"]] = dict()

                    if request["params"]["sec_type"] == "STK":
                        self.client.reqMktData(request_id, Contracts.USStockAtSmart(request["params"]["symbol"]), "", False, False, [])
                    elif request["params"]["sec_type"] == "CASH":
                        self.client.reqMktData(request_id, Contracts.Fx(request["params"]["symbol"],"USD"), "", False, False, [])
                    
                    self.requests["market_data"][request_id] = {"symbol": request["params"]["symbol"],
                                                                "sec_type": request["params"]["sec_type"],
                                                                "error": None}
                
                elif (request["type"] == "account_info"):

                    if not self.requests["account_info"]:
                        request_id = 2000
                    else:
                        request_id = max(self.requests["account_info"]) + 1
                    
                    self.client.reqAccountSummary(request_id,"All", AccountSummaryTags.AllTags)
                    self.requests["account_info"][request_id] = {"error": None}

                elif (request["type"] == "position"):

                    if not self.requests["position"]:
                        request_id = 3000
                    else:
                        request_id = max(self.requests["position"]) + 1
                    
                    self.client.reqPositions()
                    self.requests["position"][request_id] = {"error": None}
                
                elif (request["type"] == "open_orders"):

                    if not self.requests["open_orders"]:
                        request_id = 4000
                    else:
                        request_id = max(self.requests["open_orders"]) + 1

                    self.client.reqOpenOrders()
                    self.requests["open_orders"][request_id] = {"error": None}

                elif (request["type"] == "account_updates"):

                    if not self.requests["account_updates"]:
                        request_id = 5000
                    else:
                        request_id = max(self.requests["account_updates"]) + 1
                    
                    self.client.reqAccountUpdates(True, self.accountid)
                    self.requests["account_updates"][request_id] = {"error": None}

    #######CancelRequests#########
    def cancel_market_data(self, request_id):
        self.client.cancelMktData(request_id)
        self.requests["market_data"].pop(request_id)

    def cancel_account_info(self, request_id):
        self.client.cancelAccountSummary(request_id)
        self.requests["account_info"].remove(request_id)

    def cancel_all_requests(self):
        for request_id in list(self.requests["market_data"].keys()):
          self.cancel_market_data(request_id)
        for request_id in list(self.requests["account_info"]):
          self.cancel_account_info(request_id)
    #######CancelRequests#########

    #########Order##########
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

        self.orderid += 1
        self.client.placeOrder(self.orderid, contract, order)
        self.client.reqIds(1)

    def cancel_order(self, orderid):
        self.client.cancelOrder(orderid)
    #########Order##########

   
def main():
    logging.basicConfig(level = logging.ERROR)

    localhostname = "DESKTOP-51IRLB5.local"
    localIp = "127.0.0.1"

    cmdLineParser = argparse.ArgumentParser("api tests")
    cmdLineParser.add_argument("-p", "--port", action="store", type=int,
                                  dest="port", default=7497, help="The TCP port to use")
    cmdLineParser.add_argument("-C", "--global-cancel", action="store_true",
                                  dest="global_cancel", default=False,
                                  help="whether to trigger a globalCancel req")
    args = cmdLineParser.parse_args()
    print("Using args", args)

    app = IBGateway()


    app.connect_and_run(localIp, 7497  , 0,"DU6734746" )


if __name__ == "__main__":
  main()