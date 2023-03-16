import argparse

import logging
from threading import Thread
from typing import Dict

import ibapi
from ibapi.wrapper import EWrapper
from ibapi.client import EClient
from ibapi.wrapper import *
from ibapi.ticktype import *
from ibapi.common import *
from ibapi.utils import *

from ibapi.account_summary_tags import *
from Contracts import Contracts
from Orders import Orders

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

        self.host: str = ""
        self.port: int = None
        self.clientid: int = 0
        self.accountid: str = ""  
        
        self.connection_status: bool = False
        self.account_summary: Dict = {}
        self.requests : Dict = {
                                "market_data": {},
                                "account_info": set(),
                                "position": set(),
                                "open_orders": set(),
                                "account_updates" : {}
                              } 
        self.ticks: Dict = {}
        self.my_position: Dict = {}
        self.portfolio: Dict ={}
        self.orderid: int = 0
        self.orders: Dict = {}
  
      
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
            symbol = self.requests["market_data"][req]
            self.ticks[symbol]["bid"] = price
           
        if tickType == 2 or tickType == 67:
          
          if price != 0:
            symbol = self.requests["market_data"][req]
            self.ticks[symbol]["ask"] = price

        if tickType == 4 or tickType == 68:
          
          if price != 0:
            symbol = self.requests["market_data"][req]
            self.ticks[symbol]["last_price"] = price
        
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
                                    "remaining": remaining
                                    })
        
        if self.orders[orderid]['status'] == "Filled":
           self.orders.pop(orderid)

    # def updateAccountValue(self, 
    #     key: str, 
    #     val: str, 
    #     currency: str,
    #     accountName: str
    # ):
    #     super().updateAccountValue(key, val, currency, accountName)

    #     print("UpdateAccountValue. Key:", key, "Value:", val,
    #                 "Currency:", currency, "AccountName:", accountName)
        
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

    ########Receving########

    #######Request#########

    def request_market_data_type(self,type):
       self.client.reqMarketDataType(MARKET_DATA_TYPE[type])

    def request_market_data(self,sec_type,symbol):
        if not self.requests["market_data"]:
            request_id = 1000
        else:
            request_id = max(k for k, v in self.requests["market_data"].items()) + 1
        self.ticks[symbol] = dict()
        if sec_type == "STK":
            self.client.reqMktData(request_id, Contracts.USStockAtSmart(symbol), "", False, False, [])
        elif sec_type == "CASH":
            self.client.reqMktData(request_id, Contracts.Fx(symbol,"USD"), "", False, False, [])
        
        self.requests["market_data"][request_id] = symbol

    def request_account_info(self):
        if not self.requests["account_info"]:
            request_id = 2000
        else:
            request_id = max(self.requests["account_info"]) + 1
          
        self.client.reqAccountSummary(request_id,"All", AccountSummaryTags.AllTags)
        self.requests["account_info"].add(request_id)

    def request_position(self):
        if not self.requests["position"]:
            request_id = 3000
        else:
            request_id = max(self.requests["position"]) + 1
          
        self.client.reqPositions()
        self.requests["position"].add(request_id)

    def request_open_orders(self):
        if not self.requests["open_orders"]:
            request_id = 4000
        else:
            request_id = max(self.requests["open_orders"]) + 1

        self.client.reqOpenOrders()
        self.requests["open_orders"].add(request_id)

    def request_account_updates(self):
        if not self.requests["account_updates"]:
            request_id = 5000
        else:
            request_id = max(self.requests["account_updates"]) + 1
        print(self.accountid)
        self.client.reqAccountUpdates(True, self.accountid)

    #######Request#########

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
    def place_order(self,contract,order):
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