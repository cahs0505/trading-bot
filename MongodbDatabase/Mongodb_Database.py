from pymongo import MongoClient
import time
import datetime
from bson.decimal128 import Decimal128

from setting import SETTINGS

class MongodbDatabase :

    def __init__(self) -> None:

        self.main_bot = None
        self.api = None

        self.name = SETTINGS['database.name']
        self.host = SETTINGS['database.host']
        self.port = SETTINGS['database.port']
        self.database_name = SETTINGS['database.database']
        self.client = None
        self.db = None

    def connect (self):
        self.client  = MongoClient(f"{SETTINGS['database.name']}://{SETTINGS['database.host']}:{SETTINGS['database.port']}/")
        self.db = self.client[self.database_name]

    def save_account_info(self,account):
        data = {
            "date": datetime.datetime.utcnow(),
            "available_funds": Decimal128(account['AvailableFunds'][0]),
            "buying_power": Decimal128(account['BuyingPower'][0]),
            "equity_with_loan_value": Decimal128(account['EquityWithLoanValue'][0]),
            "excess_liquidity": Decimal128(account['ExcessLiquidity'][0]),
            "full_init_margin_req": Decimal128(account['FullInitMarginReq'][0]),
            "full_maint_margin_req": Decimal128(account['FullMaintMarginReq'][0]),
            "gross_position_value": Decimal128(account['GrossPositionValue'][0]),
            "net_liquidation": Decimal128(account['NetLiquidation'][0]),
            "total_cash_value": Decimal128(account['TotalCashValue'][0]),
        }

        self.db.accounts.insert_one(data)

    def get_lastest_account_info(self):
        return self.db.accounts.find().limit(1).sort([('$natural',-1)])[0]
    
    def get_all_account_info(self):
        data = []
        for acc in self.db.accounts.find():
            data.append(acc)

        return data
        
    def save_portfolio(self,portfolio):

        data = { 
                "date": datetime.datetime.utcnow(),
                "portfolio": []
        }

        for symbol,detail in portfolio.items():
            data["portfolio"].append({
                    "symbol": symbol,
                    "sec_type": detail["sec_type"],
                    "exchange": detail["exchange"],
                    "position": Decimal128(detail["position"]),
                    "market_price": Decimal128(detail["market_price"]),
                    "market_value": Decimal128(detail["market_value"]),
                    "average_cost": Decimal128(detail["average_cost"]),
                    "unrealized_PnL": Decimal128(detail["unrealized_PnL"]),
                    "realized_PnL": Decimal128(detail["realized_PnL"])
            })

        self.db.portfolios.insert_one(data)

    def get_portfolio(self):
        return self.db.portfolios.find().limit(1).sort([('$natural',-1)])[0]
    
    def save_order(self,orderid,order):

        data = { 
                "date": datetime.datetime.utcnow(),
                "_id": orderid,
                "symbol": order["symbol"],
                "sec_type": order["sec_type"],
                "action": order["action"],
                "order_type": order["order_type"],
                "quantity": Decimal128(order["quantity"]),
                "limit_price": Decimal128(order["limit_price"]),
                "status": order["status"],
        }

        self.db.orders.insert_one(data)

    def update_order(self,orderid,order):

        data = {
            "symbol": order["symbol"],
            "sec_type": order["sec_type"],
            "action": order["action"],
            "order_type": order["order_type"],
            "quantity": order["quantity"],
            "limit_price": order["limit_price"],
            "status": order["status"],
            "filled": order["filled"],
            "remaining": order["remaining"],
            "avg_fill_price": order["avg_fill_price"]
        }

        self.db.orders.update_one({"_id": orderid}, data, upsert=True)

def main():
    mongodb = MongodbDatabase()
    mongodb.connect()
    
    time.sleep()
    accounts = mongodb.db['accounts']
    for acc in accounts:
        print(acc)

if __name__ == "__main__":
  
  main()   